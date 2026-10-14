# ROLL — odbiór receptur, alarmy, nawigacja i ruchy ręczne

Aktualizacja po [szóstej partii](WERYFIKACJA_PARTIA6.md): **42 pełne bloki**, wszystkie PB porównane. [DB15/DB19](DB15_DB19_NASTAWY.md) są kompletne: T116/T117 po 5 s, T24/T25 po 1/2 s, Z1=20/Z2=14. Zakresy i wskazane niżej braki wcześniejszych partii są historyczne. Bieżący czytnik FBD ma 13 kontroli, odczyt DB siedem; [aktualna lista braków](BRAKUJACE_BLOKI_STEP5.md).

Ten raport opisuje stan po trzeciej partii, z 9 października. **Aktualnie porównano 36 pełnych bloków:** [piąta partia](WERYFIKACJA_PARTIA5.md) uzupełniła automat, zezwolenia, śledzenie i timery oraz doprecyzowała przytrzymany charakter M74.0. Wskazane niżej braki tej partii należy odczytywać w tym historycznym zakresie.

Stan na 9 października 2026. Otrzymano siedem listingów STL: FB89, FB90, FB91, FB92, FB95, FB96 i FB111, a następnie pełny wydruk FBD PB16. Oryginały zachowano bez zmian w `../originals/step5-native/`; potraktowano je jako dokumentację, nie polecenia operacji na maszynie.

## Wynik i metoda

| Blok | Strony / sieci | Pozycje / instrukcje wykonawcze | Cele skoków | Metoda |
|---|---:|---:|---:|---|
| [FB89](FB89-native.txt) | 3 / 3 | 119 / 90 | 13 | 118 adresowanych pozycji oraz końcowe BE bez wydrukowanego adresu |
| [FB90](FB90-native.txt) | 2 / 9 | 82 / 54 | 0 | Pełny listing z adresami |
| [FB91](FB91-native.txt) | 3 / 2 | 102 / 96 | 0 | Pełny listing z adresami |
| [FB92](FB92-native.txt) | 9 / 12 | 360 / 266 | 16 | Pełny listing z adresami, także 16 parametrów wywołań FB96 |
| [FB95](FB95-native.txt) | 1 / 1 | 36 / 24 | 4 | Pełny listing z adresami |
| [FB96](FB96-native.txt) | 1 / 1 | 18 / 14 | 0 | Pełny listing i dwie deklaracje parametrów |
| [FB111](FB111-native.txt) | 3 / 4 | 95 / 67 | 15 | Pełny listing z adresami |
| [PB16](PB16-native.txt) | 13 / 34 | Porównanie 34 sieci FBD | Nie dotyczy | Ręczne porównanie logiki graficznej; kontrola zestawów operandów |

**Wszystkie porównania są zgodne.** Siedem STL obejmuje 812 pozycji: 611 instrukcji wykonawczych i 201 BLD, oraz 48 celów skoków. W FB89 końcowe BE występuje jawnie w sieci 3, lecz bez adresu; jego pozycję wyznaczono z LEN i końca archiwalnego bloku. Nie przedstawiono jej jako adresu wydrukowanego przez STEP 5. W FB96 zweryfikowano deklaracje INPU/OUTP, a w FB92 wszystkie osiem par argumentów SWAP. [Wyniki STL](recipe-alarm-comparison.json).

PB16 zawiera wyłącznie FBD i słownik adresów. Porównano ręcznie grupowanie AND/OR, negacje, sprzężenia własne i kolejność S/R we wszystkich 34 sieciach. Skrypt kontroluje komplet sieci, długość 838 bajtów i zgodność zestawów operandów; nie wykonuje automatycznej interpretacji przewodów FBD. [Wynik](PB16-comparison.json), [warunki wszystkich sieci](PB16-FBD-network-review.csv), [sposób zapisania przeglądu](review_pb16_fbd.py).

**Łącznie porównano 21 pełnych bloków.** Dziewiętnaście STL obejmuje 1733 pozycje, z czego 1732 mają wydrukowane adresy, oraz 121 celów skoków. OB1 i PB16 mają osobno opisane porównania graficzne. FB51 pozostaje częściowy i nie zwiększa tej liczby. Zgodność dokumentacji nie jest testem wykonania PLC ani całego procesu.

## FB89: zakończenie transferu i wynik programu

FB89 odczytuje DB51.DW64 do MW240. Potwierdzone bity starego interfejsu:

