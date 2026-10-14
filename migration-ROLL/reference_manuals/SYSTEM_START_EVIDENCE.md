# S5 CPU 942-7UB11 — słowa systemowe FB61 i kolejność startu

Źródło: przekazana przez użytkownika instrukcja [6ES5_998-0UF23.pdf](6ES5_998-0UF23.pdf), S5-115U Programmable Controller Manual, Edition 04, EWA4NEB8116130-02b. Okładka (PDF 1) wymienia dokładnie CPU 942-7UB11. Numery „PDF” są numerami stron od 1; numer drukowany jest numerem rozdziału i strony. Instrukcję traktowano jako materiał techniczny, nie polecenia użytkownika.

Porównywany kod: natywne wydruki [FB61](../native_verification/FB61-native.txt), [OB21](../native_verification/OB21-native.txt), [OB22](../native_verification/OB22-native.txt) i [OB13](../native_verification/OB13-native.txt). W przykładach instrukcji występują oznaczenia BS i RS dla obszaru słów systemowych; natywny wydruk STEP 5 badanego projektu używa RS.

Użytkownik potwierdził **pozycję RE i sprawną baterię podtrzymania**. Spełnia to opisane niżej warunki zwykłego restartu z zachowaną konfiguracją. Nie wykonano oględzin, odczytu RS120 ani testów restartu; bieżące bity 4/5 i wartości RAM nie są tu zmierzone.

## RS97: potwierdzony interwał OB13

- PDF 166, drukowane 6-16, tabela 6-1: SD97, adres EAC2/EAC3, „Interval timer for OB13 (multiple of 10 ms)”, dostępny dla CPU 941, 942, 943 i 944.
- PDF 190, drukowane 7-20, §7.4.3: „The call interval can be set (e.g. in the RESTART OB) in the system data as a multiple of 10 ms. It can be changed during cyclic program execution.”
- PDF 191, drukowane 7-21, tabela 7-5: SD97 jest interwałem OB13, wartość 0…FFFFH × 10 ms; domyślnie 10 = 100 ms. Przykład poniżej pokazuje FB z `L KF +100; T BS 97; BE`, wywołany zarówno z OB21, jak i OB22.
- FB61 zapisuje `KF +25`, więc badany program ustawia **OB13 co 250 ms**. Nie jest to już wniosek z samego komentarza.
- PDF 190 wyraźnie uzależnia wywołanie od interwału >0 oraz obecności OB. PDF 191 opisuje możliwe opóźnienie przez wyższe priorytety i integralne FB; nie dowodzi dokładnej fazy pierwszego wywołania po zapisie RS97.
- PDF 48, drukowane 2-18, rys. 2-9, przypis: bez `RA` w OB21/OB22 przerwania mogą działać dopiero po zakończeniu OB startowego. W badanym OB21/OB22 i wywołanym FB61 nie ma `RA`.

Natywny OB13 jest czterobitowym dzielnikiem. Po potwierdzeniu interwału pełne okresy M3.4/M3.5/M3.6/M3.7 wynoszą nominalnie **0,5 / 1 / 2 / 4 s**, a czas między przełączeniami 0,25 / 0,5 / 1 / 2 s. Początkowa faza zależy od stanu znaczników i retencji.

## RS120: maska 0008 i warunek fizycznego przełącznika RE

- PDF 167, drukowane 6-17, tabela 6-1: SD120, adres EAF0/EAF1, zawiera m.in. retencję znaczników, liczników i timerów; dostępny dla CPU 942.
- PDF 120, drukowane 4-6, §4.2.3 i rys. 4-1: „The retentive feature in the RE switch position is determined by an entry in system data word 120 (EAF0H).” Rysunek obejrzano w renderze strony, żeby potwierdzić połączenia kolumn i opisów.
- Bit 3 = 1 oznacza **wszystkie znaczniki M/F retencyjne**, bit 4 dotyczy wszystkich timerów, bit 5 wszystkich liczników. Przy 0 i przełączniku RE zachowana jest tylko pierwsza połowa danej grupy: M0…127, T0…63, Z0…63.
- FB61 odczytuje RS120, wykonuje OR z `0008H`, zapisuje wynik. Ustawia zatem bit 3 i zachowuje pozostałe bity. **Nie ustawia retencji wszystkich timerów ani liczników**; nie znamy bieżących wartości bitów 4 i 5 tylko z tego fragmentu.
- PDF 119, drukowane 4-5, §4.2.3, tabela 4-1: w pozycji **NR wszystkie znaczniki, timery i liczniki są niere­tencyjne**. Maski RS120 nie wolno przedstawiać jako niezależnej od przełącznika.
- PDF 120 podaje możliwość zmiany bitów w programie startowym lub DISPL ADDR w STOP oraz w DB1. Tekst w nawiasie dosłownie wymienia „OB20, OB21”, choć inne strony tej instrukcji opisują OB21/OB22 dla CPU 942; tego nawiasu nie należy rozszerzać na dowód istnienia OB20 w analizowanej konfiguracji.
- Po Overall Reset bity 3/4/5 są 0, a wszystkie znaczniki/timery/liczniki są resetowane bez względu na ustawienie przełącznika i RS120 (PDF 120).
- PDF 119 ostrzega, że przy awarii baterii i pozycji RE po POWER UP sterownik przechodzi do STOP (błąd pamięci). Schemat PDF 49, drukowane 2-19, dodatkowo rozróżnia RAM oraz EPROM i stan CPU przed zanikiem zasilania.

