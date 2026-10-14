#!/usr/bin/env python3
"""Extract the supplied COMTEXT printout offline, with printed-page citations.

This is a reader for this print layout, not an O15 project decoder. Source files
are never changed. Printed words, addresses and format labels remain literal.
"""
from pathlib import Path
import csv
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent
SOURCE = ROOT / "originals/comtext-native/ROLL@@LS.INI"
EXPECTED_SHA = "c1bfee8acb6d6a69d3e22973ea03b51c9a278d31500ef4da000fa846f32c4714"


def write_csv(name, rows):
    keys = list(dict.fromkeys(k for row in rows for k in row))
    with (OUT / name).open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)


def page_range(record):
    pages = sorted(record.pop("_pages"))
    record["printed_pages"] = ",".join(map(str, pages))
    return record


def records_named(pages, first, last):
    records, current = [], None
    for page in pages:
        if not first <= page["printed_page"] <= last:
            continue
        for line in page["lines"]:
            match = re.match(r"\s*Name:\s*(\S+)", line)
            if match:
                current = {"name": match[1], "_pages": set(), "lines": []}
                records.append(current)
            if current:
                current["_pages"].add(page["printed_page"])
                current["lines"].append(line)
    return records


def property_value(lines, label):
    for line in lines:
        match = re.match(r"\s*" + re.escape(label) + r"\s*(.*?)\s*$", line)
        if match:
            return match[1]
    return ""


