# ROLL — panel, transfer receptur i diagnostyka S5

Aktualizacja po [szóstej partii](WERYFIKACJA_PARTIA6.md): **42 pełne bloki**, wszystkie PB porównane. [DB15/DB19](DB15_DB19_NASTAWY.md) są kompletne: T116/T117 po 5 s, T24/T25 po 1/2 s, Z1=20/Z2=14. Zakresy i wskazane niżej braki wcześniejszych partii są historyczne. Bieżący czytnik FBD ma 13 kontroli, odczyt DB siedem; [aktualna lista braków](BRAKUJACE_BLOKI_STEP5.md).

Ten raport opisuje stan po drugiej partii (13 pełnych bloków). Aktualnie porównano 36 pełnych bloków; [piąta partia](WERYFIKACJA_PARTIA5.md) uzupełniła automat, zezwolenia, śledzenie i timery. Wnioski i zakres 13 bloków w tym raporcie są historycznym etapem porównania.

Stan na 9 października 2026. Przeanalizowano siedem nowych wydruków STEP 5. **Sześć jest kompletnych i zgodnych z odczytem archiwum; FB51 udostępnia tylko początek bloku.** Oryginały zachowano bez zmian w `../originals/step5-native/`. Załączniki są materiałem technicznym, a nie poleceniami wykonywania operacji na maszynie.

## Zakres porównania

| Blok | Strony / sieci | Pozycje / instrukcje wykonawcze | Cele skoków | Wynik |
|---|---:|---:|---:|---|
| [FB3](FB3-native.txt) | 6 / 6 | 216 / 157 | 15 | Pełny listing zgodny |
| [FB60](FB60-native.txt) | 7 / 7 | 318 / 230 | 41 | Pełny listing zgodny |
| [FB62](FB62-native.txt) | 2 / 5 | 49 / 42 | 0 | Pełny listing zgodny |
| [FB63](FB63-native.txt) | 2 / 5 | 49 / 42 | 0 | Pełny listing zgodny |
| [FB69](FB69-native.txt) | 1 / 1 | 13 / 9 | 1 | Pełny listing zgodny |
| [OB34](OB34-native.txt) | 1 / 1 | 4 / 3 | 0 | Pełny listing zgodny |
| [FB51 — fragment](FB51-native-partial.txt) | Dwa identyczne wydruki strony 1 | 2 unikalne instrukcje | Niezweryfikowany cel | Tylko początek bloku |

W sześciu pełnych blokach zgadza się **649 pozycji**, obejmujących 483 instrukcje wykonawcze i 166 BLD, oraz **57 celów skoków**. Sprawdzono adresy, instrukcje, operandy, sieci i długości, także wielosłowowe instrukcje oraz parametry wywołań. Nie wykryto nowego błędu czytnika. [Wyniki maszynowe i sumy SHA-256](panel-control-comparison.json); odtworzenie: `python native_verification/compare_addressed_listings.py`.

Łącznie z [pierwszą partią](WERYFIKACJA_STEP5.md) weryfikacja natywna obejmuje **13 pełnych bloków kodu**. Dwanaście listingów z adresami to 921 pozycji, 666 instrukcji wykonawczych, 255 BLD i 73 cele skoków. OB1 porównano osobno: 27 wywołań, 44 widoczne instrukcje tekstowe i dwie sieci FBD ręcznie. FB51 nie zwiększa liczby pełnych bloków.

## FB51: zakres widoczny w STEP 5

Plik `FB51ROLS.INI` ma 478 bajtów i zawiera dwa identyczne wydruki po 239 bajtów. Każdy podaje nazwę `TDOP:511` i tylko:

```text
0005 :JU =M001
0006 :BE
```

**Użytkownik potwierdził: „Edytor pokazuje tylko te dwie linie”.** Nie prosimy więc o ponowne wykonanie tego samego eksportu. Nie ustalono przyczyny ograniczonej prezentacji i nie przypisano jej konkretnej ochronie bloku.

Adresy i mnemoniki dwóch instrukcji odpowiadają bajtom początku archiwalnego FB51, który ma 1052 bajty. Wydruk nie definiuje etykiety M001 ani długości bloku; nie pozwala nawet niezależnie sprawdzić celu pierwszego skoku. Dalszy kod i końcówka pozostają poza zakresem natywnego porównania.

