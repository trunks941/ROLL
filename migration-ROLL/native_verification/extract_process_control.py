#!/usr/bin/env python3
"""Build migration tables from the fully compared native process networks.

Only simplifies Boolean expressions for mutually exclusive manual selections;
does not simulate a scan, plant, timers or counters and is not a TIA import.
"""
from pathlib import Path
import csv
import json
import re
from compare_fbd_listings import canon,expression_text

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent


def read_csv(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f,delimiter=';'))


def write_csv(name,rows):
    with (HERE/name).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter=';');w.writeheader();w.writerows(rows)


def freeze(node):
    return tuple(freeze(x) if isinstance(x,list) else x for x in node)


def simplify(node,bindings):
    node=freeze(node);op=node[0]
    if op=='READ':return bindings.get(node[1],node)
    if op=='NOT':
        n=simplify(node[1],bindings)
        return ('BOOL',not n[1]) if n[0]=='BOOL' else canon('NOT',n)
    if op in ('AND','OR'):
        args=[simplify(x,bindings) for x in node[1:]]
        decisive=False if op=='AND' else True
        if any(a==('BOOL',decisive) for a in args):return ('BOOL',decisive)
        args=[a for a in args if a!=('BOOL',not decisive)]
        if not args:return ('BOOL',not decisive)
        return canon(op,*args)
    return node


def refs(node):
    if not node:return set()
    if node[0]=='READ':return {node[1]}
    if node[0] in ('NUMBER','TIME','COUNTER_PRESET','BOOL'):return set()
    return set().union(*(refs(x) for x in node[1:]))


