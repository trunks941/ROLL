# ROLL — migracja Siemens S5-115U / OP15 do S7-1513 / TP900

Komplet materiałów zgromadzonych podczas analizy maszyny Karl Roll KS04201. Główny katalog [migration-ROLL](migration-ROLL/README.md) zawiera oryginalne archiwa, wydruki STEP 5 i COMTEXT, instrukcję S5, komplet 50 stron schematu, zestawienia oraz skrypty analizy offline.

**TIA V19:** [instrukcja i narzędzia](tia-v19/README.md), [źródło PLC ROLL_ALL.scl](tia-v19/ROLL_ALL.scl). Raport z 15.10.2026, godz. 12:09 potwierdził kompilację aktualnego PLC: **0 błędów, 1 ostrzeżenie** dotyczące nieprzypisanych modułów I/O, oraz retencję sześciu DB. CPU i TP900 są utworzone w zapisanym projekcie użytkownika. W repozytorium są źródła, narzędzia i natywne eksporty; pełny `.ap19` pozostał na komputerze z TIA.

**Teraz: [wzór HMI w edytorze i jego eksport](tia-v19/HMI_WZOR.md)**. Comfort API udostępnia import/eksport, ale nie tworzenie ekranów i tagów. Nie należy ponawiać budowy pustego panelu. Docelowe kontrolki, połączenie, alarmy i fizyczne I/O pozostają do wykonania.

- [Mapa migracji](migration-ROLL/MAPA_MIGRACJI.md)
- [Wariant modułów I/O S7](migration-ROLL/hardware_review/DOBOR_IO_S7.md)
- [Zasilanie i blokady sprzętowe](migration-ROLL/schematic_review/ZASILANIE_BLOKADY.md)
- [Mapa 208 kanałów i połączeń](migration-ROLL/schematic_review/channel-wire-map-draft.csv)
- [Odczytane DB15 i DB19](migration-ROLL/native_verification/DB15_DB19_NASTAWY.md)
- [Receptury operatora](migration-ROLL/operator_recipes/RECEPTURY_OPERATORA.md)

Aktualny stan: 42 pełne bloki porównane z natywnymi wydrukami, 50 stron schematu przeanalizowanych i potwierdzone typy modułów S5 430-7LA12, 451-7LA12 oraz 454-7LA12. Wariant S7 zachowuje 128 wejść i 80 wyjść oraz sprzętowe tory odcięcia. Wentylator pozostaje na %Q24.4, lampka na %Q16.0. Dane cewek nie będą ponownie zamawiane; podstawą doboru są udokumentowane klasy i limity starego I/O.

Końcowe MLFB modułów S7 i zaciski wymagają sprawdzenia oficjalnych kart oraz konfiguracji TIA V19. Kompilacja kodu PLC nie potwierdza działania na maszynie. [Wynik natywny i zakres potwierdzenia](tia-v19/reports/windows-feedback-2026-10-15-120907-compiled.json).

[Aktualna pełna paczka ZIP](migration-ROLL-weryfikacja-STEP5.zip) i [manifest SHA-256](migration-ROLL-weryfikacja-STEP5.manifest.json) zachowują wersję materiałów z 14 października 2026. [Paczka wcześniejszego etapu](migration-ROLL-etap2.zip) dokumentuje stan historyczny. Bieżące zestawienia znajdują się w głównym katalogu migracji.

Skrypty można uruchamiać standardowym Pythonem 3 z katalogu `migration-ROLL`; kolejność odtwarzania zestawień i ich ograniczenia opisuje jego README. Oryginalne pliki pozostają w podkatalogu `originals`. Licencję oraz źródła pomocniczego czytnika MC5 dokumentuje [NOTICE](migration-ROLL/offline_decoder/NOTICE.md).
