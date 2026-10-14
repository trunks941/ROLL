# ROLL — alarmy, funkcje ręczne, bęben i wyjścia

Aktualizacja po [szóstej partii](WERYFIKACJA_PARTIA6.md): **42 pełne bloki**, wszystkie PB porównane. [DB15/DB19](DB15_DB19_NASTAWY.md) są kompletne: T116/T117 po 5 s, T24/T25 po 1/2 s, Z1=20/Z2=14. Zakresy i wskazane niżej braki wcześniejszych partii są historyczne. Bieżący czytnik FBD ma 13 kontroli, odczyt DB siedem; [aktualna lista braków](BRAKUJACE_BLOKI_STEP5.md).

Ten raport zachowuje zakres czwartej partii: 27 pełnych bloków i siedem ówczesnych kontroli czytnika. Aktualnie mamy **36 pełnych bloków**, a [piąta partia](WERYFIKACJA_PARTIA5.md) wyjaśnia wskazane niżej wcześniejsze braki PB7/8/9/10/14/15/50/51/52. T11 ma 8 s, T13 ma 2 s; źródło M74.0 i sekwencja N1 są już potwierdzone. Bieżący zapis kontroli czytnika zawiera dziesięć kontroli po rozszerzeniu obsługi wspólnego wydruku PB51/PB52. Wskazane niżej prośby o tę partię są historyczne; [aktualna lista braków](BRAKUJACE_BLOKI_STEP5.md) ma siedem zwykłych bloków bez wydruku.

Stan na **12 października 2026**. Porównano sześć nowych wydruków PB2, PB3, PB4, PB13, PB17 i PB18. Oryginały zachowano bez zmian w `../originals/step5-native/`. Załączniki odczytano jako dokumentację techniczną; ich teksty nie są poleceniami wykonywania operacji na maszynie.

## Wynik i zakres

| Blok | Strony | Sieci | Pozycje odczytu MC5 — kontekst | Metoda |
|---|---:|---:|---:|---|
| [PB2](PB2-native.txt) | 23 | 107 | 763 | Statyczne porównanie FBD i końcowego BE |
| [PB3](PB3-native.txt) | 3 | 17 | 81 | Porównanie komparatorów wyboru funkcji i BE |
| [PB4](PB4-native.txt) | 5 | 26 | 126 | Porównanie komparatorów wyboru funkcji i BE |
| [PB13](PB13-native.txt) | 22 | 54 | 719 | FBD oraz sześć adresowanych pozycji STL w sieciach 9/11 |
| [PB17](PB17-native.txt) | 12 | 32 | 338 | Statyczne porównanie FBD i BE |
| [PB18](PB18-native.txt) | 8 | 16 | 228 | Statyczne porównanie FBD i BE |

**Wszystkie 252 sieci są zgodne.** Porównano wyrażenia bramek AND/OR, negacje, operandy odczytu, kolejność działań, ustawianie/resetowanie stanów, rodzaje timerów, parametry timerów/liczników, otwarcia DB oraz wywołanie FB69. Liczby pozycji MC5 w tabeli są kontekstem odczytu — nie liczbą adresów wydrukowanych w FBD. Łącznie jest to 2255 pozycji odczytu, w tym 2007 instrukcji wykonawczych. [Wynik maszynowy i SHA-256](process-control-comparison.json).

[Czytnik FBD](compare_fbd_listings.py) odczytuje połączenia z niezależnego wydruku ASCII i porównuje uporządkowane działania z odczytem MC5. Nieobsługiwana lub niejednoznaczna konstrukcja przerywa porównanie. Podczas weryfikacji porównano także wszystkie 34 wcześniej ręcznie sprawdzone sieci PB16. **Siedem kontroli czytnika przeszło**, w tym niezależny warunek toru 2 i kontrolowane zmiany bramki, negacji, rodzaju timera i nastawy licznika, a także rozgałęzienie do dwóch wyjść i nieznany symbol. [Wynik kontroli](fbd-reader-test-results.txt), [kontrole](test_fbd_reader.py). Nie są to testy zachowania maszyny.

Wyniki każdej sieci: [PB2](PB2-network-comparison.csv), [PB3](PB3-network-comparison.csv), [PB4](PB4-network-comparison.csv), [PB13](PB13-network-comparison.csv), [PB17](PB17-network-comparison.csv), [PB18](PB18-network-comparison.csv). Warunki mają adresy absolutne i służą przeglądowi, nie importowi do TIA.