def main():
    blocks={b:json.loads((HERE/f'{b}-comparison.json').read_text()) for b in ['PB2','PB3','PB4','PB13','PB17','PB18']}
    symbols={(r['area'],r['address']):r for r in read_csv(ROOT/'analysis/symbols.csv')}
    active={int(r['entry_number']):r for r in read_csv(ROOT/'comtext_review/screen-and-recipe-membership.csv') if r['kind']=='screen' and r['container_number']=='10'}
    catalog={r['name']:r for r in read_csv(ROOT/'comtext_review/entry-catalog.csv')}
    selectors=[]
    for b in ['PB3','PB4']:
        for net in blocks[b]['reviews']:
            for a in net['actions']:
                if a['command']!='=':continue
                expr=a['condition_ast'];assert expr[0]=='EQ'
                number=next(x[1] for x in expr[1:] if x[0]=='NUMBER')
                assert ['READ','MB 239'] in expr[1:]
                s=symbols[('M',a['target'].split()[1])]
                entry=active.get(number)
                selectors.append(dict(function_code=number,source_block=b,source_network=net['network'],selector_M=a['target'],
                                      selector_symbol=s['symbol'],selector_comment=s['comment_de'],active_on_COMTEXT_screen_10=bool(entry),
                                      COMTEXT_entry_name=entry['entry_name'] if entry else '',COMTEXT_entry_text=entry['text'] if entry else '',
                                      COMTEXT_help=catalog[entry['entry_name']]['info_text'] if entry else ''))
    assert len(selectors)==41 and len({s['function_code'] for s in selectors})==41
    allflags={s['selector_M'] for s in selectors}
    for s in selectors:
        bindings={flag:('BOOL',flag==s['selector_M']) for flag in allflags}
        for net in blocks['PB18']['reviews']:
            for a in net['actions']:
                if a['command']=='=':
                    bindings[a['target']]=simplify(a['condition_ast'],bindings)
        base=bindings['M 250.0'];work=bindings['M 252.0']
        s['base_position_condition']=expression_text(base);s['work_position_condition']=expression_text(work)
        s['status_source_bits']=' | '.join(sorted(refs(base)|refs(work)))
        source=refs(base)|refs(work)
        s['status_basis']='No PB18 base/work condition for this code' if not source else 'PLC output command' if all(x.startswith('A ') for x in source) else 'Sensor or internal state; see source bits'
        s['DB210_DW60_rule']='0 undefined; 1 base; 2 work; base has priority if both true (verified FB3)'
    write_csv('manual-function-and-position-map.csv',selectors)
    outputs=[];timers=[]
    for b in ['PB13','PB17']:
        for net in blocks[b]['reviews']:
            for a in net['actions']:
                if a['command']=='=' and a['target'].startswith('A '):
                    s=symbols[('A',a['target'].split()[1])]
                    outputs.append(dict(source_block=b,source_network=net['network'],output_A=a['target'],symbol=s['symbol'],comment=s['comment_de'],
                                        condition=a['condition'],output_bits_read=' | '.join(sorted(x for x in refs(a['condition_ast']) if x.startswith('A '))),
                                        scan_order_limit='Keep the native network order and OB1 call order; earlier and later output reads differ',
                                        hardware_limit='S5 software address only; physical wiring and S7 module/channel mapping pending schematic'))
    assert len(outputs)==22
    write_csv('transport-and-drum-output-map.csv',outputs)
    for b in ['PB2','PB13']:
        current_db=''
        for net in blocks[b]['reviews']:
            for a in net['actions']:
                if a['command']=='OPEN_DB':current_db=a['target']
                if a['command'] in ['SE','SA','ZR','ZV'] or (a['command']=='S' and a['target'].startswith('Z ')):
                    preset=a['preset'];duration=''
                    if preset.startswith('KT'):
                        count,base=preset[2:].split('.');duration=int(count)*[10,100,1000,10000][int(base)]
                    timers.append(dict(source_block=b,source_network=net['network'],operation=a['command'],target=a['target'],condition=a['condition'],
                                       preset=preset,preset_DB_context=current_db if preset.startswith('DW') else '',constant_preset_ms=duration,
                                       timing_basis='S5 timer operation and cycle order' if a['target'].startswith('T ') else 'S5 counter edges; preset is BCD',
                                       proposed_S7_family='TON candidate' if a['command']=='SE' else 'TOF candidate' if a['command']=='SA' else 'Counter with explicit preset and direction/edge handling',
                                       migration_limit='Static mapping only; retention, edge behavior and dynamic presets need behavioral comparison'))
    assert len(timers)==17
    write_csv('process-timer-and-counter-map.csv',timers)
    pb2={}
    for net in blocks['PB2']['reviews']:
        for a in net['actions']:
            if a['target'].startswith('M '):pb2.setdefault(a['target'],[]).append((net['network'],a))
    decoded=read_csv(ROOT/'offline_decoder/instructions.csv')
    verified={r['block'] for r in json.loads((HERE/'native-files-inventory.json').read_text())['verified_native_files']}
    plant_alarm={}
    plant_path=HERE/'plant-alarm-writes.csv'
    if plant_path.exists():
        for action in read_csv(plant_path):
            plant_alarm.setdefault(action['target'],[]).append(action)
    alarm_rows=[]
    for r in read_csv(HERE/'alarm-memory-and-text-map.csv'):
        target='M '+r['source_M'][1:];actions=pb2.get(target,[])
        writes=[x for x in decoded if x['operand']==target and x['command'] in ['=','S','R']]
        r.update(PB2_networks=' | '.join(str(n) for n,a in actions),
                 PB2_set_or_direct_condition=' | '.join(a['command']+': '+a['condition'] for n,a in actions if a['command'] in ['S','=']),
                 PB2_reset_condition=' | '.join(a['condition'] for n,a in actions if a['command']=='R'),
                 source_writers=' | '.join(dict.fromkeys(x['block'] for x in writes)),
                 writers_without_native_comparison=' | '.join(dict.fromkeys(x['block'] for x in writes if x['block'] not in verified)),
                 PB2_evidence='Full native network expression comparison confirmed' if actions else 'No direct write to this bit in PB2',
                 reset_order='PB2 S then R; reset wins when both are true' if any(a['command']=='R' for _,a in actions) else 'See direct/external source')
        additional=plant_alarm.get(target,[])
        r.update(plant_source_networks=' | '.join(dict.fromkeys(x['source_block']+':'+x['source_network'] for x in additional)),
                 plant_set_or_direct_condition=' | '.join(x['operation']+': '+x['condition'] for x in additional if x['operation'] in ['S','=']),
                 plant_reset_condition=' | '.join(x['condition'] for x in additional if x['operation']=='R'))
        r['generation_and_reset_status']='Compared PB2 and plant source conditions; other writers listed with their native verification status'
        alarm_rows.append(r)
    assert len(alarm_rows)==120 and sum(bool(r['PB2_networks']) for r in alarm_rows)==102
    write_csv('alarm-source-and-reset-map.csv',alarm_rows)
    summary=dict(manual_selector_codes=41,active_COMTEXT_manual_entries=len(active),
                 active_entries_with_compared_selector=sum(s['active_on_COMTEXT_screen_10'] for s in selectors),
                 transport_and_drum_output_writes=22,timer_operations=10,counter_operations=7,
                 alarm_bits_with_PB2_write=102,alarm_bits_without_PB2_write=18,
                 status_is_not_always_physical_feedback=True,runtime_test=False)
    (HERE/'process-data-evidence.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(summary))
    for s in selectors:
        if s['active_on_COMTEXT_screen_10']:print(s['function_code'],s['COMTEXT_entry_name'],s['base_position_condition'],s['work_position_condition'])


if __name__=='__main__':main()
