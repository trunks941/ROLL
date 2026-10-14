# ROLL KS04201 — materiały migracji

**I/O — 14 października:** użytkownik potwierdził typy **430-7LA12 / 451-7LA12 / 454-7LA12**. [Wariant S7](hardware_review/DOBOR_IO_S7.md): 4 DI32, 4 DQ16/0,5 A i 2 DQ8/2 A, z zachowaniem adresów i fizycznych torów odcięcia. Zachowano klasy 0,5 A i 2 A; dane cewek nie będą ponownie zamawiane. Końcowe MLFB S7 i zaciski wymagają weryfikacji oficjalnych kart. Dostęp do katalogu został zablokowany przez politykę sieci; zapisano propozycję domen w ustawieniach środowiska.

Komplet **50 stron schematu** jest przeanalizowany. [Zasilanie i blokady](schematic_review/ZASILANIE_BLOKADY.md) wskazują G1 24 V/30 A, PNOZ, odcięcia ogrzewania, hamulce przez styczniki i zewnętrzne regulatory. [Mapa 208 kanałów](schematic_review/channel-wire-map-draft.csv) obejmuje zaciski S5, typy modułów i obwody mocy. Wentylator pozostaje na %Q24.4, lampka na %Q16.0. Potwierdzone pompa stacji 2, K19.14 i K-UHR mają zostać zachowane.

[Zdjęcie kasety](hardware_review/SPRZET_ZE_ZDJECIA.md) dokumentuje pojemność 128 DI i 80 DQ (64 z etykietą 0,5 A oraz 16 z etykietą 2 A). Użytkownik potwierdził, że to cały zestaw. 28 adresów programu poza etykietami i otrzymanymi stronami pozostaje do wyjaśnienia, bez przypisywania dodatkowych modułów.

**DB15 i DB19 są kompletne:** [nastawy i źródła](native_verification/DB15_DB19_NASTAWY.md), 264 słowa i 28 potwierdzonych parametrów. DB15 ma czasy zgodne z fabrycznymi; DB19 presety Z1=20/Z2=14 zamiast 5/5. T116/T117 mają po 5 s. Wzorzec fabryczny, otrzymany snapshot i receptury są odrębne.

Zacznij od [ustaleń etapu 2](USTALENIA_ETAP2.md) i [listy eksportów](EKSPORTY_DO_WERYFIKACJI.md).

Pierwsza partia wydruków natywnych STEP 5 jest kompletna: [weryfikacja OB1, FB105, FB61, OB13, OB21, OB22 i FB101](native_verification/WERYFIKACJA_STEP5.md). W OB1 zgadzają się 27 wywołań oraz 44 instrukcje pokazane tekstowo; dwie sieci graficzne porównano ręcznie. W pozostałych sześciu blokach porównano 272 pozycje. Rozstrzygnięto oznaczenie `7805` i poprawiono czytnik: tworzenie DB, nie DX.

[Szósta partia](native_verification/WERYFIKACJA_PARTIA6.md) potwierdziła wszystkie 181 sieci PB19/20/21/23/24/25. Łącznie porównano **42 pełne bloki**, w tym wszystkie PB z katalogu. FB51 pozostaje częściowy, FB0 bez natywnego wydruku. Zestawienia obejmują 37 zapisów wyjść procesu i kolejność wszystkich 61 zapisów do 60 bitów. [Lista braków](native_verification/BRAKUJACE_BLOKI_STEP5.md).

Otrzymano i przeanalizowano **128 stron natywnego wydruku COMTEXT ROLL@@LS.INI**: [ustalenia konfiguracji OP15](comtext_review/USTALENIA_COMTEXT.md). Wydruk dokumentuje cztery ekrany, dziesięć wpisów receptury PRG, adresy nastaw, klawisze, komunikaty i obszary wymiany. Użytkownik potwierdził dostępność trybu obrót/kołysanie; należy zachować go na TP900. Użytkownik dostarczył i potwierdził [komplet wartości programów 1 i 2](operator_recipes/RECEPTURY_OPERATORA.md): oba są identyczne, czasy są w sekundach, bęben obraca się, ruch pionowy jest wyłączony. Zakres wszystkich programów na panelu pozostaje do potwierdzenia.

