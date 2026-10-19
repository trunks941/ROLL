# ROLL — budowa projektu TIA Portal V19

Raport użytkownika z **15.10.2026, godz. 12:09** potwierdził kompilację bieżącego źródła PLC: **0 błędów, 1 ostrzeżenie** dotyczące nieskonfigurowanych modułów I/O. Retencja wszystkich sześciu DB jest potwierdzona natywnym eksportem. Utworzono CPU i TP900, a projekt `.ap19` zapisano na komputerze użytkownika. Chmura nie uruchamia TIA; w paczce są źródła i narzędzia, bez pełnego projektu `.ap19`.

**Aktualny krok: [pierwszy import wygenerowanych ekranów do kopii istniejącego projektu](HMI_IMPORT.md).** Paczka ma 5 ekranów, 53 tagi i 137 obiektów. Uruchom **`IMPORTUJ_HMI.cmd`** z zapisanym projektem ROLL otwartym w TIA i przekaż `ROLL_HMI_IMPORT_…_raport.zip`. Skrypt archiwizuje źródło, odtwarza oddzielną kopię i dopiero w niej importuje HMI. Podgląd układu jest w `PODGLAD_HMI.html`.

[Raport z 19.10, godz. 07:08](reports/hmi-import-feedback-2026-10-19-070814.json) potwierdził poprawne utworzenie archiwum, odtworzenie kopii oraz przyjęcie tabeli tagów i pięciu pustych ekranów przez V19. Obecna poprawka usuwa niespójność promienia wszystkich 15 lampek, na której zatrzymał się import pierwszego pełnego ekranu. Przed następną próbą otwórz pierwotny projekt z `WZOR_ROLL`, spoza katalogów `ROLL_HMI_IMPORT_…\project-copy`. Poprawkę pełnych ekranów trzeba jeszcze potwierdzić w TIA.

Wzór jest już wystarczający: ostatni eksport potwierdza pole I/O powiązane z `WzorLiczba`. Alarm view jest widoczny w GUI, ale pomijany przez XML; nie wymagamy kolejnego identycznego eksportu. Zachowujemy go przez archiwizację pełnego projektu i pozostawienie `WZOR_ROLL` bez importu zastępującego jego zawartość. Edycja i wszystkie polecenia operatorskie nowych ekranów są w pierwszej wersji wyłączone. **Natywna kompilacja nowego HMI, heartbeat i pełna obsługa poleceń pozostają do potwierdzenia/dokończenia.**

## Budowa nowego projektu — do odtworzenia od początku

1. Pobierz [paczkę TIA_ROLL_V19.zip](../TIA_ROLL_V19.zip) lub repozytorium i rozpakuj do zwykłego katalogu na komputerze z **STEP 7 Professional V19 i WinCC Advanced V19**. Zachowaj cały katalog `tia-v19` wraz z podkatalogami. Sama paczka wystarcza do budowy w TIA; ponowna generacja źródeł Python wymaga pełnego repozytorium z materiałami migracji.
2. Sprawdź, czy istnieje plik `C:\Program Files\Siemens\Automation\Portal V19\PublicAPI\V19\Siemens.Engineering.dll`. Jeżeli go nie ma, doinstaluj komponent **TIA Portal Openness V19** z instalatora Siemens. Openness pozwala skryptowi utworzyć urządzenia i zaimportować kod w TIA.
3. Konto Windows uruchamiające skrypt musi należeć do lokalnej grupy **Siemens TIA Openness** — to pełna nazwa grupy potwierdzona komunikatem Siemens. Jeżeli trzeba je dopisać: Zarządzanie komputerem → Użytkownicy i grupy lokalne → Grupy → Siemens TIA Openness → Dodaj. Wymaga to administratora Windows; po zmianie **wyloguj się z Windows i zaloguj ponownie**. Samo zamknięcie TIA lub PowerShell nie odświeży grup w bieżącej sesji. Skrypt sam nie zmienia grup ani uprawnień.
4. Uruchom [UTWORZ_PROJEKT.cmd](UTWORZ_PROJEKT.cmd). Gdy TIA wyświetli pytanie o dostęp aplikacji Openness, zezwól na dostęp temu lokalnemu skryptowi. Nie trzeba podłączać sterownika ani panelu.
5. Wyniki trafią do `Dokumenty\ROLL_TIA_V19`. Skrypt poda ścieżkę projektu i paczki `ROLL_…_raport.zip`. **Przekaż tę paczkę do dalszej pracy nad projektem.** Zawiera wynik kompilacji, eksport bloków i opis rzeczywistego API WinCC V19, bez wysyłania ich gdziekolwiek przez skrypt.

