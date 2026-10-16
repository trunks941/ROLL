# Wzór HMI — 16.10.2026, 10:35

Ostatni wzór: pole I/O jest powiązane z WzorLiczba. XML zawiera cztery eksportowalne obiekty (przycisk, I/O, tekst, okrąg). Alarm view jest widoczny w GUI, ale pomijany w eksporcie; raport starego eksportera mylnie traktował ten brak w XML jako brak kontrolki.

Z raportu usunięto tylko lokalną ścieżkę reportArchive. Pozostałe pliki zachowano bez zmian. Pochodzenie i sumy bieżących wzorów są w hmi/seed/provenance.json. Na ich podstawie powstał pierwszy pakiet importu ekranów do kopii pełnego projektu, zachowującej istniejący widok alarmów.