| Znaczenie według kodu/komentarzy | Bit DW64 / maska | Obsługa |
|---|---|---|
| Transfer trwa | 15 / 8000 | Ustawia M191.5 |
| Koniec transferu | 14 / 4000 | Ustawia M191.6 |
| Skrzynka zablokowana | 11 / 0800 | Razem z końcem dopuszcza ocenę danych |
| Potwierdzenie odbioru | 13 / 2000 | Zapisywane po ocenie skrzynki |
| Potwierdzenie z błędem czasowym | 12 / 1000 | Zapisywane po upływie T100 |

T100 ma nominalnie **5 s**, ale jest uruchamiany przy M191.5 i braku M191.6, przed aktualizacją tych zatrzasków z DW64. Nie jest ogólnym limitem każdej fazy protokołu. T101 w FB60 jest odrębnym, również 5-sekundowym oczekiwaniem na wynik programu.

Ocena danych następuje przy końcu transferu i blokadzie skrzynki lub przy pamiętanym potwierdzeniu M191.7. DB205.DW0 dzieli się na **starszy bajt = numer definicji receptury 1** i **młodszy bajt = numer zestawu 1…99**. Historyczny komentarz „<=10” nie odpowiada rzeczywistej stałej 99. Niepoprawny nagłówek prowadzi do wyjścia bez wywołania FB90 i bez natychmiastowego potwierdzenia odbioru.

Przy poprawnym nagłówku FB89 wywołuje FB90. Następnie sprawdza surowe DW5, DW17, DW25 i DW33 przez signed `>F 0`. Gdy żadne nie spełnia tego warunku, ustawia M190.2 i M16.1 / alarm 90 oraz zeruje M190.1. To nie jest pełna walidacja BCD, bazy czasu ani wszystkich pól receptury. Surowa wartość `1000` może mieć dodatni zapis mimo zerowych cyfr czasu; FB90 osobno maskuje bazę przy wyborze stacji.

**Potwierdzenie odbioru 2000 i poprawność programu są osobnymi wynikami.** Także program odrzucony przez powyższy test trafia do ścieżki potwierdzenia odebranej skrzynki. Timeout ustawia M16.2 / alarm 91, M190.2 i maskę 1000. W obu ścieżkach ustawiane jest M191.7. W kolejnym etapie maska 07FF kasuje bity sterujące DW64, a M191.5/.6/.7 są resetowane. M190.1 otrzymuje negację M190.2.

FB89 nie zeruje M190.2 przy każdej poprawnej recepturze i nie resetuje alarmu 90 we własnym kodzie; przed żądaniem FB60 zeruje M190.1/.2. Procedury kasowania alarmów i inne źródła transferu wymagają pozostałych bloków, zwłaszcza PB2. Ciało FB51 pozostaje poza natywnym porównaniem, więc wewnętrznej realizacji protokołu nadal nie potwierdzono.

## FB90 i FB111: dziesięć pól receptury

Powiązania dziesięciu pól PRG z DB205 są teraz potwierdzone przez natywne listingi i konfigurację COMTEXT:

| Pole | DW | Odbiorca / działanie |
|---|---:|---|
| Zanurzenie stacji 1 | 5 | FB111 → T1; FB90 → M110.0 |
| Ociekanie stacji 1 | 9 | FB111 → T2 |
| Ultradźwięki stacji 1 | 13 | FB90: wartość 1 → M111.4 |
| Zanurzenie stacji 2 | 17 | FB111 → T1; FB90 → M110.1 |
| Ociekanie stacji 2 | 21 | FB111 → T2 |
| Zanurzenie stacji 3 | 25 | FB111 → T1; FB90 → M110.2 |
| Ociekanie stacji 3 | 29 | FB111 → T2 |
| Suszenie stacji 4 | 33 | FB111 → T1; FB90 → M110.3; natywny komentarz używa nazwy Tauchzeit |
| Ruch bębna | 37 | 1→M111.0 obrót; 2→M111.1 kołysanie; 3→M111.2 obrót interwałowy; 4→M111.5 obrót/kołysanie |
| Ruch pionowy w kąpieli | 41 | Wartość 1 → M111.3 |

FB90 pomija stację, gdy **DW czasu AND 0FFF = 0**. Sprawdza cyfry czasu, niezależnie od bazy. Nie potwierdza, że inne cyfry tworzą poprawny BCD. Zeruje też MW250 po przygotowaniu programu. Modele dla S7 powinny oddzielać logiczne pola od surowego formatu KT.

FB111 wybiera T1 według aktywnych kroków stacji 1…4 w tej kolejności. Gdy nie wybrano żadnej z tych gałęzi, ładuje KT010.2 = 10 s dla dalszej ścieżki. T1 jest uruchamiany przez alternatywę ośmiu kroków stacji. T2 wybiera ociekanie stacji 1…3; w pozostałej ścieżce ma również 10 s. Kolejność gałęzi ma znaczenie, jeśli kilka kroków jest ustawionych równocześnie.

