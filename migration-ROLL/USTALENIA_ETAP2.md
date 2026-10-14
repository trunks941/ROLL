# ROLL KS04201 — analiza instrukcji i danych, etap 2

Aktualizacja po [szóstej partii](native_verification/WERYFIKACJA_PARTIA6.md): **42 pełne bloki i wszystkie PB porównane**. [DB15/DB19](native_verification/DB15_DB19_NASTAWY.md) są kompletne. [Komplet 50 stron schematu](schematic_review/ZASILANIE_BLOKADY.md) już przeanalizowano. Wskazane niżej zakresy poprzednich partii są historyczne; aktualnie potrzebne są końcowe modele S7 i modele G1/PNOZ i sprawdzenie szczegółów połączeń.

Wznowienie: 9 października 2026. Materiał źródłowy jest zachowany bez zmian; SHA-256 wszystkich plików oryginalnych zgadza się z poprzednią inwentaryzacją. Użytkownik potwierdził zgodność kopii z maszyną, dostęp do STEP 5 i COMTEXT, posiadanie schematu i oznaczeń modułów. CPU jest zamówiony; firmware poznamy po dostawie. Podany pakiet „Advanced” przyjęto jako WinCC Advanced V19; STEP 7 Professional i docelową konfigurację urządzeń trzeba jeszcze potwierdzić.

## Co przygotowano

- Robocze listingi MC5/AWL dla bloków z bieżącego katalogu S5D, z pozycjami, surowymi bajtami i opisami symboli, w `offline_decoder/listings/`.
- Wykaz statycznych wywołań, otwarć bloków danych, instrukcji tworzenia i odwołań pośrednich. Listingi służą analizie, a nie importowi do TIA.
- Odczyt deklarowanych formatów danych z nagłówków DV i zestawienia surowych wartości domyślnych w `data_review/`.
- Zestawienie odwołań do I/O, timerów i liczników w `analysis-stage2/io-timer-counter-references.csv`.
- [Dokładny zakres eksportów STEP 5 / COMTEXT](EKSPORTY_DO_WERYFIKACJI.md), potrzebnych do porównania oraz dalszej migracji.
- [Porównanie pierwszej partii siedmiu wydruków](native_verification/WERYFIKACJA_STEP5.md): OB1, FB105, FB61, OB13, OB21, OB22 i FB101. W sześciu blokach z adresami sprawdzono 272 pozycje i 16 celów skoków; kod `7805` oznacza tworzenie DB. W OB1 potwierdzono wszystkie 27 wywołań, widoczne instrukcje i dwie sieci graficzne.
- [Druga partia](native_verification/WERYFIKACJA_PARTIA2.md): pełne FB3, FB60, FB62, FB63, FB69 i OB34 — 649 pozycji i 57 celów skoków zgodnych. Łącznie 13 pełnych bloków, w tym 12 adresowanych / 921 pozycji. FB51 jest dwuwierszowym fragmentem, zgodnie z potwierdzonym widokiem edytora.
- [Trzecia partia](native_verification/WERYFIKACJA_PARTIA3.md): FB89/90/91/92/95/96/111 — 812 pozycji STL i 48 celów skoków oraz PB16 — 34 sieci FBD porównane ręcznie. Zakres po tej partii: 21 pełnych bloków. Przygotowano mapę 120 bitów alarmowych z tekstami, kolejność bajtów kroków N1 i warunki wszystkich sieci PB16.
- [Czwarta partia — 12 października](native_verification/WERYFIKACJA_PARTIA4.md): PB2/3/4/13/17/18 — wszystkie 252 sieci zgodne, w tym parametry timerów/liczników i kolejność działań. Zakres po tej partii: 27 pełnych bloków. Dodano warunki ustawiania/resetów alarmów, 41 kodów funkcji z 14 aktywnymi wpisami, statusy PB18 i 22 wyjścia transportu/bębna. Obrót w programach 1/2 przechodzi w obrót interwałowy w wybranych fazach ociekania.
- [Piąta partia](native_verification/WERYFIKACJA_PARTIA5.md): dziewięć bloków PB7/8/9/10/14/15/50/51/52 w ośmiu plikach, 220 sieci zgodnych. **Aktualny zakres: 36 pełnych bloków.** Potwierdzono 111 bitów kroków, zezwolenia, opóźnienia 2 s i 8 s, T16=60 min, ruch BADHUB i siedem resetowanych bitów śledzenia. M74.0 jest cyklicznym poleceniem wymagającym przytrzymania K13.
- [Robocze założenia startu, taktów i nastaw w S7](ZALOZENIA_START_NASTAWY_S7.md), z propozycją rozdzielenia danych i scenariuszami przyszłej symulacji.
- [Ustalenia CPU](CPU_S5_USTALENIA.md) na podstawie dostarczonej instrukcji Edition 04 dla CPU 942-7UB11 oraz potwierdzonej przez użytkownika pozycji RE i sprawnej baterii.
- [Weryfikacja konfiguracji OP15](comtext_review/USTALENIA_COMTEXT.md) na podstawie 128-stronicowego wydruku COMTEXT: adresy nastaw, cztery ekrany, dziesięć wpisów receptury PRG, klawisze i obszary wymiany.

