# Wzór HMI z 16.10.2026

XML pochodzi z natywnego eksportu użytkownika `ROLL_HMI_WZOR_20261016_080615_914505_eksport.zip`. Zachowano bajty oryginalnego ekranu i tabeli tagów.

Ekran ma cztery obiekty: przycisk, pole I/O, tekst i okrąg. Przycisk ustawia/kasuje `WzorPrzycisk`, a animacja okręgu korzysta z `WzorStan`. Pole I/O nie ma powiązania z tagiem; brakuje widoku alarmów. To wzór częściowy, nie gotowe ekrany operatorskie.

Tabela zawiera trzy tagi. Dwa zewnętrzne odwołują się do `ROLL_PLC`; brak definicji połączenia w eksporcie nie potwierdza jego braku w projekcie. Zachowaj istniejący projekt i jego połączenie.

Poprzedni eksporter podał błędnie zero obiektów, ponieważ `Screen` nie udostępnia ich jako publicznej właściwości API. Poprawka odczytuje obiekty z warstw XML. [Analiza i sumy](../../reports/hmi-seed-audit-2026-10-16.json).
