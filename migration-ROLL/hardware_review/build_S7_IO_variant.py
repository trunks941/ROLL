#!/usr/bin/env python3
"""Build a structural S7 variant from confirmed S5 ratings and cutoff routes.

Target MLFBs and terminal numbers remain unassigned until official target-module
data is verified. The 9 A power-contact rating is never a PLC coil current.
"""
from pathlib import Path
import csv
import json

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent


def write(name, records):
    with (HERE/name).open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(records[0]),delimiter=';')
        writer.writeheader()
        writer.writerows(records)


def main():
    identification=json.loads((HERE/'module-identification.json').read_text())
    modules=[]
    for n,start in enumerate([0,4,8,12],1):
        modules.append(dict(proposed_module_id=f'S7_DI{n}',kind='DI',family='SM 521',
            channels=32,per_channel_nominal_A='',nominal_VDC=24,start_byte=start,end_byte=start+3,
            proposed_address_range=f'%I{start}.0..%I{start+3}.7',
            legacy_module=f'DI{n}',legacy_MLFB='6ES5 430-7LA12',
            required_supply_partition='5L+ input circuit' if start<8 else '6L+ input circuit',
            aggregate_current_requirement='Input characteristics and response compatible with existing contact/sensor interfaces',
            target_MLFB='',target_terminal_map='',status='Structural candidate; official target data not verified'))
    for n,start in enumerate([16,18,20,22],1):
        modules.append(dict(proposed_module_id=f'S7_DQ05_{n}',kind='DQ',family='SM 522',
            channels=16,per_channel_nominal_A=0.5,nominal_VDC=24,start_byte=start,end_byte=start+1,
            proposed_address_range=f'%Q{start}.0..%Q{start+1}.7',
            legacy_module='DQ1' if start<20 else 'DQ2',legacy_MLFB='6ES5 451-7LA12',
            required_supply_partition='Two independently supplied eight-channel groups; preserve each source cutoff route',
            aggregate_current_requirement='Inductive loads, group/module sums and temperature derating must cover the legacy operating envelope; retain feeder separation',
            target_MLFB='',target_terminal_map='',status='Structural candidate; official target data not verified'))
    for n,start in enumerate([24,25],1):
        modules.append(dict(proposed_module_id=f'S7_DQ2_{n}',kind='DQ',family='SM 522',
            channels=8,per_channel_nominal_A=2,nominal_VDC=24,start_byte=start,end_byte=start,
            proposed_address_range=f'%Q{start}.0..%Q{start}.7',
            legacy_module='DQ3',legacy_MLFB='6ES5 454-7LA12',
            required_supply_partition='11L+ through existing emergency-stop/door contacts; old half-byte groups have the same supply path',
            aggregate_current_requirement='Two legacy four-channel groups allow 4 A each; target must support their combined 8 A envelope at the design temperature, or retain equivalent separate groups',
            target_MLFB='',target_terminal_map='',status='Structural candidate; official target data not verified'))
    with (ROOT/'schematic_review/output-potential-groups.csv').open(encoding='utf-8-sig') as stream:
        legacy_groups=list(csv.DictReader(stream,delimiter=';'))
    groups=[]
    for source in legacy_groups:
        byte=int(source['S5_byte'][1:])
        module=next(m for m in modules if m['kind']=='DQ' and m['start_byte']<=byte<=m['end_byte'])
        groups.append(dict(legacy_byte=source['S5_byte'],legacy_group=source['group_index_within_byte'],
            legacy_channel_range=source['channel_range'],proposed_S7_module=module['proposed_module_id'],
            proposed_partition=f'Eight-channel section Q{byte}' if byte<24 else f'Four-channel section Q{byte}, half {source["group_index_within_byte"]}',
            existing_supply=source['supply_rail'],existing_cutoff_route=source['supply_route'],
            target_Lplus_pin='',target_M_pin='',
            grouping_rule='Keep independently fed from other byte of the 16-channel candidate' if byte<24 else
                'Separate half-byte groups preferred; combining permitted only with identical L+/M/cutoff route and sufficient total-current/thermal rating',
            status='Required supply route recorded; actual target terminal assignment pending official data'))
    channels=[]
    for module in modules:
        for index in range(module['channels']):
            byte=module['start_byte']+index//8; bit=index%8
            area='E' if module['kind']=='DI' else 'A'
            channels.append(dict(S5_address=f'{area}{byte}.{bit}',proposed_S7_address=f'%{"I" if area=="E" else "Q"}{byte}.{bit}',
                proposed_module_id=module['proposed_module_id'],module_channel_index=index,
                per_channel_nominal_A=module['per_channel_nominal_A'],
                target_MLFB='',target_terminal='',actual_coil_current_A='',
                source_basis='Confirmed legacy type/rating and drawing; not measured coil current'))
    assert sum(m['channels'] for m in modules if m['kind']=='DI')==128
    assert sum(m['channels'] for m in modules if m['kind']=='DQ')==80
    assert len(modules)==10 and len(groups)==12 and len(channels)==208
    assert len({r['proposed_S7_address'] for r in channels})==208
    assert next(r for r in channels if r['S5_address']=='A24.4')['proposed_S7_address']=='%Q24.4'
    assert next(r for r in channels if r['S5_address']=='A16.0')['proposed_S7_address']=='%Q16.0'
    for byte in [20,21,22,23]:
        match=next(g for g in groups if g['legacy_byte']==f'A{byte}')
        assert byte in [m['start_byte']+offset for m in modules if m['proposed_module_id']==match['proposed_S7_module'] for offset in range(m['channels']//8)]
    assert len({g['existing_cutoff_route'] for g in groups if g['legacy_byte'] in ['A20','A21','A22','A23']})==4
    write('S7-IO-layout-variant.csv',modules)
    write('S7-output-supply-assignment.csv',groups)
    write('S7-channel-assignment-variant.csv',channels)
    evidence=dict(date=identification['date'],confirmed_legacy_MLFBs=[t['MLFB'] for t in identification['module_types'].values()],
        structure={'DI32':4,'DQ16_0_5A':4,'DQ8_2A':2},proposed_IO_modules=10,
        DI_capacity=128,DQ_capacity=80,channel_rows=208,legacy_supply_group_rows=12,
        legacy_2A_channels_reduced_to_0_5A=False,coil_ratings_will_not_be_requested_again=True,
        actual_coil_currents_known=False,power_contact_rating_9A_used_as_coil_current=False,
        original_cutoff_routes_preserved_in_requirements=True,
        fan='%Q24.4',lamp='%Q16.0',
        target_MLFBs_or_terminal_assignments_final=False,
        official_S7_module_data_verified=False,
        network_check={'result':'HTTPS proxy CONNECT denied, HTTP 403','host':'mall.industry.siemens.com',
            'configuration_draft':'Saved domain additions for user review; requires publication, not applied to runtime',
            'proposed_domains':['mall.industry.siemens.com','support.industry.siemens.com','sieportal.siemens.com']},
        design_assumption='Existing installation operates within the documented legacy module limits; this is a selection envelope, not an electrical acceptance test',
        TIA_compiled=False,PLC_or_hardware_changes=False,consistency_result='Passed')
    (HERE/'S7-IO-variant-evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(evidence,ensure_ascii=False))


if __name__=='__main__': main()
