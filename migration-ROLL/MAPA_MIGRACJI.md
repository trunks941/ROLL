# ROLL KS04201 — pierwsza mapa migracji S5 → S7-1513 / TP900

Cel: CPU S7-1513-1 PN `6ES7513-1AM03-0AB0`, TIA Portal V19, panel TP900 rozważany przed zakupem.

Stan: zakończona inwentaryzacja archiwów, symboli i katalogu bloków. Nie powstał jeszcze projekt TIA ani program sprawdzony przez kompilację lub symulację. Mapa opisuje materiał źródłowy i proponowaną realizację.

Aktualizacja 13 października: porównano 42 pełne bloki, komplet DB15/DB19 i **50 stron schematu**. [Sprzęt ze zdjęcia](hardware_review/SPRZET_ZE_ZDJECIA.md): 4 moduły DI32, 2 moduły DQ32/0,5 A oraz DQ16/2 A, razem 128 DI i 80 DQ. Użytkownik potwierdził, że to całość. [Mapa 208 kanałów](schematic_review/channel-wire-map-draft.csv) obejmuje zaciski narysowane dla S5 i powiązania z obwodami mocy; docelowe zaciski S7, MLFB i sprawdzone przewody pozostają do ustalenia. [Zasilanie i blokady](schematic_review/ZASILANIE_BLOKADY.md) dokumentują G1 24 V/30 A, PNOZ, niezależne odcięcia grzania i zewnętrzne regulatory. Wentylator pozostaje na %Q24.4, lampka na %Q16.0. Odwołania E119…E125/A112…A113 nie dostały przypisania do dodatkowych fizycznych modułów.

Aktualizacja z 9 października 2026: dodatkowy odczyt instrukcji i danych jest opisany w [ustaleniach etapu 2](USTALENIA_ETAP2.md). Przygotowano robocze listingi zwykłych bloków MC5 i sprawdzono czytnik. Otrzymane wydruki STEP 5 pozwoliły już [porównać siedem bloków startu, inicjalizacji i nastaw](native_verification/WERYFIKACJA_STEP5.md); pozostałe bloki wymagają porównania. Przygotowano [założenia odpowiadającej im części S7](ZALOZENIA_START_NASTAWY_S7.md). Dokładny zakres następnych materiałów opisano w [instrukcji eksportów](EKSPORTY_DO_WERYFIKACJI.md).

## Materiały i wiarygodność odczytu

Użytkownik potwierdził zgodność kopii z działającą maszyną oraz dostęp do STEP 5 i COMTEXT. Jest to informacja użytkownika; w tym środowisku nie wykonano porównania online ze sterownikiem.

- `s5.zip`: 9 plików projektu, w tym `04201@ST.S5D` i tekstowa tabela symboli `04201@Z0.SEQ`. Folder nosi datę `1998_07_03`; historia w symbolach obejmuje zmianę z 30.06.1998 dotyczącą mieszanego obracania/kołysania bębna.
- `OP15.zip`: plik `04201.O15`, projekt obsługiwany przez COMTEXT według użytkownika. W nagłówku występuje `V3_10` oraz opis `GL 05.05.98 ... CH-ROHRBOGEN 04201 ...`. Znacznik w pliku nie potwierdza wersji aktualnie zainstalowanego COMTEXT.
- Oba ZIP-y przeszły sprawdzenie CRC. Sumy SHA-256 wszystkich rozpakowanych plików zapisano w `analysis/inventory.json`. Oryginały zachowano w `originals/` i nie modyfikowano.
- Katalog S5 odczytano przez wskaźniki sekcji i wpisów bloków; sprawdzono typ, numer i długość wszystkich 63 bloków programu/danych w odniesieniu do ich nagłówków. Dla OB/PB/FB/DB potwierdzono także kompletność łańcuchów wpisów katalogu. Starsze treści bloków obecne poza tymi wpisami nie są traktowane jako bieżące.
- Odczytano też 922 rekordy komentarzy, razem z tytułami komentarzy DB. Powiązanie komentarza z konkretną instrukcją wymaga pełnego listingu AWL. Sekcja pomocnicza typu `0x20` pozostaje nieodkodowana; nie jest zaliczona do 63 bloków programu/danych.

