#!/usr/bin/env python3
"""Exploratory READ-ONLY STEP 5 MC5 listing. No execution or PLC writes.

Opcode table and core layout/matching ideas adapted from
DotNetSiemensPLCToolBoxLibrary, commit
3d3eea50d9b24b53481809585f73e67f93ddb1d9 (LGPL-2.1).
See NOTICE.md and LICENSE-LGPL-2.1.txt. This derivative decoder is LGPL-2.1.
Native STEP 5 comparison is required before relying on semantic equivalence.
"""
from pathlib import Path
from collections import Counter
import csv
import hashlib
import json

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
TABLE = json.loads((HERE / 'opcode_table.json').read_text())
JUMPS = {'SPA=', 'SPB=', 'SPZ=', 'SPN=', 'SPP=', 'SPM=', 'SPO='}
TYPE = {2:'E', 4:'D', 5:'T', 6:'Z', 7:'B', 8:'A'}
FMT = {16:'D', 32:'W', 64:'BY', 128:'BI'}
DFMT = {1:'KZ',2:'KT',4:'KF',8:'KG',16:'KC',32:'KY',64:'KH',128:'KM'}


def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f, delimiter=';'))


def write_csv(name, fields, rows):
    with (HERE / name).open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter=';')
        w.writeheader()
        w.writerows(rows)


def signed(n, bits):
    return n - (1 << bits) if n & (1 << (bits - 1)) else n


def lookup(data, pos):
    """Preserve upstream ordered matching, and expose ambiguous matches."""
    c16 = int.from_bytes(data[pos:pos+2], 'big')
    c32 = int.from_bytes(data[pos:pos+4], 'big') if pos+4 <= len(data) else None
    matches = []
    for idx, t in enumerate(TABLE):
        if t['codelen'] <= 16:
            ok = (c16 & t['cmask']) == t['code']
        else:
            ok = c32 is not None and (c32 & (t['cmask'] << (32-t['codelen']))) == ((t['code'] << 16) | t['code1'])
        if ok:
            matches.append(idx)
    return matches


