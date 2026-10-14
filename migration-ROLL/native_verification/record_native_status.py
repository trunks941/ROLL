#!/usr/bin/env python3
"""Record full native comparisons separately from the limited FB51 prefix.

Uses only local copies and existing comparison evidence. Does not alter source
files, decode the missing FB51 body, or connect to PLC/HMI hardware.
"""
from pathlib import Path
import csv
import hashlib
import json
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as source:
        return list(csv.DictReader(source, delimiter=';'))


def write_json(name, value):
    (HERE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    native = ROOT / 'originals/step5-native'
    raw = (native / 'FB51ROLS.INI').read_bytes()
    assert len(raw) == 478 and raw[:239] == raw[239:]
    text = raw.decode('cp850')
    addressed = re.findall(r'^([0-9A-F]{4})\s*:(.*?)\r?$', text, re.MULTILINE)
    assert [(a, c.strip()) for a, c in addressed] == [('0005', 'JU  =M001'), ('0006', 'BE')] * 2
    assert not re.search(r'LEN=\d+|^\s*[0-9A-F]{4}\s+M001\s*:', text, re.MULTILINE)
    decoded = {int(r['offset']): r for r in read_csv(ROOT / 'offline_decoder/instructions.csv') if r['block'] == 'FB51'}
    directory = read_csv(ROOT / 'analysis/s5-program-blocks.csv')
    block = next(r for r in directory if r['kind'] == 'FB' and r['number'] == '51')
    assert int(block['bytes']) == 1052
    assert decoded[20]['command'] == 'SPA=' and decoded[20]['raw_hex'] == '2D02'
    assert decoded[22]['command'] == 'BE' and decoded[22]['raw_hex'] == '6500'
    confirmation = json.loads((HERE / 'user-confirmations.json').read_text())['FB51_editor_view']
    cleaned = re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]', '', text).replace('\r\n', '\n').replace('\x0c', '\n')
    (HERE / 'FB51-native-partial.txt').write_text(cleaned, encoding='utf-8')
    result = dict(block='FB51', source_file='FB51ROLS.INI', size_bytes=len(raw),
                  sha256=hashlib.sha256(raw).hexdigest(), archived_block_bytes=1052,
                  repeated_reports=2, unique_native_positions=2, fully_verified=False,
                  prefix_mnemonics_and_addresses_match=True, jump_targets_verified=False,
                  prefix=[dict(native_word_address='0005', block_byte_offset=20,
                               native_instruction='JU =M001', raw_hex='2D02',
                               offline_target_block_byte_offset=24,
                               native_target_status='M001 is not defined in the supplied listing'),
                          dict(native_word_address='0006', block_byte_offset=22,
                               native_instruction='BE', raw_hex='6500')],
                  editor_confirmation=confirmation,
                  unresolved_tail=dict(jump_offset='0416', offline_target='041A',
                                       overlapping_linear_instruction='0418: L KH 6500',
                                       native_confirmation=False),
                  limitations=['Body, length and tail are not exposed by the native listing.',
                               'The missing target label prevents native verification of even the prefix jump target.',
                               'The duplicate prefix is not an additional verified block.',
                               'No protection mechanism is inferred; no whole-block or runtime validation.'])
    write_json('FB51-partial-comparison.json', result)
    inventory = json.loads((HERE / 'native-files-inventory.json').read_text())
    verified = {r['block']: r for r in inventory['verified_native_files']}
    for r in json.loads((HERE / 'addressed-blocks-comparison.json').read_text())['blocks']:
        verified[r['block']] = dict(block=r['block'], source_file=r['source_file'],
                                    size_bytes=r['size_bytes'], sha256=r['sha256'],
                                    method='All addressed native positions compared',
                                    evidence=f"{r['block']}-comparison.json")
        if r.get('unaddressed_final_instructions'):
            verified[r['block']]['method']='Native STL: 118 addressed positions and final unaddressed BE compared'
    fbd=json.loads((HERE/'PB16-comparison.json').read_text())
    assert fbd['networks_manually_compared']==34
    verified['PB16']={k:fbd[k] for k in ['block','source_file','size_bytes','sha256','method']}
    verified['PB16']['evidence']='PB16-comparison.json'
    process=json.loads((HERE/'FBD-blocks-comparison.json').read_text())
    for r in process['blocks']:
        assert r['matched']==r['networks']
        verified[r['block']]={k:r[k] for k in ['block','source_file','size_bytes','sha256','method','source_scope']}
        verified[r['block']]['evidence']=f"{r['block']}-comparison.json"
    assert len(verified) == 42 and 'FB51' not in verified
    for r in verified.values():
        contents = (native / r['source_file']).read_bytes()
        assert len(contents) == r['size_bytes']
        assert hashlib.sha256(contents).hexdigest() == r['sha256']
    inventory['verified_native_files'] = list(verified.values())
    inventory['partial_native_files'] = [dict(block='FB51', source_file=result['source_file'],
        size_bytes=result['size_bytes'], sha256=result['sha256'], fully_verified=False,
        method='Only two unique prefix positions; jump target and body not verified',
        evidence='FB51-partial-comparison.json')]
    inventory['counts'] = dict(full_code_blocks=42, partial_code_blocks=1,
                               ordinary_code_blocks_without_full_listing=2,
                               ordinary_code_blocks_without_any_native_listing=1,
                               assembler_code_blocks=5,
                               unique_full_native_source_files=len({r['source_file'] for r in verified.values()}),
                               unique_all_native_source_files=len({r['source_file'] for r in verified.values()} | {result['source_file']}))
    snapshot_path=HERE/'runtime-db-snapshots.json'
    inventory['runtime_data_files']=[]
    if snapshot_path.exists():
        for source in json.loads(snapshot_path.read_text())['sources']:
            inventory['runtime_data_files'].append({**{k:source[k] for k in ['block','source_file','size_bytes','sha256','data_words']},
                'method':'Complete native KH printout parsed; parameter KT/BCD decoding checked separately',
                'evidence':'runtime-db-snapshots.json'})
    inventory['counts']['runtime_DBs_received']=len(inventory['runtime_data_files'])
    inventory['counts']['unique_native_source_files_including_runtime_DBs']=len({r['source_file'] for r in verified.values()} | {result['source_file']} | {r['source_file'] for r in inventory['runtime_data_files']})
    write_json('native-files-inventory.json', inventory)
    status_path = HERE / 'program-native-verification-status.csv'
    statuses = read_csv(status_path)
    for r in statuses:
        if r['block'] in verified:
            if r['block']=='PB16':
                r['native_status']='Native FBD confirmed; all 34 networks manually compared'
            elif r['block'] in {x['block'] for x in process['blocks']}:
                r['native_status']='Native FBD/mixed networks confirmed; complete static action-expression comparison'
            elif r['block']=='FB89':
                r['native_status']='Native STL confirmed; 118 addressed positions plus final unaddressed BE'
            elif r['block'] != 'OB1':
                r['native_status'] = 'All addressed native positions confirmed'
            r['native_source'] = verified[r['block']]['source_file']
        elif r['block'] == 'FB51':
            r['native_status'] = 'Partial prefix only; editor also exposes two lines; body and jump targets unverified'
            r['native_source'] = 'FB51ROLS.INI'
    assert len(statuses) == 49
    with status_path.open('w', encoding='utf-8-sig', newline='') as output:
        writer = csv.DictWriter(output, fieldnames=list(statuses[0]), delimiter=';')
        writer.writeheader()
        writer.writerows(statuses)
    print(json.dumps(inventory['counts']))


if __name__ == '__main__':
    main()