Jeżeli Windows blokuje pobrany plik PS1, sprawdź jego zawartość i odblokuj **ten plik** we Właściwościach → Odblokuj. CMD ustawia `RemoteSigned` wyłącznie dla uruchomionego procesu PowerShell; nie zmienia polityki systemowej. Przy polityce narzuconej przez administratora użyj zatwierdzonego sposobu uruchamiania skryptów.

Skrypt uruchamia 64-bitowy PowerShell, tworzy osobny projekt z unikalną nazwą, importuje [ROLL_ALL.scl](ROLL_ALL.scl), generuje bloki, uruchamia kompilator STEP 7 i zapisuje raport. Nie otwiera istniejącego projektu ani nie wykonuje wgrywania do urządzeń. Nawet przy błędzie zapisuje dostępny raport i utworzoną część projektu.

Ostatni raport potwierdza usunięcie błędów nazw i trzech ostrzeżeń konwersji `SHL`. Wynik dotyczy dokładnie aktualnego źródła SHA-256 `020d153c27c8a7c0adb7b5ada7887c2d8d3021e04975e660ca2107c1abb4e4c1`. [Wynik, retencja i sumy eksportów](reports/windows-feedback-2026-10-15-120907-compiled.json). Generator przypisuje potwierdzenie natywne tylko do identycznej sumy źródła; zmiana kodu powoduje ponowny status wymaganej kompilacji.

Builder zapisuje teraz wynik generowania i SHA-256 faktycznie importowanego źródła. Jeżeli generowanie SCL zgłosi błąd, zachowuje go, pomija kompilację niepełnego programu oraz próbuje zebrać dostępne eksporty PLC i dane TP900. Błąd generowania nadal oznacza nieudaną budowę i kod zakończenia 1; powstanie obiektów HMI nie zmienia tego wyniku.

## Co jest przygotowane

- Wszystkie **22 PB**, z zachowaniem kolejności instrukcji i kolejnych zapisów do tego samego wyjścia. Wygenerowane źródła zachowują również wartość VKE pomiędzy kolejnymi cewkami i nakładanie się znaczników M/MB/MW.
- Kolejność części procesowej OB1 oraz odpowiedniki FB69, FB90 i FB111. Funkcje komunikacyjne OP15 otrzymały osobny interfejs PLC/HMI zamiast sterownika szeregowego FB51.
- Odczytane online nastawy DB15/DB19, w tym presety Z1=20 i Z2=14, oraz dwa jednakowe programy operatora z potwierdzonymi czasami. Pierwsze załadowanie nowego S7 zaczyna od tych danych; bieżące znaczniki i wartości liczników pracującego S5 nie są kopią jego stanu wykonania.
- Profil czterech stacji, bez automatycznego podawania/odbierania. Wejścia opcjonalne E119–E125 mają stan zero i nie otrzymują modułów fizycznych. Wyjścia A112–A113 pozostają wewnętrznym obrazem starszych gałęzi.
- Adresy fizyczne `%I0.0…%I15.7` i `%Q16.0…%Q25.7`. Wentylator zachowuje `%Q24.4`, lampka `%Q16.0`. Warunki wyjść pompy stacji 2 i istniejących obwodów pozostają w PB; sprzętowe blokady wynikają ze schematu.
- Interfejs 47 zmiennych skalarnych i specyfikacja pięciu ekranów po polsku: przegląd, receptury, sterowanie ręczne, alarmy, nastawy. Zachowano **14 aktywnych funkcji ręcznych COMTEXT** i tryby bębna 0–4.

W źródłach `Simulation=TRUE`, `PhysicalIoConfigured=FALSE`, `PhysicalOutputsEnabled=FALSE`. To projekt do kompilacji i weryfikacji. Moduły oraz ich adresy i grupy zasilania trzeba jeszcze skonfigurować i sprawdzić przed uruchomieniem sprzętu.

## Co pozostaje do dokończenia po lokalnej budowie

Skrypt tworzy dokładną CPU **6ES7513-1AM03-0AB0** oraz **TP900 Comfort 6AV2124-0JC01-0AX0** z wersji dostępnych w lokalnym katalogu. Raport potwierdził CPU w wersji projektowej **V3.1** i panel o identyfikatorze `OrderNumber:6AV2 124-0JC01-0AX0/17.0.0.0`. Udane utworzenie urządzenia ustala wersję projektu; **nie ustala firmware dopiero zamówionej CPU**.