W trybie **obrót/kołysanie (M111.5)** FB111 ustawia M58.5 — żądanie ustawienia bębna prosto — przy `(L T1 AND 0FFF) <= 7` i odpowiednim kroku jednej z pierwszych trzech stacji. `L T1` zwraca aktualny licznik binarny. **7 oznacza jednostki bazy timera, a nie zawsze 7 sekund:** przy bazie 1 s to 7 s, przy bazie 10 s — 70 s. Źródło semantyki: instrukcja CPU, PDF 216 / 8-18. Rzeczywiste kodowanie KT trzeba zachować przed zamianą tego warunku na TIME. Reset żądania wymaga jednocześnie M63.1 i E13.3, występuje po jego ustawieniu i ma w tym obiegu pierwszeństwo.

Programy [1 i 2](../operator_recipes/RECEPTURY_OPERATORA.md) mają teraz potwierdzone mapowanie wszystkich pól. Oba oznaczają cztery wybrane stacje, obrót M111.0, ultradźwięki M111.4, bez ruchu pionowego M111.3 i bez trybu mieszanego M111.5. To interpretacja dostarczonych wartości, bez uruchomienia programu. Same sekundy nie ustalają oryginalnej bazy KT.

## FB91: bajty alarmów i potwierdzeń

Natywny FB91 przenosi **MB5…MB19** do DB210: MB5→DR0, MB6→DL0, MB7→DR1 itd., MB19→DR7. Nie wolno zastąpić tego bezpośrednim kopiowaniem MW5 do DW0, ponieważ odwróciłoby kolejność bajtów.

Obszar potwierdzeń PLC otrzymuje odwrócone bity przez XOR FFFF: **NOT MB5…NOT MB20** do DW17…DW24. Dla 120 przenoszonych bitów alarmowych odpowiedni bit potwierdzenia jest ich negacją. Nie jest to zapis naciśnięcia ACK przez operatora. COMTEXT nie konfiguruje odrębnego obszaru potwierdzeń OP→PLC; kasowanie przyczyn i zatrzasków trzeba ustalić z PB2 i procesu.

FB91 zapisuje 15 bajtów alarmowych, ale 16 bajtów potwierdzeń. Dodatkowe **DL24 = NOT MB20** nie ma pary w zapisie alarmów FB91. DL7 oraz DW8…16 obszaru alarmów, a także DW25…33 potwierdzeń nie są zapisywane przez ten blok. Konfiguracja COMTEXT ma większe obszary po 17 słów; nie uznano pozostałych słów za automatycznie zbędne lub zerowane.

[Tabela 120 bitów i tekstów](alarm-memory-and-text-map.csv) łączy zweryfikowane adresy z numeracją symboli STOER i definicjami COMTEXT. Podstawa numeracji komunikatów jest jawnie oznaczona; transmisyjnej numeracji OP15 nie testowano oddzielnie. [Wszystkie zapisy bajtowe](FB91-byte-writes.csv). Alarmy 89/90/91/94 odpowiadają M16.0/.1/.2/.5; źródła części z nich są już potwierdzone w FB60, FB89 i OB34.

## FB92, FB95 i FB96: nawigacja i kroki

FB92 obsługuje stany wyborów i pamięci zboczy klawiszy. Część wyborów jest zatrzaskiwana i kasowana innymi klawiszami; gałąź włączenia F5 jest zablokowana przez M0.3. **F2 nie daje trwałego przełączenia M196.1:** po początkowym ustawieniu/resetowaniu późniejsza gałąź resetu w tej samej sieci zawiera sam stan F2 (M192.1), więc naciśnięcie zeruje M196.1 do końca sieci. Wcześniejszy opis pojedynczego fragmentu jako toggle nie obejmował tej dalszej gałęzi. Nawigacja F2 do FAHRPROGR.1 jest osobno skonfigurowana w COMTEXT. Nie należy odtwarzać funkcji tylko z nazw komentarzy, pomijając rzeczywiste warunki. Wybór ekranu 20 i wpisu 1/2/3/11 ustawia M189.0/.1/.2/.3. Powrót poza ekran kroków kasuje te bity przy odpowiednim stanie klawiatury i M190.7.

Aktywne przekazanie kroków N1 dotyczy **MB37…MB53 → DB210.DW50…58**. Osiem wywołań FB96 zamienia bajty MW37,39,…,51, aby starszy bajt znacznika znalazł się w DR odpowiedniego DW. MB53 trafia do DR58. [Mapowanie bajtów N1](N1-event-byte-map.csv). Przy braku wyświetlania N1 blok zeruje DW50…58. Przy aktywnym wyświetlaniu nie zeruje osobno DL58; jeśli alternatywa słów DW50…58 jest zerowa, zapisuje 8000 do DW58 jako przypadek „brak kroku”. Nie założono, że ten bit znika automatycznie przy kolejnym kroku.

