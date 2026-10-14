# Instrukcja S5-115U: zakres CPU, tworzenie DB i zachowanie pamięci

Źródło: dostarczony przez użytkownika `6ES5_998-0UF23.pdf`. Odczyt tekstu PDF oraz kontrola obrazu stron PDF 233–234. Numer strony PDF jest liczony od 1; numer drukowany znajduje się w stopce instrukcji.

## Zgodność instrukcji z CPU

| Ustalenie | Dowód |
|---|---|
| Tytuł: *SIMATIC S5, S5-115U Programmable Controller, Manual*. | Strona PDF 1, okładka. |
| Okładka obejmuje `CPU 942-7UB11`, a także CPU 941-7UB11, CPU 943-7UB11/7UB21 i CPU 944-7UB11/7UB21. | Strona PDF 1. |
| Dokładny MLFB użytkownika, `6ES5 942-7UB11`, jest podany w specyfikacji CPU 942. | Strona PDF 543, drukowana 15-15, §15.2.3: „Central Processing Unit CPU 942 (6ES5 942-7UB11)”. |
| Wydanie 04; oznaczenie dokumentu na okładce i większości stopek: `EWA4NEB8116130-02b`. | Strona PDF 1; np. PDF 233, drukowana 8-35. |
| Prawa autorskie © Siemens AG 1991. | PDF 2; na tej stronie występuje odmienne oznaczenie `EWA4NEB8126130-02b`. Nie utożsamiać samego roku copyright z pewną datą wydania. |

Instrukcja obejmuje dokładny model starej CPU. Zasady opisane wyłącznie dla CPU 943/944 należy oddzielić od zachowania CPU 942.

## `G DB` / niemieckie `E DB`

W instrukcji angielskiej operacja utworzenia DB nosi nazwę `G DB`. Niemiecki wydruk STEP 5 i poprawiony czytnik używają `E DB`; natywne porównanie FB105 potwierdziło dziewięć takich operacji w programie. `G DB` nie otwiera DB do dalszych operacji: do tego służy `C DB` (niemieckie `A DB`).

| Zachowanie | Cytat / odwołanie |
|---|---|
| Utworzenie nowego bloku. | PDF 233, drukowana 8-35: „The ‘G DB x’ statement does not call a data block. Instead, it generates a new block.” |
| Istniejący DB nie zostaje ponownie utworzony ani przeskalowany. | PDF 233, 8-35: „If an already existing data block is to be set up, the statement G DBx will have no effect!” Dotyczy to istniejącego DB niezależnie od żądanej nowej długości; instrukcja nie podaje wyjątku dla krótszego DB. |
| Nowy DB jest w RAM i jego słowa są wyzerowane. | PDF 234, 8-36, przykład `L KF +127; G DB 5`: „Data block 5 is generated with a length of 128 data words (0000) in the RAM of the PC and entered in the block address list.” |
| Długość w dodatnim parametrze to najwyższy indeks DW, a nie liczba słów z nagłówkiem. | Ten sam przykład `+127` tworzy **128 słów danych**. Parametr `n > 0` odpowiada zatem zakresowi DW0…DWn. Kontrola obrazu PDF 234 potwierdza `+127`, `128 data words` i `(0000)`. |
| Parametr zero usuwa DB z listy adresowej. | PDF 233, 8-35, oraz PDF 234, 8-36, przykład `L KF +0; G DB 5`. **Zero jest poleceniem usunięcia, a nie utworzeniem DW0.** Fizycznie pozostaje blok „dead” do kompresji pamięci. |
| Brak wystarczającej pamięci. | PDF 233, 8-35: „If the DB to be set up is longer than the available memory, the CPU goes to STOP with ‘TRAF’ or jumps to the relevant error response OB.” |
| Miejsce bloków tworzonych w programie. | PDF 119, drukowana 4-5, §4.2.2, „Special Points When Setting Up Data Blocks”: „Data blocks generated in the control program with the ‘G DB’ operation are automatically dumped by the operating system direct in internal program memory.” |

W §8-35 opis słowny mówi ogólnie o wskazaniu liczby słów w ACCUM 1; konkretny przykład na następnej stronie jednoznacznie pokazuje przesunięcie o jeden. Dlatego do obliczeń należy użyć przykładu `+127 → 128`, bez włączania nagłówka bloku.

### Długości wynikające z FB105

| DB | Parametr `L KF` przed utworzeniem | Słowa danych nowo tworzonego DB | Zakres DW | Słowa w archiwalnym DB |
|---|---:|---:|---|---:|
| 15 | +131 | 132 | 0…131 | brak DB15 w archiwum |
| 19 | +131 | 132 | 0…131 | brak DB19 w archiwum |
| 41 | +40 | 41 | 0…40 | 41 |
| 51 | +186 | 187 | 0…186 | 187 |
| 205 | +220 | 221 | 0…220 | 221 |
| 210 | +128 | 129 | 0…128 | 129 |
| 211 | +10 | 11 | 0…10 | 11 |
| 60 | +50 | 51 | 0…50 | 51 |
| 213 | +10 | 11 | 0…10 | 11 |

Parametry: `native_verification/FB105-created-DBs.csv`; długości archiwalne: `analysis/s5-program-blocks.csv`. Siedem istniejących archiwalnych DB ma długości dokładnie zgodne z regułą `parametr + 1`; to dodatkowa kontrola, a nie osobny dowód zachowania CPU.

