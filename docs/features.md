---
hide:
  - navigation
---

### Architektura systemu

System składa się z następujących komponentów:

1. **Aplikacja webowa Django** – główna aplikacja backendowa serwująca treści dynamiczne przez Gunicorn
2. **Baza danych PostgreSQL** – przechowuje wszystkie dane aplikacji
3. **Nginx** – reverse proxy obsługujący żądania HTTP, serwowanie plików statycznych i routing

### Kluczowe funkcje
- Uwierzytelnianie użytkowników z rolami administratora i zwykłego użytkownika
- Organizacja magazynu: pomieszczenia, regały, półki
- Śledzenie przedmiotów z kategoriami, datami ważności i lokalizacją
- Interfejs responsywny na urządzenia mobilne do łatwego zarządzania stanami magazynowymi
- Generowanie kodów QR dla szybkiego dostępu do informacji o półkach
- Eksport do Excela raportów magazynowych
- Powiadomienia e-mail o kończących się terminach ważności i resetowaniu hasła
- Obsługa wielu języków (polski i angielski)

### Konfiguracja sieci

Aplikacja, zgodnie z założeniami, jest dostępna tylko w sieci lokalnej, więc nie są wydawane certyfikaty, domeny ani https.  
Urządzenia mobilne muszą być podłączone do tej samej sieci co host.

### Typy użytkowników

1. **Administrator magazynu**:  
   - Pełny dostęp do wszystkich funkcji aplikacji  
   - Może zarządzać strukturą magazynu (pomieszczenia, regały, półki)  
   - Może zarządzać kategoriami przedmiotów  
   - Może eksportować do Excela  
   - Może przeglądać historię ruchów przedmiotów (usunięcia, dodania)

2. **Zwykły użytkownik**:  
   - Może przeglądać stan magazynu  
   - Może dodawać/usuwać przedmioty z półek  
   - Może filtrować i wyszukiwać przedmioty
