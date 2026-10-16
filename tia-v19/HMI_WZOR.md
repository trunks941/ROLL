# Jednorazowy wzór HMI w TIA V19

PLC z raportu `ROLL_20261015_120907_bfeaa0` kompiluje się bez błędów; retencja sześciu DB została potwierdzona. WinCC Comfort udostępnia import/eksport HMI, ale jego `GetCreationInfos` dla ekranów, tagów i połączeń jest puste. Potrzebny jest wzór utworzony w edytorze, zawierający rzeczywisty format obiektów, zdarzeń oraz symbolicznego adresowania PLC. Wzór nie musi mieć docelowego wyglądu.

## Etap wzoru zakończony

Ostatni eksport `ROLL_HMI_WZOR_20261016_103516_d82103_eksport.zip` potwierdził przypisanie `WzorLiczba` do pola I/O. Przycisk i animacja lampki są poprawne. Widok alarmów widać w edytorze, mimo że eksport XML go pomija; nie jest to polecenie jego ponownego dodawania.

**Następny krok to [HMI_IMPORT.md](HMI_IMPORT.md) i `IMPORTUJ_HMI.cmd`.** Poniższa instrukcja pozostaje opisem wcześniejszego przygotowania wzoru; nie trzeba jej ponawiać.

## 1. Otwórz zapisany projekt

W TIA V19 otwórz plik `ROLL_20261015_120907_bfeaa0.ap19` z podkatalogów `Dokumenty\ROLL_TIA_V19`. Przejdź do widoku projektu i panelu `ROLL_TP900`. Zachowaj ten projekt do dalszej pracy. Aktualnego programu PLC nie trzeba ponownie generować.

## 2. Utwórz połączenie panel–PLC

W panelu otwórz **Connections / Połączenia**. Dodaj połączenie `ROLL_PLC` do `ROLL_CPU1513` z tego projektu, używając sterownika komunikacyjnego **SIMATIC S7-1200/1500** i interfejsu PROFINET/Ethernet. Wybierz CPU z projektu, aby w tagach dało się wskazać symbole DB. Przy kreatorze połączenia HMI wybierz tę samą CPU. To konfiguracja offline; do przygotowania wzoru urządzenia nie muszą być podłączone.

## 3. Dodaj trzy tagi HMI

W **HMI tags / Zmienne HMI → Default tag table** dodaj:

| Nazwa HMI | Typ | Połączenie / symbol PLC |
|---|---|---|
| `WzorPrzycisk` | Bool | wewnętrzna zmienna HMI — bez połączenia PLC |
| `WzorLiczba` | Int | `ROLL_PLC` → `"ROLL_HMI".Dwell1Seconds` |
| `WzorStan` | Bool | `ROLL_PLC` → `"ROLL_HMI".Connected` |

Dla dwóch zmiennych zewnętrznych wybierz symbol z listy tagów/bloków CPU. Nie wpisuj absolutnego `DBx.DBW...`: DB są zoptymalizowane. Wybór symbolu powinien ustalić typ automatycznie.

## 4. Dodaj ekran i obiekty

W **Screens / Ekrany → Add new screen / Dodaj nowy ekran** utwórz `WZOR_ROLL`. Z przybornika dodaj:

1. **Text field / Pole tekstowe** z napisem `Wzór ROLL`.
2. **Button / Przycisk** z napisem `Test`. W jego właściwościach **Events / Zdarzenia** przypisz do **Press / Naciśnięcie** funkcję `SetBit` dla `WzorPrzycisk`, a do **Release / Puszczenie** funkcję `ResetBit` dla tego samego tagu.
3. **I/O field / Pole I/O** w trybie wejście/wyjście, format liczbowy dziesiętny, tag `WzorLiczba`.
4. **Alarm view / Widok alarmów** — wystarczą ustawienia domyślne. Nie trzeba przepisywać alarmów maszyny.

Jeśli możesz, dodaj także **Circle / Okrąg** i w jego animacji wyglądu powiąż kolor z `WzorStan`: 0 = szary, 1 = zielony. To dodatkowy wzór lampki; brak tego elementu nie blokuje eksportu podstawowych obiektów.

Rozmieszczenie i kolory pozostałych obiektów mogą być dowolne. Przyciskiem wzoru sterujesz tylko wewnętrzną zmienną HMI.

## 5. Ustaw ekran startowy i zapisz

W **Runtime settings / Ustawienia Runtime → General / Ogólne** ustaw **Start screen / Ekran startowy** na `WZOR_ROLL`. Jeżeli TIA ustawiło go automatycznie, zachowaj to ustawienie. Zapisz projekt. Możesz skompilować oprogramowanie panelu, aby sprawdzić wskazania tagów i ekran startowy. Pozostaw projekt otwarty w TIA.

## 6. Wyeksportuj wzór

Z aktualnej paczki uruchom **`EKSPORTUJ_WZOR_HMI.cmd`**. Zezwól na lokalny dostęp Openness, jeśli TIA zapyta. Jeśli otwartych jest kilka projektów, skrypt wyświetli ich nazwy i poprosi o wybór właściwego numeru.

Skrypt podłącza się do otwartego edytora i eksportuje dostępne ekrany, tagi, połączenia, listy i skrypty. Nie zapisuje zmian projektu, nie importuje obiektów i nie wykonuje wgrywania do urządzeń. Wynik to `Dokumenty\ROLL_TIA_V19\ROLL_HMI_WZOR_…_eksport.zip` — **prześlij ten ZIP**. Kod 2 oznacza zapisany eksport z brakami, których lista pojawi się w konsoli i raporcie; taki eksport również może być przydatny do analizy.

Nie uruchamiaj teraz ponownie `UTWORZ_PROJEKT.cmd`: tworzy osobny projekt z pustym panelem. Wzór i ustawienia połączenia/startu zachowaj w otwartym projekcie; dalszy import HMI będzie wymagał zachowania tych ustawień. Eksporty XML nie są kopią całego projektu.
