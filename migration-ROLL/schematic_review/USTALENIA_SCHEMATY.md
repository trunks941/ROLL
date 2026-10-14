# ROLL KS04201 — schematy i powiązanie z programem

Stan na **13 października 2026**. Pierwsze archiwum zawiera 26 fotografii stron **25–50** schematu KS04201, oznaczenie maszyny RET0120-080-056-04. Drugie archiwum uzupełniło **strony 1–24**, więc dostępny jest komplet 50 stron. [Analiza zasilania i blokad](ZASILANIE_BLOKADY.md) uzupełnia niniejszą mapę I/O. Wszystkie fotografie obejrzano ręcznie; OCR służył wyłącznie do wyszukiwania. Archiwa i zdjęcia zachowano bez zmian; [pochodzenie części 1](provenance.json), [części 2](provenance-part2.json), [indeks 50 stron](sheet-index.csv).

## Ustalenie dotyczące wentylatora

Zgodnie z ostatnią decyzją użytkownika wentylator bębna pozostaje na **A24.4 → %Q24.4**. Zachować warunek z PB13, sieć 44: **A24.0 OR A24.2**. Wyjście **A16.0 → %Q16.0** zachowuje lampkę „Steuerung Ein”, z warunkiem PB25, sieć 20: **E1.2 OR E3.4**; E1.2 jest testem lampek. [Tabela obu wyjść](fan-and-lamp-decision.csv).

Na stronie 49 cewka K24.4M jest przekreślona i opisana odręcznie „A16.0 / Steuerung Ein”. Ten dopisek pozostaje udokumentowaną rozbieżnością. Użytkownik nie potwierdził obecnego podłączenia wentylatora; docelowy wybór A24.4 jest ustalony. Wcześniejsza propozycja przeniesienia na A16.0 została zastąpiona tą decyzją. Nie zmieniono starego programu ani okablowania.

## Mapa wejść i wyjść

[Robocza mapa przewodów i kanałów](channel-wire-map-draft.csv) ma **208 wierszy**: 128 wejść E0…E15 i 80 wyjść A16…A25. Dla każdego kanału podaje stronę, numer zacisku narysowany dla S5, urządzenie/złącze, symbol programu, odwołania oraz propozycję adresu %I/%Q. Dla wyjść dołączono warunki zapisów z wcześniejszego porównania natywnych listingów, z zachowaniem kolejności autorów.

Na rysunkach znaleziono **83 ścieżki wejściowe** i **50 ścieżek wyjściowych**, w tym przyłącza opcji i mostków. To liczby narysowanych połączeń, nie niezależnie sprawdzonych odbiorników. Narysowany zacisk S5 nie jest numerem zacisku S7; kolumny docelowych MLFB, zacisków i sprawdzonych przewodów pozostają puste do doboru sprzętu.

| Rozbieżność | Ustalenie |
|---|---|
| E4.6 | Narysowany zacisk rezerwowy X303:181; brak znalezionego zwykłego odwołania w kodzie. |
| E6.6 | Narysowany poziom MIN zbiornika VE; brak znalezionego zwykłego odwołania w kodzie. |
| A16.7 | Program używa tego wyjścia, ale strona 41 nie pokazuje odbiornika. |
| E2.0 | Numer zacisku X31 jest słabo czytelny; zaznaczono granicę odczytu. Oznaczenie regulatora A8.4 rozstrzyga otrzymana strona 24. |
| A25.0…A25.7 | Strona 50 ma niespójną numerację zacisków; osiem przypisań pozostaje wstrzymanych. |

E6.7 jest poziomem TGS zbiornika VE zarówno na rysunku, jak i w komentarzu symbolu B6.5_3 oraz alarmie PB2, sieć 27. Odrębny MIN znajduje się na E6.6; nie należy łączyć tych sygnałów.

Pełne [zestawienie rozbieżności](drawing-code-discrepancies.csv) obejmuje także dopisek wentylatora. Brak odwołania w kodzie lub połączenia na rysunku nie rozstrzyga, czy kanał można usunąć. Adresy **E119…E125 i A112…A113** nadal pozostają poza zakresem otrzymanych stron i etykiet kasety; [28 odwołań poza zdjęciem](../hardware_review/addresses-outside-photo.csv) nie otrzymało dodatkowych fizycznych kanałów S7. Użytkownik potwierdził, że zdjęcie obejmuje cały zestaw modułów.

## Zasilanie grup i obwody wykonawcze

Rysunki pokazują wejścia zasilane z **5L+** (E0…E7, F4.1, 2 A) i **6L+** (E8…E15, F4.11, 2 A). Wyjścia są rozdzielone na grupy potencjałowe: [12 grup wyjściowych](output-potential-groups.csv).

