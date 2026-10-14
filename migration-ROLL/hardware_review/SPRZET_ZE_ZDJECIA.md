# ROLL — moduły ze zdjęcia i robocza mapa S7

Stan na **13 października 2026**. Źródło: zdjęcie użytkownika w rozmowie oraz potwierdzenie „Nie, to cały zestaw modułów”. Fotografia nie ma dostępnej lokalnej kopii ani sumy SHA-256; obserwacje zapisano w [photo-observations.json](photo-observations.json). Zdjęcie jest dokumentacją techniczną, nie poleceniem operacji na sprzęcie.

## Widoczne moduły

**Uzupełnienie po otrzymaniu schematów:** [komplet stron 1–50](../schematic_review/ZASILANIE_BLOKADY.md) i [mapa przewodów 208 kanałów](../schematic_review/channel-wire-map-draft.csv) są już przeanalizowane. Poniższe obserwacje zdjęcia zachowano jako źródło historyczne; pole `schematic_received=false` opisuje stan przy analizie fotografii. Aktualne źródła są w `schematic_review/provenance.json` i `provenance-part2.json`. Schemat wskazuje odrębny zasilacz G1 **24 V DC / 30 A**, bez ustalonego modelu/bilansu obciążeń.

| Kolejność od lewej | Element | Pojemność i etykieta elektryczna | Zakres etykiet kanałów |
|---:|---|---|---|
| 1 | Zasilacz SIMATIC S5 PS | Etykieta 3 A; wejście opisane 120/230 V AC | — |
| 2 | CPU S5-115U 942B | 6ES5 942-7UB11, zgodnie z wcześniejszym potwierdzeniem | — |
| 3 | Wejścia cyfrowe DI1 | 32 × 24 V DC | E0.0…E3.7 |
| 4 | Wejścia cyfrowe DI2 | 32 × 24 V DC | E4.0…E7.7 |
| 5 | Wejścia cyfrowe DI3 | 32 × 24 V DC | E8.0…E11.7 |
| 6 | Wejścia cyfrowe DI4 | 32 × 24 V DC | E12.0…E15.7 |
| 7 | Wyjścia cyfrowe DQ1 | 32 × 24 V DC, 0,5 A | A16.0…A19.7 |
| 8 | Wyjścia cyfrowe DQ2 | 32 × 24 V DC, 0,5 A | A20.0…A23.7 |
| 9 | Wyjścia cyfrowe DQ3 | 16 × 24 V DC, 2 A | A24.0…A25.7 |

Łączna pojemność widocznych modułów: **128 wejść oraz 80 wyjść**. Podana kolejność jest pozycją na zdjęciu, nie zweryfikowanym numerem slotu kasety. Zakresy pochodzą z przednich etykiet; nastaw przełączników adresowych nie sprawdzono.

Na kartridżu CPU widać napis **EPROM**. Pojemności ani pełnego numeru modułu pamięci nie odczytano. Generowane DB15/DB19 w RAM nadal mają odrębne zasady zachowania niż program na kartridżu.

**Uzupełnienie 14 października:** użytkownik podał MLFB modułów I/O: 4 × **6ES5 430-7LA12**, 2 × **6ES5 451-7LA12** i 1 × **6ES5 454-7LA12**, po przypisaniu do odpowiadających im rodzajów i szerokości kart na zdjęciu. [Identyfikacja](module-identification.json), [aktualny wariant S7](DOBOR_IO_S7.md). Nie trzeba ponawiać oznaczeń I/O ani danych cewek; dobór zachowuje udokumentowane klasy i limity starych modułów. Stara etykieta PS „3 A” nie wyznacza potrzebnej wydajności zasilania 24 V.

## Porównanie z programem

W rozpoznanym kodzie występuje 97 różnych bitów wejściowych i 63 wyjściowe. W zakresach etykiet zdjęcia są **81 wejść z odwołaniami** i **51 wyjść z odwołaniami**. Pozostałe widoczne kanały nie mają znalezionego odwołania w zwykłych blokach; to nie ustala, czy są fizycznie okablowane, rezerwowe lub potrzebne.