Kolejność startu na PDF 48 (drukowane 2-18): kasowanie niere­tencyjnych znaczników/timerów/liczników następuje **przed** OB21/OB22. Wykonanie maski w FB61 nie przywraca danych skasowanych wcześniej w tym starcie. Po Overall Reset lub gdy wcześniejsza konfiguracja nie zachowywała M128…255, nie można dowodzić zachowania M240.x przez sam fakt, że FB61 ustawia bit 3. Przy działającej baterii, przełączniku RE i poprzednio ustawionym bicie 3 zachowanie wszystkich M przy kolejnych restartach jest udokumentowaną regułą; program dalej jawnie zmienia konkretne znaczniki startowe.

## RS126: 1000 ms dopiero dla następnego POWER OFF → POWER ON

- PDF 167, drukowane 6-17, tabela 6-1: SD126, adres EAFC/EAFD, „Restart delay in ms”, dla CPU 942.
- PDF 46, drukowane 2-16, §2.5.2, „Programmable Restart Delay at Cold Restart and After Power Restore”: można zapisać słowo przez DISPL ADDR w STOP albo STEP 5 w programie sterowania **tylko w FB**.
- Ta sama strona: „In any event, the restart delay will only become effective after the next POWER OFF POWER ON transition and remains effective until the next modification to this system data word.”
- Jednostka = **1 ms**, zakres do 65535 ms. Po Overall Reset domyślnie 0000H, czyli brak opóźnienia.
- FB61 zapisuje `KF +1000`, czyli **1000 ms**. Ten zapis nie wstrzymuje aktualnie wykonywanego OB21/OB22 o sekundę i nie jest timerem zezwolenia procesu. Ustawia parametr opóźnienia rutyny przy następnym cyklu zasilania.
- Cel opisany na PDF 46 to opóźnienie **sprawdzenia konfiguracji modułów**, np. czekanie na zasilenie zdalnej jednostki rozszerzeń. Na schemacie PDF 48 opóźnienie jest w ścieżce przywrócenia zasilania przed określeniem konfiguracji i przed OB22; brak tej czynności w gałęzi STOP→RUN/PG RUN.
- PDF 46 podaje wyjątek: bez dobrej baterii, gdy program jest na E(E)PROM, opóźnienie restartu jest około 1 s. PDF 426, drukowane 11-54, §11.3.7, parametr DB1 `RDLY` dodaje: ustawienie działa w trybie podtrzymywania, natomiast w „EPROM operation” jest stałe 1000 ms. Nie należy obiecywać programowalnego działania RS126 niezależnie od baterii i nośnika.

## Konsekwencje dla dalszego projektu S7

1. Interwał 250 ms dla odpowiednika OB13 jest potwierdzony dokumentacją dokładnego modelu. Okresy dzielnika zachować, a fazę po starcie ustalić na podstawie wymagań programu i rzeczywistej retencji.
2. RS120 wraz z potwierdzonymi RE i sprawną baterią uzasadnia zachowanie wszystkich M podczas zwykłego restartu po wcześniejszym wykonaniu FB61. Po Overall Reset nie zachowuje M/T/Z. Nie ma podstaw do zbiorowego ustawienia wszystkich pól procesu, timerów i liczników S7 jako retencyjnych.
3. Parametru RS126 nie odwzorowywać automatycznie timerem 1 s po każdym przejściu RUN. Przyszłe wymagania opóźnienia S7 zależą od zasilania i gotowości nowych modułów, starych jednostek rozszerzeń i procesu. Nie jest to tutaj wdrożony kod ani test sprzętowy.
4. Wymagane materiały nadal obejmują schemat i listę modułów, bieżące nastawy/receptury i pozostałe listingi. [Dokumentacja konfiguracji COMTEXT](../comtext_review/USTALENIA_COMTEXT.md) została już dostarczona; sam podręcznik CPU nie rozstrzyga obsługi OP15 ani wszystkich ścieżek programu.
