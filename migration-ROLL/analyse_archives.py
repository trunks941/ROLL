#!/usr/bin/env python3
"""Read-only inventory of the supplied STEP 5 / OP15 archives.

This is an inventory tool, not a PLC program converter or an OP15 project reader.
The STEP 5 directory/header layout was checked against Step5Project.cs and
PLCBlockType.cs in dotnetprojects/DotNetSiemensPLCToolBoxLibrary, commit
3d3eea50d9b24b53481809585f73e67f93ddb1d9, and against the supplied block headers.
Directory offsets are used explicitly: old block bodies remain in the S5D file.
"""
from pathlib import Path
from collections import Counter
import csv
import hashlib
import json
import re

BASE = Path(__file__).resolve().parent
OUT = BASE / 'analysis'
OUT.mkdir(exist_ok=True)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def csvfile(name, fields, rows):
    # UTF-8 BOM and semicolon delimiters make these readable in Polish Excel.
    with (OUT / name).open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter=';')
        writer.writeheader()
        writer.writerows(rows)


seq = next((BASE / 'originals').rglob('*Z0.SEQ'))
seq_data = seq.read_bytes().split(b'\x1a')[0]
seq_text = seq_data.decode('cp850')
(BASE / 'symbols-original-utf8.txt').write_text(seq_text, encoding='utf-8')
symbols = []
for line_no, line in enumerate(seq_text.splitlines(), 1):
    if not line.strip() or line.lstrip().startswith(';'):
        continue
    match = re.fullmatch(r'\s*([A-Z]+)\s+(\d+(?:\.\d+)?)\t([^\t]*)\t(.*)', line)
    if not match:
        raise ValueError(f'Unparsed symbol line {line_no}: {line!r}')
    area, address, name, comment = match.groups()
    symbols.append(dict(line=line_no, area=area, address=address,
                        symbol=name, comment_de=comment))
assert len({(s['area'], s['address']) for s in symbols}) == len(symbols)
csvfile('symbols.csv', ['line', 'area', 'address', 'symbol', 'comment_de'], symbols)
symbol_by_address = {(s['area'], s['address']): s for s in symbols}

io = []
for s in symbols:
    if s['area'] not in ('E', 'A'):
        continue
    target = '%I' if s['area'] == 'E' else '%Q'
    io.append(dict(source_line=s['line'], s5_address=s['area'] + s['address'],
                   provisional_s7_address=target + s['address'],
                   symbol=s['symbol'], comment_de=s['comment_de'],
                   status='Propozycja adresu; potwierdzic sprzet, schemat i uzycie w programie'))
csvfile('io-map-draft.csv', list(io[0]), io)

alarm_symbols = [s for s in symbols if re.fullmatch(r'STOER_?\d+', s['symbol'])]
csvfile('alarm-symbols.csv', ['line', 'area', 'address', 'symbol', 'comment_de'], alarm_symbols)

s5_path = next((BASE / 'originals').rglob('*.S5D'))
s5 = s5_path.read_bytes()
types = {1: 'DB', 2: 'SB', 4: 'PB', 5: 'FX', 8: 'FB', 12: 'DX', 16: 'OB',
         81: 'OK', 49: 'PK', 65: 'FK', 90: 'FKX', 33: 'SK', 91: 'DK',
         92: 'DKX', 100: 'BB', 6: 'DV', 17: 'DVX', 13: 'FV', 10: 'FVX'}
