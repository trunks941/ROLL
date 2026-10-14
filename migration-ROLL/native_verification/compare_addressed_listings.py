#!/usr/bin/env python3
"""Compare supplied STEP 5 instruction word addresses with offline MC5 rows.

Read-only with respect to originals and PLCs. This supports the supplied
addressed listings below, not arbitrary STEP 5 syntax or program execution.
Outputs are written only beside this script. OB1's mixed graphical listing and
FB105's earlier comparison are documented separately.
"""
from pathlib import Path
import csv
import hashlib
import json
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
STARTUP_FILES = {
    'FB61': 'FB61ROLS.INI',
    'OB13': 'OB13ROLS.INI',
    'OB21': 'OB21ROLS.INI',
    'OB22': 'OB22ROLS.INI',
    'FB101': 'FB101RLS.INI',
}
PANEL_FILES = {
    'FB3': 'FB3ROLLS.INI',
    'FB60': 'FB60ROLS.INI',
    'FB62': 'FB62ROLS.INI',
    'FB63': 'FB63ROLS.INI',
    'FB69': 'FB69ROLS.INI',
    'OB34': 'OB34ROLS.INI',
}
RECIPE_FILES = {
    'FB89': 'FB89ROLS.INI',
    'FB90': 'FB90ROLS.INI',
    'FB91': 'FB91ROLS.INI',
    'FB92': 'FB92ROLS.INI',
    'FB95': 'FB95ROLS.INI',
    'FB96': 'FB96ROLS.INI',
    'FB111': 'FB111RLS.INI',
}
FILES = {**STARTUP_FILES, **PANEL_FILES, **RECIPE_FILES}
COMMANDS = {
    'A': 'U', 'AN': 'UN', 'C': 'A', 'DO': 'B', 'G': 'E',
    'JU': 'SPA', 'JC': 'SPB', 'BEU': 'BEA', 'BEC': 'BEB', 'SD': 'SE',
    'A(': 'U(', 'AW': 'UW', 'O(': 'O(',
}
AREAS = {'F': 'M', 'FW': 'MW', 'FY': 'MB', 'I': 'E', 'Q': 'A', 'RS': 'BS'}
NO_OPERAND = {'BE', 'BEU', 'BEC', 'OW', 'AW', 'XOW', 'A(', 'O(', ')',
              '!=F', '><F', '<F', '>F', '<=F', '-F', '+F', 'TAK'}


def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as source:
        return list(csv.DictReader(source, delimiter=';'))


