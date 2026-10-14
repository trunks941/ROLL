#!/usr/bin/env python3
"""Check source preservation and current static migration artifacts.

No PLC scan, process, timer, hardware or TIA execution is performed.
"""
from pathlib import Path
import csv
import hashlib
import json
import re
from urllib.parse import unquote

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
RESULT = HERE / 'partia5-artifact-checks.json'


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def rows(path):
    with path.open(encoding='utf-8-sig', newline='') as source:
        return list(csv.DictReader(source, delimiter=';'))


def main():
    preserved = {}

    def preserve(path, expected_sha, expected_size=None):
        data = path.read_bytes()
        assert hashlib.sha256(data).hexdigest() == expected_sha, path
        if expected_size is not None:
            assert len(data) == expected_size, path
        relative = str(path.relative_to(ROOT))
        if relative in preserved:
            assert preserved[relative] == expected_sha
        preserved[relative] = expected_sha
        return data

    for item in load(ROOT / 'analysis/inventory.json')['files']:
        preserve(ROOT / item['path'], item['sha256'], item['bytes'])
    inventory = load(HERE / 'native-files-inventory.json')
    assert len(inventory['verified_native_files']) == 36
    assert len(inventory['partial_native_files']) == 1
    for item in inventory['verified_native_files'] + inventory['partial_native_files']:
        preserve(ROOT / 'originals/step5-native' / item['source_file'], item['sha256'], item['size_bytes'])
    manual = load(ROOT / 'reference_manuals/manual-provenance.json')
    preserve(ROOT / 'reference_manuals' / manual['filename'], manual['sha256'])
    comtext = load(ROOT / 'comtext_review/provenance.json')
    preserve(ROOT / comtext['source'], comtext['sha256'], comtext['size_bytes'])
    assert len(preserved) == 48
    received = load(HERE / 'partia5-native-received.json')
    assert len(received) == 8
    for item in received:
        preserve(ROOT / 'originals/step5-native' / item['file'], item['sha256'], item['bytes'])

    statuses = rows(HERE / 'program-native-verification-status.csv')
    catalog = rows(ROOT / 'analysis/s5-program-blocks.csv')
    code = {r['kind'] + r['number']: r for r in catalog if r['kind'] != 'DB'}
    assert len(statuses) == len(code) == 49
    assert {r['block'] for r in statuses} == set(code)
    full = {r['block'] for r in inventory['verified_native_files']}
    partial = {r['block'] for r in inventory['partial_native_files']}
    assembler = {b for b, r in code.items() if r['assembler_flag'] == 'True'}
    missing = set(code) - full - partial - assembler
    assert partial == {'FB51'} and len(assembler) == 5
    assert missing == {'FB0', 'PB19', 'PB20', 'PB21', 'PB23', 'PB24', 'PB25'}
    assert inventory['counts']['unique_full_native_source_files'] == 35
    assert inventory['counts']['unique_all_native_source_files'] == 36
    assert inventory['counts']['ordinary_code_blocks_without_full_listing'] == 8
    for row in statuses:
        if row['block'] in full:
            source = next(r for r in inventory['verified_native_files'] if r['block'] == row['block'])
            assert row['native_source'] == source['source_file']
            assert 'confirmed' in row['native_status']

    summary = load(HERE / 'automation-control-comparison.json')
    assert summary['total_networks'] == 220
    assert summary['native_addressed_STL_positions'] == 13
    assert summary['total_offline_positions_in_context'] == 2334
    assert summary['total_offline_executing_instructions'] == 2119
    new_blocks = {r['block'] for r in summary['blocks']}
    assert new_blocks == {'PB7', 'PB8', 'PB9', 'PB10', 'PB14', 'PB15', 'PB50', 'PB51', 'PB52'}
    assert load(HERE / 'FBD-blocks-comparison.json')['total_networks'] == 472
    for block in summary['blocks']:
        detail = load(HERE / f"{block['block']}-comparison.json")
        assert not detail['errors']
        assert detail['matched'] == detail['networks'] == len(detail['reviews'])
        assert all(r['result'] == 'Match' for r in detail['reviews'])
        source = (ROOT / 'originals/step5-native' / detail['source_file']).read_bytes()
        scope = detail['source_scope']
        assert 0 <= scope['source_byte_start'] < scope['source_byte_end'] <= len(source)
        assert len(rows(HERE / f"{block['block']}-network-comparison.csv")) == block['networks']
    pb51, pb52 = [load(HERE / f'{b}-comparison.json') for b in ['PB51', 'PB52']]
    assert pb51['source_file'] == pb52['source_file'] == 'PB51ROLS.INI'
    assert pb51['sha256'] == pb52['sha256']
    assert pb51['source_scope']['source_byte_start'] == 0
    assert pb51['source_scope']['source_byte_end'] == pb52['source_scope']['source_byte_start'] == 3738
    assert pb52['source_scope']['source_byte_end'] == 13537

    raw = (ROOT / 'originals/s5/s5/1998_07_03/04201@ST.S5D').read_bytes()
    decoded = [r for r in rows(ROOT / 'offline_decoder/instructions.csv') if r['block'] in new_blocks]
    assert len(decoded) == 2334
    for row in decoded:
        start, size = int(row['absolute_offset']), int(row['size'])
        assert raw[start:start + size].hex().upper() == row['raw_hex']
        assert start == int(code[row['block']]['offset']) + int(row['offset'])

    evidence = load(HERE / 'automation-data-evidence.json')
    for name, count in evidence['table_rows'].items():
        assert len(rows(HERE / name)) == count
    assert evidence['automatic_step_bits'] == 111
    steps = rows(HERE / 'automatic-steps-SR.csv')
    assert len(steps) == 222
    assert len({r['target'] for r in steps}) == 111
    timers = rows(HERE / 'automation-timer-map.csv')
    assert len(timers) == 30
    assert sum(r['operation'] in ['SE', 'SA'] for r in timers) == 29
    assert sum(r['operation'] == 'R' for r in timers) == 1
    assert next(r for r in timers if r['target'] == 'T 16')['constant_preset_ms'] == '3600000'
    assert next(r for r in timers if r['target'] == 'T 13')['constant_preset_ms'] == '2000'
    assert next(r for r in timers if r['target'] == 'T 11')['constant_preset_ms'] == '8000'
    track = rows(HERE / 'tracking-state-SR.csv')
    assert {r['target'] for r in track} == {'M 70.2', 'M 70.3', 'M 70.4', 'M 70.5', 'M 70.6', 'M 70.7', 'M 71.0'}
    assert all('M73.7' in r['condition'] for r in track if r['operation'] == 'R')

    # Existing recipe CSV must remain byte-for-byte identical, not just numerically equal.
    recipe_bytes = (ROOT / 'operator_recipes/operator-recipes.csv').read_bytes()
    assert hashlib.sha256(recipe_bytes).hexdigest() == '9aa33392a8a92f27c472f8b085d48118ed1341972d6a343da8689013991d88db'
    assert len(rows(ROOT / 'operator_recipes/operator-recipes.csv')) == 20
    recipes = load(ROOT / 'operator_recipes/operator-recipes.json')['records']
    assert [r['actual_program_number'] for r in recipes] == [1, 2]
    assert all(r['complete'] and len(r['fields']) == 10 for r in recipes)
    assert [r['fields'] for r in recipes][0] == [r['fields'] for r in recipes][1]

    test_text = (HERE / 'fbd-reader-test-results.txt').read_text()
    assert re.search(r'Ran 10 tests\b', test_text) and test_text.rstrip().endswith('OK')
    assert test_text.count(' ... ok') == 10
    json_count = 0
    for path in ROOT.rglob('*.json'):
        load(path)
        json_count += 1
    local_links = 0
    for path in ROOT.rglob('*.md'):
        for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', path.read_text(encoding='utf-8')):
            if re.match(r'^[a-z]+:', target) or target.startswith('#'):
                continue
            target = unquote(target.split('#')[0].strip('<>'))
            destination = path.parent / target
            assert destination.exists() or destination.resolve() == RESULT.resolve(), (str(path), target)
            local_links += 1
    result = dict(date='2026-10-12', scope='Source preservation and static artifact consistency; no PLC runtime, hardware or TIA compilation',
                  preserved_unique_source_files=len(preserved), preserved_source_sha256=preserved,
                  new_native_files=8, new_complete_blocks=9,
                  code_block_status_counts=dict(full=36, partial=1, ordinary_missing=7, assembler=5),
                  unique_full_native_source_files=35, unique_all_native_source_files=36,
                  new_networks_compared=220, all_fifteen_FBD_blocks_networks_compared=472,
                  new_addressed_STL_positions=13, new_MC5_positions_cross_checked_against_original_bytes=len(decoded),
                  new_MC5_executing_positions_context=2119, new_MC5_BLD_positions_context=215,
                  shared_source='PB51/PB52: same preserved source/hash; contiguous non-overlapping byte scopes',
                  new_table_rows=evidence['table_rows'], automatic_step_bits=111,
                  reader_controls_passed=10, operator_recipe_fields='20 rows unchanged byte-for-byte; program numbers and values preserved',
                  FB51='Still partial; body and jump targets unresolved',
                  markdown_local_links_checked=local_links, JSON_files_parsed=json_count, result='Passed')
    RESULT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k != 'preserved_source_sha256'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
