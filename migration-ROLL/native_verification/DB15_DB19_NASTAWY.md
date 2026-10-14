# ROLL — nastawy z otrzymanych DB15 i DB19

Otrzymano 12 października 2026 po potwierdzeniu przez użytkownika możliwości odczytu CPU→PC. Oba wydruki wskazują C:ROLLPRST.S5D, mają LEN=137 i komplet 132 słów DW0…DW131. Puste końcowe `132:` jest znacznikiem końca wydruku, nie dodatkowym słowem.

**DB15.DW0…127 odpowiada fabrycznemu DB12. DB19 ma dwie zmienione nastawy: Z1=20 i Z2=14, zamiast 5/5.** Są to presety BCD: KH0020 oznacza 20, KH0014 oznacza 14. Nie stosowano zwykłej interpretacji binarnej.

| Odbiorca | Źródło | KH z wydruku | Wartość | Domyślna |
|---|---|---|---:|---:|
| T 116 | DB15.DW116 | 1050 | 5 s | 5 s |
| T 117 | DB15.DW117 | 1050 | 5 s | 5 s |
| T 24 | DB15.DW24 | 1010 | 1 s | 1 s |
| T 25 | DB15.DW25 | 1020 | 2 s | 2 s |
| T 17 | DB15.DW17 | 3360 | 3600 s | 3600 s |
| T 31 | DB15.DW31 | 3120 | 1200 s | 1200 s |
| T 32 | DB15.DW32 | 3120 | 1200 s | 1200 s |
| T 33 | DB15.DW33 | 2900 | 900 s | 900 s |
| T 58 | DB15.DW58 | 3180 | 1800 s | 1800 s |
| T 59 | DB15.DW59 | 3180 | 1800 s | 1800 s |
| T 63 | DB15.DW63 | 2010 | 10 s | 10 s |
| T 62 | DB15.DW62 | 2600 | 600 s | 600 s |
| T 85 | DB15.DW85 | 2120 | 120 s | 120 s |
| T 61 | DB15.DW61 | 2600 | 600 s | 600 s |
| T 55 | DB15.DW55 | 1010 | 1 s | 1 s |
| T 60 | DB15.DW60 | 2060 | 60 s | 60 s |
| T 56 | DB15.DW56 | 2060 | 60 s | 60 s |
| T 65 | DB15.DW65 | 2015 | 15 s | 15 s |
| T 67 | DB15.DW67 | 1050 | 5 s | 5 s |
| T 75 | DB15.DW75 | 2600 | 600 s | 600 s |
| T 77 | DB15.DW77 | 2300 | 300 s | 300 s |
| T 102 | DB15.DW102 | 2300 | 300 s | 300 s |
| T 103 | DB15.DW103 | 2300 | 300 s | 300 s |
| T 107 | DB15.DW107 | 2015 | 15 s | 15 s |
| T 54 | DB15.DW54 | 2120 | 120 s | 120 s |
| T 53 | DB15.DW53 | 2120 | 120 s | 120 s |
| Z 1 | DB19.DW1 | 0020 | 20 | 5 |
| Z 2 | DB19.DW2 | 0014 | 14 | 5 |

26 nastaw czasu ma potwierdzony odbiorca KT w programie, a dwa słowa DB19 są presetami liczników. W szczególności obrót interwałowy korzysta z T116/T117 po 5 s, a krótki ruch w kąpieli z T24=1 s i T25=2 s. Programy 1/2 mają BADHUB=aus, więc wybrana funkcja krótkiego skoku pozostaje wyłączona.

DW128…131 są odrębnymi polami edytora/sterowania. DB15 ma wybór DW128=DW129=17 oraz bufor DW130=3360, czyli kod KT jednej godziny. DB19 ma wybór 1 oraz bufor 0020 odpowiadający presetowi 20. DW131 wynosi zero w obu blokach. Te sześć różnic względem pierwszego utworzenia DB nie jest sześcioma dodatkowymi nastawami procesu.

Zachowano oddzielnie cały snapshot oraz wzorzec fabryczny. Czas pobrania z CPU i tryb maszyny nie zostały podane; plików źródłowych nie zmieniano. Porównanie nie wykonuje połączenia z CPU ani testu programu S7.

Pliki: [wartości i jednostki](runtime-parameter-values.csv), [264 słowa](runtime-db-words.csv), [osiem różnic](runtime-db-differences.csv), [źródła i SHA-256](runtime-db-snapshots.json), [typowane parametry dla przygotowania S7](S7-runtime-parameters.json). Ten JSON jest referencją danych; nie jest skompilowanym projektem ani automatycznym importem TIA.