main_types = {'DB', 'SB', 'PB', 'FX', 'FB', 'DX', 'OB'}
comments_types = {'PK', 'FK', 'OK', 'DK', 'SK', 'FKX', 'DKX'}
inventory = []
sections = []
payloads = {}
for section_index in range(s5[0x16]):
    entry = 0x44 + section_index * 19
    section_offset = int.from_bytes(s5[entry + 15:entry + 17], 'little') * 128
    assert s5[section_offset:section_offset + 8] == s5[8:16]
    section_type = s5[section_offset + 8]
    if section_type not in types:
        sections.append(dict(index=section_index, offset=section_offset,
                             type_hex=f'{section_type:02X}', status='unsupported auxiliary section'))
        continue
    kind = types[section_type]
    count = s5[section_offset + 22]
    sections.append(dict(index=section_index, offset=section_offset, type=kind, count=count))
    if kind in main_types:
        # Check the linked directory chain as well as the declared entry count.
        # Unreachable trailing records/bodies can belong to previous versions.
        cursor = int.from_bytes(s5[section_offset + 24:section_offset + 26], 'little')
        visited = []
        while cursor != 0xffff:
            assert cursor < count and cursor not in visited
            visited.append(cursor)
            p = section_offset + 68 + cursor * 15
            cursor = int.from_bytes(s5[p:p + 2], 'little')
        assert set(visited) == set(range(count))
        numbers = [s5[section_offset + 68 + i * 15 + 4] for i in visited]
        assert numbers == sorted(numbers)
        sections[-1]['directory_chain_verified'] = True
    for item in range(count):
        pos = section_offset + 68 + item * 15
        header = s5[pos:pos + 15]
        number = header[4]
        length = int.from_bytes(header[9:11], 'little')
        offset = section_offset + int.from_bytes(header[11:13], 'little') * 128
        assert 0 <= offset and offset + length <= len(s5)
        raw = s5[offset:offset + length]
        if kind in {'DV', 'DVX', 'FV', 'FVX'}:
            assert raw[0] == section_type and raw[1] == number
            assert int.from_bytes(raw[4:6], 'big') * 2 == length
        else:
            assert raw[:2] == b'pp' and raw[2] == section_type and raw[3] == number
            encoded_length = int.from_bytes(raw[8:10], 'big') * 2
            # Comment lengths are byte counts; their word header includes rounding.
            assert encoded_length in ({length, length + length % 2}
                                      if kind in comments_types else {length})
        key = (kind, number)
        assert key not in payloads
        payloads[key] = raw
        sym = symbol_by_address.get((kind, str(number)), {})
        row = dict(kind=kind, number=number, offset=offset, bytes=length,
                   data_words=(length - 10) // 2 if kind in {'DB', 'DX'} else '',
                   directory_flags_hex=f'{header[5]:02X}',
                   assembler_flag=bool(raw[4] & 8) if kind in main_types else '',
                   fb_header_name=raw[12:20].decode('cp850') if kind in {'FB', 'FX'} else '',
                   symbol=sym.get('symbol', ''), comment_de=sym.get('comment_de', ''),
                   sha256=sha(raw))
        inventory.append(row)

main_inventory = [r for r in inventory if r['kind'] in main_types]
csvfile('s5-program-blocks.csv', list(main_inventory[0]),
        sorted(main_inventory, key=lambda r: (r['kind'], r['number'])))
csvfile('s5-all-directory-blocks.csv', list(inventory[0]), inventory)

comments = []
comment_targets = {'PK': 'PB', 'FK': 'FB', 'OK': 'OB', 'DK': 'DB'}
for (kind, number), data in sorted(payloads.items()):
    if kind not in comment_targets:
        continue
    pos = 26
    if kind == 'DK':
        title_length = data[28] & 127
        title = data[29:29 + title_length].decode('cp850')
        comments.append(dict(block=f'{comment_targets[kind]}{number}',
                             source_comment_block=f'{kind}{number}',
                             record_offset=28, index='', record_type='title',
                             text_de=title))
        pos = 29 + title_length
    while pos < len(data):
        assert pos + 3 <= len(data)
        length = data[pos + 2] & 127
        assert pos + 3 + length <= len(data)
        text = data[pos + 3:pos + 3 + length].decode('cp850')
        comments.append(dict(block=f'{comment_targets[kind]}{number}',
                             source_comment_block=f'{kind}{number}',
                             record_offset=pos, index=data[pos],
                             record_type=f'0x{data[pos + 1]:02X}', text_de=text))
        pos += 3 + length
csvfile('s5-comment-records.csv', list(comments[0]), comments)

word_rows = []
for (kind, number), data in sorted(payloads.items()):
    if kind not in {'DB', 'DX'}:
        continue
    for word_index, offset in enumerate(range(10, len(data), 2)):
        word = data[offset:offset + 2]
        word_rows.append(dict(block=f'{kind}{number}', dw=word_index,
                              hex=word.hex().upper(), unsigned=int.from_bytes(word, 'big'),
                              signed=int.from_bytes(word, 'big', signed=True),
                              status='Surowa wartosc z archiwum; typ i aktualna nastawa niepotwierdzone'))
