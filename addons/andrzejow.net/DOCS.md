# 📚 Dokumentacja & API Administracyjne Add-onu

Web server andrzejow.net – dodatek do Home Assistant z aplikacjami wewnętrznymi:
- **Metale Szlachetne Polska**: Generator etykiet na holdery monet (`/MetaleSzlachetnePolska/etykiety`).
- **Koło Fortuny by Weekendowy Detektorysta**: Aplikacja do losowań z YouTube (`/MetaleSzlachetnePolska/youtube`).

---

## 🔐 System Logowania i Bezpieczeństwo Panelu Administracyjnego

Wszystkie trasy administracyjne modułu etykiet (`/MetaleSzlachetnePolska/etykiety/admin/*`) są zabezpieczone autoryzacją sesyjną i regułami IP:

### 1. Zaufane Adresy IP (`admin_trusted_ips`)
W konfiguracji dodatku Home Assistant (`config.yaml`) można zdefiniować listę zaufanych adresów IP (domyślnie `195.74.49.211` oraz `192.168.12.223`).
- W przypadku połączeń z tych adresów wystarczy podać **nazwę użytkownika** (hasło jest pomijane).

### 2. Standardowe Logowanie (Pozostałe Adresy IP)
W przypadku połączeń z innych adresów IP użytkownik musi podać poprawną nazwę użytkownika oraz hasło:
- Domyślne konto administratora: **`admin`** z hasłem `admin_password` zdefiniowanym w konfiguracji HA.
- Dodatkowi użytkownicy dodani przez administratora w panelu `/admin/users`.

### 3. Wygasanie Sesji (10 minut)
- Sesja wygasa automatycznie po **10 minutach bezczynności**.
- Każde wejście lub odświeżenie dowolnej strony w obszarze `/MetaleSzlachetnePolska/etykiety/*` przedłuża aktywność sesji o kolejne 10 minut.

---

## 🛠️ Trasy Administracyjne Generatora Etykiet

- **Logowanie**: `/MetaleSzlachetnePolska/etykiety/admin/login`
- **Edytor Bazy Monet**: `/MetaleSzlachetnePolska/etykiety/admin/edit`
  *(Edycja wierszy na żywo, usuwanie pozycji, wyszukiwanie oraz przycisk pobierania pliku CSV)*
- **Zarządzanie Użytkownikami**: `/MetaleSzlachetnePolska/etykiety/admin/users`
  *(Dostępne wyłącznie dla konta z rolą `admin` – tworzenie, zmiana haseł i ról użytkowników)*
- **Masowe Wgrywanie CSV**: `/MetaleSzlachetnePolska/etykiety/admin/add`
  *(Formularz importu i wklejania danych z detekcją duplikatów)*
- **Eksport Całej Bazy (CSV)**: `/MetaleSzlachetnePolska/etykiety/admin/export-csv`

---

## 🏷️ Zarządzanie Bazą Etykiet (API Generatora Etykiet)

Baza etykiet serwera jest zapisywana w pliku `labels_db.json`. Każda etykieta składa się z 8 elementów:
`["Rok", "Seria", "Nazwa", "Nakład", "Nominał", "WalutaPo", "Stop", "WalutaPrzed"]`

Przykład wpisu (złoty/dolar/funt):
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

### 3. Usunięcie etykiety z bazy serwera:
```bash
curl -X DELETE https://andrzejow.net/MetaleSzlachetnePolska/etykiety/api/admin/labels \
  -H "Content-Type: application/json" \
  -d '{"name": "Zbigniew Herbert (1924–1998)"}'
```

---

## 💻 Polecenia `curl` dla Koła Fortuny (YouTube)

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
