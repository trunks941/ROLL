# ROLL — automat, zezwolenia, śledzenie i czasy

Aktualizacja po [szóstej partii](WERYFIKACJA_PARTIA6.md): **42 pełne bloki**, wszystkie PB porównane. [DB15/DB19](DB15_DB19_NASTAWY.md) są kompletne: T116/T117 po 5 s, T24/T25 po 1/2 s, Z1=20/Z2=14. Zakresy i wskazane niżej braki wcześniejszych partii są historyczne. Bieżący czytnik FBD ma 13 kontroli, odczyt DB siedem; [aktualna lista braków](BRAKUJACE_BLOKI_STEP5.md).

Stan na **12 października 2026**. Osiem nowych plików STEP 5 zawiera **dziewięć pełnych bloków**: PB7/8/9/10/14/15/50/51/52. Plik **PB51ROLS.INI zawiera zarówno PB51, jak i PB52**. Zachowano cały oryginał; oba bloki mają osobne wyniki porównania i zakresy bajtów w tym samym źródle. Użytkownik zapowiedział ponowne przesłanie oddzielnych wydruków PB51/PB52; zostaną porównane jako dodatkowe źródła, gdy nadejdą.

## Wynik porównania

| Blok | Strony | Sieci | Pozycje MC5 — kontekst | Adresowane pozycje STL |
|---|---:|---:|---:|---:|
| [PB7](PB7-native.txt) | 7 | 27 | 194 | 0 |
| [PB8](PB8-native.txt) | 4 | 6 | 102 | 0 |
| [PB9](PB9-native.txt) | 24 | 65 | 723 | 0 |
| [PB10](PB10-native.txt) | 24 | 61 | 716 | 0 |
| [PB14](PB14-native.txt) | 9 | 23 | 260 | 3 |
| [PB15](PB15-native.txt) | 3 | 9 | 86 | 0 |
| [PB50](PB50-native.txt) | 1 | 5 | 25 | 7 |
| [PB51](PB51-native.txt) | 2 | 8 | 67 | 0 |
| [PB52](PB52-native.txt) | 5 | 16 | 161 | 3 |

**Wszystkie 220 sieci są zgodne w statycznym porównaniu.** Czytnik odtwarza działania z połączeń ASCII FBD i porównuje warunki AND/OR, negacje, adresy, kolejność ustawiania/resetowania, operacje timerów, nastawy i otwarcia DB z odczytem archiwum. Trzynaście pozycji adresowanego STL porównano osobno. 2334 pozycje MC5 obejmują 2119 instrukcji wykonawczych i 215 BLD; te liczby są kontekstem odczytu, a nie liczbą adresów wydrukowanych w FBD.

[Wyniki, SHA-256 i zakresy źródła](automation-control-comparison.json). Wspólny plik ma 13537 bajtów: PB51 zajmuje zakres `[0,3738)`, PB52 `[3738,13537)`. SHA-256 i długość w obu wynikach odnoszą się do całego pliku. Nie zapisano fikcyjnego osobnego oryginału PB52.

[Dziesięć kontroli czytnika FBD](fbd-reader-test-results.txt) przeszło, w tym wybór obu bloków ze wspólnego pliku i odrzucenie nieobecnego bloku. Odtworzenie: `compare_fbd_listings.py`, `test_fbd_reader.py`, `record_native_status.py`, a następnie [extract_automation_control.py](extract_automation_control.py). Czytnik MC5 pozostał bez zmian; nie powtarzano jego wcześniejszych 17 kontroli.

**Aktualnie porównano 36 pełnych bloków.** FB51 nadal jest częściowym wydrukiem. Pozostało siedem zwykłych bloków bez wydruku i pięć bloków systemowych w osobnej grupie. Dziewiętnaście pełnych STL nadal obejmuje 1733 pozycje i 121 celów skoków; nowe fragmenty STL nie zmieniają tego zakresu. [Status](program-native-verification-status.csv), [inwentaryzacja](native-files-inventory.json), [lista braków](BRAKUJACE_BLOKI_STEP5.md).

## PB7 i PB50: zezwolenia oraz start

PB7 oblicza M28.5 z E10.7 (ciśnienie powietrza), E3.4 (sterowanie włączone), E3.5 (drzwi serwisowe zamknięte) i E3.7 (stan zabezpieczeń napędów). M28.6 wymaga ponadto braku alarmów M13.4, M16.6 i M5.7. Są to warunki programu; schemat jest potrzebny do ustalenia rzeczywistych obwodów.

```text
S M29.0: (AUTO E0.2 AND AUTO_EIN E0.4) OR HAND E0.1
R M29.0: NOT M28.6
M29.1 = M29.0 AND T13
SE T13: M29.0, KT020.1 = 2 s
```

M29.0 jest zatrzaskiem zezwolenia napędów, z resetem po ustawieniu. M29.1 dodaje **2 s opóźnienia zezwolenia torów rolkowych**. T13 jest liczony w PB50 przed PB7, z wartością M29.0 zastaną w tym obiegu. Nie jest to wspólne dwusekundowe opóźnienie wszystkich wyjść.