Odczyt katalogu nie dowodzi poprawności wykonania programu. Nie wykonano pełnej dekompilacji MC5 ani odczytu struktury pól, receptur i połączeń COMTEXT.

## Inwentaryzacja programu

| Rodzaj | Liczba | Numery w katalogu pliku |
|---|---:|---|
| OB | 6 | 1, 13, 21, 22, 31, 34 |
| PB | 22 | 2, 3, 4, 7, 8, 9, 10, 13, 14, 15, 16, 17, 18, 19, 20, 21, 23, 24, 25, 50, 51, 52 |
| FB | 21 | 0, 3, 51, 60, 61, 62, 63, 69, 89, 90, 91, 92, 95, 96, 101, 105, 111, 240, 241, 242, 243 |
| DB | 14 | 0, 1, 12, 16, 41, 50, 51, 60, 205, 206, 210, 211, 213, 219 |

Tabela symboli ma 1254 wpisy: 98 E, 63 A, 866 M, 39 MB, 50 MW, 75 T, 3 Z oraz 60 wpisów nazw bloków. Nie stwierdzono powtórzonych operandów ani nieodczytanych wierszy deklaracji symboli.

**98 wejść i 63 wyjścia to liczby opisanych adresów, a nie potwierdzona liczba wymaganych kanałów.** W komentarzach występują opcjonalne dodatkowe stacje i automatyczne podawanie. Trzeba zestawić użycie w kodzie z istniejącymi modułami i schematem.

Symbole DB15 i DB19 istnieją, ale ich treści nie ma w bieżących wpisach katalogu archiwum. Natywny FB105 potwierdził tworzenie DB dla zmiennych czasów i liczników oraz kopiowanie DW127…0 z DB12/DB16. Nie należy brać starszego ciała DB19 z pozostałości pliku ani utożsamiać wartości domyślnych DB12/DB16 z aktualnymi nastawami.

FB0 oraz DB0, DB1, DB50 i DB219 nie mają deklaracji w dostarczonej tabeli symboli. Wymagają opisania na podstawie kodu/konfiguracji. DB0 i DB1 trzeba rozpatrzyć także pod kątem ich specjalnej roli w S5.

## Mapa funkcji PLC

Nazwy funkcji wynikają z niemieckich komentarzy i symboli. Dobór końcowej struktury FC/FB/DB nastąpi po analizie instrukcji.

| Element S5 | Rola widoczna w dokumentacji | Proponowana realizacja S7-1500 |
|---|---|---|
| OB1 | Program cykliczny | OB cykliczny z zachowaniem kolejności obliczeń, blokad i aktualizacji wyjść |
| OB13 + FB61 | Generacja taktów i ustawienie okresu | OB przerwania cyklicznego, z ustalonym okresem i priorytetem |
| OB21, OB22 | Uruchomienie po STOP i zaniku zasilania | OB startowy; jawne reguły inicjalizacji oraz retencji |
| OB31 | Systemowy restart monitora czasu cyklu | Dobór podziału inicjalizacji i limitu czasu cyklu S7 z uwzględnieniem wywołań w FB105 |
| OB34 | Wykrycie awarii baterii | Zastąpienie diagnostyką nowego CPU według potrzeb maszyny; numeru OB nie przenosić mechanicznie |
| PB2 | Alarmy i znaczniki usterek | Logika alarmów z zachowaniem warunków, opóźnień, blokad i kasowania |
| PB3, PB4, PB16 | Tryb ręczny | Osobna logika poleceń, zezwoleń i potwierdzeń |
| PB7–PB10, PB14, PB15, PB18 | Pozycje bazowe, nadzór i sekwencje | FC/FB sekwencji; zachowanie przejść kroków i warunków ponownego startu |
| PB13 | Mechanizm bębna | Odtworzenie obrotu, kołysania, kierunku i hamowania |
| PB17, PB23 | Sterowanie wyjściami transportu/procesu | Oddzielona warstwa wyjść z zachowaniem blokad i priorytetów poleceń |
| PB19–PB21, PB24 | Grzanie, proces, stacje, separator oleju | FC/FB procesowe, zgodne z aktualnym wyposażeniem |
| PB25 | Lampki | Wyjścia sygnalizacji i statusy dla HMI |
| PB50–PB52, FB69, FB101, FB111 | Czasy, liczniki i ich nastawy | Typowane parametry oraz odpowiednio dobrane timery/liczniki; weryfikacja baz czasowych i zboczy |
| FB240–FB243 | BCD ↔ liczba całkowita, mnożenie, dzielenie | Funkcje/operatory S7; testy zakresów, znaków, przepełnienia i dzielenia przez zero |
| FB105 | Tworzenie i inicjalizacja DB | Statycznie zadeklarowane DB z kontrolowaną inicjalizacją i retencją |
| FB0 | Brak opisu w symbolach | Rozpoznanie treści i wywołań przed decyzją o migracji |

