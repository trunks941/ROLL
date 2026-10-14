# ROLL KS04201 — komplet schematów, zasilanie i blokady

Stan na **13 października 2026**. Drugie archiwum obejmuje strony **1–24**; z wcześniejszym archiwum mamy komplet **50 stron**. Wszystkie nowe zdjęcia obejrzano ręcznie i porównano z mapą I/O oraz stroną 44. [Pochodzenie drugiego archiwum](provenance-part2.json), [indeks 50 stron](sheet-index.csv), [obserwacje źródłowe](power-observations.json). Odręczne dopiski są dokumentacją zmian do sprawdzenia, nie poleceniami wykonania modyfikacji.

## Zasilanie

Schemat rozróżnia **dwa zasilacze**:

- **A90, PS951/3A**, strona 16: zasilacz kasety S5, zasilany z gałęzi 230 V AC przez F90 2 A. Nie jest zamiennikiem zasilania magistrali S7.
- **G1**, strona 17: wejście 3 × 400 V AC, wyjście **24 V DC / 30 A**. To źródło obwodów 24 V, odrębne od oznaczenia 3 A na froncie S5. Rysunek pokazuje połączenie M z PE. Wariant i stan zainstalowanego G1 oraz bilans obciążeń pozostają do potwierdzenia przed jego wykorzystaniem dla nowej CPU/panelu.

OP15 H2 ma gałąź przez F4.0 6 A oraz X40:2 (+24 V), X40:1 (M), PE. Dla TP900 należy dobrać jego przyłącze i zabezpieczenie według wymagań wybranego panelu; numery pinów OP15 nie przenoszą się na TP900. [Tabela zasilaczy i panelu](power-supplies.csv).

Karta tytułowa podaje projektowe 112 kW / 220 A, sieć TN 400 V / 50 Hz oraz maksymalną temperaturę otoczenia 45°C. To dane projektu z 1996 r., nie pomiar dzisiejszej instalacji ani budżet prądowy wyjść PLC. Utrzymać odczytane osobne tory zasilania i fizyczne odcięcia: [12 grup wyjściowych](output-potential-groups.csv).

## Niezależne obwody sprzętowe

[Tabela funkcji i sprzężeń z PLC](independent-hardware-functions.csv) zawiera 11 pozycji, w tym poniższe obwody.

| Funkcja | Realizacja w schemacie | Sygnał do PLC / skutek |
|---|---|---|
| Zatrzymanie awaryjne i „Sterowanie włączone” | A3.4 **PNOZ3 24 V DC**, strona 18; S93/S97, przyłącze X303:140/141, reset S90, pętla sprzężenia zwrotnego styczników. | E3.4; styki odcinają zasilanie grup A20, A22 oraz 11L+ napędów. |
| Drzwi serwisowe | A3.5 **PNOZ 24 V DC**, strona 19; S104…S107. | E3.5; odcięcie 11L+. Odręcznie dodano K19.14 i czujniki zabezpieczenia przed wykolejeniem. |
| Drzwi załadunku/rozładunku | A14.0 **PNOZ 24 V DC**, strona 20; S14.0. | E14.0; odcięcie 11L+. |
| Ogrzewanie stacji 4 | B8.3 i kaskada K18.0MF…K18.3MF, strona 21. | E8.3 monitoruje K18.3MF. Styki MF odcinają moc grzałek niezależnie od wyjść A18.0…A18.3. |
| Ogrzewanie RAV | K9.6A, B9.0/B9.01, B9.3/B9.31 oraz K18.4MF…K18.7MF, strona 22. | E9.0/E9.3 monitorują styczniki odcięcia; wyjścia A18.4…A18.7 sterują odrębnymi stycznikami procesu. |
| Wyciek | B5.0/K5.0A, strona 4. | E5.0 oraz fizyczne odcięcie grup A20/A22. |
| Suchobieg pompy P0 | Miernik mocy czynnej A3.2, strona 12. | E3.2 jest kontaktem monitora, nie analogowym pomiarem mocy w PLC. |

Przy migracji zachować rzeczywiste tory sprzętowe, reset i pętle sprzężenia zwrotnego. Wejście statusowe PLC nie zastępuje styków przekaźnika odcinającego. Zamówiony standardowy CPU S7-1513 obsłuży logikę procesu; przeniesienie funkcji PNOZ do samej zwykłej logiki CPU/HMI nie jest częścią tej migracji. Dokładne warianty PNOZ i stan instalacji wymagają odczytu oznaczeń. Nie wykonano oceny PL/SIL ani prób działania tych obwodów.

A17.7 nadal jest przekaźnikiem K17.7A i bezpotencjałowym kontaktem zakończenia czyszczenia X303:190/M. W komplecie 50 stron nie znaleziono sterowanego nim siłownika drzwi. Jeżeli kontakt jest wykorzystany w zewnętrznym układzie klienta, jego działanie trzeba ustalić po stronie tego układu; nie utożsamiać go z E14.0.

## Obwody mocy i wyjścia PLC

[Tabela 18 obwodów mocy](power-loads-and-PLC.csv) powiązała **32 wyjścia PLC** z odbiornikami, stycznikami i zabezpieczeniami. Przykłady odczytanych danych:

