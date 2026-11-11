import os
import io
import csv
import re
import time
import json
import uuid
import shutil
import urllib.request
from datetime import datetime
from werkzeug.utils import secure_filename

DEFAULT_SHEETS_CSV_URL = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vQ_69XhwIdS7SMtX14UziMkzylOTfGbN6gvWhq9yERPME2ckY-yK9Oz4nTJACznkt1Sb81BOLgYL2QE/"
    "pub?gid=906110529&single=true&output=csv"
)

CACHE_TTL_SECONDS = 300  # 5 minut
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".avif"}


def _migrate_legacy_kolekcja_data(data_dir_base, target_data_dir):
    """
    Jeśli na dysku istnieje dawny folder 'kolekcja_data', przenosi z niego
    wgrane zdjęcia oraz pliki pamięci podręcznej do nowego folderu 'katalog_data'.
    """
    legacy_dir = os.path.join(data_dir_base, "kolekcja_data")
    if not os.path.isdir(legacy_dir) or os.path.abspath(legacy_dir) == os.path.abspath(target_data_dir):
        return

    try:
        os.makedirs(target_data_dir, exist_ok=True)
        target_uploads = os.path.join(target_data_dir, "uploads")
        os.makedirs(target_uploads, exist_ok=True)

        legacy_uploads = os.path.join(legacy_dir, "uploads")
        if os.path.isdir(legacy_uploads):
            for fname in os.listdir(legacy_uploads):
                src = os.path.join(legacy_uploads, fname)
                dst = os.path.join(target_uploads, fname)
                if os.path.isfile(src) and not os.path.exists(dst):
                    shutil.move(src, dst)

        legacy_csv = os.path.join(legacy_dir, "kolekcja_cache.csv")
        target_csv = os.path.join(target_data_dir, "katalog_cache.csv")
        if os.path.isfile(legacy_csv) and not os.path.exists(target_csv):
            shutil.move(legacy_csv, target_csv)

        legacy_meta = os.path.join(legacy_dir, "kolekcja_meta.json")
        target_meta = os.path.join(target_data_dir, "katalog_meta.json")
        if os.path.isfile(legacy_meta) and not os.path.exists(target_meta):
            shutil.move(legacy_meta, target_meta)

        # Usuń stary folder, jeśli jest już pusty
        if os.path.isdir(legacy_uploads) and not os.listdir(legacy_uploads):
            os.rmdir(legacy_uploads)
        if not os.listdir(legacy_dir):
            os.rmdir(legacy_dir)
    except Exception as e:
        print(f"[KatalogService] Ostrzeżenie podczas migracji kolekcja_data -> katalog_data: {e}", flush=True)


def get_katalog_paths(data_dir_base, data_subdir="katalog_data"):
    data_dir = os.path.join(data_dir_base, data_subdir)
    uploads_dir = os.path.join(data_dir, "uploads")
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(uploads_dir, exist_ok=True)
    _migrate_legacy_kolekcja_data(data_dir_base, data_dir)
    return {
        "data_dir": data_dir,
        "uploads_dir": uploads_dir,
        "csv_file": os.path.join(data_dir, "katalog_cache.csv"),
        "meta_file": os.path.join(data_dir, "katalog_meta.json"),
    }


def _parse_float(raw_str):
    if not raw_str:
        return None
    s = str(raw_str).strip()
    if not s or s == "-" or s.startswith("#"):
        return None
    # Usuń spacje (w tym twarde spacje \xa0 i \u202f)
    s = re.sub(r"[\s\xa0\u202f]+", "", s)
    # Wyciągnij pierwszą liczbę (z przecinkiem lub kropką)
    m = re.search(r"(\d+(?:[.,]\d+)?)", s)
    if not m:
        return None
    try:
        return float(m.group(1).replace(",", "."))
    except ValueError:
        return None


def _normalize_photo_url(raw_url):
    u = (raw_url or "").strip()
    if not u or u == "-":
        return ""
    if u.lower().startswith("/kolekcja/uploads/"):
        return "/katalog/uploads/" + u[len("/kolekcja/uploads/"):]
    return u


