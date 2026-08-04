# Changelog - YouTube Koło Fortuny Web Server (andrzejow.net)

Wszystkie istotne zmiany w projekcie będą dokumentowane w tym pliku.

## [1.5.3] - 2026-08-04

### Zmieniono
- Podbicie wersji dodatku Home Assistant do `1.5.3` z pełnym wymuszeniem aktualizacji z repozytorium GitHub.

---

## [1.5.2] - 2026-08-04

### Zmieniono / Dodano
- **Pełna izolacja sesji użytkowników**: Ustawienia (`api_key`, `channel_handle`, `target_users`) są od teraz zapisywane **wyłącznie w przeglądarce klienta** (`localStorage`).
- Każda przeglądarka i urządzenie posiada własne, niezależne ustawienia, które nie są widoczne dla innych użytkowników wchodzących na ten sam adres URL.
- Serwer działa w trybie bezstanowym proxy – nie zapisuje kluczy API użytkowników na dysku serwera.

---

## [1.5.1] - 2026-08-04

### Usunięto
- Usunięto domyślny klucz API z kodu źródłowego oraz plików konfiguracyjnych.
- Usunięto domyślną nazwę kanału oraz domyślną listę wyróżnionych użytkowników.

---

## [1.5.0] - 2026-08-04

### Dodano
- **Nowy układ 2-kolumnowy** w widoku komentarzy filmu.
- **Panel boczny z listą autorów**: Unikalna, posortowana alfabetycznie lista wszystkich użytkowników, którzy napisali komentarze pod danym filmem.
- **Sterowanie masowe autorami**: Checkbox `Zaznacz / Odznacz wszystko` oraz przycisk `Odwróć` dla listy autorów.
- **Filtr wykluczania autora kanału**: Nowy checkbox `Wyklucz autora kanału` (ukrywa komentarze oraz usuwa właściciela kanału z panelu autorów).
- **Filtr unikalności**: Checkbox `Unikalni użytkownicy (1 komentarz / osobę)`.
- Dynamiczne przefiltrowywanie panelu autorów po wpisaniu słowa w wyszukiwarkę.

---

## [1.2.1] - 2026-08-04

### Naprawiono
- Naprawiono błąd `KeyError: 'contentDetails'` występujący podczas parsowania listy filmów dla niektórych kanałów YouTube.
- Uodporniono rozpoznawanie kanałów po identyfikatorze, uchwycie `@handle` lub wyszukiwarce.

---

## [1.2.0] - 2026-08-03

### Zmieniono
- Domyślna strona pod adresem głównym (`/`) serwuje treść z pliku `default.html`.
- Aplikacja YouTube Koło Fortuny Online została przeniesiona pod dedykowany adres `https://URL/youtube`.

---

## [1.1.0] - 2026-08-03

### Dodano
- Serwer WWW oparty o Flask w kontenerze Home Assistant Add-on.
- Wyświetlanie listy najnowszych filmów z kanału (miniaturki, tytuły, daty publikacji, statystyki komentarzy).
- Pobieranie i prezentacja komentarzy pod wybranym filmem w responsywnej tabeli z wyróżnianiem użytkowników i eksportem do CSV.
- Modal ustawień umożliwiający bezpieczną edycję klucza API, nazwy kanału i wyróżnionych użytkowników.

---

## [1.0.1] - 2026-08-03

### Dodano
- Pierwotna wersja dodadku dla serwera WWW `andrzejow.net`.
