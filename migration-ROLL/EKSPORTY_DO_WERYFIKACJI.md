# Materiały potrzebne do weryfikacji migracji

Dotyczy projektu `04201`, STEP 5 / COMTEXT → S7-1513-1 PN / TP900 Comfort, TIA V19.

Archiwa S5 i OP15 są już zachowane i zinwentaryzowane. Użytkownik potwierdził ich zgodność z maszyną oraz dostęp do STEP 5 i COMTEXT. Nie trzeba przesyłać tych samych ZIP-ów ponownie.

## Otrzymane partie: weryfikacja odczytu instrukcji

Aktualny zakres to **42 pełne bloki**. [Szósta partia](native_verification/WERYFIKACJA_PARTIA6.md) potwierdziła wszystkie PB. Otrzymano również komplet DB15/DB19: [nastawy](native_verification/DB15_DB19_NASTAWY.md), w tym Z1=20/Z2=14 zamiast fabrycznych 5/5. FB51 jest częściowy, FB0 bez natywnego wydruku.

**Pierwsza partia jest kompletna:** OB1, FB105, FB61, OB13, OB21, OB22 i FB101. [Porównanie](native_verification/WERYFIKACJA_STEP5.md) potwierdziło wszystkie 27 wywołań OB1, jego instrukcje pokazane tekstowo i dwie czytelne sieci graficzne oraz wszystkie 272 pozycje w pozostałych sześciu blokach. FB105 jednoznacznie pokazuje tworzenie DB, a nie DX. Nie trzeba ponownie eksportować bloków z poniższej tabeli; tabela dokumentuje otrzymany zakres.

Zweryfikowane listingi kopii offline `04201@ST.S5D`:

| Blok | Cel porównania |
|---|---|
| OB1 | Kolejność wywołań i warunek pierwszej inicjalizacji |
| OB13 | Dzielenie taktów i zachowanie zegarów |
| OB21 i OB22 | Uruchomienie po STOP / zaniku zasilania |
| FB61 | Okres OB13, ustawienia systemowe i retencja |
| FB105 | Tworzenie DB, kopiowanie wartości domyślnych i ustawienie stanu inicjalizacji |
| FB101 | Przekazywanie nastaw czasów/liczników z panelu |

Wydruk powinien zawierać **pełne instrukcje, numery sieci, operandy absolutne oraz komentarze**, a przy wywołaniach FB także parametry. Symbole mogą występować dodatkowo. Preferowany jest plik tekstowy; czytelny PDF również wystarczy. Nazwa rozszerzenia pliku nie jest istotna — potrzebna jest treść listingu, nie kolejna kopia pliku binarnego S5D.

[Lista braków](native_verification/BRAKUJACE_BLOKI_STEP5.md) obejmuje FB0, częściowy FB51, pięć bloków systemowych i formaty archiwalnych DB. Wszystkie PB, robocze DB15/DB19, komplet 50 stron i typy I/O S5 są otrzymane. Do końcowego doboru pozostaje weryfikacja kart modeli S7 według zachowanych klas prądowych; dane cewek nie będą ponownie zamawiane.

W otrzymanym FB105 zapis `G DB` rozstrzygnął wszystkie dziewięć instrukcji zaczynających się od `78 05`. Poprawiono operand w czytniku na DB. Wariant wydruku zawierający operandy absolutne i adresy instrukcji jest szczególnie przydatny również dla kolejnych bloków.

## COMTEXT: adresy i zachowanie panelu

**Otrzymano ROLL@@LS.INI:** 128 stron dokumentacji COMTEXT projektu 04201. [Raport i tabele](comtext_review/USTALENIA_COMTEXT.md) obejmują poniższy zakres; nie trzeba ponownie eksportować tych definicji:

- połączenie ze sterownikiem i ustawione obszary wymiany danych;
- listę aktywnych ekranów oraz numery/nazwy ekranów;
- każde pole ze wskazaniem DB/obszaru, numeru słowa lub bitu, formatu, kierunku odczyt/zapis, limitów i jednostki;
- przypisania klawiszy funkcyjnych oraz funkcje wywoływane przy ich obsłudze;
- alarmy z numerami, tekstami i powiązaniem z PLC, wraz ze sposobem potwierdzania;
- strukturę receptury/programu, kolejność pól i mechanizm przesyłania/potwierdzania;
- używane funkcje systemowe i ewentualne drukowanie danych.

