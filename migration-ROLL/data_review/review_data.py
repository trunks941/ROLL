#!/usr/bin/env python3
"""Offline evidence only; read original catalogued bytes, write data_review only."""
from pathlib import Path
import csv
import hashlib
import json

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'data_review'
RAW_PATH = ROOT / 'originals/s5/s5/1998_07_03/04201@ST.S5D'
RAW = RAW_PATH.read_bytes()

def read_csv(name):
    with (ROOT/'analysis'/name).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f, delimiter=';'))

def write_csv(name, rows):
    with (OUT/name).open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter=';')
        w.writeheader()
        w.writerows(rows)

DIRECTORY = {(r['kind'], int(r['number'])): r for r in read_csv('s5-all-directory-blocks.csv')}
SYMBOLS = {(r['area'], r['address']): r for r in read_csv('symbols.csv')}
COMMENTS = read_csv('s5-comment-records.csv')
TAGS = {1:'KM',2:'KH',3:'KY',4:'KC',5:'KF',6:'KT',7:'KZ',8:'KG',11:'A',12:'C'}
CODE_CSV = ROOT/'offline_decoder/instructions.csv'
with CODE_CSV.open(encoding='utf-8-sig', newline='') as f:
    CODE = {int(r['absolute_offset']):r for r in csv.DictReader(f, delimiter=';')}
for off, row in CODE.items():
    assert RAW[off:off+int(row['size'])].hex().upper() == row['raw_hex'].replace(' ','').upper()

def body(kind, number):
    r = DIRECTORY[(kind, number)]
    offset, size = int(r['offset']), int(r['bytes'])
    b = RAW[offset:offset+size]
    assert hashlib.sha256(b).hexdigest() == r['sha256'], (kind, number, 'hash mismatch')
    return offset, b

def regions(number):
    offset, b = body('DV', number)
    # Comparative source MC5toDB.GetDB uses header[6:8] for type entries;
    # type tag at 9+4*n, begin DW at 10+4*n, next begin is exclusive end.
    ntypes = (int.from_bytes(b[6:8], 'big')-2)//2
    assert 12+ntypes*4 == len(b)
    result = []
    for n in range(ntypes):
        tag = b[9+4*n]
        start = int.from_bytes(b[10+4*n:12+4*n], 'big')
        end = int.from_bytes(b[14+4*n:16+4*n], 'big')
        assert end >= start
        result.append(dict(block=f'DB{number}', dv_offset=offset,
                           dv_type_entry_file_offset=offset+8+4*n,
                           type_tag_hex=f'{tag:02X}', declared_format=TAGS.get(tag, f'unknown_{tag:02X}'),
                           dw_begin=start, dw_end_exclusive=end,
                           dw_last_inclusive=end-1,
                           evidence='Current directory DV bytes; comparative MC5toDB.GetDB and S7DataRowType enum',
                           confidence='High for raw bytes; comparative format pending native STEP 5 confirmation'))
    return result

REGIONS = {n:regions(n) for n in [12,16,206,219]}
write_csv('declared-db-format-regions.csv', [r for rs in REGIONS.values() for r in rs])

def numeric_bcd(word):
    digits = [(word >> shift)&15 for shift in [0,4,8]]
    return (all(d<=9 for d in digits), digits[0]+10*digits[1]+100*digits[2])

