# ROLL — odczyt aktualnych nastaw DB15 i DB19

**DB15 i DB19 już otrzymano:** [nastawy i źródła](DB15_DB19_NASTAWY.md). Poniższa instrukcja pozostaje do ewentualnego nowego odczytu po zmianie nastaw; nie trzeba powtarzać dostarczonych plików.

Brak DB15/DB19 w oryginalnym pliku S5D jest zgodny z programem: FB105 tworzy je w RAM starej CPU. Aktualne wartości trzeba odczytać z tej CPU. Użytkownik potwierdził 12 października 2026, że może wykonać taki odczyt.

1. Przygotuj osobny katalog/kopię projektu STEP 5 do danych odczytanych z maszyny.
2. Połącz STEP 5 ze starą CPU i wybierz źródło bloków **PLC/AG**, czyli sterownik. Odczytaj **DB15 oraz DB19 w kierunku CPU→PC** do przygotowanej kopii. Nazwy pól zależą od języka STEP 5.
3. Z odczytanej kopii wykonaj wydruki bloków, tak jak wcześniejsze INI. Potrzebne są numery słów **DW0…DW131** i wartości **KH, szesnastkowe**; nagłówek powinien identyfikować DB15 lub DB19. Zachowaj również odczytany plik programu S5D.
4. Zanotuj datę odczytu oraz tryb maszyny. Odczytane wartości pozwolą porównać wszystkie nastawy; DW128/129/130 opisują aktualny stan edytora i nie są kolejnymi nastawami procesu.

Możesz przesłać dwa listingi INI/PDF lub archiwum osobnej kopii z odczytanymi blokami. Oryginalne materiały pozostają odrębnym źródłem.

Jeśli w CPU nie znajdziesz tych DB, zapisz tę informację wraz ze statusem połączenia i CPU — nie uruchamiaj inicjalizacji ani kasowania w celu ich utworzenia. Dostępność starej CPU nie jest jeszcze dowodem, że odczytane wartości zostały przekazane.

[Rekonstrukcja fabryczna](runtime-db-factory-reconstruction.csv) i [powiązania parametrów](runtime-parameter-use-map.csv) są przygotowane do porównania. Domyślne wartości nie są przyjęte jako bieżące nastawy operatora. [Pełne ustalenia](WERYFIKACJA_PARTIA6.md).