Wydruk rozstrzyga adresy i typy skonfigurowanych pól, przypisania ekranów i klawiszy oraz strukturę PRG. Definicje niewymienione w ekranach/recepturze zostały oznaczone osobno. Użytkownik potwierdził dostępność trybu obrót/kołysanie mimo limitu liczbowego 0…3 w powiązaniu COMTEXT; zachowamy tę opcję w migracji.

Otrzymano [komplet wartości programów 1 i 2](operator_recipes/RECEPTURY_OPERATORA.md). Nadal potrzebne jest ustalenie, czy istnieją inne używane programy, oraz porównanie pozostałego kodu PLC, aby zakończyć mapowanie bitów alarmowych, potwierdzania i transferu. Zakres numerów nastaw 0…128 w konfiguracji różni się od pomocy 0…127 i wymaga zachowania/wyjaśnienia reguły FB101.

Nazwy menu dokumentacji/drukowania zależą od wersji i języka STEP 5 oraz COMTEXT. Jeśli nie możesz znaleźć sposobu zapisu wydruku, prześlij obraz menu dokumentacji lub drukowania — wtedy instrukcję można dopasować do rzeczywiście dostępnych opcji.

## Dane robocze i receptury

**DB15/DB19 są już otrzymane w całości**, po 132 słowa DW0…DW131 z C:ROLLPRST.S5D. Ich brak w pierwotnym archiwum jest zgodny z tworzeniem w RAM przez FB105. Otrzymane nastawy przechowujemy oddzielnie od fabrycznych DB12/DB16. Nie trzeba ponawiać tych samych wydruków.

Programy 1 i 2 zostały już opisane wszystkimi dziesięcioma polami i potwierdzone przez użytkownika. Jeśli istnieją inne używane programy, potrzebne są także ich wartości. Projektowanie ekranów i formatów receptur nie dowodzi, że archiwum projektu zawiera wszystkie aktualne zestawy wartości.

W DB12 i DB16 występują wartości `FFFF` i słowa przy końcu bloków. Nie traktować ich automatycznie jako nastaw czasu lub licznika. Ich rolę trzeba ustalić przez kod i dokumentację pól.

## Sprzęt i oprogramowanie

Otrzymano zdjęcie całego zestawu i potwierdzenie braku dodatkowych modułów. [Inwentaryzacja](hardware_review/SPRZET_ZE_ZDJECIA.md) obejmuje 128 DI i 80 DQ. [Komplet 50 stron schematu](schematic_review/ZASILANIE_BLOKADY.md) jest już przeanalizowany; mapa 208 kanałów zawiera zaciski narysowane dla S5, grupy zasilania i powiązania z obwodami mocy. Potrzebne są końcowe modele S7 i modele G1/PNOZ i sprawdzenie szczegółów połączeń. Na kartridżu widać EPROM, bez czytelnej pojemności/MLFB.

CPU **6ES5 942-7UB11**, pozycja RE, sprawna bateria i instrukcja systemowa są już dostarczone. [Ustalenia CPU](CPU_S5_USTALENIA.md) rozstrzygają znaczenie RS97/120/126 i działanie tworzenia DB. Komplet schematu jest otrzymany; należy uzupełnić czytelne oznaczenia modułów I/O i typu pamięci. Dobór S7 ma zachować różne sprzętowo odcinane grupy zasilania wyjść; sama tabela symboli nie jest listą zakupową.

CPU `6ES7513-1AM03-0AB0` jest zamówiony. Wersja firmware zostanie sprawdzona po dostawie; jej brak obecnie nie blokuje analizy źródeł. Użytkownik podał pakiet „Advanced”, interpretowany jako WinCC Advanced w TIA V19. Ten pakiet obsługuje panele Comfort; dostępność STEP 7 Professional, zakres licencji i katalog urządzeń należy potwierdzić przy budowaniu projektu TIA.

Pozostałe materiały mogą być przesyłane partiami: oznaczenia modułów, zasilacza/przekaźników i cewek oraz pozostałe listingi STEP 5. Komplet 50 stron schematu, DB15/DB19, programy operatora 1/2 i wydruk konfiguracji COMTEXT są już odczytane.
