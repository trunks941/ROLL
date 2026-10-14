# ROLL — założenia startu, taktów i nastaw dla S7

Wersja robocza: 12 października 2026. Cel: CPU 1513-1 PN `6ES7513-1AM03-0AB0`, TIA Portal V19 i planowany TP900 Comfort. Dokument określa podstawę dalszego projektu; nie zawiera programu TIA, konfiguracji fizycznych I/O ani instrukcji uruchomienia maszyny. Firmware zamówionego CPU, obecność STEP 7 Professional i wariant panelu pozostają do sprawdzenia.

Podstawą są **42 pełne natywne bloki**, [otrzymane DB15/DB19](native_verification/DB15_DB19_NASTAWY.md) i [komplet 50 stron schematu](schematic_review/ZASILANIE_BLOKADY.md). [Szósta partia](native_verification/WERYFIKACJA_PARTIA6.md) potwierdziła proces, RAV i sygnalizację. Zachować nastawy czasu oraz Z1=20/Z2=14. A21.5 ma dwóch kolejnych autorów; A17.7 jest poleceniem bezpotencjałowego kontaktu zakończenia czyszczenia. Wentylator pozostaje na %Q24.4 z A24.0 OR A24.2, lampka %Q16.0 z E1.2 OR E3.4. Zachować fizyczne PNOZ, odcięcia MF, sterowanie hamulcami i zewnętrzne regulatory temperatury. Potrzebne są końcowe modele S7 według zachowanej klasy prądowej i sprawdzenie szczegółów połączeń. FB0 i ciało FB51 pozostają poza pełnym porównaniem.

Użytkownik zidentyfikował starą CPU jako **6ES5 942-7UB11** (CPU 942), potwierdził **RE i sprawną baterię** oraz dostarczył instrukcję Edition 04, EWA4NEB8116130-02b. [Ustalenia CPU](CPU_S5_USTALENIA.md) potwierdzają interwał, zakres retencji i działanie opóźnienia konfiguracji.

## Potwierdzone zachowanie S5

| Obszar | Fakt wynikający z natywnych wydruków |
|---|---|
| Dopuszczenie logiki procesu | OB1 wywołuje FB105 przy wyzerowanym M0.4 i może zakończyć obieg przed logiką procesu. FB105 po zakończeniu ustawia M0.4. |
| Wartości domyślne | FB105 kopiuje DW127…DW0 z DB12 do DB15 oraz z DB16 do DB19, etapami po jednym słowie. Tworzone DB15/19 mają 132 wyzerowane słowa DW0…131. Nie kopiuje pól DW128–131. Samo G DB pozostawia istniejący DB bez zmiany; późniejsze kopiowanie jest osobną operacją. |
| Start | OB21 i OB22 mają identyczne instrukcje: wywołują FB61, ustawiają znaczniki M0.1/M0.2 oraz M191.0 sygnalizujący start panelu. Nie wykonują ogólnego zerowania pamięci. |
| Dalsza obsługa restartu | PB50 resetuje M0.2 przy M0.1, a OB1 w kolejnym obiegu resetuje M0.1 przy braku M0.2. T11 uruchamia 8 s opóźnienia ogólnej sygnalizacji alarmów przy E3.0 i braku M0.1. |
| Zezwolenia | PB7 zatrzaskuje M29.0 z HAND lub AUTO/AUTO_EIN i resetuje przy braku M28.6. M29.1 dodaje T13=2 s, liczony wcześniej w PB50. AUTO_E M31.4 i AUTO_L M31.5 mają odrębne warunki resetu. |
| Kroki N1 | PB9/PB10 zapisują 111 bitów kroków w kolejności S/R; nie potwierdzono zasady jednego aktywnego bitu ani jednego przejścia na obieg. PB8 nadzoruje tylko wybrane fazy ruchu przez T40/T41=30 s. |
| Dojazd i BADHUB | M74.0 z PB15 wymaga przytrzymanego K13 i jest czytany wcześniej w PB16. BADHUB=aus wyłącza krótki ruch w kąpieli, bez wyłączenia zwykłego podnoszenia/opuszczania transportu. |
| Ustawienia CPU | RS97=25 ustawia nominalny interwał OB13 250 ms. RS120 OR0008 włącza retencję wszystkich M przy RE; FB61 nie ustawia bitów pełnej retencji T/Z. RS126=1000 jest opóźnieniem sprawdzania konfiguracji modułów przy następnym cyklu zasilania, nie timerem bieżącego startu. |
| Edycja nastaw | W DB15/DB19 DW128 wybiera parametr, DW129 przechowuje poprzedni wybór, DW130 jest buforem edycji. Nowy wybór ładuje bufor; niezmieniony wybór powoduje cykliczny zapis bufora do parametru, bez oddzielnego zatwierdzenia w FB101. `FFFF` jest pomijane przez zwiększenie indeksu. |
| Klawisze | FB3 potwierdza stany K13/K16 na M190.5/M190.6 i wspólne zbocze OR na M190.3. Przy błędach 115/188 zeruje roboczy obraz klawiatury i unieważnia wybór funkcji ręcznej; reakcje procesu nadal wymagają odbiorców. |
| Żądanie receptury | FB60 używa etapów 10…13 i T101=5 s. FB89 potwierdza odbiór i odpowiedzi M190.1/.2, T100=5 s w fazie transferu, definicję 1 i zestawy 1…99. Potwierdzenie skrzynki jest oddzielne od poprawności programu; ciało FB51 nadal niezweryfikowane. |
| Aktualne czasy | FB3 przesyła LC T1/T2 do DB210.DW70/71: aktualna wartość BCD z bazą czasu. FB69 wybiera 0,5 s lub 5 s do MW240; sam nie uruchamia timera. |
| Zachowanie pamięci wokół drivera | FB62/63 zapisują i odtwarzają 20 słów MW200…MW238 przez co drugie słowo DB41.DW0…38. |

