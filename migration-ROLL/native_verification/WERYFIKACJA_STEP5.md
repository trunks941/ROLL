# Weryfikacja wydruków STEP 5 — start, inicjalizacja i nastawy

Aktualizacja po [szóstej partii](WERYFIKACJA_PARTIA6.md): **42 pełne bloki**, wszystkie PB porównane. [DB15/DB19](DB15_DB19_NASTAWY.md) są kompletne: T116/T117 po 5 s, T24/T25 po 1/2 s, Z1=20/Z2=14. Zakresy i wskazane niżej braki wcześniejszych partii są historyczne. Bieżący czytnik FBD ma 13 kontroli, odczyt DB siedem; [aktualna lista braków](BRAKUJACE_BLOKI_STEP5.md).

Ten raport dokumentuje pierwszą partię siedmiu bloków. Aktualnie porównano **36 pełnych bloków**, a FB51 pozostaje częściowy. [Piąta partia](WERYFIKACJA_PARTIA5.md) opisuje ostatnie 220 sieci FBD/mieszanych. Dziewiętnaście pełnych STL nadal ma 1733 pozycje i 121 celów skoków; adresowane fragmenty, grafika OB1/PB16 i nowe FBD są osobno opisane.

Otrzymano `OB1ROLLS.INI` 9 października 2026. Rozszerzenie `.INI` nie określa tu zawartości: plik jest tekstowym wydrukiem dokumentacji STEP 5 z trzema stronami i sześcioma sieciami. Nagłówek wskazuje `04201@ST.S5D`, blok OB1, `LEN=75`; odpowiada to 150 bajtom bloku w analizowanym archiwum.

Oryginał zachowano bez zmian w `../originals/step5-native/OB1ROLLS.INI`. SHA-256: `a582ff2216b18114ddeebf290979cf3695750436ce112af7e427656e787c8506`. W [czytelnej kopii](OB1-native.txt) ujednolicono końce wierszy i usunięto znaki sterujące drukowaniem.

## Wynik porównania

- Wszystkie 44 instrukcje widoczne tekstowo w sieciach 1, 2, 5 i 6 odpowiadają wcześniejszemu odczytowi OB1, po ujednoliceniu mnemoników i rozwiązaniu symboli przez słownik z wydruku. Z porównania pominięto instrukcje organizujące prezentację `BLD` i `NOP0`.
- Wszystkie 27 wywołań bloków mają zgodną kolejność i warunkowość. Angielskie `JC` odpowiada `SPB`, a `JU` odpowiada `SPA`.
- Sieci 3 i 4 przedstawiono jako schematy FBD. Ich logika zgadza się z odczytem przy ręcznym porównaniu. Nie jest to porównanie natywnego zapisu STL tych dwóch sieci instrukcja po instrukcji.
- Nie stwierdzono rozbieżności w porównanym materiale. OB1 można wykorzystać bez ponownego eksportu.

Wydruk potwierdza początek `AN M0.4 → JC FB105 → AN M0.4 → BEC`: przy wyzerowanym M0.4 uruchamiane jest tworzenie danych, a jeśli po wywołaniu bit pozostaje wyzerowany, OB1 kończy się przed logiką procesu. Kolejność części obsługi panelu to FB3 → FB60 → FB89 → FB101.

W sieci 3 ustawienie M3.3 przez M3.2 występuje przed jego resetowaniem przez wejście AUTO (E0.2). Sieć 4 dopiero później oblicza M3.2 jako HAND (E0.1) i negację RI/NEUST (M0.1). Przy migracji trzeba zachować kolejność wykonania, a nie zastąpić tych sieci dowolnym przełącznikiem trybu.

Wydruk używa angielskich nazw obszarów: `F` odpowiada `M`, a `I` odpowiada `E`. Symbole mają w wydruku słownik adresów absolutnych. [Wynik maszynowy](OB1-comparison.json) i [ujednolicone instrukcje tekstowe](OB1-native-normalized-instructions.csv) dokumentują zakres porównania.

