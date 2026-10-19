# Pierwszy import ekranów TP900 do kopii projektu

Paczka zawiera **5 ekranów, 53 tagi i 137 obiektów**, wygenerowanych na podstawie rzeczywistego XML z Twojego TP900. Polskie napisy zachowują aktywną kulturę `en-US` ze wzoru, żeby import nie wymagał wcześniejszego włączania dodatkowego języka. Język okien systemowych Runtime można ustawić osobno.

To wersja do sprawdzenia importu i kompilacji w lokalnym **TIA V19 / WinCC Advanced**. W chmurze sprawdzono odwołania, geometrię, typy tagów i skrypt importu z atrapami API. Natywny importer i kompilator WinCC muszą ją jeszcze zaakceptować.

**Poprawka po raporcie z 19.10, godz. 07:08:** archiwizacja, odtworzenie kopii, import tabeli tagów i pięciu pustych ekranów przeszły w TIA. Pierwszy pełny ekran został odrzucony: lampka o wymiarach 20×20 zachowała `Radius=24` ze wzoru, zamiast wymaganego `10`. Generator poprawia teraz wszystkie 15 lampek, a importer sprawdza tę zależność przed połączeniem z TIA. Dodano zapis kopii przed importem i po każdej ukończonej kategorii; raport zachowuje jej ścieżkę oraz nazwę aktualnie importowanego pliku także przy błędzie. Poprawiony import pełnych ekranów i kompilacja wymagają następnej próby w TIA.

Po poprzednim błędzie sesja TIA została unieważniona i zapis kopii nie powiódł się. Jeśli TIA się zamknęło, uruchom je ponownie. Otwórz **pierwotny projekt z `WZOR_ROLL`**, spoza katalogów `ROLL_HMI_IMPORT_…\project-copy`. Częściowa kopia może już zawierać tagi i puste ekrany; importer celowo odrzuci ich nadpisanie. Nie trzeba odtwarzać wzoru ani zmieniać widoku alarmów.

## Co uruchomić teraz

1. Pobierz aktualny `TIA_ROLL_V19.zip` i rozpakuj do nowego katalogu. Zachowaj cały podkatalog `tia-v19`.
2. W TIA V19 otwórz **dotychczasowy projekt `ROLL_20261015_120907_bfeaa0` z ekranem `WZOR_ROLL`**, widokiem alarmów i połączeniem `ROLL_PLC`. Zapisz go i pozostaw otwarty.
3. Uruchom **`tia-v19\IMPORTUJ_HMI.cmd`**. Gdy TIA zapyta o dostęp Openness, zezwól temu lokalnemu skryptowi. Przy kilku otwartych projektach wybierz właściwy numer w konsoli.
4. Skrypt sprawdzi pliki importu, geometrię lampek i kolizje nazw, utworzy archiwum `.zap19`, zamknie zapisane źródło i odtworzy **oddzielną kopię** w `Dokumenty\ROLL_TIA_V19\ROLL_HMI_IMPORT_…\project-copy`. Zapisze ją przed importem, następnie zaimportuje tagi, puste ekrany i ich zawartość, zapisując każdy ukończony etap. Uruchomi kompilator HMI oraz zapisze wynik. Poczekaj na wynik w konsoli.
5. **Prześlij `ROLL_HMI_IMPORT_…_raport.zip`.** Pełne archiwum projektu i `.ap19` pozostają na Twoim komputerze; paczka raportu zawiera JSON i dostępne eksporty nowych ekranów.

Jeżeli TIA zgłasza niezapisane zmiany, zapisz projekt przed uruchomieniem. Importer blokuje edycję GUI na czas pracy przez standardowy dostęp wyłączny Openness. Nie uruchamiaj go na projekcie zawierającym już ekrany `ROLL_*` z tej paczki: pierwsza wersja celowo odmawia nadpisywania istniejących ekranów i kolidujących tagów.

`UTWORZ_PROJEKT.cmd` nadal tworzy projekt od początku. **Na obecnym etapie potrzebny jest `IMPORTUJ_HMI.cmd`.**

## Co zobaczysz

W `ROLL_TP900 → Screens` pojawią się:

| Ekran | Zawartość |
|---|---|
| `ROLL_Przeglad` | aktywny program, dwa czasy procesu, połączenie, tryb ręczny i stan konfiguracji I/O |
| `ROLL_Receptury` | dwa numery programów, dziesięć pól receptury, jednostki i tryby bębna 0–4 |
| `ROLL_Reczny` | 14 potwierdzonych funkcji ręcznych oraz dwa przyciski pozycji podstawowej/roboczej |
| `ROLL_Alarmy` | diagnostyka i przejście do istniejącego `WZOR_ROLL` z widokiem alarmów |
| `ROLL_Nastawy` | wybór DB15/DB19 i indeksu, odczyt bieżącej wartości, pole nowej wartości i wynik polecenia |