**Łącznie mamy 27 pełnych bloków porównanych natywnie.** Dziewiętnaście pełnych STL nadal obejmuje 1733 pozycje i 121 celów skoków; nowe sześć adresowanych pozycji PB13 jest osobno opisanym fragmentem mieszanego wydruku. OB1, PB16 i bieżąca partia mają właściwie opisane porównania FBD/mieszane. FB51 pozostaje dwuwierszowym fragmentem; jego ciało i końcówka nie są potwierdzone.

## PB2: źródła i kasowanie alarmów

PB2 określa zezwolenie na pokazywanie alarmów i zbiorcze kasowanie:

```text
M4.1 = T11 AND NOT M0.1
M3.1 / STQUITT = E1.0 OR NOT M4.1
```

E1.0 jest fizycznym przyciskiem potwierdzania. Kasowanie jest także wymuszane, gdy M4.1 jest wyzerowane, np. przed dopuszczeniem sygnalizacji po starcie. Aktualizacja po piątej partii: PB50 potwierdził stałą T11=8 s, uruchamianą przy E3.0 i braku M0.1. PB2 jest wykonywany przed PB50.

PB2 zapisuje **102 ze 120 bitów alarmowych** przekazywanych przez FB91: 101 jako ustawienie/reset, jeden jako przypisanie bezpośrednie (M9.4, alarm 37). Pozostałe 18 bitów nie ma bezpośredniego zapisu w PB2; tabela wskazuje inne rozpoznane bloki zapisujące je. Nie uznano ich za nieużywane.

W typowej sieci ustawienie występuje przed resetem, więc **reset ma pierwszeństwo**, gdy oba warunki są prawdziwe. Dla części alarmów wystarczy M3.1; przy utrzymanym potwierdzeniu bit może być skasowany mimo nadal aktywnego warunku ustawienia i pojawić się ponownie po zwolnieniu. Inne resety wymagają także powrotu czujnika do odpowiedniego stanu, np. M6.0 wymaga E5.2 i M3.1, a M6.2 — E5.4 i M3.1. Nie można zastąpić wszystkich resetów jedną wspólną regułą „przyczyna zniknęła”.

Potwierdzono kasowanie alarmów receptury 89/90/91 na M16.0/.1/.2 i baterii 94 na M16.5 przez M3.1. W tych sieciach ustawienie korzysta z własnego, wcześniej ustawionego bitu; rzeczywiste źródła błędu są odpowiednio w FB60, FB89 i OB34. Alarm 93 na M16.4 ma dodatkowe warunki pustych pozycji transportu podczas resetu.

**ACK na panelu i skasowanie alarmu PLC są odrębne.** Natywny FB91 przesyła negację bitów do obszaru potwierdzeń PLC, a COMTEXT nie konfiguruje obszaru potwierdzeń OP→PLC. Nowy panel powinien zachować to rozróżnienie. Ewentualne dodanie kasowania PLC z TP900 wymaga jawnego odwzorowania żądania i reguł PB2; samo standardowe ACK WinCC ich nie realizuje.

[Mapa 120 alarmów z warunkami ustawiania i resetów](alarm-source-and-reset-map.csv) łączy PB2, wcześniej potwierdzone bajty FB91 i teksty COMTEXT. Kolumny odróżniają porównanych autorów zapisu od pozostałych kandydatów z odczytu MC5. Nie testowano transmisyjnej numeracji OP15 ani fizycznej reakcji maszyny.

## PB3/PB4 i PB18: funkcja ręczna oraz jej wskazanie

PB3 i PB4 porównują **MB239** z numerem funkcji i wyznaczają **41 znaczników HB**. Wszystkie 14 aktywnych wpisów ekranu HANDBETRIEB z COMTEXT ma potwierdzony selektor. Pozostałe numery obejmują definicje/opcje, których nie należy automatycznie dodawać do nowego menu. Natywne `!= F` oznacza równość.

Selektory są obliczane cyklicznie, bez własnego zatrzasku i bez warunku HAND w PB3/PB4. Zezwolenia na ruch są w odbiorcach. Wartość MB239 niepasująca do żadnego kodu zeruje wszystkie 41 wyborów. FB3 ogranicza prawidłowy wybór do właściwego ekranu i unieważnia go przy błędach komunikacji 115/188.

