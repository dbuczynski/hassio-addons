# Changelog - Koło Fortuny by Weekendowy Detektorysta (andrzejow.net)

Wszystkie istotne zmiany w projekcie będą dokumentowane w tym pliku.

## [1.7.4] - 2026-08-05

### Dodano / Zmieniono
- **Zmienna ścieżka w pasku adresu (History API)**: Dodano wywołanie `history.replaceState(null, "", "/MetaleSzlachetnePolska.WeekendowyDetektorysta")`, dzięki czemu w pasku adresu po załadowaniu wyświetla się: `MetaleSzlachetnePolska.WeekendowyDetektorysta`.
- **Tytuł strony w przeglądarce**: Zaktualizowano znacznik `<title>` na `MetaleSzlachetnePolska.WeekendowyDetektorysta v1.7.4`.

---

## [1.7.3] - 2026-08-05

### Dodano / Zmieniono (Optymalizacja UI i Układu)
- **Przycisk Trybu Pełnoekranowego `⛶ Pełny ekran`**: Dodano w głównym menu nawigacji. Po kliknięciu uruchamia tryb `Fullscreen` przeglądarki (ukrywając pasek adresu URL, karty oraz boczne menu Home Assistant).
- **Nagłówek w Jednej Linii**: Przycisk `← Powrót do listy filmów`, tytuł wybranego filmu oraz przycisk `📥 Pobierz plik CSV` umieszczono w **jednym poziomym rzędzie**, drastically zmniejszając zużycie miejsca na wysokość (zaznaczone na czerwono).
- **Scalony Pasek Wyszukiwania i Checkboxów**: Pole wyszukiwania frazy przeniesiono do tego samego rzędu co checkbox-y filtrów i licznik wyników (zaznaczone na żółto).
- **Poszerzony Kontener Aplikacji (`max-width: 1750px / 96%`)**: Zwiększono szerokość całego interfejsu (zaznaczone na zielono), dzięki czemu koło, tabele i lista użytkowników optymalnie wykorzystują szerokie ekrany monitorów.
