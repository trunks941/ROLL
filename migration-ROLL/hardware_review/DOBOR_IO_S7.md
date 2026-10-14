# ROLL — wariant I/O S7 na podstawie potwierdzonych modułów S5

Aktualizacja **14 października 2026**. Użytkownik podał trzy MLFB i poinformował, że nie dostarczy danych obciążeń cewek. [Zapis identyfikacji i uzgodnionej podstawy doboru](module-identification.json). Dane cewek nie będą ponownie zamawiane; wariant zachowuje klasy prądowe i tory odcięcia istniejących modułów. Oznaczenie stycznika **9 A** opisuje obciążalność styków mocy. Nie wpisano go jako prądu cewki ani obciążenia PLC.

## Potwierdzony zestaw S5

| Typ | Ilość wynikająca ze zdjęcia | Parametry z instrukcji | Adresy |
|---|---:|---|---|
| **6ES5 430-7LA12** | 4 | 32 DI, 24 V DC, izolowane grupy po 8 | E0…E15 |
| **6ES5 451-7LA12** | 2 | 32 DQ, 24 V DC, 0,5 A/kanał, grupy po 8 | A16…A23 |
| **6ES5 454-7LA12** | 1 | 16 DQ, 24 V DC, 2 A/kanał, grupy po 4; maks. 4 A/grupę | A24…A25 |

Podstawa: użytkownik, zdjęcie całej kasety i [instrukcja S5](../reference_manuals/6ES5_998-0UF23.pdf), strony PDF **549 / 560 / 563**, drukowane **15-21 / 15-32 / 15-35**. Przypisanie typów do pozycji wynika z jednoznacznego dopasowania rodzaju, liczby kanałów i klasy prądowej widocznych kart. Przełączników adresowych ani szczegółowych przewodów nie sprawdzono.

Dla 451 instrukcja podaje dopuszczalny sumaryczny prąd 100% przy 25°C i 50% przy 55°C. Dla 454 suma na cztery kanały wynosi 50% sumy prądów nominalnych, czyli **4 A**. Podaje też ograniczenie napięcia indukowanego przy wyłączeniu −15 V oraz częstotliwość przełączania obciążeń indukcyjnych maks. 0,5 Hz / 0,27 Hz. Nowe moduły trzeba dopasować również do tych właściwości; sam prąd jednego kanału nie wyznacza pełnej zgodności.

## Wariant docelowy

| Proponowana grupa | Liczba modułów | Łączna pojemność | Proponowane adresy |
|---|---:|---:|---|
| SM 521, DI32 / 24 V DC | 4 | 128 DI | %I0…%I15 |
| SM 522, DQ16 / 24 V DC / 0,5 A | 4 | 64 DQ | %Q16…%Q23 |
| SM 522, DQ8 / 24 V DC / 2 A | 2 | 16 DQ | %Q24…%Q25 |

To **wariant budowy z 10 modułami I/O**, wymagający potwierdzenia parametrów konkretnych modeli w kartach producenta. Nie jest ostateczną listą zakupową. [Rozmieszczenie modułów](S7-IO-layout-variant.csv), [przypisanie 208 kanałów](S7-channel-assignment-variant.csv), [wymagane tory zasilania](S7-output-supply-assignment.csv). Końcowe MLFB i numery zacisków S7 pozostają puste do tej weryfikacji. Nie zmniejszono wyjść starego 454 z 2 A do 0,5 A.

**Wentylator pozostaje na %Q24.4**, z dotychczasowym warunkiem `A24.0 OR A24.2`. **Lampka pozostaje na %Q16.0**, z `E1.2 OR E3.4`. Nie zmieniono warunków ani kolejności zapisów w programie S5.

## Grupy potencjałowe i obciążalność

Dla czterech kandydatów DQ16 wymagane są **dwie niezależnie zasilane sekcje po 8 kanałów**. Dzięki temu można zachować:

- %Q16/%Q17 i %Q18/%Q19: zasilanie 7L+.
- %Q20: 9L+ przez styki A3.4 i K5.0A; %Q21: osobna sekcja 9L+.
- %Q22: 9L+ przez inne styki A3.4 i K5.0A; %Q23: 11L+ przez styki zatrzymania awaryjnego i drzwi.

Wariant z DQ32 trzeba oceniać według rzeczywistej liczby niezależnych grup, nie samej liczby kanałów. Nie wolno wspólnym przyłączem L+ połączyć sekcji mających różne fizyczne tory odcięcia. Model DQ16 bez wymaganej niezależności również nie spełni tego wariantu.

Dla %Q24 i %Q25 stare połówki bajtów mają ten sam tor 11L+ i wspólny M. Można rozważyć większą grupę nowego modułu, jeżeli zachowuje ten tor i obejmuje **sumę dwóch dotychczasowych limitów po 4 A**, czyli 8 A na osiem kanałów, przy projektowej temperaturze i ułożeniu modułów. W przeciwnym razie trzeba zachować równoważne osobne sekcje. W żadnym przypadku nominalne „2 A/kanał” nie zastępuje sprawdzenia sumy prądów.

Podstawą doboru jest założenie projektowe, że obecne obciążenia pracują w limitach potwierdzonych modułów S5. To nie pomiar cewek ani wynik próby elektrycznej. Weryfikacja kart nowych modułów obejmuje typ obciążenia indukcyjnego, sumy prądów, temperaturę, zabezpieczenia i sposób tłumienia energii przy wyłączeniu. Nie oparto doboru na deklaracji, że wszystkie cewki mają konkretny niski prąd. Parametry wejść oraz czas reakcji także wymagają dopasowania; stary 430 ma opóźnienie narastania do 5,5 ms i zaniku do 5 ms.

PNOZ, odcięcia MF ogrzewania, hamulce przez styczniki oraz potwierdzone przez użytkownika pompa stacji 2, K19.14 i K-UHR pozostają w zakresie migracji. Dokładne warianty G1/PNOZ i połączenia należy uwzględnić w końcowym projekcie. Projekt TIA ani instalacja nie zostały zmienione.

## Rozbieżność A25 i dostęp do katalogu S7

Podany MLFB 454 potwierdza właściwą numerację zacisków producenta. Dla A25 są to **27, 29, 31, 33, 39, 41, 43, 45**, z M=35/47. Błędnych numerów 27…34 i podwójnego M=47 z rysunku strony 50 nie użyto jako sprawdzonych połączeń. Aktualna [mapa ze schematami](../schematic_review/channel-wire-map-draft.csv) zachowuje osobno numery wydrukowane i numery producenta. To zaciski S5; nie są numerami złącza S7.

Próba odczytu katalogu `mall.industry.siemens.com` przez obowiązujący proxy zakończyła się odmową **CONNECT HTTP 403**. Oficjalne dane kandydatów S7 nie zostały w tej sesji pobrane. Zapisano do przeglądu w ustawieniach środowiska dodanie domen `mall.industry.siemens.com`, `support.industry.siemens.com` i `sieportal.siemens.com`, zachowując pozostałą konfigurację. Zapis projektu ustawień wymaga publikacji i sam nie zmienia bieżącego dostępu. Nie omijano polityki sieci.

[Podsumowanie wariantu](S7-IO-variant-evidence.json), [generator](build_S7_IO_variant.py) i [kontrola źródeł i tabel](../schematic_review/schematic-artifact-checks.json). Po udostępnieniu katalogu można wybrać końcowe MLFB i zatwierdzić grupy/zaciski w TIA V19; to nie wymaga ponownego żądania danych cewek od użytkownika.