Nadal nierozstrzygnięty jest skok pod `0x0416` do `0x041A`, nakładający się na stałą instrukcji odczytanej liniowo pod `0x0418` jako `L KH 6500`. Obie interpretacje i ostrzeżenie pozostają zachowane. [Dowód częściowego porównania](FB51-partial-comparison.json), [potwierdzenie użytkownika](user-confirmations.json).

Przy migracji połączenia AS511 na komunikację S7 przez Ethernet można oprzeć projekt nowego interfejsu na zweryfikowanych wywołaniach i obszarach danych. Dokumentacja producenta funkcji TDOP:511, jeśli jest dostępna, pomoże wyjaśnić statusy i interfejs. Nie będzie to dowód zgodności nieudostępnionego ciała FB51.

## FB3: klawisze, wybór funkcji i statusy

Sekwencja obsługi to FB62 → przygotowanie startu OP15 w DB51.DW64 → FB51 → zapis błędu M191.3 i wyniku MW187 → FB63. MB187/MB188 obejmują status i kod błędu starego sterownika komunikacyjnego; nie ustalono znaczenia wszystkich kodów.

DB211.DW5 zawiera typ i numer ekranu, DW6 numer wpisu. Funkcja ręczna MB239 jest dostępna tylko przy typie ekranu 1 i ekranie 10; w innych przypadkach otrzymuje `FF`. Dla błędów MB188 równych **115 lub 188** wybór jest również unieważniany. Komentarze opisują je jako watchdog i przerwę połączenia; pełna tabela kodów FB51 pozostaje do sprawdzenia.

Obraz klawiatury funkcyjnej pochodzi z DB211.DW2/3, a systemowej z DW0/1. Przy 115/188 FB3 zeruje ich robocze kopie: stany klawiszy i sygnał transferu M198.0 zostają wyzerowane. **Nie dowodzi to zatrzymania wszystkich ruchów maszyny** — odbiorcy poleceń, w tym PB16, nie mają jeszcze pełnego porównania natywnego.

| Klawisz / sygnał | Potwierdzone odwzorowanie |
|---|---|
| F1…F8 | M192.0…M192.7 |
| F9…F16 | M193.0…M193.7 |
| K13 / F13 | Offset 12 w obszarze COMTEXT; M193.4 i stan M190.5 |
| K16 / F16 | Offset 15; M193.7 i stan M190.6 |
| Wspólne naciśnięcie | M190.3: zbocze narastające alternatywy M190.5 OR M190.6, pamięć M190.4 |

Zmiana z jednego wciśniętego klawisza na drugi bez zwolnienia obu nie tworzy nowego wspólnego zbocza. Przyciski TP900 muszą odtwarzać stany naciśnięcia/zwolnienia oraz tę regułę tam, gdzie wymagają jej odbiorcy. Nie należy zastępować jej dwoma niezależnymi impulsami.

PB18 wyznacza położenie wybranej funkcji. FB3 zapisuje do DB210.DW60: 0 — nieokreślone, 1 — bazowe, 2 — robocze; położenie bazowe ma pierwszeństwo, jeśli oba warunki są ustawione. W DW62 przygotowuje odpowiednie bity LED13/LED16. PB18 nadal wymaga własnego listingu.

`LC T1` i `LC T2` trafiają do DB210.DW70/71. Są to **aktualne wartości timerów w BCD z bazą czasu**, nie same nastawy receptury ani zwykłe liczby sekund. Instrukcja CPU: PDF 216 / drukowana 8-18. Przy prezentacji pozostałego czasu w S7 trzeba przeliczyć kod i uwzględnić zachowanie właściwego timera. FB3 kończy obsługę wywołaniami FB91 i FB92, które pozostają do porównania.

## FB60: żądanie i oczekiwanie na recepturę

Potwierdzono stany DB60.DW10 oraz następujący przepływ w trybie zwykłym:

| Stan | Działanie |
|---:|---|
| 10 | Odczyt numeru programu z DB211.DW8 i sprawdzenie zakresu 1…99; zapis wybranego numeru w DB60 |
| 11 | Oczekiwanie na wolny slot DB51.DW60, przygotowanie DB213 i przekazanie wskaźnika zlecenia |
| 12 | Oczekiwanie na M190.1 / M190.2 oraz kontrola czasu T101 |
| 13 | Ustawienie stanu załadowania i M191.4 — program poprawny |

