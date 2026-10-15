# ROLL — migracja Siemens S5-115U / OP15 do S7-1513 / TP900

Komplet materiałów zgromadzonych podczas analizy maszyny Karl Roll KS04201. Główny katalog [migration-ROLL](migration-ROLL/README.md) zawiera oryginalne archiwa, wydruki STEP 5 i COMTEXT, instrukcję S5, komplet 50 stron schematu, zestawienia oraz skrypty analizy offline.

**Budowa TIA V19:** [instrukcja i skrypt lokalny](tia-v19/README.md), [źródło PLC ROLL_ALL.scl](tia-v19/ROLL_ALL.scl). Raport użytkownika z 15.10.2026, godz. 11:42 potwierdził kompilację PLC: **0 błędów, 4 ostrzeżenia**, utworzenie CPU i TP900 oraz zapis projektu `.ap19` na komputerze z TIA. W repozytorium są źródła, builder i natywne eksporty; pełny projekt pozostał na komputerze użytkownika. Aktualna paczka poprawia konwersje typów, sprawdzanie retencji i wywołania API HMI; te poprawki wymagają kolejnego uruchomienia w TIA. Fizyczne I/O oraz kontrolki, połączenie i alarmy TP900 pozostają do wykonania.

- [Mapa migracji](migration-ROLL/MAPA_MIGRACJI.md)
- [Wariant modułów I/O S7](migration-ROLL/hardware_review/DOBOR_IO_S7.md)
- [Zasilanie i blokady sprzętowe](migration-ROLL/schematic_review/ZASILANIE_BLOKADY.md)
- [Mapa 208 kanałów i połączeń](migration-ROLL/schematic_review/channel-wire-map-draft.csv)
- [Odczytane DB15 i DB19](migration-ROLL/native_verification/DB15_DB19_NASTAWY.md)
- [Receptury operatora](migration-ROLL/operator_recipes/RECEPTURY_OPERATORA.md)

Aktualny stan: 42 pełne bloki porównane z natywnymi wydrukami, 50 stron schematu przeanalizowanych i potwierdzone typy modułów S5 430-7LA12, 451-7LA12 oraz 454-7LA12. Wariant S7 zachowuje 128 wejść i 80 wyjść oraz sprzętowe tory odcięcia. Wentylator pozostaje na %Q24.4, lampka na %Q16.0. Dane cewek nie będą ponownie zamawiane; podstawą doboru są udokumentowane klasy i limity starego I/O.

Końcowe MLFB modułów S7 i zaciski wymagają sprawdzenia oficjalnych kart oraz konfiguracji TIA V19. Kompilacja kodu PLC nie potwierdza działania na maszynie. [Wynik natywny i zakres potwierdzenia](tia-v19/reports/windows-feedback-2026-10-15-compiled.json).

[Aktualna pełna paczka ZIP](migration-ROLL-weryfikacja-STEP5.zip) i [manifest SHA-256](migration-ROLL-weryfikacja-STEP5.manifest.json) zachowują wersję materiałów z 14 października 2026. [Paczka wcześniejszego etapu](migration-ROLL-etap2.zip) dokumentuje stan historyczny. Bieżące zestawienia znajdują się w głównym katalogu migracji.

Skrypty można uruchamiać standardowym Pythonem 3 z katalogu `migration-ROLL`; kolejność odtwarzania zestawień i ich ograniczenia opisuje jego README. Oryginalne pliki pozostają w podkatalogu `originals`. Licencję oraz źródła pomocniczego czytnika MC5 dokumentuje [NOTICE](migration-ROLL/offline_decoder/NOTICE.md).