44 zwykłe bloki OB/PB/FB obejmują 18 252 bajty ciał instrukcji; czytnik przypisał wszystkie te bajty do rozpoznanych instrukcji i danych wywołań. Pozostałych 5 bloków ma flagę assemblera i zachowano je jako surowe dane: OB31, FB240–FB243. Ich ciała po deklaracjach FB obejmują 30 bajtów. Odczyt zawiera 51 statycznych wywołań i 178 skoków. To pokrycie bajtów i kontrola struktury, nie potwierdzenie semantycznej równoważności przez STEP 5.

Przeszło 17 kontroli czytnika, obejmujących długości instrukcji ze stałymi, maski I/O, formaty KT/KZ, deklaracje i argumenty FB, ujemne skoki oraz zachowanie nieznanego kodu. Sprawdzono osiem wywołań FB96 w dostarczonym programie, granice skoków oraz dziewięć instrukcji tworzenia DB w FB105 względem natywnego wydruku. Kontrole nie uruchamiają logiki maszyny.

## Uruchomienie i inicjalizacja

OB1 zaczyna od `UN M0.4` i warunkowego wywołania FB105. M0.4 jest w symbolach opisany jako stała logiczna 1. Dopóki nie jest ustawiony, OB1 może zakończyć się przed logiką procesu. FB105 używa etapów w M240.x, a przy końcu ustawia M0.4 i zeruje M0.3. To wskazuje na inicjalizację rozłożoną na kolejne obiegi, którą trzeba odróżnić od zwykłego ponownego uruchomienia CPU.

W odczycie FB105:

- przed instrukcjami tworzenia DB15/DB19 ładowany jest parametr 131, który oznacza 132 słowa danych DW0…DW131;
- MW242 otrzymuje 128, jest zmniejszany o 1 i służy jako indeks przy kopiowaniu DW z DB12 → DB15 oraz DB16 → DB19;
- pętla kopiowania obejmuje indeksy 127…0, a nie cały archiwalny blok z końcowymi polami;
- dalsze obszary tworzenia mają numery 41, 51, 205, 210, 211, 60 i 213, z dodatkowymi ustawieniami komunikacji;
- blok trzykrotnie wywołuje systemowy OB31, restartujący monitor czasu cyklu podczas inicjalizacji (instrukcja PDF 404 / drukowana 11-32).

Natywny wydruk FB105 rozstrzygnął instrukcje `78 05`: angielskie `G DB`, czyli niemieckie `E DB`, we wszystkich dziewięciu wystąpieniach. Operand DX w zewnętrznej tabeli był błędny; poprawiono pomocniczy czytnik, zachowując tabelę źródłową. Porównanie potwierdziło także wszystkie pozostałe pozycje FB105. Instrukcja CPU potwierdza, że przy dodatnim parametrze istniejący DB pozostaje bez zmiany; nowy DB jest wyzerowany, a parametr n odpowiada DW0…DWn (PDF 233–234 / drukowane 8-35–8-36). Osobne kopiowanie w FB105 może nadpisać dane, jeżeli program wejdzie w tę ścieżkę. Propozycja dla S7 to jawne, statycznie zadeklarowane DB oraz odtworzona inicjalizacja z ustalonymi regułami retencji; bieżące nastawy trzeba pobrać osobno.

