# 📚 Dokumentacja & API Administracyjne Add-onu

Koło Fortuny by Weekendowy Detektorysta – dodatek do Home Assistant pozwalający na przeprowadzenie profesjonalnych losowań wśród komentarzy pod materiałami YouTube lub własnych list użytkowników.

---

## 💻 Polecenia `curl` do zarządzania API

Możesz zdalnie i administracyjnie zarządzać konfiguracją dodatku poprzez zapytania HTTP `curl`:

### 1. Zmiana globalnego klucza API YouTube na serwerze:
```bash
curl -X POST https://andrzejow.net/youtube/api/admin/set-global-key \
  -H "Content-Type: application/json" \
  -d '{"global_api_key": "AIzaSy_TWOJ_KLUCZ_API"}'
```

### 2. Dodanie nowego obsługiwanego kanału do listy:
```bash
curl -X POST https://andrzejow.net/youtube/api/admin/channels/add \
  -H "Content-Type: application/json" \
  -d '{"handle": "@NowyKanal", "title": "Opcjonalna Nazwa Kanału"}'
```

### 3. Usunięcie kanału z listy obsługiwanych:
```bash
curl -X POST https://andrzejow.net/youtube/api/admin/channels/remove \
  -H "Content-Type: application/json" \
  -d '{"handle": "@ArturK92"}'
```

### 4. Dodanie / zmiana tokenu bota Discord:
```bash
curl -X POST https://andrzejow.net/youtube/api/admin/set-discord-token \
  -H "Content-Type: application/json" \
  -d '{"discord_bot_token": "MTEyMzQ1Njc4OTA...TOKEN_BOTA"}'
```

### 5. Pobranie archiwalnej historii wygranych losowań:
```bash
curl -X GET https://andrzejow.net/youtube/api/admin/draw-history
```

---

## 🏷️ Zarządzanie Bazą Etykiet (API Generatora Etykiet)

Baza etykiet serwera jest zapisywana w pliku `labels_db.json`. Każda etykieta składa się z 8 elementów:
`["Rok", "Seria", "Nazwa", "Nakład", "Nominał", "WalutaPo", "Stop", "WalutaPrzed"]`

Przykład wpisu (złoty/dolar):
- `["2008", "", "Zbigniew Herbert (1924–1998)", "1 510 000", "2", "zł", "NG", ""]`
- `["2024", "Britannia", "King Charles III", "50 000", "5", "", "Ag999", "£"]`

### 1. Pobranie całej bazy etykiet:
```bash
curl -X GET https://andrzejow.net/MetaleSzlachetnePolska/etykiety/api/labels
```

### 2. Dodanie pojedynczej nowej etykiety na serwerze:
```bash
curl -X POST https://andrzejow.net/MetaleSzlachetnePolska/etykiety/api/admin/labels \
  -H "Content-Type: application/json" \
  -d '{
    "year": "2024",
    "series": "Britannia",
    "name": "King Charles III",
    "mintage": "50 000",
    "nominal": "5",
    "currency_after": "",
    "currency_before": "£",
    "stop": "Ag999"
  }'
```

### 3. Wypchnięcie gotowej całej nowej bazy etykiet (podmiana pliku `labels_db.json`):
```bash
curl -X POST https://andrzejow.net/MetaleSzlachetnePolska/etykiety/api/admin/labels \
  -H "Content-Type: application/json" \
  -d '{
    "labels": [
      ["2008", "", "Zbigniew Herbert (1924–1998)", "1 510 000", "2", "zł", "NG", ""],
      ["2024", "Britannia", "King Charles III", "50 000", "5", "", "Ag999", "£"]
    ]
  }'
```

### 4. Usunięcie etykiety z bazy serwera (po nazwie):
```bash
curl -X DELETE https://andrzejow.net/MetaleSzlachetnePolska/etykiety/api/admin/labels \
  -H "Content-Type: application/json" \
  -d '{"name": "Zbigniew Herbert (1924–1998)"}'
```

### 5. Ukryty panel masowego wgrywania monet z pliku CSV:
Dostęp do ukrytego panelu zarządzania monetami znajduje się pod adresem:
`https://andrzejow.net/MetaleSzlachetnePolska/etykiety/admin/add`
*(Lokalnie: `http://127.0.0.1:8080/MetaleSzlachetnePolska/etykiety/admin/add`)*

Panel oferuje:
- Pobranie wzorca CSV (`wzor_etykiet.csv`).
- Masowy import plików CSV / wklejanie danych w formularzu.
- Automatyczną detekcję duplikatów i zapis nowych monet na serwerze.

---

## 🔑 Wygenerowanie klucza YouTube Data API v3

1. Wejdź na stronę [Google Cloud Console](https://console.cloud.google.com/) i zaloguj się swoim kontem Google.
2. Stwórz nowy projekt lub wybierz istniejący w górnym menu.
3. Przejdź do zakładki **APIs & Services ➔ Library**.
4. Wyszukaj **YouTube Data API v3** i kliknij niebieski przycisk **Enable** (Włącz).
5. Przejdź do **APIs & Services ➔ Credentials**.
6. Kliknij **+ Create Credentials ➔ API key**.
7. Skopiuj wygenerowany klucz API (zaczyna się od `AIzaSy...`) i wklej go w Ustawieniach aplikacji w dodatku lub ustaw serwerowo poleceniem `curl`.

---

## 🤖 Wygenerowanie darmowego Bota i Tokenu Discord

1. Otwórz portal [Discord Developer Portal](https://discord.com/developers/applications).
2. Kliknij przycisk **New Application** w prawym górnym rogu i wpisz nazwę (np. `KoloFortunyBot`).
3. Z menu po lewej stronie wybierz zakładkę **Bot**.
4. Kliknij **Reset Token** (lub *Copy Token*), aby pobrać swój **Bot Token**. Przechowuj go w bezpiecznym miejscu!
5. Przewiń stronę w dół do sekcji **Privileged Gateway Intents**.
6. Zaznacz przełącznik przy **Message Content Intent** (umożliwia odczytanie treści wiadomości z kanału) i zapisz zmiany (**Save Changes**).

---

## 📩 Zaproszenie Bota na swój serwer Discord

1. W panelu [Discord Developer Portal](https://discord.com/developers/applications) wejdź w zakładkę **OAuth2 ➔ URL Generator**.
2. W sekcji **Scopes** zaznacz kratkę przy: `bot`.
3. W sekcji **Bot Permissions** zaznacz uprawnienia:
   - `Read Messages / View Channels`
   - `Read Message History`
4. Na dole strony pojawi się wygenerowany link URL. Skopiuj go i otwórz w nowej karcie przeglądarki.
5. Z listy wybierz swój serwer Discord i kliknij **Autoryzuj** (Authorize). Bot pojawi się na Twoim serwerze!
