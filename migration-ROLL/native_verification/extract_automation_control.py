#!/usr/bin/env python3
"""Extract ordered actions from nine completely compared native STEP 5 blocks.

Source is the independently read native FBD/mixed listing, not a PLC simulation.
The combined PB51/PB52 source remains preserved and identified by byte scopes.
"""
from pathlib import Path
import csv
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BLOCKS = ['PB7', 'PB8', 'PB9', 'PB10', 'PB14', 'PB15', 'PB50', 'PB51', 'PB52']


def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as source:
        return list(csv.DictReader(source, delimiter=';'))


def write_csv(name, rows):
    assert rows
    with (HERE / name).open('w', encoding='utf-8-sig', newline='') as output:
        writer = csv.DictWriter(output, fieldnames=list(rows[0]), delimiter=';')
        writer.writeheader()
        writer.writerows(rows)


def main():
    symbols = {(r['area'], r['address']): r for r in read_csv(ROOT / 'analysis/symbols.csv')}
    tables = {name: [] for name in ['automatic-steps-SR.csv', 'automation-timer-map.csv',
              'automation-permits-and-state-map.csv', 'tracking-state-SR.csv',
              'automatic-motion-command-map.csv', 'automation-meter-output-map.csv']}
    sources = []
    for block in BLOCKS:
        comparison = json.loads((HERE / f'{block}-comparison.json').read_text())
        assert not comparison['errors'] and comparison['matched'] == comparison['networks']
        sources.append({k: comparison[k] for k in ['block', 'source_file', 'sha256', 'source_scope']})
        current_db = ''
        for network in comparison['reviews']:
            for order, action in enumerate(network['actions'], start=1):
                command, target = action['command'], action['target']
                if command == 'OPEN_DB':
                    current_db = target
                area, _, address = target.partition(' ')
                symbol = symbols.get((area, address), {})
                common = dict(source_block=block, source_network=network['network'], action_order=order,
                              operation=command, target=target, symbol=symbol.get('symbol', ''),
                              comment_de=symbol.get('comment_de', ''), condition=action.get('condition', ''))
                if block in ['PB9', 'PB10'] and command in ['S', 'R'] and area == 'M' and 37 <= int(address.split('.')[0]) <= 53:
                    tables['automatic-steps-SR.csv'].append(dict(common,
                        scan_rule='Preserve PB9 before PB10 and network/action order; no single-step-per-scan assumption',
                        runtime_test=False))
                if area == 'T' and command in ['SE', 'SA', 'R']:
                    preset = action.get('preset', '')
                    duration = ''
                    if preset.startswith('KT'):
                        count, base = preset[2:].split('.')
                        duration = int(count) * [10, 100, 1000, 10000][int(base)]
                    tables['automation-timer-map.csv'].append(dict(common, preset=preset,
                        preset_DB_context=current_db if preset.startswith('DW') else '',
                        constant_preset_ms=duration,
                        proposed_S7_family={'SE': 'TON candidate', 'SA': 'TOF candidate', 'R': 'Explicit timer reset'}[command],
                        migration_limit='Static operation mapping; compare scan order, start/reset edges, dynamic presets and retention'))
                if (block in ['PB7', 'PB8', 'PB50'] and area == 'M') or (block == 'PB9' and area == 'M' and int(address.split('.')[0]) < 37) or (block == 'PB15' and target == 'M 74.0'):
                    tables['automation-permits-and-state-map.csv'].append(dict(common,
                        scan_rule='Preserve OB1 call order and set before later reset; reset wins if both true',
                        runtime_test=False))
                if block == 'PB15' and command in ['S', 'R']:
                    tables['tracking-state-SR.csv'].append(dict(common,
                        correction_request='M73.7 is produced by PB16 for function 99 and both held keys',
                        status_limit='PB18 function 99 status omits M70.5 and M70.7; correction resets all seven listed tracking bits'))
                if block == 'PB14' and area == 'M':
                    tables['automatic-motion-command-map.csv'].append(dict(common,
                        output_layer='Motion request/state only; physical output is calculated later in PB17',
                        hardware_limit='Physical channel, wiring and interlocks pending schematic'))
                if block == 'PB7' and area == 'A' and command == '=':
                    tables['automation-meter-output-map.csv'].append(dict(common,
                        hardware_limit='Software command address; physical channel and meter wiring pending schematic'))
    for name, rows in tables.items():
        write_csv(name, rows)
    timers = tables['automation-timer-map.csv']
    assert len(timers) == 30
    assert sum(r['operation'] == 'R' for r in timers) == 1
    assert next(r for r in timers if r['target'] == 'T 16')['constant_preset_ms'] == 3600000
    assert next(r for r in timers if r['target'] == 'T 13')['constant_preset_ms'] == 2000
    assert next(r for r in timers if r['target'] == 'T 11')['constant_preset_ms'] == 8000
    assert len(tables['tracking-state-SR.csv']) == 14
    assert len({r['target'] for r in tables['tracking-state-SR.csv']}) == 7
    assert len(tables['automation-meter-output-map.csv']) == 2
    steps = tables['automatic-steps-SR.csv']
    assert all(sum(r['target'] == target and r['operation'] == cmd for r in steps) == 1
               for target in {r['target'] for r in steps} for cmd in ['S', 'R'])
    summary = dict(source_blocks=sources, table_rows={name: len(rows) for name, rows in tables.items()},
                   automatic_step_bits=len({r['target'] for r in steps}),
                   timer_starts=29, timer_resets=1, tracking_bits_reset_by_M73_7=7,
                   M74_0='Cyclic held-state command from PB15, not a latch; PB16 reads its previous-cycle value',
                   static_only=True, runtime_test=False)
    (HERE / 'automation-data-evidence.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in summary.items() if k != 'source_blocks'}))


if __name__ == '__main__':
    main()
