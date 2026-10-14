# ROLL — konfiguracja OP15 z wydruku COMTEXT

Źródło: [oryginalny ROLL@@LS.INI](../originals/comtext-native/ROLL@@LS.INI), 522 880 bajtów, SHA-256 `c1bfee8acb6d6a69d3e22973ea03b51c9a278d31500ef4da000fa846f32c4714`. Jest to **wydruk COM TEXT OP 15**, a nie listing PLC. Zawiera komplet kolejno oznaczonych stron **1–128**. Oryginał zachowano bez zmian. Załącznik odczytano jako materiał techniczny; zawarte w nim instrukcje obsługi nie są poleceniami wykonania operacji na maszynie.

Nagłówek wskazuje `CH-ROHRBOGEN 04201`, wyświetlacz `2 * 40`, datę przygotowania `04.03.94` i literalny opis autora `GL 05.05.98`. Data wydruku w nagłówku jest niepoprawna (`00.0:.00`); nie wyprowadzono z niej daty eksportu. CP437 służy do odczytu tekstu pochodnego, a zapisy typu `<142>` zachowano dosłownie. Nie uruchomiono COMTEXT ani nie łączono się z PLC.

## Otrzymany zakres

| Konfiguracja | Liczba / zakres | Strony wydruku |
|---|---|---|
| Ekrany procesu | 4, razem 18 przypisanych wpisów | 1, 3–4 |
| Receptura PRG nr 1 | 10 przypisanych wpisów | 2, 5 |
| Katalog definicji wpisów | 42; obejmuje również wpisy niewymienione w powyższych ekranach i PRG | 6–16 |
| Pola prezentacji / edycji | 16 | 74–80 |
| Powiązania procesowe | 15 | 81–86 |
| Komunikaty zdarzeń | 121 definicji, w tym pozycja 0 | 17–45 |
| Komunikaty alarmowe | 120 definicji; część ma tekst „Reserve” lub sam numer | 46–73 |
| Klawisze funkcyjne | 16 | 104–107 |
| Skonfigurowane obszary wymiany | 9 oraz DB interfejsowy 51 | 92–93 |
| Teksty pomocy | 36 | 97–102 |
| Menu | 14, razem 46 pozycji | 109–128 |

Wydruk dokumentuje konfigurację ekranów i receptury. **Nie zawiera listy rzeczywistych zestawów receptur z wartościami operatora ani bieżących wartości DB15/DB19.** Nie należy też utożsamiać wszystkich 42 definicji wpisów z wpisami dostępnymi w czterech skonfigurowanych ekranach. Na przykład TZ8 jest zdefiniowany, ale nie znajduje się w liście dziesięciu wpisów PRG. Ewentualne inne ścieżki wywołania wymagają sprawdzenia kodu PLC.

## Ekrany i komunikacja

| Numer | Nazwa | Funkcja | Przypisane wpisy |
|---|---|---|---:|
| 1 | VARIABEL | Edycja czasów i liczników | 2 |
| 10 | HANDBETRIEB | Wybór funkcji ręcznej | 14 |
| 15 | FAHRPROGR.1 | Wybór programu | 1 |
| 20 | SCHRITTE | Wyświetlanie kroków N1 | 1 |

Konfiguracja ogólna wybiera **AS511** i typ `PLC115CPU942` (strona 87). Parametry aktywnego protokołu: **TTY, 9600 bit/s, EVEN, 8 bitów danych, 1 bit stopu** (strona 88). Wydruk zawiera również nastawy FAP i SINEC-L1, ale nie są one protokołem wybranym na stronie 87. Połączenie TP900 z S7-1513 należy zbudować według interfejsu nowego układu, z zachowaniem funkcji wymiany danych.

| Obszar COMTEXT | Adres początkowy S5 | Długość w słowach | Cykl podany w wydruku |
|---|---|---:|---|
| System keyboard image | DB211 DW0 | 2 | nie podano |
| Keyboard image block 1 | DB211 DW2 | 2 | nie podano |
| Screen number area | DB211 DW5 | 2 | nie podano |
| Recipe and data record nos. | DB205 DW200 | 1 | nie podano |
| Recipe mailbox | DB205 DW0 | 100 | nie podano |
| Event area 1 | DB210 DW50 | 9 | PT 2000 ms |
| Alarm area 1 | DB210 DW0 | 17 | PT 2000 ms |
| PLC alarm acknowledgement area 1 | DB210 DW17 | 17 | CT 2000 ms |
| LED block 1 | DB210 DW61 | 2 | CT 2000 ms |