def parse_addressed(text, block_length):
    network = 0
    rows, labels = [], {}
    for line in text.splitlines():
        segment = re.match(r'^Segment\s+(\d+)', line)
        if segment:
            network = int(segment.group(1))
        match = re.match(r'^([0-9A-F]{4})\s+(?:(M\d+)\s*)?:(.*)$', line)
        if not match:
            continue
        word_address, label, content = match.groups()
        offset = 10 + 2 * int(word_address, 16)
        if label:
            assert (network, label) not in labels, 'Duplicate local label'
            labels[(network, label)] = offset
        rows.append(dict(native_word_address=word_address,
                         block_byte_offset=offset, network=network,
                         native_content=content))
    for row in rows:
        content = row['native_content']
        if not content or content[0].isspace():
            command, operand = 'BLD', '130'
        elif content.split()[0] == 'STL':
            command, operand = 'BLD', '131'
        elif content.split()[0] == '***':
            command, operand = 'BLD', '255'
        else:
            parts = content.split()
            native_command = parts[0]
            command = COMMANDS.get(native_command, native_command)
            if native_command in ('JU', 'JC') and parts[1].startswith('='):
                target = labels[(row['network'], parts[1][1:])]
                command += '='
                operand = f'@{target:04X}'
                row['jump_target_block_byte_offset'] = target
            elif native_command in NO_OPERAND:
                operand = ''
            elif native_command == 'O' and len(parts) == 1:
                operand = ''
            elif native_command in ('SLW', 'SRW'):
                operand = str(int(parts[1]))
            elif native_command in ('L', 'T') and parts[1].startswith('='):
                operand = parts[1]
            elif native_command == 'I':
                operand = str(int(parts[1]))
            elif native_command == 'NOP':
                assert parts[1] in ('0', '1'), content
                command, operand = 'NOP' + parts[1], ''
            else:
                assert native_command in ('A', 'AN', 'O', 'ON', 'L', 'LC', 'T', 'C',
                                          'DO', 'S', 'R', '=', 'G', 'JU', 'JC', 'SD'), content
                area, number = parts[1:3]
                assert area in ('F', 'FW', 'FY', 'RS', 'DB', 'DW', 'OB', 'FB', 'PB',
                                'I', 'T', 'KF', 'KH', 'KT', 'KY', 'KM', 'DL', 'DR'), content
                if area == 'KM':
                    assert len(number) == 8 and len(parts[3]) == 8
                    number += parts[3]
                if area not in ('KH', 'KT', 'KY', 'KM') and '.' not in number:
                    number = str(int(number))
                    if area == 'KF' and int(number) >= 0:
                        number = '+' + number
                operand = f'{AREAS.get(area, area)} {number}'
        row['command'], row['operand'] = command, operand
    # FB89's final network has an explicit BE without a printed address.
    # Its offset is inferred from LEN, and reported separately from addresses.
    unaddressed = re.findall(r'^\s+:BE\s*$', text, re.MULTILINE)
    if unaddressed:
        assert len(unaddressed) == 1
        rows.append(dict(native_word_address='', block_byte_offset=block_length-2,
                         network=network, native_content='BE (no printed address)',
                         command='BE', operand='', position_note='Offset inferred from LEN'))
    return rows


