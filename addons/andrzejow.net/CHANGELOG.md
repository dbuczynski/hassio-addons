# Changelog - Koło Fortuny by Weekendowy Detektorysta (andrzejow.net)

Wszystkie istotne zmiany w projekcie będą dokumentowane w tym pliku.

## [1.7.0] - 2026-08-05

### Dodano
- **Własna Lista Użytkowników (Import CSV / TXT / Pole tekstowe)**:
  - Dodano przycisk **`📋 Własna lista`** na pasku nawigacyjnym oraz na ekranie z listą filmów.
  - Opcja wgrywania własnego pliku `.csv` lub `.txt` z listą użytkowników (jedna osoba na linijkę lub rozdzieleni przecinkami).
  - Pole tekstowe do bezpośredniego wklejania własnych loginów.
  - Wykorzystanie **istniejącego silnika Koła Fortuny** – przejście bezpośrednio do widoku z kołem, filtrami, listą autorów, pomiarem mocy startu i wskaźnikiem *Live HUD*.
  - Gdy koło zakręci się dla własnej listy użytkowników, wyświetla czysto i czytelnie **samą nazwę wybranego użytkownika** (bez zbędnej sekcji komentarza).

---

## [1.6.2] - 2026-08-05

### Dodano
- **Kanał `@ArturK92`**: Dodano kanał `@ArturK92` (ArturK92) do listy dozwolonych kanałów (`ALLOWED_CHANNELS`).

---

## [1.6.1] - 2026-08-05

### Dodano / Naprawiono / Zmieniono
- **Odliczanie Czasu w Czasie Kręcenia**: Podczas obrotu koła fortuny etykieta przy suwaku dynamicznie maleje (np. `15s` ➔ `14s` ➔ `...` ➔ `0s`), co dokładnie wskazuje, ile sekund pozostało do zatrzymania koła.
- **Dynamiczne Przyciski (Start / Restart)**:
  - Podczas kręcenia przycisk Start automatycznie znika.
  - W jego miejscu pojawia się czerwony przycisk **`🔄 RESTARTUJ`**, który umożliwia natychmiastowe przerwanie obrotu, zresetowanie stanu koła i ponowne wyświetlenie przycisku Start.
- **Krótszy Opis Przycisku Start**: Usunięto tekst `(PRZYTRZYMAJ START)`, skracając etykietę do zwięzłego `🎯 WYBIERZ CIEKAWY KOMENTARZ` oraz zwężając szerokość przycisku z `480px` do zgrabnego `320px`.

---

## [1.6.0] - 2026-08-05

### Dodano / Zmieniono
- **Okienko Live HUD Ticker ("on a top") nad Kołem Fortuny**:
  - Dodano dedykowane okienko nad wykresem koła fortuny, które w czasie rzeczywistym (60 FPS) wyświetla aktualnie wskazywanego przez czerwoną strzałkę **autora oraz treść jego komentarza**.
  - Przy dużej liczbie użytkowników (> 50) napisy wewnątrz bardzo wąskich wycinków koła są automatycznie ukrywane, zapobiegając zlewaniu się tekstu i zapewniając idealną czytelność wykresu, przy jednoczesnym wyraźnym pokazywaniu każdego komentarza w górnym okienku Live HUD.

---

## [1.5.9] - 2026-08-05

### Dodano / Naprawiono / Zmieniono
- **Kanał `@ZlotyBazyliszek`**: Dodano kanał `@ZlotyBazyliszek` (Złoty Bazyliszek) do listy dozwolonych kanałów (`ALLOWED_CHANNELS`).
- **Naprawiono Szerokość Przycisku Start (`width: 480px`)**: Ustalono stałą szerokość przycisku start (`width: 480px; min-width: 480px`), dzięki czemu po zmianie tekstu z domyślnego na "MOC WSKAZANIA: X / 20" przycisk nie zmniejsza swoich wymiarów, a kursor myszy pozostaje idealnie w granicach przycisku niezależnie od tego, z której strony klikamy.
- **Zmiana Słownictwa**: Usunięto z interfejsu słowa sugerujące "losowanie" (np. "Zaproś do losowania") i zastąpiono je jednoznacznymi sformułowaniami dotyczącymi wyboru ciekawego komentarza (np. `🎯 WYBIERZ CIEKAWY KOMENTARZ (PRZYTRZYMAJ START)` oraz `🎉 WYBRANY AUTOR I KOMENTARZ 🎉`).
