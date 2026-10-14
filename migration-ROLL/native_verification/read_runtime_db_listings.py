#!/usr/bin/env python3
"""Read complete KH DB15/DB19 native printouts and compare factory reference.

Only parses supplied offline files. Acquisition context is user-provided;
the script performs no online operation and never writes a PLC or TIA project.
"""
from pathlib import Path
import csv
import hashlib
import json
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def rows(path):
    with path.open(encoding='utf-8-sig', newline='') as source:
        return list(csv.DictReader(source, delimiter=';'))


def write(name, values):
    with (HERE / name).open('w', encoding='utf-8-sig', newline='') as target:
        writer = csv.DictWriter(target, fieldnames=list(values[0]), delimiter=';')
        writer.writeheader()
        writer.writerows(values)


def bcd_count(word):
    assert 0 <= word <= 0x0999
    digits = [(word >> shift) & 15 for shift in [0, 4, 8]]
    assert all(d < 10 for d in digits)
    return digits[0] + 10 * digits[1] + 100 * digits[2]


def kt_ms(word):
    base = word >> 12
    assert base in range(4), 'Invalid S5 KT base'
    return bcd_count(word & 0x0fff) * [10, 100, 1000, 10000][base]


def parse_printout(raw, expected_db):
    text = raw.decode('cp850')
    headers = re.findall(r'^\s*DB(\d+)\s+([^\r\n]*?)LEN=(\d+)[^\r\n]*', text, re.MULTILINE)
    assert headers and all(int(h[0]) == expected_db for h in headers)
    assert {int(h[2]) for h in headers} == {137}
    values = re.findall(r'^\s*(\d+):\s+KH\s*=\s*([0-9A-F]{4});\s*$', text, re.MULTILINE)
    assert [int(dw) for dw, _ in values] == list(range(132)), 'Incomplete, duplicated or unordered data words'
    assert len(values) == int(headers[0][2]) - 5
    other = [line for line in text.splitlines() if re.match(r'^\s*\d+:', line)
             and not re.fullmatch(r'\s*\d+:\s+KH\s*=\s*[0-9A-F]{4};\s*', line)]
    assert len(other) == 1 and re.fullmatch(r'\s*132:\s*', other[0]), 'Unexpected data row'
    return dict(block=f'DB{expected_db}', source_file=f'DB{expected_db}ROLS.INI',
                size_bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(),
                header_source_literal=headers[0][1].strip(), header_LEN_words=137,
                data_words=132, block_bytes=274, printed_pages=len(re.findall(r'Page\s+\d+', text)),
                empty_end_marker=132,
                words=[dict(dw=int(dw), raw_hex=value) for dw, value in values]), text


