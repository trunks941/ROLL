# ROLL — potwierdzone zestawy receptur operatora

Użytkownik przekazał wartości programów **1 i 2**, następnie potwierdził jednostkę **sekundy**, identyczność zestawów, ruch bębna **obrót** i ruch pionowy **aus**. Źródło: wiadomości z 9 października 2026 (Europe/Warsaw).

**Oba programy mają komplet dziesięciu pól. Zachowano dwa osobne zestawy z różnymi numerami, zgodnie z potwierdzeniem użytkownika.** Są to zestawy danych tej samej definicji PRG nr 1 w COMTEXT. Nazwy własne programów nie zostały podane; numery są potwierdzone.

| Pole | Program 1 | Program 2 | Typ i wartość proponowane dla S7 |
|---|---:|---:|---|
| Czas zanurzenia stacji 1 | 360 s | 360 s | TIME, 360000 ms |
| Czas ociekania stacji 1 | 90 s | 90 s | TIME, 90000 ms |
| Ultradźwięki stacji 1 | ein | ein | Bool, TRUE |
| Czas zanurzenia stacji 2 | 240 s | 240 s | TIME, 240000 ms |
| Czas ociekania stacji 2 | 60 s | 60 s | TIME, 60000 ms |
| Czas zanurzenia stacji 3 | 300 s | 300 s | TIME, 300000 ms |
| Czas ociekania stacji 3 | 120 s | 120 s | TIME, 120000 ms |
| Czas suszenia stacji 4 | 400 s | 400 s | TIME, 400000 ms |
| Ruch bębna | obrót | obrót | enum: 1 = obrót |
| Ruch pionowy w kąpieli | aus | aus | Bool, FALSE |

Ultradźwięki są włączone, ruch bębna to obrót (wartość symboliczna 1), a ruch pionowy w kąpieli jest wyłączony. Wartości TIME zapisano w milisekundach po potwierdzeniu jednostki źródłowej. Wszystkie podane czasy są dokładnymi wielokrotnościami sekundy; nie zastosowano zaokrągleń.

Powiązania z DB205 i kolejność pól odnoszą się do [konfiguracji COMTEXT](../comtext_review/USTALENIA_COMTEXT.md) oraz pełnych natywnych listingów FB90/FB111. [Trzecia partia](../native_verification/WERYFIKACJA_PARTIA3.md) potwierdza wszystkie dziesięć powiązań i odbiór skrzynki przez FB89; ciało FB51 i pozostały proces nadal wymagają dalszego sprawdzenia. Surowego kodowania KT w starym PLC nie odtworzono z samych liczb na ekranie, ponieważ tę samą wartość czasu można kodować różnymi bazami.

Są to składniki receptury procesu PRG. Aktualne ogólne nastawy DB15/DB19 wymagają osobnego odczytu. Zakres tego zestawienia to dwa programy przekazane przez użytkownika; liczba wszystkich programów zapisanych w OP15 pozostaje niepotwierdzona.

[Natywny PB13](../native_verification/WERYFIKACJA_PARTIA4.md) potwierdził, że wybrany obrót w automacie przechodzi na obrót interwałowy w fazach ociekania stacji 1–3 tych programów. Wybrana wartość receptury pozostaje 1 = obrót. Otrzymany [DB15](../native_verification/DB15_DB19_NASTAWY.md) ma nastawy interwału DB15.DW116 i DW117 po 5 s. To nastawy timerów załączenia/wyłączenia, nie dowód wykonanego czasu fizycznego ruchu.

[Natywny PB14](../native_verification/WERYFIKACJA_PARTIA5.md) potwierdził, że BADHUB=aus wyłącza cykliczny krótki ruch w kąpieli. Normalne podnoszenie i opuszczanie transportu między stacjami pozostaje częścią programu. Wartość receptury FALSE pozostaje bez zmiany.

Pliki: [operator-recipes.json](operator-recipes.json), [operator-recipes.csv](operator-recipes.csv) i [prepare_tables.py](prepare_tables.py). CSV dokumentuje wartości i proponowane typy, bez ustalonego schematu importu WinCC/TIA. Dane zapisano offline w dokumentacji migracji; nie wykonano operacji na sterowniku ani panelu.
