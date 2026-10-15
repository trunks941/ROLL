# ROLL — budowa projektu TIA Portal V19

Ten pakiet zawiera źródła PLC i skrypt tworzący **nowy projekt offline na komputerze z TIA V19**. Chmura nie uruchamia TIA. Nie ma jeszcze potwierdzonego kompilacją pliku `.ap19` ani gotowych ekranów operatorskich TP900. Następny krok to uruchomienie budowy lokalnie i przekazanie jej raportu.

## Co uruchomić

1. Pobierz [paczkę TIA_ROLL_V19.zip](../TIA_ROLL_V19.zip) lub repozytorium i rozpakuj do zwykłego katalogu na komputerze z **STEP 7 Professional V19 i WinCC Advanced V19**. Zachowaj cały katalog `tia-v19` wraz z podkatalogami. Sama paczka wystarcza do budowy w TIA; ponowna generacja źródeł Python wymaga pełnego repozytorium z materiałami migracji.
2. Sprawdź, czy istnieje plik `C:\Program Files\Siemens\Automation\Portal V19\PublicAPI\V19\Siemens.Engineering.dll`. Jeżeli go nie ma, doinstaluj komponent **TIA Portal Openness V19** z instalatora Siemens. Openness pozwala skryptowi utworzyć urządzenia i zaimportować kod w TIA.
3. Konto Windows uruchamiające skrypt musi należeć do lokalnej grupy **Siemens TIA Openness** — to pełna nazwa grupy potwierdzona komunikatem Siemens. Jeżeli trzeba je dopisać: Zarządzanie komputerem → Użytkownicy i grupy lokalne → Grupy → Siemens TIA Openness → Dodaj. Wymaga to administratora Windows; po zmianie **wyloguj się z Windows i zaloguj ponownie**. Samo zamknięcie TIA lub PowerShell nie odświeży grup w bieżącej sesji. Skrypt sam nie zmienia grup ani uprawnień.
4. Uruchom [UTWORZ_PROJEKT.cmd](UTWORZ_PROJEKT.cmd). Gdy TIA wyświetli pytanie o dostęp aplikacji Openness, zezwól na dostęp temu lokalnemu skryptowi. Nie trzeba podłączać sterownika ani panelu.
5. Wyniki trafią do `Dokumenty\ROLL_TIA_V19`. Skrypt poda ścieżkę projektu i paczki `ROLL_…_raport.zip`. **Przekaż tę paczkę do dalszej pracy nad projektem.** Zawiera wynik kompilacji, eksport bloków i opis rzeczywistego API WinCC V19, bez wysyłania ich gdziekolwiek przez skrypt.

Jeżeli Windows blokuje pobrany plik PS1, sprawdź jego zawartość i odblokuj **ten plik** we Właściwościach → Odblokuj. CMD ustawia `RemoteSigned` wyłącznie dla uruchomionego procesu PowerShell; nie zmienia polityki systemowej. Przy polityce narzuconej przez administratora użyj zatwierdzonego sposobu uruchamiania skryptów.

Skrypt uruchamia 64-bitowy PowerShell, tworzy osobny projekt z unikalną nazwą, importuje [ROLL_ALL.scl](ROLL_ALL.scl), generuje bloki, uruchamia kompilator STEP 7 i zapisuje raport. Nie otwiera istniejącego projektu ani nie wykonuje wgrywania do urządzeń. Nawet przy błędzie zapisuje dostępny raport i utworzoną część projektu.

Raport z 15 października 2026 zatrzymał się podczas uruchamiania Openness: konto procesu nie należało do `Siemens TIA Openness`. Projekt i kompilacja nie zostały rozpoczęte; nie jest to komunikat błędu kodu PLC. Administrator powinien dodać **konto, które ma uruchamiać skrypt**; samo uruchomienie skryptu jako inny administrator nie zastępuje tej konfiguracji. Po ponownym zalogowaniu można uruchomić także poprzednią wersję paczki. Zaktualizowana wersja dodatkowo zapisuje w raporcie kod diagnozy i instrukcję dalszego działania.

## Co jest przygotowane