def main():
    snapshots = []
    factory = {(r['block'], int(r['dw'])): r for r in rows(ROOT / 'data_review/timer-counter-defaults.csv')}
    uses = rows(HERE / 'runtime-parameter-use-map.csv')
    snapshot_words = {}
    word_rows, differences, parameters, s7_values = [], [], [], []
    for db, default in [(15, 'DB12'), (19, 'DB16')]:
        raw = (ROOT / f'originals/step5-native/DB{db}ROLS.INI').read_bytes()
        snapshot, text = parse_printout(raw, db)
        snapshots.append(snapshot)
        cleaned = re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]', '', text).replace('\r\n', '\n').replace('\x0c', '\n')
        (HERE / f'DB{db}-native.txt').write_text(cleaned, encoding='utf-8')
        for word in snapshot['words']:
            dw, value = word['dw'], word['raw_hex']
            reference = factory[(default, dw)]['raw_hex'] if dw < 128 else '0000'
            item = dict(runtime_DB=f'DB{db}', runtime_DW=dw, supplied_hex=value,
                        factory_first_preparation_hex=reference, differs_from_first_preparation=value != reference,
                        region='Parameter slots 0..127' if dw < 128 else 'Editor/control state 128..131',
                        source_file=snapshot['source_file'], source_sha256=snapshot['sha256'])
            word_rows.append(item)
            snapshot_words[(f'DB{db}', dw)] = item
            if value != reference:
                differences.append(item)
    for use in uses:
        db, dw = use['runtime_DB'], int(use['runtime_DW'])
        word = snapshot_words[(db, dw)]
        value = int(word['supplied_hex'], 16)
        timer = use['consumer'].startswith('T ')
        decoded = kt_ms(value) if timer else bcd_count(value)
        default_value = int(word['factory_first_preparation_hex'], 16)
        default_decoded = kt_ms(default_value) if timer else bcd_count(default_value)
        item = dict(runtime_DB=db, runtime_DW=dw, consumer=use['consumer'], comment_de=use['consumer_comment'],
                    operation=use['operation'], use_block=use['use_block'], use_network=use['use_network'],
                    supplied_hex=word['supplied_hex'], coding='S5 KT' if timer else 'S5 counter BCD',
                    decoded_value=decoded, decoded_unit='ms' if timer else 'count',
                    factory_hex=word['factory_first_preparation_hex'], factory_decoded_value=default_decoded,
                    differs_from_factory=decoded != default_decoded, source_file=word['source_file'],
                    acquisition_context='User supplied after confirming online CPU access; acquisition timestamp and machine state not provided')
        parameters.append(item)
        s7_values.append(dict(name='Preset_' + use['consumer'].replace(' ', ''),
                              proposed_type='TIME' if timer else 'Int', value=decoded,
                              unit=item['decoded_unit'], legacy_source=f'{db}.DW{dw}',
                              legacy_consumer=use['consumer'], legacy_hex=word['supplied_hex'],
                              evidence=word['source_file']))
    assert len(word_rows) == 264 and len(parameters) == 28
    assert len({(r['runtime_DB'], r['runtime_DW']) for r in parameters}) == 28
    assert all(r['supplied_hex'] == r['factory_first_preparation_hex'] for r in word_rows if r['runtime_DB'] == 'DB15' and r['runtime_DW'] < 128)
    assert [(r['runtime_DW'], r['supplied_hex']) for r in differences if r['runtime_DB'] == 'DB19' and r['runtime_DW'] < 128] == [(1, '0020'), (2, '0014')]
    assert [(r['consumer'], r['decoded_value']) for r in parameters if r['runtime_DB'] == 'DB19'] == [('Z 1', 20), ('Z 2', 14)]
    assert len(differences) == 8
    write('runtime-db-words.csv', word_rows)
    write('runtime-db-differences.csv', differences)
    write('runtime-parameter-values.csv', parameters)
    provenance = dict(received_date='2026-10-12', acquisition_context='Supplied after user confirmed ability to read DB15/DB19 online and received CPU to PC instructions',
                      acquisition_timestamp=None, machine_mode_at_acquisition=None,
                      independent_online_verification=False, sources=snapshots,
                      compared_factory_blocks=['DB12', 'DB16'], parameter_word_changes=dict(DB15=0, DB19=2),
                      editor_control_word_changes=dict(DB15=3, DB19=3),
                      decoded_timer_presets=26, decoded_counter_presets=2,
                      runtime_test=False, TIA_compilation=False)
    (HERE / 'runtime-db-snapshots.json').write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    proposed = dict(scope='Typed parameter reference from supplied native runtime DB listings; not a compiled TIA project or automatic import',
                    received_date='2026-10-12', parameter_count=len(s7_values), parameters=s7_values,
                    editor_state_migrated_as_process_presets=False, hardware_test=False)
    (HERE / 'S7-runtime-parameters.json').write_text(json.dumps(proposed, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    report=['# ROLL — nastawy z otrzymanych DB15 i DB19','',
            'Otrzymano 12 października 2026 po potwierdzeniu przez użytkownika możliwości odczytu CPU→PC. '
            'Oba wydruki wskazują C:ROLLPRST.S5D, mają LEN=137 i komplet 132 słów DW0…DW131. '
            'Puste końcowe `132:` jest znacznikiem końca wydruku, nie dodatkowym słowem.','',
            '**DB15.DW0…127 odpowiada fabrycznemu DB12. DB19 ma dwie zmienione nastawy: Z1=20 i Z2=14, zamiast 5/5.** '
            'Są to presety BCD: KH0020 oznacza 20, KH0014 oznacza 14. Nie stosowano zwykłej interpretacji binarnej.','',
            '| Odbiorca | Źródło | KH z wydruku | Wartość | Domyślna |',
            '|---|---|---|---:|---:|']
    for value in parameters:
        unit=value['decoded_unit']
        supplied_display=f"{value['decoded_value']/1000:g} s" if unit=='ms' else str(value['decoded_value'])
        factory_display=f"{value['factory_decoded_value']/1000:g} s" if unit=='ms' else str(value['factory_decoded_value'])
        report.append(f"| {value['consumer']} | {value['runtime_DB']}.DW{value['runtime_DW']} | {value['supplied_hex']} | {supplied_display} | {factory_display} |")
    report+=['',
             '26 nastaw czasu ma potwierdzony odbiorca KT w programie, a dwa słowa DB19 są presetami liczników. '
             'W szczególności obrót interwałowy korzysta z T116/T117 po 5 s, a krótki ruch w kąpieli z T24=1 s i T25=2 s. '
             'Programy 1/2 mają BADHUB=aus, więc wybrana funkcja krótkiego skoku pozostaje wyłączona.','',
             'DW128…131 są odrębnymi polami edytora/sterowania. DB15 ma wybór DW128=DW129=17 oraz bufor DW130=3360, '
             'czyli kod KT jednej godziny. DB19 ma wybór 1 oraz bufor 0020 odpowiadający presetowi 20. '
             'DW131 wynosi zero w obu blokach. Te sześć różnic względem pierwszego utworzenia DB nie jest sześcioma dodatkowymi nastawami procesu.','',
             'Zachowano oddzielnie cały snapshot oraz wzorzec fabryczny. Czas pobrania z CPU i tryb maszyny nie zostały podane; '
             'plików źródłowych nie zmieniano. Porównanie nie wykonuje połączenia z CPU ani testu programu S7.','',
             'Pliki: [wartości i jednostki](runtime-parameter-values.csv), [264 słowa](runtime-db-words.csv), '
             '[osiem różnic](runtime-db-differences.csv), [źródła i SHA-256](runtime-db-snapshots.json), '
             '[typowane parametry dla przygotowania S7](S7-runtime-parameters.json). Ten JSON jest referencją danych; '
             'nie jest skompilowanym projektem ani automatycznym importem TIA.','']
    (HERE/'DB15_DB19_NASTAWY.md').write_text('\n'.join(report),encoding='utf-8')
    from extract_plant_control import main as refresh_mappings
    refresh_mappings()
    print(json.dumps({k: v for k, v in provenance.items() if k != 'sources'}))


if __name__ == '__main__':
    main()