Między częścią faz występuje flaga pustego cyklu; kolejnych etapów nie można bez porównania scalić w jedno wywołanie. M81.4 zezwala na odczyt programu; jego brak resetuje stan załadowania, M191.4 i etap do 10.

Zlecenie przygotowane przez PLC ma: DB213.DW1=`KY0,70`, DW2=1 (numer definicji receptury PRG), DW3=wybrany numer programu. DB51.DW60/61 wskazują DB213 i DW1. Przy wydaniu żądania FB60 zeruje M190.1/M190.2. Natywne komentarze wiążą zlecenie z transferem receptury; pełne znaczenie kodu protokołu 70 wymaga dokumentacji tego interfejsu.

**T101 jest opóźnieniem załączenia o nominalnych 5 s**, aktywnym w stanie 12 przy braku obu odpowiedzi M190.1/M190.2 (`SD T101`, `KT005.2`). Po upływie czasu blok ustawia M16.0 / STOER_89. Przejście do ponowienia obejmuje zmianę wyboru lub M3.1 / STQUITT, łącznie z wejściem E1.0 / STOER_Q. Nie jest to bezwarunkowe ponawianie żądania co pięć sekund.

Sukces M190.1 prowadzi do stanu 13. Komentarz historyczny wskazuje M192.0/1, ale rzeczywiste, zweryfikowane operandy to **M190.1/2**. Producentem odpowiedzi jest dalsza logika FB89; bez FB89/FB90/FB111 nie potwierdzono jeszcze całego przyjęcia i rozłożenia receptury.

Programy operatora [1 i 2](../operator_recipes/RECEPTURY_OPERATORA.md) są kompletne i identyczne. To dwa osobne zestawy danych tej samej definicji PRG, której numer w zleceniu wynosi 1. Nowy interfejs powinien jawnie rozdzielać numer definicji, numer zestawu, żądanie i wynik transferu. Propozycja dla S7 obejmuje przyjęcie kompletnego zestawu po walidacji, z jednoznacznym potwierdzeniem; nie jest jeszcze implementacją TIA.

## FB62/FB63, FB69 i OB34

**FB62/FB63:** zapis i odtworzenie 20 słów MW200, MW202, …, MW238 (40 bajtów M200…M239). W DB41 odpowiadają im **DW0, DW2, …, DW38** — co drugie słowo, nie ciąg DW0…19. Są to operacje wokół wywołania FB51. DB41 ma 41 słów. W S7 można zrezygnować z ochrony wymaganej przez stary driver dopiero po ustaleniu wykorzystania tych danych procesu.

**FB69:** wybiera `KT005.1` — **0,5 s**, albo `KT005.2` — **5 s**, gdy jednocześnie są ustawione M240.0 i M240.1. Zapisuje zakodowany czas do MW240; sam nie uruchamia timera. Komentarze opisują czas ociekania i tryb kołysania. Użycie przez odbiorcę w PB13 pozostaje do porównania. Bazy czasu: instrukcja PDF 214 / 8-16.

**OB34:** przy M0.4 ustawia i zatrzaskuje M16.5 / STOER_94. Nie ma w nim resetu alarmu. Instrukcja CPU PDF 194 / 7-24 identyfikuje OB34 jako reakcję na awarię baterii BAU, wykonywaną przed kolejnymi cyklami, dopóki warunek awarii nie zostanie usunięty i potwierdzony. Jest to diagnostyka starej CPU. Odpowiednik diagnostyczny S7 trzeba dobrać do nowego sprzętu; numer OB34 ani alarm baterii S5 nie przechodzą automatycznie do S7-1500.

## Kolejne materiały

Bloki panelu, alarmów, funkcji ręcznych, automatu, zezwoleń i timerów zostały już porównane. Aktualne priorytety to PB19, PB20, PB21, PB23, PB24, PB25 i FB0. [Lista braków](BRAKUJACE_BLOKI_STEP5.md) rozróżnia siedem zwykłych bloków bez wydruku, częściowy FB51 i pięć bloków systemowych.

Porównania dotyczą dokumentacji offline. Nie wykonano testów maszyny, połączenia z PLC/OP15, symulacji procesu ani kompilacji projektu TIA.
