# Eksploracyjny odczyt MC5 z bieżącego katalogu S5D

Aktualny zakres: **42 pełne bloki**, wszystkie PB. [Szósta partia](../native_verification/WERYFIKACJA_PARTIA6.md) daje 181 nowych sieci; łącznie 21 bloków FBD ma 653 zgodne sieci. [DB15/DB19](../native_verification/DB15_DB19_NASTAWY.md) są otrzymane i odczytane. Dekoder MC5 pozostał bez zmian.

Ten katalog zawiera **listing do analizy**, nie program S7 i nie projekt TIA.
Nie wykonuje połączenia ze sterownikiem, nie wysyła instrukcji i nie zapisuje
oryginalnych archiwów. Natywne listingi STEP 5 pozwoliły porównać 27 wywołań
OB1, jego widoczne instrukcje i dwie sieci graficzne, 34 sieci FBD PB16 oraz
**1733 pozycje w 19 STL** (1732 adresowane i końcowe BE FB89 bez adresu).
Łącznie, po [piątej partii](../native_verification/WERYFIKACJA_PARTIA5.md),
to **36 pełnych bloków**. PB2/3/4/13/17/18 mają 252 sieci porównane statycznie,
a PB7/8/9/10/14/15/50/51/52 kolejne 220 sieci. W obu partiach osobno porównano
odpowiednio sześć i trzynaście adresowanych pozycji STL. PB51 i PB52 pochodzą
z jednego zachowanego pliku; zakresy źródła zapisano oddzielnie.
Część pełnych STL nadal ma 1277 instrukcji wykonawczych,
456 BLD i 121 celów skoków. Obejmuje to DB
dziewięciu instrukcji tworzenia. [Pierwsza](../native_verification/WERYFIKACJA_STEP5.md)
i [druga](../native_verification/WERYFIKACJA_PARTIA2.md) oraz
[trzecia partia](../native_verification/WERYFIKACJA_PARTIA3.md) rozdzielają zgodność
listingu, funkcje systemowe potwierdzone instrukcją CPU i ograniczenia migracji.
Pozostałe bloki wymagają porównania. Użytkownik potwierdził zgodność archiwum z maszyną; w tym
środowisku nie było porównania online.

## Odtworzenie i sprawdzenie

Wymagany jest wyłącznie Python 3 ze standardową biblioteką:

```sh
python /workspace/migration-ROLL/offline_decoder/decode_mc5.py
python /workspace/migration-ROLL/offline_decoder/test_decoder.py
```

Skrypt bierze numery, długości i przesunięcia **bieżących** bloków z
`../analysis/s5-program-blocks.csv`. Sprawdza SHA-256 każdej treści przed
odczytem. Nie szuka bloków w pozostałościach starszych wersji pliku. Zapisuje
wyłącznie nowe zestawienia i listingi w tym katalogu.

Wynik 2026-10-09: **17 testów przeszło**. Testy obejmują niezależne małe
próbki 4- i 6-bajtowych instrukcji ze stałą, KT/KZ z BCD i bazą czasu, maski
wejść/wyjść, deklaracje FB, argumenty wywołań, błędną liczbę argumentów,
ujemne skoki liczone od własnego adresu, skok w środek stałej oraz nieznany
kod. Dodatkowo sprawdzono osiem rzeczywistych wywołań FB96 z FB92 i jedyny
znany przypadek nakładania instrukcji. Nowy test porównuje dziewięć rzeczywistych
instrukcji `7805` w FB105 z adresami i celami odczytanymi z natywnego STEP 5,
sprawdza operand DB, czterobajtową długość i wyrównanie następnej instrukcji.
To kontrola czytnika i struktury,
**nie test zachowania maszyny**.

## Zakres i wyniki

