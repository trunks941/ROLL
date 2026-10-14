#!/usr/bin/env python3
"""Prepare the reviewable HMI contract, not fictional WinCC import XML."""
import csv
import json
import re
import generate as gen


LABELS = {
    'Connected': 'Połączenie z panelem', 'ManualFunction': 'Wybrana funkcja ręczna',
    'GroundHeld': 'Pozycja podstawowa', 'WorkHeld': 'Pozycja robocza',
    'SelectedProgram': 'Wybrany program', 'CurrentProgram': 'Aktywny program',
    'Dwell1Seconds': 'Zanurzenie — stacja 1 [s]', 'Drain1Seconds': 'Ociekanie — stacja 1 [s]',
    'Ultrasound1': 'Ultradźwięki — stacja 1', 'Dwell2Seconds': 'Zanurzenie — stacja 2 [s]',
    'Drain2Seconds': 'Ociekanie — stacja 2 [s]', 'Dwell3Seconds': 'Zanurzenie — stacja 3 [s]',
    'Drain3Seconds': 'Ociekanie — stacja 3 [s]', 'Dry4Seconds': 'Suszenie — stacja 4 [s]',
    'BasketMotion': 'Ruch bębna', 'BathLift': 'Ruch pionowy w kąpieli',
    'ProcessTimer1Units': 'Pozostały czas zanurzenia / suszenia [jednostki T1]',
    'ProcessTimer2Units': 'Pozostały czas ociekania [jednostki T2]',
    'ParameterIndex': 'Numer nastawy', 'ParameterValue': 'Wartość nastawy [ms lub szt.]',
    'ParameterCurrentValue': 'Aktualna nastawa [ms lub szt.]', 'ParameterSlotPresent': 'Nastawa dostępna',
}
MANUAL = {
    1: 'Dojazd do pozycji podstawowej', 7: 'Drzwi załadunkowe',
    20: 'Podnoszenie / opuszczanie wózka', 21: 'Przejazd wózka',
    22: 'Obrót / ustawienie bębna prosto', 23: 'Kołysanie / ustawienie bębna prosto',
    36: 'Napełnianie stacji 1–3 wodą demineralizowaną',
    50: 'Napełnianie stacji 1–3 ze zbiornika czystego RAV',
    60: 'Przepompowywanie do stacji 1–3 i osadnika',
    65: 'Przepompowywanie do zbiornika brudnego RAV',
    66: 'Pompa dozowania środka przeciwpiennego RAV',
    72: 'Przepompowywanie do instalacji odbiorczej',
    73: 'Napełnianie parownika RAV ze zbiornika brudnego',
    99: 'Kasowanie znaczników śledzenia kosza',
}


def csv_write(path, rows):
    assert rows
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, rows[0].keys(), delimiter=';', lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def main():
    text = (gen.OUT / 'sources/00-runtime.scl').read_text().split('DATA_BLOCK "ROLL_HMI"', 1)[1].split('END_DATA_BLOCK', 1)[0]
    read_only = {'Connected', 'RecipeAck', 'RecipeError', 'ParameterAck', 'ParameterError', 'CurrentProgram', 'ProcessTimer1Units', 'ProcessTimer2Units', 'ParameterCurrentValue', 'ParameterSlotPresent'}
    tags = []
    for name, datatype in re.findall(r'^    (\w+) : (Bool|Int|DInt|Word)\b', text, re.M):
        tags.append({'tag': name, 'plc_symbol': f'"ROLL_HMI".{name}', 'data_type': datatype, 'direction': 'PLC->HMI' if name in read_only else 'HMI->PLC', 'label_pl': LABELS.get(name, ''), 'native_binding_verified': False})
    for n in range(1, 17):
        tags.append({'tag': f'KeyF{n}', 'plc_symbol': f'"ROLL_HMI".KeyF[{n}]', 'data_type': 'Bool', 'direction': 'HMI->PLC', 'label_pl': f'Klawisz F{n} (obsługa dawnego OP15)', 'native_binding_verified': False})
    csv_write(gen.OUT / 'hmi/interface.csv', tags)
    manual = []
    for row in gen.csv_rows(gen.OLD / 'comtext_review/screen-and-recipe-membership.csv'):
        if row['container'] != 'HANDBETRIEB':
            continue
        code = int(row['entry_number'])
        assert code in MANUAL, row
        manual.append({'code': code, 'label_pl': MANUAL[code], 'legacy_entry': row['entry_name'], 'legacy_text_de': row['text'].replace('\n', '').replace('<CR>', ' / '), 'press_ground': 'ROLL_HMI.GroundHeld=TRUE', 'press_work': 'ROLL_HMI.WorkHeld=TRUE', 'release_or_screen_change': 'set both held commands FALSE', 'native_control_created': False})
    assert len(manual) == 14
    csv_write(gen.OUT / 'hmi/manual-functions.csv', manual)
    screens = {
        'status': 'specification; native WinCC controls and binding pending local API/export',
        'panel': 'TP900 Comfort 6AV2124-0JC01-0AX0', 'language': 'pl-PL',
        'screens': [
            {'name': 'Przeglad', 'title': 'Przegląd maszyny', 'content': ['Stacje 1–4', 'Wózek i bęben', 'Aktywny program', 'Status połączenia']},
            {'name': 'Receptury', 'title': 'Programy mycia', 'programs': [1, 2], 'fields': list(LABELS)[5:15], 'commands': {'load': 1, 'save_and_apply': 2}, 'commit': 'set RecipeCommand then increment RecipeRequest; wait for RecipeAck and check RecipeError'},
            {'name': 'Reczny', 'title': 'Sterowanie ręczne', 'functions_csv': 'manual-functions.csv', 'held_motion': ['GroundHeld', 'WorkHeld']},
            {'name': 'Alarmy', 'title': 'Alarmy', 'source': '../../migration-ROLL/comtext_review/messages.csv', 'pending': ['translations', 'FB91 byte order / inverted acknowledgement bits', 'native alarm classes and bindings']},
            {'name': 'Nastawy', 'title': 'Nastawy serwisowe', 'parameter_db': [15, 19], 'commit': 'set DB/index/value then increment ParameterRequest; wait for ParameterAck', 'range': [0, 127], 'counter_unit': 'szt.', 'timer_unit': 'ms'},
        ],
        'heartbeat': {'symbol': 'ROLL_HMI.Heartbeat', 'period_ms': 500, 'plc_timeout_ms': 1500, 'pending': 'native global cyclic WinCC event'},
        'basket_motion': {'0': 'Brak', '1': 'Obrót', '2': 'Kołysanie', '3': 'Obrót interwałowy', '4': 'Obrót / kołysanie'},
    }
    # Explicit recipe field names, independent of dictionary display order.
    screens['screens'][1]['fields'] = ['Dwell1Seconds', 'Drain1Seconds', 'Ultrasound1', 'Dwell2Seconds', 'Drain2Seconds', 'Dwell3Seconds', 'Drain3Seconds', 'Dry4Seconds', 'BasketMotion', 'BathLift']
    (gen.OUT / 'hmi/screens.json').write_text(json.dumps(screens, indent=2, ensure_ascii=False) + '\n')
    print(f'HMI contract: {len(tags)} scalar tags, {len(manual)} native OP15 manual functions; WinCC binding pending.')


if __name__ == '__main__':
    main()