Natywne OB21 i OB22 potwierdziły identyczne ciała instrukcji: wywołują FB61, ustawiają znaczniki restartu M0.1/M0.2 oraz M191.0 dotyczący startu panelu. Nie zerują tutaj M0.4, etapów inicjalizacji, taktów ani nastaw. Nie należy zastępować tych działań ogólnym wyzerowaniem pamięci. Na poziomie docelowego projektu trzeba rozdzielić stan inicjalizacji, dane operatora, stany sekwencji i sygnały restartu.

## Takty i ustawienia CPU

Natywny FB61 potwierdził zapis 25 do BS97, ustawienie maski `0008` w BS120 i zapis 1000 do BS126 (angielskie oznaczenie obszaru: RS). Dostarczona instrukcja dla **6ES5 942-7UB11** potwierdza: nominalny interwał OB13 250 ms, retencję wszystkich M przy RE oraz opóźnienie sprawdzenia konfiguracji modułów o 1000 ms przy następnym POWER OFF → POWER ON. Ostatni zapis nie opóźnia bieżącego OB startowego ani każdego STOP → RUN. Użytkownik potwierdził RE i sprawną baterię. Bity pełnej retencji timerów i liczników nie są ustawiane przez maskę 0008; ich bieżące wartości pozostają nieznane. [Źródła i warunki](CPU_S5_USTALENIA.md). Numery tych obszarów nie przechodzą do programu S7.

Natywny OB13 potwierdził wzorzec: odwróć M3.4, zakończ warunkowo; następnie tak samo M3.5 i M3.6, a na końcu odwróć M3.7. Jest to dzielnik taktów. **Dla potwierdzonego interwału 250 ms nominalne czasy wynoszą**:

| Bit | Czas pomiędzy zmianami stanu | Pełny okres sygnału |
|---|---:|---:|
| M3.4 | 250 ms | 500 ms |
| M3.5 | 500 ms | 1 s |
| M3.6 | 1 s | 2 s |
| M3.7 | 2 s | 4 s |

Nazwy symboli opisują takty, a nie jednoznacznie pełny okres. W S7 trzeba zachować wykorzystywane zbocza, fazę oraz stan po restarcie; błędne przyjęcie nazw jako okresów może podwoić lub skrócić czas działania.

## Nastawy czasu i liczników

Nagłówek DV12 opisuje regiony KT/KH, a DV16 deklaruje słowa KH. Deklarowany format wyświetlania nie przesądza o interpretacji podczas wykonania instrukcji. W DB12 jest 131 słów, w tym 99 `FFFF`. W DB16 jest 132 słowa, w tym 126 `FFFF`. Nie należy zamieniać `FFFF` na zwykłą nastawę liczbową.

FB101 otwiera osobno DB15 i DB19. W obu korzysta z:

| Pole źródłowe | Znaczenie wynikające z odczytanego przepływu |
|---|---|
| DW0…DW127 | Indeksowane wartości parametrów |
| DW128 | Wybrany numer parametru |
| DW129 | Zapamiętany poprzedni wybór |
| DW130 | Bufor wartości pokazywanej/edytowanej |

Natywny FB101 potwierdził pomijanie wpisów `FFFF`, wczytanie bufora po zmianie wyboru i cykliczny zapis bufora do indeksowanej wartości przy tym samym wyborze. Nie ma osobnego sygnału zatwierdzania w tym bloku. Zatem DW128–130 w roboczych DB nie są trzema kolejnymi nastawami procesu. Potwierdzono asymetrię korekty indeksu ≥128: dla czasów zerowane jest DW128 i pomijana dalsza obsługa, dla liczników zerowane jest wyłącznie MW240 i obsługa kontynuuje na wpisie 0. Brakuje jawnej kontroli dolnej granicy signed oraz poprawności KT/BCD; COMTEXT potwierdza limit numerów 0…128, podczas gdy pomoc podaje 0…127; zatwierdzanie wszystkich pól nadal wymaga porównania obecnej obsługi. MW240 współdzieli adresy M240.x z etapami FB105, co w S7 proponuje się rozdzielić.

