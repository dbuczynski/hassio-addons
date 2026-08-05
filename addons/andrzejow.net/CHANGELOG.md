# Changelog - Koło Fortuny by Weekendowy Detektorysta (andrzejow.net)

Wszystkie istotne zmiany w projekcie będą dokumentowane w tym pliku.

## [1.7.2] - 2026-08-05

### Naprawiono
- **Naprawiono pobieranie komentarzy spod wybranego filmu (`get_all_comments_for_video`)**: Dodano brakujący alias dla nazwy funkcji w `youtube_service.py`, co całkowicie rozwiązało błąd `module 'youtube_service' has no attribute 'get_all_comments_for_video'` przy ładowaniu komentarzy filmu.

---

## [1.7.1] - 2026-08-05

### Naprawiono
- **Naprawiono błąd `get_channel_videos()`**: Zaktualizowano sygnaturę funkcji w `youtube_service.py`, eliminując błąd `unexpected keyword argument 'channel_handle'` przy pobieraniu listy filmów.

### Dodano / Zmieniono
- **Nowy Przycisk `🎬 Lista filmów`**: Dodano w prawym górnym rogu paska nawigacji (obok *Własna lista* i *Ustawienia*), pozwalający w dowolnym momencie przejść do widoku filmów.
- **Strona Startowa (`LandingPage.html`)**:
  - Dodano elegancką stronę startową ładowaną z pliku `LandingPage.html` z opisem funkcji i przyciskami szybkiego dostępu.
  - W przypadku braku zdefiniowanego klucza API (globalnego lub własnego w sesji) aplikacja **automatycznie otwiera okno Ustawień**, pozwalając od razu podać klucz.

---

## [1.7.0] - 2026-08-05

### Dodano
- **Własna Lista Użytkowników (Import CSV / TXT / Pole tekstowe)**:
  - Dodano przycisk **`📋 Własna lista`** na pasku nawigacyjnym oraz na ekranie z listą filmów.
  - Opcja wgrywania własnego pliku `.csv` lub `.txt` z listą użytkowników (jedna osoba na linijkę lub rozdzieleni przecinkami).
  - Pole tekstowe do bezpośredniego wklejania własnych loginów.
  - Wykorzystanie **istniejącego silnika Koła Fortuny** – przejście bezpośrednio do widoku z kołem, filtrami, listą autorów, pomiarem mocy startu i wskaźnikiem *Live HUD*.
  - Gdy koło zakręci się dla własnej listy użytkowników, wyświetla czysto i czytelnie **samą nazwę wybranego użytkownika** (bez zbędnej sekcji komentarza).
