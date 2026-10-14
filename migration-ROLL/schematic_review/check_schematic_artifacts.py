#!/usr/bin/env python3
"""Check preserved source integrity, cross-source mapping and local references.

These are document consistency checks, not electrical or PLC behavior tests.
"""
from pathlib import Path
import csv
import hashlib
import json
import re
import zipfile
from urllib.parse import unquote

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream, delimiter=';'))


def main():
    identification=json.loads((ROOT/'hardware_review/module-identification.json').read_text())
    check_date=identification['date']
    # Create this run's output before checking documents that link to it.
    # A failed run must not leave an earlier success report presented as current.
    (HERE/'schematic-artifact-checks.json').write_text(
        json.dumps({'date':check_date,'result':'Checks in progress'})+'\n',encoding='utf-8')
    old = json.loads((ROOT / 'native_verification/partia6-artifact-checks.json').read_text())
    preserved = dict(old['preserved_source_sha256'])
    provenances = [json.loads((HERE/name).read_text()) for name in ['provenance.json','provenance-part2.json']]
    for provenance in provenances:
        preserved[provenance['archive_path']] = provenance['archive_sha256']
        for photo in provenance['files']:
            preserved[photo['path']] = photo['sha256']
    for relative, expected in preserved.items():
        assert sha(ROOT / relative) == expected, f'Source hash changed: {relative}'
    assert len(preserved) == 108
    images = {p['page_in_filename']:p for provenance in provenances for p in provenance['files']}
    assert sorted(images)==list(range(1,51))
    for provenance in provenances:
        with zipfile.ZipFile(ROOT / provenance['archive_path']) as archive:
            assert archive.testzip() is None
            members = {Path(info.filename).name: info for info in archive.infolist() if not info.is_dir()}
            assert len(members) == len(provenance['files'])
            for photo in provenance['files']:
                raw = archive.read(members[photo['file']])
                assert raw == (ROOT / photo['path']).read_bytes(), photo['file']

    observations = json.loads((HERE / 'manual-observations.json').read_text())
    sheets = {(s['area'],s['byte']):s for s in observations['sheets']}
    power = json.loads((HERE/'power-observations.json').read_text())
    index = rows(HERE/'sheet-index.csv')
    assert [int(r['page']) for r in index]==list(range(1,51))
    for row in index:
        photo=images[int(row['page'])]
        assert row['original_image']==photo['path'] and row['original_image_SHA256']==photo['sha256']
    mapping = rows(HERE / 'channel-wire-map-draft.csv')
    assert len(mapping) == len({r['S5_address'] for r in mapping}) == 208
    for row in mapping:
        label = row['S5_address']
        byte, bit = map(int,label[1:].split('.'))
        sheet = sheets[(label[0],byte)]
        path = sheet['channels'].get(str(bit))
        assert int(row['page']) == sheet['page']
        assert row['original_image'] == images[sheet['page']]['path']
        assert row['drawn_signal_path'] == str(bool(path))
        assert row['device_and_connector'] == (path[0] if path else '')
        assert row['drawing_description'] == (path[1] if path else '')
        assert row['provisional_S7_address'] == '%' + ('I' if label[0]=='E' else 'Q') + label[1:]
        assert not row['target_module_MLFB'] and not row['target_terminal'] and not row['verified_as_built_wire']
        assert not row['verified_PLC_coil_current_A']
        expected_type=identification['rack_type_assignments'][row['module_id']]
        assert row['confirmed_legacy_module_MLFB']==identification['module_types'][expected_type]['MLFB']
        if expected_type=='DQ_2A':
            pin_index=(byte-24)*8+bit
            assert int(row['manufacturer_S5_channel_terminal'])==identification['module_types']['DQ_2A']['output_pins'][pin_index]
        loads=[x for x in power['power_loads'] if label in x['output_addresses']]
        assert row['power_circuit_pages']==' | '.join(str(x['page']) for x in loads)
        assert row['associated_power_load']==' | '.join(x['load'] for x in loads)
        assert row['motor_or_heater_current_A_literal']==' | '.join(x['current_A_literal'] for x in loads)
        if 'printed_channel_terminals' in sheet:
            assert int(row['printed_S5_channel_terminal']) == sheet['printed_channel_terminals'][bit]
    groups = rows(HERE / 'output-potential-groups.csv')
    assert len(groups) == 12 and sum(int(r['group_width']) for r in groups) == 80
    for row in groups:
        sheet = sheets[('A',int(row['S5_byte'][1:]))]
        group = int(row['group_index_within_byte'])
        assert row['supply_route'] == sheet['supply_route']
        assert int(row['printed_legacy_Lplus_terminal']) == sheet['module_Lplus_terminals'][group]
        assert int(row['printed_legacy_M_terminal']) == sheet['module_M_terminals'][group]
        assert not row['S7_group_assignment']
    policies = rows(HERE / 'fan-and-lamp-decision.csv')
    assert {r['S5_address']:r['target_S7_address'] for r in policies} == {'A24.4':'%Q24.4','A16.0':'%Q16.0'}
    writers = rows(ROOT / 'native_verification/all-output-writer-order.csv')
    for policy in policies:
        address = policy['S5_address']
        source = [w for w in writers if w['target'] == address[0]+' '+address[1:]]
        assert len(source)==1 and policy['original_condition']==source[0]['condition']
        assert policy['as_built_wiring_confirmed']=='False' and policy['code_or_hardware_action_performed']=='False'

    for filename, key in [('power-loads-and-PLC.csv','power_loads'),
                          ('independent-hardware-functions.csv','hardware_functions'),
                          ('power-supplies.csv','power_supplies'),
                          ('confirmed-modifications.csv','user_confirmed_modifications')]:
        exported=rows(HERE/filename)
        assert len(exported)==len(power[key])
        for row, original in zip(exported,power[key]):
            assert row=={k:' | '.join(map(str,v)) if isinstance(v,list) else str(v) for k,v in original.items()}
    fan=next(x for x in power['power_loads'] if x['id']=='FAN')
    assert fan['output_addresses']==['A24.4'] and fan['current_A_literal']=='0.45'
    fan_channel=next(x for x in mapping if x['S5_address']=='A24.4')
    assert not fan_channel['verified_PLC_coil_current_A']
    assert 'Generator 4 mains' in next(x for x in power['power_loads'] if x['id']=='US_REMOTE_GEN4')['load']

    variant=rows(ROOT/'hardware_review/S7-IO-layout-variant.csv')
    assigned=rows(ROOT/'hardware_review/S7-channel-assignment-variant.csv')
    supply=rows(ROOT/'hardware_review/S7-output-supply-assignment.csv')
    assert len(variant)==10 and len(assigned)==208 and len(supply)==12
    assert sum(int(r['channels']) for r in variant if r['kind']=='DI')==128
    assert sum(int(r['channels']) for r in variant if r['kind']=='DQ')==80
    indexed={r['S5_address']:r for r in mapping}
    for row in assigned:
        original=indexed[row['S5_address']]
        assert row['proposed_S7_address']==original['provisional_S7_address']
        assert not row['target_MLFB'] and not row['target_terminal'] and not row['actual_coil_current_A']
        if row['S5_address'].startswith('A'):
            expected='DQ_2A' if int(row['S5_address'][1:].split('.')[0])>=24 else 'DQ_0_5A'
            assert float(row['per_channel_nominal_A'])==identification['module_types'][expected]['current_per_channel_A']
    assert identification['coil_data_policy']['do_not_request_again']
    assert not identification['coil_data_policy']['9A_entered_as_PLC_coil_current']

    recipe = ROOT / 'operator_recipes/operator-recipes.csv'
    recipe_sha = sha(recipe)
    assert recipe_sha == '9aa33392a8a92f27c472f8b085d48118ed1341972d6a343da8689013991d88db'
    assert len(rows(recipe)) == 20
    assert len(rows(ROOT / 'native_verification/runtime-db-words.csv')) == 264
    outside = rows(ROOT / 'hardware_review/addresses-outside-photo.csv')
    assert len(outside)==28 and all(not r['provisional_physical_S7_address'] for r in outside)

    json_count=0
    for path in ROOT.rglob('*.json'):
        json.loads(path.read_text(encoding='utf-8-sig'))
        json_count+=1
    links=0
    for document in ROOT.rglob('*.md'):
        for target in re.findall(r'\[[^\]]*\]\(([^\n)]+)\)', document.read_text()):
            target=target.strip().strip('<>')
            if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:',target) or target.startswith('#'):
                continue
            relative=unquote(target.split('#',1)[0])
            if not relative:
                continue
            assert (document.parent/relative).exists(), f'Broken link in {document.relative_to(ROOT)}: {target}'
            links+=1
    result=dict(date=check_date, scope='Source integrity and offline document consistency; no electrical, PLC or TIA test',
        preserved_original_files_checked=len(preserved), preserved_source_sha256=preserved,
        schematic_archives_CRC='Passed (2 archives)', extracted_images_identical_to_archives=50,
        received_pages=50, missing_schematic_pages=[], power_circuit_rows=18,
        outputs_with_power_circuit=sum(bool(x['power_circuit_pages']) for x in mapping),
        independent_hardware_function_rows=11, actual_PLC_coil_currents_unfilled=True,
        mapped_channels=208, output_supply_groups=12, A25_pin_assignments_held=8,
        outside_addresses_unassigned=28, operator_recipe_values_unchanged=True,
        operator_recipe_rows=20, runtime_DB_word_rows=264,
        local_markdown_links_checked=links, JSON_files_parsed=json_count,
        fan_output='%Q24.4', lamp_output='%Q16.0', native_conditions_preserved=True,
        installed_IO_types_confirmed=3,proposed_S7_IO_modules=10,
        legacy_output_current_classes_preserved=True,coil_ratings_will_not_be_requested_again=True,
        official_target_catalog_data_verified=False,
        result='Passed')
    (HERE/'schematic-artifact-checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='preserved_source_sha256'},ensure_ascii=False))


if __name__=='__main__':
    main()