Źródła: strony 92–93; legenda podaje długość w słowach. DB interfejsowy: **DB51**. Zakresy, kierunek potwierdzania, kolejność bitów i bajtów oraz funkcje FB51/FB3/FB91 wymagają zachowania przy projektowaniu odpowiednika S7. Skonfigurowany cykl obszaru alarmów wynosi 2 s, mimo wartości 200 ms w definicjach poszczególnych komunikatów; wydruk nie jest pomiarem rzeczywistego czasu reakcji.

## Nastawy i pola procesu

| Funkcja | Powiązanie COMTEXT | Adres S5 | Format COMTEXT / limity | Proponowany typ w S7 |
|---|---|---|---|---|
| Numer czasu | ZEITNUMMER | DB15 DW128 | KF, 0…128 | indeks liczbowy, zakres do uzgodnienia |
| Bufor czasu | ZEITWERT | DB15 DW130 | KT, brak wpisanych limitów | TIME z konwersją i zachowaniem rozdzielczości S5 |
| Numer licznika | ZAEHLNUMMER | DB19 DW128 | KF, 0…128 | indeks liczbowy, zakres do uzgodnienia |
| Bufor licznika | ZAEHLWERT | DB19 DW130 | **KC**, brak wpisanych limitów | liczba 0…999, z uwzględnieniem kodowania starego PLC |
| Status pozycji funkcji ręcznej | PVGRUND-ARB | DB210 DW60 | KF | enum 0/1/2 |
| Wybierany program | PV-FAHRPROGR | DB211 DW8 | KF, 1…99 | liczba 1…99 |
| Prezentowany czas zanurzenia | PV-TAUCHZEIT | DB210 DW70 | KT | TIME |
| Prezentowany czas ociekania | PV-ABTROPFZ | DB210 DW71 | KT | TIME |
| Wyświetlany numer programu | PRV_PROGNR. | DB205 DW175 | KF, 0…99 | liczba ze znaczeniem zera do potwierdzenia |

Źródła: pola 74–80, powiązania 81–86. Pola ZEITZEIGER, ZEITWERT, ZAEHLZEIGER, ZAEHLWERT i FAHRPROGRAMM mają typ **SP-ACT.VALUE**. Status GRUNDARBEIT tłumaczy 0/1/2 na `undefiniert / Grundstellung / Arbeitsstellung`; AUSEIN-HB używa tego samego adresu i tekstów `--- / aus / ein`.

Adresy DW128/DW130 odpowiadają w całości zweryfikowanemu FB101: DW128 jest wyborem, a DW130 buforem. Wydruk potwierdza dolny limit 0 dla numerów, lecz górny limit to **128**, podczas gdy teksty pomocy na stronie 98 podają **0…127**. Natywny FB101 koryguje indeks ≥128 różnie dla czasów i liczników. Nie zmieniono tej reguły i nie przyjęto bez wyjaśnienia zakresu 0…128 dla tablicy 128 nastaw w S7.

Pomoc ZAEHLWERT podaje **0…999**, a ZEITWERT **0,0…9990 sekund** i kontrolę granic w panelu (strona 98). Format **KC w COMTEXT zachowano dosłownie**; nie interpretowano go jako tekstowej stałej KC z języka STEP 5. Presety Z1/Z2 są używane przez stary PLC jako BCD — wynika to z wcześniejszego odczytu PB13, który nadal wymaga własnego wydruku natywnego. W nowym panelu licznik można prezentować dziesiętnie, a konwersję ustalić na granicy z logiką PLC.

Sposób zatwierdzania Enter opisano w pomocy FAHRPROGR.2 (strona 100) dla wyboru programu/liczby partii. Nie rozszerzono tego opisu na dowód zachowania wszystkich pól. FB101 sam nie zawiera osobnego sygnału zatwierdzenia; zachowanie jego cyklicznego zapisu pozostaje podstawą porównania edycji na TP900.

## Receptura PRG