- Wszystkie **22 PB**, z zachowaniem kolejności instrukcji i kolejnych zapisów do tego samego wyjścia. Wygenerowane źródła zachowują również wartość VKE pomiędzy kolejnymi cewkami i nakładanie się znaczników M/MB/MW.
- Kolejność części procesowej OB1 oraz odpowiedniki FB69, FB90 i FB111. Funkcje komunikacyjne OP15 otrzymały osobny interfejs PLC/HMI zamiast sterownika szeregowego FB51.
- Odczytane online nastawy DB15/DB19, w tym presety Z1=20 i Z2=14, oraz dwa jednakowe programy operatora z potwierdzonymi czasami. Pierwsze załadowanie nowego S7 zaczyna od tych danych; bieżące znaczniki i wartości liczników pracującego S5 nie są kopią jego stanu wykonania.
- Profil czterech stacji, bez automatycznego podawania/odbierania. Wejścia opcjonalne E119–E125 mają stan zero i nie otrzymują modułów fizycznych. Wyjścia A112–A113 pozostają wewnętrznym obrazem starszych gałęzi.
- Adresy fizyczne `%I0.0…%I15.7` i `%Q16.0…%Q25.7`. Wentylator zachowuje `%Q24.4`, lampka `%Q16.0`. Warunki wyjść pompy stacji 2 i istniejących obwodów pozostają w PB; sprzętowe blokady wynikają ze schematu.
- Interfejs 47 zmiennych skalarnych i specyfikacja pięciu ekranów po polsku: przegląd, receptury, sterowanie ręczne, alarmy, nastawy. Zachowano **14 aktywnych funkcji ręcznych COMTEXT** i tryby bębna 0–4.

W źródłach `Simulation=TRUE`, `PhysicalIoConfigured=FALSE`, `PhysicalOutputsEnabled=FALSE`. To projekt do kompilacji i weryfikacji. Moduły oraz ich adresy i grupy zasilania trzeba jeszcze skonfigurować i sprawdzić przed uruchomieniem sprzętu.

## Co pozostaje do dokończenia po lokalnej budowie

Skrypt próbuje utworzyć dokładną CPU **6ES7513-1AM03-0AB0** oraz **TP900 Comfort 6AV2124-0JC01-0AX0** z wersji dostępnych w lokalnym katalogu. Podane identyfikatory są kandydatami, nie wynikiem sprawdzenia katalogu Siemens. Udane utworzenie urządzenia ustala wersję projektu; **nie ustala firmware dopiero zamówionej CPU**.

Skrypt tworzy dostępne natywne obiekty pustych ekranów i eksportuje ich rzeczywistą strukturę. **Przyciski, pola, zmienne, połączenie PLC, alarmy i zdarzenie heartbeat nie są jeszcze skonfigurowane w WinCC.** Bez tych elementów panel nie obsługuje maszyny. Eksport z lokalnego V19 pozwoli przygotować właściwy import ekranów i powiązań. `hmi/interface.csv` i `hmi/screens.json` są specyfikacją, nie formatem gotowym do importu WinCC.

Dobór i wstawienie modułów S7, przypisanie zacisków i niezależnych torów zasilania pozostają odrębnym krokiem. Podstawą są [wariant I/O](../migration-ROLL/hardware_review/S7-IO-layout-variant.csv) oraz [grupy zasilania](../migration-ROLL/hardware_review/S7-output-supply-assignment.csv). Skrypt nie zgaduje końcowych MLFB modułów.

## Zmiany zachowania wymagające porównania

