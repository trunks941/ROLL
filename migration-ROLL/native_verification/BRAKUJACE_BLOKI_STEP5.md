# ROLL — brakujące wydruki STEP 5

Stan na 12 października 2026. Program z archiwum S5D jest zinwentaryzowany. Poniższa lista określa wydruki natywne potrzebne do porównania odczytu i zakończenia analizy migracji.

**Pełne wydruki otrzymane i porównane — 42 bloki:** pięć OB, piętnaście FB i wszystkie 22 PB z bieżącego katalogu. [Szósta partia](WERYFIKACJA_PARTIA6.md) potwierdziła 181 nowych sieci. Kompletne [DB15/DB19](DB15_DB19_NASTAWY.md) są otrzymane i odczytane. Pełne numery bloków dokumentuje [status](program-native-verification-status.csv).

**Następne materiały:** końcowe modele S7 i modele G1/PNOZ i sprawdzenie szczegółów połączeń do mapowania S7. [Komplet 50 stron schematu](../schematic_review/ZASILANIE_BLOKADY.md) już przeanalizowano. Do kompletności kodu pozostaje natywny FB0; archiwum pokazuje tylko BE i brak znalezionego statycznego wywołania. Dodatkowe oddzielne PB51/PB52 są opcjonalne.

**FB51 otrzymano częściowo:** plik i edytor STEP 5 pokazują tylko `JU =M001` i `BE`. Użytkownik potwierdził ten widok; nie trzeba ponawiać identycznego eksportu. Ciało, cel pierwszego skoku i końcówka pozostają niezweryfikowane. Jeśli dostępna jest dokumentacja producenta funkcji TDOP:511, potrzebne są opis i interfejs. Nie ustalono konkretnej przyczyny ograniczonej prezentacji.

## Pozostałe zwykłe bloki kodu bez pełnej weryfikacji — 2

To **FB0 bez natywnego wydruku oraz częściowy FB51**.

| Typ | Numery bloków wymagających wydruku |
|---|---|
| OB | Wszystkie zwykłe OB porównane; OB31 w grupie systemowej poniżej |
| FB — bez wydruku | FB0 |
| FB — fragment | FB51: otrzymany początek nie pozwala porównać całego bloku |
| PB | Wszystkie PB porównane |

## Bloki systemowe — osobne sprawdzenie

OB31 oraz FB240, FB241, FB242 i FB243 mają flagę assemblera. Instrukcja producenta identyfikuje funkcje: restart monitora czasu cyklu, konwersje BCD/binarną, mnożenie i dzielenie. Jeśli STEP 5 udostępnia ich dokumentację/deklaracje, dołączyć je do wydruku. Pełnego AWL nie wymuszać, gdy narzędzie pokazuje funkcję integralną; wtedy potrzebne jest potwierdzenie oznaczenia, interfejsu i użycia w projekcie.

## Bloki danych

Dla pełnej weryfikacji danych potrzebne są wydruki z numerami DW i formatami wszystkich DB z katalogu: **DB0, DB1, DB12, DB16, DB41, DB50, DB51, DB60, DB205, DB206, DB210, DB211, DB213, DB219**. Dane bajtowe tych DB są w archiwum; wydruk pozwoli porównać ich deklarowane formaty i komentarze.

**Robocze DB15/DB19 są otrzymane i przeanalizowane**, po 132 słowa z listingów KH. Wydruki przekazano po potwierdzeniu dostępu online; czasu pobrania i trybu maszyny nie podano. Nastawy, ich źródła i różnice wobec fabrycznych wartości zapisano osobno. Receptury programów 1/2 są również kompletne.

## Format eksportu

Preferowany AWL/STL: adresy instrukcji, operandy absolutne, wszystkie sieci, komentarze oraz parametry wywołań FB. Dla DB: numery DW, wartości, formaty i komentarze. Pliki tekstowe INI takie jak poprzednie eksporty są odpowiednie; czytelny PDF też wystarczy. Pełny wydruk projektu może zastąpić eksportowanie pojedynczych bloków.

Źródła listy: [status porównania bloków](program-native-verification-status.csv), [katalog S5D](../analysis/s5-program-blocks.csv) i [inwentaryzacja otrzymanych eksportów](native-files-inventory.json).