Lista PRG na stronie 5 określa następującą kolejność. **Pełne natywne FB90/FB111 potwierdziły wszystkie dziesięć odbiorców**, a FB89 odbiór skrzynki, numer definicji 1 i zestawy 1…99. [Trzecia partia](../native_verification/WERYFIKACJA_PARTIA3.md) rozdziela potwierdzenie odbioru od poprawności programu. Nie odkodowano całego formatu transmisji ani ciała FB51.

| Wpis PRG | Nazwa | Funkcja | Wartość odczytywana w PLC |
|---:|---|---|---|
| 11 | TZ1 | Czas zanurzenia stacji 1 | DB205 DW5 |
| 12 | AZ1 | Czas ociekania stacji 1 | DB205 DW9 |
| 13 | US.STATION1 | Ultradźwięki stacji 1 | DB205 DW13 |
| 21 | TZ2 | Czas zanurzenia stacji 2 | DB205 DW17 |
| 22 | AZ2 | Czas ociekania stacji 2 | DB205 DW21 |
| 31 | TZ3 | Czas zanurzenia stacji 3 | DB205 DW25 |
| 32 | AZ3 | Czas ociekania stacji 3 | DB205 DW29 |
| 41 | TZ4 | Czas suszenia stacji 4 | DB205 DW33 |
| 91 | KBALLG | Ruch bębna | DB205 DW37 |
| 93 | BADHUB | Ruch pionowy w kąpieli | DB205 DW41 |

REZ_ZEIT_ALT i REZ_ZEIT_NEU mają odpowiednio typ REC.ACT.VAL i REC.SETPOINT, z powiązaniem REZ_ZEIT (FW198, KT). Pola AUS/EIN_A i AUS/EIN_N są symbolicznymi odpowiednikami wartości bieżącej i nastawy, powiązanymi z PRVAUS/EIN (FW198, KF, 0…1). Wspólne powiązania pól receptury i skrzynka DB205 nie są podstawą do przypisania wszystkim jej czasom jednego wspólnego tagu procesu na TP900. Nowa receptura powinna mieć osobne, nazwane składniki i określony transfer do PLC.

Definicje KT dla REZ_ZEIT, PRVTAUCHZEIT, PRVABTROPFZ i PRVAZ3 mają wydrukowane limity 0…999 (strony 82–84). Liczb tych nie uznano automatycznie za sekundy. Pomoc TZALLGEMEIN wyjaśnia, że czas 0 pomija daną stację (strona 99); natywny FB90 potwierdził maskowanie bazy 0FFF i pomijanie stacji przy zerowych cyfrach czasu.

Wydruk wyłącza `Compress data record` (strona 87). Nie zawiera wartości rzeczywistych zestawów. DW45 obecny w archiwalnym buforze nie ma odpowiednika w dziesięciu wpisach PRG; nie dodano na tej podstawie jedenastej nastawy.

Użytkownik później podał i potwierdził [komplet wartości programów 1 i 2](../operator_recipes/RECEPTURY_OPERATORA.md): dziesięć pól dla każdego, identyczne wartości, czasy w sekundach, obrót bębna i ruch pionowy aus. Dane operatora są osobnym źródłem, poza wydrukiem konfiguracji. Zachowano oba numery programów; nie scalono zestawów.

**Niespójność trybu ruchu:** listy KBA/KBN zawierają 0 brak, 1 obrót, 2 kołysanie, 3 obrót interwałowy, **4 obrót/kołysanie** (strony 78–79). Powiązanie PRVKB ma jednak adres **DB205 DW85** i limity **0…3** (strona 84), podczas gdy wcześniejszy odczyt FB90 rozpoznaje tryb 4 w DW37. Adres pola i pozycja w skrzynce receptury zostały zachowane jako osobne fakty; nie stwierdzono na tej podstawie błędu działającego układu. **Użytkownik potwierdził, że tryb obrót/kołysanie jest dostępny na obecnym OP15. Należy zachować tę opcję na TP900.** Znaczenie limitu dla edycji symbolicznej i układ transferu wymagają dalszej weryfikacji; sam zapis 0…3 nie jest podstawą usunięcia działającej funkcji. Potwierdzenie jest zapisane w [user-confirmations.json](user-confirmations.json).

## Klawisze i funkcje ręczne