**Okres i retencja:** DB1 zawiera tekst `DB1 TFB: OB13 100 ; SDP: WD 500 ; END`, lecz FB61 wywoływany przez OB21/OB22 nadpisuje interwał OB13 na **250 ms**. Dostarczona instrukcja CPU 942-7UB11 potwierdza także retencję wszystkich M przy RS120 OR0008 i pozycji RE oraz działanie RS126=1000 dopiero przy następnym cyklu zasilania, przed sprawdzeniem konfiguracji modułów. Użytkownik potwierdził RE i sprawną baterię. Zwykły restart zachowuje M0.4 i nastawy RAM; Overall Reset kasuje M/T/Z. Maska 0008 nie ustawia pełnej retencji timerów ani liczników. [Dokładne warunki i strony instrukcji](CPU_S5_USTALENIA.md).

W nagłówkach OB31 oraz FB240–FB243 występuje bit oznaczany przez analizowany czytnik jako tryb assemblera; ich surowe ciała nie zostały odkodowane. Instrukcja identyfikuje OB31 jako restart monitora cyklu, a FB240–FB243 jako konwersje BCD/binarną, mnożenie i dzielenie. Dobór odpowiedników wymaga zachowania semantyki i oceny zastosowania w całym programie. FB61 zawiera odwołania do obszaru BS — potwierdzone ustawienia systemowe S5 należy odwzorować przez konfigurację S7.

`analysis/ob1-call-sequence.csv` zawiera 27 zapisanych wywołań w kolejności OB1, wraz z surowym kodem i pozycją w bloku. To kolejność statyczna; wywołania SPB i wcześniejsze warunki wpływają na faktyczne wykonanie. Analiza wykorzystuje układ instrukcji tego konkretnego OB1, a nie ogólny dekompilator MC5.

## PLC ↔ panel

[Czwarta partia](native_verification/WERYFIKACJA_PARTIA4.md) uzupełniła wcześniejsze porównania panelu: PB2/3/4/13/17/18 — 252 zgodne sieci, źródła/reset alarmów, wybór funkcji, bęben, wyjścia i wskazania pozycji. Funkcje HMI mają 41 kodów, z czego 14 jest aktywnych w COMTEXT. Wskazania nie zawsze są sprzężeniem z czujnika. Wybrany obrót obejmuje obrót interwałowy w wybranych fazach ociekania. FB51 pozostaje fragmentem, a pozostały automat i proces wymagają dalszych listingów.

| Element źródłowy | Widoczna funkcja | Realizacja docelowa |
|---|---|---|
| FB51 + DB51 | Standardowa obsługa OP15 | Połączenie S7-1500 z panelem przez Ethernet; stary blok komunikacyjny zastąpić konfiguracją i nową obsługą danych |
| FB3, FB91, FB92, FB95, DB206 | Numery ekranów, alarmy, menu i zlecenia panelu | Ekrany i alarmy WinCC oraz jawny interfejs poleceń/statusów |
| FB60, FB89, FB90, DB60, DB205 | Przenoszenie receptury/programu i przygotowanie danych | Zdefiniowana struktura receptury oraz sekwencja przesłania, walidacji, potwierdzenia i błędu |
| DB210 / DB211 | Według symboli: PLC → OP / OP → PLC | Rozdzielone struktury statusów PLC i poleceń HMI |
| DB213 | Natywny FB60: żądanie PLC do OP, stany 10…13 i oczekiwanie T101=5 s; stary komentarz symbolu nie określa poprawnie kierunku | Żądanie receptury i potwierdzenie przesłania z opisanym właścicielem danych |
| FB62, FB63, DB41 | Natywnie potwierdzony zapis/odtworzenie 20 słów M200–M239 przez DW0,2,…,38 w DB41 | Ustalenie używanych danych; usunięcie potrzeby zapisu/odtwarzania dopiero po zastąpieniu komunikacji |
| MW192, M190.x, M191.x | Obraz klawiatury, polecenia, start HMI i potwierdzenia transferu | Obsługa przycisków dotykowych, impulsów/stanów oraz utraty komunikacji |
| FB96 | Zamiana bajtów słowa | Sprawdzenie, gdzie zamiana jest częścią formatu danych, a gdzie tylko starego protokołu |
| DB50, DB219 | Brak opisu w symbolach | Ustalenie roli na podstawie listingów i dokumentacji COMTEXT |

