import os
import io
import json
import uuid
import shutil
import zipfile
from datetime import datetime
from werkzeug.utils import secure_filename

def get_wyprzedaz_paths(data_dir_base, data_subdir="wyprzedaz_data"):
    data_dir = os.path.join(data_dir_base, data_subdir)
    uploads_dir = os.path.join(data_dir, "uploads")
    archive_dir = os.path.join(uploads_dir, "images-archive")
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(uploads_dir, exist_ok=True)
    os.makedirs(archive_dir, exist_ok=True)
    return {
        "data_dir": data_dir,
        "uploads_dir": uploads_dir,
        "archive_dir": archive_dir,
        "products_file": os.path.join(data_dir, "products.json"),
        "categories_file": os.path.join(data_dir, "categories.json")
    }

class WyprzedazService:
    def __init__(self, data_dir_base, data_subdir="wyprzedaz_data", url_prefix="/wyprzedaz"):
        self.url_prefix = url_prefix.rstrip("/")
        self.paths = get_wyprzedaz_paths(data_dir_base, data_subdir=data_subdir)
        self._ensure_defaults()

    def _ensure_defaults(self):
        if not os.path.exists(self.paths["categories_file"]):
            default_categories = [
                {"id": "cat_elektronika", "name": "Elektronika", "parent_id": None, "description": "Komputery, telefony, RTV"},
                {"id": "cat_agd", "name": "AGD", "parent_id": None, "description": "Sprzęt gospodarstwa domowego"},
                {"id": "cat_narzedzia", "name": "Narzędzia & Warsztat", "parent_id": None, "description": "Elektronarzędzia, meble warsztatowe"},
                {"id": "cat_audio", "name": "Audio i Hi-Fi", "parent_id": "cat_elektronika", "description": "Głośniki, wzmacniacze, słuchawki"},
                {"id": "cat_inne", "name": "Inne", "parent_id": None, "description": "Różności i akcesoria"}
            ]
            self.save_categories(default_categories)

        if not os.path.exists(self.paths["products_file"]):
            self.save_products([])

    def _archive_image_if_unused(self, img_path, remaining_products):
        """
        Przenosi plik zdjęcia do podfolderu 'images-archive', jeśli żadna inna pozycja w bazie już z niego nie korzysta.
        """
        if not img_path:
            return
        filename = os.path.basename(img_path)
        if not filename:
            return

        # Sprawdź czy jakikolwiek inny produkt nadal odwołuje się do tego pliku zdjęcia
        for p in remaining_products:
            for z in p.get("zdjecia", []):
                if os.path.basename(z) == filename:
                    return

        src_path = os.path.join(self.paths["uploads_dir"], filename)
        if os.path.exists(src_path) and os.path.isfile(src_path):
            archive_dir = self.paths["archive_dir"]
            os.makedirs(archive_dir, exist_ok=True)
            dst_path = os.path.join(archive_dir, filename)
            if os.path.exists(dst_path):
                dst_path = os.path.join(archive_dir, f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}")
            try:
                shutil.move(src_path, dst_path)
            except Exception as e:
                print(f"Błąd przenoszenia zdjęcia {filename} do images-archive: {e}", flush=True)

    # --- KATEGORIE ---
    def load_categories(self):
        try:
            if os.path.exists(self.paths["categories_file"]):
                with open(self.paths["categories_file"], "r", encoding="utf-8") as f:
                    cats = json.load(f)
                    if isinstance(cats, list):
                        return cats
        except Exception as e:
            print(f"Błąd odczytu kategorii: {e}", flush=True)
        return []

    def save_categories(self, categories):
        with open(self.paths["categories_file"], "w", encoding="utf-8") as f:
            json.dump(categories, f, ensure_ascii=False, indent=2)

    def get_category_depth(self, cat_id, cats=None):
        """Oblicza głębokość kategorii (1 dla głównej, 2 dla podkategorii 1. stopnia, itd.)."""
        if not cat_id:
            return 0
        if cats is None:
            cats = self.load_categories()
        cat_map = {c["id"]: c for c in cats}
        
        depth = 0
        visited = set()
        curr_id = cat_id
        while curr_id and curr_id in cat_map:
            if curr_id in visited:
                break
            visited.add(curr_id)
            depth += 1
            curr_id = cat_map[curr_id].get("parent_id")
        return depth

    def get_subtree_height(self, cat_id, cats=None):
        """Oblicza wysokość poddrzewa zakorzenionego w cat_id (1 dla pojedynczego węzła bez dzieci)."""
        if cats is None:
            cats = self.load_categories()
        
        children_map = {}
        for c in cats:
            pid = c.get("parent_id")
            if pid not in children_map:
                children_map[pid] = []
            children_map[pid].append(c["id"])

        def calc_h(cid, visited):
            if cid in visited:
                return 0
            visited.add(cid)
            kids = children_map.get(cid, [])
            if not kids:
                return 1
            return 1 + max(calc_h(k, visited.copy()) for k in kids)

        return calc_h(cat_id, set())

    def get_category_tree(self):
        cats = self.load_categories()
        cat_dict = {c["id"]: dict(c, children=[]) for c in cats}
        tree = []

        # Oblicz głębokość dla każdego węzła
        for c_id, c_data in cat_dict.items():
            c_data["depth"] = self.get_category_depth(c_id, cats)

        for c_id, c_data in cat_dict.items():
            parent_id = c_data.get("parent_id")
            if parent_id and parent_id in cat_dict:
                cat_dict[parent_id]["children"].append(c_data)
            else:
                tree.append(c_data)

        # Sortuj alfabetycznie na każdym poziomie
        def sort_tree_recursive(nodes):
            nodes.sort(key=lambda c: (c.get("name") or "").lower())
            for node in nodes:
                if node.get("children"):
                    sort_tree_recursive(node["children"])
            return nodes

        return sort_tree_recursive(tree)

    def add_category(self, name, parent_id=None, description=""):
        cats = self.load_categories()
        parent_id_clean = parent_id if parent_id and parent_id.strip() else None

        if parent_id_clean:
            parent_depth = self.get_category_depth(parent_id_clean, cats)
            if parent_depth >= 4:
                raise ValueError("Maksymalny poziom zagłębienia drzewa kategorii wynosi 4 poziomy.")

        new_id = f"cat_{str(uuid.uuid4())[:8]}"
        new_cat = {
            "id": new_id,
            "name": name.strip(),
            "parent_id": parent_id_clean,
            "description": description.strip()
        }
        cats.append(new_cat)
        self.save_categories(cats)
        return new_cat

    def update_category(self, cat_id, name, parent_id=None, description=""):
        cats = self.load_categories()
        parent_id_clean = parent_id if parent_id and parent_id.strip() else None

        if parent_id_clean == cat_id:
            raise ValueError("Kategoria nie może być swoją własną kategorią nadrzędną.")

        if parent_id_clean:
            curr = parent_id_clean
            cat_map = {c["id"]: c for c in cats}
            visited = set()
            while curr and curr in cat_map:
                if curr == cat_id:
                    raise ValueError("Kategoria nadrzędna nie może być podkategorią edytowanej kategorii.")
                if curr in visited:
                    break
                visited.add(curr)
                curr = cat_map[curr].get("parent_id")

            parent_depth = self.get_category_depth(parent_id_clean, cats)
            subtree_height = self.get_subtree_height(cat_id, cats)
            if parent_depth + subtree_height > 4:
                raise ValueError("Maksymalny poziom zagłębienia drzewa kategorii wynosi 4 poziomy.")

        updated = None
        for c in cats:
            if c["id"] == cat_id:
                c["name"] = name.strip()
                c["parent_id"] = parent_id_clean
                c["description"] = description.strip()
                updated = c
                break
        if updated:
            self.save_categories(cats)
        return updated

    def delete_category(self, cat_id):
        cats = self.load_categories()
        # Zmień podkategorie tak, aby ich parent_id wynosło None lub id nadrzędnej
        parent_map = {c["id"]: c.get("parent_id") for c in cats}
        new_cats = []
        for c in cats:
            if c["id"] == cat_id:
                continue
            if c.get("parent_id") == cat_id:
                c["parent_id"] = parent_map.get(cat_id)
            new_cats.append(c)
        self.save_categories(new_cats)

        # W produktach wyczyść przypisanie usuniętej kategorii
        prods = self.load_products()
        changed = False
        for p in prods:
            if p.get("kategoria_id") == cat_id:
                p["kategoria_id"] = None
                changed = True
        if changed:
            self.save_products(prods)
        return True

    # --- PRODUKTY ---
    def load_products(self):
        try:
            if os.path.exists(self.paths["products_file"]):
                with open(self.paths["products_file"], "r", encoding="utf-8") as f:
                    prods = json.load(f)
                    if isinstance(prods, list):
                        return prods
        except Exception as e:
            print(f"Błąd odczytu produktów: {e}", flush=True)
        return []

    def save_products(self, products):
        with open(self.paths["products_file"], "w", encoding="utf-8") as f:
            json.dump(products, f, ensure_ascii=False, indent=2)

    def add_product(self, nazwa, cena, opis, kategoria_id=None, zdjecia=None, waga_jednostkowa="", ilosc=1, widocznosc=True, lokalizacja=""):
        prods = self.load_products()
        prod_id = f"prod_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:6]}"
        
        try:
            ilosc_val = int(ilosc)
        except (ValueError, TypeError):
            ilosc_val = 1

        new_prod = {
            "id": prod_id,
            "nazwa": nazwa.strip(),
            "cena": str(cena).strip(),
            "opis": opis.strip(),
            "kategoria_id": kategoria_id if kategoria_id and str(kategoria_id).strip() else None,
            "waga_jednostkowa": str(waga_jednostkowa or "").strip(),
            "lokalizacja": str(lokalizacja or "").strip(),
            "ilosc": ilosc_val,
            "widocznosc": bool(widocznosc),
            "zdjecia": zdjecia or [],
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        prods.insert(0, new_prod)
        self.save_products(prods)
        return new_prod

    def update_product(self, prod_id, nazwa, cena, opis, kategoria_id=None, zdjecia=None, waga_jednostkowa=None, ilosc=None, widocznosc=None, lokalizacja=None):
        prods = self.load_products()
        updated = None
        removed_images = []
        for p in prods:
            if p["id"] == prod_id:
                p["nazwa"] = nazwa.strip()
                p["cena"] = str(cena).strip()
                p["opis"] = opis.strip()
                p["kategoria_id"] = kategoria_id if kategoria_id and str(kategoria_id).strip() else None
                
                if waga_jednostkowa is not None:
                    p["waga_jednostkowa"] = str(waga_jednostkowa).strip()
                if lokalizacja is not None:
                    p["lokalizacja"] = str(lokalizacja).strip()
                if ilosc is not None:
                    try:
                        p["ilosc"] = int(ilosc)
                    except (ValueError, TypeError):
                        pass
                if widocznosc is not None:
                    p["widocznosc"] = bool(widocznosc)
                if zdjecia is not None:
                    old_photos = p.get("zdjecia", []) or []
                    new_basenames = {os.path.basename(z) for z in zdjecia if z}
                    removed_images = [old_z for old_z in old_photos if os.path.basename(old_z) not in new_basenames]
                    p["zdjecia"] = zdjecia
                    
                p["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                updated = p
                break
        if updated:
            self.save_products(prods)
            for img_path in removed_images:
                self._archive_image_if_unused(img_path, prods)
        return updated

    def delete_product(self, prod_id):
        prods = self.load_products()
        to_delete = None
        new_prods = []
        for p in prods:
            if p["id"] == prod_id:
                to_delete = p
            else:
                new_prods.append(p)

        if to_delete:
            self.save_products(new_prods)
            # Przenieś pliki zdjęć powiązane z tym produktem do podfolderu 'images-archive'
            for img_path in to_delete.get("zdjecia", []):
                self._archive_image_if_unused(img_path, new_prods)
            return True
        return False

    def save_uploaded_file(self, file_obj):
        if not file_obj or not file_obj.filename:
            return None
        orig_filename = secure_filename(file_obj.filename) or "image.jpg"
        unique_name = f"img_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:6]}_{orig_filename}"
        save_path = os.path.join(self.paths["uploads_dir"], unique_name)
        file_obj.save(save_path)
        return f"{self.url_prefix}/uploads/{unique_name}"

    def _normalize_imported_image_urls(self, prods):
        """Przekształca ścieżki zdjęć przy imporcie tak, aby pasowały do bieżącego url_prefix (np. /zbior/uploads/...)."""
        for p in prods:
            if "zdjecia" in p and isinstance(p["zdjecia"], list):
                normalized = []
                for z in p["zdjecia"]:
                    fname = os.path.basename(z)
                    if fname:
                        normalized.append(f"{self.url_prefix}/uploads/{fname}")
                p["zdjecia"] = normalized

    def export_zip_bytes(self):
        """Tworzy w pamięci archiwum ZIP z plikami categories.json, products.json oraz katalogiem uploads/."""
        mem_zip = io.BytesIO()
        with zipfile.ZipFile(mem_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            cats = self.load_categories()
            prods = self.load_products()
            zf.writestr("categories.json", json.dumps(cats, ensure_ascii=False, indent=2))
            zf.writestr("products.json", json.dumps(prods, ensure_ascii=False, indent=2))

            uploads_dir = self.paths["uploads_dir"]
            if os.path.exists(uploads_dir):
                for fname in os.listdir(uploads_dir):
                    fpath = os.path.join(uploads_dir, fname)
                    if os.path.isfile(fpath):
                        zf.write(fpath, arcname=f"uploads/{fname}")
        mem_zip.seek(0)
        return mem_zip

    def import_zip(self, zip_stream, mode="add"):
        """
        Importuje bazę danych i obrazki z pliku ZIP.
        mode:
          - 'overwrite': całkowicie czyści lokalną bazę kategorii, produktów oraz zdjęć przed wgraniem.
          - 'add': dodaje nowe kategorie i produkty (bez tworzenia duplikatów po id lub nazwie).
        """
        with zipfile.ZipFile(zip_stream, mode="r") as zf:
            names = zf.namelist()
            imported_cats = []
            imported_prods = []

            if "categories.json" in names:
                raw_cats = json.loads(zf.read("categories.json").decode("utf-8"))
                if isinstance(raw_cats, list):
                    imported_cats = raw_cats

            if "products.json" in names:
                raw_prods = json.loads(zf.read("products.json").decode("utf-8"))
                if isinstance(raw_prods, list):
                    imported_prods = raw_prods
                    self._normalize_imported_image_urls(imported_prods)

            uploads_dir = self.paths["uploads_dir"]
            os.makedirs(uploads_dir, exist_ok=True)
            os.makedirs(self.paths["archive_dir"], exist_ok=True)

            if mode == "overwrite":
                # Usuń wszystkie dotychczasowe pliki zdjęć z uploads_dir
                for fname in os.listdir(uploads_dir):
                    fpath = os.path.join(uploads_dir, fname)
                    if os.path.isfile(fpath):
                        try:
                            os.remove(fpath)
                        except Exception:
                            pass

                # Wypakuj wszystkie zdjęcia z archiwum
                img_count = 0
                for member in names:
                    if member.startswith("uploads/") and not member.endswith("/"):
                        fname = os.path.basename(member)
                        if fname:
                            target_path = os.path.join(uploads_dir, secure_filename(fname) or fname)
                            with zf.open(member) as src, open(target_path, "wb") as dst:
                                shutil.copyfileobj(src, dst)
                            img_count += 1

                self.save_categories(imported_cats)
                self.save_products(imported_prods)
                return {
                    "mode": "overwrite",
                    "categories_added": len(imported_cats),
                    "products_added": len(imported_prods),
                    "products_skipped": 0,
                    "images_imported": img_count
                }
            else:
                # Tryb 'add' - dodaj bez duplikatów
                existing_cats = self.load_categories()
                existing_prods = self.load_products()

                cat_id_map = {}  # mapowanie starego ID kategorii z importu na istniejące ID (jeśli dopasowano po nazwie i rodzicu)
                existing_cat_ids = {c["id"] for c in existing_cats}

                cats_added = 0
                for ic in imported_cats:
                    ic_id = ic.get("id")
                    ic_name = (ic.get("name") or "").strip().lower()
                    ic_parent = ic.get("parent_id")
                    mapped_parent = cat_id_map.get(ic_parent, ic_parent)

                    if ic_id in existing_cat_ids:
                        cat_id_map[ic_id] = ic_id
                        continue

                    # Sprawdź czy kategoria o tej samej nazwie i rodzicu już istnieje
                    match = next(
                        (c for c in existing_cats if (c.get("name") or "").strip().lower() == ic_name and c.get("parent_id") == mapped_parent),
                        None
                    )
                    if match:
                        cat_id_map[ic_id] = match["id"]
                    else:
                        new_cat = dict(ic)
                        new_cat["parent_id"] = mapped_parent
                        existing_cats.append(new_cat)
                        existing_cat_ids.add(ic_id)
                        cat_id_map[ic_id] = ic_id
                        cats_added += 1

                existing_prod_ids = {p.get("id") for p in existing_prods}
                existing_prod_names = {(p.get("nazwa") or "").strip().lower() for p in existing_prods if p.get("nazwa")}

                prods_added = 0
                prods_skipped = 0
                needed_images = set()

                for ip in imported_prods:
                    ip_id = ip.get("id")
                    ip_name = (ip.get("nazwa") or "").strip().lower()

                    if (ip_id and ip_id in existing_prod_ids) or (ip_name and ip_name in existing_prod_names):
                        prods_skipped += 1
                        continue

                    new_prod = dict(ip)
                    orig_cat = new_prod.get("kategoria_id")
                    if orig_cat in cat_id_map:
                        new_prod["kategoria_id"] = cat_id_map[orig_cat]

                    existing_prods.append(new_prod)
                    if ip_id:
                        existing_prod_ids.add(ip_id)
                    if ip_name:
                        existing_prod_names.add(ip_name)
                    prods_added += 1

                    for img_url in new_prod.get("zdjecia", []):
                        needed_images.add(os.path.basename(img_url))

                img_count = 0
                for member in names:
                    if member.startswith("uploads/") and not member.endswith("/"):
                        fname = os.path.basename(member)
                        if fname and (fname in needed_images or not os.path.exists(os.path.join(uploads_dir, fname))):
                            target_path = os.path.join(uploads_dir, fname)
                            if not os.path.exists(target_path):
                                with zf.open(member) as src, open(target_path, "wb") as dst:
                                    shutil.copyfileobj(src, dst)
                                img_count += 1

                self.save_categories(existing_cats)
                self.save_products(existing_prods)
                return {
                    "mode": "add",
                    "categories_added": cats_added,
                    "products_added": prods_added,
                    "products_skipped": prods_skipped,
                    "images_imported": img_count
                }