def primitive(data, pos, parameters=()):
    if pos+2 > len(data):
        return dict(offset=pos, size=len(data)-pos, raw_hex=data[pos:].hex().upper(),
                    command='UNKNOWN', operand='', operand_area='', value=None,
                    issues=['ODD_TRAILING_BYTE'], table_index=None)
    matches = lookup(data, pos)
    if not matches:
        return dict(offset=pos, size=2, raw_hex=data[pos:pos+2].hex().upper(),
                    command='UNKNOWN', operand='', operand_area='', value=None,
                    issues=['UNKNOWN_OPCODE'], table_index=None)
    idx = matches[0]
    t = TABLE[idx]
    bits = t['codelen'] + t['parlen']
    # S5 instructions occupy whole words. One upstream QB entry totals 14 bits.
    length = ((bits + 15) // 16) * 2
    issues = []
    if bits % 16:
        issues.append(f'TABLE_NONWORD_BITS:{bits}')
    if pos+length > len(data):
        issues.append(f'TRUNCATED_INSTRUCTION_EXPECTED:{length}')
        length = len(data)-pos
    raw = data[pos:pos+length]
    if bits <= 16:
        val = int.from_bytes(raw[:2], 'big') & t['pmask']
    else:
        # Immediate bytes are not opcode bytes. This also correctly handles 48-bit
        # instructions, unlike the upstream find_mc5_param's >32-bit placeholder.
        val = int.from_bytes(raw, 'big') & t['pmask']
    if t['parlen'] == 0 and t['pmask']:
        issues.append('TABLE_PARAMETER_BITS_ZERO_WITH_MASK')
    if len(matches)>1 and any(TABLE[m]['cmask'].bit_count() >= t['cmask'].bit_count() for m in matches[1:]):
        issues.append('AMBIGUOUS_TABLE_MATCHES:' + ','.join(map(str,matches)))
    if t['operation']=='SVW':
        # Upstream leaves the packed nibble at bit 4 instead of normalizing it.
        val >>= 4
        issues.append('SVW_PACKED_NIBBLE_NORMALIZED_NATIVE_CHECK_REQUIRED')
    area=t['operand'] or ''
    if t['operation']=='E' and t['code']==0x7805:
        # Native STEP 5 V7.x FB105RLS.INI (SHA256 947e446a3f2937a85925e4a
        # 39cff7caf6256722626bc8b90989aec81008eb81c) prints all nine 7805
        # occurrences as G DB (English mnemonic; German E DB). Its absolute
        # listing 0018 G DB15 maps to block byte offset 003A, raw 7805000F.
        # See ../native_verification/FB105-comparison.json. Correct only the
        # operand label; preserve opcode_table.json and reference/*.cs.
        area='DB'
    fmt=t['formatter']
    arg=''
    if area=='PAR':
        if 1 <= val <= len(parameters):
            arg='='+parameters[val-1]['name']
        else:
            arg=f'=PAR[{val}]'; issues.append('INVALID_FORMAL_PARAMETER_INDEX')
    elif fmt:
        if fmt in ('PrintMerkerBit','PrintSMerkerBit'):
            shift=12 if fmt=='PrintSMerkerBit' else 8
            arg=f'{val & ((1<<shift)-1)}.{val>>shift}'
        elif area=='KT':
            digits=[(val>>n)&15 for n in (8,4,0)]
            basis=val>>12
            if basis>3 or any(n>9 for n in digits):
                issues.append('INVALID_KT_BCD_OR_BASE')
            arg=''.join(map(str,digits))+'.'+str(basis)
        elif area=='KZ':
            digits=[(val>>n)&15 for n in (8,4,0)]
            if val>>12 or any(n>9 for n in digits): issues.append('INVALID_KZ_BCD')
            arg=''.join(map(str,digits))
        elif area=='KF':
            arg=f'{signed(val,16):+d}'
        elif area=='KM':
            arg=f'{val:016b}'
        elif fmt=='PrintKY':
            arg=f'{val>>8},{val&255}'
        elif fmt=='PrintChar':
            arg=repr(val.to_bytes(2,'big').decode('cp850'))
            issues.append('KC_BYTE_ORDER_NATIVE_COMPARISON_REQUIRED')
        elif fmt in ('PrintHEX4','PrintHEX8'):
            arg=f'{val:0{8 if fmt=="PrintHEX8" else 4}X}'
        elif fmt=='PrintGleitpunkt':
            arg=f'RAW32:{val:08X}'; issues.append('KG_FLOAT_SEMANTICS_UNSUPPORTED')
        elif fmt in ('PrintNummer','PrintTimer'):
            arg=str(val)
            if fmt=='PrintTimer' and area not in ('KT','KZ','T'):
                issues.append('UNSUPPORTED_TIMER_FORMAT')
        else:
            arg=f'RAW:{val:X}'; issues.append(f'UNSUPPORTED_FORMATTER:{fmt}')
    operand=arg if area=='PAR' else ' '.join(x for x in (area,arg) if x)
    if t['operation'] in ('SAR=','SVZ=','SPR'):
        issues.append('CONTROL_FLOW_SEMANTICS_UNSUPPORTED')
    if t['operation']=='B':
        issues.append('INDIRECT_MODIFICATION_NEXT_INSTRUCTION')
    return dict(offset=pos,size=length,raw_hex=raw.hex().upper(),command=t['operation'],
                operand=operand,operand_area=area,value=val,issues=issues,
                table_index=idx)


def fb_declarations(data):
    assert len(data)>=20 and data[10]==0x2d, 'Missing FB entry SPA'
    displacement=data[11]
    assert displacement>=5 and (displacement-5)%3==0, 'Invalid FB declaration span'
    count=(displacement-5)//3
    start=10+displacement*2
    assert start<=len(data), 'FB declaration outside block'
    pars=[]
    for i in range(count):
        pos=20+i*6
        typ=TYPE.get(data[pos], f'UNKNOWN_TYPE_{data[pos]:02X}')
        fmt=(DFMT if typ=='D' else FMT).get(data[pos+1],f'UNKNOWN_FORMAT_{data[pos+1]:02X}')
        pars.append(dict(index=i+1,name=data[pos+2:pos+6].decode('cp850').rstrip(),type=typ,
                         format=fmt,offset=pos,raw_hex=data[pos:pos+6].hex().upper()))
    assert 20+count*6==start
    return start, pars


def actual_arg(raw, declaration):
    """Only independently observable formats from this project are supported."""
    value=int.from_bytes(raw,'big')
    fmt=declaration['format']; typ=declaration['type']; issues=[]
    if typ in ('E','A'):
        if fmt=='BI' and raw[0]&0xf0==0x80 and raw[0]&0xf < 8:
            text=f'M {raw[1]}.{raw[0]&0xf}'
        elif fmt in ('W','BY'):
            area={0x12:'MW',0x32:'DW',0x0a:'MB',0x2a:'DR',0x22:'DL'}.get(raw[0])
            if area and ((fmt=='W' and area in ('MW','DW')) or (fmt=='BY' and area in ('MB','DR','DL'))):
                text=f'{area} {raw[1]}'
            else: text=f'RAW:{raw.hex().upper()}'; issues.append('UNSUPPORTED_ARGUMENT_ADDRESS_AREA')
        else: text=f'RAW:{raw.hex().upper()}'; issues.append('UNSUPPORTED_ARGUMENT_FORMAT_OR_AREA')
    elif typ=='D':
        if fmt=='KF': text=f'KF {signed(value,16):+d}'
        elif fmt=='KH': text=f'KH {value:04X}'
        elif fmt=='KY': text=f'KY {raw[0]},{raw[1]}'
        elif fmt=='KM': text=f'KM {value:016b}'
        else: text=f'{fmt} RAW:{raw.hex().upper()}'; issues.append('UNSUPPORTED_CONSTANT_ARGUMENT_FORMAT')
    elif typ=='B' and raw[0]==0x20: text=f'DB {raw[1]}'
    elif typ in ('T','Z'): text=f'{typ} {raw[1]}'; issues.append('TIMER_COUNTER_ARG_AREA_NOT_VERIFIED')
    else: text=f'RAW:{raw.hex().upper()}'; issues.append('UNSUPPORTED_ARGUMENT_TYPE')
    return text, issues


def decode_body(data,start,parameters,interfaces):
    rows=[]; pos=start
    while pos<len(data):
        row=primitive(data,pos,parameters)
        row['arguments']=[]
        is_fb=row['command'] in ('SPA','SPB','BA','BAB') and row['operand_area'] in ('FB','FX')
        if is_fb:
            descriptor_pos=pos+row['size']
            if descriptor_pos+2>len(data) or data[descriptor_pos]!=0x2d or data[descriptor_pos+1]<1:
                row['issues'].append('INVALID_FB_CALL_DESCRIPTOR')
            else:
                span=data[descriptor_pos+1]*2
                row['call_descriptor_offset']=descriptor_pos
                row['call_descriptor_hex']=data[descriptor_pos:descriptor_pos+2].hex().upper()
                row['argument_span_words']=span//2-1
                if descriptor_pos+span>len(data):
                    row['issues'].append('TRUNCATED_FB_CALL_ARGUMENT_SPAN')
                    span=len(data)-descriptor_pos
                target=row['operand_area']+str(row['value'])
                declarations=interfaces.get(target)
                payload=data[descriptor_pos+2:descriptor_pos+span]
                if declarations is None:
                    row['issues'].append('CALLED_INTERFACE_MISSING')
                    declarations=[]
                # This project has only one-word address descriptors. Do not
                # pretend general KG/double-word signatures have been validated.
                if any(p['format'] in ('KG','D') for p in declarations):
                    row['issues'].append('MULTIWORD_CALL_ARGUMENT_FORMAT_UNSUPPORTED')
                if len(payload)!=2*len(declarations):
                    row['issues'].append(f'CALL_ARGUMENT_COUNT_MISMATCH:{len(payload)//2}:{len(declarations)}')
                for j in range(0,len(payload),2):
                    raw=payload[j:j+2]
                    decl=declarations[j//2] if j//2<len(declarations) else None
                    arg,issues=actual_arg(raw,decl) if decl else (f'RAW:{raw.hex().upper()}',['ARGUMENT_WITHOUT_DECLARATION'])
                    row['arguments'].append(dict(offset=descriptor_pos+2+j,raw_hex=raw.hex().upper(),
                         name=decl['name'] if decl else '',type=decl['type'] if decl else '',
                         format=decl['format'] if decl else '',value=arg,issues=issues))
                    row['issues'].extend(issues)
                row['size']+=span
                row['raw_hex']=data[pos:pos+row['size']].hex().upper()
        rows.append(row)
        assert row['size']>0
        pos+=row['size']
    assert pos==len(data)
    boundaries={r['offset'] for r in rows}
    for row in rows:
        if row['command'] in JUMPS:
            val=signed(row['value'],8)
            target=row['offset']+val*2
            row['jump_words_signed']=val
            row['jump_target_offset']=target
            row['jump_boundary_ok']=target in boundaries
            row['operand']=f'@{target:04X} (relative {val:+d} words)'
            if target not in boundaries: row['issues'].append('JUMP_TARGET_NOT_INSTRUCTION_BOUNDARY')
    return rows


def main():
    source=BASE/'originals/s5/s5/1998_07_03/04201@ST.S5D'
    raw=source.read_bytes()
    directory=read_csv(BASE/'analysis/s5-program-blocks.csv')
    symbols={(s['area'],s['address']):s for s in read_csv(BASE/'analysis/symbols.csv')}
    bodies={}; blocks={}; interfaces={}
    for b in directory:
        name=b['kind']+b['number']; off=int(b['offset']); length=int(b['bytes'])
        data=raw[off:off+length]
        assert hashlib.sha256(data).hexdigest()==b['sha256'], f'Changed original {name}'
        bodies[name]=data
        if b['kind'] not in ('OB','PB','FB','SB','FX'): continue
        start,pars=fb_declarations(data) if b['kind'] in ('FB','FX') else (10,[])
        blocks[name]=dict(directory=b,start=start,parameters=pars)
        if b['kind'] in ('FB','FX'): interfaces[name]=pars
    stats=[]; all_rows=[]; calls=[]; db_refs=[]; creates=[]; issue_rows=[]; arg_rows=[]; jumps=[]; params=[]; overlays=[]
    for name,block in blocks.items():
        b=block['directory']; data=bodies[name]; start=block['start']; off=int(b['offset'])
        assembler=b['assembler_flag']=='True'
        rows=[] if assembler else decode_body(data,start,block['parameters'],interfaces)
        block['rows']=rows
        for r in rows:
            if 'jump_target_offset' in r and not r['jump_boundary_ok'] and start <= r['jump_target_offset'] < len(data):
                target=r['jump_target_offset']
                overlay=primitive(data,target,block['parameters'])
                overlays.append(dict(block=name,source_offset=r['offset'],target_offset=target,
                     target_absolute_offset=off+target,raw_hex=overlay['raw_hex'],
                     alternate_command=overlay['command'],alternate_operand=overlay['operand'],
                     status='Alternate instruction at branch target overlaps linear immediate; native STEP 5 comparison required'))
        network=1
        for line,r in enumerate(rows,1):
            r['block']=name; r['absolute_offset']=off+r['offset']; r['line']=line; r['network']=network
            if r['command']=='BLD' and r['value']==255: network+=1
            # Block-local DB addressing depends on control flow and B modifiers;
            # attach symbols for absolute operands only, not guessed DB fields.
            key=(r['operand_area'], str(r['value']))
            if r['operand_area'] in ('M','E','A'):
                v=r['value']; key=(r['operand_area'],f'{v&255}.{v>>8}')
            sym=symbols.get(key,{})
            r['symbol']=sym.get('symbol',''); r['comment_de']=sym.get('comment_de','')
            all_rows.append(dict(block=name,offset=r['offset'],absolute_offset=r['absolute_offset'],
                raw_hex=r['raw_hex'],size=r['size'],command=r['command'],operand=r['operand'],
                operand_area=r['operand_area'],value=r['value'],network=r['network'],symbol=r['symbol'],
                comment_de=r['comment_de'],issues=' | '.join(r['issues'])))
            common=dict(source=name,offset=r['offset'],absolute_offset=r['absolute_offset'],raw_hex=r['raw_hex'])
            if r['command'] in ('SPA','SPB','BA','BAB') and r['operand_area'] in ('OB','PB','FB','SB','FX'):
                target=r['operand_area']+str(r['value'])
                calls.append(dict(**common,command=r['command'],target=target,
                     conditional=r['command'] in ('SPB','BAB'),
                     present_in_directory=target in blocks,argument_words=r.get('argument_span_words',''),
                     callee_assembler_flag=(blocks[target]['directory']['assembler_flag'] if target in blocks else ''),
                     status=('indirect target if previous B modifies this instruction; inspect context' if line>1 and rows[line-2]['command']=='B' else 'static call; conditions not evaluated')))
            if r['command'] in ('A','AX') and r['operand_area'] in ('DB','DX'):
                db_refs.append(dict(**common,command=r['command'],target=r['operand_area']+str(r['value']),
                           present_in_directory=r['operand_area']+str(r['value']) in bodies,
                           preceding_indirect_modifier=line>1 and rows[line-2]['command']=='B'))
            if r['table_index'] is not None and TABLE[r['table_index']]['reference_access']=='Create':
                table_operand=TABLE[r['table_index']]['operand']
                creates.append(dict(**common,reference_table_operand=f'{table_operand} {r["value"]}',
                     decoded_operand=r['operand'],target_number=r['value'],
                     archive_DB_present='DB'+str(r['value']) in bodies,archive_DX_present='DX'+str(r['value']) in bodies,
                     previous_command=rows[line-2]['command'] if line>1 else '',
                     previous_operand=rows[line-2]['operand'] if line>1 else '',
                     status='DB operand verified against native STEP 5 FB105RLS.INI; upstream DX label retained separately; PLC behavior not simulated' if r['command']=='E' and r['raw_hex'].startswith('7805') else 'Unverified semantic create operation'))
            for issue in r['issues']: issue_rows.append(dict(**common,issue=issue))
            for arg in r['arguments']:
                arg_rows.append(dict(source=name,call_offset=r['offset'],argument_offset=arg['offset'],
                     absolute_offset=off+arg['offset'],name=arg['name'],type=arg['type'],format=arg['format'],
                     raw_hex=arg['raw_hex'],value=arg['value'],issues=' | '.join(arg['issues'])))
            if 'jump_target_offset' in r:
                jumps.append(dict(**common,command=r['command'],signed_word_displacement=r['jump_words_signed'],
                            target_offset=r['jump_target_offset'],target_absolute_offset=off+r['jump_target_offset'],
                            instruction_boundary_ok=r['jump_boundary_ok']))
        for p in block['parameters']: params.append(dict(block=name,**p))
        counts=Counter(issue for r in rows for issue in r['issues'])
        unknown_bytes=sum(r['size'] for r in rows if r['command']=='UNKNOWN')
        stats.append(dict(block=name,bytes=len(data),code_start=start,code_bytes=len(data)-start,
                     assembler_flag=assembler,listed_instructions=len(rows),
                     consumed_code_bytes=sum(r['size'] for r in rows),unknown_bytes=unknown_bytes,
                     unsupported_raw_body_bytes=len(data)-start if assembler else 0,
                     direct_calls=sum(c['source']==name for c in calls),
                     formal_parameters=len(block['parameters']),jumps=sum(j['source']==name for j in jumps),
                     invalid_jump_boundaries=sum(j['source']==name and not j['instruction_boundary_ok'] for j in jumps),
                     issues=dict(counts)))
        text=[f'{name}: {b["symbol"]} — {b["comment_de"]}',
              'EXPLORATORY MC5 LISTING — not S7 source; native STEP 5 comparison required.',
              f'Source file offset: 0x{off:X}; block bytes: {len(data)}; SHA256: {b["sha256"]}',
              f'Directory flags: {b["directory_flags_hex"]}; assembler flag: {assembler}',
              f'Raw block header [0..9]: {data[:10].hex(" ").upper()}',
              f'Code starts at block offset 0x{start:04X}.']
        if b['kind'] in ('FB','FX'):
            text.append(f'FB name: {data[12:20].decode("cp850")!r}; entry SPA bytes: {data[10:12].hex().upper()}')
            for p in block['parameters']:
                text.append(f'  Formal #{p["index"]} @{p["offset"]:04X} {p["raw_hex"]}: {p["name"]} {p["type"]}/{p["format"]}')
        if assembler:
            text.append('UNSUPPORTED_ASSEMBLER_BODY: retained as raw bytes; no instruction claims.')
            for pos in range(start,len(data),16): text.append(f'{pos:04X} [{off+pos:06X}]  {data[pos:pos+16].hex(" ").upper()}')
        else:
            for r in rows:
                line=f'{r["offset"]:04X} [{r["absolute_offset"]:06X}]  {r["raw_hex"]:<26} {r["command"]:<6} {r["operand"]}'
                if r['symbol']: line+=f' ; {r["symbol"]} — {r["comment_de"]}'
                if r['issues']: line+=' ; FLAGS: '+' | '.join(r['issues'])
                text.append(line)
                if 'jump_target_offset' in r and not r['jump_boundary_ok']:
                    for alt in overlays:
                        if alt['block']==name and alt['source_offset']==r['offset']:
                            text.append(f'       Alternate branch-target decode @{alt["target_offset"]:04X}: {alt["raw_hex"]} {alt["alternate_command"]} {alt["alternate_operand"]}; overlaps linear listing.')
                if 'call_descriptor_hex' in r:
                    text.append(f'       Call descriptor @{r["call_descriptor_offset"]:04X}: {r["call_descriptor_hex"]}; argument words: {r["argument_span_words"]}')
                for arg in r['arguments']:
                    text.append(f'       Argument @{arg["offset"]:04X} {arg["raw_hex"]}: {arg["name"]} ({arg["type"]}/{arg["format"]}) = {arg["value"]}')
        (HERE/'listings'/f'{name}.txt').write_text('\n'.join(text)+'\n',encoding='utf-8')
    output=[('instructions.csv',list(all_rows[0]),all_rows),('direct-calls.csv',list(calls[0]),calls),
            ('db-open-references.csv',list(db_refs[0]),db_refs),('create-candidates.csv',list(creates[0]),creates),
            ('decoder-issues.csv',list(issue_rows[0]),issue_rows),('call-arguments.csv',list(arg_rows[0]),arg_rows),
            ('jump-references.csv',list(jumps[0]),jumps),('fb-parameters.csv',list(params[0]),params),
            ('jump-target-overlays.csv',list(overlays[0]),overlays)]
    for fname,fields,records in output: write_csv(fname,fields,records)
    serial_stats=[dict(s,issues=json.dumps(s['issues'],ensure_ascii=False)) for s in stats]
    write_csv('block-statistics.csv',list(serial_stats[0]),serial_stats)
    summary=dict(source=str(source),source_sha256=hashlib.sha256(raw).hexdigest(),blocks=len(stats),
        interpreted_blocks=sum(not s['assembler_flag'] for s in stats),assembler_blocks=sum(s['assembler_flag'] for s in stats),
        code_bytes=sum(s['code_bytes'] for s in stats),consumed_interpreted_code_bytes=sum(s['consumed_code_bytes'] for s in stats),
        unknown_bytes=sum(s['unknown_bytes'] for s in stats),unsupported_assembler_code_bytes=sum(s['unsupported_raw_body_bytes'] for s in stats),
        listed_instructions=len(all_rows),direct_calls=len(calls),open_references=len(db_refs),create_candidates=len(creates),
        jumps=len(jumps),invalid_jump_boundaries=sum(not j['instruction_boundary_ok'] for j in jumps),
        issue_counts=dict(Counter(i['issue'] for i in issue_rows)),block_statistics=stats)
    (HERE/'decoder-statistics.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    # Preserve the exact disjoint spans; hashes prove no changes to originals.
    for name,b in blocks.items():
        if b['directory']['assembler_flag']!='True':
            assert b['start']+sum(r['size'] for r in b['rows'])==len(bodies[name])
    print(json.dumps({k:v for k,v in summary.items() if k!='block_statistics'},ensure_ascii=False,indent=2))


if __name__=='__main__': main()