PB50 uruchamia **T11 = KT008.2 = 8 s**, gdy E3.0 (napięcie sterowania) jest prawdziwe i M0.1 jest wyzerowane. PB2, wykonywany wcześniej, wylicza `M4.1 = T11 AND NOT M0.1` oraz `STQUITT = E1.0 OR NOT M4.1`. To potwierdzone opóźnienie ogólnej sygnalizacji alarmów. Jest odrębne od systemowego RS126=1000 ms. PB50 resetuje także M0.2, jeśli M0.1 jest ustawione; OB1 na początku kolejnego obiegu resetuje M0.1 przy wyzerowanym M0.2. Nie oznacza to resetu całej pamięci.

M28.4 zbiera pozycję podstawową z M28.0…M28.3. W PB7 sieci 4/5 zawierają alternatywy z M0.4, który po inicjalizacji ma wartość logiczną 1. Zachowano rzeczywiste wyrażenia, bez dopisywania dodatkowej kontroli pozycji.

M31.1 łączy warunki startu M30.5/.6/.7, M31.0 i M31.2. Gałąź M30.5 dopuszcza także SERVICE E0.0 lub E_TROCK E0.6; pozostałe warunki M31.1 nadal obowiązują. M31.4 (AUTO_E) jest ustawiany przy pozycji bazowej lub trwającym AUTO_L, E0.4 i M4.4. Reset wymaga alternatywy: brak AUTO, brak E0.3 AUTO_AUS, brak M29.0 lub brak M31.1.

**M31.4 i M31.5 oznaczają różne stany.** M31.5 (AUTO_L) jest ustawiany przez M31.4, lecz po usunięciu AUTO_E może pozostać aktywny do właściwego etapu i pozycji bazowej. Brak E0.2 resetuje go bezpośrednio. Nie zastępować obu stanów jednym sygnałem RUN. PB7 zapisuje też A16.6=M31.5 (licznik godzin) oraz A16.7=M40.0 (licznik partii), zgodnie z symbolami.

[41 działań dotyczących zezwoleń i stanów](automation-permits-and-state-map.csv), [dwa wyjścia liczników](automation-meter-output-map.csv).

## PB9/PB10: kolejność kroków automatu

Zestawienie zawiera **111 bitów kroków i 222 działania S/R**, z pełnymi warunkami i kolejnością sieci: [automatic-steps-SR.csv](automatic-steps-SR.csv). PB9 najpierw oblicza impuls M32.0, pamięć zbocza M32.1 i reset M32.2. Ten ostatni ma warunek `NOT E0.2 OR E0.1`; jest wspólną gałęzią resetów kroków.

M35.2 zezwala na przechodzenie kroków: ustawienie przez E0.4, późniejszy reset przez brak M29.0, brak M31.5, brak M35.1 lub alarm czasu kroków M16.3. M35.1 wymaga braku M12.0, M5.0, M5.2 i M9.0. PB9/PB10 odczytują zezwolenia sprzed późniejszego wywołania PB7; zachowanie po poleceniu start/stop trzeba porównywać z tą kolejnością.

M37.2 oznacza etap obecności nośnika i odczytu programu. Przejście do M37.3 wymaga m.in. zamkniętych drzwi E14.0, programu odebranego i poprawnego M190.1, poprawności M191.4, braku trwającego transferu M191.5 i braku wybranych alarmów receptury. Potwierdza to powiązanie żądania receptury w PB17 z odbiorem w FB60/89; samo potwierdzenie skrzynki nie wystarcza do przejścia kroku.

| Stacja | Zanurzenie / praca — oczekiwanie T1 | Ociekanie — oczekiwanie T2 |
|---|---|---|
| 1 | M40.5 → M40.6 | M41.1 → M41.2 |
| 2 | M42.1 → M42.2 | M42.5 → M42.6 |
| 3 | M43.5 → M43.6 | M44.1 → M44.2 |
| 4 | M45.2 → M45.3 | M45.6 → M45.7 ma `(M0.4 OR T2)`, więc po inicjalizacji nie czeka na T2 |

M110.0…M110.7 wybierają stacje 1…8. Kod zawiera pomijanie niewybranych stacji i kolejne opcjonalne stacje; nie wolno dodawać ich do receptury tylko na podstawie obecności kodu. Cztery stacje PRG pozostają zgodne z COMTEXT. PB10 kończy przebieg powrotem do załadunku i M53.6, które przygotowuje kolejny cykl przez M37.0.

Ustawienie późniejszego kroku następuje przed resetem poprzedniego w następnym wywołaniu. Kilka warunków przejścia może być spełnionych w jednym obiegu. **Nie dowiedziono, że zawsze aktywny jest dokładnie jeden bit.** Prosta zamiana na enum z jednym przejściem na obieg może zmienić zachowanie; potrzebne jest późniejsze porównanie przebiegów.

PB8 nadzoruje wybrane fazy ruchu przez T40/T41, oba **30 s**. Ustawia M34.1, a PB2 przenosi go do alarmu M16.3. Te watchdogi nie ograniczają czasu zanurzenia 360 s do 30 s — dotyczą wskazanych w warunkach etapów przejściowych.