Przy tłumaczeniu porównań należy zachować starą notację S5: `!=F` oznacza porównanie równości, natomiast `><F` nierówność. Znaków `!=` nie można interpretować tak jak operatora nierówności w nowoczesnych językach.

## Receptura i program czyszczenia

Natywne FB89/FB90/FB111 potwierdziły nagłówek DB205, odbiór skrzynki i wszystkich dziesięć odbiorców PRG, zgodnych z COMTEXT. Potwierdzenie odbioru nie oznacza poprawności programu; walidacja starych bloków nie obejmuje wszystkich kodów KT/BCD. Ciało FB51 i pełny format protokołu pozostają niezweryfikowane.

| Dane źródłowe | Funkcja w odczycie kodu |
|---|---|
| Starszy bajt DW0 | Sprawdzenie identyfikatora receptury równego 1 |
| Młodszy bajt DW0 | Numer zestawu danych sprawdzany w zakresie 1…99 |
| DW5, DW17, DW25, DW33 | Czasy przebywania w stacjach 1…4; część wyboru stacji w FB90 i nastaw T1 w FB111 |
| DW9, DW21, DW29 | Czasy ociekania stacji 1…3 przekazywane do T2 |
| DW13 | Porównanie z 1 włącza ultradźwięki stacji 1 |
| DW37 | Tryb ruchu: 1 obrót, 2 kołysanie, 3 obrót interwałowy, 4 obrót/kołysanie |
| DW41 | Porównanie z 1 włącza funkcję opisaną jako BADHUB |

Kod FB89 wymaga zestawu danych 1…99, więc nie należy ograniczać programu wyłącznie według starego komentarza mówiącego o 10 zestawach. Nie jest to dowód, że wszystkie 99 zestawów zapisano w panelu.

Transfer ma stany rozpoczęcia, zakończenia, potwierdzenia i błędu, a także kontrolę czasu. Docelowy interfejs TP900 powinien odtwarzać wynikowe funkcje, zamiast przenosić stare słowa protokołu bez opisania ich znaczenia. Stanowisko HMI, aktualna receptura i bufor nowej receptury powinny być rozdzielone, z przełączeniem po zakończeniu i walidacji transferu. To propozycja projektu do sprawdzenia wobec obecnego sposobu obsługi.

FB60 przygotowuje w DB213 żądanie: DW1 otrzymuje `KY 0,70`, DW2 liczbę 1, DW3 wybrany numer programu. DB51.DW60/61 wskazują na DB213 i jego DW1. W tym przepływie PLC przygotowuje żądanie do panelu; wcześniejszy opis DB213 wyłącznie jako zleceń OP15 → PLC, oparty na komentarzu symbolu, został skorygowany. Kod polecenia 70 i funkcję jego parametrów trzeba porównać z dokumentacją COMTEXT/protokołu.

Natywne FB60/89/90/111 potwierdziły żądanie, odpowiedzi i odbiorców receptury. T101 ma 5 s w oczekiwaniu na wynik; T100 osobno nadzoruje fazę trwającego transferu przed końcem. Potwierdzenie skrzynki i poprawność programu są odrębne. FB3 i PB16 potwierdziły stany K13/K16, wspólne zbocze, gałęzie ruchów i zatrzaski. PB15 doprecyzował M74.0: wymaga przytrzymania K13 i nie jest samodzielnym zatrzaskiem; wcześniejszy PB16 odczytuje poprzednią wartość. PB17 potwierdził odrębne podtrzymania wyjść. Zerowanie klawiszy w późniejszym FB3 nie dowodzi natychmiastowego wyłączenia wszystkich ruchów. Szczegóły są w piątej partii.

**Zapisane słowa DB205 nie potwierdzają poprawnej aktualnej receptury.** W archiwalnym buforze DW13=`2020`, DW37=`2150`, DW41=`0002`, podczas gdy odczytane warunki używają odpowiednio wartości 1, trybów 1…4 i wartości 1. Tych słów nie należy automatycznie uznać za aktualny program operatora ani przeliczać wszystkich jako czasy. Potrzebne są aktywne zestawy danych OP15 i ich definicja z COMTEXT. Zgodność programu z maszyną, potwierdzona przez użytkownika, nie rozstrzyga interpretacji każdej archiwalnej zawartości bufora.

