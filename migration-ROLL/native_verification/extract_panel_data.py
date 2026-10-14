#!/usr/bin/env python3
"""Derive byte mappings from verified native FB91/FB92 and COMTEXT tables.

Alarm message numbers are joined by source-symbol numbering and COMTEXT names;
the CSV states that distinction. No PLC/HMI connection or import is performed.
"""
from pathlib import Path
import csv
import json

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent


def read_csv(p):
    with p.open(encoding='utf-8-sig',newline='') as f:
        return list(csv.DictReader(f,delimiter=';'))


def write_csv(name,rows):
    with (HERE/name).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter=';');w.writeheader();w.writerows(rows)


def main():
    rows=[r for r in read_csv(HERE/'FB91-native-normalized-instructions.csv') if r['command']!='BLD']
    scratch={};writes=[]
    for i,r in enumerate(rows):
        if r['command']=='T' and r['operand'].startswith('MW ') and rows[i-1]['command']=='XOW':
            source=int(rows[i-3]['operand'].split()[1]);target=int(r['operand'].split()[1])
            assert rows[i-2]['operand']=='KH FFFF'
            scratch[target]=source;scratch[target+1]=source+1
        if r['command']=='T' and r['operand'].split()[0] in ['DL','DR']:
            load=rows[i-1];assert load['command']=='L' and load['operand'].startswith('MB ')
            byte=int(load['operand'].split()[1]);inverted=byte in scratch;source=scratch.get(byte,byte)
            area,dw=r['operand'].split();dw=int(dw)
            writes.append(dict(source_MB=source,source_expression=('NOT ' if inverted else '')+f'MB{source}',
                               target_DB=210,target_DW=dw,target_half=area,
                               target_bits='8..15' if area=='DL' else '0..7',
                               inverted=inverted,role='PLC acknowledgement' if dw>=17 else 'Alarm',
                               native_load_address=load['native_word_address'],native_store_address=r['native_word_address']))
    alarm=[r for r in writes if r['role']=='Alarm'];ack=[r for r in writes if r['role']=='PLC acknowledgement']
    assert len(alarm)==15 and [r['source_MB'] for r in alarm]==list(range(5,20))
    assert len(ack)==16 and [r['source_MB'] for r in ack]==list(range(5,21))
    assert all(not r['inverted'] for r in alarm) and all(r['inverted'] for r in ack)
    write_csv('FB91-byte-writes.csv',writes)
    symbols={(r['area'],r['address']):r for r in read_csv(ROOT/'analysis/symbols.csv')}
    messages={int(r['number']):r for r in read_csv(ROOT/'comtext_review/messages.csv') if r['kind']=='alarm'}
    alarms=[]
    for r in alarm:
        a=next(x for x in ack if x['source_MB']==r['source_MB'])
        assert a['target_DW']==r['target_DW']+17 and a['target_half']==r['target_half']
        for bit in range(8):
            number=(r['source_MB']-5)*8+bit+1
            symbol=symbols[('M',f"{r['source_MB']}.{bit}")]
            message=messages[number]
            wordbit=bit+(8 if r['target_half']=='DL' else 0)
            alarms.append(dict(number_from_symbol_and_COMTEXT=number,source_M=f"M{r['source_MB']}.{bit}",
                               source_symbol=symbol['symbol'],alarm_DB=210,alarm_DW=r['target_DW'],alarm_word_bit=wordbit,
                               PLC_ack_DW=a['target_DW'],PLC_ack_word_bit=wordbit,PLC_ack_expression='NOT '+f"M{r['source_MB']}.{bit}",
                               COMTEXT_name=message['name'],COMTEXT_text=message['text'],COMTEXT_pages=message['printed_pages'],
                               memory_mapping_status='Full native FB91 comparison confirmed',
                               message_number_basis='Matching source-symbol numbering and COMTEXT definitions; wire message numbering not separately tested',
                               generation_and_reset_status='See alarm-source-and-reset-map.csv for verified PB2 conditions and remaining external writers'))
    assert len(alarms)==120
    write_csv('alarm-memory-and-text-map.csv',alarms)
    fb92=json.loads((HERE/'FB92-comparison.json').read_text())
    args=fb92['call_arguments_compared'];assert len(args)==16
    events=[]
    for i in range(8):
        assert args[2*i]['value']==f'MW {37+2*i}' and args[2*i+1]['value']==f'DW {50+i}'
        for j in range(2):
            events.append(dict(source_MB=37+2*i+j,target_DB=210,target_DW=50+i,
                               target_half='DR' if j==0 else 'DL',
                               condition='M189.0 (N1 display active)',
                               evidence='Verified FB92 call arguments and native FB96 byte swap'))
    native92=read_csv(HERE/'FB92-native-normalized-instructions.csv')
    assert any(r['command']=='L' and r['operand']=='MB 53' and r['native_word_address']=='0106' for r in native92)
    assert any(r['command']=='T' and r['operand']=='DR 58' and r['native_word_address']=='0107' for r in native92)
    events.append(dict(source_MB=53,target_DB=210,target_DW=58,target_half='DR',
                       condition='M189.0 (N1 display active)',evidence='Native FB92 0106/0107'))
    write_csv('N1-event-byte-map.csv',events)
    summary=dict(alarm_bits_with_memory_map=120,alarm_byte_writes=15,PLC_ack_byte_writes=16,
                 extra_ack_byte='DB210 DL24 = NOT MB20; no matching alarm-byte write in FB91',
                 alarm_area_not_written_by_FB91=['DL7','DW8..16'],
                 ack_area_not_written_by_FB91=['DW25..33'],N1_event_source_bytes=17,
                 N1_event_limit='DL58 is preserved during active copying; 8000 is written to DW58 when the OR of DW50..58 is zero',
                 source_blocks=['FB91','FB92','FB96'],runtime_test=False)
    (HERE/'panel-data-evidence.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(summary))


if __name__=='__main__':
    main()
