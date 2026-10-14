# Dane S5 i interfejs OP15 — analiza dowodów do migracji

Ten dokument rozdziela odczytane fakty, interpretacje i proponowany interfejs S7/TP900. Nie jest projektem TIA ani instrukcją wgrania programu. Oryginały pozostają niezmienione. Użytkownik potwierdził zgodność kopii z maszyną i dostęp do STEP 5 oraz COMTEXT; tutaj analizowano wyłącznie kopie offline.

Uzupełnienie: otrzymano **128 stron wydruku konfiguracji COMTEXT ROLL@@LS.INI**. [Aktualny raport OP15](../comtext_review/USTALENIA_COMTEXT.md) i tabele w `comtext_review/` dokumentują adresy pól, zakresy, przypisania ekranów, klawisze, recepturę i obszary wymiany. Zestawienia surowych tekstów O15 z tego katalogu pozostają zapisem wcześniejszej analizy archiwum. Użytkownik dostarczył i potwierdził [pełne wartości programów 1 i 2](../operator_recipes/RECEPTURY_OPERATORA.md). Bieżące DB15/DB19 oraz zakres innych programów nadal pozostają do uzupełnienia.

## Zakres i śledzenie źródeł

Odczyty korzystają z pozycji bieżących wpisów `analysis/s5-all-directory-blocks.csv`; nie wyszukują starszych ciał bloków poza katalogiem. Dla każdego użytego ciała DB/DV skrypt sprawdza SHA-256 względem katalogu. Absolutne pozycje słów w S5D, formaty i źródła komentarzy są w CSV tego katalogu.