Obraz 16 klawiszy jest w DB211 DW2…3. K13 ma offset bitowy 12, K16 offset 15; są to offsety w obszarze klawiatury (strony 104–106). **Pełny natywny FB3 potwierdził** M193.4/M193.7 oraz stany M190.5/M190.6. M190.3 jest wspólnym zboczem alternatywy obu stanów; zmiana klawisza bez zwolnienia obu nie daje kolejnego zbocza. Przy kodach błędu 115/188 FB3 zeruje odczytane stany klawiszy i unieważnia funkcję ręczną. Reakcja wszystkich odbiorców w procesie pozostaje do sprawdzenia. [Porównanie FB3 i FB60](../native_verification/WERYFIKACJA_PARTIA2.md).

Pomoc potwierdza konkretne działania (strony 97 i 102):

- HBGRDARB: K13 pozycja podstawowa, K16 pozycja robocza.
- HBEINAUS: K13 wyłączenie, K16 włączenie.
- HBGERASCHW: K13 ustawienie bębna prosto, K16 obrót/kołysanie.
- HBINFOSETZ: kasowanie znaczników za pomocą K13 i K16; dokładny warunek kombinacji wynika z PLC.
- **HBEIN: włączenie tylko tak długo, jak K16 jest naciśnięty.** Pomoc jest przypisana do HBDOSIERRAV, wpisu 66 aktywnego ekranu HANDBETRIEB — pompy dozującej środek przeciwpienny RAV (strony 4 i 14).

W TP900 odpowiednik ostatniej funkcji wymaga zachowania polecenia podczas przytrzymania i jego zwolnienia; krótki impuls zmieniłby działanie. Pozostałe przyciski trzeba dopasować do ich konkretnych warunków i zatrzasków w PLC. Reakcja po utracie połączenia oraz warunki zatrzymania ruchów nadal wymagają kodu procesu i schematu.

Funkcje nawigacyjne przypisane klawiszom: K1 menu 1, K2 ekran FAHRPROGR.1, K3 menu 31, K4 menu 2, K14 HANDBETRIEB, K15 VARIABEL (strona 107). Wszystkie klawisze mają Repeat OFF i puste funkcje Shift. Obraz LED jest w DB210 DW61…62; każdy klawisz ma parę bitów, z offsetami 0, 2, …, 30.

Tabele pól, klawiszy i pozycji menu zachowują numery poziomów dostępu wydrukowane jako Passwordlevel/PW Level. Są to oznaczenia uprawnień, bez wartości haseł. Funkcje menu serwisowego i funkcje procesu trzeba rozpatrzyć osobno podczas projektowania nawigacji TP900.

## Artefakty i dalsza praca

[provenance.json](provenance.json) dokumentuje źródło, protokół i liczby obiektów. Pliki CSV zawierają literalne adresy, typy oraz numery stron:

- [process-tags.csv](process-tags.csv), [fields.csv](fields.csv) — powiązania PLC i typy pól;
- [screens-and-recipes.csv](screens-and-recipes.csv), [screen-and-recipe-membership.csv](screen-and-recipe-membership.csv), [entry-catalog.csv](entry-catalog.csv) — przypisania i definicje;
- [exchange-areas.csv](exchange-areas.csv), [keyboard.csv](keyboard.csv) — komunikacja i klawisze;
- [messages.csv](messages.csv), [help-texts.csv](help-texts.csv), [menus.csv](menus.csv), [menu-items.csv](menu-items.csv) — teksty i nawigacja;
- [ROLL-COMTEXT.txt](ROLL-COMTEXT.txt), [COMTEXT-pages.json](COMTEXT-pages.json), [extract_comtext.py](extract_comtext.py) — pochodny odczyt i jego odtwarzanie.

Porównano **42 pełne bloki** i otrzymane DB15/DB19. [Szósta partia](../native_verification/WERYFIKACJA_PARTIA6.md) potwierdziła ręczne dozowanie K16/HB66, automatyczną gałąź z T107=15 s oraz A17.7=M71.5 — kontakt zakończenia czyszczenia używany jako status funkcji drzwi. [Komplet schematu](../schematic_review/ZASILANIE_BLOKADY.md) potwierdził K17.7A, kontakt X303:190/M i odrębny sygnał drzwi E14.0; nie pokazuje siłownika klienta sterowanego A17.7. ACK panelu i reset PLC pozostają odrębne. Następne materiały: końcowe modele S7 według kart producenta oraz sprawdzenie szczegółów połączeń; FB0 i ciało FB51 nadal osobno oznaczone.