Obsługa ręczna zawiera także warunki reagujące na utrzymany stan klawisza, m.in. powiązania M190.6 z poleceniami w PB16. Dlatego przy zamianie klawiatury OP15 na ekran dotykowy nie można jednolicie zamienić wszystkich przycisków na krótkie impulsy. Dla każdego ruchu trzeba ustalić funkcję klawisza, zezwolenia, czas utrzymania polecenia i zachowanie po utracie łączności.

## I/O i ograniczenia odczytu

W statycznych odwołaniach odczytanych zwykłych bloków występuje 97 różnych bitów E, 63 bity A, 75 timerów i 3 liczniki. Wszystkie mają symbole. E6.6 — opisany jako minimum zbiornika wody VE — nie ma bezpośredniego odwołania w tych listingach. Nie wynika z tego, że kanał jest fizycznie zbędny: znaczenie trzeba potwierdzić w schemacie i weryfikacji programu.

FB0 i FB240–FB243 nie mają znalezionych statycznych wywołań w zwykłych listingach. Pozostają w inwentaryzacji; nie usunięto ich ani nie uznano za na pewno nieużywane. Instrukcja identyfikuje funkcje integralnych FB240–FB243: BCD → liczba binarna, liczba binarna → BCD, mnożenie i dzielenie (PDF 373–376 / drukowane 11-1–11-4). Surowych ciał assemblerowych nie odkodowano; zastosowanie i odpowiedniki trzeba ocenić w kontekście całego programu.

Dwa konkretne ograniczenia:

1. W FB51 skok z pozycji `0x0416` wskazuje `0x041A`, czyli słowo rozpoznawane jako BE, które jest jednocześnie częścią argumentu poprzedniej instrukcji w liniowym odczycie. Zachowano obie interpretacje. Otrzymany wydruk i edytor pokazują jedynie początkowe `JU =M001` i `BE`, więc nie rozstrzygają końcówki. Nie ustalono przyczyny ograniczonego widoku; sama nietypowa struktura nie dowodzi błędu działającego programu.
2. Tworzenie DB i kopiowanie wartości domyślnych w FB105 są już potwierdzone przez STEP 5 i instrukcję CPU. Przy RE, sprawnej baterii i uprzednio wykonanym FB61 zwykły restart zachowuje wszystkie M, w tym M0.4, a OB1 pomija FB105. Podtrzymanie danych RAM nie wynika z przełącznika RE/NR. Nadal brak aktualnych wartości roboczych DB, wartości bitów retencji T/Z i typu modułu pamięci. Po Overall Reset wszystkie M/T/Z są zerowane; nie należy utożsamiać tej operacji ze zwykłym restartem.

Kontrole parsera nie zastępują kompilacji, porównania STEP 5 ani testów maszyny. O15 nie został odkodowany jako pełny aktywny projekt HMI, lecz dostarczony wydruk COMTEXT pozwolił odczytać konfigurację pól, klawiszy, receptury i obszarów wymiany. Otrzymano [potwierdzone zestawy wartości programów 1 i 2](operator_recipes/RECEPTURY_OPERATORA.md), po dziesięć pól każdy. Czasy są w sekundach; oba programy mają obrót bębna i wyłączony ruch pionowy. Dostępność innych programów na panelu pozostaje do ustalenia. Instrukcję S5 odczytano lokalnie i potwierdzono znaczenie użytych słów systemowych. Zgodność docelowej konfiguracji S7 z rzeczywistym firmware pozostaje do sprawdzenia po dostawie CPU.

## Następny krok

Porównano **42 pełne bloki**, otrzymane DB15/DB19 i komplet 50 stron schematu. [Szósta partia](native_verification/WERYFIKACJA_PARTIA6.md) domknęła wszystkie PB. Następny materiał: końcowe modele S7 i modele G1/PNOZ i sprawdzenie szczegółów połączeń. FB0 pozostaje bez natywnego wydruku, FB51 częściowy. [Lista braków](native_verification/BRAKUJACE_BLOKI_STEP5.md).
