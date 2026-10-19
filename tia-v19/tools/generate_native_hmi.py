#!/usr/bin/env python3
"""Clone the user's native V19 objects into an offline HMI review package.

No PLC code is changed. Source and reference evidence are recorded separately
from native compilation. Command execution remains locked in this first import.
"""
from pathlib import Path
import copy
import csv
import hashlib
import html
import json
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / 'hmi/seed'
OUT = ROOT / 'hmi/native'
NAMES = [('ROLL_Przeglad', 'Przegląd'), ('ROLL_Receptury', 'Receptury'),
         ('ROLL_Reczny', 'Ręczne'), ('ROLL_Alarmy', 'Alarmy'), ('ROLL_Nastawy', 'Nastawy')]
SEED_SCREEN = ET.parse(SEED / 'WZOR_ROLL.xml').getroot()
SEED_TAGS = ET.parse(SEED / 'tags.xml').getroot()
TEMPLATES = {item.tag: item for item in SEED_SCREEN.iter() if item.get('CompositionName') == 'ScreenItems'}


def node(parent, name, text=None, **attrs):
    result = ET.SubElement(parent, name, attrs)
    if text is not None:
        result.text = str(text)
    return result


def attr(obj, name, value):
    attributes = obj.find('AttributeList')
    if attributes is None:
        attributes = ET.SubElement(obj, 'AttributeList')
    element = attributes.find(name)
    if element is None:
        element = ET.SubElement(attributes, name)
    element.text = str(value)


def object_list(obj):
    result = obj.find('ObjectList')
    return result if result is not None else ET.SubElement(obj, 'ObjectList')


def link(parent, name, target):
    item = node(parent, name, TargetID='@OpenLink')
    node(item, 'Name', target)


def document_object(seed, tag):
    doc = copy.deepcopy(seed)
    for child in list(doc):
        if child.tag not in ('Engineering', 'DocumentInfo'):
            doc.remove(child)
    obj = copy.deepcopy(seed.find(tag))
    doc.append(obj)
    return doc, obj


def renumber(doc):
    count = 0
    for element in doc.iter():
        if 'ID' in element.attrib:
            element.set('ID', f'{count:X}')
            count += 1
        if 'TargetID' in element.attrib:
            assert element.get('TargetID') == '@OpenLink', 'Unmodelled internal reference'


def write_xml(path, doc):
    renumber(doc)
    ET.indent(doc, space='  ')
    path.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(doc).write(path, encoding='utf-8', xml_declaration=True)


def text_content(obj, composition, text):
    for container in object_list(obj):
        if container.get('CompositionName') == composition:
            for field in container.findall('.//MultilingualTextItem/AttributeList/Text'):
                field.clear()
                body = ET.SubElement(field, 'body')
                for line in text.split('\n'):
                    node(body, 'p', line)


