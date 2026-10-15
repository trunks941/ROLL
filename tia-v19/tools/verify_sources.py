#!/usr/bin/env python3
"""Cross-file source/contract checks. Does not parse or compile full Siemens SCL."""
import collections
import hashlib
import json
import re
import generate as gen


def conflicting_identifiers(source):
    # Narrow regression gate for the supplied native V19 syntax failures.
    # This does not replace the Siemens SCL parser or assert a complete keyword list.
    unsafe = {'timer', 'counter', 'db', 'compare'}
    return sorted({name for name in re.findall(r'^\s*([A-Za-z_]\w*)\s*:\s*(?!=)', source, re.M) if name.lower() in unsafe})


def main():
    bundle = (gen.OUT / 'ROLL_ALL.scl').read_text()
    conflicts = conflicting_identifiers(bundle)
    assert not conflicts, ('Identifiers rejected or implicated by native TIA import', conflicts)
    hashes = json.loads((gen.OUT / 'reports/source-hashes.json').read_text())
    for name, wanted in hashes.items():
        assert hashlib.sha256((gen.OUT / name).read_bytes()).hexdigest() == wanted, name
    functions = re.findall(r'^FUNCTION "(ROLL_\w+)"', bundle, re.M)
    definitions = re.findall(r'^(?:FUNCTION|DATA_BLOCK|TYPE) "(ROLL_\w+)"', bundle, re.M)
    duplicate = [name for name, count in collections.Counter(definitions).items() if count != 1]
    assert not duplicate, duplicate
    calls = set(re.findall(r'"(ROLL_\w+)"\(', bundle))
    assert not calls.difference(functions), sorted(calls.difference(functions))
    expected_pbs = {x['block'] for x in gen.csv_rows(gen.OLD / 'offline_decoder/instructions.csv') if x['block'].startswith('PB')}
    assert {name[5:] for name in functions if name.startswith('ROLL_PB')} == expected_pbs
    assert re.findall(r'^ORGANIZATION_BLOCK (OB\d+)', bundle, re.M) == ['OB100', 'OB1']
    # HMI fields read or written by source must be declared in the HMI DB.
    hmi = bundle.split('DATA_BLOCK "ROLL_HMI"', 1)[1].split('END_DATA_BLOCK', 1)[0]
    hmi_fields = set(re.findall(r'^    (\w+) : ', hmi, re.M))
    accessed = set(re.findall(r'"ROLL_HMI"\.(\w+)', bundle))
    assert not accessed.difference(hmi_fields), sorted(accessed.difference(hmi_fields))
    interface = gen.csv_rows(gen.OUT / 'hmi/interface.csv')
    assert len(interface) == 47
    for tag in interface:
        field = re.fullmatch(r'"ROLL_HMI"\.(\w+)(?:\[\d+\])?', tag['plc_symbol'])
        assert field and field[1] in hmi_fields, tag
        assert tag['native_binding_verified'] == 'False', tag
    screens = json.loads((gen.OUT / 'hmi/screens.json').read_text())
    assert set(screens['screens'][1]['fields']).issubset(hmi_fields)
    assert set(screens['basket_motion']) == set('01234')
    manual = gen.csv_rows(gen.OUT / 'hmi/manual-functions.csv')
    assert len(manual) == 14 and all(row['native_control_created'] == 'False' for row in manual)
    target = json.loads((gen.OUT / 'openness/target.json').read_text())
    assert all('6ES7513-1AM03-0AB0/' in value.replace(' ', '') for value in target['cpuIdentifiers'])
    assert all('6AV2124-0JC01-0AX0/' in value.replace(' ', '') for value in target['hmiIdentifiers'])
    assert target['hmiScreenControlsConfigured'] is False
    assert target['physicalIoConfigured'] is False
    coverage = json.loads((gen.OUT / 'reports/coverage.json').read_text())
    assert coverage['pb_count'] == 22
    assert all(row['tia_compiled'] is False for row in coverage['pb_coverage'])
    result = {
        'source_contract_checks_passed': True,
        'function_definitions': len(functions), 'unique_named_definitions': len(definitions),
        'unresolved_function_calls': [], 'hmi_scalars': len(interface), 'manual_functions': len(manual),
        'source_bundle_sha256': hashes['ROLL_ALL.scl'],
        'known_native_identifier_conflicts': conflicts,
        'tia_compiled': False, 'hmi_native_binding_verified': False, 'hardware_io_verified': False,
    }
    (gen.OUT / 'reports/source-contracts.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
