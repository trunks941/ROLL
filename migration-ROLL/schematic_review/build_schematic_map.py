#!/usr/bin/env python3
"""Join manually reviewed drawing data with existing static program evidence.

Printed S5 terminals are source evidence, never S7 terminal assignments. This
generator performs no hardware access, address allocation or PLC-code changes.
"""
from pathlib import Path
from collections import Counter
import csv
import hashlib
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream, delimiter=';'))


def write_csv(name, records):
    with (HERE / name).open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]), delimiter=';')
        writer.writeheader()
        writer.writerows(records)


def main():
    observations = json.loads((HERE / 'manual-observations.json').read_text())
    provenance = json.loads((HERE / 'provenance.json').read_text())
    power = json.loads((HERE / 'power-observations.json').read_text())
    provenance2 = json.loads((HERE / 'provenance-part2.json').read_text())
    identification = json.loads((ROOT / 'hardware_review/module-identification.json').read_text())
    sheets = {(s['area'], s['byte']): s for s in observations['sheets']}
    photos = {p['page_in_filename']: p for p in provenance['files']+provenance2['files']}
    assert sorted(photos) == list(range(1,51))
    code = read_csv(ROOT / 'hardware_review/visible-channel-to-S7-draft.csv')
    writers = read_csv(ROOT / 'native_verification/all-output-writer-order.csv')
    channel_rows, group_rows, sheet_rows = [], [], []

    for sheet in observations['sheets']:
        image = photos[sheet['page']]
        sheet_rows.append(dict(page=sheet['page'], drawing=observations['drawing_number'],
            S5_byte=f"{sheet['area']}{sheet['byte']}",
            drawn_signal_paths=len(sheet['channels']),
            signal_or_supply_rail=sheet.get('signal_rail', sheet.get('supply_rail', '')),
            original_image=image['path'], original_image_SHA256=image['sha256'],
            observation_method='Manual visual review; not independently inspected as-built wiring', sheet_type='PLC I/O'))
        if sheet['area'] != 'A':
            continue
        width = 4 if sheet['byte'] >= 24 else 8
        for group, (lp, mp) in enumerate(zip(sheet['module_Lplus_terminals'], sheet['module_M_terminals'])):
            start = group * width
            group_rows.append(dict(page=sheet['page'], S5_byte=f"A{sheet['byte']}",
                group_index_within_byte=group,
                channel_range=f"A{sheet['byte']}.{start}..A{sheet['byte']}.{start+width-1}",
                group_width=width, printed_legacy_Lplus_terminal=lp,
                printed_legacy_M_terminal=mp, supply_rail=sheet['supply_rail'],
                supply_route=sheet['supply_route'],
                pin_status='HOLD: inconsistent drawing' if sheet['byte'] == 25 else 'Printed drawing; actual MLFB/wiring pending',
                S7_group_assignment='', requirement='Preserve supply route and physical contact cutoffs; confirm target group independence'))

    for sheet in power['sheets']:
        photo = photos[sheet['page']]
        sheet_rows.append(dict(page=sheet['page'], drawing=observations['drawing_number'],
            S5_byte='', drawn_signal_paths='', signal_or_supply_rail='',
            original_image=photo['path'], original_image_SHA256=photo['sha256'],
            observation_method='Manual visual review; not independently inspected as-built wiring',
            sheet_type=sheet['title']))
    sheet_rows.sort(key=lambda r:r['page'])

    for channel in code:
        label = channel['S5_front_label']
        area = label[0]
        byte, bit = map(int, label[1:].split('.'))
        sheet = sheets[(area, byte)]
        path = sheet['channels'].get(str(bit))
        count = int(channel['reference_count'])
        if area == 'A' and byte >= 24:
            pin = sheet['printed_channel_terminals'][bit]
            group = bit // 4
        else:
            module_start = 0 if area == 'E' else 16
            pin = 3 + 12 * ((byte-module_start) % 4) + bit
            group = 0
        notes = []
        if label == 'E2.0':
            notes.append('X31 terminal number faint; not supplied as a verified connector pin.')
        if label == 'E8.4':
            notes.append('Controller tag faint on page 33; page 24 identifies A8.4 ST70.31.02, contact via X34:5.')
        if label == 'A19.1':
            notes.append('Page 9: K19.01M also supplies generator 4 mains. Page 44: K19.0M:13-14 gates its coil; K19.01M:13-14 supplies K19.1M remote-control coil. Preserve complete chain.')
        if label == 'A24.4':
            notes.append('Final user choice: retain %Q24.4; original PB13 network 44 condition (A24.0 OR A24.2). Handwritten A16.0 annotation not an as-built confirmation.')
        if label == 'A16.0':
            notes.append('Retain control ON lamp; PB25 network 20 condition (E1.2 OR E3.4), including lamp test.')
        if byte == 25 and area == 'A':
            notes.append('Printed channel pins 27..34 and repeated M=47 conflict with 16x2A reference. Do not use printed pins as verified wiring instructions.')
        matches = [w for w in writers if w['target'] == f'{area} {byte}.{bit}']
        loads = [x for x in power['power_loads'] if label in x['output_addresses']]
        functions = [x for x in power['hardware_functions'] if label in x['PLC_status_addresses']]
        evidence = ('Drawn path and identified code reference' if path and count else
            'Drawn path without identified ordinary-code reference' if path else
            'Identified code reference without drawn load/path' if count else
            'No drawn path and no identified ordinary-code reference; not established disposable')
        photo = photos[sheet['page']]
        reference_pins=identification['module_types']['DQ_2A']
        reference_index=(byte-24)*8+bit if area=='A' and byte>=24 else None
        maker_pin=reference_pins['output_pins'][reference_index] if reference_index is not None else ''
        maker_M=reference_pins['M_pins'][reference_index//4] if reference_index is not None else ''
        channel_rows.append(dict(S5_address=label,
            provisional_S7_address=channel['provisional_S7_address'],
            module_id=channel['module_id'], module_channel_index=channel['channel_index_0_based'],
            page=sheet['page'], drawing=observations['drawing_number'], original_image=photo['path'],
            printed_S5_channel_terminal=pin,
            confirmed_legacy_module_MLFB=channel['confirmed_legacy_module_MLFB'],
            manufacturer_S5_channel_terminal=maker_pin,
            manufacturer_S5_M_terminal=maker_M,
            terminal_status='HOLD: drawing inconsistent; confirmed 454 manufacturer pins listed separately; actual wires unverified' if area == 'A' and byte == 25 else 'Printed S5 drawing; not S7 pin assignment',
            drawn_signal_path=bool(path), device_and_connector=path[0] if path else '',
            drawing_description=path[1] if path else '',
            signal_or_supply_rail=sheet.get('signal_rail', sheet.get('supply_rail', '')),
            output_group_index_within_byte=group if area == 'A' else '',
            printed_S5_Lplus_terminal=sheet['module_Lplus_terminals'][group] if area == 'A' else '',
            printed_S5_M_terminal=sheet['module_M_terminals'][group] if area == 'A' else '',
            symbol=channel['symbol'], code_comment_de=channel['comment_de'],
            code_reference_count=count, referenced_blocks=channel['referenced_blocks'],
            verified_output_writers=' | '.join(f"{w['source_block']} n{w['source_network']} order{w['writer_order_for_output']}" for w in matches),
            verified_output_conditions=' | '.join(w['condition'] for w in matches),
            power_circuit_pages=' | '.join(str(x['page']) for x in loads),
            associated_power_load=' | '.join(x['load'] for x in loads),
            motor_or_heater_power_kW_literal=' | '.join(x['power_kW_literal'] for x in loads),
            motor_or_heater_current_A_literal=' | '.join(x['current_A_literal'] for x in loads),
            rating_interpretation='Power-load rating; not PLC coil current or a DQ sizing value' if loads else '',
            verified_PLC_coil_current_A='',
            hardware_function_pages=' | '.join(str(x['page']) for x in functions),
            external_hardware_devices=' | '.join(x['device'] for x in functions),
            hardware_migration_requirements=' | '.join(x['migration_requirement'] for x in functions),
            comparison=evidence, notes=' | '.join(notes),
            target_module_MLFB='', target_terminal='', verified_as_built_wire='',
            implementation_status='Offline mapping draft; target hardware and wiring not commissioned'))

    discrepancy_rows = []
    for row in channel_rows:
        if row['notes'] or (row['drawn_signal_path'] != bool(row['code_reference_count'])):
            discrepancy_rows.append(dict(S5_address=row['S5_address'], page=row['page'],
                drawing_device=row['device_and_connector'], symbol=row['symbol'],
                comparison=row['comparison'], finding=row['notes'],
                resolution='Verify existing wiring/device/MLFB; retain source evidence; no automatic signal deletion or remap'))

    policy_rows = []
    for address, role in [('A24.4', 'Drum fan'), ('A16.0', 'Control ON lamp / lamp test')]:
        row = next(r for r in channel_rows if r['S5_address'] == address)
        policy_rows.append(dict(S5_address=address, target_S7_address=row['provisional_S7_address'], role=role,
            original_writer=row['verified_output_writers'], original_condition=row['verified_output_conditions'],
            drawing_page=row['page'], decision='Retain original output and condition',
            as_built_wiring_confirmed=False, code_or_hardware_action_performed=False))

    outputs = {'sheet-index.csv': sheet_rows, 'channel-wire-map-draft.csv': channel_rows,
        'output-potential-groups.csv': group_rows, 'drawing-code-discrepancies.csv': discrepancy_rows,
        'fan-and-lamp-decision.csv': policy_rows}
    for name, records in outputs.items():
        write_csv(name, records)

    assert len(sheet_rows) == 50 and len(channel_rows) == 208 and len(group_rows) == 12
    assert len({r['S5_address'] for r in channel_rows}) == 208
    drawn = Counter(r['S5_address'][0] for r in channel_rows if r['drawn_signal_path'])
    assert drawn == {'E': 83, 'A': 50}
    without_code = {r['S5_address'] for r in channel_rows if r['drawn_signal_path'] and not r['code_reference_count']}
    without_path = {r['S5_address'] for r in channel_rows if not r['drawn_signal_path'] and r['code_reference_count']}
    assert without_code == {'E4.6', 'E6.6'} and without_path == {'A16.7'}
    assert all(not r['target_module_MLFB'] and not r['target_terminal'] for r in channel_rows)
    assert observations['user_fan_choice']['target_output'] == '%Q24.4'
    assert policy_rows[0]['original_condition'] == '(A24.0 OR A24.2)'
    assert policy_rows[1]['original_condition'] == '(E1.2 OR E3.4)'
    assert len([r for r in channel_rows if r['terminal_status'].startswith('HOLD')]) == 8
    result = dict(date=identification['date'], source='50 manually reviewed photographs and user-confirmed legacy module types',
        source_observations_SHA256=hashlib.sha256((HERE/'manual-observations.json').read_bytes()).hexdigest(),
        power_observations_SHA256=hashlib.sha256((HERE/'power-observations.json').read_bytes()).hexdigest(),
        received_pages=sorted(photos), missing_pages=[],
        generated_CSV_rows={k:len(v) for k,v in outputs.items()}, drawn_input_paths=83, drawn_output_paths=50,
        drawn_paths_without_code=sorted(without_code), code_without_drawn_path=sorted(without_path),
        output_potential_groups=12, A25_terminal_assignments_held=8,
        fan_target='%Q24.4', lamp_target='%Q16.0', fan_and_lamp_conditions='Original conditions retained',
        installed_legacy_IO_types_confirmed=True, coil_ratings_will_not_be_requested_again=True,
        as_built_wiring_verified=False, final_S7_module_selection=False,
        PLC_code_changed=False, hardware_action_performed=False, consistency_result='Passed')
    (HERE/'schematic-evidence.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