class KatalogService:
    def __init__(
        self,
        data_dir_base,
        data_subdir="katalog_data",
        csv_url=DEFAULT_SHEETS_CSV_URL,
        cache_ttl=CACHE_TTL_SECONDS,
    ):
        self.csv_url = csv_url
        self.cache_ttl = cache_ttl
        self.paths = get_katalog_paths(data_dir_base, data_subdir=data_subdir)
        self._memory_cache = None
        self._memory_cache_mtime = 0
        self._memory_cache_loaded_iso = None

    def _get_cache_age(self):
        csv_path = self.paths["csv_file"]
        if not os.path.exists(csv_path):
            return None
        try:
            mtime = os.path.getmtime(csv_path)
            return max(0.0, time.time() - mtime)
        except OSError:
            return None

    def ensure_fresh_csv(self, force=False):
        """
        Sprawdza wiek lokalnej kopii pliku CSV.
        Jeśli plik nie istnieje, jest starszy niż 5 minut (300 s) lub force=True,
        pobiera świeżą wersję z Google Sheets i zapisuje lokalną kopię.
        Zwraca słownik z informacją o statusie synchronizacji.
        """
        csv_path = self.paths["csv_file"]
        meta_path = self.paths["meta_file"]
        age = self._get_cache_age()

        refreshed = False
        error_msg = None

        if force or age is None or age >= self.cache_ttl:
            try:
                req = urllib.request.Request(
                    self.csv_url,
                    headers={"User-Agent": "andrzejow.net-katalog/1.0"},
                )
                with urllib.request.urlopen(req, timeout=15) as resp:
                    raw_bytes = resp.read()
                text = raw_bytes.decode("utf-8")

                tmp_path = csv_path + ".tmp"
                with open(tmp_path, "w", encoding="utf-8", newline="") as f:
                    f.write(text)
                os.replace(tmp_path, csv_path)

                now_ts = time.time()
                meta = {
                    "last_sync_ts": now_ts,
                    "last_sync_iso": datetime.fromtimestamp(now_ts).strftime("%Y-%m-%d %H:%M:%S"),
                    "source_url": self.csv_url,
                }
                with open(meta_path, "w", encoding="utf-8") as mf:
                    json.dump(meta, mf, ensure_ascii=False, indent=2)

                refreshed = True
                age = 0.0
            except Exception as e:
                error_msg = str(e)
                print(f"[KatalogService] Błąd odświeżania CSV z Google Sheets: {e}", flush=True)

        mtime = os.path.getmtime(csv_path) if os.path.exists(csv_path) else 0
        return {
            "refreshed": refreshed,
            "cache_age_seconds": round(age, 1) if age is not None else None,
            "last_modified_iso": (
                datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S") if mtime else None
            ),
            "error": error_msg,
        }

    def get_items(self, is_trusted=False, force_sync=False):
        """
        Zwraca listę monet z lokalnej kopii CSV (odświeżając ją jeśli starsza niż 5 minut)
        oraz metadane synchronizacji.
        Dla zapytań spoza zaufanego IP ukrywa informację o stanie posiadania.
        """
        sync_info = self.ensure_fresh_csv(force=force_sync)
        csv_path = self.paths["csv_file"]
        read_now_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sync_info["db_read_iso"] = read_now_iso

        if not os.path.exists(csv_path):
            return {"items": [], "sync": sync_info}

        mtime = os.path.getmtime(csv_path)
        if self._memory_cache is None or self._memory_cache_mtime != mtime:
            items = []
            try:
                with open(csv_path, "r", encoding="utf-8") as f:
                    content = f.read()

                reader = csv.DictReader(io.StringIO(content))
                for idx, row in enumerate(reader, start=2):
                    emitent = (row.get("Emitent") or "").strip()
                    nazwa = (row.get("Nazwa") or "").strip()
                    typ = (row.get("Typ") or "").strip()

                    # Pomiń wiersze nagłówkowe/separatory sekcji (gdzie Emitent to '-' lub pusty)
                    if not nazwa or emitent in ("", "-"):
                        continue

                    stan = (row.get("Stan") or "").strip()
                    dodatkowe_info = (row.get("Dodatkowe info") or "").strip()
                    nominal = (row.get("Nominał") or "").strip()
                    rok = (row.get("Rok") or "").strip()
                    lp = (row.get("L.p.") or "").strip()
                    stop = (row.get("Stop") or "").strip()
                    waga = (row.get("Waga") or "").strip()
                    ksztalt = (row.get("Kształt") or "").strip()
                    srednica = (row.get("Średnica") or "").strip()
                    koszt = (row.get("Koszt") or "").strip()
                    value = (row.get("Value") or "").strip()
                    estymacja = (row.get("estymacja") or "").strip()
                    zakup = (row.get("Zakup") or "").strip()
                    platforma = (row.get("Platforma") or "").strip()
                    zdjecia_raw = (row.get("Zdjęcia") or row.get("Zdjecia") or row.get("Identyfikator") or "").strip()
                    zdjecia_list = [
                        _normalize_photo_url(u)
                        for u in re.split(r"[;\n\r]+", zdjecia_raw)
                        if _normalize_photo_url(u)
                    ]
                    identyfikator = (row.get("Identyfikator") or "").strip()
                    czystego_ag = (row.get("Czystego Ag") or "").strip()
                    czystego_au = (row.get("Czystego Au") or "").strip()
                    naklad = (row.get("Nakład") or "").strip()
                    data_emisji = (row.get("Dataemisji") or "").strip()
                    cena_emisji = (row.get("Cena emisji") or "").strip()
                    awers = (row.get("Awers") or "").strip()
                    rewers = (row.get("Rewers") or "").strip()
                    cechy = (row.get("Cechy dodatkowe") or "").strip()
                    numista_id = (row.get("Numista #") or "").strip()

                    is_trial = bool(re.search(r"(?:pr[óo]ba|trial)", nazwa, re.IGNORECASE))

                    stan_lower = stan.lower()
                    is_private = stan_lower == "private"
                    has_coin = stan_lower in ("jest", "private")
                    qty = 0
                    if has_coin:
                        try:
                            qty = int(float(dodatkowe_info.replace(",", ".")))
                        except ValueError:
                            qty = 1

                    # Wartości liczbowe do filtrowania i sortowania
                    waga_num = _parse_float(waga)
                    srednica_num = _parse_float(srednica)
                    value_num = _parse_float(value if not value.startswith("#") else "")
                    estymacja_num = _parse_float(estymacja if not estymacja.startswith("#") else "")

                    raw_db_row = {
                        str(k).strip(): (v if v is not None else "")
                        for k, v in row.items()
                        if k is not None and str(k).strip() != ""
                    }

                    item = {
                        "id": f"coin_{idx}",
                        "row_number": idx,
                        "stan": stan,
                        "is_private": is_private,
                        "ilosc": qty,
                        "posiadana": has_coin,
                        "dodatkowe_info": dodatkowe_info,
                        "typ": typ,
                        "emitent": emitent,
                        "nominal": nominal,
                        "rok": rok,
                        "lp": lp,
                        "nazwa": nazwa,
                        "proba": is_trial,
                        "stop": stop,
                        "waga": waga,
                        "waga_num": waga_num,
                        "ksztalt": ksztalt,
                        "srednica": srednica,
                        "srednica_num": srednica_num,
                        "koszt": koszt,
                        "value": "" if value.startswith("#") else value,
                        "value_num": value_num,
                        "estymacja": "" if estymacja.startswith("#") else estymacja,
                        "estymacja_num": estymacja_num,
                        "zakup": zakup,
                        "platforma": platforma,
                        "identyfikator": identyfikator,
                        "zdjecia": zdjecia_list,
                        "zdjecia_zadeklarowane": zdjecia_list,
                        "czystego_ag": "" if czystego_ag.startswith("#") else czystego_ag,
                        "czystego_au": "" if czystego_au.startswith("#") else czystego_au,
                        "naklad": naklad if naklad != "0,00" else "",
                        "data_emisji": data_emisji,
                        "cena_emisji": cena_emisji,
                        "awers": awers,
                        "rewers": rewers,
                        "cechy_dodatkowe": cechy,
                        "numista_id": numista_id,
                        "raw_db_row": raw_db_row,
                    }
                    items.append(item)

                self._memory_cache = items
                self._memory_cache_mtime = mtime
                self._memory_cache_loaded_iso = read_now_iso
            except Exception as e:
                print(f"[KatalogService] Błąd parsowania pliku CSV: {e}", flush=True)

        sync_info["db_loaded_iso"] = self._memory_cache_loaded_iso or sync_info.get("last_modified_iso") or read_now_iso

        # Sprawdź jakie pliki zdjęć faktycznie istnieją na serwerze w katalog_data/uploads
        uploads_dir = self.paths["uploads_dir"]
        existing_uploads = {}
        if os.path.isdir(uploads_dir):
            try:
                for fname in os.listdir(uploads_dir):
                    fpath = os.path.join(uploads_dir, fname)
                    if os.path.isfile(fpath):
                        existing_uploads[fname.lower()] = fname
            except Exception:
                pass

        def _filter_existing_photo_urls(declared_urls):
            valid_urls = []
            for raw_u in declared_urls or []:
                u = _normalize_photo_url(raw_u)
                if not u:
                    continue
                clean_path = u.split("?")[0].split("#")[0].strip()
                if clean_path.lower().startswith("/katalog/uploads/"):
                    rel_fname = clean_path[len("/katalog/uploads/"):].lstrip("/")
                    actual_fname = existing_uploads.get(rel_fname.lower())
                    if actual_fname:
                        valid_urls.append(f"/katalog/uploads/{actual_fname}")
                else:
                    valid_urls.append(u)
            return valid_urls

        cached_items = self._memory_cache or []
        result_items = []
        for it in cached_items:
            entry = dict(it)
            entry["zdjecia"] = _filter_existing_photo_urls(it.get("zdjecia_zadeklarowane") or it.get("zdjecia"))
            if not is_trusted:
                entry["posiadana"] = False
                entry["ilosc"] = 0
                entry["stan"] = ""
                entry["dodatkowe_info"] = ""
                entry["is_private"] = False
                entry["koszt"] = ""
                entry["zakup"] = ""
                entry["platforma"] = ""
                entry.pop("raw_db_row", None)
                entry.pop("zdjecia_zadeklarowane", None)
            result_items.append(entry)

        return {"items": result_items, "sync": sync_info}

    def save_uploaded_photos(self, file_objs, host_url=""):
        """
        Zapisuje listę przesłanych plików graficznych w katalogu katalog_data/uploads.
        Zwraca listę słowników z metadanymi zapisanych plików.
        """
        uploads_dir = self.paths["uploads_dir"]
        os.makedirs(uploads_dir, exist_ok=True)
        saved = []

        for f in file_objs:
            if not f or not f.filename:
                continue
            orig_name = secure_filename(f.filename) or "zdjecie.jpg"
            _, ext = os.path.splitext(orig_name)
            ext_lower = ext.lower()
            if ext_lower not in ALLOWED_IMAGE_EXTENSIONS:
                ext_lower = ".jpg"
                orig_name = orig_name + ext_lower

            unique_name = f"img_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:6]}_{orig_name}"
            save_path = os.path.join(uploads_dir, unique_name)
            f.save(save_path)

            stat = os.stat(save_path)
            rel_url = f"/katalog/uploads/{unique_name}"
            saved.append({
                "filename": unique_name,
                "relative_url": rel_url,
                "full_url": rel_url,
                "size_bytes": stat.st_size,
                "size_kb": round(stat.st_size / 1024.0, 1),
                "created_at_ts": stat.st_mtime,
                "created_at": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "is_linked": False,
                "linked_items": [],
            })

        return saved

    def list_photos(self, host_url="", force_sync=False):
        """
        Zwraca wszystkie wgrane zdjęcia w katalogu katalog_data/uploads wraz ze statusem,
        czy dane zdjęcie jest już zlinkowane jako '/katalog/uploads/<nazwa>' w bazie wzorcowej CSV.
        """
        uploads_dir = self.paths["uploads_dir"]
        os.makedirs(uploads_dir, exist_ok=True)

        data = self.get_items(is_trusted=True, force_sync=force_sync)
        items = data.get("items", [])
        sync_info = data.get("sync", {})

        # Mapa: ścieżka '/katalog/uploads/<plik>' (lower) -> lista nazw walorów, w których występuje
        linked_map = {}
        for it in items:
            coin_label = f"{it.get('emitent', '')} - {it.get('nazwa', '')} ({it.get('rok', '')})".strip(" -()")
            for raw_url in it.get("zdjecia_zadeklarowane") or it.get("zdjecia") or []:
                clean_u = _normalize_photo_url(raw_url.split("?")[0].split("#")[0].strip().rstrip("/"))
                if not clean_u:
                    continue
                if clean_u.lower().startswith("/katalog/uploads/"):
                    linked_map.setdefault(clean_u.lower(), []).append(coin_label)

        photos = []
        try:
            for fname in os.listdir(uploads_dir):
                fpath = os.path.join(uploads_dir, fname)
                if not os.path.isfile(fpath):
                    continue
                _, ext = os.path.splitext(fname)
                if ext.lower() not in ALLOWED_IMAGE_EXTENSIONS:
                    continue

                stat = os.stat(fpath)
                rel_url = f"/katalog/uploads/{fname}"
                matched_coins = linked_map.get(rel_url.lower(), [])
                is_linked = len(matched_coins) > 0

                photos.append({
                    "filename": fname,
                    "relative_url": rel_url,
                    "full_url": rel_url,
                    "size_bytes": stat.st_size,
                    "size_kb": round(stat.st_size / 1024.0, 1),
                    "created_at_ts": stat.st_mtime,
                    "created_at": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                    "is_linked": is_linked,
                    "linked_items": matched_coins,
                })
        except Exception as e:
            print(f"[KatalogService] Błąd odczytu katalogu uploads: {e}", flush=True)

        photos.sort(key=lambda p: p["created_at_ts"], reverse=True)
        unlinked_count = sum(1 for p in photos if not p["is_linked"])
        linked_count = sum(1 for p in photos if p["is_linked"])

        return {
            "photos": photos,
            "total_count": len(photos),
            "unlinked_count": unlinked_count,
            "linked_count": linked_count,
            "sync": sync_info,
        }

    def delete_photo(self, filename):
        """Usuwa wskazany plik zdjęcia z katalogu katalog_data/uploads."""
        if not filename:
            return False
        safe_name = os.path.basename(filename)
        if safe_name != filename or ".." in filename:
            return False
        target = os.path.join(self.paths["uploads_dir"], safe_name)
        if os.path.isfile(target):
            os.remove(target)
            return True
        return False

    def rename_photo(self, old_filename, new_filename):
        """Zmienia nazwę pliku zdjęcia w katalogu katalog_data/uploads (zachowując rozszerzenie)."""
        if not old_filename or not new_filename:
            raise ValueError("Brak nazwy pliku")
        safe_old = os.path.basename(old_filename)
        if safe_old != old_filename or ".." in old_filename:
            raise ValueError("Nieprawidłowa obecna nazwa pliku")

        old_path = os.path.join(self.paths["uploads_dir"], safe_old)
        if not os.path.isfile(old_path):
            raise ValueError("Plik źródłowy nie istnieje")

        _, old_ext = os.path.splitext(safe_old)
        clean_new = secure_filename(new_filename)
        if not clean_new:
            raise ValueError("Nowa nazwa pliku jest nieprawidłowa")

        new_root, new_ext = os.path.splitext(clean_new)
        if not new_ext or new_ext.lower() not in ALLOWED_IMAGE_EXTENSIONS:
            final_new_name = f"{clean_new}{old_ext.lower()}"
        else:
            final_new_name = f"{new_root}{new_ext.lower()}"

        new_path = os.path.join(self.paths["uploads_dir"], final_new_name)
        if os.path.exists(new_path) and os.path.abspath(old_path) != os.path.abspath(new_path):
            raise ValueError("Plik o takiej nazwie już istnieje")

        os.rename(old_path, new_path)
        return final_new_name
