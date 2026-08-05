# Changelog - Koło Fortuny by Weekendowy Detektorysta (andrzejow.net)

Wszystkie istotne zmiany w projekcie będą dokumentowane w tym pliku.

## [1.7.5] - 2026-08-05

### Zmieniono
- **Cofnięto nadpisywanie adresu (History API)**: Usunięto wywołanie `history.replaceState` i przywrócono standardowe działanie adresu URL oraz oryginalny tytuł strony `Koło Fortuny by Weekendowy Detektorysta`.

---

## [1.7.4] - 2026-08-05

### Dodano / Zmieniono
- **Zmienna ścieżka w pasku adresu (History API)**: Dodano wywołanie `history.replaceState(null, "", "/MetaleSzlachetnePolska.WeekendowyDetektorysta")`.
- **Tytuł strony w przeglądarce**: Zaktualizowano znacznik `<title>`.

---

## [1.7.3] - 2026-08-05

### Dodano / Zmieniono (Optymalizacja UI i Układu)
- **Przycisk Trybu Pełnoekranowego `⛶ Pełny ekran`**: Dodano w głównym menu nawigacji. Po kliknięciu uruchamia tryb `Fullscreen` przeglądarki (ukrywając pasek adresu URL, karty oraz boczne menu Home Assistant).
- **Nagłówek w Jednej Linii**: Przycisk `← Powrót do listy filmów`, tytuł wybranego filmu oraz przycisk `📥 Pobierz plik CSV` umieszczono w **jednym poziomym rzędzie**.
- **Scalony Pasek Wyszukiwania i Checkboxów**: Pole wyszukiwania frazy przeniesiono do tego samego rzędu co checkbox-y filtrów i licznik wyników.
- **Poszerzony Kontener Aplikacji (`max-width: 1750px / 96%`)**: Zwiększono szerokość całego interfejsu.
