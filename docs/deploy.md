---
hide:
  - navigation
---

# Przewodnik wdrożeniowy

Ten przewodnik wyjaśnia, jak wdrożyć aplikację do zarządzania magazynem przy użyciu Dockera i Nginx w środowiskach produkcyjnych.

## Wymagania wstępne

- Zainstalowany Docker i Docker Compose
- Git (do sklonowania repozytorium)
- Port 80 dostępny na maszynie hosta

## Kroki wdrożenia

### 1. Sklonuj repozytorium

```sh
git clone https://github.com/yourusername/ce-it-hub-hackathon-2025.git ksp
cd ksp
```

### 2.A Użyj uv do utworzenia środowiska wirtualnego i instalacji zależności

[Zainstaluj uv](https://docs.astral.sh/uv/getting-started/installation/#installing-uv)
```sh
uv sync
```

### 3. Skonfiguruj zmienne środowiskowe

Skopiuj przykładowy plik środowiskowy i zaktualizuj go według własnych ustawień:

```sh
cp .env.example .env
```

Edytuj plik `.env` zgodnie z własną konfiguracją:
- Ustaw bezpieczny `SECRET_KEY`
- Ustaw wszystkie wymienione nazwy użytkowników i hasła w pliku .env
- Ustaw poprawny adres IP sieci, uruchamiając: `./scripts/set_network_ip.sh` z katalogu `ksp`.

> **WAŻNE**: Zmienna `NETWORK_HOST` jest kluczowa dla funkcjonalności kodów QR. Jeśli nie zostanie ustawiona poprawnie, kody QR nie będą wskazywać adresu IP lub nazwy domeny Twojego serwera, przez co będą niedostępne na urządzeniach mobilnych.

### 4. Zbuduj aplikację
- Zbuduj aplikację, uruchamiając: `docker compose up`

To spowoduje:
- Zbudowanie obrazów Dockera dla aplikacji Django i Nginx
- Uruchomienie bazy danych PostgreSQL
- Uruchomienie aplikacji Django z Gunicorn
- Uruchomienie serwera WWW Nginx

### 5. Wykonaj migracje bazy danych i utwórz superużytkownika
Uruchom skrypt, aby utworzyć superużytkownika i wykonać migracje Django.
```sh
./scripts/manage_django.sh
```

### 6. Uzyskaj dostęp do aplikacji

Twoja aplikacja będzie dostępna pod adresem:
- `http://localhost/warehouse/` (jeśli korzystasz z tej samej maszyny)
- `http://twoj-adres-ip/warehouse` (jeśli korzystasz z innych urządzeń w sieci).  
Upewnij się, że używasz `http`, a nie `https`. Ponieważ aplikacja nie posiada domeny ani certyfikatu, https nie może być używane.

Sprawdź swój adres IP poleceniem:
```sh
# Na macOS
ipconfig getifaddr en0

# Na Linux
hostname -I | awk '{print $1}'
```

### (Opcjonalnie). Uruchom skrypt przebudowy statycznych plików

Ten krok jest wymagany tylko, jeśli napotkasz problemy z ładowaniem plików statycznych.

**Objawy:**  
- Brak stylów CSS  
- Niedziałająca funkcjonalność JavaScript  
- Brak obrazów  
- Konsola przeglądarki pokazuje błędy 404 dla plików statycznych

**Rozwiązania:**  
1. Wykonaj twarde odświeżenie przeglądarki (Ctrl+F5 lub Cmd+Shift+R)  
2. Uruchom skrypt `sudo ./scripts/rebuild_static.sh`  
3. (jeśli 2 nie pomogło) Wyczyść pamięć podręczną przeglądarki

Skrypt ten:
- Zatrzyma wszystkie kontenery  
- Wyczyści katalog staticfiles  
- Utworzy wymagane katalogi z odpowiednimi uprawnieniami  
- Przebuduje i ponownie uruchomi kontenery  
- Uruchomi polecenie collectstatic

## Rozwiązywanie problemów

1. Upewnij się, że nie pominąłeś żadnego kroku, szczególnie uruchomienia wymaganych skryptów (`set_network_ip.sh` i `manage.django.sh`)

1. Sprawdź, czy wszystkie kontenery działają:
   `docker compose ps`

2. Sprawdź logi pod kątem błędów:
   `docker compose logs`

3. Zweryfikuj poprawność konfiguracji Nginx:
   `docker compose exec nginx nginx -t`

4. Upewnij się, że zapora sieciowa pozwala na ruch na porcie 80.