| Sprawdzenie | Wynik |
|---|---:|
| Bloki OB/PB/FB w bieżącym katalogu | 49 |
| Bloki bez flagi assemblera z listingiem instrukcji | 44 |
| Bajty ich treści instrukcji, włącznie z opisami wywołań | 18 252 |
| Bajty zachowane jako nieznany kod w tych 44 blokach | 0 |
| Bloki z flagą assemblera, zachowane jako surowe dane | 5 |
| Surowe bajty ich treści po nagłówku/deklaracjach | 30 |
| Wiersze instrukcji listingu liniowego | 8 821 |
| Bezpośrednie wywołania zapisane w kodzie | 51 |
| Otwarcia DB zapisane w kodzie | 49 |
| Instrukcje tworzenia z operandem DB potwierdzonym w STEP 5 | 9 |
| Skoki względne / wsteczne | 178 / 6 |
| Cele skoków na granicy instrukcji liniowej | 177 / 178 |

Zero nieznanych kodów oznacza dopasowanie do tabeli porównawczej i zużycie
całych bajtów, a nie dowód poprawnej semantyki. Warunki wywołań, akumulatory,
VKE/RLO, flagi, timery, pośrednie adresowanie oraz stan DB nie są symulowane.

Wszystkie 51 celów bezpośrednich wywołań ma wpis w dostarczonym katalogu.
Jedynymi otwieranymi DB bez bieżącej treści archiwalnej są **DB15 i DB19**.
Zestawienie otwarć obejmuje również stałe bazowe instrukcji modyfikowanych
przez poprzedzające `B`; nie są one dowodem, że rzeczywisty cel pozostaje stały.

## Korekta potwierdzona w natywnym STEP 5

**FB105: opcode `78 05 00 xx`.** Natywny wydruk `FB105RLS.INI` z STEP 5 V7.x
pokazuje wszystkie dziewięć wystąpień jako `G DB` (angielska nazwa instrukcji;
niemiecka `E DB`). Potwierdzono cele DB15, DB19, DB41, DB51, DB205, DB210,
DB211, DB60 i DB213. Offsety bajtowe w bloku to
`003A,008C,00DC,00E6,00FA,0108,0112,0120,012A`.
Poprawiono etykietę operandu w czytniku z DX na DB i usunięto flagę
`OPCODE_7805_DB_DX_LABEL_UNVERIFIED`; nie zmieniono tabeli ani plików źródłowych
biblioteki. Zestawienie `create-candidates.csv` zachowuje upstreamowe DX w
kolumnie `reference_table_operand`, a DB w `decoded_operand`, z jawnym statusem
potwierdzenia. Szczegóły: `../native_verification/FB105-comparison.json`.
Potwierdzenie rodzaju i numeru operandu nie jest symulacją skutków instrukcji
w CPU ani dowodem poprawności całej migracji.

## Miejsca wymagające porównania z STEP 5

1. **FB51, końcówka bloku.** `2D02` pod `0416` prowadzi do `041A`, gdzie
   surowe `6500` można odczytać jako `BE`. Listing liniowy pod `0418`
   odczytuje `30406500` jako `L KH 6500`; cel jest wewnątrz tej stałej.
   Zachowano oba odczyty i ostrzeżenie. Nie ustalono, czy to zamierzona
   technika bloku standardowego, czy specjalna reprezentacja wymagająca
   natywnego narzędzia. Otrzymany wydruk FB51 i edytor STEP 5 pokazują tylko
   początkowe `JU =M001` i `BE`, co potwierdził użytkownik. Fragment nie
   rozstrzyga ciała ani końcówki i nie definiuje celu pierwszego skoku.
   [Zakres częściowy](../native_verification/FB51-partial-comparison.json).
2. **OB31 i FB240–FB243:** ustawiona flaga assemblera. Nie deklarowano
   zgodności ich treści z AWL. FB240–243 mają rozpoznane deklaracje parametrów,
   ale treść `7808 0000 6500` pozostaje surowa. `7808` nie ma w tabeli.
   Dostarczona instrukcja identyfikuje ich funkcje: OB31 restartuje monitor
   czasu cyklu, a FB240–243 wykonują konwersje BCD/binarną, mnożenie i dzielenie.
   Nie oznacza to odkodowania ciał ani potwierdzenia ich użycia w całym programie.
3. **18 instrukcji `B`:** ich działanie modyfikuje następny operand. Surowe
   `L DW0`, `T DW0` albo `A DB0` po nich nie oznacza stałego rzeczywistego
   adresu. Odtworzenie wymaga semantyki CPU i bieżącego akumulatora.