def main():
    data = SOURCE.read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    assert sha == EXPECTED_SHA, "The source differs from the received printout"
    text = data.decode("cp437")
    # EOF/control padding is omitted only from derived text; original is intact.
    clean_text = text.replace("\x00", "").replace("\x1a", "").replace("\r\n", "\n")
    (OUT / "ROLL-COMTEXT.txt").write_text(clean_text, encoding="utf-8")
    pages = []
    for chunk in text.split("\f"):
        match = re.search(r"Page:\s*(\d+)", chunk)
        if not match:
            continue
        lines = chunk.replace("\x00", "").split("\n")
        borders = [i for i, line in enumerate(lines)
                   if re.fullmatch(r"\s*\+[+-]+\+\s*", line)]
        assert len(borders) >= 3
        lines = lines[borders[2] + 1:]
        body = [line.rstrip("\r ").replace("\x1a", "") for line in lines
                if line.strip() and not re.fullmatch(r"\s*(\+[+-]+\+|!\s*!)\s*", line)]
        pages.append({"printed_page": int(match[1]), "lines": body})
    assert [p["printed_page"] for p in pages] == list(range(1, 129))
    (OUT / "COMTEXT-pages.json").write_text(json.dumps(pages, ensure_ascii=False, indent=2) + "\n")

    # Screen/recipe membership, including entries continued on the next page.
    containers, memberships = [], []
    container, entry = None, None
    for page in pages:
        pn = page["printed_page"]
        if not 3 <= pn <= 5:
            continue
        for line in page["lines"]:
            match = re.match(r"\s*Name:\s*(\S+)\s+No:\s*(\d+)\s+Inf\. text:\s*(.*)", line)
            if match:
                container = {"kind": "recipe" if pn == 5 else "screen",
                             "number": int(match[2]), "name": match[1],
                             "info_text": match[3].strip(), "_pages": {pn}}
                containers.append(container)
                entry = None
                continue
            if container is None:
                continue
            container["_pages"].add(pn)
            if line.strip().startswith("Title:"):
                container["title"] = line.split(":", 1)[1].strip()
            if line.strip().startswith("Return link:"):
                container["return_link"] = line.split(":", 1)[1].strip()
            match = re.match(r"\s*(\d+)\s*!\s*(\S+)\s+(.*?)\s*!\s*(.*)", line)
            if match:
                entry = {"kind": container["kind"], "container": container["name"],
                         "container_number": container["number"], "entry_number": int(match[1]),
                         "entry_name": match[2], "text": match[3], "info_text": match[4],
                         "_pages": {pn}}
                memberships.append(entry)
            elif entry and line.lstrip().startswith("!"):
                columns = line.split("!")
                entry["text"] += "\n" + columns[1].strip()
                entry["_pages"].add(pn)
    containers = [page_range(c) for c in containers]
    memberships = [page_range(e) for e in memberships]
    write_csv("screens-and-recipes.csv", containers)
    write_csv("screen-and-recipe-membership.csv", memberships)

    linked = {e["entry_name"] for e in memberships}
    catalog = []
    for record in records_named(pages, 6, 16):
        lines = record.pop("lines")
        match = re.search(r"Polling time:\s*(\d+)\s*msec\s+Info text:\s*(.*)", lines[0])
        record.update(polling_ms=int(match[1]), info_text=match[2].strip(),
                      entry_type=property_value(lines, "Type:"),
                      linked_in_screen_or_recipe_list=record["name"] in linked)
        start = next(i for i, line in enumerate(lines) if line.startswith("Type:")) + 1
        source_text = []
        for line in lines[start:]:
            if line.lstrip().startswith("!"):
                break
            source_text.append(line)
        record["text"] = "\n".join(source_text)
        fields = re.findall(r"<([^<>]+)>", record["text"])
        record["field_names"] = " | ".join(re.sub(r"\s+", "", f) for f in fields
                                                if f != "CR" and not f.isdigit())
        catalog.append(page_range(record))
    write_csv("entry-catalog.csv", catalog)

    fields = []
    for record in records_named(pages, 74, 80):
        lines = record.pop("lines")
        type_line = property_value(lines, "Field type:")
        level = re.search(r"Passwordlevel:\s*(\d+)", type_line)
        record.update(field_type=re.split(r"\s+Passwordlevel:", type_line)[0],
                      access_level=int(level[1]) if level else "",
                      process_link=property_value(lines, "Process link:"),
                      bit_number=property_value(lines, "Bit - no.:"),
                      field_length=property_value(lines, "Field length:"))
        enums = []
        for line in lines:
            match = re.match(r"\s*(\d+)\s+(.+)", line)
            if match:
                enums.append(f"{match[1]}={match[2].strip()}")
        record["symbolic_values"] = " | ".join(enums)
        fields.append(page_range(record))
    write_csv("fields.csv", fields)

    tags = []
    for record in records_named(pages, 81, 86):
        lines = record.pop("lines")
        record.update(data_type=property_value(lines, "Data type:"),
                      data_format=property_value(lines, "Data format:"),
                      fractional_digits=property_value(lines, "Fractional digits:"),
                      lower_limit=property_value(lines, "Lower limit:"),
                      upper_limit=property_value(lines, "Upper limit:"))
        tags.append(page_range(record))
    tag_by_name = {t["name"]: t for t in tags}
    assert all(f["process_link"] in tag_by_name for f in fields)
    write_csv("process-tags.csv", tags)

    areas = []
    for page in pages:
        if page["printed_page"] not in [92, 93]:
            continue
        for line in page["lines"]:
            match = re.match(r"\s*(.*?)\s+DT DB\s+(\d+)\s+ADR\s+(\d+)\s+LW\s+(\d+)(.*)", line)
            if match:
                cycle = re.search(r"(PT|CT)\s+(\d+)", match[5])
                areas.append({"area_name": match[1], "db": int(match[2]),
                              "start_dw": int(match[3]), "length_words": int(match[4]),
                              "last_dw": int(match[3]) + int(match[4]) - 1,
                              "cycle_label": cycle[1] if cycle else "",
                              "cycle_ms": int(cycle[2]) if cycle else "",
                              "printed_pages": page["printed_page"]})
    write_csv("exchange-areas.csv", areas)

    keys, current = [], None
    for page in pages:
        if not 104 <= page["printed_page"] <= 106:
            continue
        for line in page["lines"]:
            match = re.search(r"FUNCTION KEY:\s*(\d+)\s*!\s*Keyboard image area:\s*(\d+)\s*!\s*Bit offset:\s*(\d+)", line)
            if match:
                current = {"key": int(match[1]), "keyboard_image_area": int(match[2]),
                           "keyboard_bit_offset": int(match[3]), "_pages": set()}
                keys.append(current)
            if current:
                current["_pages"].add(page["printed_page"])
                led = re.search(r"LED image area:\s*(\d+)\s*!\s*Bit offset:\s*(\d+)", line)
                if led:
                    current.update(led_image_area=int(led[1]), led_bit_offset=int(led[2]))
                fun = re.search(r"Function !\s*(.*?)\s*!! Repeat !\s*(\S+)", line)
                if fun:
                    prefix = "shift_" if re.search(r"!\s*Shift\s*!", line) else ""
                    current[prefix + "function"] = fun[1]
                    current[prefix + "repeat"] = fun[2]
                    level = re.search(r"PW Level\s*!\s*(\d+)", line)
                    current[prefix + "access_level"] = int(level[1]) if level else ""
    for page in pages:
        if page["printed_page"] != 107:
            continue
        for line in page["lines"]:
            match = re.match(r"\s*(\d+)\s*!", line)
            if match:
                params = [c.strip() for c in line.split("!")]
                key = next(k for k in keys if k["key"] == int(match[1]))
                key["parameter_1"] = params[3]
                key["_pages"].add(107)
    fb3_evidence = json.loads((ROOT / 'native_verification/FB3-comparison.json').read_text())
    assert fb3_evidence['block'] == 'FB3' and fb3_evidence['positions_compared'] == 216
    assert fb3_evidence['result'] == 'All positions, commands, operands, networks, lengths and jump targets match.'
    for key in keys:
        # Keep existing column names; the evidence status now records the
        # complete addressed native FB3 comparison instead of a pending one.
        n = key["key"]
        key["plc_flag_from_comparative_FB3"] = f"M{192 if n <= 8 else 193}.{(n-1)%8}"
        key["motion_flag_from_comparative_FB3"] = {13: "M190.5", 16: "M190.6"}.get(n, "")
        key["FB3_evidence_status"] = "Full native STEP 5 comparison confirmed"
        key["FB3_evidence_file"] = "native_verification/FB3-comparison.json"
        page_range(key)
    write_csv("keyboard.csv", keys)

    messages = []
    for kind, first, last in [("event", 17, 45), ("alarm", 46, 73)]:
        current = None
        for page in pages:
            if not first <= page["printed_page"] <= last:
                continue
            for line in page["lines"]:
                match = re.match(r"\s*No:\s*(\d+)\s+Name:\s*(\S+)\s+Printout:\s*(\S+)", line)
                if match:
                    current = {"kind": kind, "number": int(match[1]), "name": match[2],
                               "printout": match[3], "_pages": set(), "text_parts": [],
                               "collect_text": False}
                    messages.append(current)
                if current:
                    current["_pages"].add(page["printed_page"])
                    if "Info text:" in line and "Priority:" in line:
                        current["info_text"] = line.split("Info text:", 1)[1].split("Acknowl.", 1)[0].split("Priority:", 1)[0].strip()
                        current["priority"] = re.search(r"Priority:\s*(\d+)", line)[1]
                        current["collect_text"] = True
                    elif "Polling time:" in line:
                        current["polling_ms"] = int(re.search(r"Polling time:\s*(\d+)", line)[1])
                        current["collect_text"] = False
                    elif current["collect_text"]:
                        current["text_parts"].append(line.strip())
        for record in messages:
            if record["kind"] == kind:
                record["text"] = "\n".join(record.pop("text_parts"))
                record.pop("collect_text")
                page_range(record)
    write_csv("messages.csv", messages)

    help_texts = []
    for record in records_named(pages, 97, 102):
        lines = record.pop("lines")
        record["text"] = "\n".join(line.strip() for line in lines[1:]
                                    if not line.strip().startswith("Prog. language:"))
        help_texts.append(page_range(record))
    write_csv("help-texts.csv", help_texts)

    menus, items, current_menu, item = [], [], None, None
    for page in pages:
        if not 109 <= page["printed_page"] <= 128:
            continue
        for line in page["lines"]:
            match = re.match(r"\s*Menu no.:\s*(\d+)", line)
            if match:
                current_menu = {"menu_number": int(match[1]), "_pages": set()}
                menus.append(current_menu)
                item = None
            if not current_menu:
                continue
            current_menu["_pages"].add(page["printed_page"])
            for label, prop in [("Menu title:", "title"), ("Return link:", "return_link")]:
                if line.strip().startswith(label):
                    current_menu[prop] = line.strip()[len(label):].strip()
            match = re.match(r"\s*Menu item\s+(\d+)\s*$", line)
            if match:
                item = {"menu_number": current_menu["menu_number"], "item_number": int(match[1]), "_pages": set()}
                items.append(item)
            if item:
                item["_pages"].add(page["printed_page"])
                if line.strip().startswith("Menu text"):
                    item["text"] = line.strip()[len("Menu text"):].strip()
                if line.strip().startswith("Function:"):
                    item["function"] = line.split(":", 1)[1].strip()
                level = re.match(r"\s*Passwordlevel:\s*(\d+)", line)
                if level:
                    item["access_level"] = int(level[1])
    menus = [page_range(m) for m in menus]
    items = [page_range(i) for i in items]
    write_csv("menus.csv", menus)
    write_csv("menu-items.csv", items)

    counts = {"printed_pages": len(pages), "screens": sum(c["kind"] == "screen" for c in containers),
              "recipes": sum(c["kind"] == "recipe" for c in containers),
              "screen_entries_bound": sum(e["kind"] == "screen" for e in memberships),
              "recipe_entries_bound": sum(e["kind"] == "recipe" for e in memberships),
              "entry_catalog_definitions": len(catalog), "display_fields": len(fields),
              "process_links": len(tags), "configured_exchange_areas": len(areas),
              "function_keys": len(keys), "events": sum(m["kind"] == "event" for m in messages),
              "alarms": sum(m["kind"] == "alarm" for m in messages),
              "help_texts": len(help_texts), "menus": len(menus), "menu_items": len(items)}
    assert counts["screens"] == 4 and counts["recipe_entries_bound"] == 10
    assert len(keys) == 16 and len(fields) == 16 and len(tags) == 15
    assert all(e["entry_name"] in {c["name"] for c in catalog} for e in memberships)
    assert tag_by_name["ZEITNUMMER"]["data_type"] == "DB   15   DW  128"
    assert tag_by_name["ZAEHLWERT"]["data_format"] == "KC"
    for kind in ["event", "alarm"]:
        nums = [m["number"] for m in messages if m["kind"] == kind]
        assert len(nums) == len(set(nums))
    provenance = {"source": str(SOURCE.relative_to(ROOT)), "sha256": sha,
                  "size_bytes": len(data), "encoding_for_derived_text": "CP437",
                  "scope": "Native COMTEXT printout; no COMTEXT runtime or PLC hardware accessed",
                  "project_header": {"system": "CH-ROHRBOGEN 04201", "prepared": "04.03.94",
                                     "prepared_by_literal": "GL 05.05.98", "display": "2 * 40"},
                  "active_protocol": {"name": "AS511", "interface": "TTY", "baud": 9600,
                                      "parity": "EVEN", "data_bits": 8, "stop_bits": 1,
                                      "printed_pages": [87, 88]},
                  "interface_DB": {"number": 51, "printed_page": 92},
                  "recipe_compression": {"value": "OFF", "printed_page": 87},
                  "counts": counts,
                  "limits": ["Recipe records with actual operator values are not listed",
                             "Configured objects and unused definitions must be distinguished",
                             "FB91 byte order and FB89/90/111 recipe consumers verified natively; wire message numbering, FB51 body and remaining process behavior still need verification",
                             "COMTEXT KC format is kept literal, not treated as STEP 5 KC text syntax"]}
    provenance["native_keyboard_evidence"] = {
        "block": "FB3", "source_file": fb3_evidence["source_file"],
        "sha256": fb3_evidence["sha256"], "positions_compared": fb3_evidence["positions_compared"],
        "evidence_file": "native_verification/FB3-comparison.json",
        "scope": "Native comparison of FB3 keyboard decoding; process consumers still require verification"}
    provenance["user_confirmations"] = json.loads((OUT / "user-confirmations.json").read_text())
    (OUT / "provenance.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(counts, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
