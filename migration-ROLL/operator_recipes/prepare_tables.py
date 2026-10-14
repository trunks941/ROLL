#!/usr/bin/env python3
"""Render the confirmed user recipe records; no PLC connection or TIA import."""
from pathlib import Path
import csv
import json

ROOT = Path(__file__).resolve().parent


def main():
    source = json.loads((ROOT / "operator-recipes.json").read_text())
    records = source["records"]
    rows = []
    for record in records:
        assert record["complete"] and record["provided_fields"] == 10
        assert isinstance(record["actual_program_number"], int)
        assert len(record["fields"]) == 10
        for field in record["fields"]:
            assert field["provided"]
            kind = field["value_kind"]
            if kind == "time":
                assert field["unit_confirmed"] and field["confirmed_unit"] == "s"
                value = field["value_as_supplied"] * 1000
                assert value == field["normalized_time_ms"] and 0 <= value <= 2147483647
                target_type, target_unit = "TIME", "ms"
            elif kind == "bool":
                value = field["normalized_bool"]
                assert isinstance(value, bool)
                target_type, target_unit = "Bool", ""
            else:
                value = field["normalized_enum"]
                assert value in range(5)
                target_type, target_unit = "BasketMotion enum", ""
            rows.append({
                "program_number": record["actual_program_number"],
                "field_key": field["key"], "field_label_pl": field["label_pl"],
                "value_as_supplied": field["user_value_literal"],
                "confirmed_source_unit": "s" if kind == "time" else "",
                "proposed_s7_type": target_type, "normalized_s7_value": value,
                "normalized_s7_unit": target_unit,
                "comtext_entry_number": field["comtext_entry_number"],
                "comtext_entry_name": field["comtext_entry_name"],
                "legacy_consumer": field["legacy_consumer_from_comparative_PLC"],
                "legacy_mapping_status": field["legacy_mapping_status"],
            })
    signatures = [{f["key"]: (f.get("normalized_time_ms"), f.get("normalized_bool"),
                               f.get("normalized_enum")) for f in r["fields"]} for r in records]
    identical = all(s == signatures[0] for s in signatures)
    assert identical == source["provided_fields_identical_between_records"]
    with (ROOT / "operator-recipes.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter=";")
        writer.writeheader()
        writer.writerows(rows)

    report = [
        "# ROLL — potwierdzone zestawy receptur operatora", "",
        "Użytkownik przekazał wartości programów **1 i 2**, następnie potwierdził "
        "jednostkę **sekundy**, identyczność zestawów, ruch bębna **obrót** i ruch "
        "pionowy **aus**. Źródło: wiadomości z 9 października 2026 (Europe/Warsaw).", "",
        "**Oba programy mają komplet dziesięciu pól. Zachowano dwa osobne zestawy "
        "z różnymi numerami, zgodnie z potwierdzeniem użytkownika.** "
        "Są to zestawy danych tej samej definicji PRG nr 1 w COMTEXT. "
        "Nazwy własne programów nie zostały podane; numery są potwierdzone.", "",
        "| Pole | Program 1 | Program 2 | Typ i wartość proponowane dla S7 |",
        "|---|---:|---:|---|",
    ]
    for field in records[0]["fields"]:
        if field["value_kind"] == "time":
            display = f"{field['value_as_supplied']} s"
            target = f"TIME, {field['normalized_time_ms']} ms"
        elif field["value_kind"] == "bool":
            display = str(field["user_value_literal"])
            target = "Bool, " + ("TRUE" if field["normalized_bool"] else "FALSE")
        else:
            display = str(field["user_value_literal"])
            target = f"enum: {field['normalized_enum']} = obrót"
        report.append(f"| {field['label_pl']} | {display} | {display} | {target} |")
    report += ["",
        "Ultradźwięki są włączone, ruch bębna to obrót (wartość symboliczna 1), "
        "a ruch pionowy w kąpieli jest wyłączony. Wartości TIME zapisano w "
        "milisekundach po potwierdzeniu jednostki źródłowej. Wszystkie podane "
        "czasy są dokładnymi wielokrotnościami sekundy; nie zastosowano zaokrągleń.", "",
        "Powiązania z DB205 i kolejność pól odnoszą się do "
        "[konfiguracji COMTEXT](../comtext_review/USTALENIA_COMTEXT.md) oraz "
        "pełnych natywnych listingów FB90/FB111. "
        "[Trzecia partia](../native_verification/WERYFIKACJA_PARTIA3.md) "
        "potwierdza wszystkie dziesięć powiązań i odbiór skrzynki przez FB89; "
        "ciało FB51 i pozostały proces nadal wymagają dalszego sprawdzenia. "
        "Surowego kodowania KT w starym PLC nie odtworzono z samych liczb "
        "na ekranie, ponieważ tę samą wartość czasu można kodować różnymi bazami.", "",
        "Są to składniki receptury procesu PRG. Aktualne ogólne nastawy "
        "DB15/DB19 wymagają osobnego odczytu. Zakres tego zestawienia to "
        "dwa programy przekazane przez użytkownika; liczba wszystkich "
        "programów zapisanych w OP15 pozostaje niepotwierdzona.", "",
        "[Natywny PB13](../native_verification/WERYFIKACJA_PARTIA4.md) potwierdził, "
        "że wybrany obrót w automacie przechodzi na obrót interwałowy w "
        "fazach ociekania stacji 1–3 tych programów. Wybrana wartość receptury "
        "pozostaje 1 = obrót. Otrzymany [DB15](../native_verification/DB15_DB19_NASTAWY.md) "
        "ma nastawy interwału DB15.DW116 i DW117 po 5 s. "
        "To nastawy timerów załączenia/wyłączenia, nie dowód wykonanego czasu fizycznego ruchu.", "",
        "[Natywny PB14](../native_verification/WERYFIKACJA_PARTIA5.md) potwierdził, "
        "że BADHUB=aus wyłącza cykliczny krótki ruch w kąpieli. "
        "Normalne podnoszenie i opuszczanie transportu między stacjami "
        "pozostaje częścią programu. Wartość receptury FALSE pozostaje bez zmiany.", "",
        "Pliki: [operator-recipes.json](operator-recipes.json), "
        "[operator-recipes.csv](operator-recipes.csv) i "
        "[prepare_tables.py](prepare_tables.py). CSV dokumentuje wartości "
        "i proponowane typy, bez ustalonego schematu importu WinCC/TIA. "
        "Dane zapisano offline w dokumentacji migracji; nie wykonano "
        "operacji na sterowniku ani panelu.",
    ]
    (ROOT / "RECEPTURY_OPERATORA.md").write_text("\n".join(report) + "\n")
    print(json.dumps({"program_numbers": [r["actual_program_number"] for r in records],
                      "fields_per_record": 10, "csv_rows": len(rows), "identical": identical,
                      "time_unit": "seconds confirmed", "pending_information": source["pending_information"]}))


if __name__ == "__main__":
    main()