## FB105: rozstrzygnięcie DB/DX i pełne porównanie

Otrzymano `FB105RLS.INI` 9 października 2026: dwa warianty tego samego listingu, każdy po trzy strony i osiem sieci. Pierwszy używa symboli, drugi zawiera też operandy absolutne oraz adresy słów instrukcji. `LEN=166` odpowiada 332 bajtom FB105 w archiwum. Wszystkie sieci są czytelne w STL.

Oryginał zachowano w `../originals/step5-native/FB105RLS.INI`. SHA-256: `947e446a3f2937a85925e4a39cff7caf6256722626bc8b90989aec81008eb81c`. Dostępne są [czytelna kopia](FB105-native.txt), [wynik porównania](FB105-comparison.json) oraz [ujednolicone instrukcje](FB105-native-normalized-instructions.csv).

Porównano wszystkie **131 pozycji**, w tym 82 instrukcje wykonawcze i 49 znaczników prezentacji BLD. Adres słowa instrukcji z wydruku przeliczono na pozycję bajtową w bloku przez `10 + 2 × adres_słowa`. Zgadza się osiem sieci, pięć celów skoków oraz wszystkie operandy po jednej korekcie opisanej niżej.

**Natywny STEP 5 drukuje `G DB`, czyli niemieckie `E DB`.** Dotychczasowa tabela biblioteki błędnie opisuje operand kodu `7805` jako DX. Wszystkie dziewięć wystąpień w FB105 tworzy DB. Poprawiono odczyt operandu w pomocniczym czytniku, zachowując niezmienioną tabelę źródłową i wskazanie tego wydruku jako dowodu.

Po poprawce przeszło **17 kontroli czytnika**, w tym nowa kontrola dziewięciu adresów i operandów natywnych względem rzeczywistych bajtów FB105, czterobajtowej długości tych instrukcji i wyrównania następnej instrukcji. [Zapis wyników](../offline_decoder/test-results.txt) dokumentuje uruchomienie. Te kontrole dotyczą odczytu, nie wykonania programu PLC.

| Tworzony DB | KF przed G | Nowe słowa danych | Rola według kodu i symboli |
|---|---:|---:|---|
| DB15 | 131 | 132 | Robocze nastawy czasów |
| DB19 | 131 | 132 | Robocze nastawy liczników |
| DB41 | 40 | 41 | Zachowanie znaczników M200–M239 |
| DB51 | 186 | 187 | Komunikacja OP15 |
| DB205 | 220 | 221 | Bufor receptury |
| DB210 | 128 | 129 | Dane PLC → panel |
| DB211 | 10 | 11 | Dane panel → PLC |
| DB60 | 50 | 51 | Dane robocze transferu receptury |
| DB213 | 10 | 11 | Zarządzanie zleceniami panelu |

Przesłana instrukcja CPU, PDF 233–234 / drukowane 8-35–8-36, rozstrzyga działanie G DB: dodatni parametr n tworzy DW0…DWn z zerowymi wartościami; istniejący DB pozostaje bez zmiany. Późniejsza pętla kopiowania FB105 jest oddzielną operacją i może nadpisać dane. Parametr zero usuwa DB. Siedem obecnych DB ma archiwalne długości zgodne z tabelą; [zestawienie](../reference_manuals/FB105-creation-verified.csv). Tabela nie jest listą docelowych DB w TIA.

Potwierdzono kopiowanie DB12 → DB15 oraz DB16 → DB19: indeks MW242 zaczyna od 128, jest zmniejszany przed kopiowaniem i obejmuje DW127…DW0. Każde wywołanie przenosi jedno słowo i kończy FB105 przez `BEU`. Wywołanie wykrywające indeks zero ustawia odpowiednio M240.2 lub M240.7 i kończy blok przez `BEC`; następny etap rozpoczyna się w kolejnym wywołaniu. Pola DW128–130 nie są kopiowane z bloków wartości domyślnych.

