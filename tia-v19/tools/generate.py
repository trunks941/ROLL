#!/usr/bin/env python3
"""ROLL-specific S5 -> SCL generation. Fails on every unhandled instruction.

Preserves instruction ordering and snapshots the RLO before consecutive coils.
This is source generation, not a Siemens compiler or a commissioning tool.
"""
from pathlib import Path
import csv
import hashlib
import importlib.util
import json
import re

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'tia-v19'
OLD = ROOT / 'migration-ROLL'
spec = importlib.util.spec_from_file_location('fbd_reader', OLD / 'native_verification/compare_fbd_listings.py')
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)


def csv_rows(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f, delimiter=';'))


def kt_word(text):
    match = re.fullmatch(r'(\d{1,3})\.([0-3])', text)
    if not match:
        raise ValueError(('Invalid KT', text))
    value, base = int(match[1]), int(match[2])
    return (base << 12) | ((value // 100) << 8) | (((value // 10) % 10) << 4) | (value % 10)


def operand(text, db='#db', boolean=False):
    area, index = text.split()
    if area in ('M', 'E', 'A'):
        byte, bit = index.split('.')
        table = {'M': '"ROLL_State".M', 'E': '"ROLL_IO".Input', 'A': '"ROLL_IO".Output'}[area]
        return f'{table}[{int(byte)}, {int(bit)}]'
    if area in ('T', 'Z'):
        n = int(index)
        if boolean:
            return f'"ROLL_State".Timer[{n}].Q' if area == 'T' else f'("ROLL_State".Counter[{n}].Value <> 0)'
        return f'"ROLL_TimerValue"(Number := {n})' if area == 'T' else f'INT_TO_WORD("ROLL_State".Counter[{n}].Value)'
    if area in ('MB', 'MW'):
        return f'"ROLL_GetM"(FirstByte := {int(index)}, Width := {8 if area == "MB" else 16})'
    if area == 'DW':
        return f'"ROLL_GetDW"(DbNumber := {db}, Index := {int(index)})'
    if area == 'KT':
        return f'W#16#{kt_word(index):04X}'
    if area in ('KH', 'KM', 'KB', 'KF', 'KZ'):
        n = int(index, {'KH': 16, 'KM': 2}.get(area, 10))
        if area == 'KZ':
            assert 0 <= n <= 999
            n = kt_word(f'{n}.0')
        return f'W#16#{n & 65535:04X}'
    raise ValueError(('Unhandled operand', text))


def expression(node):
    op = node[0]
    if op == 'LOCAL':
        return '#' + node[1]
    if op == 'READ':
        return operand(node[1], boolean=True)
    if op == 'NOT':
        return '(NOT ' + expression(node[1]) + ')'
    if op in ('AND', 'OR'):
        return '(' + (' ' + op + ' ').join(expression(x) for x in node[1:]) + ')'
    if op in ('EQ', 'NE', 'GT', 'LT', 'LE', 'GE'):
        operator = {'EQ': '=', 'NE': '<>', 'GT': '>', 'LT': '<', 'LE': '<=', 'GE': '>='}[op]
        return f'(WORD_TO_INT(#{node[1][1]}) {operator} WORD_TO_INT(#{node[2][1]}))'
    raise ValueError(('Unhandled expression', node))


def fc(name, body, temp=''):
    return f'''FUNCTION "{name}" : Void
{{ S7_Optimized_Access := 'TRUE' }}
VERSION : 0.1
{temp}
BEGIN
{body}
END_FUNCTION
'''


def compile_pb(block, rows):
    logic = reader.Logic()
    stack = []
    lines = ['    #db := 0;']
    last_network = None
    meaningful = 0
    comparison_count = 0
    for row in rows:
        c, o = row['command'], row['operand']
        if row['network'] != last_network:
            last_network = row['network']
            lines.append(f'    // {block}, STEP 5 network {last_network}')
        if c in ('BLD', 'NOP0'):
            continue
        meaningful += 1
        if c in ('U(', 'O('):
            stack.append((logic, c[0]))
            logic = reader.Logic()
        elif c == ')':
            arg = logic.value()
            logic, command = stack.pop()
            logic.apply(command, arg)
        elif c in ('U', 'UN', 'O', 'ON'):
            arg = ('READ', o) if o else None
            if c in ('UN', 'ON'):
                arg = reader.canon('NOT', arg)
            logic.apply(c[0], arg)
        elif c == 'L':
            lines += ['    #a2 := #a1;', f'    #a1 := {operand(o)};']
        elif c in ('!=F', '><F', '>F', '<F', '<=F', '>=F'):
            op = {'!=F': 'EQ', '><F': 'NE', '>F': 'GT', '<F': 'LT', '<=F': 'LE', '>=F': 'GE'}[c]
            lines.append(f'    #compare[{comparison_count}] := {expression((op, ("LOCAL", "a2"), ("LOCAL", "a1")))};')
            logic.apply('U', ('LOCAL', f'compare[{comparison_count}]'))
            comparison_count += 1
        elif c in ('=', 'S', 'R', 'SE', 'SA', 'ZR', 'ZV'):
            condition = logic.action()
            # A second coil consumes the stored RLO; it must not re-read an
            # expression whose inputs could have changed in the preceding coil.
            if condition != ('LOCAL', 'r'):
                lines.append(f'    #r := {expression(condition)};')
            logic.current = ('LOCAL', 'r')
            if o.startswith('Z '):
                mode = {'S': 0, 'R': 1, 'ZV': 2, 'ZR': 3}[c]
                lines.append(f'    "ROLL_CounterOp"(Number := {int(o.split()[1])}, Operation := {mode}, Signal := #r, Preset := #a1);')
            elif o.startswith('T '):
                mode = {'SE': 0, 'SA': 1, 'R': 2}[c]
                lines.append(f'    "ROLL_TimerOp"(Number := {int(o.split()[1])}, Operation := {mode}, Signal := #r, Preset := #a1);')
            elif c == '=':
                lines.append(f'    {operand(o)} := #r;')
            elif c in ('S', 'R'):
                lines.append(f'    IF #r THEN {operand(o)} := {"TRUE" if c == "S" else "FALSE"}; END_IF;')
            else:
                raise ValueError((block, c, o))
        elif c == 'A' and o.startswith('DB '):
            lines.append(f'    #db := {int(o.split()[1])};')
        elif c == 'SPA' and o == 'FB 69':
            lines.append('    "ROLL_FB69"();')
        elif c == 'BE':
            lines.append('    RETURN;')
        else:
            raise ValueError(('Unhandled instruction', block, row))
    assert not stack
    temp = f'VAR_TEMP\n    r : Bool;\n    a1 : Word;\n    a2 : Word;\n    db : Int;\n    compare : Array[0..{max(0,comparison_count - 1)}] of Bool;\nEND_VAR'
    # Unused accumulators are initialized for deterministic, diagnosable code.
    lines[0:0] = ['    #r := FALSE;', '    #a1 := W#16#0000;', '    #a2 := W#16#0000;']
    return fc('ROLL_' + block, '\n'.join(lines), temp), meaningful


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def main():
    rows = csv_rows(OLD / 'offline_decoder/instructions.csv')
    blocks = sorted({x['block'] for x in rows if x['block'].startswith('PB')}, key=lambda x: int(x[2:]))
    sources, coverage = [], []
    for b in blocks:
        selected = [x for x in rows if x['block'] == b]
        # Check the decoder against the separately recorded native FBD evidence.
        if b != 'PB16':
            evidence = json.loads((OLD / f'native_verification/{b}-comparison.json').read_text())
            assert all(x['result'] == 'Match' for x in evidence['reviews']), b
            recorded = [a for net in evidence['reviews'] for a in net['actions']]
            actions = reader.mc5_actions(selected)
            assert len(recorded) == len(actions), b
            for old, new in zip(recorded, actions):
                assert old['command'] == new[0] and old['target'] == new[1], (b, old, new)
                assert old['condition_ast'] == json.loads(json.dumps(new[2])), (b, old, new)
        else:
            evidence = json.loads((OLD / 'native_verification/PB16-comparison.json').read_text())
            assert evidence['networks_manually_compared'] == 34, evidence
        text, count = compile_pb(b, selected)
        sources.append(text)
        coverage.append({'block': b, 'decoded_rows': len(selected), 'executable_rows': count, 'source': '02-process.scl', 'method': 'ordered SCL from MC5 verified against native STEP 5', 'tia_compiled': False})
    write(OUT / 'sources/02-process.scl', '\n'.join(sources))
    # Use actual online DB snapshots, without silently substituting factory data.
    values = {15: {}, 19: {}}
    for row in csv_rows(OLD / 'native_verification/runtime-db-words.csv'):
        db = int(row['runtime_DB'][2:])
        values[db][int(row['runtime_DW'])] = int(row['supplied_hex'], 16)
    data = []
    for db in (15, 19):
        assert set(values[db]) == set(range(132))
        data.append(f'''DATA_BLOCK "ROLL_DB{db}"
{{ S7_Optimized_Access := 'TRUE' }}
VERSION : 0.1
NON_RETAIN
VAR
    DW : Array[0..131] of Word;
END_VAR
BEGIN
''' + '\n'.join(f'    DW[{index}] := W#16#{value:04X};' for index, value in sorted(values[db].items())) + '\nEND_DATA_BLOCK\n')
    # Time base 1 s is an explicit migration choice, not an inferred old KT base.
    recipes = {1: {}, 2: {}}
    for row in csv_rows(OLD / 'operator_recipes/operator-recipes.csv'):
        program = int(row['program_number'])
        index = int(row['legacy_consumer'].split('DW')[1])
        if row['proposed_s7_type'] == 'TIME':
            seconds = int(row['normalized_s7_value']) // 1000
            value = kt_word(f'{seconds}.2')
        elif row['proposed_s7_type'] == 'Bool':
            value = int(row['normalized_s7_value'] == 'True')
        else:
            value = int(row['normalized_s7_value'])
        recipes[program][index] = value
    assert recipes[1] == recipes[2] and len(recipes[1]) == 10
    for program in (1, 2):
        data.append(f'''DATA_BLOCK "ROLL_Recipe{program}"
{{ S7_Optimized_Access := 'TRUE' }}
VERSION : 0.1
NON_RETAIN
VAR
    DW : Array[0..41] of Word;
END_VAR
BEGIN
''' + '\n'.join(f'    DW[{index}] := W#16#{value:04X};' for index, value in sorted(recipes[program].items())) + '\nEND_DATA_BLOCK\n')
    data.append('''DATA_BLOCK "ROLL_DB205"
{ S7_Optimized_Access := 'TRUE' }
VERSION : 0.1
NON_RETAIN
VAR
    DW : Array[0..41] of Word;
END_VAR
BEGIN
''' + '\n'.join(f'    DW[{index}] := W#16#{value:04X};' for index, value in sorted(recipes[1].items())) + '\nEND_DATA_BLOCK\n')
    write(OUT / 'sources/01-data.scl', '\n'.join(data))
    input_body = [
        '    // Confirmed four-station profile: absent optional inputs are zero.',
        '    FOR #b := 119 TO 125 DO',
        '        FOR #bit := 0 TO 7 DO "ROLL_IO".Input[#b, #bit] := FALSE; END_FOR;',
        '    END_FOR;',
        '    IF "ROLL_IO".PhysicalIoConfigured AND NOT "ROLL_IO".Simulation THEN',
    ]
    input_body += [f'        "ROLL_IO".Input[{byte}, {bit}] := %I{byte}.{bit};' for byte in range(16) for bit in range(8)]
    input_body.append('    END_IF;')
    output_body = [
        '    IF "ROLL_IO".PhysicalIoConfigured THEN',
        '        #enabled := "ROLL_IO".PhysicalOutputsEnabled AND NOT "ROLL_IO".Simulation AND NOT "ROLL_IO".ConversionFault;',
    ]
    output_body += [f'        %Q{byte}.{bit} := #enabled AND "ROLL_IO".Output[{byte}, {bit}];' for byte in range(16, 26) for bit in range(8)]
    output_body.append('    END_IF;')
    write(OUT / 'sources/03-io.scl', fc('ROLL_ReadInputs', '\n'.join(input_body), 'VAR_TEMP\n    b : Int;\n    bit : Int;\nEND_VAR') + '\n' + fc('ROLL_WriteOutputs', '\n'.join(output_body), 'VAR_TEMP\n    enabled : Bool;\nEND_VAR'))
    facts = {
        'format': 1,
        'status': 'SCL generated; local TIA V19 compilation required',
        'pb_count': len(blocks), 'pb_coverage': coverage,
        'adaptations': {'FB69': 'SCL pause selection', 'FB90': 'SCL recipe decoding', 'FB111': 'SCL two process timers', 'FB101': 'native HMI parameter commands', 'FB105': 'initialized persistent data blocks', 'FB61': 'startup/retention/clock adaptation', 'OB13': '250 ms cadence accumulated from cycle time', 'OB21/OB22': 'OB100 startup', 'OB34': 'old S5 battery warning requires S7 diagnostic redesign'},
        'op15_replaced': ['FB3', 'FB51', 'FB60', 'FB62', 'FB63', 'FB89', 'FB91', 'FB92', 'FB95', 'FB96'],
        'unresolved': ['TIA compilation', 'native retention properties and online RS120 bits 4/5', 'CPU catalog/firmware', 'configured physical I/O and electrical grouping', 'TP900 connection, tags, screen controls and alarm import', 'S5 timer phase/jitter equivalence', 'power-loss tests and physical commissioning'],
        'source_sha256': hashlib.sha256((OLD / 'offline_decoder/instructions.csv').read_bytes()).hexdigest(),
        'target': {'cpu': '6ES7513-1AM03-0AB0', 'hmi': '6AV2124-0JC01-0AX0', 'stations': [1, 2, 3, 4], 'automatic_feeding': False},
        'recipe_time_base_seconds': 1,
        'physical_outputs_default_enabled': False,
    }
    write(OUT / 'reports/coverage.json', json.dumps(facts, indent=2, ensure_ascii=False) + '\n')
    runtime = (OUT / 'sources/00-runtime.scl').read_text()
    declarations, functions = runtime.split('FUNCTION "ROLL_GetM"', 1)
    combined = [declarations, (OUT / 'sources/01-data.scl').read_text(), 'FUNCTION "ROLL_GetM"' + functions,
                (OUT / 'sources/03-process-functions.scl').read_text(), (OUT / 'sources/02-process.scl').read_text(),
                (OUT / 'sources/03-io.scl').read_text(), (OUT / 'sources/04-hmi-cycle.scl').read_text()]
    write(OUT / 'ROLL_ALL.scl', '\n'.join(combined))
    hashes = {str(path.relative_to(OUT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted((OUT / 'sources').glob('*.scl'))}
    hashes['ROLL_ALL.scl'] = hashlib.sha256((OUT / 'ROLL_ALL.scl').read_bytes()).hexdigest()
    write(OUT / 'reports/source-hashes.json', json.dumps(hashes, indent=2) + '\n')
    print(f'Generated {len(blocks)} PB functions, {sum(x["executable_rows"] for x in coverage)} executable MC5 positions; 2 confirmed recipes; runtime DB15/19.')


if __name__ == '__main__':
    main()
