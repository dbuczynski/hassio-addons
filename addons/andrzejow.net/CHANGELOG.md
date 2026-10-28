# Changelog - Web server andrzejow.net

Wszystkie istotne zmiany w projekcie będą dokumentowane w tym pliku.

## [1.14.1] - 2026-10-28

### Dodano / Zmieniono
- **Nowa Aplikacja Zbiór (`/zbior/` & `/zbior/admin`)**:
  - Powielono aplikację katalogową `wyprzedaz` na niezależną aplikację `zbior` korzystającą z osobnej bazy danych (`zbior_data/categories.json`, `zbior_data/products.json`, `zbior_data/uploads/`) oraz własnego eksportu/importu ZIP (`/api/zbior/export`, `/api/zbior/import`).
  - Dodano automatyczne przekierowania (`302`) niezależnie od wielkości liter i polskich znaków diakrytycznych dla `/zbior` (`/zbiór`, `/Zbiór`, `/ZBIÓR` itd.) oraz `/wyprzedaz` (`/wyprzedaż`, `/Wyprzedaz` itd.).
- **Archiwizacja Usuwanych Zdjęć (`images-archive`)**:
  - W obu aplikacjach (`wyprzedaz` oraz `zbior`) usunięcie zdjęcia z produktu podczas edycji lub całkowite usunięcie produktu przenosi nieużywane pliki graficzne do podfolderu `uploads/images-archive/` zamiast ich trwałego kasowania.
- **Kompaktowy Selektor Układu Wyświetlania (z zapisem w sesji)**:
  - W obu aplikacjach dodano zminimalizowany wizualnie selektor liczby elementów w rzędzie (`3`, `4`, `5`) oraz maksymalnej liczby elementów na stronie:
    - dla `3`: `6`, `9`, `12`, `wszystko`,
    - dla `4`: `8`, `12`, `16`, `wszystko`,
    - dla `5`: `10`, `15`, `20`, `wszystko`.
  - Wybór układu jest zapamiętywany w sesji przeglądarki (`sessionStorage` / `localStorage`), dzięki czemu zostaje zachowany po odświeżeniu strony.
- **Drzewo Kategorii dla Produktów z Zerowym Stanem**:
  - W drzewie kategorii w obu aplikacjach wyświetlane są również kategorie posiadające widoczne produkty ze stanem `0 szt.` (bez wliczania ich do sumy dostępnych sztuk w licznikach).

---

## [1.14.0] - 2026-10-28

### Dodano / Zmieniono
- **Aplikacja Wyprzedaż Sprzętu (`/wyprzedaz/` & `/wyprzedaz/admin`)**:
  - **Wybór Ilości Elementów na Stronie i Układu Siatki**: Dodano przełącznik liczby wyświetlanych produktów w galerii głównej:
    - `6 na stronę`: 2 rzędy po 3 elementy (`grid-cols-3`),
    - `12 na stronę`: 3 rzędy po 4 elementy (`grid-cols-4`),
    - `Wszystko`: po 5 elementów na rząd (`grid-cols-5`).
  - **Dopasowanie Grafik (`object-fit: contain`)**: Zdjęcia produktów na kartach galerii oraz w oknie szczegółów (wraz z miniaturami) są wyrównane i skalowane proporcjonalnie do dostępnego okna bez przycinania góry ani dołu.
  - **Tryb Pełnoekranowy Zdjęcia (Lightbox)**: Kliknięcie na aktualnie wyświetlane zdjęcie w oknie szczegółów przedmiotu otwiera je w trybie pełnoekranowym (maks. `95%` szerokości ekranu) z przyciskiem `✕` w prawym górnym rogu.
  - **Zamiana Miejscami Zdjęć w Edycji**: Dodano obsługę zmiany kolejności zdjęć przedmiotu za pomocą przycisków `◀` / `▶` oraz przeciągania myszką (`Drag & Drop`).
  - **Eksport i Import Bazy Danych ze Zdjęciami (ZIP)**: W górnej belce panelu administracyjnego dodano eksport pełnej bazy (`categories.json`, `products.json` oraz katalog `uploads/`) do pliku `.zip` oraz import z wyborem trybu:
    - **Dodaj (bez tworzenia duplikatów)**: dopisuje nowe kategorie, produkty i zdjęcia bez duplikowania istniejących pozycji,
    - **Nadpisz**: całkowicie usuwa lokalną bazę oraz zdjęcia przed wgraniem danych z archiwum.
  - **Parametr Lokalizacji Magazynowej (`lokalizacja`)**: Pole widoczne wyłącznie dla administratora oraz w galerii otwieranej z zaufanego adresu IP (`admin_trusted_ips`), z obsługą wyszukiwania w panelu admina.
  - **Wydzielony Widok Zarządzania Kategoriami**: Przeniesiono formularz dodawania/edycji kategorii do osobnej zakładki (`📁 Zarządzanie Kategoriami` / `/wyprzedaz/admin/kategorie`), oczyszczając widok edycji produktu.

