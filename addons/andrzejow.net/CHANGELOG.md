# Changelog - Koło Fortuny by Weekendowy Detektorysta (andrzejow.net)

Wszystkie istotne zmiany w projekcie będą dokumentowane w tym pliku.

## [1.8.1] - 2026-08-05

### Dodano / Zmieniono
- **Dokumentacja & API w panelu**: Dodano sekcję instrukcji oraz przykładowe polecenia `curl` (zmiana klucza API, zarządzanie kanałami, token Discorda).
- **Zarządzanie Tokenem Discorda**: Dodano endpoint `POST /api/admin/set-discord-token` zapisujący token bota.
- **Zakładki i podział materiałów**: Dodano zakłady `🎬 Filmy`, `⚡ Shorts`, `🔴 Live`, `🌐 Wszystkie` oraz ulepszoną autodetekcję premier i archiwalnych streamów.
- **Odchudzenie interfejsu**: Zmieniono etykiety przycisków w navbarze na czytelne ikony oraz przycisk `🎬 YouTube`.

---

## [1.8.0] - 2026-08-05

### Dodano / Zmieniono
- **Usunięto opcję "Inny kanał (wpisz ręcznie)"**: Z rozwijanego menu w Ustawieniach usunięto możliwość wpisywania własnego kanału z ręki. Wybierać można wyłącznie kanały zatwierdzone i zarządzane przez serwer.
- **Dedykowane API Administracyjne Kanałów**:
  - `GET /youtube/api/admin/channels` – pobieranie aktualnej listy dozwolonych kanałów.
  - `POST /youtube/api/admin/channels/add` – dodawanie (lub aktualizacja) kanału w postaci `{"handle": "@NowyKanal", "title": "Opcjonalna Nazwa"}` z automatycznym rozwiązywaniem tytułu z YouTube API.
  - `POST /youtube/api/admin/channels/remove` lub `DELETE` – usuwanie kanału w postaci `{"handle": "@ArturK92"}`.
- **Trwała Konfiguracja Kanałów**: Zmiany w liście kanałów są zapisywane w pliku `global_config.json` w katalogu danych `/data`.

---

## [1.7.5] - 2026-08-05

### Zmieniono
- **Cofnięto nadpisywanie adresu (History API)**: Usunięto wywołanie `history.replaceState` i przywrócono standardowe działanie adresu URL oraz oryginalny tytuł strony `Koło Fortuny by Weekendowy Detektorysta`.