4. **Legacy porównania:** Siemens S5 `!=F` oznacza równość, `><F`
   nierówność. Nie tłumaczyć `!=F` według znaczenia `!=` w Pythonie/C.
5. **Parametry czasu:** `KT xxx.b` odczytano jako trzy cyfry BCD i numer
   bazy czasu (0:10 ms, 1:100 ms, 2:1 s, 3:10 s). Zachować surowe słowo i
   porównać z STEP 5. Domyślne wartości DB nie są bieżącymi nastawami maszyny.

## Co wnosi odczyt priorytetowych bloków

- **FB105** ma stany M240.x oraz indeks MW242. Dla czasów kopiuje DB12
  do DB15, a dla liczników DB16 do DB19, przez operand modyfikowany `B MW242`.
  Indeks startuje od 128, następnie jest zmniejszany; widoczny zakres kopii
  to DW127…DW0. `!=F` z zerem ustawia stan zakończenia. Kopia odbywa się
  etapami z powrotami `BEA`/`BEB`, nie jako jeden ciąg instrukcji w jednym
  wywołaniu. Operand dziewięciu instrukcji `E DB` potwierdzono w natywnym
  STEP 5 jak wyżej. Stałe bezpośrednio przed kolejnymi instrukcjami tworzenia
  to 131 dla 15/19, 40 dla 41, 186
  dla 51, 220 dla 205, 128 dla 210, 10 dla 211, 50 dla 60 i 10 dla 213.
  Instrukcja CPU potwierdza regułę n → DW0…DWn dla dodatniego parametru:
  DB15/19 mają zatem 132 słowa. Nowy DB jest wyzerowany; istniejący pozostaje
  bez zmiany przez samo tworzenie. Kopiowanie DW127…0 jest osobną operacją.
  [Źródła](../reference_manuals/APPLICABILITY_DB_EVIDENCE.md).
- **FB61** zapisuje `KF +25` do BS97, wykonuje OR BS120 z `KH 0008`,
  zapisuje `KF +1000` do BS126. Instrukcja CPU 942-7UB11 potwierdza nominalny
  interwał OB13 250 ms, retencję wszystkich M przy RE i opóźnienie konfiguracji
  modułów przy następnym POWER OFF/ON o 1000 ms. Użytkownik potwierdził RE
  i sprawną baterię. Maska 0008 nie ustawia bitów pełnej retencji T/Z;
  zapis BS126 nie opóźnia bieżącego startu ani każdego STOP/RUN.
  [Źródła i warunki](../CPU_S5_USTALENIA.md).
- **OB13** odwraca M3.4, następnie warunkowo wychodzi przez BEB; podobnie
  M3.5 i M3.6, na końcu M3.7. Przy wywołaniu co 250 ms jest to dzielnik
  binarny: pełne okresy M3.4/M3.5/M3.6/M3.7 wynoszą odpowiednio
  0,5/1/2/4 s, a czasy między zmianami stanu 0,25/0,5/1/2 s.
  Interwał jest potwierdzony; faza po restarcie zależy od zachowanych stanów M,
  a wykonanie może być opóźnione przez wyższe priorytety. Nazwy symboli nie
  oznaczają tutaj pełnych okresów.
- **OB21 i OB22** wywołują FB61 i ustawiają bity restartu M0.1/M0.2;
  ustawiają także M191.0 identyfikujący start panelu. Należy zachować
  różnicę między ustawieniem i skasowaniem bitu.
- **FB60** obejmuje etapy zapisane w DB60.DW10 i wymianę z DB51/205/213.
  **FB89** używa DB51.DW64, sprawdza DB205 i wywołuje FB90.
  **FB90** wyprowadza cechy receptury do M110/M111 z wybranych słów DB205.
  Dokładny interfejs danych trzeba zestawić z COMTEXT.
- **FB101** obsługuje pośrednie nastawy w DB15 i DB19: DW128 jako indeks,
  DW129 jako poprzednio wybrany indeks, DW130 jako pole bieżącej wartości.
  Sprawdza słowo `FFFF` i przełącza odczyt/edycję zależnie od zmiany indeksu.
  Nie ma tu podstaw do automatycznego uznania wszystkich wartości za BCD.