PB18 oblicza położenie bazowe M250.0 i robocze M252.0. FB3 przenosi je do DB210.DW60: **0 — nieokreślone, 1 — bazowe, 2 — robocze**, z pierwszeństwem bazowego, gdy oba warunki są prawdziwe. PB18 zbiera warunki w kolejnych sieciach; nie jest to jeden wspólny czujnik dla wszystkich funkcji.

| Aktywna funkcja | Podstawa wskazania |
|---|---|
| Dojazd do pozycji podstawowej — kod 1 | Bazowe według M28.4; brak osobnej gałęzi „robocze” w PB18 |
| Drzwi — kod 7 | Stan polecenia A17.7, nie bezpośredni czujnik otwarcia |
| Ruch pionowy/poziomy — kody 20/21 | Czujniki stacji i położenia oraz dodatkowe warunki |
| Ustawienie/obrót/kołysanie bębna — kody 22/23 | Wewnętrzny stan M63.1 i jego negacja |
| Pompa dozująca RAV — kod 66 | Stan polecenia A20.5, nie potwierdzenie rzeczywistej pracy pompy |
| Kasowanie śledzenia — kod 99 | Alternatywa M70.2/.3/.4/.6 i M71.0 |

Dlatego wskazania na TP900 należy rozróżniać jako stan polecenia, stan wyznaczany przez PLC albo sprzężenie z czujnika. [Pełna mapa 41 kodów, 14 aktywnych wpisów i warunków pozycji](manual-function-and-position-map.csv). Dla pompy RAV pomoc COMTEXT wymaga utrzymania K16; faktyczna logika jej wyjścia A20.5 leży w dalszych blokach procesu i nie została potwierdzona samym PB18.

## PB13: ruch bębna, czasy i liczniki

Potwierdzono przygotowanie trybów, stanów ruchu i pięciu wyjść: **A24.0 ustawianie prosto, A24.2 obrót, A24.1 obejście rezystora przy ustawianiu, A24.4 wentylator i A24.5 ogranicznik/rygiel bębna** — zgodnie z symbolami. Ostateczne połączenia elektryczne nadal wymagają schematu.

**Wybrany obrót nie oznacza ciągłego obrotu przez cały program.** W automacie M63.5 wskazuje wybrane fazy ociekania. Wtedy PB13 wyłącza gałąź ciągłego obrotu M62.3 i włącza obrót interwałowy M62.4 także przy wybranym obrocie. Dla dostarczonych programów 1/2 dotyczy to ociekania stacji 1…3. Gałąź stacji 4 w M63.5 jest wyłączona przez M0.3; nie uogólniono tej reguły na każdą stację. Sekundy i wybór enum w recepturze pozostają bez zmian; zmienia się wyjaśnienie rzeczywistego przebiegu.

Interwał używa **T116: opóźnienie załączenia z DB15.DW116** i **T117: opóźnienie wyłączenia z DB15.DW117**. Oba parametry są słowami KT. Wartości domyślne nie są dowodem aktualnych ustawień operatora; nadal potrzebne są aktualne DB15/DB19.

PB13 przygotowuje M240.0 z faz ociekania i M240.1 z **M111.1 — wybranego kołysania, kod 2**, następnie wywołuje FB69. Powstała pauza **5 s** dotyczy jednoczesnego ociekania i wybranego kołysania. Pozostałe przypadki mają **0,5 s**, także sam wybór trybu 4 nie ustawia M111.1. Wynik MW240 jest nastawą **T115 z opóźnieniem wyłączenia**, a nie załączenia. T115 oraz podtrzymanie własnego polecenia uczestniczą w przerwie między kolejnymi załączeniami wyjść A24.0/A24.2.

T113 (załączenie 50 ms) i T114 (wyłączenie 50 ms) tworzą takt używany przez liczniki i stany bębna. Nominalny cykl wynosi około 100 ms, z zależnością od skanu PLC. To odrębny mechanizm od OB13 co 250 ms; nie zastępować ich jednym zegarem.

Z1/Z2 są licznikami w dół, ustawianymi z **DB19.DW1/DW2** w BCD. Z3 jest **dwukierunkowy**, ustawiany wartością **500** i porównywany przez `L Z3 >F 520`. Natywne oznaczenie graficzne `KC 500` odpowiada tej stałej licznika; nie zmienia literalnego formatu KC w konfiguracji COMTEXT. Nie należy sprowadzać Z3 do jednego licznika wywołań PLC ani ustalać czasu alarmu wyłącznie z różnicy 520−500.