---

## [1.13.0] - 2026-09-25

### Dodano / Zmieniono
- **Aplikacja Wyprzedaż Sprzętu (`/wyprzedaz/` & `/wyprzedaz/admin`)**:
  - **Przycisk "Zapisz jako nowy przedmiot"**: Dedykowana opcja przy edycji wybranego produktu pozwalająca zapisać jego modyfikację jako nowy osobny produkt.
  - **Przeliczanie Dostępnych Sztuk w Menu Bocznym**: Liczniki drzewa kategorii w panelu admina oraz galerii sumują łączną dostępną i widoczną ilość sztuk produktów (`ilosc`), zamiast unikalnych pozycji w bazie.
  - **Format `({n} szt)` w Galerii**: Nazwy na kartach produktów w galerii zawierają informację o liczbie sztuk w nawiasie przed nazwą przedmiotu.
  - **Informacja o Ilości w Tabeli Admina**: W tabeli edycji produktów dodano czytelną informację `(n szt)` obok nazwy przedmiotu.
  - **Bezpośrednie Linki URL (`?kategoria=ID` & `?produkt=ID`)**: Integracja `history.replaceState` i `URLSearchParams` pozwalająca na dzielenie się bezpośrednimi linkami do kategorii oraz wyskakujących okien ze szczegółami przedmiotu.
  - **Górne Stronnicowanie Nad Galerią**: Przeniesiono pasek stronnicowania wyłącznie nad siatkę produktów ze stałą widocznością przycisków stron.
  - **Wykrywanie Duplikatów Nazw na Żywo**: Automatyczna sugestia zwiększenia ilości sztuk (`+1 szt`), przejścia do edycji lub utworzenia osobnego wpisu przy wpisywaniu nazwy istniejącego produktu.
  - **Obsługa Aparatu / Kamery Lokalnej**: Wykonywanie i podgląd zdjęć prosto z kamery urządzenia w panelu admina z obsługą wyboru kamer (np. przednia / tylna).
  - **Nowa Baza Produktów w Kategorii Kryształy**: Wygenerowano 80 pozycji w kategorii P3 (kryształy).

---

## [1.12.1] - 2026-09-22

### Dodano / Zmieniono
- **Poprawka Budowania Kontenera Docker (`Dockerfile`)**:
  - Dodano brakującą instrukcję `COPY wyprzedaz_service.py /app/wyprzedaz_service.py` w pliku `Dockerfile`.
  - Naprawiono błąd uruchomienia kontenera `ModuleNotFoundError: No module named 'wyprzedaz_service'`.

---

## [1.12.0] - 2026-09-22

### Dodano / Zmieniono
- **Nowa Aplikacja Wyprzedaż Sprzętu (`/wyprzedaz/` & `/wyprzedaz/admin`)**:
  - **Publiczna Galeria (`/wyprzedaz/`)**:
    - Siatka kart produktów z podglądem zdjęć, badgami liczby zdjęć oraz oznaczeniami niedostępności (grayscale przy `ilosc == 0`).
    - Drzewo kategorii z licznikami widocznych produktów (w tym z podkategorii) oraz automatycznym ukrywaniem pustych kategorii (0 produktów).
    - Odrzucanie i ukrywanie produktów z błędną lub nieistniejącą kategorią z widoku publicznego.
    - Opcjonalne pole ceny oraz specjalna prezentacja ceny `0 PLN` jako **`🎁 Za darmo`**.
    - Wyszukiwarka z obsługą fraz ujętych w cudzysłowy oraz słów kluczowych (`AND`).
    - Ograniczenie wyświetlania do 6 produktów na stronę z pełnym stronnicowaniem (`▶ Poprzednia`, numery stron, `Następna ▶`).
  - **Panel Administracyjny Wyprzedaży (`/wyprzedaz/admin`)**:
    - Dostęp ograniczony wyłącznie do zaufanych adresów IP (`admin_trusted_ips`). Wyświetlanie przycisku nawigacyjnego "🔒 Panel Admina" wyłącznie dla zaufanych IP.
    - Dwukolumnowy układ z drzewem kategorii po lewej stronie i zarządzaniem produktami po prawej.
    - Tworzenie i edycja drzewa kategorii do 4 poziomów głębokości z automatycznym zapobieganiem pętlom i sortowaniem alfabetycznym.
    - Wskaźnik i filtr `⚠️ BŁĘDNA KATEGORIA` pozwalający natychmiast odnaleźć produkty wymagające przypisania kategorii.
    - Wyszukiwarka produktów w panelu admina z tokenizatorem fraz i słów kluczowych.
    - Bezszwowe zachowywanie trybu edycji przedmiotu po jego zapisaniu.

