#!/usr/bin/env python3
"""Extract compared plant actions and factory-only runtime DB reference data.

Never treats factory defaults as actual online settings. Never connects to a PLC.
"""
from pathlib import Path
import csv
import json
import re
from collections import defaultdict

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PLANT = ['PB19', 'PB20', 'PB21', 'PB23', 'PB24', 'PB25']


def rows(path):
    with path.open(encoding='utf-8-sig', newline='') as source:
        return list(csv.DictReader(source, delimiter=';'))


def write(name, values):
    assert values
    with (HERE / name).open('w', encoding='utf-8-sig', newline='') as target:
        writer = csv.DictWriter(target, fieldnames=list(values[0]), delimiter=';')
        writer.writeheader()
        writer.writerows(values)


def main():
    symbols = {(r['area'], r['address']): r for r in rows(ROOT / 'analysis/symbols.csv')}
    full = {r['block'] for r in json.loads((HERE / 'native-files-inventory.json').read_text())['verified_native_files']}
    snapshot_path=HERE/'runtime-db-snapshots.json'
    supplied={}
    if snapshot_path.exists():
        for source in json.loads(snapshot_path.read_text())['sources']:
            for word in source['words']:
                supplied[(source['block'],word['dw'])]=word['raw_hex']
    calls = {r['target']: int(r['order']) for r in rows(ROOT / 'analysis/ob1-call-sequence.csv')}
    tables = {name: [] for name in ['plant-output-map.csv', 'plant-timer-map.csv', 'plant-state-SR.csv',
                                  'plant-alarm-writes.csv', 'all-output-writer-order.csv',
                                  'runtime-parameter-use-map.csv', 'runtime-db-factory-reconstruction.csv']}
    by_output = defaultdict(list)
    timer_sources = []
    all_fbd = json.loads((HERE / 'FBD-blocks-comparison.json').read_text())['blocks']
    for metadata in all_fbd:
        block = metadata['block']
        comparison = json.loads((HERE / f'{block}-comparison.json').read_text())
        assert block in full and not comparison['errors'] and comparison['matched'] == comparison['networks']
        current_db = ''
        for net in comparison['reviews']:
            for order, action in enumerate(net['actions'], start=1):
                operation, target = action['command'], action['target']
                if operation == 'OPEN_DB':
                    current_db = target
                area, _, address = target.partition(' ')
                symbol = symbols.get((area, address), {})
                common = dict(source_block=block, OB1_call_order=calls.get(block, ''), source_network=net['network'],
                              action_order=order, operation=operation, target=target,
                              symbol=symbol.get('symbol', ''), comment_de=symbol.get('comment_de', ''),
                              condition=action['condition'])
                if area == 'A' and operation in ['=', 'S', 'R']:
                    output = dict(common,
                        output_image_reads=' | '.join(sorted(set(re.findall(r'\bA\d+\.\d+', action['condition'])))),
                        migration_limit='Preserve writer/read order; software output image is not sensor feedback',
                        hardware_limit='S5 software address; S7 module/channel and physical wiring pending schematic')
                    by_output[target].append(output)
                    if block in PLANT:
                        tables['plant-output-map.csv'].append(output)
                if area == 'T' and operation in ['SE', 'SA', 'R']:
                    preset, milliseconds = action['preset'], ''
                    if preset.startswith('KT'):
                        count, base = preset[2:].split('.')
                        milliseconds = int(count) * [10, 100, 1000, 10000][int(base)]
                    timer = dict(common, preset=preset,
                        preset_DB_context=current_db if preset.startswith('DW') else '',
                        constant_preset_ms=milliseconds,
                        proposed_S7_family={'SE': 'TON candidate', 'SA': 'TOF candidate', 'R': 'Explicit timer reset'}[operation],
                        migration_limit='Static mapping; compare scan order, start/reset edges, dynamic presets and retention')
                    timer_sources.append(timer)
                    if block in PLANT:
                        tables['plant-timer-map.csv'].append(timer)
                if block in PLANT and area == 'M' and operation in ['S', 'R']:
                    tables['plant-state-SR.csv'].append(dict(common,
                        reset_rule='Later reset wins when both set and reset conditions are true'))
                if block in PLANT and area == 'M' and 5 <= int(address.split('.')[0]) <= 19:
                    tables['plant-alarm-writes.csv'].append(dict(common,
                        number_from_M_and_COMTEXT=(int(address.split('.')[0]) - 5) * 8 + int(address.split('.')[1]) + 1,
                        panel_limit='PLC source logic; standard HMI ACK is a separate function'))
    for target, writers in sorted(by_output.items()):
        writers.sort(key=lambda r: (r['OB1_call_order'], r['source_network'], r['action_order']))
        for index, writer in enumerate(writers, start=1):
            tables['all-output-writer-order.csv'].append(dict(writer,
                writes_to_same_output=len(writers), writer_order_for_output=index,
                last_cyclic_writer=index == len(writers),
                final_writer=writers[-1]['source_block'], final_writer_network=writers[-1]['source_network']))
    default_words = {(r['block'], int(r['dw'])): r for r in rows(ROOT / 'data_review/timer-counter-defaults.csv')}
    used = defaultdict(list)
    for timer in timer_sources:
        if timer['operation'] not in ['SE', 'SA'] or not timer['preset'].startswith('DW'):
            continue
        assert timer['preset_DB_context'] == 'DB 15'
        dw = int(timer['preset'].replace('DW', '').strip())
        default = default_words[('DB12', dw)]
        item = dict(runtime_DB='DB15', runtime_DW=dw, factory_source_DB='DB12',
                    factory_source_DW=dw, factory_source_hex=default['raw_hex'],
                    factory_decoded_ms=default['kt_decoded_ms'],
                    use_block=timer['source_block'], use_network=timer['source_network'],
                    operation=timer['operation'], consumer=timer['target'],
                    consumer_comment=timer['comment_de'], condition=timer['condition'],
                    coding='S5 KT; timer operation confirmed by full native network comparison',
                    supplied_snapshot_value_known=(db_key:=('DB15',dw)) in supplied,
                    supplied_snapshot_hex=supplied.get(db_key,''),
                    migration_status='Factory reference and supplied native DB snapshot; acquisition context in runtime-db-snapshots.json' if supplied else 'Factory reference only; values awaiting CPU to PC read')
        tables['runtime-parameter-use-map.csv'].append(item)
        used[('DB15', dw)].append(item)
    # Z1/Z2 presets were independently compared in native PB13.
    pb13 = json.loads((HERE / 'PB13-comparison.json').read_text())
    for net in pb13['reviews']:
        for action in net['actions']:
            if action['command'] != 'S' or not action['target'].startswith('Z '):
                continue
            if not action['preset'].startswith('DW'):
                continue
            dw = int(action['preset'].replace('DW', '').strip())
            assert (dw, action['target']) in [(1, 'Z 1'), (2, 'Z 2')]
            default = default_words[('DB16', dw)]
            item = dict(runtime_DB='DB19', runtime_DW=dw, factory_source_DB='DB16',
                        factory_source_DW=dw, factory_source_hex=default['raw_hex'], factory_decoded_ms='',
                        use_block='PB13', use_network=net['network'], operation='S', consumer=action['target'],
                        consumer_comment=symbols[('Z', action['target'].split()[1])]['comment_de'],
                        condition=action['condition'], coding='S5 counter preset BCD; native PB13 confirmed',
                        supplied_snapshot_value_known=(db_key:=('DB19',dw)) in supplied,
                        supplied_snapshot_hex=supplied.get(db_key,''),
                        migration_status='Factory reference and supplied native DB snapshot; acquisition context in runtime-db-snapshots.json' if supplied else 'Factory reference only; values awaiting CPU to PC read')
            tables['runtime-parameter-use-map.csv'].append(item)
            used[('DB19', dw)].append(item)
    for runtime, factory in [('DB15', 'DB12'), ('DB19', 'DB16')]:
        for dw in range(132):
            reference = default_words[(factory, dw)] if dw <= 127 else None
            origin = 'FB105 copy of factory word' if reference else 'Zero on newly generated DB; outside FB105 copy range'
            role = {128: 'Parameter selector', 129: 'Previous selector', 130: 'Editing buffer',
                    131: 'Outside verified FB101 editor and factory copy'}.get(dw, 'Parameter slot; use-site mapping listed separately')
            tables['runtime-db-factory-reconstruction.csv'].append(dict(runtime_DB=runtime, runtime_DW=dw,
                factory_initial_hex=reference['raw_hex'] if reference else '0000',
                factory_source_DB=factory if reference else '', factory_source_DW=dw if reference else '',
                origin=origin, role=role,
                confirmed_consumers=' | '.join(r['consumer'] for r in used[(runtime, dw)]),
                supplied_snapshot_value_known=(runtime,dw) in supplied,
                supplied_snapshot_hex=supplied.get((runtime,dw),''),
                status='Factory reference compared to supplied native DB snapshot; not a TIA import' if supplied else 'First preparation reference; runtime snapshot pending'))
    for name, values in tables.items():
        write(name, values)
    assert len(tables['runtime-db-factory-reconstruction.csv']) == 264
    assert set(by_output) == {r['operand'] for r in rows(ROOT / 'offline_decoder/instructions.csv')
                              if r['operand_area'] == 'A' and r['command'] in ['=', 'S', 'R']}
    assert {target for target, writers in by_output.items() if len(writers) > 1} == {'A 21.5'}
    assert len(tables['plant-output-map.csv']) == 37
    assert len(tables['plant-timer-map.csv']) == 34
    assert sum(r['operation'] == 'R' for r in tables['plant-timer-map.csv']) == 2
    summary = dict(table_rows={name: len(values) for name, values in tables.items()},
                   plant_output_writes=37, all_identified_output_bits=len(by_output),
                   multiply_written_output_bits=['A21.5'],
                   plant_timer_starts=32, plant_timer_resets=2,
                   parameter_slots_with_confirmed_timer_or_counter_consumer=sum(bool(values) for values in used.values()),
                   runtime_DB_snapshot_values_available=bool(supplied), first_preparation_words=264,
                   A17_7='PB25 writes M71.5 cleaning-completed contact; OP15 door status reads this output, not a door position sensor',
                   A20_5='PB20: held K16 in HAND with function 66, or automatic dosing with valve A21.6 and T107 off-delay',
                   static_only=True, runtime_test=False)
    (HERE / 'plant-data-evidence.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
