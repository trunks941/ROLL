# Wzór HMI — 16.10.2026, 08:06

Natywny eksport użytkownika: ekran WZOR_ROLL, trzy tagi, cykle oraz metadane. Wynik zero obiektów w raporcie eksportera jest błędny: XML zawiera przycisk, pole I/O, tekst i okrąg. Przycisk SetBit/ResetBit i animacja okręgu są powiązane. Pole I/O nie ma tagu, brak widoku alarmów. Tagi wskazują ROLL_PLC, ale definicji połączenia nie wyeksportowano; nie można z tego stwierdzić braku połączenia w projekcie.

Oryginalny raport ma usunięte pole lokalnej ścieżki reportArchive; pozostałe pliki zachowano bez zmian. [Analiza i pochodzenie](../../reports/hmi-seed-audit-2026-10-16.json). Wzór używany w kontrolach regresji jest w hmi/seed.