---

## [1.11.3] - 2026-09-05

### Dodano / Zmieniono
- **Uprawnienia Home Assistant API (`homeassistant_api: true`)**:
  - Dodano wymagane ustawienie `homeassistant_api: true` w `config.yaml`, umożliwiające Supervisorowi dostarczenie tokena autoryzacji (`SUPERVISOR_TOKEN`) dla kontenera.
- **Diagnostyka & Przycisk Testowy Telegram**:
  - Dodano szczegółowe logowanie diagnostyczne w funkcji `send_telegram_ha_notification` drukowane w dzienniku dodatku w Home Assistant (`[Telegram HA] ...`).
  - Dodano dedykowany endpoint `/MetaleSzlachetnePolska/etykiety/admin/test-telegram` oraz przycisk `✈️ Test Telegram` w panelu edycji monet do natychmiastowego testowania i weryfikacji powiadomień Telegram w przeglądarce.

---

## [1.11.2] - 2026-09-04

### Dodano / Zmieniono
- **Hierarchiczne Sortowanie Monet (Kraj -> Rocznik -> Stop -> Nominał -> Nazwa...)**:
  - Wdrożono spójne sortowanie wielokryterialne na stronie głównej oraz w panelu edycji monet według hierarchii: Kraj -> Rocznik -> Stop -> Nominał (numerycznie) -> Nazwa -> Seria -> Średnica (numerycznie) -> Waga (numerycznie) -> Rant -> Typ -> Trial.
  - Naprawiono parser wartości liczbowych (`parse_num_val`), co zapewnia poprawne sortowanie numeryczne nominale (np. `2 zł` przed `10 zł`), średnic oraz wag.
- **Wyświetlanie Wszystkich Monet w Panelu Edycji (`/admin/edit`)**:
  - Dodano opcję `Wszystkie` (`limit = 100000`) w przyciskach wyboru liczby pozycji, dostępną wyłącznie dla administratorów z rolą `admin`.
- **Podział Badgy Monet na 3 Osobne Tag-Boxy (`/etykiety`)**:
  - Rozdzielono dawny pojedynczy badge na 3 czytelne, estetyczne boxy: **Nominał & Waluta**, **Rok** oraz **Stop**.
- **Wyszukiwanie Zaawansowane (Cudzysłowy & Keywords Trial)**:
  - Obsługa ścisłych fraz w cudzysłowach (`"Husaria 3"` lub `'Husaria 3'`), słów kluczowych `trial`/`próba`/`proba` (filtrujących wyłącznie monety z flaga `TRIAL = True`) oraz wykluczenie pól rocznika, kraju i flagi trial z głównej szukajki tekstowej.
- **Eksport CSV z Formatowaną Datą oraz Integracja Powiadomień Telegram HA**:
  - Format daty w pliku eksportu całej bazy (`baza_etykiet_YYYY-MM-DD_HH-MM-SS.csv`) zawierającego kompletne 14 pól bazy.
  - Obsługa akcji powiadomień Telegram (`telegram_bot.send_message`) za pośrednictwem konfiguracji dodatku (`telegram_chat_id`, `telegram_config_entry_id`).

---

## [1.10.6] - 2026-09-03

### Dodano / Zmieniono
- **Dziennik Zdarzeń i Aktywności (Logs)**:
  - Trwały zapis logów aktywności w pliku `activity_logs.json` odporny na restarty kontenera.
  - Rejestracja wejść na strony (`page_view`), wydruków etykiet z parametrami monet (`label_print`) oraz wyników losowań Koła Fortuny (`wheel_draw` z wygranym, filmem, filtrami i uczestnikami).
  - Dedykowany podgląd human-friendly pod adresem `/logs` dostępny wyłącznie z zaufanych adresów IP (`admin_trusted_ips`).
  - Zwięzły, jednolinijkowy układ tabeli z rozwijanymi szczegółami (Accordion Drawer) dla każdego zdarzenia.