def compare(block, filename, decoded, directory):
    path = ROOT / 'originals/step5-native' / filename
    raw = path.read_bytes()
    text = raw.decode('cp850')
    block_length = int(directory[block]['bytes'])
    rows = parse_addressed(text, block_length)
    expected = {int(row['offset']): row for row in decoded if row['block'] == block}
    offsets = [row['block_byte_offset'] for row in rows]
    assert offsets == sorted(expected), f'{block}: incomplete or reordered positions'
    header_lengths = re.findall(r'LEN=(\d+)', text)
    assert header_lengths and all(2 * int(n) == block_length for n in header_lengths)
    headers = re.findall(r'^(?:\x0c)?(OB|FB|PB)\s+(\d+)[^\r\n]*LEN=\d+',
                         text, re.MULTILINE)
    assert headers and all(kind + number == block for kind, number in headers)
    for i, native in enumerate(rows):
        offset = native['block_byte_offset']
        previous = expected[offset]
        operand = previous['operand']
        if 'jump_target_block_byte_offset' in native:
            operand = operand.split()[0]
        assert (native['command'], native['operand'], native['network']) == (
            previous['command'], operand, int(previous['network'])
        ), (block, native, previous)
        # Word addresses also check constants/call descriptors skipped by print.
        next_offset = offsets[i + 1] if i + 1 < len(offsets) else block_length
        assert next_offset - offset == int(previous['size']), (block, offset)
        native['raw_hex'] = previous['raw_hex']
        native['size_bytes'] = int(previous['size'])
    # Check addressed call arguments as well as the containing instruction.
    native_args = []
    for match in re.finditer(r'^([0-9A-F]{4})\s+(INPU|OUTP)\s*:\s*(FW|DW)\s+(\d+)', text, re.MULTILINE):
        word_address, name, area, number = match.groups()
        native_args.append(dict(argument_offset=10+2*int(word_address,16), name=name,
                                value=f'{AREAS.get(area,area)} {int(number)}'))
    expected_args = [r for r in read_csv(ROOT/'offline_decoder/call-arguments.csv') if r['source']==block]
    assert len(native_args) == len(expected_args), (block, 'Call argument count')
    for native_arg, previous in zip(native_args, expected_args):
        assert (native_arg['argument_offset'],native_arg['name'],native_arg['value']) == (
            int(previous['argument_offset']),previous['name'],previous['value']), (block,native_arg,previous)
        native_arg['raw_hex'] = previous['raw_hex']
    # FB96 is the only supplied block with formal declarations.
    native_params = re.findall(r'^Decl\s*:(\w+)\s+I/Q/D/B/T/C:\s*(\w+)\s+BI/BY/W/D:\s*(\w+)', text, re.MULTILINE)
    expected_params = [r for r in read_csv(ROOT/'offline_decoder/fb-parameters.csv') if r['block']==block]
    assert [(n, {'I':'E','Q':'A'}.get(t,t),f) for n,t,f in native_params] == [
        (r['name'],r['type'],r['format']) for r in expected_params], (block,'Formal declarations')
    cleaned = re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]', '', text)
    cleaned = cleaned.replace('\r\n', '\n').replace('\x0c', '\n')
    (HERE / f'{block}-native.txt').write_text(cleaned, encoding='utf-8')
    fields = ['native_word_address', 'block_byte_offset', 'network',
              'native_content', 'command', 'operand', 'raw_hex', 'size_bytes',
              'jump_target_block_byte_offset']
    fields.append('position_note')
    with (HERE / f'{block}-native-normalized-instructions.csv').open(
            'w', encoding='utf-8-sig', newline='') as output:
        writer = csv.DictWriter(output, fieldnames=fields, delimiter=';')
        writer.writeheader()
        writer.writerows(rows)
    result = dict(block=block, source_file=filename,
                  sha256=hashlib.sha256(raw).hexdigest(), size_bytes=len(raw),
                  pages=len(re.findall(r'Page\s+\d+', text)),
                  networks=max(row['network'] for row in rows),
                  block_bytes=block_length, positions_compared=len(rows),
                  executing_instructions=sum(row['command'] != 'BLD' for row in rows),
                  BLD_display_rows=sum(row['command'] == 'BLD' for row in rows),
                  jumps_compared=sum('jump_target_block_byte_offset' in row for row in rows),
                  addressed_positions=sum(bool(row['native_word_address']) for row in rows),
                  unaddressed_final_instructions=sum(not row['native_word_address'] for row in rows),
                  call_arguments_compared=native_args,
                  formal_declarations_compared=len(native_params),
                  result='All positions, commands, operands, networks, lengths and jump targets match.',
                  limitations='Native documentation comparison, not PLC execution or whole-program validation. System effects and HMI behavior are documented separately.')
    (HERE / f'{block}-comparison.json').write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return result


def main():
    decoded = read_csv(ROOT / 'offline_decoder/instructions.csv')
    directory = {row['kind'] + row['number']: row for row in
                 read_csv(ROOT / 'analysis/s5-program-blocks.csv')}
    results = [compare(block, filename, decoded, directory)
               for block, filename in FILES.items()]
    def summarize(selected):
        return dict(blocks=selected,
                    total_positions_compared=sum(r['positions_compared'] for r in selected),
                    total_executing_instructions=sum(r['executing_instructions'] for r in selected),
                    total_jumps_compared=sum(r['jumps_compared'] for r in selected))
    for filename, selected in [
            ('startup-parameters-comparison.json', [r for r in results if r['block'] in STARTUP_FILES]),
            ('panel-control-comparison.json', [r for r in results if r['block'] in PANEL_FILES]),
            ('recipe-alarm-comparison.json', [r for r in results if r['block'] in RECIPE_FILES]),
            ('addressed-blocks-comparison.json', results)]:
        summary = summarize(selected)
        (HERE / filename).write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
        if filename == 'recipe-alarm-comparison.json':
            print(json.dumps({k:v for k,v in summary.items() if k!='blocks'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