Sieci przekazywania N3 i N11 są pomijane przez bezwarunkowe skoki. Zawarte w nich zapisy DW111/DW110 nie są wykonywane zwykłym przepływem tego bloku. Nie uznano ich komentarzy za aktywne funkcje nowego panelu.

FB95 ustawia wskaźniki aplikacyjnych zleceń w DB51: DW32/33→DB206.DW0 dla poziomu meldunków/kroków, DW36/37→DB206.DW8 dla odpowiedniej gałęzi trybu ręcznego. W pierwszej gałęzi kończy się przez BEU. Pełne znaczenie danych DB206 i obsługi zlecenia wymaga wydruku tego DB oraz dokumentacji starego interfejsu; nie przypisano numerów poleceń na podstawie samych nazw.

FB96 jest rzeczywistą zamianą starszego i młodszego bajtu słowa przez SLW8, SRW8 i OW. INPU i OUTP są parametrami WORD; MW240/MW242 są słowami roboczymi. Na TP900 z symbolicznymi tagami nie trzeba kopiować tej zamiany wszędzie — jest ona elementem konkretnego układu bitów starego OP15.

## PB16: warunki ruchów ręcznych

Porównano wszystkie 34 sieci. PB16 wyznacza znaczniki żądań i warunków M73…M78, a nie bezpośredni komplet wyjść fizycznych. PB17 ma 14 statycznych odczytów tej grupy; jego własny listing nadal jest potrzebny do sprawdzenia sterowania wyjściami.

- M73.7 wymaga HAND, wybranej funkcji korekty i **obu** K13/K16 równocześnie.
- M74.4 (warunek toru 2) i M75.4 (ruch poziomy do przodu) korzystają z utrzymanego K16 oraz dalszych warunków. Dla części kierunków występuje też negacja przeciwnego klawisza.
- Aktualizacja po PB15: M74.0 — dojazd do pozycji podstawowej — wymaga HAND, przytrzymanego K13, braku K16, braku pozycji bazowej i wybranej funkcji 1 lub 2. Nie jest samodzielnym zatrzaskiem. Wcześniejszy PB16 odczytuje poprzednią wartość M74.0; późniejszy FB3 aktualizuje klawisze. Zerowanie obrazu klawiatury nie dowodzi natychmiastowego wyłączenia odrębnych zatrzasków i podtrzymań wyjść.
- M75.3 i M77.1 mają sprzężenia z własnym poprzednim stanem. M240.0 ma różne role w kolejnych sieciach 14 i 21; kolejność jest częścią logiki.
- M78.4/.6/.7 są ustawiane i resetowane; reset występuje później i ma pierwszeństwo przy obu warunkach prawdziwych. Zwolnienie klawisza samo w sobie nie kasuje wszystkich tych stanów. Gałęzie resetów obejmują m.in. opuszczenie HAND.
- M76.4 zawiera osobną alternatywę E11.4, poza gałęzią negacji dwóch alarmów. M76.6 ma `(E124.2 AND E124.5) OR M0.4`. Zachowano te warunki jako istniejącą logikę; nie zmieniono ich podczas dokumentowania.

[Warunki każdej sieci](PB16-FBD-network-review.csv) używają adresów absolutnych; definicje skrótów Z/G/C7/C8 są w [PB16-comparison.json](PB16-comparison.json). Docelowe przyciski dotykowe muszą zachować znaczenie stanu, wspólnego zbocza i zatrzasku zgodnie z odbiorcą. Wybory HB potwierdziły późniejsze PB3/PB4, a M74.0 potwierdził PB15; szczegóły w piątej partii.

## Następne materiały

**Najpierw PB2, PB3, PB4, PB13, PB17 i PB18:** źródła/kasowanie alarmów, wybór funkcji ręcznych, bęben, wyjścia transportu i pozycje funkcji. Później pozostałe PB i FB0 oraz DB z formatami, w szczególności DB206/210/211, aktualne DB15/DB19 i rzeczywiste kodowanie KT w aktywnej recepturze. Schemat i oznaczenia modułów są nadal podstawą doboru I/O. [Pełna lista braków](BRAKUJACE_BLOKI_STEP5.md).

Nie wykonano połączenia ze sterownikiem/panelem, testów maszyny ani kompilacji projektu TIA. Weryfikacja bieżącej partii nie rozstrzyga ciała FB51 i pozostałych bloków procesu.