csvfile('db-raw-words.csv', list(word_rows[0]), word_rows)

# OB1 has only two-byte instructions and FB call descriptors in this supplied file.
# Keep the raw word and offset, and require the following FB descriptor to be valid.
ob1 = payloads[('OB', 1)]
calls = []
opcodes = {0x1d: ('SPB', 'FB'), 0x3d: ('SPA', 'FB'),
           0x4d: ('SPB', 'OB'), 0x55: ('SPB', 'PB'), 0x5d: ('SPB', 'SB'),
           0x6d: ('SPA', 'OB'), 0x75: ('SPA', 'PB'), 0x7d: ('SPA', 'SB')}
pos = 10
while pos < len(ob1):
    word = ob1[pos:pos + 2]
    assert len(word) == 2
    if word[0] in opcodes:
        command, kind = opcodes[word[0]]
        calls.append(dict(order=len(calls) + 1, block_offset=pos,
                          raw_hex=word.hex(), command=command,
                          target=f'{kind}{word[1]}',
                          conditional=(command == 'SPB'),
                          note='Kolejnosc zapisu w OB1; warunki wykonania wymagaja analizy logiki'))
        if kind == 'FB':
            descriptor = ob1[pos + 2:pos + 4]
            assert len(descriptor) == 2 and descriptor[0] == 0x2d
            assert descriptor[1] == 1, 'This OB1 reader does not decode FB parameters'
            pos += 2
    # These ranges can carry immediate payloads; stop rather than silently misalign.
    assert word[0] not in (0x30, 0x38, 0x58, 0x78)
    pos += 2
csvfile('ob1-call-sequence.csv', list(calls[0]), calls)

op_path = next((BASE / 'originals').rglob('*.O15'))
op = op_path.read_bytes()
op_texts = []
for match in re.finditer(rb'[\x20-\x7e]{8,}', op):
    text = match.group().decode('ascii').strip()
    if len(text) < 8 or not re.search('[A-Za-z]', text):
        continue
    if re.search(r'passw|kennwort|password', text, re.I):
        continue
    op_texts.append(dict(offset=match.start(), text=text,
                         status='Fragment ASCII; wpis moze byc nieaktywny, powtorzony lub niepelny'))
csvfile('op15-text-fragments.csv', list(op_texts[0]), op_texts)
alarm_fragments = [r for r in op_texts if re.match(r'\d{1,3}\s*:', r['text'])]
csvfile('op15-numbered-text-fragments.csv', list(op_texts[0]), alarm_fragments)

files = []
for p in sorted((BASE / 'originals').rglob('*')):
    if p.is_file():
        data = p.read_bytes()
        files.append(dict(path=str(p.relative_to(BASE)), bytes=len(data), sha256=sha(data)))
summary = dict(
    scope='Offline archive inventory; not a validated S7 program or decoded OP15 project',
    s5_sha256=sha(s5), op15_sha256=sha(op), files=files,
    symbols=len(symbols), symbol_counts=dict(Counter(s['area'] for s in symbols)),
    symbol_alarm_candidates=len(alarm_symbols),
    program_block_counts=dict(Counter(r['kind'] for r in main_inventory)),
    program_block_count=len(main_inventory), sections=sections,
    symbol_blocks_without_active_body=[f"{s['area']}{s['address']}" for s in symbols
                                       if s['area'] in main_types and
                                       (s['area'], int(s['address'])) not in payloads],
    active_blocks_without_symbol=[f"{r['kind']}{r['number']}" for r in main_inventory
                                  if (r['kind'], str(r['number'])) not in symbol_by_address],
    db1_ascii=payloads[('DB', 1)][10:].decode('ascii'),
    op15_marker=op[100:108].decode('ascii'),
    op15_text_fragments=len(op_texts),
    s5_comment_records=len(comments),
    ob1_calls=len(calls))
(OUT / 'inventory.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n',
                                    encoding='utf-8')
print(json.dumps({k: v for k, v in summary.items() if k not in {'files', 'sections'}},
                 ensure_ascii=False, indent=2))