- **FB111** pobiera wybrane czasy z DB205 i uruchamia T1/T2; stała
  rezerwowa to `KT 010.2` (10 s), nie liczba binarna 8210. Wybór czasu
  zależy od stanów sekwencji. Listing nie dowodzi obsługi wszystkich
  opcjonalnych stacji.
- **FB92 → FB96:** osiem wywołań ma zgodne deklaracje E/W `INPU`, A/W
  `OUTP` i trzy słowa opisu, włącznie ze skokiem pomijającym argumenty.
  Parametry to MW37,39,…51 → DW50,…57 aktualnie otwartego DB. Nie
  przypisano tych argumentów do DB na podstawie samego adresu DW.
- **FB0** nazwany `INDIREKT` zawiera po nagłówku wyłącznie `BE`. Nazwa
  sama w sobie nie dowodzi, że posiada kod adresowania pośredniego.

## Ograniczenia tabeli źródłowej i korekty czytnika

Źródło porównawcze nie jest autorytatywną specyfikacją Siemensa. Niezależny
przegląd zidentyfikował błędy/niekompletności jego implementacji:

- Odczyt parametrów >32 bitów zwracał zero; tutaj 6-bajtowe instrukcje
  zachowują pełne 32-bitowe dane stałej.
- `PrintTimer` nie miał obsługi, a inline KT używał dziesiętnej wartości
  surowego słowa; tutaj KT/KZ mają jawny odczyt BCD i bazy.
- `TNW` ma `parlen=0` mimo maski parametru: czytnik zachowuje maskę i
  flaguje sprzeczność, zamiast zwracać zero.
- Wpis `L QB` deklaruje 14 bitów: czytnik zaokrągla do całego słowa i
  flaguje wpis, zamiast przesuwać się o jeden bajt.
- `SVW` ma pakowany parametr w bitach 4…7: znormalizowano nibble i dodano
  wymaganie porównania natywnego. Ta instrukcja nie występuje w listingu.
- KC w źródłowej implementacji miał niespójną kolejność/obsługę bajtów;
  tutaj zachowano kolejność pliku z jawnym wymaganiem porównania.
- Warianty obszaru A przy `7038` mają błędną kombinację maski i `code1`.
  Te kody nie występują w interpretowanych blokach tego projektu;
  ogólna poprawność rozszerzonego zestawu instrukcji nie została wykazana.
- KG pozostaje surową stałą z flagą nieobsługiwanej semantyki float;
  ogólne wielosłowowe argumenty wywołań też pozostają nieobsługiwane.
- Etykietę `DX` dla `7805` poprawiono w czytniku na `DB` po otrzymaniu
  natywnego wydruku FB105. Tabela i referencyjne pliki C# pozostały bez zmian.

## Pliki

- `listings/*.txt`: 49 listingów/surowych treści z przesunięciem w bloku,
  przesunięciem w S5D, hex, operandem, symbolem i flagami.
- `instructions.csv`: instrukcje z 44 bloków; sieci według markerów BLD255
  są orientacyjne, nie oznaczają potwierdzonego przypisania komentarzy.
- `direct-calls.csv`: zapisane wywołania i warunkowość.
- `db-open-references.csv`: otwarcia DB/DX i obecność w katalogu.
- `create-candidates.csv`: opcode tworzenia, operand tabeli źródłowej,
  potwierdzony operand DB, cel numeryczny i poprzednia stała; nie jest to
  potwierdzona konfiguracja CPU ani symulacja wykonania.
- `fb-parameters.csv`, `call-arguments.csv`: deklaracje FB i argumenty
  opisów wywołań, z niezależnymi offsetami.
- `jump-references.csv`, `jump-target-overlays.csv`: cele skoków i odczyt
  alternatywny w jedynym przypadku nakładania.
- `decoder-issues.csv`: 19 pozostałych jawnych flag (18 B, 1 skok).
- `block-statistics.csv`, `decoder-statistics.json`: zakres i wyniki.
- `NOTICE.md`, `LICENSE-LGPL-2.1.txt`, `reference/`: źródło i licencja.