- FB105 tworzył i wypełniał DB w wielu cyklach. W S7 są to jawne wartości początkowe DB, bez tej sekwencji tworzenia. FB101 zastąpiono zatwierdzeniem nastawy, z zakresem 0–127 i odrzuceniem nieużywanego `FFFF`; nie jest to jego stary cykliczny edytor.
- Parametry czasu DB15 zachowują oryginalną bazę KT; edycja wymaga wartości w ms dokładnie reprezentowalnej w tej bazie. Liczniki są edytowane jako liczby 0–999. Receptury mają jawnie przyjętą bazę **1 s**. Dla trybu 4 próg FB111 `<=7` oznacza przez to 7 s. Jednostkę sekund potwierdzono, ale rzeczywistej bazy KT receptur OP15 nie odczytano. W obu dostarczonych programach wybrano tryb 1; tryb 4 wymaga osobnego porównania.
- SE/SA i liczniki mają odpowiedniki programowe. Nie są jeszcze porównane czasowo z S5 ani uruchomione w S7. Faza zegarów S5 i próbkowanie w cyklu mogą zmienić czas zadziałania o część bazy czasu i cykl; testy Python nie sprawdzają tej różnicy.
- Takt OB13 250 ms jest odtwarzany z czasu cyklu, z zachowaniem kaskady przełączeń M3.4…M3.7. Przerwanie sprzętowe i jego dokładna faza nie są odtworzone w tej wersji. RS126=1000 dotyczyło konfiguracji modułów S5, nie dodatkowego timera procesu.
- Skrypt próbuje ustawić retencję wszystkich M oraz danych przez eksport, zmianę natywnego atrybutu `Remanence` i ponowny import DB, a następnie sprawdza ją ponownym eksportem. Źródło SCL samo deklaruje DB jako `NON_RETAIN`; **bez skutecznego kroku Openness lub ustawienia retencji w TIA dane nie będą zachowane po restarcie**. Sprawdź `retentionConfigured` i `retentionChecks` w raporcie. T/Z0…63 mają pozostać zachowane, T/Z64…127 są kasowane przy OB100, zgodnie z **domyślną** konfiguracją RE i zmianą bitu 3 RS120 w FB61. Inne ustawienia bitów 4/5 RS120 online nie są odczytane. Natywne właściwości DB oraz zachowanie przy STOP/RUN, zaniku zasilania i pobraniu programu wymagają weryfikacji w TIA i CPU.
- Przyciski ruchu są przytrzymywane i kasowane przy braku heartbeat przez 1,5 s. Ruchy ręczne i ich podtrzymania nadal wynikają z PB. Zapis receptur i parametrów wymaga trybu ręcznego i aktywnego połączenia, co jest jawną zmianą obsługi względem starego transferu OP15. Heartbeat musi zostać przypisany globalnemu zdarzeniu panelu, niezależnie od otwartego ekranu. Polecenie zapisu wolno wysłać dopiero po potwierdzonym zapisie całego zestawu edytowanych wartości do PLC; natywna obsługa tych zapisów WinCC pozostaje do wykonania.
- Diagnostyka baterii S5 OB34/M16.5 wymaga dobrania diagnostyki S7; nie zastąpiono jej fikcyjnym sygnałem. Alarmy WinCC muszą zachować kolejność bajtów i polaryzację potwierdzeń FB91 oraz reguły kasowania PB2; pozostają do konfiguracji.

## Co sprawdzono w chmurze

**7 kontroli przeszło**, w tym **880 porównań stanów 22 PB**: bezpośrednie wykonanie rejestrów instrukcji MC5 przeciw wykonaniu wygenerowanego podzbioru SCL w Pythonie. Dodatkowo sprawdzono wielokrotne cewki, zapis VKE, migawki porównań, liczby ze znakiem, nakładanie M/MB/MW, receptury i adresy I/O. Obie strony porównania używają wspólnego modelu timerów/liczników; nie stanowi to niezależnego testu ich odpowiedników SCL.

Sprawdzono parser PowerShell oraz reakcję skryptu na brak API TIA: jawny błąd i raport. Po otrzymaniu raportu Windows z 15 października sprawdzono również rozpoznanie rzeczywistego błędu grupy Openness oraz pięć przypadków rozróżniających ten błąd od innych awarii. Kontrole w chmurze nie uruchamiają natywnego TIA ani WinCC; próba użytkownika na Windows zakończyła się przed utworzeniem projektu. [Pokrycie i ograniczenia](reports/coverage.json), [wynik kontroli](reports/conversion-tests.json) i [sumy źródeł](reports/source-hashes.json) są zapisane przy kodzie.

Odtwarzanie źródeł i kontroli w Linux/Python 3:

```sh
cd /workspace/ROLL
python3 tia-v19/tools/generate.py
python3 tia-v19/tools/prepare_hmi.py
python3 tia-v19/tools/test_conversion.py
python3 tia-v19/tools/verify_sources.py
```

Kontrole PowerShell: `tools/check_powershell.ps1` sprawdza składnię buildera, a `tools/test_builder_diagnostics.ps1` rozpoznawanie komunikatów o uprawnieniach. Nie uruchamiają TIA i nie zmieniają członkostwa w grupach Windows.

Ręczny import awaryjny: w nowym projekcie TIA dodaj odpowiednią CPU, w jej „External source files / Zewnętrzne pliki źródłowe” dodaj `ROLL_ALL.scl`, wybierz „Generate blocks from source / Generuj bloki ze źródła”, następnie kompilację całego programu. Zastąpienie domyślnego OB1 wykonuj tylko w tym nowym projekcie. Przekaż pełne komunikaty błędów wraz z numerami linii. Ta ścieżka nie tworzy ekranów HMI ani raportu API potrzebnego do ich automatyzacji.