Raport 12:09 wykazał, że `GetCreationInfos` zwraca puste listy dla ekranów, tagów, tabel i połączeń Comfort. Samo istnienie ogólnego interfejsu `Create` nie daje obsługi tworzenia tych obiektów. Poprzednie założenie o tej możliwości oraz test z atrapą API nie potwierdziły zachowania WinCC. Builder nie ponawia już tych prób. Kompilator HMI zgłosił jeden błąd: brak ekranu startowego.

Wzór z edytora został dostarczony. `tools/generate_native_hmi.py` klonuje jego prawdziwe obiekty, tworzy tagi i pięć ekranów oraz osobne puste ekrany do pierwszego etapu importu. Wszystkie odwołania między ekranami są rozwiązywane po utworzeniu ich nazw; źródłowy `WZOR_ROLL` i jego niewyeksportowany alarm view pozostają w kopii pełnego projektu.

[Instrukcja importu](HMI_IMPORT.md) opisuje działania i ograniczenia. Importer nie zmienia PLC, modułów ani uprawnień i nie wgrywa niczego do urządzeń. Własne ekrany mają numery 101–105 oraz prefiks `ROLL_`; kolizje nazw/numerów zatrzymują pracę przed zamknięciem źródła. Native XML i formaty zdarzeń wymagają sprawdzenia w lokalnym V19; źródła i odniesienia są opisane w `hmi/native/manifest.json`.

`hmi/interface.csv` i `hmi/screens.json` pozostają kontraktem funkcjonalnym. Utworzenie plików XML i poprawne odwołania nie oznaczają jeszcze gotowych poleceń operatorskich, potwierdzonego zapisu danych ani natywnej kompilacji HMI.

Dobór i wstawienie modułów S7, przypisanie zacisków i niezależnych torów zasilania pozostają odrębnym krokiem. Podstawą są [wariant I/O](../migration-ROLL/hardware_review/S7-IO-layout-variant.csv) oraz [grupy zasilania](../migration-ROLL/hardware_review/S7-output-supply-assignment.csv). Skrypt nie zgaduje końcowych MLFB modułów.

## Zmiany zachowania wymagające porównania

- FB105 tworzył i wypełniał DB w wielu cyklach. W S7 są to jawne wartości początkowe DB, bez tej sekwencji tworzenia. FB101 zastąpiono zatwierdzeniem nastawy, z zakresem 0–127 i odrzuceniem nieużywanego `FFFF`; nie jest to jego stary cykliczny edytor.
- Parametry czasu DB15 zachowują oryginalną bazę KT; edycja wymaga wartości w ms dokładnie reprezentowalnej w tej bazie. Liczniki są edytowane jako liczby 0–999. Receptury mają jawnie przyjętą bazę **1 s**. Dla trybu 4 próg FB111 `<=7` oznacza przez to 7 s. Jednostkę sekund potwierdzono, ale rzeczywistej bazy KT receptur OP15 nie odczytano. W obu dostarczonych programach wybrano tryb 1; tryb 4 wymaga osobnego porównania.
- SE/SA i liczniki mają odpowiedniki programowe. Nie są jeszcze porównane czasowo z S5 ani uruchomione w S7. Faza zegarów S5 i próbkowanie w cyklu mogą zmienić czas zadziałania o część bazy czasu i cykl; testy Python nie sprawdzają tej różnicy.
- Takt OB13 250 ms jest odtwarzany z czasu cyklu, z zachowaniem kaskady przełączeń M3.4…M3.7. Przerwanie sprzętowe i jego dokładna faza nie są odtworzone w tej wersji. RS126=1000 dotyczyło konfiguracji modułów S5, nie dodatkowego timera procesu.
- Skrypt ustawia retencję wszystkich M oraz danych przez eksport, zmianę natywnego atrybutu `Remanence` i ponowny import sześciu DB. Następnie kompiluje PLC i dopiero wtedy sprawdza retencję eksportem. W raporcie z 11:42 `retentionConfigured=false` wynika z poprzedniej, błędnej kolejności weryfikacji: wszystkie końcowe eksporty tych DB mają już `Retain`. Źródło SCL samo deklaruje DB jako `NON_RETAIN`; **bez skutecznego kroku Openness lub ustawienia retencji w TIA dane nie będą zachowane po restarcie**. Raport 12:09 potwierdza `retentionConfigured=true` i sześć poprawnych `retentionChecks`. T/Z0…63 mają pozostać zachowane, T/Z64…127 są kasowane przy OB100, zgodnie z **domyślną** konfiguracją RE i zmianą bitu 3 RS120 w FB61. Inne ustawienia bitów 4/5 RS120 online nie są odczytane. Zachowanie przy STOP/RUN, zaniku zasilania i pobraniu programu wymaga testów w CPU.
- Przyciski ruchu są przytrzymywane i kasowane przy braku heartbeat przez 1,5 s. Ruchy ręczne i ich podtrzymania nadal wynikają z PB. Zapis receptur i parametrów wymaga trybu ręcznego i aktywnego połączenia, co jest jawną zmianą obsługi względem starego transferu OP15. Heartbeat musi zostać przypisany globalnemu zdarzeniu panelu, niezależnie od otwartego ekranu. Polecenie zapisu wolno wysłać dopiero po potwierdzonym zapisie całego zestawu edytowanych wartości do PLC; natywna obsługa tych zapisów WinCC pozostaje do wykonania.
- Diagnostyka baterii S5 OB34/M16.5 wymaga dobrania diagnostyki S7; nie zastąpiono jej fikcyjnym sygnałem. Alarmy WinCC muszą zachować kolejność bajtów i polaryzację potwierdzeń FB91 oraz reguły kasowania PB2; pozostają do konfiguracji.

