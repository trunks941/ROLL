# ROLL — ogrzewanie, RAV, proces i sygnalizacja

Stan na **12 października 2026**. Otrzymano PB19, PB20, PB21, PB23, PB24 i PB25. Oryginały zachowano bez zmian w `../originals/step5-native/`. Załączniki są źródłami technicznymi do analizy offline.

## Wynik i metoda

| Blok | Strony | Sieci | Pozycje MC5 — kontekst | Instrukcje wykonawcze | Adresowane STL |
|---|---:|---:|---:|---:|---:|
| [PB19](PB19-native.txt) | 5 | 18 | 143 | 125 | 2 |
| [PB20](PB20-native.txt) | 17 | 69 | 568 | 499 | 3 |
| [PB21](PB21-native.txt) | 17 | 46 | 520 | 474 | 3 |
| [PB23](PB23-native.txt) | 5 | 19 | 163 | 144 | 3 |
| [PB24](PB24-native.txt) | 1 | 4 | 28 | 24 | 3 |
| [PB25](PB25-native.txt) | 5 | 25 | 148 | 123 | 3 |

**Wszystkie 181 sieci są zgodne** w porównaniu warunków, operandów, kolejności działań, rodzajów timerów i ich nastaw. Łącznie jest 1570 pozycji MC5, w tym 1389 instrukcji wykonawczych i 181 BLD. Liczba pozycji MC5 jest kontekstem odczytu; w mieszanych wydrukach osobno porównano 17 adresowanych pozycji STL.

[Wyniki i SHA-256](plant-control-comparison.json), [metadane sześciu otrzymanych źródeł](partia6-native-received.json). Wyniki sieci i pełne warunki są w plikach `PB19/PB20/PB21/PB23/PB24/PB25-network-comparison.csv` oraz odpowiednich `*-comparison.json`.

Rozszerzono czytnik o końcowe tekstowe `BE` w tej samej sieci co grafika — PB21, sieć 46. Początkowa kontrola prawidłowo odrzuciła niepełną listę działań, zamiast uznać sieć za zgodną. Odczyt uwzględnia teraz polecenie wyjścia i następujące po nim BE. **13 kontroli czytnika przeszło**, w tym wykrywanie usunięcia BE i odrzucenie BE umieszczonego przed grafiką. [Zapis kontroli](fbd-reader-test-results.txt), [czytnik](compare_fbd_listings.py), [kontrole](test_fbd_reader.py). Ponownie porównano także wcześniejsze 15 bloków FBD; łącznie 21 bloków ma 653 zgodne sieci. Dekoder MC5 pozostał bez zmian.

**Aktualnie mamy 42 pełne bloki**, FB51 częściowy, FB0 bez natywnego wydruku oraz pięć bloków systemowych w osobnej grupie. Wszystkie PB z katalogu mają już pełne porównanie. [Lista braków](BRAKUJACE_BLOKI_STEP5.md), [status](program-native-verification-status.csv).

## DB15 i DB19: brak w oryginalnym projekcie

Użytkownik potwierdził brak tych plików w projekcie i możliwość odczytu ze starej CPU. To odpowiada katalogowi S5D i natywnemu FB105: program tworzy **DB15 i DB19 w RAM, po 132 słowa DW0…DW131**, a przy pierwszym przygotowaniu kopiuje DW0…127 odpowiednio z DB12 i DB16. DW128…131 nie są kopiowane; nowo utworzone mają zero. Istniejące DB oraz zwykły restart to inne ścieżki, zgodnie z wcześniejszymi ustaleniami CPU.

Zachowano trzy odrębne rodzaje danych:

- [Rekonstrukcja fabryczna 264 słów](runtime-db-factory-reconstruction.csv) — dokładny wzorzec pierwszego przygotowania, z pochodzeniem każdego słowa i oddzielną kolumną otrzymanego snapshotu. Wartości fabryczne pozostają odrębnym zestawem.
- [Powiązania 28 parametrów z odbiorcami](runtime-parameter-use-map.csv) — 26 słów KT w DB15 i dwa presety BCD w DB19, z wartościami fabrycznymi i otrzymanymi.
- **Otrzymano komplet DB15ROLS.INI i DB19ROLS.INI**, po 132 słowa. DB15.DW0…127 odpowiada DB12; DB19.DW1/DW2 ma presety Z1=20 i Z2=14 zamiast 5/5. [Nastawy i jednostki](DB15_DB19_NASTAWY.md), [źródła](runtime-db-snapshots.json). Wydruki wskazują C:ROLLPRST.S5D; czasu pobrania i trybu maszyny nie podano. Odczyt KH oraz konwersję BCD/KT sprawdzono przez [siedem kontroli](runtime-db-reader-test-results.txt).