typed = []
for number in [12,16]:
    offset, b = body('DB', number)
    count = len(b)//2-5
    assert int.from_bytes(b[8:10], 'big') == len(b)//2
    assert REGIONS[number][0]['dw_begin'] == 0
    assert REGIONS[number][-1]['dw_end_exclusive'] == count
    for dw in range(count):
        word = int.from_bytes(b[10+2*dw:12+2*dw], 'big')
        reg = next(r for r in REGIONS[number] if r['dw_begin'] <= dw < r['dw_end_exclusive'])
        fmt = reg['declared_format']
        valid_bcd, magnitude = numeric_bcd(word)
        time_base = (word >> 12)&3
        validity = 'format_KH_does_not_establish_BCD_semantics'
        decoded_ms = ''
        decoded_seconds = ''
        if fmt == 'KT':
            if word&0xC000 or not valid_bcd:
                validity = 'invalid_KT_reserved_bits_or_BCD_digits'
            else:
                validity = 'valid_KT_encoding_usage_not_established'
                decoded_ms = magnitude * [10,100,1000,10000][time_base]
                decoded_seconds = format(decoded_ms/1000, '.3f')
        if word == 0xFFFF:
            validity += ';FFFF_slot_skipped_by_FB101_do_not_use_as_numeric_setting'
        if dw >= 128:
            validity += ';outside_FB105_default_copy_range_0_to_127_not_timer_or_counter_setting'
        area = 'T' if number == 12 else 'Z'
        sym = SYMBOLS.get((area, str(dw)), {})
        typed.append(dict(
            block=f'DB{number}', dw=dw, source_s5d_offset=offset+10+2*dw,
            raw_hex=f'{word:04X}', raw_unsigned=word,
            raw_signed=word if word<32768 else word-65536,
            declared_format=fmt, format_dv_offset=reg['dv_offset'],
            format_entry_offset=reg['dv_type_entry_file_offset'],
            validity=validity,
            kt_base_ms=[10,100,1000,10000][time_base] if fmt=='KT' else '',
            kt_bcd_magnitude=magnitude if fmt=='KT' and valid_bcd else '',
            kt_decoded_ms=decoded_ms, kt_decoded_seconds=decoded_seconds,
            counter_three_digit_bcd_candidate=magnitude if number==16 and valid_bcd and word&0xF000==0 else '',
            same_index_symbol=sym.get('symbol',''), symbol_source_line=sym.get('line',''),
            same_index_comment_de=sym.get('comment_de',''),
            association_status=('DB19 DW1/2 consumed by PB13 S Z1/Z2; default copied DB16 to DB19 by FB105'
                                if number==16 and dw in [1,2] else
                                'Z3 set from code constant KZ500; DB16 DW3 not a usable preset'
                                if number==16 and dw==3 else
                                'Outside FB105 copy range; raw encoding is not a timer/counter assignment'
                                if dw>=128 else
                                'Copied source slot0..127 to runtime DB by FB105; same-number T/Z association otherwise requires use-site'),
            confirmed_counter_preset_default=magnitude if number==16 and dw in [1,2] and valid_bcd else '',
            runtime_use_source_offsets='PB13 0xFDA8/0xFDAA' if number==16 and dw==1 else
                                       'PB13 0xFDCA/0xFDCC' if number==16 and dw==2 else '',
            value_scope='Archive default-source bytes; not online DB15/DB19 settings',
        ))
write_csv('timer-counter-defaults.csv', typed)