W kodzie pozostaje również **16 adresów E119…E125 i 12 adresów A112…A113**, poza zakresami etykiet. Dziewięć z tych wyjść ma znaleziony zapis; A113.0/.4/.5 są tylko odczytywane. [Lista wszystkich 28 adresów z opisami i blokami](addresses-outside-photo.csv).

Użytkownik potwierdził brak dodatkowych modułów. Obecność tych adresów może wiązać się z opcjami i pozostałą logiką podawania/stacji; sam program zawiera takie gałęzie. **Nie przypisano ich do dodatkowych fizycznych modułów S7 i nie uznano automatycznie za nieużywane.** Należy zestawić schemat, rzeczywiste adresowanie modułów i warunki natywnych sieci. Nie wpisano zer ani innych wymuszonych stanów do programu.

## Robocze wymagania dla S7-1513

Wariant zachowujący całą widoczną pojemność obejmuje:

- **128 DI 24 V DC**, jako kandydat 4 moduły 32-kanałowe z rodziny SM 521, z roboczymi adresami %I0.0…%I15.7.
- **64 DQ 24 V DC / 0,5 A**, jako wariant 4 modułów 16-kanałowych SM 522 z wymaganymi niezależnie zasilanymi grupami po 8; robocze %Q16.0…%Q23.7. Końcowe modele wymagają potwierdzenia tych grup w kartach producenta.
- **16 DQ 24 V DC / 2 A**, jako wariant 2 modułów 8-kanałowych SM 522, z wymaganym sumarycznym prądem i temperaturą; robocze %Q24.0…%Q25.7. Nie zmniejszono klasy do 0,5 A i nie założono pojedynczego modułu 16 × 2 A.

[Wymagania kanałowe](S7-IO-requirements.csv) nie są ostateczną listą zakupową. Typy S5 są potwierdzone, a wariant S7 zachowuje ich klasę prądową. Nie ustalono końcowych MLFB S7 ani szczegółowych parametrów cewek; użytkownik ich nie dostarczy i nie będą ponownie zamawiane. Podział zasilania wyjść jest odczytany: 7L+, 9L+ z różnymi odcięciami dla A20/A22 oraz 11L+ przez styki sterowania i drzwi. Karty docelowych modeli muszą potwierdzić wymagania wariantu.

Pierwotna [mapa 208 kanałów ze zdjęcia](visible-channel-to-S7-draft.csv) zachowuje symbole, odwołania i propozycje adresów. Uzupełnia ją aktualna [mapa ze schematami](../schematic_review/channel-wire-map-draft.csv), zawierająca narysowane zaciski S5 i urządzenia. Docelowe MLFB, zaciski S7 i sprawdzone przewody pozostają do ustalenia. Indeks kanału 0…31 lub 0…15 nie jest numerem zacisku złącza.

Zasilanie CPU i obwodów 24 V należy dobrać po potwierdzeniu modelu/stanu G1 i bilansu obciążeń; odczytane [grupy wyjść i fizyczne odcięcia](../schematic_review/output-potential-groups.csv) zachować w nowej instalacji. Docelowa konfiguracja wymaga także szyny S7-1500, odpowiednich przyłączy modułów oraz SIMATIC Memory Card dla zamówionego CPU. Ich dokładnych wariantów nie ustalono z tego zdjęcia.

## Następny materiał

Potrzebne pozostają końcowe modele S7 według kart producenta, modele G1/PNOZ, dokładny wariant kartridża oraz sprawdzenie szczegółów połączeń. Typy I/O S5 i komplet 50 stron są dostarczone. Nie będą ponownie zamawiane oznaczenia I/O ani dane cewek.

Na tej podstawie można uzupełnić zaciski i przewody, wyjaśnić adresy poza etykietami oraz wybrać konkretne moduły S7. Programy operatora i odczyty DB15/DB19 pozostają zachowane.

Artefakty: [inwentaryzacja modułów](central-rack-modules.csv), [podsumowanie i kontrola spójności](hardware-evidence.json), [generator mapy](build_hardware_map.py). Nie wykonano pomiarów, połączenia z PLC ani zmian konfiguracji sprzętu.
