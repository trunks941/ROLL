# Stara CPU S5 — ustawienia potwierdzone instrukcją

Użytkownik podał oznaczenie **6ES5 942-7UB11** (MLFB bez spacji: **6ES5942-7UB11**) oraz potwierdził **pozycję RE i sprawną baterię podtrzymania**. Są to informacje użytkownika; nie wykonywano oględzin ani operacji na sterowniku.

Na [zdjęciu przekazanym 13 października](hardware_review/SPRZET_ZE_ZDJECIA.md) widać CPU 942B i kartridż z napisem EPROM. Pełne oznaczenie i pojemność kartridża pozostają nieodczytane; nie jest to oględzina fizyczna. Otrzymane DB15/DB19 są osobnym snapshotem danych tworzonych w RAM.

Przesłana [instrukcja S5-115U](reference_manuals/6ES5_998-0UF23.pdf), **Edition 04**, dokument **EWA4NEB8116130-02b**, obejmuje dokładnie CPU 942-7UB11 na okładce (PDF 1) oraz `6ES5 942-7UB11` w specyfikacji (PDF 543, drukowana 15-15). PDF ma 674 strony. SHA-256: `58a35a2ed6c91282569e338588ed0a7f2fd0764b49a00f22650efd1a54d0940f`. Rok copyright 1991 nie jest tu przyjmowany jako data wydania. Instrukcję odczytano lokalnie; wcześniejsza blokada witryny producenta nie blokuje już tego sprawdzenia.

## FB61: znaczenie zapisów systemowych

Kod: [natywny FB61](native_verification/FB61-native.txt), porównany w całości z archiwum. RS to angielskie, a BS niemieckie oznaczenie obszaru systemowego. Numery PDF poniżej są liczone od 1; podano też numery drukowane w stopkach.

| Słowo i działanie | Znaczenie dla CPU 942 | Źródło instrukcji |
|---|---|---|
| RS97 := 25 | Interwał OB13 = 25 × 10 ms = **250 ms**. Można ustawiać w programie startowym i zmieniać podczas pracy cyklicznej. | §7.4.3, PDF 190–191, drukowane 7-20–7-21; tabela 6-1, PDF 166 / 6-16 |
| RS120 := RS120 OR `16#0008` | Bit 3 włącza **retencję wszystkich znaczników**, przy przełączniku **RE**. Bit 4 dotyczy timerów, bit 5 liczników; FB61 zachowuje ich dotychczasowe wartości. | §4.2.3, PDF 119–120, drukowane 4-5–4-6; rys. 4-1 sprawdzony wizualnie |
| RS126 := 1000 | **1000 ms opóźnienia sprawdzania konfiguracji modułów przy następnym POWER OFF → POWER ON**. Zapis nie wstrzymuje bieżącego OB21/OB22 i nie ustanawia opóźnienia po każdym STOP → RUN. | §2.5.2, PDF 46 / 2-16; rys. 2-9, PDF 48 / 2-18; tabela 6-1, PDF 167 / 6-17 |

Podany przez użytkownika stan RE spełnia warunek retencji znaczników. Przy wcześniejszym wykonaniu FB61 i zachowanym ustawieniu bitu 3 wszystkie M są zachowywane podczas zwykłego restartu. Kasowanie obszarów nieretencyjnych następuje **przed OB21/OB22**; późniejsze ustawienie bitu nie odtwarza skasowanych danych. Po Overall Reset bity 3–5 oraz wszystkie M/T/Z są zerowane niezależnie od RE (PDF 120 / 4-6).

Overall Reset kasuje również wewnętrzną pamięć programu i moduł RAM CPU 941/942 (PDF 116 / 4-2), w tym wygenerowane w RAM DB15/DB19. Sprawna bateria nie chroni przed tą operacją; reguła zachowania nastaw dotyczy zwykłego restartu.

FB61 nie włącza pełnej retencji timerów ani liczników. Ich rzeczywisty zakres wynika z pozostałych bitów RS120 i konfiguracji; nie należy traktować komentarza o wszystkich znacznikach jako ustawienia retencji całej pamięci.