hmi_words = []
for number in [205,206,210,211,213,219]:
    offset, b = body('DB', number)
    for dw in range(len(b)//2-5):
        word = int.from_bytes(b[10+2*dw:12+2*dw], 'big')
        reg = next((r for r in REGIONS.get(number, []) if r['dw_begin']<=dw<r['dw_end_exclusive']), None)
        comments = [c for c in COMMENTS if c['block']==f'DB{number}' and c['index']==str(dw)]
        hmi_words.append(dict(block=f'DB{number}', dw=dw, source_s5d_offset=offset+10+2*dw,
                              raw_hex=f'{word:04X}', raw_unsigned=word,
                              declared_format=reg['declared_format'] if reg else 'Not present in current directory DV',
                              comment_de=' | '.join(c['text_de'] for c in comments),
                              comment_evidence=' | '.join(c['source_comment_block']+':'+c['record_offset'] for c in comments),
                              value_scope='Archive bytes; field function requires code/COMTEXT evidence'))
write_csv('hmi-db-raw-typed-evidence.csv', hmi_words)

hs = [r for r in SYMBOLS.values() if (r['area']=='M' and 187<=int(r['address'].split('.')[0])<=199)
      or (r['area']=='MW' and r['address']=='192')]
write_csv('hmi-key-and-status-symbols.csv', hs)

op_path = ROOT/'originals/OP15/OP15/1998_05_11/04201.O15'
op_bytes = op_path.read_bytes()
op_fragments = []
for f in read_csv('op15-text-fragments.csv'):
    off = int(f['offset'])
    if 39931<=off<=40400 or 42753<=off<=43120:
        # ASCII fragment selection remains literal source evidence, not O15 structure decoding.
        assert op_bytes[off:off+len(f['text'])] == f['text'].encode('ascii')
        op_fragments.append(dict(source_file='04201.O15', source_offset=off,
                                 text_ascii=f['text'],
                                 interpretation_limit='Raw ASCII fragment; active entry, linkage and duplicate status unknown'))
write_csv('op15-parameter-key-help-fragments.csv', op_fragments)

VERIFIED_NATIVE_BLOCKS = {
    r['block'] for r in json.loads(
        (ROOT/'native_verification/native-files-inventory.json').read_text()
    )['verified_native_files']
}

def code_fact(offsets, source_fact, interpretation, confidence='Comparative MC5 listing; native STEP 5 confirmation required'):
    rows = [CODE[off] for off in offsets]
    if all(r['block'] in VERIFIED_NATIVE_BLOCKS for r in rows):
        confidence = 'Full native STEP 5 comparison confirmed; process behavior not executed'
    return dict(block=' | '.join(dict.fromkeys(r['block'] for r in rows)),
                s5d_offsets=' | '.join(f'0x{off:X}' for off in offsets),
                raw_hex=' | '.join(r['raw_hex'] for r in rows),
                source_instructions=' | '.join(r['command']+' '+r['operand'] for r in rows),
                source_fact=source_fact, interpretation=interpretation, confidence=confidence)

code_facts = [
    code_fact([0x20B0,0x20B2,0x20B6,0x20BE], 'FB101 DB15 compares indexed slot with FFFF; equal case increments selector DW128', 'FFFF marks a skipped editable slot'),
    code_fact([0x2100,0x2102,0x2106,0x210E], 'FB101 DB19 compares indexed slot with FFFF; equal case increments selector DW128', 'FFFF marks a skipped editable slot'),
    code_fact([0x2098,0x20C6,0x20CE,0x20D0,0x20D6,0x20DC,0x20E0], 'FB101 DB15 accesses DW128 selector; DW129 comparison/previous selector; DW130 buffer load/store; indexed DW0 update', 'Runtime DB15 tail is parameter-editor state, not T128..T130'),
    code_fact([0x20EA,0x2116,0x211E,0x2120,0x2126,0x212C,0x2130], 'FB101 DB19 accesses DW128 selector; DW129 comparison/previous selector; DW130 buffer load/store; indexed DW0 update', 'Runtime DB19 tail is parameter-editor state, not Z128..Z130'),
    code_fact([0x21C0,0x21EA,0x21F0,0x21F2,0x21F4,0x21F6,0x21F8,0x21FA], 'FB105 initializes128, subtracts1, uses indexed DW0 load DB12 then store DB15', 'Default copy processes indices127..0 only; source tail values128+ are not copied'),
    code_fact([0x2240,0x2244,0x2246,0x2248,0x224A,0x224C], 'FB105 indexed DW0 load DB16 then store DB19', 'Counter default copy follows the analogous indexed loop'),
    code_fact([0xFD88,0xFDA8,0xFDAA,0xFDCA,0xFDCC], 'PB13 opens DB19, loads DW1 then S Z1 and DW2 then S Z2', 'DW1/2 are consumed as S5 counter presets; declarations KH do not supersede instruction semantics'),
    code_fact([0x101DE,0x101E2], 'PB13 loads KZ500 then S Z3', 'Z3 preset is code constant500; not default DB16 DW3'),
    code_fact([0x189C,0x18A2,0x18A4,0x18AC,0x18AE,0x18B8], 'FB89 DB205 DW0 split high/low byte; high byte compared1 and low byte range1..99', 'Recipe1, data sets1..99 recognized; native compare confirmation required'),
    code_fact([0x2446,0x244A,0x2470,0x247C,0x248A,0x248C], 'FB3 DB211 DW5/DW6 bytes compared1/10 and byte of DW6 storedMB239', 'Active screen-type/number and selected manual function govern decoding'),
    code_fact([0x249C,0x24D0,0x24D2,0x24D6,0x24D8,0x2542,0x2544,0x2554,0x2556], 'FB3 DB211 DW2 toMW240; high-byte bit4 toM190.5/F13, bit7 toM190.6/F16', 'PLC ground/work-position keys share held-state bits with F13/F16; COMTEXT confirms K13 offset12 and K16 offset15'),
    code_fact([0x24E6,0x24E8,0x24EA,0x24EC,0x24EE,0x24F2,0x24F4,0x24F6], 'FB3 generates M190.3 when either position key true and edge-memory M190.4 false, resets memory when both released', 'Edge is for OR of two keys; switching key while the other stays pressed does not make a new combined edge'),
    code_fact([0xDCC6,0xDCC8,0xDD30,0xDD36], 'PB16 M190.6 contributes as level to conveyor2 M74.4 and horizontal-forward M75.4', 'Some manual motion branches require held-state semantics; do not turn all keys into one-shot commands'),
    code_fact([0x1C4A,0x1C4C,0x1C4E,0x1C50,0x1C56,0x1C58,0x1C5A,0x1C5C,0x1C62,0x1C64,0x1C6A,0x1C6C,0x1C6E,0x1C70,0x1C72,0x1C74,0x1C76,0x1C78,0x1C7A,0x1C7C,0x1C7E], 'FB92 F2 sets/resets M196.1 with helper M194.1; later reset in the same network includes M192.1', 'F2 press clears M196.1 by the end of the network; partial toggle fragment is not the final persistent state'),
]
write_csv('hmi-and-parameter-code-evidence.csv', code_facts)

recipe = []
for dw, role, use_offsets, coding in [
    (5,'Tauchzeit Station1 / czas zanurzenia stacji1',[0x231E,0x199C],'S5 KT consumed by T1'),
    (9,'Abtropfzeit Station1 / czas ociekania stacji1',[0x23A0],'S5 KT consumed by T2'),
    (13,'Ultraschall Station1 / ultradzwieki stacji1',[0x1A3C,0x1A3E,0x1A42,0x1A44],'equals1 enables M111.4; other values do not'),
    (17,'Tauchzeit Station2 / czas zanurzenia stacji2',[0x232A,0x19B2],'S5 KT consumed by T1'),
    (21,'Abtropfzeit Station2 / czas ociekania stacji2',[0x23AC],'S5 KT consumed by T2'),
    (25,'Tauchzeit Station3 / czas zanurzenia stacji3',[0x2336,0x19C8],'S5 KT consumed by T1'),
    (29,'Abtropfzeit Station3 / czas ociekania stacji3',[0x23B8],'S5 KT consumed by T2'),
    (33,'Station4 / czas suszenia stacji4; native comment Tauchzeit',[0x2342,0x19DE],'S5 KT consumed by T1'),
    (37,'Drehbewegung / wybor ruchu bebna',[0x19F4,0x1A00,0x1A0C,0x1A18],'1 rotation;2 swing;3 interval rotation;4 rotation/swing'),
    (41,'Hubbewegung / ruch pionowy w kapieli',[0x1A2A,0x1A2C,0x1A30,0x1A32],'equals1 enables M111.3; other values do not'),
    (45,'Unresolved tuple value outside the ten active PRG entries',[],'No consumer identified; received COMTEXT has no eleventh PRG field')]:
    off,b=body('DB',205)
    word=int.from_bytes(b[10+2*dw:12+2*dw],'big')
    recipe.append(dict(block='DB205',dw=dw,source_s5d_offset=off+10+2*dw,raw_hex=f'{word:04X}',
                       interpreted_role=role,code_s5d_offsets=' | '.join(f'0x{x:X}' for x in use_offsets),
                       consumer_blocks=' | '.join(dict.fromkeys(CODE[x]['block'] for x in use_offsets)),
                       coding_from_use_site=coding,
                       archive_value_runtime_enum_status='Outside recognized enum; archive buffer not valid data set evidence'
                            if (dw==37 and word not in [1,2,3,4]) or (dw in [13,41] and word not in [0,1]) else
                            'Current recipe value not established from archive snapshot',
                       confidence='Full native FB90/FB111 comparison and active COMTEXT PRG entries confirmed'
                            if use_offsets and all(CODE[x]['block'] in VERIFIED_NATIVE_BLOCKS for x in use_offsets) else
                            'No active COMTEXT PRG entry or native PLC consumer identified'))
write_csv('recipe-fields-from-code.csv',recipe)

summary = dict(source_file=str(RAW_PATH), source_sha256=hashlib.sha256(RAW).hexdigest(),
               op15_source_sha256=hashlib.sha256(op_bytes).hexdigest(),
               source_catalogue=str(ROOT/'analysis/s5-all-directory-blocks.csv'),
               comparative_reference_commit='3d3eea50d9b24b53481809585f73e67f93ddb1d9',
               declared_formats={str(n):REGIONS[n] for n in REGIONS},
               defaults_counts={str(n):{
                   'word_count':len([r for r in typed if r['block']==f'DB{n}']),
                   'FFFF_count':len([r for r in typed if r['block']==f'DB{n}' and r['raw_hex']=='FFFF']),
                   'valid_KT_words':len([r for r in typed if r['block']==f'DB{n}' and r['kt_decoded_ms']!='']),
                   'nonFFFF_words':[(r['dw'],r['raw_hex'],r['declared_format'],r['kt_decoded_ms'])
                                    for r in typed if r['block']==f'DB{n}' and r['raw_hex']!='FFFF']}
                                  for n in [12,16]})
(OUT/'evidence-summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps(summary['defaults_counts'], ensure_ascii=False, indent=2))