Przygotowano [robocze założenia startu, taktów i nastaw dla S7](ZALOZENIA_START_NASTAWY_S7.md), z rozdzieleniem potwierdzonych faktów i proponowanej architektury oraz scenariuszami przyszłego porównania w symulacji.

Stara CPU **6ES5 942-7UB11**, pozycja **RE** i sprawna bateria są potwierdzone przez użytkownika. Przesłana instrukcja Edition 04 obejmuje dokładny model. [Ustalenia sprzętowe](CPU_S5_USTALENIA.md) potwierdzają interwał OB13 250 ms, retencję znaczników, opóźnienie konfiguracji przy następnym cyklu zasilania oraz zachowanie tworzenia istniejących DB. W `reference_manuals/` zachowano PDF, cytowania i zweryfikowane długości DB15/19: 132 słowa.

Oryginalne pliki S5, COMTEXT oraz schematy są w `originals/`. Sumy archiwów są zapisane w `analysis/inventory.json`, wydruków STEP 5 w `native_verification/native-files-inventory.json`, wydruku COMTEXT w `comtext_review/provenance.json`, schematów w `schematic_review/provenance.json` i `schematic_review/provenance-part2.json`. Program i panel nie zostały zmienione; nie powstał jeszcze projekt TIA do kompilacji/wgrania.

Mapa początkowa: [MAPA_MIGRACJI.md](MAPA_MIGRACJI.md). Dokładny przegląd danych panelu: [data_review/PRZEGLAD_DANYCH_HMI.md](data_review/PRZEGLAD_DANYCH_HMI.md). Ograniczenia czytnika i jego kontrola: [offline_decoder/README.md](offline_decoder/README.md).

Zestawienia można odtworzyć standardowym Pythonem 3, po rozpakowaniu całego katalogu. W podanej kolejności:

```sh
python analyse_archives.py
python offline_decoder/decode_mc5.py
python offline_decoder/test_decoder.py
python comtext_review/extract_comtext.py
python native_verification/compare_addressed_listings.py
python native_verification/review_pb16_fbd.py
python native_verification/compare_fbd_listings.py
python native_verification/test_fbd_reader.py
python native_verification/record_native_status.py
python data_review/review_data.py
python native_verification/extract_panel_data.py
python native_verification/extract_automation_control.py
python native_verification/extract_plant_control.py
python native_verification/read_runtime_db_listings.py
python native_verification/test_runtime_db_reader.py
python native_verification/record_native_status.py
python native_verification/extract_process_control.py
python operator_recipes/prepare_tables.py
python hardware_review/build_hardware_map.py
python hardware_review/build_S7_IO_variant.py
python schematic_review/build_power_map.py
python schematic_review/build_schematic_map.py
python schematic_review/check_schematic_artifacts.py
```

Polecenia odczytują kopie offline i zapisują zestawienia obok nich. Nie wykonują połączenia ze sterownikiem ani panelem. Kontrole czytnika nie są testami zachowania maszyny. CSV używają UTF-8 z BOM i separatora średnik.

`analysis-stage2/io-timer-counter-references.csv` jest dodatkowym zestawieniem statycznych odwołań z aktualnego `offline_decoder/instructions.csv`; nie jest konfiguracją sprzętu ani listą zakupową.

Źródła i licencja pomocniczego czytnika MC5: `offline_decoder/NOTICE.md`, `offline_decoder/LICENSE-LGPL-2.1.txt` i `offline_decoder/reference/`. Oryginalny program użytkownika nie otrzymuje przez to nowej licencji.