W tekstach OP15 odczytano m.in. nazwy `SCHRITTE`, `HANDBETRIEB`, `FAHRPROGR.1`, `ZEITEN`, `ZAEHLER`, `PROGRAMMNR`, `FAHRPROGRAMM`, obsługę receptur i ruchu bębna. Są też komunikaty o pompach, ogrzewaniu, drzwiach i temperaturze oraz ekran identyfikacji `ROLL Reinigungssysteme / KS04201`.

Proponowane ekrany TP900: przegląd maszyny, tryb ręczny, przebieg kroków, program/receptura, czasy i liczniki, alarmy oraz diagnostyka. [Otrzymany wydruk COMTEXT](comtext_review/USTALENIA_COMTEXT.md) dokumentuje cztery ekrany źródłowe, dziesięć wpisów PRG, adresy edytora czasów/liczników, obszary wymiany i klawisze. Użytkownik potwierdził dostępność trybu obrót/kołysanie; zachować go w nowym panelu. Dla wpisu pompy dozującej RAV pomoc określa pracę podczas przytrzymania K16.

Znaleziono 116 symboli o nazwach odpowiadających alarmom. Natywny wydruk COMTEXT zawiera **120 definicji alarmów i 121 definicji zdarzeń**; część jest rezerwą lub ma tylko numer. W O15 występują powtórzone teksty i różne warianty numeracji. `op15-text-fragments.csv` zachowuje 1886 fragmentów ASCII z pierwszego odczytu; właściwe definicje, adresy pól, typy i limity są teraz zestawione osobno w `comtext_review/`. Wydruk nie zawiera rzeczywistych zestawów wartości receptur. Przypisanie bitów do komunikatów i potwierdzanie trzeba porównać z pozostałym PLC.

**Adresy i typy:** S5 DW jest adresowany słowami, a S7 DBW bajtami. Przykładowo DW10 odpowiadałby DBW20 tylko przy świadomym zachowaniu identycznego układu kolejnych słów w DB ze stałymi offsetami. Zalecany interfejs HMI powinien mieć opisane typy i zmienne symboliczne. Trzeba osobno sprawdzić BCD, wartości czasu, znaczenie bajtów DL/DR, SWAP i znaki wartości; automatyczne mnożenie adresów nie rozwiązuje tych zależności.

TP900 Comfort `6AV2124-0JC01-0AX0` pozostaje kandydatem. Zakup należy oprzeć na zweryfikowanym pakiecie WinCC obsługującym Comfort, wymaganiach projektu i dostępności panelu. W tym środowisku nie potwierdzono zgodności firmware CPU z V19 ani zakresu posiadanych licencji.

## Materiały do następnego etapu

1. **STEP 5:** 42 pełne bloki porównane, w tym wszystkie PB. [Szósta partia](native_verification/WERYFIKACJA_PARTIA6.md) domknęła proces i sygnalizację. FB0, ciało FB51 i formaty archiwalnych DB pozostają osobno oznaczone.
2. **Dane robocze:** otrzymano DB15/DB19: [26 nastaw czasu i dwa presety BCD](native_verification/DB15_DB19_NASTAWY.md), Z1=20/Z2=14. Receptury 1/2 są kompletne; inne używane programy pozostają do ustalenia.
3. **COMTEXT:** dokumentacja konfiguracji jest już dostarczona w ROLL@@LS.INI. Potrzebne są rzeczywiste zestawy receptur i dalsze porównanie PLC w zakresie transferu, potwierdzania i reakcji klawiszy; nie trzeba ponownie eksportować definicji ekranów/pól.
4. **Sprzęt:** siedem modułów I/O oraz komplet 50 stron schematu są przeanalizowane. Potrzebne są końcowe modele S7 i modele G1/PNOZ i potwierdzenie rzeczywistego okablowania odręcznych zmian. Prądy silników z rysunków nie są prądami cewek PLC. Kartridż ma napis EPROM; dokładny wariant pozostaje do ustalenia. Numer CPU, RE i sprawna bateria są już potwierdzone. Nowy CPU: firmware po dostawie. TIA: pakiety STEP 7/WinCC i licencje przy przygotowaniu projektu.