- **Aktualizacja Grafik Portalu**:
  - Podmiana ikony Discorda na nową oficjalną ikonę `metale_polska_icon.webp` we wszystkich nagłówkach nawigacyjnych.
  - Umieszczenie baneru portalu `metale_polska.webp` w sekcji nagłówkowej ekranu głównego.
- **Poprawka Formatowania Uczestników**: Poprawiono bezpieczne formatowanie uczestników losowań w konsoli serwera.

---

## [1.10.5] - 2026-09-03

### Dodano / Zmieniono
- **Poprawka Usuwania Monet w Edytorze**: Zaktualizowano endpoint `DELETE /api/admin/labels` oraz funkcję `deleteRow` w edytorze monet (`admin_edit.html`) o pełną obsługę parametrów `label` i `name`, zapobiegając błędom walidacji.

---

## [1.10.4] - 2026-09-03

### Dodano / Zmieniono
- **Obsługa `/data/options.json` w Home Assistant**: Dodano integrację funkcji `load_all_config_data()`, która automatycznie wczytuje i stosuje opcje zapisywane przez Home Assistant Supervisor w `/data/options.json` (w tym dodane zaufane adresy IP oraz zmodyfikowane hasło `admin_password`).

---

## [1.10.3] - 2026-09-03

### Dodano / Zmieniono
- **Strukturyzacja Opcji w `config.yaml`**: Przejrzysty podział opcji na sekcje (`Metale Szlachetne Polska - Youtube` oraz `Metale Szlachetne Polska - Generator etykiet`).
- **Zabezpieczenie Domyślnego Hasła `admin`**: Blokada możliwości logowania hasłem `admin` dla połączeń z niezaufanych adresów IP wraz z wymogiem zmiany hasła w konfiguracji Home Assistant.
- **Domyślny Zaufany Adres IP**: W domyślnej konfiguracji dodatku pozostawiono wyłącznie pętlę zwrotną `127.0.0.1`.
- **Wykluczenie Pliku Bazy Użytkowników z Gita**: Dodano plik `.gitignore` i wykluczono `labels_users.json` z repozytorium GitHub, aby chronić dane użytkowników lokalnych.

---

## [1.10.2] - 2026-09-03

### Dodano / Zmieniono
- **Przycisk "Zapisz Wszystkie Zmiany" (`/admin/edit`)**: Dodano zielony przycisk `💾 Zapisz Wszystkie Zmiany` w panelu edycji monet wraz z dedykowanym endpointem `POST /api/admin/labels/update-batch`, umożliwiającym masowy zapis zmodyfikowanych wierszy.
- **Jednolity Pasek Nawigacyjny w Panelu Administracyjnym**: Ujednolicono belkę nawigacyjną we wszystkich plikach panelu admina (`admin_add.html`, `admin_edit.html`, `admin_users.html`) wraz ze spójnymi linkami i wyróżnianiem wyłącznie aktywnej podstrony.
- **Ujednolicenie Nagłówków & Ikony Social Media**: 
  - Przeniesiono odznaki wersji do podtytułów (`v1.10.2 by @WeekendowyDetektorysta`) we wszystkich aplikacjach.
  - Dodano klikalne ikony Facebooka i YouTube'a w nagłówkach.
  - Naprawiono układ nagłówka (wyrównanie od lewej strony obok ikony Discorda) poprzez eliminację niepoprawnego zagnieżdżenia znaczników `<a>`.
  - W aplikacji Koło Fortuny dodano dynamiczne wyświetlanie nazwy obecnie wybranego kanału w tytule: `Koło Fortuny (<nazwa_kanału>)`.

---

## [1.10.1] - 2026-09-03

### Dodano / Zmieniono
- **Dodanie Adresu `127.0.0.1` do Zaufanych IP**: Dodano pętlę zwrotną `127.0.0.1` do domyślnej listy zaufanych adresów IP (`admin_trusted_ips`), umożliwiając bezpośrednie logowanie administracyjne samą nazwą użytkownika w środowisku lokalnym.

---

## [1.10.0] - 2026-09-03

