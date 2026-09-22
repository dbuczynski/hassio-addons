import os
import json
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename

def get_wyprzedaz_paths(data_dir_base):
    data_dir = os.path.join(data_dir_base, "wyprzedaz_data")
    uploads_dir = os.path.join(data_dir, "uploads")
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(uploads_dir, exist_ok=True)
    return {
        "data_dir": data_dir,
        "uploads_dir": uploads_dir,
        "products_file": os.path.join(data_dir, "products.json"),
        "categories_file": os.path.join(data_dir, "categories.json")
    }

class WyprzedazService:
    def __init__(self, data_dir_base):
        self.paths = get_wyprzedaz_paths(data_dir_base)
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

    def add_product(self, nazwa, cena, opis, kategoria_id=None, zdjecia=None, waga_jednostkowa="", ilosc=1, widocznosc=True):
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
            "ilosc": ilosc_val,
            "widocznosc": bool(widocznosc),
            "zdjecia": zdjecia or [],
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        prods.insert(0, new_prod)
        self.save_products(prods)
        return new_prod

    def update_product(self, prod_id, nazwa, cena, opis, kategoria_id=None, zdjecia=None, waga_jednostkowa=None, ilosc=None, widocznosc=None):
        prods = self.load_products()
        updated = None
        for p in prods:
            if p["id"] == prod_id:
                p["nazwa"] = nazwa.strip()
                p["cena"] = str(cena).strip()
                p["opis"] = opis.strip()
                p["kategoria_id"] = kategoria_id if kategoria_id and str(kategoria_id).strip() else None
                
                if waga_jednostkowa is not None:
                    p["waga_jednostkowa"] = str(waga_jednostkowa).strip()
                if ilosc is not None:
                    try:
                        p["ilosc"] = int(ilosc)
                    except (ValueError, TypeError):
                        pass
                if widocznosc is not None:
                    p["widocznosc"] = bool(widocznosc)
                if zdjecia is not None:
                    p["zdjecia"] = zdjecia
                    
                p["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                updated = p
                break
        if updated:
            self.save_products(prods)
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
            # Usuń pliki zdjęć powiązane z tym produktem
            for img_path in to_delete.get("zdjecia", []):
                filename = os.path.basename(img_path)
                full_path = os.path.join(self.paths["uploads_dir"], filename)
                if os.path.exists(full_path):
                    try:
                        os.remove(full_path)
                    except Exception as e:
                        print(f"Błąd usuwania pliku zdjęcia {filename}: {e}", flush=True)
            return True
        return False

    def save_uploaded_file(self, file_obj):
        if not file_obj or not file_obj.filename:
            return None
        orig_filename = secure_filename(file_obj.filename) or "image.jpg"
        unique_name = f"img_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:6]}_{orig_filename}"
        save_path = os.path.join(self.paths["uploads_dir"], unique_name)
        file_obj.save(save_path)
        return f"/wyprzedaz/uploads/{unique_name}"