Przy początkowo wyzerowanych znacznikach etapów M240.0/.1/.2/.6/.7 i braku zmian tych znaczników przez inne działania przebieg obejmuje 260 wywołań FB105. Nie można z tego wnioskować, że każdy restart maszyny inicjalizuje nastawy lub trwa tyle cykli. Użytkownik potwierdził RE i sprawną baterię; instrukcja wraz z ustawieniem RS120 potwierdza retencję M. Otrzymane OB21/OB22 nie zerują etapów ani M0.4, a zachowane M0.4 powoduje pominięcie FB105 w OB1. Po Overall Reset pamięć M jest jednak zerowana. Przy końcu FB105 ustawia M0.4 i zeruje M0.3; OB1 może wtedy przejść do logiki procesu.

## FB61, OB13, OB21, OB22 i FB101: pierwsza partia kompletna

Otrzymano kolejne pięć wydruków. Porównano **141 pozycji**, w tym 101 instrukcji wykonawczych oraz 40 znaczników BLD. Zgadza się każda pozycja bajtowa, instrukcja, operand, długość, przypisanie do sieci i 11 celów skoków FB101. Nie znaleziono dodatkowego błędu czytnika.

| Blok | Strony | Sieci | Pozycje / instrukcje wykonawcze | Wynik |
|---|---:|---:|---:|---|
| [FB61](FB61-native.txt) | 1 | 3 | 19 / 9 | Zgodny |
| [OB13](OB13-native.txt) | 1 | 1 | 17 / 12 | Zgodny |
| [OB21](OB21-native.txt) | 1 | 2 | 15 / 9 | Zgodny |
| [OB22](OB22-native.txt) | 1 | 2 | 15 / 9 | Zgodny |
| [FB101](FB101-native.txt) | 2 | 2 | 75 / 62 | Zgodny |

Oryginały są zachowane bez zmian w `../originals/step5-native/`. Sumy SHA-256 i szczegółowe wyniki znajdują się w [zestawieniu maszynowym](startup-parameters-comparison.json), osobnych plikach `*-comparison.json` i `*-native-normalized-instructions.csv`. Porównanie tej partii można odtworzyć poleceniem `python native_verification/compare_addressed_listings.py` z głównego katalogu materiałów. Skrypt nie łączy się z PLC i nie zmienia oryginałów.

### Ustawienia systemowe i takty

FB61 zapisuje `25` do RS97, wykonuje `RS120 OR 16#0008` i zapisuje `1000` do RS126. Przesłana instrukcja Edition 04 obejmuje dokładnie `CPU 942-7UB11` i potwierdza: interwał OB13 250 ms, bit 3 pełnej retencji M przy RE oraz opóźnienie sprawdzania konfiguracji modułów 1000 ms przy **następnym POWER OFF/ON**. Zapis RS126 nie opóźnia bieżącego OB21/22 i nie ustanawia zwłoki po każdym STOP/RUN. Użytkownik potwierdził RE i sprawną baterię. [Cytowania i warunki](../CPU_S5_USTALENIA.md) rozdzielają retencję M od T/Z i podtrzymania DB w RAM.

OB13 potwierdza kaskadę negacji i zakończeń warunkowych. Przy potwierdzonym nominalnym interwale 250 ms:

| Bit | Odstęp między zmianami stanu | Pełny okres |
|---|---:|---:|
| M3.4 | 250 ms | 500 ms |
| M3.5 | 500 ms | 1 s |
| M3.6 | 1 s | 2 s |
| M3.7 | 2 s | 4 s |

Początkowa faza zależy od stanów znaczników. Zastąpienie tego kodu pamięcią zegarową S7 wymaga sprawdzenia pełnych okresów, fazy i wykorzystywanych zboczy; same nazwy symboli nie wystarczają.

### Start po STOP i zaniku zasilania

OB21 i OB22 mają identyczną treść wykonywalną. Wywołują FB61, ustawiają M0.1/M0.2 oraz M191.0. `A M0.4; ON M0.4` zapewnia warunek prawdziwy przed ustawieniem M191.0 niezależnie od M0.4. W tych blokach nie ma kasowania M0.4, etapów M240.x, bitów taktów ani nastaw DB15/DB19.