### Dodano / Zmieniono
- **System Logowania & Autoryzacja Zaufanych IP**: Zabezpieczono panel administracyjny `/MetaleSzlachetnePolska/etykiety/admin`. Zaufane adresy IP (`admin_trusted_ips`, domyślnie `195.74.49.211`, `192.168.12.223`) wymagają jedynie nazwy użytkownika. Pozostałe IP wymagają podania loginu i hasła.
- **Zarządzanie Użytkownikami (`/admin/users`)**: Tworzenie, modyfikacja haseł oraz usuwanie użytkowników bazy aplikacji (dostęp wyłącznie dla konta z rolą `admin`).
- **Wygasanie Sesji po 10 minutach bezczynności**: Automatyczne unieważnianie sesji po 10 minutach z odnawianiem ważności po otwarciu stron generatora etykiet.
- **Panel Edycji Monet (`/admin/edit`)**: Przeglądanie monet z wyszukiwarką max 50 wyników, edycja pól wiersza na żywo, usuwanie pozycji oraz eksport całej bazy do pliku CSV (`/admin/export-csv`).

---

## [1.9.2] - 2026-09-03

### Dodano / Zmieniono
- **Inicjalizacja Domyślnej Bazy Monet**: Poprawiono `load_labels_db()`, aby w sytuacji, gdy plik `/data/labels_db.json` w trwałej pamięci Home Assistant był pusty `[]` lub nie istniał, dodatek automatycznie załadował i zapisał domyślną bazę monet dołączoną do obrazu kontenera (`DEFAULT_LABELS_DB_PATH`).

---

## [1.9.1] - 2026-09-03

### Dodano / Zmieniono
- **Przekierowania URL (Redirects)**: Dodano automatyczne przekierowania z adresów `/MSP`, `/msp`, `/metaleszlachetnePolska` oraz `/METALESZLACHETNEPOLSKA` na portal główny `/MetaleSzlachetnePolska`.
- **Ogólna Nazwa Serwisu**: Zmiana nazwy dodatku w `config.yaml` na `Web server andrzejow.net` – aplikacja stanowi ogólny serwer WWW hostujący moduły wewnętrzne serwisu `andrzejow.net`.

---

## [1.9.0] - 2026-09-03

### Dodano / Zmieniono
- **Generator Etykiet dla Metali Szlachetnych**: Nowy moduł `/MetaleSzlachetnePolska/etykiety` z wyszukiwarką bazy monet i tworzeniem etykiet w sesji.
- **Obsługa Walut i Formatu**: Dodano pole waluty przed/po nominału (`$`, `£`, `zł`, `EUR`), bezspacyjną typografię i nakład z separatorem tysięcznym.
- **Jednoliniowe Etykiety i Grupowanie**: Wyodrębnienie etykiet niższych (5.7mm) dla samej serii/nazwy (`Górna`) lub nominału (`Dolna`) z automatycznym grupowaniem i podglądem łączonym na 1 stronie A4.
- **Ukryta Strona Wgrywania CSV**: Dostępny pod niepodlinkowanym adresem `/MetaleSzlachetnePolska/etykiety/admin/add` panel masowego wgrywania monet z CSV z weryfikacją duplikatów.

---

## [1.8.3] - 2026-08-05

### Dodano / Zmieniono
- **Stabilny Live HUD Ticker**: Usztywniono wysokość okienka podglądu komentarzy do 70px oraz ograniczono podgląd do pojedynczej linijki z wielokropkiem, co wyeliminowało przeskakiwanie i skakanie koła fortuny w pionie podczas obrotu.

---

## [1.8.2] - 2026-08-05

### Dodano / Zmieniono
- **Szybki Wybór Kanału w Nagłówku**: Dodano listę rozwijaną kanałów w prawym górnym rogu navbara dla natychmiastowego przełączania profilu i filmików.
- **Profil Aktywnego Kanału na Stronie Startowej**: Wyświetlanie baneru, avatara, nazwy, statystyk (subskrybenci, wideo) i opisu wybranego kanału.
- **Płynny Suwak Materiałów**: Zamieniono dropdown w Ustawieniach na suwak od 10 do 100 materiałów ze skokiem 5.
- **Kompaktowe Oznaczenie Wyróżnionych**: Zamieniono pigułkę wyróżnionego widzów na małą złotą gwiazdkę `⭐` wyświetlaną bezpośrednio przed nazwą użytkownika.
- **Wyrównanie Nagłówka**: Dopasowano wysokość przycisków nawigacyjnych (`38px`) do listy rozwijanej bez załamywania wierszy.
- **Przeniesienie Dokumentacji do DOCS.md**: Instrukcje administracyjne API `curl` przeniesiono do pliku `DOCS.md` dodatku Home Assistant.

---

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