Otrzymane programy operatora 1 i 2 mają komplet dziesięciu pól; ich wartości pozostają bez zmiany. Receptury PRG i ogólne nastawy DB15/DB19 są różnymi zestawami danych.

## PB19: suszenie i ogrzewanie

Potwierdzono warunki M82.0 i M82.2, zatrzaski M82.3 (obciążenie podstawowe) oraz M82.4 (pełna moc), dwie prędkości wentylatora A17.2/A17.3 i stopnie ogrzewania A18.0…A18.3. Warunki obejmują zegar E3.1 lub AUTO_L, zabezpieczenia, poziomy i sygnalizację M4.1. Ostateczna interpretacja polaryzacji wejść i obwodów wymaga schematu.

**T22=KT060.3 to 600 s, czyli 10 minut podtrzymania wentylatora po ogrzewaniu.** T90=0,5 s i T91=4 s są opóźnieniami wyłączenia przy przełączaniu prędkości. A17.2 jest liczone przed A17.3, a timery później; wzajemne blokady czytają obraz wyjść zgodnie z kolejnością sieci. T22 odczytuje A18.0 przed jego późniejszym zapisem.

## PB20: RAV i pompa dozująca

Potwierdzono źródła dziesięciu alarmów RAV: M8.0…M8.5 oraz M12.4…M12.7. Dwa są przypisaniami bezpośrednimi, osiem ma ustawienie i późniejszy reset. Większość resetów korzysta z M3.1; M12.7 wymaga także E9.6. [18 działań alarmowych](plant-alarm-writes.csv) uzupełnia [mapę 120 alarmów](alarm-source-and-reset-map.csv).

W rozpoznanym kodzie wszystkich autorów bezpośrednich zapisów bitów alarmowych porównano natywnie. Osiem skonfigurowanych bitów nadal nie ma znalezionego bezpośredniego autora: M13.5/.6, M14.4/.5/.6/.7 i M15.0/.1. Nie uznano ich automatycznie za nieużywane; ciało FB51 i opcje sprzętu pozostają poza pełnym rozstrzygnięciem.

Pompa A20.5 ma potwierdzony warunek:

```text
A20.5 = (HAND E0.1 AND K16 M190.6 AND HB66 M26.6)
        OR (AUTO E0.2 AND (A21.6 OR T107))
SA T107: AUTO E0.2 AND A21.6; nastawa DB15.DW107
```

Ręczne dozowanie wymaga przytrzymania K16. Automatyczne dozowanie jest związane z zaworem zasilania parownika A21.6 i podtrzymaniem T107; to odrębna gałąź. Otrzymane DW107 daje 15 s, zgodnie z wartością fabryczną. Sam warunek A20.5 nie zawiera globalnego M29.0 — nie dodawano go w dokumentacji.

PB20 zawiera także stopnie ogrzewania parownika A18.4…A18.7, zawory A21.0/A21.2/A21.6 i sekwencję zasilania zbiornika M151…M153. Warunki własnego podtrzymania, poziomy i późniejsze resety są w [94 działaniach stanów procesu](plant-state-SR.csv). T104 i T105 mają **KT002.0=20 ms**, a T106=10 s. Nie tłumaczyć tych dwóch stałych jako 2 s. Część gałęzi/opcji używa M0.3/M0.4 i rzeczywistych stałych logicznych po inicjalizacji.

## PB21 i PB23: napełnianie, pompy i ultradźwięki

PB21 wyznacza zezwolenia M99.7/M100.0 i żądania napełniania/uzupełniania. Nie wszystkie funkcje ręczne działają wyłącznie podczas przytrzymania: część używa zatrzasków z resetem przez poziomy, wybór funkcji, wyjście z HAND i K13. Wiele rezerwowych gałęzi ma `NOT M0.3` w resecie, więc po inicjalizacji pozostaje wyłączonych. Nie dodawać ich do panelu na podstawie samego komentarza.

PB21 potwierdza źródła M103.0/.3/.4, uczestniczących w resecie T62 z PB52, oraz podtrzymanie T119=5 s. PB23 realizuje końcowe polecenia pomp i zaworów. Warunek M102.7 zawiera alternatywę z M0.4; zachowano ten rzeczywisty zapis. Zawory i pompy mają wzajemne blokady odczytujące obraz wyjść, z określoną kolejnością OB1.