Granice indeksu w FB101 są asymetryczne. Dla czasów indeks ≥128 zeruje DW128 i kończy część obsługi; dla liczników zeruje tylko roboczy MW240 i kontynuuje obsługę wpisu 0. Brakuje jawnej kontroli dolnej granicy przy porównaniu signed `<F`. Ograniczenia pola panelu i walidacja wartości nie są dowiedzione tym blokiem. W notacji S5 `!=F` oznacza równość, a `><F` nierówność.

## Proponowana struktura danych i start S7

Zadeklarować statyczne DB z osobnymi grupami: wartości fabryczne, aktualne nastawy operatora, stan inicjalizacji, stan procesu, takty oraz wymiana HMI. Używać pól symbolicznych z opisanym autorem zapisu. Zachować bieżące nastawy RAM i odpowiednik M0.4 podczas zwykłego restartu. Dla stanów przenoszonych ze znaczników M uwzględnić potwierdzoną retencję oraz późniejsze jawne resety w logice procesu. Zakres retencji timerów/liczników wymaga ustalenia pozostałych bitów RS120 i odbiorców; nie wynika z maski 0008.

Stan inicjalizacji musi być niezależny od indeksów roboczych. W S5 MW240 obejmuje bajty MB240 i MB241; FB105 przechowuje bity etapów w M240.x, a FB101 później używa MW240 jako indeksu. Ta współdzielona pamięć działa w określonej kolejności programu. W strukturach S7 proponuje się osobne pola dla etapu, indeksu kopiowania i indeksu edytora, bez przenoszenia tej zależności adresowej.

Przewidzieć osobne ścieżki pierwszego przygotowania danych oraz zwykłego restartu. Przy zwykłym restarcie zachować poprawne, przeniesione nastawy operatora; wartości domyślne nie powinny ich automatycznie nadpisywać. Przy zachowanym M0.4 S5 pomija FB105. Pierwsze przygotowanie wymaga rozpoznania dostępności i wersji danych oraz zakończenia inicjalizacji przed dopuszczeniem logiki procesu. Po Overall Reset S5 kasuje M/T/Z niezależnie od RE; nie traktować tej operacji jak zwykłego STOP/RUN. Odtworzyć programowe zmiany stanów sekwencji, zezwoleń i sygnałów restartu na podstawie pozostałych bloków.

Kasowanie ogólne usuwa także wewnętrzną pamięć programu i moduł RAM CPU 941/942, w tym generowane DB15/DB19 (instrukcja PDF 116 / 4-2). Nastawy tych DB nie przetrwają tej operacji. W S7 trzeba odrębnie określić skutki kasowania pamięci i ponownego wgrania danych, niezależnie od reguły zwykłego restartu.

## Takty

Dla odpowiednika OB13 proponuje się OB przerwania cyklicznego S7 z **interwałem 250 ms, potwierdzonym instrukcją CPU 942**. W S5 zapis RS97 nadpisuje początkowe ustawienie DB1; nie należy przenosić domyślnych 100 ms zamiast wartości ustalonej w FB61. Nominalne okresy dzielnika są podane niżej.

| Odpowiednik S5 | Czas między przełączeniami przy 250 ms | Pełny okres |
|---|---:|---:|
| M3.4 | 250 ms | 500 ms |
| M3.5 | 500 ms | 1 s |
| M3.6 | 1 s | 2 s |
| M3.7 | 2 s | 4 s |