## Co sprawdzono w chmurze

**7 kontroli przeszło**, w tym **880 porównań stanów 22 PB**: bezpośrednie wykonanie rejestrów instrukcji MC5 przeciw wykonaniu wygenerowanego podzbioru SCL w Pythonie. Dodatkowo sprawdzono wielokrotne cewki, zapis VKE, migawki porównań, liczby ze znakiem, nakładanie M/MB/MW, receptury i adresy I/O. Obie strony porównania używają wspólnego modelu timerów/liczników; nie stanowi to niezależnego testu ich odpowiedników SCL.

Sprawdzono parser PowerShell, rozpoznanie błędu grupy Openness (pięć przypadków), obsługę wyniku generowania źródła (dwa przypadki z atrapą API), kolejność import/kompilacja/eksport i wykrywanie błędów retencji (cztery scenariusze na natywnych XML z atrapą API), odczyt pustej listy typów tworzenia HMI bez wywołania `Create` oraz eksport metadanych. Dla eksportera sprawdzono zagnieżdżone foldery ekranów i tagów, cztery scenariusze braków wzoru i brak wywołań zmieniających konfigurację projektu. Trzy kontrole na rzeczywistym XML z 16.10 potwierdzają cztery obiekty w warstwach, wykrywanie pola bez tagu w starszym wzorze, poprawnego powiązania w ostatnim wzorze oraz odwołania do ROLL_PLC mimo braku eksportu definicji połączenia. Brak alarm view w XML nie jest blokadą eksportu. Dodatkowo sprawdzono 53 tagi i 137 obiektów nowego HMI, odwołania nawigacji, geometrię, blokady przycisków, warianty publicznego API archiwizacji i kontrolę sum importu. Kontrole w chmurze nie uruchamiają TIA ani WinCC. [Wynik kontroli PB](reports/conversion-tests.json), [kontrole buildera](reports/builder-native-feedback-tests.json), [historyczna regresja nazw](reports/native-identifier-regression.json), [zakres trzech konwersji](reports/shift-count-regression.json) i [sumy źródeł](reports/source-hashes.json) rozdzielają sprawdzenia aktualnej wersji od wyniku natywnego dokładnie wskazanej wersji.

Odtwarzanie źródeł i kontroli w Linux/Python 3:

```sh
cd /workspace/ROLL
python3 tia-v19/tools/generate.py
python3 tia-v19/tools/prepare_hmi.py
python3 tia-v19/tools/test_conversion.py
python3 tia-v19/tools/verify_sources.py
python3 tia-v19/tools/test_native_evidence.py
python3 tia-v19/tools/generate_native_hmi.py
python3 tia-v19/tools/test_native_hmi.py
```

Kontrole PowerShell: `tools/check_powershell.ps1`, `tools/test_builder_diagnostics.ps1`, `tools/test_builder_native_feedback.ps1` , `tools/test_hmi_seed_exporter.ps1` i `tools/test_hmi_importer.ps1`. Kontrola retencji wymaga pełnego repozytorium z natywnymi eksportami w `native-feedback`; paczka budowy ich nie zawiera. Kontrole nie uruchamiają TIA ani nie zmieniają uprawnień Windows.

Ręczny import awaryjny: w nowym projekcie TIA dodaj odpowiednią CPU, w jej „External source files / Zewnętrzne pliki źródłowe” dodaj `ROLL_ALL.scl`, wybierz „Generate blocks from source / Generuj bloki ze źródła”, następnie kompilację całego programu. Zastąpienie domyślnego OB1 wykonuj tylko w tym nowym projekcie. Przekaż pełne komunikaty błędów wraz z numerami linii. Ta ścieżka nie tworzy ekranów HMI ani raportu API potrzebnego do ich automatyzacji.
