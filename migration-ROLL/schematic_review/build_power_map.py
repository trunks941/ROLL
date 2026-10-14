#!/usr/bin/env python3
"""Export manually reviewed power circuits and independent hardware functions."""
from pathlib import Path
import csv
import hashlib
import json

HERE=Path(__file__).resolve().parent


def write(name, records):
    with (HERE/name).open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(records[0]),delimiter=';')
        writer.writeheader()
        for row in records:
            writer.writerow({k:' | '.join(map(str,v)) if isinstance(v,list) else v for k,v in row.items()})


def main():
    source=HERE/'power-observations.json'
    power=json.loads(source.read_text())
    write('power-loads-and-PLC.csv',power['power_loads'])
    write('independent-hardware-functions.csv',power['hardware_functions'])
    write('power-supplies.csv',power['power_supplies'])
    write('confirmed-modifications.csv',power['user_confirmed_modifications'])
    sheets=[]
    provenance=json.loads((HERE/'provenance-part2.json').read_text())
    photos={p['page_in_filename']:p for p in provenance['files']}
    for sheet in power['sheets']:
        sheets.append({**sheet,'source_image':photos[sheet['page']]['path'],
            'source_image_SHA256':photos[sheet['page']]['sha256']})
    write('power-sheet-observations.csv',sheets)
    addresses=[a for x in power['power_loads'] for a in x['output_addresses']]
    assert len(addresses)==len(set(addresses))==32
    assert len(sheets)==24 and sorted(photos)==list(range(1,25))
    assert not next(x for x in power['power_loads'] if x['id']=='PUMP_ST2_ADDED')['output_addresses']
    assert next(x for x in power['power_supplies'] if x['id']=='FIELD_24V')['output']=='DC24 V30 A, M/PE bond shown'
    result=dict(date=power['review_date'],source_SHA256=hashlib.sha256(source.read_bytes()).hexdigest(),
        manually_reviewed_new_pages=24,combined_received_pages=50,missing_pages=[],
        power_circuit_rows=len(power['power_loads']),outputs_with_identified_power_circuit=len(addresses),
        independent_hardware_function_rows=len(power['hardware_functions']),power_supply_rows=len(power['power_supplies']),
        user_confirmed_installed_and_working_modifications=len(power['user_confirmed_modifications']),
        regulator_contact_interfaces_retained=True,additional_analog_PLC_channels_inferred=False,
        additional_PLC_outputs_for_brakes_or_added_pump_inferred=False,PLC_coil_currents_established=False,
        installed_MLFBs_established=False,as_built_confirmation=power['as_built_confirmation'],
        PLC_or_hardware_changes=False,consistency_result='Passed')
    (HERE/'power-evidence.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__': main()
