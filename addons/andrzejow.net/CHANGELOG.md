# Changelog - Koło Fortuny by Weekendowy Detektorysta (andrzejow.net)

Wszystkie istotne zmiany w projekcie będą dokumentowane w tym pliku.

## [1.7.3] - 2026-08-05

### Dodano / Zmieniono (Optymalizacja UI i Układu)
- **Przycisk Trybu Pełnoekranowego `⛶ Pełny ekran`**: Dodano w głównym menu nawigacji. Po kliknięciu uruchamia tryb `Fullscreen` przeglądarki (ukrywając pasek adresu URL, karty oraz boczne menu Home Assistant).
- **Nagłówek w Jednej Linii**: Przycisk `← Powrót do listy filmów`, tytuł wybranego filmu oraz przycisk `📥 Pobierz plik CSV` umieszczono w **jednym poziomym rzędzie**, drastycznie zmniejszając zużycie miejsca na wysokość (zaznaczone na czerwono).
- **Scalony Pasek Wyszukiwania i Checkboxów**: Pole wyszukiwania frazy przeniesiono do tego samego rzędu co checkbox-y filtrów i licznik wyników (zaznaczone na żółto).
- **Poszerzony Kontener Aplikacji (`max-width: 1750px / 96%`)**: Zwiększono szerokość całego interfejsu (zaznaczone na zielono), dzięki czemu koło, tabele i lista użytkowników optymalnie wykorzystują szerokie ekrany monitorów.

---

## [1.7.2] - 2026-08-05

### Naprawiono
- **Naprawiono pobieranie komentarzy spod wybranego filmu (`get_all_comments_for_video`)**: Dodano brakujący alias dla nazwy funkcji w `youtube_service.py`, co całkowicie rozwiązało błąd `module 'youtube_service' has no attribute 'get_all_comments_for_video'` przy ładowaniu komentarzy filmu.

---

## [1.7.1] - 2026-08-05

### Naprawiono
- **Naprawiono błąd `get_channel_videos()`**: Zaktualizowano sygnaturę funkcji w `youtube_service.py`, eliminując błąd `unexpected keyword argument 'channel_handle'` przy pobieraniu listy filmów.