FB105 kopiuje tylko DW127…DW0 z DB12 do DB15 i z DB16 do DB19. Pola DW128…DW130 służą do edycji, a DW131 pozostaje poza tym kopiowaniem. Nowo utworzony DB ma zero w tych polach dzięki `G DB`; istniejący DB nie zostaje wyzerowany przez samą tę instrukcję. **Późniejsze operacje kopiowania w FB105 mogą nadpisać wartości istniejącego DB**, jeśli program wejdzie w ich ścieżkę. Brak działania `G DB` nie stanowi dowodu, że cała inicjalizacja jest pomijana po restarcie.

## CPU 942: RAM, E(E)PROM i bateria

| Ustalenie | Odwołanie |
|---|---|
| CPU 941/942 wykonują program bezpośrednio z modułu pamięci, gdy jest tam zapisany. CPU 943/944 kopiują go do wewnętrznego RAM. | PDF 117, drukowana 4-3, §4.2.2; również uwaga pod rys. 2-9, PDF 48, drukowana 2-18. |
| DB umieszczone na E(E)PROM CPU 941/942 nie mogą być modyfikowane przez program sterowania. Zmieniane DB należy wgrać bezpośrednio do pamięci CPU albo utworzyć operacją `G DB`. | PDF 119, 4-5, „Special Points When Setting Up Data Blocks”. |
| RAM (wewnętrzny lub moduł RAM) traci zawartość po zaniku zasilania bez podtrzymania baterią. | PDF 34, drukowana 2-4, „Program Memory”: „When the power fails and there is no battery, the memory contents are lost.” |
| Bateria podtrzymuje program i dane po wyłączeniu S5-115U. | PDF 58, drukowana 2-28, §2.7.1: „The backup battery maintains the program and data when the S5-115U is switched off.” |
| Kasowanie ogólne zeruje wewnętrzną pamięć programu oraz moduł RAM w CPU 941/942. | PDF 116, drukowana 4-2, §4.2.1. To odrębna operacja od zwykłego STOP/RUN. |

Nie stosować do CPU 942 opisanego dla CPU 943/944 mechanizmu automatycznego ładowania „starych” DB z E(E)PROM do RAM po każdym POWER ON. Instrukcja rozróżnia te rodziny wprost.

Sam numer CPU i plik programu nie określają faktycznego typu modułu pamięci, stanu baterii ani położenia przełącznika RE/NR w maszynie. **Użytkownik dodatkowo potwierdził położenie przełącznika RE oraz sprawną baterię podtrzymania.** Jest to informacja o maszynie podana przez użytkownika, odrębna od dowodów z instrukcji. Typ modułu pamięci pozostaje nieustalony.

## STOP, restart i OB systemowe

* PDF 44, drukowana 2-14, §2.5.1: w STOP zachowane są bieżące wartości timerów, liczników, znaczników i obrazów procesu; program nie jest wykonywany, a wyjścia są wyłączone sygnałem BASP. Nie jest to jeszcze reguła przejścia z STOP do RUN.
* PDF 48, drukowana 2-18, rys. 2-9: podczas procedury startu kasowany jest obraz wejść/wyjść oraz **nieretencyjne** timery, liczniki i znaczniki; wyjścia pozostają wyłączone. Następuje odpowiedni OB startowy, zwolnienie BASP i cykl OB1. Rysunek nie wymienia kasowania DB jako składnika zwykłego restartu.
* PDF 188, drukowana 7-18, §7.4.1: **OB21** jest wywoływany przy ręcznym restarcie STOP→RUN; **OB22** przy automatycznym starcie po przywróceniu zasilania, gdy CPU wcześniej była w RUN. Wykonują się przed cyklicznym programem OB1, jeśli zostały zaprogramowane.
* PDF 46, drukowana 2-16: w RESTART obraz wejść nie jest jeszcze odświeżony; wejścia wymagają bezpośredniego dostępu peryferyjnego. Timery są przetwarzane. OB przerwań/czasowe stają się aktywne po OB startowym, chyba że w nim jawnie włączono je instrukcją `RA`.
* PDF 404, drukowana 11-32, §11.2.1: **OB31 jest funkcją systemową wyzwalającą ponownie kontrolę czasu cyklu**. Cytat: „The scan time monitor can be started at any point in the control program using the OB31 call (JU OB31), i.e. the scan monitoring time is restarted.” Nie jest zwykłym pustym blokiem użytkownika. W migracji jego wywołania trzeba odnieść do monitorowania czasu cyklu S7.

Retencja M0.4 użytego do sterowania FB105 powoduje pominięcie inicjalizacji w OB1 po zwykłym restarcie. Potwierdzone przez użytkownika RE i sprawna bateria oraz wcześniejsze wykonanie FB61 z ustawieniem bitu 3 BS120 uzasadniają ten wniosek; badane OB21/OB22 nie zerują M0.4. Samo `G DB` tego nie rozstrzyga. [Szczegółowe bity BS120 i znaczenie BS97/BS126](SYSTEM_START_EVIDENCE.md). **Przełącznik RE/NR dotyczy timerów, liczników i znaczników; podtrzymanie bloków danych w RAM wynika z baterii, a nie z tego przełącznika.** Kasowanie ogólne usuwa również program i DB w RAM.

## Granice ustaleń

Instrukcja pozwala już ustalić zachowanie `G DB`, właściwe długości nowo tworzonych DB oraz zależność RAM od baterii. RE i sprawność baterii potwierdził użytkownik. Nadal nie znamy typu modułu pamięci ani zawartości żywych DB15/DB19; nie wykonano prób restartu ani żadnych operacji na sterowniku. Zwykły restart z zachowanym RAM należy odróżnić od kasowania ogólnego, utraty podtrzymania i ponownego wgrania programu.
