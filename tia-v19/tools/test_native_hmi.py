#!/usr/bin/env python3
"""Cross-reference, geometry and command-lock checks for native HMI candidates.

Does not replace the installed Siemens XML importer or WinCC compiler.
"""
from pathlib import Path
import hashlib
import json
import xml.etree.ElementTree as ET
import generate_native_hmi as gen


def main():
    manifest = json.loads((gen.OUT / 'manifest.json').read_text())
    assert manifest['native_compiled'] is False
    assert hashlib.sha256((gen.ROOT / 'ROLL_ALL.scl').read_bytes()).hexdigest() == manifest['plc_source_sha256']
    docs = {}
    for entry in manifest['files']:
        path = gen.OUT / entry['path']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == entry['sha256']
        doc = ET.parse(path)
        ids = [el.get('ID') for el in doc.iter() if el.get('ID') is not None]
        assert len(ids) == len(set(ids)), path
        assert all(el.get('TargetID') in (None, '@OpenLink') for el in doc.iter())
        docs[entry['path']] = doc
    table = docs['tags/ROLL_TP900_Tags.xml']
    tags = {}
    for item in table.findall('.//Hmi.Tag.Tag'):
        name = item.findtext('AttributeList/Name')
        kind = item.findtext('LinkList/DataType/Name')
        assert name not in tags
        assert int(item.findtext('AttributeList/Length')) == {'Bool': 1, 'Int': 2, 'DInt': 4}[kind]
        assert item.findtext('LinkList/Connection/Name') == 'ROLL_PLC'
        assert item.findtext('LinkList/ControllerTag/Name')
        tags[name] = kind
    assert len(tags) == manifest['tag_count'] == 53
    names = {entry['name'] for entry in manifest['screens']} | {'WZOR_ROLL'}
    counts = dict(objects=0, circles=0, tag_links=0, navigation_actions=0, manual_selectors=0, held_buttons=0, locked_buttons=0)
    seen_numbers = set()
    for spec in manifest['screens']:
        path = 'screens/' + spec['name'] + '.xml'
        doc = docs[path]
        screen = doc.find('Hmi.Screen.Screen')
        assert screen.findtext('AttributeList/Name') == spec['name']
        number = int(screen.findtext('AttributeList/Number'))
        assert number == spec['number'] and number not in seen_numbers
        seen_numbers.add(number)
        skeleton = docs['skeletons/' + spec['name'] + '.xml']
        assert not list(skeleton.iterfind(".//*[@CompositionName='ScreenItems']"))
        items = list(screen.iterfind(".//*[@CompositionName='ScreenItems']"))
        assert len(items) == spec['objects']
        counts['objects'] += len(items)
        for item in items:
            fields = item.find('AttributeList')
            x,y,w,h = [int(fields.findtext(key)) for key in ('Left','Top','Width','Height')]
            assert 0 <= x < 800 and 0 <= y < 480 and w > 0 and h > 0 and x+w <= 800 and y+h <= 480, (path,fields.findtext('ObjectName'))
            if item.tag == 'Hmi.Screen.Circle':
                counts['circles'] += 1
                radius = int(fields.findtext('Radius'))
                assert w == h == 2 * radius, (path, fields.findtext('ObjectName'), w, h, radius)
            for tag in item.findall('.//Hmi.Dynamic.TagConnectionDynamic/LinkList/Tag/Name') + item.findall('.//Hmi.Dynamic.TagElementTrigger/LinkList/Tag/Name'):
                assert tag.text in tags, (path,tag.text)
                counts['tag_links'] += 1
            entries = item.findall('.//Hmi.Event.FunctionListEntry')
            functions = []
            for entry in entries:
                function = entry.findtext('AttributeList/Name')
                functions.append(function)
                assert function in {'SetBit','ResetBit','SetTag','ActivateScreen'}
                parameters = entry.findall('ObjectList/Hmi.Event.FunctionListEntryParameter')
                for arg in parameters:
                    key = arg.findtext('AttributeList/Name')
                    linked = arg.findtext('LinkList/Value/Name')
                    literal = arg.find('AttributeList/Value')
                    if key == 'Tag':
                        assert linked in tags
                        assert linked not in {'ROLL_RecipeRequest','ROLL_ParameterRequest','ROLL_Heartbeat'}
                        if function in {'SetBit','ResetBit'}:
                            assert tags[linked] == 'Bool'
                    elif key == 'Screen name':
                        assert linked in names
                    else:
                        assert literal is not None and literal.get('Type') in {'System.Int32','System.Double'}
                        float(literal.text)
                if function == 'ActivateScreen':
                    counts['navigation_actions'] += 1
                    assert functions[:2] == ['ResetBit','ResetBit']
                if function == 'SetTag' and parameters[0].findtext('LinkList/Value/Name') == 'ROLL_ManualFunction':
                    counts['manual_selectors'] += 1
                    assert functions[:2] == ['ResetBit','ResetBit']
            if item.tag == 'Hmi.Screen.Button' and fields.findtext('Enabled') == 'false':
                counts['locked_buttons'] += 1
            if item.tag == 'Hmi.Screen.Button' and 'ActivateScreen' not in functions:
                assert fields.findtext('Enabled') == 'false', 'Review import must not execute operator commands'
            if item.tag == 'Hmi.Screen.IOField' and fields.findtext('Mode') == 'InOutput':
                assert fields.findtext('Enabled') == 'false', 'Review import must not edit PLC payloads'
            if item.tag == 'Hmi.Screen.Button' and item.find("ObjectList/Hmi.Event.Event/AttributeList/Name") is not None:
                events = {e.findtext('AttributeList/Name'): e for e in item.findall('ObjectList/Hmi.Event.Event')}
                if 'Press' in events:
                    counts['held_buttons'] += 1
                    assert fields.findtext('Enabled') == 'false'
                    assert events['Press'].findtext('.//Hmi.Event.FunctionListEntry/AttributeList/Name') == 'SetBit'
                    assert events['Release'].findtext('.//Hmi.Event.FunctionListEntry/AttributeList/Name') == 'ResetBit'
        assert all(item.tag != 'Hmi.Screen.AlarmView' for item in items), 'Do not invent an unsupported alarm view export'
    assert counts['objects'] == 137 and counts['manual_selectors'] == 14
    assert counts['circles'] == 15
    assert counts['held_buttons'] == 2 and counts['locked_buttons'] == 25
    assert counts['navigation_actions'] == 26
    result = dict(success=True, native_tia_executed=False, native_hmi_compiled=False,
                  tag_count=len(tags), screen_count=5, **counts,
                  scope='candidate XML identities, hashes, geometry, tag/screen references, selector ordering and locks; not Siemens schema/native runtime validation',
                  native_manifest_sha256=hashlib.sha256((gen.OUT/'manifest.json').read_bytes()).hexdigest())
    (gen.ROOT/'reports/native-hmi-checks.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