Ultradźwięki stacji 1 są powiązane z M111.4 i etapami M40.3/.4/.5. **A19.0 — stycznik sieciowy — ma T51=120 s opóźnienia wyłączenia**. **A19.1 — zdalne włączenie — korzysta z T52=5 s opóźnienia załączenia**, z dodatkowymi warunkami M35.2, poziomu i T70. Recepturowe „ein” jest wyborem funkcji, a nie bezwarunkowym stanem obu wyjść przez cały cykl.

T76=KT360.3 ma **60 minut** i bierze udział w gałęzi pracy pompy P1 podczas nagrzewania; inne gałęzie mogą nadal żądać tej pompy. Nie potraktowano T76 jako wspólnego limitu pracy wszystkich pomp.

**A21.5 jest zapisywane dwukrotnie:** w PB20 sieć 63, a potem w PB23 sieć 18. W standardowym obiegu OB1 ostatni zapis pochodzi z PB23. Wcześniejszy zapis PB20 może zostać odczytany przed nadpisaniem. Nie sprowadzać tego do jednego dowolnego przypisania.

## PB24: separator oleju

T54 (SE) korzysta z DB15.DW54, a T53 (SA) z DB15.DW53; A19.4 ma warunek `NOT M40.5 AND T53`. W sieci 2 M240.0 jest dokładnie `E5.0 AND M13.3 AND T59`, z **dodatnim M13.3**, a następnie resetuje T53. Zachowano tę polaryzację i nie zastąpiono jej domyślną regułą „pracuj przy braku alarmu”. Wyjaśnienie obwodu i wyposażenia wymaga schematu. Otrzymane DW53/DW54 mają po 120 s, zgodnie z wartościami fabrycznymi.

## PB25: lampki, alarm zbiorczy i drzwi

PB25 wyznacza M87.0…M88.6 przez porównanie bajtów MB5…MB19 z zerem i zbiorczy M88.7. Używa **M3.6**, którego pełny okres z OB13 wynosi 2 s, do migania wybranych lampek. M31.1 z PB7 korzysta z części tych zbiorczych bitów; PB7 jest wykonywany przed PB25, więc odczytuje stan sprzed bieżącego wyliczenia.

Istotne doprecyzowanie wcześniejszego opisu funkcji drzwi: **A17.7 = M71.5**. Symbol wyjścia opisuje bezpotencjałowy sygnał „czyszczenie zakończone”. PB25 zatrzaskuje M71.5 z przebiegu automatu lub ręcznej funkcji 7 (K16 ustawia, K13 resetuje). PB18 i OP15 pokazują A17.7 jako stan tej funkcji. Nie jest to bezpośredni czujnik położenia drzwi; faktyczne połączenie kontaktu z mechanizmem drzwi wymaga schematu.

## Artefakty i dalsza praca

- [37 nowych zapisów wyjść](plant-output-map.csv) — ogrzewanie, pompy, zawory, skimmer i sygnalizacja.
- [34 działania timerów](plant-timer-map.csv) — 32 uruchomienia i dwa resety; SE/SA zachowano osobno.
- [Kolejność wszystkich znalezionych zapisów wyjść](all-output-writer-order.csv) — 61 zapisów do 60 różnych bitów. Dodatkowo A113.0/.4/.5 są odczytywane, ale w rozpoznanym kodzie brak ich zapisu; nie utożsamiać liczby referencji z liczbą sterowanych kanałów.
- [Skrypt zestawień](extract_plant_control.py), [podsumowanie](plant-data-evidence.json), [kontrola artefaktów](partia6-artifact-checks.json).

Uzupełnienie po analizie [kompletu 50 stron schematu](../schematic_review/ZASILANIE_BLOKADY.md): następny materiał to **końcowe modele S7 i modele G1/PNOZ i sprawdzenie szczegółów połączeń**. Otrzymane strony potwierdziły fizyczny kontakt zakończenia czyszczenia A17.7, sprzętowe blokady napędów i rozdzielone grupy zasilania. A19.1 uczestniczy także w zasilaniu generatora ultradźwięków nr 4 przez K19.01M. DB15/DB19 są otrzymane i porównane. Do kompletności wydruków kodu pozostaje FB0; archiwalny odczyt pokazuje tylko BE i brak znalezionego statycznego wywołania, lecz to nie zastępuje natywnego listingu. FB51 nadal ma tylko znany dwuwierszowy fragment. Pozostają również deklarowane formaty archiwalnych DB i sprawdzenie docelowego katalogu/licencji TIA po dostawie CPU. Wcześniejsze odwołania w tym raporcie do brakującego schematu opisują stan analizy samego kodu; aktualny zakres odczytu podaje przegląd schematów.

Porównanie jest statyczne. Nie powstał jeszcze skompilowany projekt TIA ani wynik testów maszyny; analiza jest podstawą przygotowania programu S7 i mapowania sprzętu.