| Odbiornik | Moc / prąd narysowany w schemacie | Wyjścia sterujące stycznikami |
|---|---|---|
| Grzałki stacji 4 | 4 × 9 kW, po 13 A | A18.0…A18.3 |
| Grzałki RAV | 4 × 12 kW, po 17,3 A | A18.4…A18.7 |
| Transport pionowy | 0,63 / 2,5 kW; 3,0 / 6,5 A | A23.4…A23.7 |
| Silnik bębna | 0,9 kW, 2,1 A | A24.0/A24.1/A24.2 |
| Wentylator bębna | 0,11 kW, 0,45 A, trzy fazy | **A24.4 → %Q24.4** |

**Te prądy dotyczą silników i grzałek, nie cewek podłączonych do wyjść PLC.** Nie wpisano ich do kolumn obciążeń PLC. **14 października użytkownik poinformował, że nie dostarczy danych cewek, i podał typy 430/451/454.** [Wariant I/O S7](../hardware_review/DOBOR_IO_S7.md) zachowuje klasy 0,5 A i 2 A oraz wymagania grup; zgodność obciążeń indukcyjnych, sum prądów i temperatur trzeba potwierdzić dla wybranych modeli. Dane cewek nie będą ponownie zamawiane.

Hamulce Y23.0/Y23.4/Y24.0 są zasilane przez układy prostownicze i styki styczników kierunku/prędkości. Z tego schematu nie wynikają osobne wyjścia PLC do hamulców. R24.1, 150 Ω, jest bocznikowany przez K24.1M; zachować zależności istniejącego napędu. Odręczne zmiany połączeń bębna/hamulca na stronie 15 wymagają porównania z instalacją.

**Doprecyzowanie ultradźwięków:** strona 9 pokazuje zasilanie generatora 4 przez **K19.01M**. Na stronie 44 A19.1 zasila jego cewkę przez K19.0M:13–14, a kontakt K19.01M:13–14 zasila K19.1M sterowania zdalnego. K19.0M zasila generatory 1–3. Zachować cały tor i istniejące warunki A19.0/A19.1; uproszczenie „A19.1 to tylko sterowanie zdalne” pomija zasilanie generatora 4.

## Regulacja temperatury i odręczne dodatki

Temperaturą sterują zewnętrzne regulatory **A8.0/A8.2/A9.7 ST70.31.10** i **A8.4 ST70.31.02** (strony 23/24). Czujniki są podłączone do tych regulatorów; PLC otrzymuje kontakty E8.0/E8.2/E8.4/E9.7. Strona 24 rozstrzyga słabo czytelne oznaczenie A8.4 na stronie 33. Wariant migracji zachowujący tę regulację nie wymaga dodawania analogowych wejść do pomiaru tych temperatur. Nie ustalono typu samych czujników ani nie przenoszono regulatorów do PLC.

Strona 5 pokazuje tor mocy odręcznie dodanej pompy obiegowej stacji 2, z KM45.16/Q5.11/F5.12; odpowiada dopiskom ze stron 36/37/45. W tej dokumentacji nie wskazano jej nowego wyjścia PLC. Strona 19 pokazuje obwód „Wagensicherung / Entgleisung”, z połączeniem diodowym czujników oraz stykiem K19.14 w obwodzie A3.5. Zegar K-UHR występuje w dopiskach stron 25/28. **13 października użytkownik potwierdził: „Tak, wszystkie są zamontowane i działają”. Wszystkie trzy funkcje należą do zakresu migracji i mają zostać zachowane.** [Tabela potwierdzonych obwodów](confirmed-modifications.csv). Potwierdzenie dotyczy obecności i działania; szczegółowe trasy przewodów, warianty urządzeń i prądy cewek pozostają do ustalenia przy przygotowaniu docelowych połączeń.

Wentylator pozostaje na **%Q24.4** z warunkiem `A24.0 OR A24.2`, a lampka „Sterowanie włączone” na **%Q16.0** z `E1.2 OR E3.4`. Nowy materiał nie zmienia tej ustalonej decyzji. Aktualne fizyczne podłączenie wentylatora nadal wymaga sprawdzenia wobec dopisku A16.0 na stronie 49.

## Dane do następnego etapu

Nie brakuje stron schematu ani typów modułów I/O S5. Potrzebne pozostają końcowe modele S7 według kart producenta, oznaczenie/model G1, warianty PNOZ i szczegóły połączeń. Dobór na podstawie klas 451/454 pozwala kontynuować bez ponownego żądania danych cewek. Podany 454 potwierdził numerację zacisków producenta dla A25; błędy wydruku nadal są oznaczone osobno od rzeczywistych przewodów. Odbiornik A16.7 i adresy E119…E125/A112…A113 pozostają do wyjaśnienia.

Do prac nad projektem TIA pozostają także firmware nowej CPU po dostawie oraz dostępność STEP 7 Professional V19 i wybranego wariantu TP900 Comfort. DB15/DB19 i receptury 1/2 są zachowane. [Podsumowanie danych obwodów mocy](power-evidence.json), [generator](build_power_map.py) i [kontrola źródeł](schematic-artifact-checks.json). Nie zmieniono programu ani instalacji i nie wykonano kompilacji TIA.