Porównać wykorzystane zbocza, początkowy stan i fazę po restarcie. Nie przyjmować nazwy symbolu jako pełnego okresu ani bez sprawdzenia zastępować dzielnika bajtem zegarowym S7. RS126 dotyczy opóźnienia sprawdzania konfiguracji modułów po następnym POWER OFF/ON, przed OB22. Nie zastępować go bezpośrednio timerem blokującym proces przez 1 s po każdym przejściu S7 do RUN; wymagania gotowości nowych modułów wynikną ze schematu i docelowej konfiguracji.

OB31 w FB105 restartuje systemowy monitor czasu cyklu. Docelowy podział inicjalizacji i limit cyklu S7 trzeba dobrać do rzeczywistego wykonania; wywołania nie są pustymi funkcjami do pominięcia na podstawie ich surowego listingu.

## Parametry i panel

Proponowane tablice obejmują indeksy 0…127 z osobną flagą użycia wpisu, jego typem i wartością. Zachować surowy zapis S5 jako dowód; `FFFF` odwzorować jako informację o nieużywanym wpisie, bez zamiany na czas lub zero. DW128–130 odwzorować jako oddzielny stan edytora, poza tablicą nastaw. Robocze DB S5 mają także DW131: nowo tworzone ma zero, leży poza FB101 i kopiowaniem. Jego ewentualne wykorzystanie w pozostałych blokach lub COMTEXT trzeba sprawdzić przed pominięciem.

Typy docelowe ustalić według instrukcji odbiorców, nie tylko formatów wyświetlania DV. KT wymaga rozpoznania bazy czasu i cyfr BCD; presety liczników używają BCD zgodnie z instrukcjami S5. Konwersję do TIME lub liczby całkowitej poprzedzić kontrolą poprawności, jednostek, zakresu i zachowania timerów/liczników w pozostałych blokach. Nie ma jeszcze podstaw do jednolitej zamiany wszystkich timerów S5 na jeden rodzaj timera IEC.

Rozdzielić wybór operatora, wartość prezentowaną i wartość przyjętą przez PLC. Odtworzenie obecnej edycji wymaga zachowania cyklicznego zapisu DW130 i kolejności zmiany indeksu. **Jawne polecenie zatwierdzenia** jest proponowaną alternatywą, która zmienia zachowanie; wymaga świadomego porównania z obecną obsługą. Również jawne odrzucanie ujemnych lub niedostępnych indeksów zmieniałoby niektóre ścieżki FB101. Nie przesądza się jeszcze tych decyzji.

Ustalić zachowanie edytora po zmianie ekranu, restarcie panelu i utracie komunikacji. Kolejność oraz potwierdzanie wymiany mają zapobiegać zapisowi wartości z bufora poprzedniego parametru do nowego indeksu. COMTEXT określa dolny limit numerów 0, górny 128, format czasu KT i licznika KC; pomoc podaje numery 0…127. Zachować rozróżnienie konfiguracji i korekty FB101, zamiast przyjmować wspólny zakres bez wyjaśnienia. Szczegóły są w raporcie COMTEXT.

W recepturze nowego panela zachować tryb obrót/kołysanie (wartość symboliczna 4), którego dostępność na OP15 potwierdził użytkownik. Limit 0…3 wydrukowany dla PRVKB nie jest podstawą usunięcia tej opcji. Dla pompy dozującej RAV zachować włączenie podczas przytrzymania odpowiednika K16 — potwierdza to pomoc HBEIN przypisana do aktywnego wpisu 66. Reakcję przy utracie komunikacji i logikę pozostałych klawiszy ustalić z kodu PLC.

Nowy interfejs poleceń powinien rozdzielać utrzymany stan K13/K16 od wspólnego zbocza ich alternatywy i zatrzasków potwierdzonych w PB16. PB15 potwierdził przytrzymany charakter M74.0; PB16 czyta poprzednią wartość, a odrębne podtrzymania wyjść nadal wymagają uwzględnienia. Transfer powinien rozdzielać definicję PRG, numer programu, odbiór skrzynki i poprawność danych — natywne FB60/89/90/111 oraz warunek przejścia M37.2→M37.3 potwierdzają tę podstawę. FB111 używa progu 7 jednostek aktualnej bazy T1 do ustawiania bębna prosto w trybie 4; przed zamianą na TIME potrzebne jest rzeczywiste kodowanie KT. FB91 potwierdza zamianę bajtów alarmowych i zanegowane bity potwierdzeń PLC; PB2 potwierdził reguły kasowania. Diagnostyka baterii OB34/M16.5 dotyczy starego sprzętu; dla S7 dobrać właściwe statusy nowej CPU.