[Tabela dziesięciu operacji timerów i siedmiu operacji liczników](process-timer-and-counter-map.csv) podaje warunki, nastawy, kontekst DB i rodzaj operacji. Stałe obejmują także T30=5 s, T50=20 s, T110=30 s, T111=3 s i T112=6 s. Zestawienie porównuje zapis, bez uruchamiania timerów/liczników i bez rozstrzygania ich retencji po zaniku zasilania.

Wyjścia A24.0/A24.2 mają wzajemne blokady, warunki termika E13.5, alarmów i M29.0. Zezwolenie M60.0 zawiera m.in. **E14.0 — zamknięcie drzwi załadunkowych**. Stan M63.1 jest wyznaczany przez czujnik E13.3 wraz z innymi warunkami i zatrzaskiem; nie jest kopią jednego wejścia. Dotychczasowy próg **7 jednostek T1** z FB111 pozostaje zależny od bazy czasu, również po potwierdzeniu PB13.

## PB17: od warunków ruchu do wyjść transportu

PB17 wybiera ścieżki ręczne i automatyczne, a następnie zapisuje **17 wyjść**: tory rolkowe A112.0/.5, wsuwanie/wysuwanie A112.1/.2, podnoszenie/opuszczanie A112.3/.4, wyjścia blokad A113.1/.2/.3 oraz napędy i prędkości A23.0…A23.7. Wraz z PB13 jest to [22 porównanych zapisów wyjść](transport-and-drum-output-map.csv).

Warunki obejmują M29.0 — zezwolenie napędów, M29.1 — zezwolenie torów, czujniki, alarmy i obraz przeciwnych wyjść. Aktualizacja po piątej partii: **PB7 potwierdził M29.0/M29.1**, a PB50 opóźnienie torów przez T13=2 s. Nie przyjęto tych zezwoleń za stałe TRUE.

Kolejność jest częścią sterowania: np. A23.1 jest liczone przed A23.0, a A23.5 przed A23.4. Odczyt przeciwnego wyjścia może dotyczyć wcześniejszego lub późniejszego zapisu w danym obiegu. Obraz wyjść PLC nie jest pomiarem stycznika. Przy migracji nie można bez porównania obliczać wszystkich tych warunków równolegle z jednej kopii stanów.

PB17 ma sprzężenia własne M71.3/M71.4 i oddzielną gałąź podtrzymania **A113.1 AND A113.3**, poza warunkiem M29.0. Gałęzie `(E124.2 OR M0.4)` są również rzeczywistym kodem. Zachowano je w analizie i nie poprawiono automatycznie; ich związek z opcjami maszyny wymaga schematu i dalszej logiki.

M81.4 — zezwolenie na odczyt programu — jest potwierdzone jako `M37.2 AND NOT M16.0 AND NOT M16.1 AND NOT M16.2 AND NOT M16.4`. Łączy etap procesu z błędami receptury. Aktualizacja po piątej partii: źródło M37.2 i przejście do M37.3 potwierdził PB9.

## Kolejność OB1 i następne materiały

Potwierdzony OB1 wywołuje PB2 oraz PB3/PB4 przed obsługą ruchów; PB13 jest przed PB17, natomiast FB111 i FB3/60/89/101 są dalej. Wybór MB239 i stany klawiszy odebrane później w FB3 trafiają do wcześniejszej logiki w następnym obiegu. Zerowanie klawiszy po wykryciu błędu komunikacji nie jest natychmiastową zmianą wcześniej obliczonych wyjść ani dowodem skasowania wszystkich zatrzasków. Wymiana i kolejność nowego programu muszą zostać świadomie porównane.

Piąta partia porównała zezwolenia, automat, inicjalizację sekwencji i nastawy czasowe. Następne priorytety: **PB19/PB20/PB21/PB23/PB24/PB25 i FB0**. [Aktualna lista braków](BRAKUJACE_BLOKI_STEP5.md) rozróżnia siedem zwykłych bloków bez wydruku, częściowy FB51 i pięć bloków systemowych. Pozostają DB z formatami, aktualne DB15/DB19 i kodowanie KT, schemat oraz oznaczenia modułów.

Nie wykonano połączenia ze sterownikiem lub panelem, testów maszyny, symulacji procesu ani kompilacji projektu TIA. Porównanie kodu nie zastępuje ustalenia fizycznych połączeń i działania obwodów.