Ekrany mają numery 101–105 i pasek nawigacji. Niemieckie opisy funkcji ręcznych zachowano pomocniczo w HelpText przycisków. Przed przejściem do innego ekranu zdarzenie zeruje obie komendy przytrzymania. Przyciski wyboru funkcji ręcznej również najpierw je zerują. Formaty zdarzeń przejścia i stałych wartości wymagają potwierdzenia przez lokalny V19; wykorzystano dodatkowo jawnie opisane odniesienie do publicznego przykładu V17. Szczegóły są w `hmi/native/manifest.json`.

**Podgląd układu:** otwórz `PODGLAD_HMI.html` w przeglądarce. Górne przyciski przełączają makiety. Ten plik nie łączy się z PLC i nie symuluje procesu ani komunikacji WinCC.

## Po udanym imporcie

Otwórz nowe ekrany w edytorze i sprawdź także `WZOR_ROLL` w kopii projektu: kontrolka alarmów powinna pozostać dzięki odtworzeniu pełnego archiwum, a nie dzięki XML. Raport potwierdza obecność oryginalnego ekranu; samej kontrolki nie da się zweryfikować dotychczasowym eksportem.

Przed próbą Runtime ustaw **Runtime settings → General → Start screen = ROLL_Przeglad** w nowej kopii. Do czasu przeniesienia alarm view do docelowego ekranu warto skopiować przycisk **Przegląd** z górnego paska nowego ekranu do `WZOR_ROLL` przez Ctrl+C/Ctrl+V. Zachowa gotowe zdarzenie powrotu. Pozwoli to wrócić z istniejącego widoku alarmów do nowych ekranów. Te ustawienia dotyczą kopii; zachowaj źródłowe archiwum.

## Co jest celowo zablokowane

Wszystkie polecenia operatorskie i edycja pól nowych ekranów są wyłączone w tej wersji. Aktywna jest nawigacja i odczyty. Dotyczy to również wyboru funkcji ręcznej, wyboru programu oraz opcji receptury: nie przedstawiamy ich jako gotowej obsługi procesu przed potwierdzeniem komunikacji i transakcji. PLC, jego konfiguracja sprzętowa i zabezpieczenia nie są modyfikowane przez importer.

Kolejny krok po poprawnym imporcie obejmuje globalny heartbeat, potwierdzenie dotarcia całego zestawu edytowanych danych do PLC przed wysłaniem żądania, obsługę odpowiedzi i błędów oraz zwalnianie komend ruchu po zmianie widoku/utracie komunikacji. Samo kolejne wywołanie funkcji zapisu tagów HMI nie daje jeszcze takiego potwierdzenia. Dlatego ta paczka nie przedstawia zapisu receptur jako gotowej funkcji operatorskiej.

Pełne definicje alarmów maszyny, ich tłumaczenia i potwierdzanie również wymagają osobnego powiązania z programem. Obecny `Alarm view` jest zachowany w kopii całego projektu, mimo że nie pojawia się w eksporcie XML ekranu. Nie trzeba go ponownie eksportować ani dodawać.

## Dalsze ustawienie heartbeat — po potwierdzeniu importu

Paczka zawiera przygotowaną treść `hmi/heartbeat/ROLL_HeartbeatTick.vbs`. Docelowe wywołanie korzysta z tagu `ROLL_Clock`, który odczytuje `ROLL_HMI.StatusM[3,5]`: ten bit PLC zmienia się co 500 ms. Cykl odczytu 100 ms ogranicza możliwość pominięcia jego przełączeń. W TIA trzeba będzie ustawić dla tego tagu **Cyclic continuous / Cyklicznie ciągle** i powiązać jego zdarzenie **Value change** z bezparametrowym skryptem. Skrypt zwiększa `ROLL_Heartbeat`, a PLC nadzoruje odstęp 1,5 s. Wymaga to lokalnej konfiguracji i testu komunikacji; samo umieszczenie pliku VBS w paczce nie instaluje zdarzenia w panelu.

Po otrzymaniu wyniku importu ustawienia te oraz transakcje zostaną dopracowane w kolejnej wersji. Wyjścia fizyczne oraz tryb symulacji nadal podlegają istniejącym blokadom programu i wymaganiom uruchomienia maszyny.