## Scenariusze późniejszego porównania w symulacji

| Scenariusz | Co należy wykazać |
|---|---|
| Restart z istniejącymi nastawami | Nastawy operatora pozostają zachowane; inicjalizacja nie kopiuje bezwarunkowo wartości fabrycznych. Zachowanie stanów procesu odpowiada ustalonej regule startu. |
| Pierwsze przygotowanie lub brak danych | Dane stają się kompletne przed dopuszczeniem procesu; wartości fabryczne i przeniesione nastawy są jednoznacznie rozróżnione. |
| Zmiana wyboru podczas edycji | Nowy parametr wczytuje właściwy bufor; poprzedni bufor nie nadpisuje innego wpisu. Wariant cykliczny i ewentualny wariant z zatwierdzeniem porównuje się osobno. |
| Wpis nieużywany i indeks poza zakresem | Zachowanie `FFFF`, końca tablicy, wartości ujemnej i asymetrii czas/licznik jest udokumentowane; każda zamierzona zmiana ma jawny wynik porównania. |
| Utrata i powrót komunikacji HMI | Nie występuje przypadkowy zapis starego bufora ani przyjęcie niepełnego polecenia; odświeżenie ekranu i wznowienie edycji przebiegają według ustalonej reguły. |
| Takty i kodowania | Okresy, zbocza i faza po restarcie są zgodne z potwierdzonym interwałem; wartości KT/BCD oraz niepoprawne kody dają ustalone wyniki. |
| Ociekanie i pauza bębna | Wybrany obrót daje obrót interwałowy we właściwych fazach ociekania; T116/T117 zachowują aktualne nastawy, a T115 odpowiada opóźnieniu wyłączenia z wyborem 0,5/5 s. |
| Kasowanie alarmu z trwającą przyczyną | Reguły PB2 zachowują pierwszeństwo resetu i dodatkowe warunki czujników; ACK panelu i kasowanie PLC mają odrębne wyniki. |
| Zmiana kierunku i status funkcji | Wynik uwzględnia kolejność odczytu/zapisu obrazu wyjść; wskazanie oparte na poleceniu nie jest prezentowane jako pomiar czujnika. |
| Start i zatrzymanie automatu | M29.0/M29.1, AUTO_E/AUTO_L i M35.2 zachowują odrębne warunki oraz opóźnienia; zatrzymanie i powrót bazowy odpowiadają kolejności OB1. |
| Przejścia kroków i zmiana trybu | Porównać kilka spełnionych przejść w jednym obiegu, późniejsze resety poprzednich bitów i wybór bloków przez M3.3; nie założyć sekwencji one-hot. |
| Przytrzymanie dojazdu i korekta śledzenia | Zwolnienie K13 i błąd komunikacji propagują się przez FB3/PB15/PB16 w odtworzonej kolejności. Korekta zeruje wszystkie siedem bitów, mimo wskazania panelu obejmującego pięć. |
| Stałe timerów i BADHUB=aus | T16 ma 3600 s, T45 ma 0,5 s, a T11/T13 odpowiednio 8/2 s. Wyłączenie BADHUB pozostawia normalny transport pionowy. |

To wymagania do przyszłych testów, a nie wyniki uruchomionej symulacji.

## Materiały potrzebne do zamknięcia założeń

- Końcowe modele S7 i modele G1/PNOZ, typ modułu pamięci i sprawdzenie szczegółów połączeń. Komplet stron 1–50, zdjęcie całej kasety, CPU `6ES5942-7UB11`, instrukcja, RE oraz sprawna bateria są już dostarczone; nie trzeba ich ponownie przesyłać.
- DB15/DB19 otrzymano w całości: 264 słowa, 26 nastaw KT i dwa presety BCD. Programy 1/2 są kompletne; zakres innych używanych programów i surowe kodowanie KT receptur pozostają odrębnymi tematami.
- Konfiguracja COMTEXT i programy 1/2 są już dostarczone. Pozostają ewentualne inne używane zestawy oraz wyjaśnienie pełnego odbioru, zatwierdzania i mapowania alarmów przez porównanie kodu PLC.
- Wszystkie PB porównano. Do kompletności kodu pozostaje FB0; FB51 nadal pokazuje tylko początek i nie wymaga ponawiania identycznego eksportu.
- Pełna natywna dokumentacja pozostałych bloków, w tym odbiorców timerów/liczników i znaczników restartu oraz DB z formatami danych.
- Po dostawie: firmware CPU S7, dostępność STEP 7 Professional V19 i dokładny wariant TP900 Comfort. Dobór modułów I/O nastąpi na podstawie schematu i istniejącego osprzętu.