Interpretacja nagłówka DV korzysta ze źródła porównawczego [MC5toDB.cs](https://github.com/dotnetprojects/DotNetSiemensPLCToolBoxLibrary/blob/3d3eea50d9b24b53481809585f73e67f93ddb1d9/LibNoDaveConnectionLibrary/PLCs/S5/MC5/MC5toDB.cs#L29) oraz [S7DataRowType.cs](https://github.com/dotnetprojects/DotNetSiemensPLCToolBoxLibrary/blob/3d3eea50d9b24b53481809585f73e67f93ddb1d9/LibNoDaveConnectionLibrary/DataTypes/Blocks/Step7V5/S7DataRowType.cs#L79), commit `3d3eea50d9b24b53481809585f73e67f93ddb1d9`. Biblioteka liczy typy z DV[6:8], odczytuje znacznik z DV[9+4*n] i granice DW z DV[10+4*n] oraz DV[14+4*n]. CSV podaje początek dwubajtowego wpisu typu; właściwy bajt znacznika jest o jeden bajt dalej.

Pozycje i bajty są odczytane z wysoką pewnością. Znaczenie znaczników DV jest oparte na implementacji porównawczej i wymaga potwierdzenia w wydruku STEP 5. Deklaracja formatu słowa nie dowodzi użycia przez program ani aktualnej nastawy operatora.

## Fakty: wartości domyślne

DB12 (`DBDEF_T`, S5D offset 11648) zawiera 131 słów; DV12 (offset 1920) deklaruje następujące zakresy:

| DW, oba końce włącznie | Format |
|---|---|
| 0–21 | KT |
| 22 | KH |
| 23–33 | KT |
| 34–38 | KH |
| 39–44 | KT |
| 45 | KH |
| 46–49 | KT |
| 50–51 | KH |
| 52–78 | KT |
| 79–84 | KH |
| 85–123 | KT |
| 124–126 | KH |
| 127–130 | KT |

99 słów ma wartość `FFFF`. To poprawna surowa wartość KH, ale niepoprawne kodowanie KT: cyfry BCD są większe od 9, a bity zarezerwowane ustawione. Natywny listing FB101 potwierdził pomijanie takiego indeksowanego wpisu przez zwiększenie numeru parametru (S5D `0x20B0–0x20BE` dla DB15, `0x2100–0x210E` dla DB19). Jest to dowód funkcji znacznika pomijanego wpisu w edytorze. Nie wolno przeliczać `FFFF` na nastawę czasu ani zastępować wszystkich takich wpisów zerem.

32 słowa mają poprawne kodowanie KT, z czego 29 mieści się w zakresie DW0–127 kopiowanym przez FB105. Przykłady: DW17=`3360` → 360×10 s=3600 s; DW24=`1010` → 10×0,1 s=1 s; DW31=`3120` → 120×10 s=1200 s; DW55=`1010` → 1 s; DW127=`0038` → 38×0,01 s=0,38 s. To przeliczenia kodowania, nie dowód nastaw pracującej maszyny. DW128=`0038`, DW129=`2060`, DW130=`0000` również mają kodowanie KT, ale leżą poza pętlą kopiowania wartości domyślnych. Nie są nastawami T128–T130.

DB16 (`DBDEF_Z`, S5D offset 12416) zawiera 132 słowa. DV16 (offset 2048) deklaruje **KH dla wszystkich DW0–131**, nie KZ. 126 słów ma `FFFF`. Pozostałe: DW1 i DW2=`0005`, DW128 i DW129=`0002`, DW130=`0005`, DW131=`0000`. Same bajty nie rozstrzygają między binarnym a BCD, ale listing PB13 pokazuje DB19 DW1→`S Z1` (`0xFDA8/0xFDAA`) i DW2→`S Z2` (`0xFDCA/0xFDCC`), po otwarciu DB19 w `0xFD88`. Wraz z kopiowaniem DB16→DB19 przez FB105 dowodzi to użycia dwóch źródeł domyślnych jako presetów liczników S5, kodowanych dla instrukcji `S Z` w BCD. W obu wypadkach wartość domyślna wynosi 5. Deklarację KH należy zachować w dowodach; nie zmienia ona semantyki instrukcji odbiorcy. Z3 jest ustawiany stałą `KZ500` (`0x101DE/0x101E2`), nie z DB16 DW3. CSV rozdziela te potwierdzone użycia od pozostałych kandydackich interpretacji.

Nie ma bieżących wpisów katalogu DB15 (`DBVZEIT`) ani DB19 (`DBVZAEHL`). Z archiwum DB12/DB16 nie da się odtworzyć ich bieżących, edytowanych wartości. Natywny wydruk FB105 potwierdził pętle kopiujące tylko DW127…0 z DB12→DB15 oraz DB16→DB19. Rozstrzygnął też instrukcję `7805`: angielskie `G DB`, czyli niemieckie `E DB`. Operand DX w tabeli porównawczej był błędny i został poprawiony w czytniku. Nie należy inicjalizować nowego PLC wyłącznie wartościami domyślnymi, pomijając istniejące nastawy.

Instrukcja CPU potwierdza, że parametr 131 tworzy **132 wyzerowane słowa DW0…DW131**, a istniejący DB pozostaje bez zmiany przez samo `G DB`. Osobna pętla FB105 może jednak nadpisać nastawy, jeśli zostanie wykonana. DB generowane przez tę instrukcję znajdują się w RAM podtrzymywanym sprawną baterią. Użytkownik potwierdził sprawną baterię i RE; retencja danych DB nie zależy od przełącznika RE/NR. Przy zwykłym restarcie z zachowanym M0.4 OB1 pomija FB105. [Warunki i dowody](../CPU_S5_USTALENIA.md). Aktualne wartości DB15/DB19 nadal trzeba pozyskać z działającego układu.

Natywny FB101 potwierdził w **roboczych DB15 i DB19** DW128 jako bieżący numer parametru, DW129 jako poprzedni numer, a DW130 jako bufor edycji. Zmiana numeru wczytuje wybrany parametr do bufora; przy tym samym numerze bufor zapisuje się do indeksowanego parametru w każdym wywołaniu, bez osobnego sygnału zatwierdzenia w tym bloku. Przy czytaniu listingu trzeba zachować semantykę porównań S5: `!=F` oznacza równość, a `><F` nierówność. To nie znaczy, że ogon źródłowych DB12/DB16 jest kopiowany do tych pól — pętle FB105 go pomijają. Warunki zakresu również nie są symetryczne: DB15 dla numeru ≥128 zapisuje 0 do DW128 i kończy tę część, natomiast DB19 zapisuje 0 do roboczego MW240 i kontynuuje; nie kopiuje w tym miejscu zera do DW128. Brakuje jawnej kontroli dolnej granicy signed oraz poprawności edytowanej wartości. Otrzymany COMTEXT określa limity numerów 0…128 i typy pól SP-ACT.VALUE; pomoc podaje 0…127. Nie dowiedziono jeszcze sposobu zatwierdzania wszystkich pól. MW240 obejmuje adresy M240.x etapów FB105; docelowo proponuje się osobną pamięć inicjalizacji i indeksów roboczych.

W O15 odczytano teksty: offset 40132 „Zaehlernummer eingeben 0 ... 127”, 40274 „Zeitnummer eingeben 0 ... 127”, 40025 „Wert eingeben 0 ... 999”, 40167 „Zeit eingeben 0.0 ... 9990 Sekunden”. Otrzymany COMTEXT potwierdza te teksty pomocy, adresy wyboru DW128 i bufora DW130 oraz formaty KT dla czasu i KC dla licznika. Powiązania numerów mają jednak limity 0…128, co różni się od tekstów pomocy 0…127. Zakres i korekta FB101 wymagają odrębnej decyzji w migracji.

## Fakty: dane panelu i polecenia

| Źródło | Fakt z archiwum | Granica interpretacji |
|---|---|---|
| DB205, 221 DW | Symbol `REZEPT`, komentarz `OP15 REZEPTFACH`; DW0=`0102`, DW1=`002E`; DW2–45 tworzą 11 czwórek `02FF / 00C6 / 0001 / wartość`; DW46–220 są zerowe. FB89 dzieli DW0 na dwa bajty i sprawdza: receptura1, numer zestawu1–99 | Trzy słowa opisu czwórki i DW1 nadal wymagają COMTEXT/protokołu; to bufor pojedynczego transferu, nie lista wszystkich receptur |
| DB206, 28 DW | Komentarze DK206: DW0–2 odnoszą się do menu1/poziomu komunikatów; DW8–11 do obrazu procesu dla trybu ręcznego, obraz10, wpis0, pole0. Surowo DW0=48, DW1=1, DW8=51, DW9=10 | Liczby poleceń i parametrów muszą być potwierdzone dokumentacją protokołu/STEP 5 |
| DV206 | DW0–1 KF; DW2–3 KH; DW4–5 KF; DW6–7 KH; DW8 KF; DW9–10 KY; DW11–12 KF; DW13–14 KY; DW15–16 KF; DW17–18 KY; DW19–22 KF; DW23 KH; DW24–27 KF | KY oznacza parę bajtów, nie zwykłe Int; np. DW9=`000A` wymaga zachowania znaczenia obu bajtów |
| DB210, 129 DW | Natywny FB91: MB5…19 do alarmów DW0…7 z zamianą bajtów; NOT MB5…20 do potwierdzeń DW17…24. Natywne FB92/96: MB37…53 do kroków DW50…58 | [Tabela 120 bitów](../native_verification/alarm-memory-and-text-map.csv) i [bajtów N1](../native_verification/N1-event-byte-map.csv). Źródła/kasowanie alarmów i dalsza logika procesu wymagają pozostałych bloków |
| DB211, 11 DW | Natywny FB3 czyta DW5 jako typ/numer obrazu i DW6 jako wpis/funkcję ręczną; DW2/3 to obraz klawiatury funkcyjnej, DW0/1 systemowej. Archiwum: DW5=`0101`, DW6=`0202`, DW8=`0003` | Mapowanie FB3 i COMTEXT potwierdzone; odbiorcy poleceń w procesie nadal wymagają własnych listingów |
| DB213, 11 DW | Symbol `DBAUF`; FB60 zapisuje `KY0,70` do DW1, 1 do DW2 i wybrany numer programu z DB60 DW11 do DW3, a DB51 DW60/61 wskazują DB213/DW1. Snapshot DW1=`0046`, DW2=1, DW3=2 odpowiada temu układowi | Kierunek wynika z FB60: PLC przygotowuje żądanie programu do OP. Stary komentarz symbolu „OP15-AG” nie wystarcza do określenia kierunku. Numer polecenia70 wymaga potwierdzenia w dokumentacji |
| DB219, 31 DW | Brak symbolu; DV219 deklaruje wszystkie słowa jako KF. DW11,21,23=2, reszta=0 | Funkcja nieustalona; nie usuwać jako „nieużywany” |

Nazwy w symbolach opisują MB187 jako status zleceń standardowego FB51 i MB188 jako numer błędu. FB3 potwierdza zapisywanie wyniku FB51 do MW187 i rozpoznaje błędy115/188. Nie odkodowano wszystkich wartości statusu/błędu. M191.0 to identyfikacja startu OP15; M191.3 błąd FB51; M191.4 poprawność programu czyszczenia; M191.5–7 odpowiednio transfer receptury w toku, koniec i potwierdzenie. M190.1/M190.2 są w kodzie FB89/FB60 potwierdzeniami programu poprawnego/niepoprawnego. Komentarz FB60 „gut/FE” odnosi je do 192.0/192.1, lecz aktualny kod używa M190.1/2 — komentarz jest nieaktualny względem użytych operandów. M192.0/1 pozostają w FB3 stanami F1/F2.

FB89 kod pokazuje nadzór transferu przez T100 ze stałą `KT005.2` (5 s), potwierdzenie sukcesu/błędu i aktualizację DB51 DW64. Komentarz „DS-Nr. <= 10” jest sprzeczny z kodem porównującym numer do99 (`0x18B8`, `KF+99`). W tym listingu rozpoznawany zakres zestawu to1–99; COMTEXT potwierdza wybór programu 1…99 w PV-FAHRPROGR; zakres rzeczywiście zapisanych zestawów nadal nie jest dostarczony.

## Pola receptury ustalone przez instrukcje

`recipe-fields-from-code.csv` podaje pozycje i bloki odbiorców. Według FB90 i FB111: DW5/17/25/33 to czasy zanurzenia stacji1/2/3/4; DW9/21/29 to czasy ociekania stacji1/2/3. Wartości są bezpośrednio używane do uruchamiania T1/T2; FB90 maskuje bazę czasu (`0FFF`) i na podstawie niezerowej wartości wybiera stacje. DW13==1 włącza ultradźwięki stacji1. DW37 rozpoznaje1=obrót,2=kołysanie,3=obrót interwałowy,4=obrót/kołysanie. DW41==1 włącza ruch pionowy w kąpieli. Odbiorca jedenastej wartości DW45 pozostaje nieustalony.

**Archiwalny bufor nie dowodzi poprawnej receptury roboczej:** DW13=`2020`, DW37=`2150`, DW41=`0002` leżą poza wskazanymi typowymi kodami Bool/enum. Instrukcje nie interpretują ich jako wartości czasu w tych trzech polach; np. DW37 nie ustawi żadnego z czterech rozpoznanych wyborów ruchu. Nie wolno z tego bufora konstruować rzekomo aktualnego programu/receptury. Należy zabezpieczyć wszystkie rzeczywiste zestawy zapisane w OP15 i potwierdzić ich definicję COMTEXT.

## Przyciski: dowody i niewiadome

MW192 jest opisany jako obraz klawiatury. M192.0–M193.7 opisują naciśnięcie F1–F16; M194/M195 — znaczniki pomocnicze zboczy; M196/M197 — przerzutniki F1–F16. M190.3 opisuje zbocze przycisków ruchu pozycja bazowa/robocza, M190.4 znacznik pomocniczy tego zbocza, M190.5/6 stany przycisków, M190.7 zbocze co najmniej jednego F. M198.0 to klawisz przejęcia/potwierdzenia. M199 to znaczniki robocze, które nie stanowią automatycznie interfejsu HMI.

Listing potwierdza rozróżnienie stanu, zbocza i pamiętanego wyboru. FB3 wyprowadza M190.5/F13 z tego samego bitu4 starszego bajtu DB211 DW2, a M190.6/F16 z tego samego bitu7. M190.3 jest zboczem **alternatywy obu** klawiszy; znacznika pomocniczego nie resetuje się, dopóki oba klawisze nie są zwolnione. Zamiana klawisza bez zwolnienia drugiego nie daje nowego wspólnego zbocza. Fragmenty O1542753–42896 wymieniają K13/K16 przy odpowiednich funkcjach; otrzymany COMTEXT potwierdza offsety K13=12 i K16=15 w obszarze klawiatury, zgodne z odczytem F13/F16 w FB3.

PB16 ma **34 natywne sieci FBD porównane ręcznie**. Potwierdził utrzymane stany M190.5/6, m.in. w M74.4 i M75.4, sprzężenia M75.3/M77.1 i zatrzaski M78.4/.6/.7. PB15 doprecyzował M74.0: wymaga przytrzymanego K13 i nie jest samodzielnym zatrzaskiem; PB16 odczytuje poprzednią wartość. Nie wszystkie pozostałe gałęzie są „trzymaj, aby jechać”. Pełny FB92 skorygował wcześniejszy opis fragmentu F2: późniejszy reset zawiera sam M192.1, więc naciśnięcie zeruje M196.1 do końca tej sieci; nie jest to trwały toggle. [Warunki PB16 i wyjaśnienie FB92](../native_verification/WERYFIKACJA_PARTIA3.md), [źródło M74.0](../native_verification/WERYFIKACJA_PARTIA5.md). Nie zastępować wszystkich klawiszy jednym rodzajem impulsu lub jedną regułą zatrzasku.

Do migracji potrzebne jest osobne odwzorowanie każdej funkcji: naciśnięcie, zwolnienie, zbocze, zatrzaśnięcie, warunki zezwolenia, zachowanie przy zmianie ekranu i utracie komunikacji. Sterowanie ruchem na panelu dotykowym wymaga potwierdzenia rzeczywistej logiki na podstawie listingu i schematu. Samo skopiowanie bitu klawiatury do TP900 nie rozstrzyga tych zależności.

## Proponowany interfejs S7/TP900 — do zatwierdzenia przez analizę

Propozycja nie przydziela jeszcze stałych offsetów S7 ani wartości enum. Struktury mają mieć symboliczne pola i jednoznacznego autora zapisów.

| Grupa | Autor danych | Pola proponowane | Dowód i wymagane uzupełnienie |
|---|---|---|---|
| Statusy maszyny | PLC | tryb, kroki sekwencji, zezwolenia ruchów, wybrane/aktywne parametry, statusy pomp/grzania | DB210, symbole maszyny; pełny listing i mapowanie pól COMTEXT |
| Polecenia operatora | HMI, przyjęcie przez PLC | wybór funkcji ręcznej, żądanie ruchu, pozycja bazowa/robocza, opróżnianie; identyfikator przyjęcia/odrzucenia polecenia | M190, MW192, DB211; osobna semantyka każdego naciśnięcia/zwolnienia |
| Nawigacja i sygnalizacja | HMI/PLC zgodnie z potrzebą | aktualny ekran i wybór sekwencji, żądanie wyświetlenia; wizualne odpowiedniki aktywnych LED | FB3/FB92/FB95, DB206, M189; aktywne numery ekranów i priorytety |
| Receptura oczekująca | HMI, walidacja PLC; PLC może żądać wczytania z HMI | numer programu, komplet pól receptury, żądanie transferu, identyfikator transferu | DB205/DB213 i FB60/89/90; definicje wszystkich pól i aktualne zestawy danych |
| Status receptury | PLC | w toku, zakończona, przyjęta, błąd/timeout, program aktywny | M190.1/2, M191.4–7; dokładne warunki i limity, kontrola przerwanego transferu |
| Nastawy czasu/liczników | HMI, przyjęcie PLC | numer parametru, typowana wartość, limity, zatwierdzenie i wynik; wartości robocze oddzielone od fabrycznych | DB12/16 vs DB15/19; listy odczytów/zapisów i aktualne nastawy |
| Alarmy | PLC, potwierdzenie zgodnie z logiką | bity/identyfikatory, teksty, klasy, aktywność i potwierdzenia | PB2/FB91, tabela symboli, COMTEXT; mapowanie bit→tekst i procedury kasowania |
| Diagnostyka połączenia | PLC/HMI | stan połączenia, restart panelu, ostatni transfer, kod błędu | Stare MB187/188/M191.0/3 opisują FB51; nowe znaczenie ustalić po zastąpieniu protokołu |

Stare znaczniki zboczy/przerzutników i pamięć robocza komunikacji pozostają częścią analizy PLC; nie należy udostępniać ich wszystkich jako edytowalnych tagów panelu. Decyzje o retencji, typie TIME/UInt/Bool/enum i atomowym przyjęciu receptury nastąpią po rozpoznaniu instrukcji.

## Zakres dokumentacji COMTEXT — otrzymany wydruk

Poniższa lista była zakresem wymaganej dokumentacji. ROLL@@LS.INI dostarczył definicje ekranów, pól, klawiszy, komunikatów, obszarów i PRG; nie trzeba ponownie eksportować tych definicji. Dokładne warunki w PLC, zachowanie przy utracie połączenia, porządek bitów alarmów i rzeczywiste zestawy wartości nadal wymagają uzupełnienia. Zakres kontrolny obejmuje:

1. Aktywne ekrany/obrazy procesu i menu: numer/nazwa, numer każdego wpisu i pola, kolejność/układ, wszystkie teksty i pomoc, przejścia i uprawnienia poziomów. Szczególnie tryb ręczny, przebieg kroków, wybór/edycja programu oraz czasy/liczniki.
2. Każde pole I/O: rodzaj wejście/wyjście, połączenie, obszar PLC, numer DB, DW/DL/DR/bit, długość, format KF/KH/KY/KZ/KT lub inne, skalowanie, jednostka, miejsca dziesiętne, granice, sposób zatwierdzenia i powiązanie dynamicznych adresów. Potrzebne również wskaźniki numeru parametru/pośrednie adresowanie czasów/liczników.
3. Klawiatura: wszystkie F/K oraz systemowe klawisze i LED; funkcje globalne i zależne od ekranu/wpisu, dane zapisywane przy naciśnięciu/zwolnieniu, sekwencje, zatrzaski, wymagane SHIFT i powiązania z obrazem klawiatury. Zwłaszcza K13/K16 i klawisz przejęcia.
4. Wskaźniki obszarów i komunikacja: typ połączenia, adresy i długości obszarów, aplikacyjne/zleceniowe obszary DB206/213, obraz klawiatury i LED, informacje o ekranie, alarmy, receptury, synchronizacja/start panelu oraz mechanizm potwierdzania. Parametry uwierzytelnienia/hasła nie są potrzebne w eksporcie.
5. Komunikaty: wszystkie aktywne teksty, numer, klasa, priorytet, adres wyzwolenia, numer bitu i kolejność bajtów/słów, wymagania potwierdzenia, reset, pomoc i dynamiczne wartości w tekście.
6. Definicje receptur: numer/nazwa, kolejność i typ każdego pola, adres docelowy, zakres, skalowanie, jednostka, format nagłówka/obszaru, blokady transferu i potwierdzenia sukcesu/błędu. Osobno wszystkie aktualne zestawy danych/numery programów; plik projektu nie dowodzi zachowania danych później zapisanych w panelu.

Otrzymano DB15/DB19 oraz porównano 42 pełne bloki, w tym wszystkie PB. [Komplet 50 stron schematu](../schematic_review/ZASILANIE_BLOKADY.md) jest przeanalizowany; pozostają końcowe modele S7, sprawdzenie szczegółów połączeń, FB0, ciało FB51 i formaty archiwalnych DB. [Lista braków](../native_verification/BRAKUJACE_BLOKI_STEP5.md).

## Artefakty i ograniczenia

- `declared-db-format-regions.csv`: granice i znaczniki DV12/16/206/219.
- `timer-counter-defaults.csv`: wszystkie 263 słowa DB12/16, surowe wartości, deklarowany format, kontrola kodowania i oddzielone kandydackie powiązanie T/Z.
- `hmi-db-raw-typed-evidence.csv`: wszystkie słowa DB205/206/210/211/213/219 wraz z formatem, jeśli jest zadeklarowany, i komentarzami DW.
- `hmi-key-and-status-symbols.csv`: dokładne symbole M187–199 i MW192 z wierszami źródłowymi.
- `op15-parameter-key-help-fragments.csv`: wybrane literalne teksty O15 i pozycje w pliku; nie jest dokumentacją aktywnych ekranów.
- `hmi-and-parameter-code-evidence.csv`: sprawdzone surowe opkody/pozycje, odczyt instrukcji i oddzielone wnioski o edytorze parametrów, licznikach, recepturze i klawiszach.
- `recipe-fields-from-code.csv`: 11 pól wartości bufora, ich odbiorcy i kodowanie; flagi niezgodności snapshotu z rozpoznawanymi enumami.
- `evidence-summary.json`: sumy SHA-256 i podsumowanie.
- `review_data.py`: odtwarza CSV, sprawdza sumy i zgodność wybranych fragmentów ASCII z oryginałem; zapisuje tylko do tego katalogu.

Porównano **42 pełne bloki offline**. [Szósta partia](../native_verification/WERYFIKACJA_PARTIA6.md) potwierdziła proces i sygnalizację. Otrzymane DB15 ma T116/T117 po 5 s, T24/T25 po 1/2 s, a DB19 Z1=20/Z2=14. A17.7 jest poleceniem kontaktu zakończenia czyszczenia powiązanym z funkcją drzwi, nie bezpośrednim czujnikiem. Programów operatora 1/2 nie zmieniono; nie uruchomiono TIA ani procesu.