## PB14: ruchy i BADHUB

[21 działań poleceń automatycznych](automatic-motion-command-map.csv) dokumentuje M64…M68. PB17 później wybiera gałęzie ruchu i oblicza fizyczne polecenia wyjść. M66.4 i M66.7 łączą ruch pionowy transportu z krótkim ruchem w kąpieli, z warunkiem E11.6.

M68.0 wymaga **M111.3 — BADHUB** i właściwego etapu. M68.2/M68.3 wyznaczają podnoszenie/opuszczanie krótkiego skoku, używając T24/T25 z DB15.DW24/DW25. Dlatego **BADHUB=aus w programach 1/2 wyłącza ruch krótkiego skoku w kąpieli; normalne podnoszenie i opuszczanie transportu nadal jest potrzebne**. Bieżące nastawy DW24/DW25 nie są znane z archiwum wartości domyślnych.

## PB15: śledzenie nośników i korekta opisu M74.0

PB15 wylicza cyklicznie:

```text
M74.0 = HAND E0.1 AND K13 M190.5 AND NOT K16 M190.6
        AND NOT M28.4 AND (HB1 M20.1 OR HB2 M20.2)
```

**M74.0 nie jest osobnym zatrzaskiem i wymaga przytrzymania K13.** Doprecyzowuje to wcześniejsze raporty PB16: alternatywa z M74.0 nie dowodzi samodzielnej kontynuacji dojazdu po zwolnieniu klawisza. PB16 jest jednak wykonywany przed PB15, więc korzysta z poprzedniej wartości M74.0. FB3 aktualizuje klawisze jeszcze później. Opóźnienie propagacji zmian i odrębne zatrzaski/podtrzymania wyjść nadal trzeba uwzględniać; samo wyzerowanie obrazu klawiszy nie dowodzi natychmiastowego wyłączenia wszystkich ruchów.

M73.7, wyliczany w PB16 dla funkcji 99 i obu klawiszy, resetuje **siedem bitów**: M70.2/.3/.4/.5/.6/.7 oraz M71.0. Status tej funkcji w PB18 obejmuje tylko pięć z nich — pomija M70.5 i M70.7. Nie należy więc używać wskazania panelu jako pełnej listy resetowanej pamięci. [14 działań śledzenia i resetów](tracking-state-SR.csv).

## PB51/PB52: stałe i nastawy czasowe

[30 działań timerów](automation-timer-map.csv) obejmuje 29 uruchomień i jeden reset T62, ze wskazaniem rodzaju operacji, warunku, stałej lub kontekstu DB15. SE i SA wymagają różnych odpowiedników; TON/TOF w tabeli są kandydatami do porównania, bez potwierdzonej równoważności wykonania i retencji.

**T16 = KT360.3 oznacza 360 × 10 s = 3600 s, czyli 60 minut.** Nadzoruje warunek `NOT E5.6 AND M31.5`, opisany jako opóźnienie alarmu TGS separatora oleju. To osobny timer, niezwiązany z czasem 360 s zanurzenia receptury.

Inne stałe: T15=60 s, T18=1 s, T19=15 s, T20=1 s, T21=5 s, T95=5 s, T45=0,5 s, T70/T72=10 s (SA). T17/T31/T32/T33 oraz T24/T25/T58/T59/T62/T63/T85 korzystają z właściwych DW w roboczym DB15, którego aktualnych wartości nadal potrzebujemy.

T35…T38 mają 300 s, lecz warunek `NOT M0.4`; po zakończonej inicjalizacji nie są aktywnymi watchdogami dodatkowych stacji. T62 ma dodatkowy reset od M103.0/.3/.4 i T119. Autorzy tych żądań w pozostałym procesie wymagają dalszego porównania; nie wyznaczono pełnego cyklu uzupełniania wyłącznie z timerów.

## Kolejność OB1 i pozostałe materiały

PB2 → PB3/PB4 → PB19/PB21 → PB50/PB51/PB52 → warunkowe PB8/PB9/PB10/PB14 lub PB16 → PB7 → PB13 → PB15 → PB17 → pozostały proces → FB111 → obsługa OP15. **Warunkiem wywołań jest M3.3, nie bezpośrednio E0.2.** OB1 zatrzaskuje M3.3 z M3.2, resetuje go przez AUTO, a dopiero później wylicza M3.2 z HAND i negacji restartu. Nie usuwać tego przejściowego zachowania bez porównania.

Następne brakujące zwykłe listingi: **PB19, PB20, PB21, PB23, PB24, PB25 oraz FB0**. FB51 pozostaje osobną niewyjaśnioną funkcją komunikacyjną. Nadal potrzebne są DB z formatami, aktualne DB15/DB19, rzeczywiste kodowanie KT, schemat i oznaczenia modułów. Dwa programy operatora mają komplet potwierdzonych wartości; nie zmieniono ich.

To analiza statyczna źródeł offline. Nie wykonano testów maszyny, symulacji procesu ani kompilacji TIA. [Kontrola zachowania źródeł i spójności artefaktów](partia5-artifact-checks.json) dotyczy tylko dokumentacji i narzędzi analizy.
