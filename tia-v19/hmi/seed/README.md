# Wzór HMI z 16.10.2026

Bieżące `WZOR_ROLL.xml` i `tags.xml` pochodzą z eksportu `ROLL_HMI_WZOR_20261016_103516_d82103_eksport.zip`. Pochodzenie i sumy są w `provenance.json`. Zachowano oryginalne bajty.

Ekran zawiera przycisk, pole I/O powiązane z WzorLiczba, tekst i okrąg z animacją WzorStan. Widok alarmów jest widoczny w GUI użytkownika, lecz pomijany w XML. Nie wymagamy jego ponownego dodawania/eksportu; importer zachowuje WZOR_ROLL w kopii całego projektu.

`WZOR_ROLL-unbound-regression.xml` jest starszym wzorem z 08:06, używanym do testu wykrywania brakującego powiązania pola I/O. Nie jest bieżącym ekranem do importu.

`../native` zawiera kandydatów pięciu ekranów i tagów do lokalnego importu/kompilacji, a nie potwierdzony natywny projekt. [Instrukcja](../../HMI_IMPORT.md).