def clone_item(kind, name, x, y, width, height, font=13):
    obj = copy.deepcopy(TEMPLATES['Hmi.Screen.' + kind])
    for key, value in dict(ObjectName=name, Left=x, Top=y, Width=width, Height=height).items():
        attr(obj, key, value)
    if kind == 'Circle':
        # V19 treats Radius as dependent on Width, but import validates both.
        # The seed's radius (24) must not survive resizing its diameter to 20.
        if width <= 0 or width != height or width % 2:
            raise ValueError('Circle requires equal, positive, even width and height')
        attr(obj, 'Radius', width // 2)
    for field in obj.findall('.//Hmi.Globalization.FontItem/AttributeList/FontSize'):
        field.text = str(font)
    # The seed text field sizes itself to fit. Fix its geometry for predictable
    # 800x480 layout and keep all captions inside the configured rectangles.
    if obj.find('AttributeList/FitToLargest') is not None:
        attr(obj, 'FitToLargest', 'false')
    return obj


def event(trigger, actions):
    obj = ET.Element('Hmi.Event.Event', ID='0', CompositionName='Events')
    node(node(obj, 'AttributeList'), 'Name', trigger)
    handler = node(node(obj, 'ObjectList'), 'Hmi.Event.FunctionListEventHandler', ID='0', CompositionName='EventHandler')
    entries = node(handler, 'ObjectList')
    for function, parameters in actions:
        entry = node(entries, 'Hmi.Event.FunctionListEntry', ID='0', CompositionName='FunctionListEntries')
        fields = node(entry, 'AttributeList')
        node(fields, 'Name', function)
        node(fields, 'Type', 'SystemFunction')
        args = node(entry, 'ObjectList')
        for name, value, literal_type in parameters:
            argument = node(args, 'Hmi.Event.FunctionListEntryParameter', ID='0', CompositionName='Parameters')
            fields = node(argument, 'AttributeList')
            node(fields, 'Name', name)
            if literal_type:
                node(fields, 'Value', value, Type=literal_type)
            else:
                link(node(argument, 'LinkList'), 'Value', value)
    return obj


def bit(function, tag):
    return function, [('Tag', 'ROLL_' + tag, None)]


def set_value(tag, value):
    return 'SetTag', [('Tag', 'ROLL_' + tag, None), ('Value', value, 'System.Double')]


def navigate(name):
    return 'ActivateScreen', [('Screen name', name, None), ('Object number', 0, 'System.Int32')]


class Screen:
    def __init__(self, name, number):
        self.doc, self.obj = document_object(SEED_SCREEN, 'Hmi.Screen.Screen')
        attr(self.obj, 'Name', name)
        attr(self.obj, 'Number', number)
        attr(self.obj, 'BackColor', '242, 245, 249')
        for layer in self.obj.findall('ObjectList/Hmi.Screen.ScreenLayer'):
            for content in list(object_list(layer)):
                object_list(layer).remove(content)
        self.items = object_list(self.obj.find('ObjectList/Hmi.Screen.ScreenLayer'))
        self.name = name
        self.count = 0

    def add(self, kind, label, x, y, width, height, font=13):
        self.count += 1
        item = clone_item(kind, f'{self.name}_{kind}_{self.count:03}', x, y, width, height, font)
        self.items.append(item)
        if kind == 'TextField':
            text_content(item, 'Text', label)
        elif kind == 'Button':
            text_content(item, 'TextOff', label)
            text_content(item, 'TextOn', label)
            for child in list(object_list(item)):
                if child.tag == 'Hmi.Event.Event':
                    object_list(item).remove(child)
        return item

    def text(self, text, x, y, width, height=24, font=13):
        return self.add('TextField', text, x, y, width, height, font)

    def field(self, tag, x, y, width=100, readonly=False, digits=5):
        obj = self.add('IOField', '', x, y, width, 30)
        attr(obj, 'Mode', 'Output' if readonly else 'InOutput')
        attr(obj, 'FormatPattern', 's' + '9' * digits)
        attr(obj, 'FieldLength', digits)
        target = obj.find('.//Hmi.Screen.Property/AttributeList/Name')
        assert target is not None and target.text == 'ProcessValue', 'A bound native I/O field is required'
        obj.find('.//Hmi.Dynamic.TagConnectionDynamic/LinkList/Tag/Name').text = 'ROLL_' + tag
        return obj

    def button(self, label, x, y, width, height, actions=(), held=None, enabled=True, font=12):
        obj = self.add('Button', label, x, y, width, height, font)
        attr(obj, 'Enabled', str(enabled).lower())
        if held:
            object_list(obj).append(event('Press', [bit('SetBit', held)]))
            object_list(obj).append(event('Release', [bit('ResetBit', held)]))
        elif actions:
            object_list(obj).append(event('Click', actions))
        return obj

    def lamp(self, label, tag, x, y, width=210, on_color=None):
        obj = self.add('Circle', '', x, y + 2, 20, 20)
        obj.find('.//Hmi.Dynamic.TagElementTrigger/LinkList/Tag/Name').text = 'ROLL_' + tag
        if on_color:
            for interval in obj.findall('.//Hmi.Dynamic.Range'):
                if interval.findtext('AttributeList/LowerLimit') == '1':
                    attr(interval, 'BackColor', on_color)
        self.text(label, x + 28, y, width - 28)

    def header(self, title):
        for index, (name, label) in enumerate(NAMES):
            self.button(label, 16 + 156 * index, 8, 148, 32,
                        [bit('ResetBit', 'GroundHeld'), bit('ResetBit', 'WorkHeld'), navigate(name)])
        self.text(title, 16, 53, 590, 31, 21)
        self.lamp('PLC', 'Connected', 696, 56, 85)

    def save(self):
        # First import verifies the native schema, not process actuation. Keep
        # all generated operator commands and editable fields locked; navigation
        # may only clear the two held bits before changing the displayed screen.
        for item in self.items:
            if item.tag == 'Hmi.Screen.Button':
                functions = item.findall('.//Hmi.Event.FunctionListEntry/AttributeList/Name')
                if not any(field.text == 'ActivateScreen' for field in functions):
                    attr(item, 'Enabled', 'false')
            elif item.tag == 'Hmi.Screen.IOField' and item.findtext('AttributeList/Mode') == 'InOutput':
                attr(item, 'Enabled', 'false')
        write_xml(OUT / 'screens' / (self.name + '.xml'), self.doc)
        skeleton = copy.deepcopy(self.doc)
        for layer in skeleton.findall('.//Hmi.Screen.ScreenLayer'):
            for item in list(object_list(layer)):
                object_list(layer).remove(item)
        write_xml(OUT / 'skeletons' / (self.name + '.xml'), skeleton)


def build_tags():
    with (ROOT / 'hmi/interface.csv').open(encoding='utf-8-sig') as stream:
        rows = list(csv.DictReader(stream, delimiter=';'))
    rows += [dict(tag='Clock', data_type='Bool', plc_symbol='"ROLL_HMI".StatusM[3,5]', direction='PLC->HMI')]
    for name, symbol in [('ManualMode', 'Input[0,1]'), ('Simulation', 'Simulation'),
                         ('OutputsEnabled', 'PhysicalOutputsEnabled'), ('IoConfigured', 'PhysicalIoConfigured'),
                         ('ConversionFault', 'ConversionFault')]:
        rows.append(dict(tag=name, data_type='Bool', plc_symbol='"ROLL_IO".' + symbol, direction='PLC->HMI'))
    doc, table = document_object(SEED_TAGS, 'Hmi.Tag.TagTable')
    attr(table, 'Name', 'ROLL_TP900_Tags')
    old = list(table.findall('ObjectList/Hmi.Tag.Tag'))
    external = {tag.findtext('LinkList/DataType/Name'): tag for tag in old if tag.find('LinkList/Connection') is not None}
    objects = object_list(table)
    objects.clear()
    for row in rows:
        kind = row['data_type']
        obj = copy.deepcopy(external['Bool' if kind == 'Bool' else 'Int'])
        attr(obj, 'Name', 'ROLL_' + row['tag'])
        attr(obj, 'Length', {'Bool': 1, 'Int': 2, 'DInt': 4}[kind])
        obj.find('LinkList/ControllerTag/Name').text = row['plc_symbol'].replace('"', '')
        obj.find('LinkList/Connection/Name').text = 'ROLL_PLC'
        obj.find('LinkList/DataType/Name').text = kind
        obj.find('LinkList/HmiDataType/Name').text = kind
        if row['tag'] == 'Clock':
            obj.find('LinkList/AcquisitionCycle/Name').text = '100 ms'
        objects.append(obj)
    write_xml(OUT / 'tags/ROLL_TP900_Tags.xml', doc)
    return rows


def build_screens():
    result = []
    s = Screen(NAMES[0][0], 101)
    s.header('Przegląd maszyny')
    s.text('Program aktywny', 18, 105, 220)
    s.field('CurrentProgram', 255, 101, readonly=True)
    s.lamp('Tryb ręczny', 'ManualMode', 418, 104, 345)
    s.text('Czas procesu T1 [s]', 18, 155, 230)
    s.field('ProcessTimer1Units', 255, 151, readonly=True)
    s.text('Czas ociekania T2 [s]', 18, 201, 235)
    s.field('ProcessTimer2Units', 255, 197, readonly=True)
    s.lamp('Symulacja', 'Simulation', 418, 151, 345, on_color='241, 161, 44')
    s.lamp('Moduły I/O skonfigurowane', 'IoConfigured', 418, 198, 345)
    s.lamp('Wyjścia fizyczne odblokowane', 'OutputsEnabled', 418, 245, 345)
    s.lamp('Błąd konwersji', 'ConversionFault', 418, 292, 345, on_color='237, 88, 97')
    for i, title in enumerate(['1 · Mycie / ultradźwięki', '2 · Płukanie', '3 · Płukanie', '4 · Suszenie']):
        s.text(title, 18 + 195 * i, 365, 188, 50, 12)
    s.save(); result.append(s)

    s = Screen(NAMES[1][0], 102)
    s.header('Programy mycia')
    s.text('Program', 18, 99, 115)
    s.field('SelectedProgram', 136, 95, 70)
    for i, value in enumerate([1, 2]):
        s.button(str(value), 226 + i * 57, 95, 49, 30, [set_value('SelectedProgram', value)])
    s.text('Aktywny', 408, 100, 105)
    s.field('CurrentProgram', 518, 95, 70, readonly=True)
    fields = [('Stacja 1 · zanurzenie [s]', 'Dwell1Seconds'), ('Stacja 1 · ociekanie [s]', 'Drain1Seconds'),
              ('Stacja 2 · zanurzenie [s]', 'Dwell2Seconds'), ('Stacja 2 · ociekanie [s]', 'Drain2Seconds'),
              ('Stacja 3 · zanurzenie [s]', 'Dwell3Seconds'), ('Stacja 3 · ociekanie [s]', 'Drain3Seconds'),
              ('Stacja 4 · suszenie [s]', 'Dry4Seconds'), ('Ruch bębna · tryb 0–4', 'BasketMotion')]
    for i, (label, tag) in enumerate(fields):
        col, row = divmod(i, 4)
        s.text(label, 18 + col * 390, 145 + row * 44, 260, 26, 12)
        s.field(tag, 284 + col * 390, 141 + row * 44, 90)
    for i, (label, tag) in enumerate([('Ultradźwięki', 'Ultrasound1'), ('Ruch pionowy', 'BathLift')]):
        x = 18 + i * 390
        s.lamp(label, tag, x, 329, 190)
        s.button('Wł.', x + 202, 323, 78, 32, [bit('SetBit', tag)])
        s.button('Wył.', x + 287, 323, 78, 32, [bit('ResetBit', tag)])
    s.text('Bęben: 0 brak · 1 obrót · 2 kołysanie · 3 interwał · 4 obrót / kołysanie', 18, 370, 764, 30, 12)
    s.button('Wczytaj program', 18, 417, 238, 40, enabled=False)
    s.button('Zapisz i zastosuj', 274, 417, 238, 40, enabled=False)
    s.text('Kod wyniku', 542, 426, 135)
    s.field('RecipeError', 682, 422, 90, readonly=True)
    s.save(); result.append(s)

    s = Screen(NAMES[2][0], 103)
    s.header('Sterowanie ręczne')
    s.text('Funkcja', 556, 58, 80, 24, 12)
    s.field('ManualFunction', 636, 55, 58, readonly=True, digits=3)
    with (ROOT / 'hmi/manual-functions.csv').open(encoding='utf-8-sig') as stream:
        manual = list(csv.DictReader(stream, delimiter=';'))
    for i, row in enumerate(manual):
        col, line = divmod(i, 7)
        control = s.button(row['code'] + ' · ' + row['label_pl'], 16 + col * 392, 96 + line * 43, 376, 39,
                           [bit('ResetBit', 'GroundHeld'), bit('ResetBit', 'WorkHeld'), set_value('ManualFunction', row['code'])], font=11)
        text_content(control, 'HelpText', 'DE: ' + row['legacy_text_de'].split(' / ', 1)[0])
    s.button('Pozycja podstawowa — przytrzymaj', 16, 415, 376, 46, held='GroundHeld', enabled=False)
    s.button('Pozycja robocza — przytrzymaj', 408, 415, 376, 46, held='WorkHeld', enabled=False)
    s.save(); result.append(s)

    s = Screen(NAMES[3][0], 104)
    s.header('Alarmy i diagnostyka')
    s.button('Otwórz istniejący widok alarmów', 18, 108, 764, 48,
             [bit('ResetBit', 'GroundHeld'), bit('ResetBit', 'WorkHeld'), navigate('WZOR_ROLL')])
    s.text('Połączenie z panelem', 18, 195, 270)
    s.lamp('Aktywne', 'Connected', 418, 192, 345)
    s.text('Receptura · kod wyniku', 18, 248, 270)
    s.field('RecipeError', 418, 243, readonly=True)
    s.text('Nastawa · kod wyniku', 18, 301, 270)
    s.field('ParameterError', 418, 296, readonly=True)
    s.lamp('Błąd konwersji danych', 'ConversionFault', 18, 366, 760, on_color='237, 88, 97')
    s.save(); result.append(s)

    s = Screen(NAMES[4][0], 105)
    s.header('Nastawy serwisowe')
    for label, tag, y, readonly, width in [
        ('Blok danych · 15 = czasy, 19 = liczniki', 'ParameterDb', 112, False, 100),
        ('Numer nastawy · 0–127', 'ParameterIndex', 166, False, 100),
        ('Aktualna wartość [ms / szt.]', 'ParameterCurrentValue', 220, True, 180),
        ('Nowa wartość [ms / szt.]', 'ParameterValue', 274, False, 180)]:
        s.text(label, 18, y + 3, 450)
        s.field(tag, 496, y, width, readonly, digits=10 if width == 180 else 5)
    s.lamp('Nastawa dostępna', 'ParameterSlotPresent', 18, 333, 420)
    s.text('Kod wyniku', 496, 337, 145)
    s.field('ParameterError', 650, 332, 120, readonly=True)
    s.button('Zapisz nastawę', 18, 418, 360, 42, enabled=False)
    s.text('Czasy: ms · liczniki: szt.', 408, 428, 370)
    s.save(); result.append(s)
    return result


def build_preview(screens):
    sections = []
    for screen in screens:
        shapes = []
        for item in screen.items:
            fields = item.find('AttributeList')
            x, y, w, h = [int(fields.findtext(key)) for key in ('Left', 'Top', 'Width', 'Height')]
            if item.tag.endswith('Circle'):
                shapes.append(f'<circle cx="{x+w/2}" cy="{y+h/2}" r="{w/2}" fill="#99a7b9"/>')
                continue
            if item.tag.endswith('IOField'):
                shapes.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="white" stroke="#a3b3c4"/>')
                label = '0'
            else:
                label = ''.join(t.text or '' for t in item.findall("ObjectList/MultilingualText[@CompositionName='TextOff']/ObjectList/MultilingualTextItem/AttributeList/Text/body/p"))
                if not label:
                    label = ''.join(t.text or '' for t in item.findall("ObjectList/MultilingualText[@CompositionName='Text']/ObjectList/MultilingualTextItem/AttributeList/Text/body/p"))
                if item.tag.endswith('Button'):
                    enabled = fields.findtext('Enabled') != 'false'
                    shapes.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" fill="{chr(35)+("314b68" if enabled else "9da8b4")}"/>')
            color = 'white' if item.tag.endswith('Button') else '#21334a'
            size = int(item.findtext('.//Hmi.Globalization.FontItem/AttributeList/FontSize', '13'))
            shapes.append(f'<text x="{x+7}" y="{y+h/2+size/3}" font-size="{size}" fill="{color}">{html.escape(label)}</text>')
        sections.append(f'<section id="{screen.name}"><svg viewBox="0 0 800 480" role="img" aria-label="{screen.name}"><rect width="800" height="480" fill="#f2f5f9"/>' + ''.join(shapes) + '</svg></section>')
    buttons = ''.join(f'<button onclick="show(\'{name}\')">{label}</button>' for name, label in NAMES)
    content = '<!doctype html><html lang="pl"><meta charset="utf-8"><title>ROLL — podgląd HMI</title><style>body{font:16px system-ui;background:#18283b;color:white;margin:24px}nav{display:flex;gap:8px;margin:16px 0}button{padding:12px;border:0;border-radius:6px;cursor:pointer}section{max-width:1100px;display:none}section:first-of-type{display:block}svg{width:100%;font-family:Tahoma,Arial,sans-serif}</style><h1>ROLL · TP900 Comfort</h1><p>Podgląd układu ekranów. Przyciski wewnątrz podglądu nie sterują PLC.</p><nav>' + buttons + '</nav>' + ''.join(sections) + '<script>function show(id){document.querySelectorAll("section").forEach(e=>e.style.display=e.id===id?"block":"none")}</script></html>'
    (ROOT / 'PODGLAD_HMI.html').write_text(content)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    tags = build_tags()
    screens = build_screens()
    build_preview(screens)
    files = []
    for category in ('tags', 'skeletons', 'screens'):
        for path in sorted((OUT / category).glob('*.xml')):
            files.append(dict(path=str(path.relative_to(OUT)), category=category,
                              sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    manifest = dict(format=1, status='offline HMI review import; native V19 compilation pending',
                    connection='ROLL_PLC', table='ROLL_TP900_Tags', tag_count=len(tags),
                    screens=[dict(name=s.name, number=101+i, objects=s.count) for i,s in enumerate(screens)],
                    original_screen_required='WZOR_ROLL', tag_prefix='ROLL_',
                    culture='en-US', captions_language='pl-PL',
                    plc_source_sha256=hashlib.sha256((ROOT / 'ROLL_ALL.scl').read_bytes()).hexdigest(),
                    plc_source_changed=False, native_compiled=False,
                    native_geometry_rules={'Circle': 'Width == Height == 2 * Radius'},
                    native_geometry_feedback='reports/hmi-import-feedback-2026-10-19-070814.json',
                    downloads_performed=False, physical_machine_tested=False,
                    locked_actions=['all_generated_operator_commands', 'editable_fields', 'GroundHeld', 'WorkHeld', 'recipe_load', 'recipe_save_apply', 'parameter_save'],
                    pending=['global heartbeat configuration', 'confirmed payload transfer and request/ack commands',
                             'native alarm definitions and acknowledgement mapping', 'native import/compile', 'physical I/O'],
                    source_provenance=json.loads((SEED/'provenance.json').read_text()),
                    format_references=[dict(url='https://github.com/caoyixian06/TiaMcpServer',
                        commit='44cc125bcd0d3f9611bfe4a1a2e6668932b137e5',
                        paths=['templates/v17-calibration/screen_zonghuamian_export.xml', 'Services/HmiActionCatalog.cs'],
                        scope='Interoperability facts: ActivateScreen argument names, link/literal representation, and SetTag signature; no third-party source code copied; not V19 native validation')], files=files)
    (OUT / 'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
    print(f'Native HMI candidate: {len(tags)} tags; {len(screens)} screens; {sum(s.count for s in screens)} controls. Local V19 import/compile pending.')


if __name__ == '__main__':
    main()