STEP 5 i COMTEXT są dostępne u użytkownika. Ścieżki menu zależą od wersji i języka programu; ten raport nie zakłada konkretnej funkcji eksportu ani nie podaje niezweryfikowanych nazw menu. W razie trudności z dokumentacją wystarczy obraz ekranu menu drukowania/dokumentacji, aby dopasować instrukcję do faktycznego narzędzia.

## Sprawdzenia przed uruchomieniem nowego układu

Wynik migracji powinien zostać skompilowany w TIA V19 i sprawdzony dla rzeczywistego zestawu sprzętu. Scenariusze wynikające z odczytanego projektu obejmują: start po STOP i po zaniku zasilania, zachowanie czasów/liczników i nastaw, przejścia trybów ręczny/automatyczny, każdy ruch i blokadę transportu, obrót/kołysanie bębna, warunki pracy pomp i grzania, alarmy i kasowanie, utratę/odzyskanie połączenia HMI oraz przerwany lub błędny transfer receptury.

W symbolach występują sygnały drzwi, wyłączników krańcowych i ograniczników temperatury. Ich funkcję trzeba powiązać z rzeczywistymi obwodami i schematem podczas doboru sprzętu oraz testów maszyny. Sam standardowy CPU 1513-1 PN nie określa realizacji istniejących funkcji bezpieczeństwa.

## Pliki analizy

W katalogu `analysis/`:

- `symbols.csv`: wszystkie 1254 deklaracje z numerami wierszy źródłowych.
- `io-map-draft.csv`: adresy I/O i robocze odpowiedniki %I/%Q; nie jest to import konfiguracji sprzętowej.
- `s5-program-blocks.csv`: 63 bloki programu/danych, długości, pozycje, flagi i sumy kontrolne.
- `s5-all-directory-blocks.csv`: również nagłówki, komentarze i bloki pomocnicze rozpoznanych typów.
- `s5-comment-records.csv`: 922 rekordy komentarzy; znaczenie indeksu zależy od rodzaju rekordu.
- `db-raw-words.csv`: surowe słowa katalogowanych DB; podane reprezentacje liczbowe nie przesądzają o typie danych.
- `ob1-call-sequence.csv`: kolejność zapisanych wywołań w OB1.
- `alarm-symbols.csv`: kandydaci alarmów z tabeli symboli.
- `op15-text-fragments.csv` i `op15-numbered-text-fragments.csv`: fragmenty tekstów do dalszego porównania z COMTEXT.
- `inventory.json`: podsumowanie, ograniczenia i SHA-256 oryginałów.

`analyse_archives.py` odtwarza te zestawienia z zachowanych oryginałów bez zapisu do nich. Używa standardowej biblioteki Python. CSV mają kodowanie UTF-8 z BOM i separator średnik. Oryginalna tabela symboli jest dodatkowo dostępna jako `symbols-original-utf8.txt`.

Źródło porównawcze formatu pliku: [DotNetSiemensPLCToolBoxLibrary — Step5Project.cs](https://github.com/dotnetprojects/DotNetSiemensPLCToolBoxLibrary/blob/3d3eea50d9b24b53481809585f73e67f93ddb1d9/LibNoDaveConnectionLibrary/Projectfiles/Step5Project.cs) i enum PLCBlockType w tym samym commicie. Czytnik porównawczy nie zastępuje weryfikacji przez STEP 5; inwentaryzacja w tym raporcie sprawdza dodatkowo jawne wskaźniki katalogu i zgodność nagłówków.