Instrukcja i potwierdzone RE/sprawna bateria rozstrzygają warunki zachowania M oraz RAM. Nie oznacza to pełnej retencji wszystkich timerów/liczników: FB61 nie ustawia ich bitów 4/5. Pozostałe bloki mogą jawnie kasować lub nadpisywać stany. Przy migracji nie można automatycznie wczytywać nastaw fabrycznych podczas każdego przejścia S7 do RUN.

### Edycja czasów i liczników przez panel

Natywny FB101 potwierdził następujące pola osobno w DB15 i DB19:

| Pole | Funkcja |
|---|---|
| DW0–127 | Indeksowane wartości parametrów |
| DW128 | Wybrany numer parametru |
| DW129 | Poprzednio wybrany numer |
| DW130 | Bufor wartości odczytywanej/edytowanej przez panel |

Zmiana wyboru wczytuje parametr do DW130 i zapamiętuje numer w DW129. Przy tym samym wyborze bufor DW130 jest zapisywany do wskazanego parametru **w każdym wywołaniu**, bez osobnego sygnału zatwierdzenia w FB101. [Otrzymany COMTEXT](../comtext_review/USTALENIA_COMTEXT.md) potwierdza adresy i typy pól SP-ACT.VALUE. Nie zawiera jednoznacznego opisu zatwierdzania wszystkich tych pól; nie należy zmieniać cyklicznego zapisu bez porównania obecnej obsługi.

Wpis `FFFF` jest pomijany: numer w DW128 rośnie o jeden i ta część bloku kończy się bez aktualizacji DW129/DW130. Porównania S5 `!=F` i `><F` oznaczają odpowiednio równość i nierówność. Sześć instrukcji `DO FW240` odpowiada `B MW240` i modyfikuje następujący dostęp DW0.

Potwierdzono asymetrię obsługi indeksu ≥128: część czasów zapisuje 0 do DB15.DW128 i pomija dalszą obsługę w tym wywołaniu; część liczników zeruje wyłącznie MW240 i obsługuje wpis 0. DB19.DW128 pozostaje poprzednie, chyba że wpis 0 zawiera `FFFF`, kiedy dostaje 1. Zastosowano porównanie signed `<F` z 128; nie ma jawnego sprawdzenia dolnej granicy. Blok nie sprawdza też poprawności KT/BCD ani zakresu edytowanej wartości. Otrzymany COMTEXT podaje dolny limit numeru 0 i górny 128; pomoc opisuje 0…127. Format bufora czasu to KT, a licznika KC, bez jawnych limitów w powiązaniu.

MW240 jest współdzielonym słowem roboczym. Jego bajty obejmują także znaczniki M240.x używane przez FB105 podczas inicjalizacji. W docelowym projekcie warto oddzielić pamięć etapów inicjalizacji od bieżącego indeksu edytora; odwzorowanie nie powinno opierać się na przypadkowym współdzieleniu tych adresów.

## Następna partia

**Pięć otrzymanych partii porównano — 36 pełnych bloków.** Metody STL, FBD/mieszane oraz kontrole czytnika są opisane osobno w raportach. CPU, instrukcja, RE, sprawna bateria, COMTEXT i programy operatora 1/2 są już dostarczone. Pozostają schemat, aktualne nastawy, kodowanie KT i dalsza logika procesu.

Piąta partia została już porównana. Następne listingi: PB19, PB20, PB21, PB23, PB24, PB25 i FB0. FB51 ma tylko dwuwierszowy fragment; jego końcówka pozostaje nierozstrzygnięta. [Aktualna lista braków](BRAKUJACE_BLOKI_STEP5.md).

Potwierdzenie dotyczy dokumentacji 36 pełnych bloków oraz wymienionych funkcji systemowych z instrukcji CPU. Nie potwierdza jeszcze całego programu, kompilacji TIA ani działania maszyny.
