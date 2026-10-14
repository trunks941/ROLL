#!/usr/bin/env python3
"""Compare manually recorded photo labels with existing verified program data.

Does not infer wiring from LEDs, map unseen addresses to hardware, choose exact
catalog numbers, change PLC I/O, or assume unsupported references are unused.
"""
from pathlib import Path
from collections import defaultdict
import csv
import hashlib
import json

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


def main():
    observations = json.loads((HERE / 'photo-observations.json').read_text())
    identification = json.loads((HERE / 'module-identification.json').read_text())
    modules = [dict(m) for m in observations['modules']]
    for module in modules:
        group = identification['rack_type_assignments'].get(module['id'])
        if group:
            module['catalog_number'] = identification['module_types'][group]['MLFB']
            module['catalog_status'] = 'Type confirmed by user and S5 manual; rack assignment from matching DI/DQ width/current class'
    symbols = {(r['area'], r['address']): r for r in rows(ROOT / 'analysis/symbols.csv')}
    references = defaultdict(list)
    for instruction in rows(ROOT / 'offline_decoder/instructions.csv'):
        if instruction['operand_area'] in ['E', 'A']:
            references[instruction['operand']].append(instruction)
    full = {r['block'] for r in json.loads((ROOT / 'native_verification/native-files-inventory.json').read_text())['verified_native_files']}
    module_rows, channel_rows, unsupported = [], [], []
    for module in modules:
        row = {**module, 'address_basis': observations['address_basis']}
        row['address_label_range'] = f"{module['area']}{module['start_byte']}.0..{module['area']}{module['end_byte']}.7" if module['channels'] else ''
        row['code_referenced_channels'] = 0
        for channel in range(module['channels']):
            byte, bit = module['start_byte'] + channel // 8, channel % 8
            area, address = module['area'], f'{byte}.{bit}'
            operand = area + ' ' + address
            uses = references.get(operand, [])
            symbol = symbols.get((area, address), {})
            row['code_referenced_channels'] += bool(uses)
            channel_rows.append(dict(module_id=module['id'], position_from_left=module['position_from_left'],
                channel_index_0_based=channel, S5_front_label=area + address,
                label_nominal_signal_VDC=module['nominal_signal_VDC'],
                label_current_per_channel_A=module['label_current_per_channel_A'],
                symbol=symbol.get('symbol', ''), comment_de=symbol.get('comment_de', ''),
                reference_count=len(uses), referenced_blocks=' | '.join(sorted({r['block'] for r in uses})),
                write_count=sum(r['command'] in ['=', 'S', 'R'] for r in uses),
                provisional_S7_address='%' + ('I' if area == 'E' else 'Q') + address,
                confirmed_legacy_module_MLFB=module['catalog_number'],
                target_module_MLFB='', target_terminal='', schematic_wire_reference='',
                status='Front-label candidate; see schematic_review/channel-wire-map-draft.csv; actual module address, target terminals and wires pending verification/MLFB',
                unreferenced_limit='No identified ordinary-code reference does not establish an unwired or disposable channel'))
        module_rows.append(row)
    for operand, uses in sorted(references.items(), key=lambda item: (item[0].split()[0], int(item[0].split()[1].split('.')[0]), int(item[0].split('.')[1]))):
        area, address = operand.split()
        byte = int(address.split('.')[0])
        found = any(m['area'] == area and m['channels'] and m['start_byte'] <= byte <= m['end_byte'] for m in modules)
        if found:
            continue
        symbol = symbols.get((area, address), {})
        unsupported.append(dict(S5_address=area + address, area=area, symbol=symbol.get('symbol', ''),
            comment_de=symbol.get('comment_de', ''), reference_count=len(uses),
            referenced_blocks=' | '.join(sorted({r['block'] for r in uses})),
            commands=' | '.join(sorted({r['command'] for r in uses})),
            write_count=sum(r['command'] in ['=', 'S', 'R'] for r in uses),
            native_writers_pending=' | '.join(sorted({r['block'] for r in uses if r['block'] not in full})),
            physical_module_on_photo='', provisional_physical_S7_address='',
            user_hardware_scope='User confirms photo shows the entire module set',
            assessment='Outside front label ranges; options/residual logic are possible, not established unused',
            required_resolution='Verify hardware addresses/wiring and evaluate native branch conditions; retain code evidence'))
    write('central-rack-modules.csv', module_rows)
    write('visible-channel-to-S7-draft.csv', channel_rows)
    write('addresses-outside-photo.csv', unsupported)
    requirements = [
        dict(group='DI', required_channel_capacity=128, nominal_signal_VDC=24,
             legacy_label_current_per_channel_A='', draft_S7_family='SM 521 / appropriate S7-1500 digital input modules',
             draft_quantity_and_width='4 x 32-channel DI, preserving observed capacity',
             draft_address_ranges='%I0.0..%I15.7', final_MLFB='',
             pending='Target MLFB/input response and verified wire mapping; legacy MLFB 6ES5 430-7LA12 confirmed; 50 drawing pages received'),
        dict(group='DQ_0_5A', required_channel_capacity=64, nominal_signal_VDC=24,
             legacy_label_current_per_channel_A=0.5, draft_S7_family='SM 522 / appropriate S7-1500 digital output modules',
             draft_quantity_and_width='4 x 16-channel DQ candidate, requiring separately supplied groups of 8; 2 x 32 is not the assumed replacement',
             draft_address_ranges='%Q16.0..%Q23.7', final_MLFB='',
             pending='Target group independence, inductive-load capability/thermal limits and protection covering legacy 451 envelope; actual coil data will not be requested again'),
        dict(group='DQ_2A', required_channel_capacity=16, nominal_signal_VDC=24,
             legacy_label_current_per_channel_A=2, draft_S7_family='S7-1500 DQ appropriate for the verified loads, or defined interface relays',
             draft_quantity_and_width='2 x 8-channel DQ at 2 A candidate; official group/thermal/load data pending; no reduction to 0.5 A',
             draft_address_ranges='%Q24.0..%Q25.7', final_MLFB='',
             pending='Target per-channel/group thermal and inductive-load ratings covering legacy 454 envelope; retain 2 A class; actual coil data will not be requested again')]
    write('S7-IO-requirements.csv', requirements)
    visible_i = [r for r in channel_rows if r['S5_front_label'].startswith('E')]
    visible_q = [r for r in channel_rows if r['S5_front_label'].startswith('A')]
    outside_i = [r for r in unsupported if r['area'] == 'E']
    outside_q = [r for r in unsupported if r['area'] == 'A']
    assert len(visible_i) == 128 and len(visible_q) == 80
    assert len({r['S5_front_label'] for r in channel_rows}) == len(channel_rows) == 208
    assert len({r['provisional_S7_address'] for r in channel_rows}) == 208
    assert sum(bool(r['reference_count']) for r in visible_i) == 81
    assert sum(bool(r['reference_count']) for r in visible_q) == 51
    assert len(outside_i) == 16 and len(outside_q) == 12
    assert all(not r['provisional_physical_S7_address'] for r in unsupported)
    assert all(not r['target_terminal'] and not r['target_module_MLFB'] for r in channel_rows)
    assert sum(r['write_count'] > 0 for r in outside_q) == 9
    assert all(not r['native_writers_pending'] for r in unsupported)
    assert not observations['additional_IO_modules_confirmed_by_user']
    result = dict(date=identification['date'], scope='Photo, user-confirmed S5 types and static program comparison; not a verified wiring plan or purchase order',
        observation_file_SHA256=hashlib.sha256((HERE/'photo-observations.json').read_bytes()).hexdigest(),
        physical_address_basis=observations['address_basis'],
        observed_input_capacity=128, observed_output_capacity=80,
        IO_modules=7, DI_modules=4, DQ_modules=3, visible_channel_rows=208,
        identified_code_input_bits_in_photo_ranges=81, identified_code_output_bits_in_photo_ranges=51,
        identified_code_bits_outside_photo_ranges=dict(E=16, A=12),
        outside_output_bits_with_identified_write=9,
        outside_addresses_assigned_to_physical_S7_channels=False,
        installed_IO_module_types_confirmed=True,
        confirmed_IO_MLFBs=sorted({m['catalog_number'] for m in modules if m['kind'] in ['DI','DQ']}),
        target_module_catalog_numbers_final=False, coil_ratings_will_not_be_requested_again=True,
        module_catalog_numbers_final=False, wiring_verified=False, additional_modules=False,
        user_confirmed_complete_hardware=True,
        memory_cartridge_visible_label='EPROM',
        generated_CSV_rows={'central-rack-modules.csv':len(module_rows),
                           'visible-channel-to-S7-draft.csv':len(channel_rows),
                           'addresses-outside-photo.csv':len(unsupported),
                           'S7-IO-requirements.csv':len(requirements)},
        consistency_result='Passed')
    (HERE/'hardware-evidence.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