OB21 obsługuje ręczny restart STOP → RUN; OB22 start po przywróceniu zasilania przy poprzednim stanie RUN (PDF 188 / 7-18). Badane OB21/OB22 nie zerują M0.4 ani nastaw. Nie zawierają `RA`, więc przerwania czasowe zaczynają działać po zakończeniu OB startowego (PDF 48 / 2-18 i PDF 191 / 7-21).

Nominalne pełne okresy dzielnika OB13 dla M3.4/.5/.6/.7 wynoszą **0,5 / 1 / 2 / 4 s**. Faza zależy od wcześniejszych stanów M, a priorytety przerwań mogą opóźniać wykonanie; instrukcja nie dowodzi fazy pierwszego wywołania.

## Dane robocze RAM i tworzenie DB

Sprawna bateria podtrzymuje program i dane RAM po zaniku zasilania (PDF 34 / 2-4; PDF 58 / 2-28). Przełącznik RE/NR reguluje M/T/Z, a nie retencję całych DB. Bloki generowane przez `G DB` znajdują się w wewnętrznej pamięci programu RAM. W CPU 941/942 DB na E(E)PROM nie mogą być modyfikowane przez program sterowania (PDF 119 / 4-5). Typ faktycznego modułu pamięci pozostaje nieznany.

Instrukcja rozstrzyga działanie `G DB` (niemieckie `E DB`):

- Istniejący DB pozostaje bez zmiany, również długości, przy dodatnim parametrze tworzenia (PDF 233 / 8-35).
- Przykład `L KF +127; G DB 5` tworzy **128 wyzerowanych słów danych** (PDF 234 / 8-36, sprawdzony wizualnie). Dodatni parametr n odpowiada zatem DW0…DWn; siedem istniejących archiwalnych DB potwierdza tę regułę długości.
- `KF +131` przed utworzeniem DB15/DB19 w FB105 oznacza **132 słowa, DW0…DW131**. DW128–130 służą edytorowi; DW131 pozostaje poza kopiowaniem i obsługą FB101.
- Parametr 0 jest operacją usunięcia DB, nie tworzenia pojedynczego słowa.
- Samo tworzenie nie nadpisuje istniejących nastaw, lecz osobna pętla kopiowania FB105 może to zrobić, jeżeli program wejdzie w jej ścieżkę. Przy zwykłym restarcie z zachowanym M0.4 OB1 nie wywołuje FB105.

Wywołania OB31 w FB105 restartują monitor czasu cyklu; OB31 jest funkcją systemową, nie pustym blokiem użytkownika (PDF 404 / 11-32).

Szczegółowe cytowania: [słowa systemowe i start](reference_manuals/SYSTEM_START_EVIDENCE.md), [zakres CPU i zachowanie DB](reference_manuals/APPLICABILITY_DB_EVIDENCE.md).

## Konsekwencje dla migracji

W [założeniach S7](ZALOZENIA_START_NASTAWY_S7.md) można już przyjąć interwał przerwania cyklicznego 250 ms. Nastawy operatora oraz stan inicjalizacji należy zachować podczas zwykłego restartu. Wartości fabryczne stanowią osobną ścieżkę przygotowania danych; nie należy kopiować ich po każdym przejściu do RUN. Parametru RS126 nie odwzorowywać bezpośrednio timerem 1 s po każdym starcie — jego funkcja dotyczy gotowości konfiguracji modułów po zasileniu.

Potrzebne są końcowe modele S7 i modele G1/PNOZ i typ modułu pamięci. [Komplet 50 stron schematu](schematic_review/ZASILANIE_BLOKADY.md) jest już przeanalizowany. [DB15/DB19](native_verification/DB15_DB19_NASTAWY.md) są otrzymane w całości, a wszystkie PB procesu porównano. Programy operatora 1/2 są kompletne; zakres innych programów pozostaje do ustalenia. FB0 i ciało FB51 są osobno oznaczone. COMTEXT, instrukcja CPU, numer CPU, RE i sprawna bateria są już dostarczone.