| Wyjścia | Zasilanie narysowane w schemacie |
|---|---|
| A16…A19 | 7L+, F4.2 6 A. |
| A20 | 9L+, F4.21 6 A; styki A3.4:23–24 i K5.0A:23–24 przed L+ grupy. |
| A21 | 9L+ z tej samej gałęzi, odrębne przyłącze L+ bez powyższych styków A20. |
| A22 | 9L+; styki A3.4:33–34 i K5.0A:33–34 przed L+ grupy. |
| A23, A24, A25 | 11L+, F4.22 6 A; styki A3.4:43–44, A3.5:23–24 i A14.0:23–24. A24/A25 mają po dwie grupy czterokanałowe w wariancie referencyjnym. |

Dobór S7 musi umożliwiać zachowanie tych osobnych torów zasilania i fizycznych odcięć. Sama wspólna wartość 24 V nie uzasadnia łączenia grup. W szczególności A20/A21/A22 mają różne tory zasilania na jednym starym module.

Ruch góra/dół ma fizyczne styki przekaźników krańcowych K12.0A/K12.6A oraz przeciwnego stycznika w obwodach A23.4/A23.5. Pozostałe pary kierunków/prędkości również mają blokady stycznikowe; A24.0/A24.2 i A17.2/A17.3 są blokowane sprzętowo. Te obwody trzeba przenieść wraz z instalacją. Odczyt E12.0/E12.6 przez PLC nie zastępuje styków odcinających cewki.

Wyjścia sterują cewkami styczników/przekaźników 24 V, zaworami i sygnalizacją. Prądy znamionowe i prądy załączania cewek nie są określone w dostarczonych stronach. Przed wskazaniem końcowych MLFB trzeba sprawdzić obciążenia oraz limity kanałów i grup. Etykieta starego modułu 2 A nie jest pomiarem odbiornika.

A17.7 steruje przekaźnikiem K17.7A i bezpotencjałowym kontaktem zakończenia czyszczenia do klienta, X303:190/M. Potwierdza to dotychczasową analizę programu; nie jest pomiarem położenia drzwi.

## Odręczne zmiany oraz zaciski A25

Strony 25/28 zawierają dopiski K-UHR związane z zegarem E3.1 i AUTO E0.2, z datą 31.3.05. Strony 36/37/45 dokumentują dodatkowy czujnik pozycji, diodę 1N4007, przekaźnik K3605 i dodatkowy obwód pompy kąpieli 2 (HQA, S4515/S4516, Q5.11, KM45.16, H4514). Strona 5 drugiej części pokazuje tor mocy tej pompy. Użytkownik potwierdził, że pompa stacji 2, zabezpieczenie przed wykolejeniem K19.14 ze strony 19 i zegar K-UHR są zamontowane i działają; zachować wszystkie trzy funkcje. Z obwodu pompy **nie wyprowadzono nowego wyjścia PLC**. Szczegółowe połączenia dopisków nadal wymagają sprawdzenia przy przygotowaniu docelowych zacisków.

Strona 49 podaje dla A24 zaciski 3, 5, 7, 9, 15, 17, 19, 21. Strona 50 podaje dla A25 kolejno 27…34 oraz dwukrotnie M=47. Instrukcja producenta [6ES5_998-0UF23.pdf](../reference_manuals/6ES5_998-0UF23.pdf), **strona PDF 563, drukowana 15-35**, dla wariantu **6ES5 454-7LA12, 16 × 24 V DC / 2 A**, pokazuje A25 na 27, 29, 31, 33, 39, 41, 43, 45 oraz M=35/47. Dla tego wariantu limit sumy prądów wynosi 4 A na grupę czterech wyjść. 14 października użytkownik potwierdził typ 6ES5 454-7LA12; podane numery zacisków producenta i limit 4 A/grupę dotyczą tego typu. Nie wykonano niezależnego sprawdzenia rzeczywistych przewodów. W tabeli zachowano literalne numery z rysunku i oznaczono je jako wstrzymane; nie zastąpiono ich po cichu numerami z instrukcji.

## Następne materiały

Komplet stron **1–50 jest otrzymany i przeanalizowany**. Potrzebne pozostają końcowe modele S7 i modele G1/PNOZ oraz sprawdzenie szczegółów połączeń. Nie potrzeba ponawiać schematów. Aktualne wnioski z torów mocy, sterowania i pochodzenia przekaźników zawiera [analiza drugiej części](ZASILANIE_BLOKADY.md).

[Obserwacje źródłowe](manual-observations.json), [generator](build_schematic_map.py), [kontrola tabel](schematic-evidence.json) oraz [sprawdzenie źródeł i odnośników](schematic-artifact-checks.json) pozwalają odtworzyć zestawienia. Są to wyniki analizy offline; nie powstała jeszcze skompilowana konfiguracja TIA ani sprawdzony plan przełączenia przewodów.
