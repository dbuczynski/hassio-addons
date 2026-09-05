import csv
from datetime import datetime
import hashlib
import io
import json
import os
import re
import requests
import time
import uuid
from flask import Flask, jsonify, render_template, request, Response, redirect, session, send_from_directory
import youtube_service

app = Flask(__name__)
app.secret_key = "andrzejow_net_secret_key_metale_szlachetne"

APP_VERSION = "1.11.1"

DEFAULT_ALLOWED_CHANNELS = [
    {"handle": "@UncjuszPatyniusz", "title": "Uncjusz Patyniusz"},
    {"handle": "@ZlotyBazyliszek", "title": "Złoty Bazyliszek"},
    {"handle": "@ArturK92", "title": "ArturK92"}
]

DATA_DIR = "/data" if os.path.exists("/data") else os.path.dirname(os.path.abspath(__file__))
OPTIONS_PATH = "/data/options.json" if os.path.exists("/data/options.json") else os.path.join(DATA_DIR, "options.json")
GLOBAL_CONFIG_PATH = os.path.join(DATA_DIR, "global_config.json")
LABELS_DB_PATH = os.path.join(DATA_DIR, "labels_db.json")
DEFAULT_LABELS_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "labels_db.json")
LABELS_USERS_PATH = os.path.join(DATA_DIR, "labels_users.json")
ACTIVITY_LOGS_PATH = os.path.join(DATA_DIR, "activity_logs.json")

def log_activity_entry(entry_type, details=None, req=None):
    """
    Trwale zapisuje zdarzenie do pliku activity_logs.json w pamięci trwałej (DATA_DIR).
    entry_type: 'page_view', 'label_print', 'wheel_draw'
    """
    try:
        ip = get_client_ip() if req else "127.0.0.1"
        url_path = req.full_path if req else ""
        if url_path.endswith('?'):
            url_path = url_path[:-1]

        entry = {
            "id": str(uuid.uuid4())[:8],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": entry_type,
            "ip": ip,
            "url": url_path,
            "user_agent": req.headers.get("User-Agent", "") if req else "",
            "details": details or {}
        }

        logs = []
        if os.path.exists(ACTIVITY_LOGS_PATH):
            try:
                with open(ACTIVITY_LOGS_PATH, "r", encoding="utf-8") as f:
                    logs = json.load(f)
                    if not isinstance(logs, list):
                        logs = []
            except Exception:
                logs = []

        logs.insert(0, entry)
        if len(logs) > 5000:
            logs = logs[:5000]

        with open(ACTIVITY_LOGS_PATH, "w", encoding="utf-8") as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Błąd zapisu pliku activity_logs.json: {e}", flush=True)

def send_telegram_ha_notification(title, message, return_details=False):
    """
    Wysyła notyfikację Telegram przez Supervisor API Home Assistanta (telegram_bot.send_message).
    Wymaga zdefiniowania parametrów 'telegram_chat_id' (XXX) oraz 'telegram_config_entry_id' (YYY).
    """
    try:
        cfg = load_all_config_data()
        chat_id_val = cfg.get("telegram_chat_id")
        config_entry_id_val = cfg.get("telegram_config_entry_id")

        if not chat_id_val or not config_entry_id_val:
            msg = "[Telegram HA] Pominięto wysyłkę: brak zdefiniowanego 'telegram_chat_id' lub 'telegram_config_entry_id' w konfiguracji dodatku."
            print(msg, flush=True)
            return (False, msg) if return_details else False

        chat_ids = []
        if isinstance(chat_id_val, list):
            chat_ids = [str(x).strip() for x in chat_id_val if str(x).strip()]
        elif isinstance(chat_id_val, (str, int)) and str(chat_id_val).strip():
            chat_ids = [str(chat_id_val).strip()]

        entry_id = str(config_entry_id_val).strip()

        if not chat_ids or not entry_id:
            msg = "[Telegram HA] Pominięto wysyłkę: puste wartości 'telegram_chat_id' lub 'telegram_config_entry_id'."
            print(msg, flush=True)
            return (False, msg) if return_details else False

        token = os.environ.get("SUPERVISOR_TOKEN")
        if not token:
            msg = "[Telegram HA] BŁĄD: Brak zmiennej środowiskowej SUPERVISOR_TOKEN w kontenerze. W pliku config.yaml dodano 'homeassistant_api: true' - zaktualizuj dodatek w Home Assistant."
            print(msg, flush=True)
            return (False, msg) if return_details else False

        url = "http://supervisor/core/api/services/telegram_bot/send_message"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        payload = {
            "chat_id": chat_ids,
            "config_entry_id": entry_id,
            "message": message,
            "title": title or "Metale Szlachetne Polska"
        }

        resp = requests.post(url, headers=headers, json=payload, timeout=6)
        log_msg = f"[Telegram HA] Wywołano akcję telegram_bot.send_message (chat_ids={chat_ids}, entry_id={entry_id}). Kod odpowiedzi HA: {resp.status_code}, Treść: {resp.text}"
        print(log_msg, flush=True)

        is_ok = (resp.status_code in [200, 201])
        return (is_ok, log_msg) if return_details else is_ok
    except Exception as e:
        err_msg = f"[Telegram HA] Wyjątek podczas wysyłania notyfikacji Telegram w HA: {e}"
        print(err_msg, flush=True)
        return (False, err_msg) if return_details else False

def format_label_params_summary(item):
    """Formatuje czytelny podgląd parametrów monety do notyfikacji."""
    c = clean_label_item(item)
    parts = []
    if c[0]: parts.append(f"Rok: {c[0]}")
    if c[4]:
        denom = f"{c[7]}{c[4]} {c[5]}".strip()
        parts.append(f"Nominał: {denom}")
    if c[1]: parts.append(f"Seria: {c[1]}")
    if c[2]: parts.append(f"Nazwa: {c[2]}")
    if c[6]: parts.append(f"Stop: {c[6]}")
    if c[3]: parts.append(f"Nakład: {c[3]}")
    if c[8]: parts.append(f"Rant: {c[8]}")
    if c[9]: parts.append(f"Typ: {c[9]}")
    if c[10]: parts.append(f"Waga: {c[10]}g")
    if c[11]: parts.append(f"Średnica: {c[11]}mm")
    if c[12]: parts.append("Trial: TAK")
    if c[13]: parts.append(f"Kraj: {c[13].upper()}")
    return ", ".join(parts) if parts else "brak szczegółów"

def load_all_config_data():
    """Ładuje i łączy konfigurację z /data/options.json (zapisywanego przez Home Assistant) oraz global_config.json."""
    data = {}
    if os.path.exists(GLOBAL_CONFIG_PATH):
        try:
            with open(GLOBAL_CONFIG_PATH, "r", encoding="utf-8") as f:
                d = json.load(f)
                if isinstance(d, dict):
                    data.update(d)
        except Exception:
            pass

    for p in [OPTIONS_PATH, "/data/options.json"]:
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    d = json.load(f)
                    if isinstance(d, dict):
                        data.update(d)
            except Exception:
                pass
    return data

def load_labels_users():
    if os.path.exists(LABELS_USERS_PATH):
        try:
            with open(LABELS_USERS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def save_labels_users(users):
    with open(LABELS_USERS_PATH, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def hash_password(pwd):
    return hashlib.sha256(pwd.encode('utf-8')).hexdigest()

def get_admin_password():
    cfg = load_all_config_data()
    pwd = cfg.get("admin_password")
    if pwd and str(pwd).strip():
        return str(pwd).strip()
    return "admin"

def get_trusted_ips():
    cfg = load_all_config_data()
    ips = cfg.get("admin_trusted_ips")
    if ips and isinstance(ips, list) and len(ips) > 0:
        return [str(ip).strip() for ip in ips if str(ip).strip()]
    return ["127.0.0.1"]

def get_client_ip():
    if request.headers.get("X-Forwarded-For"):
        return request.headers.get("X-Forwarded-For").split(",")[0].strip()
    return request.remote_addr or "127.0.0.1"

def is_client_ip_trusted():
    ip = get_client_ip()
    trusted = get_trusted_ips()
    return (ip in trusted) or ("127.0.0.1" in trusted and ip == "127.0.0.1")

def refresh_labels_session_activity():
    if session.get('labels_scope') == "MetaleSzlachetnePolska/etykiety" and session.get('labels_user'):
        last_act = session.get('labels_last_activity', 0)
        now = time.time()
        # 10 minut bezczynności (600 s)
        if now - last_act > 600:
            session.pop('labels_user', None)
            session.pop('labels_role', None)
            session.pop('labels_scope', None)
            session.pop('labels_last_activity', None)
            return False
        session['labels_last_activity'] = now
        return True
    return False

def is_labels_authenticated(role_required=None):
    if not refresh_labels_session_activity():
        return False
    if session.get('labels_scope') != "MetaleSzlachetnePolska/etykiety":
        return False
    if role_required == 'admin' and session.get('labels_role') != 'admin':
        return False
    return True

@app.before_request
def check_session_inactivity():
    path = request.path
    if path.startswith('/MetaleSzlachetnePolska/etykiety'):
        refresh_labels_session_activity()

    # Automatyczne logowanie wejść na strony
    if not path.endswith(('.css', '.js', '.png', '.jpg', '.jpeg', '.webp', '.ico', '.svg', '.woff', '.woff2', '.ttf')):
        if path not in ['/api/info', '/MetaleSzlachetnePolska/youtube/api/info', '/MetaleSzlachetnePolska/youtube/api/channel-profile', '/api/logs/data']:
            log_activity_entry('page_view', details={"method": request.method}, req=request)

def load_labels_db():
    target_path = LABELS_DB_PATH
    labels = []
    
    if os.path.exists(target_path):
        try:
            with open(target_path, "r", encoding="utf-8") as f:
                labels = json.load(f)
        except Exception:
            labels = []

    # Jeśli baza w /data jest pusta lub nie istnieje, załaduj bazy domyślną z obrazu dodatku
    if (not labels or not isinstance(labels, list) or len(labels) == 0) and os.path.exists(DEFAULT_LABELS_DB_PATH):
        try:
            with open(DEFAULT_LABELS_DB_PATH, "r", encoding="utf-8") as f:
                default_labels = json.load(f)
                if default_labels and isinstance(default_labels, list) and len(default_labels) > 0:
                    labels = default_labels
                    save_labels_db(labels)
        except Exception:
            pass

    return labels if isinstance(labels, list) else []

def save_labels_db(labels):
    target_path = LABELS_DB_PATH
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(labels, f, ensure_ascii=False, indent=2)
    if os.path.exists(DEFAULT_LABELS_DB_PATH) and DEFAULT_LABELS_DB_PATH != target_path:
        try:
            with open(DEFAULT_LABELS_DB_PATH, "w", encoding="utf-8") as f:
                json.dump(labels, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

def get_global_api_key():
    """Pobiera globalny klucz API z pliku options.json (HA) lub global_config.json."""
    cfg = load_all_config_data()
    key = cfg.get("api_key") or cfg.get("global_api_key")
    if key:
        return str(key).strip()
    return ""

def save_global_api_key(key):
    """Zapisuje globalny klucz API do pliku global_config.json."""
    data = {}
    if os.path.exists(GLOBAL_CONFIG_PATH):
        try:
            with open(GLOBAL_CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
    data["global_api_key"] = key.strip()
    with open(GLOBAL_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_allowed_channels():
    """Pobiera listę dozwolonych kanałów z pliku konfiguracji lub domyślną."""
    cfg = load_all_config_data()
    if "allowed_channels" in cfg and isinstance(cfg["allowed_channels"], list) and len(cfg["allowed_channels"]) > 0:
        return cfg["allowed_channels"]
    return list(DEFAULT_ALLOWED_CHANNELS)

def save_allowed_channels(channels):
    """Zapisuje listę dozwolonych kanałów do pliku konfiguracji."""
    data = {}
    if os.path.exists(GLOBAL_CONFIG_PATH):
        try:
            with open(GLOBAL_CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
    data["allowed_channels"] = channels
    with open(GLOBAL_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_discord_bot_token():
    """Pobiera token bota Discord z pliku global_config.json jeśli istnieje."""
    if os.path.exists(GLOBAL_CONFIG_PATH):
        try:
            with open(GLOBAL_CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("discord_bot_token", "").strip()
        except Exception:
            pass
    return ""

def save_discord_bot_token(token):
    """Zapisuje token bota Discord do pliku global_config.json."""
    data = {}
    if os.path.exists(GLOBAL_CONFIG_PATH):
        try:
            with open(GLOBAL_CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
    data["discord_bot_token"] = token.strip()
    with open(GLOBAL_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

DRAW_HISTORY_PATH = os.path.join(DATA_DIR, "draw_history.json")

def load_draw_history():
    """Pobiera historię wygranych losowań z pliku JSON."""
    if os.path.exists(DRAW_HISTORY_PATH):
        try:
            with open(DRAW_HISTORY_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def save_draw_result_entry(entry):
    """Zapisuje wynik losowania do historii archiwalnej (max 500 wpisów)."""
    history = load_draw_history()
    history.insert(0, entry)
    history = history[:500]
    try:
        with open(DRAW_HISTORY_PATH, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Błąd zapisu historii losowań: {e}", flush=True)

def resolve_api_key():
    """Ustala klucz API z nagłówka żądania klienta X-Api-Key lub z pliku globalnego."""
    custom_key = request.headers.get("X-Api-Key", "").strip()
    if custom_key:
        return custom_key
    
    query_key = request.args.get("api_key", "").strip()
    if query_key:
        return query_key

    global_key = get_global_api_key()
    if global_key:
        return global_key

    return None

def resolve_channel_handle():
    """Pobiera preferowaną nazwę kanału z nagłówka klienta X-Channel-Handle."""
    header_handle = request.headers.get("X-Channel-Handle", "").strip()
    if header_handle:
        return header_handle
    query_handle = request.args.get("channel_handle", "").strip()
    if query_handle:
        return query_handle
    channels = load_allowed_channels()
    if channels:
        return channels[0]["handle"]
    return "@UncjuszPatyniusz"

@app.route('/')
def home():
    return render_template('default.html')

@app.route('/MSP')
@app.route('/MSP/')
@app.route('/msp')
@app.route('/msp/')
@app.route('/metaleszlachetnePolska')
@app.route('/metaleszlachetnePolska/')
@app.route('/METALESZLACHETNEPOLSKA')
@app.route('/METALESZLACHETNEPOLSKA/')
def redirect_msp():
    return redirect('/MetaleSzlachetnePolska')

@app.route('/MetaleSzlachetnePolska')
@app.route('/MetaleSzlachetnePolska/')
def portal_metale_szlachetne():
    return render_template('MetaleSzlachetnePolska/index.html')

@app.route('/MetaleSzlachetnePolska/etykiety')
@app.route('/MetaleSzlachetnePolska/etykiety/')
def etykiety():
    return render_template('MetaleSzlachetnePolska/etykiety/index.html')

@app.route('/MetaleSzlachetnePolska/etykiety/print')
@app.route('/MetaleSzlachetnePolska/etykiety/print/')
def etykiety_print():
    return render_template('MetaleSzlachetnePolska/etykiety/print.html')

@app.route('/MetaleSzlachetnePolska/etykiety/admin/login', methods=['GET', 'POST'])
def admin_labels_login():
    client_ip = get_client_ip()
    trusted = is_client_ip_trusted()
    next_url = request.args.get('next') or request.form.get('next') or '/MetaleSzlachetnePolska/etykiety/admin/edit'

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username:
            return render_template('MetaleSzlachetnePolska/etykiety/admin_login.html', is_trusted_ip=trusted, client_ip=client_ip, error="Podaj nazwę użytkownika.", next_url=next_url)

        role = 'user'
        authenticated = False

        if trusted:
            authenticated = True
            if username == 'admin':
                role = 'admin'
            else:
                users = load_labels_users()
                user_match = next((u for u in users if u.get('username') == username), None)
                if user_match:
                    role = user_match.get('role', 'user')
        else:
            admin_pwd = get_admin_password()
            if admin_pwd == 'admin' or password == 'admin':
                return render_template('MetaleSzlachetnePolska/etykiety/admin_login.html', is_trusted_ip=trusted, client_ip=client_ip, error="Domyślne hasło 'admin' jest zablokowane dla połączeń spoza zaufanych IP. Zmień 'admin_password' w konfiguracji kontenera w Home Assistant.", next_url=next_url)

            if username == 'admin' and password == admin_pwd:
                authenticated = True
                role = 'admin'
            else:
                users = load_labels_users()
                hashed = hash_password(password)
                user_match = next((u for u in users if u.get('username') == username and u.get('password_hash') == hashed), None)
                if user_match:
                    authenticated = True
                    role = user_match.get('role', 'user')

        if authenticated:
            session['labels_user'] = username
            session['labels_role'] = role
            session['labels_scope'] = "MetaleSzlachetnePolska/etykiety"
            session['labels_last_activity'] = time.time()
            return redirect(next_url)
        else:
            return render_template('MetaleSzlachetnePolska/etykiety/admin_login.html', is_trusted_ip=trusted, client_ip=client_ip, error="Nieprawidłowa nazwa użytkownika lub hasło.", next_url=next_url)

    return render_template('MetaleSzlachetnePolska/etykiety/admin_login.html', is_trusted_ip=trusted, client_ip=client_ip, next_url=next_url)

@app.route('/MetaleSzlachetnePolska/etykiety/admin/logout')
def admin_labels_logout():
    session.pop('labels_user', None)
    session.pop('labels_role', None)
    session.pop('labels_scope', None)
    session.pop('labels_last_activity', None)
    return redirect('/MetaleSzlachetnePolska/etykiety/admin/login')

@app.route('/MetaleSzlachetnePolska/etykiety/admin')
@app.route('/MetaleSzlachetnePolska/etykiety/admin/')
def admin_labels_root():
    if not is_labels_authenticated():
        return redirect('/MetaleSzlachetnePolska/etykiety/admin/login?next=/MetaleSzlachetnePolska/etykiety/admin/edit')
    return redirect('/MetaleSzlachetnePolska/etykiety/admin/edit')

@app.route('/MetaleSzlachetnePolska/etykiety/admin/add')
@app.route('/MetaleSzlachetnePolska/etykiety/admin/add/')
def admin_add_labels():
    """Ukryta strona administracyjna do masowego dodawania monet z pliku CSV."""
    if not is_labels_authenticated():
        return redirect('/MetaleSzlachetnePolska/etykiety/admin/login?next=/MetaleSzlachetnePolska/etykiety/admin/add')
    return render_template('MetaleSzlachetnePolska/etykiety/admin_add.html', current_user=session.get('labels_user'), current_role=session.get('labels_role'))

@app.route('/MetaleSzlachetnePolska/etykiety/admin/edit')
@app.route('/MetaleSzlachetnePolska/etykiety/admin/edit/')
def admin_edit_labels():
    """Strona edycji bazy monet z wyszukiwarką 50 wyników, podglądem i modyfikacją wierszy."""
    if not is_labels_authenticated():
        return redirect('/MetaleSzlachetnePolska/etykiety/admin/login?next=/MetaleSzlachetnePolska/etykiety/admin/edit')
    return render_template('MetaleSzlachetnePolska/etykiety/admin_edit.html', current_user=session.get('labels_user'), current_role=session.get('labels_role'))

@app.route('/MetaleSzlachetnePolska/etykiety/admin/users', methods=['GET', 'POST'])
def admin_labels_users():
    """Strona zarządzania użytkownikami aplikacji etykiet (dla roli admin)."""
    if not is_labels_authenticated('admin'):
        if not is_labels_authenticated():
            return redirect('/MetaleSzlachetnePolska/etykiety/admin/login?next=/MetaleSzlachetnePolska/etykiety/admin/users')
        return "Brak uprawnień. Tylko administrator ma dostęp do zarządzania użytkownikami.", 403

    msg = None
    error = None

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        role = request.form.get('role', 'user').strip()

        if not username or not password:
            error = "Wypełnij nazwę użytkownika oraz hasło."
        elif username == 'admin':
            error = "Wbudowany użytkownik 'admin' jest zarządzany w konfiguracji HA."
        else:
            users = load_labels_users()
            existing = next((u for u in users if u.get('username') == username), None)
            now_str = time.strftime("%Y-%m-%d %H:%M")
            if existing:
                existing['password_hash'] = hash_password(password)
                existing['role'] = role
                msg = f"Zaktualizowano hasło i rolę dla użytkownika {username}."
            else:
                users.append({
                    "username": username,
                    "password_hash": hash_password(password),
                    "role": role,
                    "created_at": now_str
                })
                msg = f"Dodano nowego użytkownika {username}."
            save_labels_users(users)

    users = load_labels_users()
    return render_template('MetaleSzlachetnePolska/etykiety/admin_users.html', users=users, current_user=session.get('labels_user'), msg=msg, error=error)

@app.route('/MetaleSzlachetnePolska/etykiety/admin/users/delete', methods=['POST'])
def admin_labels_users_delete():
    if not is_labels_authenticated('admin'):
        return jsonify({"error": "Brak uprawnień administratora"}), 403
    username = request.form.get('username', '').strip()
    if username and username != 'admin':
        users = load_labels_users()
        users = [u for u in users if u.get('username') != username]
        save_labels_users(users)
    return redirect('/MetaleSzlachetnePolska/etykiety/admin/users')

@app.route('/MetaleSzlachetnePolska/etykiety/admin/template-csv')
def template_labels_csv():
    output = io.StringIO()
    output.write("\ufeffRok;Seria;Nazwa;Nakład;Nominał;WalutaPo;Stop;WalutaPrzed;Rant;Typ;Waga;Średnica;Trial;Kraj\n")
    output.write("2008;;Zbigniew Herbert (1924–1998);1510000;2;zł;NG;;gładki;stempel zwykły;14.14;27.00;FALSE;pl\n")
    output.write("2024;Britannia;King Charles III;50000;5;;Ag999;£;ząbkowany;stempel lustrzany;31.1;38.61;FALSE;uk\n")
    return Response(
        output.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-disposition": "attachment; filename=wzorzec_etykiet.csv"}
    )

@app.route('/MetaleSzlachetnePolska/etykiety/admin/test-telegram')
def test_telegram_route():
    """Endpoint testowy dla admina do weryfikacji powiadomień Telegram w Home Assistant."""
    if not is_labels_authenticated():
        return jsonify({"error": "Wymagane logowanie"}), 401
    
    ip = get_client_ip()
    title = "Test Powiadomienia Telegram"
    message = f"🧪 Test wysyłania notyfikacji Telegram z portalu Metale Szlachetne Polska (IP: {ip})."
    
    success, log_detail = send_telegram_ha_notification(title, message, return_details=True)
    return jsonify({
        "success": success,
        "detail": log_detail,
        "supervisor_token_present": bool(os.environ.get("SUPERVISOR_TOKEN")),
        "config_loaded": load_all_config_data()
    })

@app.route('/MetaleSzlachetnePolska/etykiety/admin/export-csv')
def export_labels_csv():
    if not is_labels_authenticated():
        return redirect('/MetaleSzlachetnePolska/etykiety/admin/login?next=/MetaleSzlachetnePolska/etykiety/admin/export-csv')
    labels = load_labels_db()
    output = io.StringIO()
    output.write("\ufeffRok;Seria;Nazwa;Nakład;Nominał;WalutaPo;Stop;WalutaPrzed;Rant;Typ;Waga;Średnica;Trial;Kraj\n")
    for item in labels:
        c = clean_label_item(item)
        year = c[0]
        series = c[1]
        name = c[2]
        mintage = c[3]
        nominal = c[4]
        currencyAfter = c[5]
        stop = c[6]
        currencyBefore = c[7]
        rant = c[8]
        typ = c[9]
        weight = c[10]
        diameter = c[11]
        trial = "TRUE" if c[12] else "FALSE"
        country = c[13]
        
        line = f"{year};{series};{name};{mintage};{nominal};{currencyAfter};{stop};{currencyBefore};{rant};{typ};{weight};{diameter};{trial};{country}\n"
        output.write(line)
    
    date_str = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
    filename = f"baza_etykiet_{date_str}.csv"
    return Response(
        output.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-disposition": f'attachment; filename="{filename}"'}
    )

def clean_label_item(item):
    """Zapewnia spójność 14 pól etykiety w tablicy Python."""
    if not isinstance(item, list):
        return ["", "", "", "", "2", "", "", "", "", "", "", "", False, "pl"]
    
    year = str(item[0] if len(item) > 0 else "").strip()
    series = str(item[1] if len(item) > 1 else "").strip()
    name = str(item[2] if len(item) > 2 else "").strip()
    mintage = str(item[3] if len(item) > 3 else "").strip()
    nominal = str(item[4] if len(item) > 4 else "2").strip()
    currency_after = str(item[5] if len(item) > 5 else "").strip()
    stop = str(item[6] if len(item) > 6 else "").strip()
    
    currency_before = item[7] if len(item) > 7 else ""
    if isinstance(currency_before, bool) or str(currency_before).lower() in ["true", "false"]:
        currency_before = ""
    else:
        currency_before = str(currency_before or "").strip()

    rant = str(item[8] if len(item) > 8 else "").strip()
    typ = str(item[9] if len(item) > 9 else "").strip()
    weight = str(item[10] if len(item) > 10 else "").strip()
    diameter = str(item[11] if len(item) > 11 else "").strip()

    raw_trial = item[12] if len(item) > 12 else False
    trial = True if (raw_trial is True or str(raw_trial).lower() in ["true", "1", "próba"]) else False

    country = str(item[13] if len(item) > 13 else "pl").strip().lower() or "pl"

    return [year, series, name, mintage, nominal, currency_after, stop, currency_before, rant, typ, weight, diameter, trial, country]

def make_label_fingerprint(item):
    """Generuje unikalny odcisk etykiety/monety uwzględniający wszystkie 14 parametrów."""
    c = clean_label_item(item)
    trial_str = "1" if c[12] else "0"
    return f"{c[13].lower()}|{c[0]}|{c[1].lower()}|{c[2].lower()}|{c[4].lower()}|{c[7].lower()}|{c[5].lower()}|{c[6].lower()}|{c[8].lower()}|{c[9].lower()}|{c[10]}|{c[11]}|{trial_str}"

def deduplicate_labels(label_list):
    """Usuwa wyłącznie identyczne duplikaty monet (wszystkie parametry jednakowe)."""
    seen = set()
    unique = []
    for item in label_list:
        if not isinstance(item, list):
            continue
        cleaned = clean_label_item(item)
        fp = make_label_fingerprint(cleaned)
        if fp not in seen:
            seen.add(fp)
            unique.append(cleaned)
    return unique

@app.route('/api/admin/labels/update', methods=['POST'])
@app.route('/MetaleSzlachetnePolska/etykiety/api/admin/labels/update', methods=['POST'])
def update_admin_label():
    """Endpoint do aktualizacji pojedynczego wiersza etykiety po jej dokładnym odcisku lub dodania nowej."""
    if not is_labels_authenticated():
        return jsonify({"error": "Wymagane logowanie"}), 401
    try:
        data = request.get_json(force=True, silent=True) or {}
        orig = data.get('original')
        original_fp = data.get('original_fp') or (make_label_fingerprint(orig) if orig else None)
        is_new = data.get('is_new', False)
        updated = data.get('updated')

        if not updated or not isinstance(updated, list):
            return jsonify({"error": "Brak danych do aktualizacji"}), 400

        updated_clean = clean_label_item(updated)
        labels = load_labels_db()

        if is_new or not original_fp:
            labels.append(updated_clean)
            ip = get_client_ip()
            params_summary = format_label_params_summary(updated_clean)
            send_telegram_ha_notification("Nowa moneta w sesji", f"Adres {ip} dodał do sesji nową monetę o parametrach: {params_summary}")
        else:
            found = False
            for i, item in enumerate(labels):
                if make_label_fingerprint(item) == original_fp:
                    labels[i] = updated_clean
                    found = True
                    break
            if not found:
                labels.append(updated_clean)
                ip = get_client_ip()
                params_summary = format_label_params_summary(updated_clean)
                send_telegram_ha_notification("Nowa moneta w sesji", f"Adres {ip} dodał do sesji nową monetę o parametrach: {params_summary}")

        labels = deduplicate_labels(labels)
        save_labels_db(labels)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/labels/update-batch', methods=['POST'])
def update_batch_labels():
    if not is_labels_authenticated():
        return jsonify({"error": "Wymagane logowanie"}), 401
    try:
        data = request.get_json(force=True, silent=True) or {}
        updates = data.get('updates', [])
        if not updates or not isinstance(updates, list):
            return jsonify({"error": "Brak danych do aktualizacji"}), 400

        labels = load_labels_db()
        updated_count = 0

        for u in updates:
            orig = u.get('original')
            original_fp = u.get('original_fp') or (make_label_fingerprint(orig) if orig else None)
            is_new = u.get('is_new', False)
            upd = u.get('updated')
            if not upd or not isinstance(upd, list):
                continue

            upd_clean = clean_label_item(upd)

            if is_new or not original_fp:
                labels.append(upd_clean)
                updated_count += 1
                ip = get_client_ip()
                params_summary = format_label_params_summary(upd_clean)
                send_telegram_ha_notification("Nowa moneta w sesji", f"Adres {ip} dodał do sesji nową monetę o parametrach: {params_summary}")
            else:
                found = False
                for i, item in enumerate(labels):
                    if make_label_fingerprint(item) == original_fp:
                        labels[i] = upd_clean
                        found = True
                        updated_count += 1
                        break
                if not found:
                    labels.append(upd_clean)
                    updated_count += 1
                    ip = get_client_ip()
                    params_summary = format_label_params_summary(upd_clean)
                    send_telegram_ha_notification("Nowa moneta w sesji", f"Adres {ip} dodał do sesji nową monetę o parametrach: {params_summary}")

        labels = deduplicate_labels(labels)
        save_labels_db(labels)
        return jsonify({"success": True, "updated_count": updated_count})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/MetaleSzlachetnePolska/etykiety/admin/template-csv')
def download_csv_template():
    """Endpoint do pobrania wzorcowego pliku CSV do uzupełniania monet z rozszerzonymi polami."""
    csv_content = "\ufeffRok;Seria;Nazwa;Nakład;Nominał;WalutaPo;Stop;WalutaPrzed;Rant;Typ;Waga;Średnica;Trial;Kraj\n" \
                  "2008;;Zbigniew Herbert (1924–1998);1510000;2;zł;NG;;gładki;stempel zwykły;14.14;27.00;FALSE;pl\n" \
                  "2024;Britannia;King Charles III;50000;5;;Ag999;£;ząbkowany;stempel lustrzany;31.1;38.61;FALSE;uk\n" \
                  "2026;seria cc;Nowa moneta;45000000;2;;Nordic Gold;$;gładki;próba;14.14;27.00;TRUE;us\n"
    return Response(
        csv_content,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-disposition": "attachment; filename=wzor_etykiet.csv"}
    )

def parse_search_query(raw_query):
    """
    Parsuje zapytanie tekstowe na:
    1. req_trial (bool) - czy wpisano 'trial', 'próba' lub 'proba'
    2. exact_phrases (list of str) - frazy w cudzysłowach "..." lub '...'
    3. word_tokens (list of str) - pozostałe pojedyncze słowa
    """
    if not raw_query or not str(raw_query).strip():
        return False, [], []

    q = str(raw_query).strip()
    req_trial = False

    exact_phrases = []
    pattern = r'["\']([^"\']+)["\']'
    matches = re.findall(pattern, q)
    for m in matches:
        phrase = m.strip().lower()
        if phrase in ['trial', 'próba', 'proba']:
            req_trial = True
        elif phrase:
            exact_phrases.append(phrase)

    remainder = re.sub(pattern, ' ', q).strip().lower()

    word_tokens = []
    for token in remainder.split():
        t = token.strip()
        if t in ['trial', 'próba', 'proba']:
            req_trial = True
        elif t:
            word_tokens.append(t)

    return req_trial, exact_phrases, word_tokens

def match_label_item(item, req_trial, exact_phrases, word_tokens):
    """
    Weryfikuje czy dany wpis monety spełnia kryteria zapytania.
    Nie przeszukuje rocznika (item[0]), kraju (item[13]) ani 'true'/'false' z pola trial (item[12]).
    """
    clean = clean_label_item(item)
    trial_bool = clean[12]

    if req_trial and not trial_bool:
        return False

    # Pola przeszukiwalne w głównym oknie (wykluczono Rok[0], Trial[12], Kraj[13])
    searchable_fields = [
        clean[1], clean[2], clean[3], clean[4], clean[5],
        clean[6], clean[7], clean[8], clean[9], clean[10], clean[11]
    ]
    searchable_text = " ".join([str(x).strip().lower() for x in searchable_fields if str(x).strip()])

    for phrase in exact_phrases:
        if phrase not in searchable_text:
            return False

    for token in word_tokens:
        if token not in searchable_text:
            return False

    return True

def parse_num_val(val_str):
    """Pomocnicza funkcja parsująca elastycznie liczby (np. '2', '10', '14.14', '27,00') na float do właściwego sortowania numerycznego."""
    if not val_str:
        return 999999.0
    s = str(val_str).strip().replace(',', '.')
    match = re.search(r'\d+(?:\.\d+)?', s)
    if match:
        try:
            return float(match.group(0))
        except ValueError:
            pass
    return 999999.0

def label_sort_key(item):
    """
    Hierarchiczny klucz sortowania monet:
    1. Kraj (pl, uk, us...)
    2. Rocznik (1932, 1933...) - roczniki nie są ze sobą mieszane
    3. Stop (Ag750, Ag999, NG...) - w obrębie danego rocznika
    4. Nominał numerycznie (2 < 5 < 10) - w obrębie danego rocznika i stopu
    5. Nazwa (np. Głowa Kobiety)
    6. Seria (np. skarb istebniański)
    7. Średnica numerycznie (np. 27.00 < 38.61)
    8. Waga numerycznie (np. 14.14 < 31.1)
    9. Rant
    10. Typ
    11. Trial (0 = False, 1 = True)
    """
    c = clean_label_item(item)
    year_val = c[0]
    series_val = c[1].lower()
    name_val = c[2].lower()
    nominal_str = c[4]
    stop_val = c[6].lower()
    rant_val = c[8].lower()
    typ_val = c[9].lower()
    weight_str = c[10]
    diameter_str = c[11]
    trial_val = 1 if c[12] else 0
    country_val = c[13].lower()

    try:
        year_clean = re.sub(r'\D', '', year_val)
        year_num = int(year_clean) if year_clean else 999999
    except Exception:
        year_num = 999999

    nominal_num = parse_num_val(nominal_str)
    diameter_num = parse_num_val(diameter_str)
    weight_num = parse_num_val(weight_str)

    return (
        country_val,     # 1. Kraj
        year_num,        # 2. Rocznik
        stop_val,        # 3. Stop
        nominal_num,     # 4. Nominał numerycznie
        name_val,        # 5. Nazwa
        series_val,      # 6. Seria
        diameter_num,    # 7. Średnica numerycznie
        weight_num,      # 8. Waga numerycznie
        rant_val,        # 9. Rant
        typ_val,         # 10. Typ
        trial_val        # 11. Trial
    )

@app.route('/api/labels', methods=['GET'])
@app.route('/MetaleSzlachetnePolska/etykiety/api/labels', methods=['GET'])
def get_labels():
    """
    Zwraca bazę etykiet z precyzyjnym wyszukiwaniem, wykluczeniem rocznika/kraju/trial z szukajki,
    obsługą cudzysłowów oraz sortowaniem (kraj, stop, rocznik, nominał, nazwa, średnica, waga, rant, typ, trial).
    """
    labels = load_labels_db()
    query_raw = request.args.get('q', '').strip()
    year_filter = request.args.get('year', '').strip()
    country_filter = request.args.get('country', '').strip().lower()
    limit = request.args.get('limit', 50, type=int)

    # Wyciągnięcie dostępnych krajów z bazy
    countries_set = set()
    for item in labels:
        c = "pl"
        if len(item) > 13 and item[13]:
            c = str(item[13]).strip().lower()
        if c:
            countries_set.add(c)

    for default_c in ["pl", "us", "uk", "de", "ca", "au", "at", "ch", "fr"]:
        countries_set.add(default_c)

    countries_list = sorted(list(countries_set))

    req_trial, exact_phrases, word_tokens = parse_search_query(query_raw)

    matching = []
    for item in labels:
        clean = clean_label_item(item)
        item_year = clean[0]
        item_country = clean[13]

        if year_filter and year_filter != item_year:
            continue
        if country_filter and country_filter != item_country:
            continue

        if query_raw or req_trial:
            if not match_label_item(item, req_trial, exact_phrases, word_tokens):
                continue

        matching.append(clean)

    # Sortowanie: Kraj -> Stop -> Rocznik -> Nominał -> Nazwa -> Średnica -> Waga -> Rant -> Typ -> Trial
    matching.sort(key=label_sort_key)

    if not query_raw and not year_filter and not country_filter and not req_trial and (0 < limit <= 50):
        return jsonify({
            "status": "success",
            "total_matches": 0,
            "labels": [],
            "countries": countries_list
        })

    result_labels = matching if (limit <= 0 or limit >= 50000) else matching[:limit]

    return jsonify({
        "status": "success",
        "total_matches": len(matching),
        "labels": result_labels,
        "countries": countries_list
    })

@app.route('/api/admin/labels', methods=['POST'])
@app.route('/MetaleSzlachetnePolska/etykiety/api/admin/labels', methods=['POST'])
def update_admin_labels():
    """
    Endpoint administracyjny do edycji bazy etykiet.
    Wspiera 14 pól i zabezpiecza przed wprowadzaniem duplikatów.
    """
    try:
        data = request.get_json(force=True, silent=True) or {}
        labels = load_labels_db()

        if "labels" in data and isinstance(data["labels"], list):
            labels = data["labels"]
        elif "label" in data and isinstance(data["label"], list):
            labels.append(data["label"])
        elif "name" in data or "year" in data:
            item = [
                str(data.get("year", "")),
                str(data.get("series", "")),
                str(data.get("name", "")),
                str(data.get("mintage", "")),
                str(data.get("nominal", "2")),
                str(data.get("currency_after", data.get("currency", "zł"))),
                str(data.get("stop", "")),
                str(data.get("currency_before", "")),
                str(data.get("rant", "")),
                str(data.get("typ", "")),
                str(data.get("weight", "")),
                str(data.get("diameter", "")),
                bool(data.get("trial", False)),
                str(data.get("country", "pl")).lower().strip() or "pl"
            ]
            labels.append(item)
        else:
            return jsonify({"error": "Nieprawidłowy format danych. Przekaż 'labels' (tablica) lub dane etykiety."}), 400

        labels = deduplicate_labels(labels)
        save_labels_db(labels)
        return jsonify({
            "status": "success",
            "message": "Baza etykiet została pomyślnie zaktualizowana i odduplikowana na serwerze.",
            "total": len(labels),
            "labels": labels
        })
    except Exception as e:
        return jsonify({"error": f"Błąd aktualizacji bazy etykiet: {str(e)}"}), 500

@app.route('/api/admin/labels', methods=['DELETE'])
@app.route('/MetaleSzlachetnePolska/etykiety/api/admin/labels', methods=['DELETE'])
def delete_admin_label():
    """Endpoint administracyjny do usuwania pojedynczego wpisu z bazy etykiet."""
    try:
        data = request.get_json(force=True, silent=True) or {}
        index = data.get("index")
        label = data.get("label")
        labels = load_labels_db()
        deleted = False

        if index is not None and isinstance(index, int) and 0 <= index < len(labels):
            labels.pop(index)
            deleted = True
        elif label and isinstance(label, list):
            target_fp = make_label_fingerprint(label)
            for i, item in enumerate(labels):
                if make_label_fingerprint(item) == target_fp:
                    labels.pop(i)
                    deleted = True
                    break

        if deleted:
            save_labels_db(labels)
            return jsonify({
                "status": "success",
                "success": True,
                "message": "Etykieta została usunięta z bazy serwera.",
                "total": len(labels)
            })

        return jsonify({"error": "Nie odnaleziono podanej etykiety do usunięcia."}), 404
    except Exception as e:
        return jsonify({"error": f"Błąd usuwania etykiety: {str(e)}"}), 500

@app.route('/api/admin/labels/clear', methods=['POST'])
@app.route('/MetaleSzlachetnePolska/etykiety/api/admin/labels/clear', methods=['POST'])
def clear_admin_labels_db():
    """Endpoint administracyjny do czyszczenia całej bazy etykiet (tylko dla roli admin)."""
    if not is_labels_authenticated('admin'):
        return jsonify({"error": "Brak uprawnień administracyjnych (wymagana rola admin)."}), 403
    try:
        save_labels_db([])
        return jsonify({
            "status": "success",
            "success": True,
            "message": "Cała baza etykiet została pomyślnie wyczyszczona.",
            "total": 0
        })
    except Exception as e:
        return jsonify({"error": f"Błąd czyszczenia bazy etykiet: {str(e)}"}), 500

@app.route('/MetaleSzlachetnePolska/metale_polska.webp')
def serve_metale_polska_banner():
    return send_from_directory(os.path.join(app.template_folder, 'MetaleSzlachetnePolska'), 'metale_polska.webp')

@app.route('/MetaleSzlachetnePolska/metale_polska_icon.webp')
def serve_metale_polska_icon():
    return send_from_directory(os.path.join(app.template_folder, 'MetaleSzlachetnePolska'), 'metale_polska_icon.webp')

@app.route('/logs')
@app.route('/logs/')
@app.route('/MetaleSzlachetnePolska/logs')
@app.route('/MetaleSzlachetnePolska/logs/')
def view_logs_page():
    is_trusted = is_client_ip_trusted()
    client_ip = get_client_ip()
    if not is_trusted:
        return render_template('logs.html', error_access="Brak uprawnień. Dostęp do dziennika logów jest dozwolony wyłącznie z zaufanych adresów IP.", is_trusted=False, client_ip=client_ip), 403
    return render_template('logs.html', is_trusted=True, client_ip=client_ip, current_user=session.get('labels_user'))

@app.route('/api/logs/data', methods=['GET'])
def get_logs_data():
    if not is_client_ip_trusted():
        return jsonify({"error": "Brak uprawnień do przeglądania logów."}), 403
    logs = []
    if os.path.exists(ACTIVITY_LOGS_PATH):
        try:
            with open(ACTIVITY_LOGS_PATH, "r", encoding="utf-8") as f:
                logs = json.load(f)
                if not isinstance(logs, list):
                    logs = []
        except Exception:
            logs = []
    return jsonify({"status": "success", "logs": logs, "total": len(logs)})

@app.route('/api/logs/clear', methods=['POST'])
def clear_logs_data():
    if not is_client_ip_trusted():
        return jsonify({"error": "Brak uprawnień."}), 403
    try:
        with open(ACTIVITY_LOGS_PATH, "w", encoding="utf-8") as f:
            json.dump([], f)
        return jsonify({"status": "success", "message": "Logi zostały wyczyszczone."})
    except Exception as e:
        return jsonify({"error": f"Błąd czyszczenia logów: {str(e)}"}), 500

@app.route('/MetaleSzlachetnePolska/etykiety/api/log-print', methods=['POST'])
@app.route('/api/etykiety/log-print', methods=['POST'])
def log_label_print():
    data = request.get_json(force=True, silent=True) or {}
    labels = data.get("labels", [])
    count = len(labels)
    details = {
        "count": count,
        "labels": labels
    }
    log_activity_entry('label_print', details=details, req=request)
    
    ip = get_client_ip()
    send_telegram_ha_notification("Generowanie etykiet", f"Adres {ip} wygenerował nowe etykiety w ilości sztuk: {count}")

    return jsonify({"status": "success", "count": count})

@app.route('/MetaleSzlachetnePolska/youtube')
@app.route('/MetaleSzlachetnePolska/youtube/')
def index():
    return render_template('MetaleSzlachetnePolska/youtube/index.html')

@app.route('/youtube')
@app.route('/youtube/')
def redirect_old_youtube():
    return redirect('/MetaleSzlachetnePolska/youtube', code=302)

@app.route('/api/info')
@app.route('/youtube/api/info')
@app.route('/MetaleSzlachetnePolska/api/info')
@app.route('/MetaleSzlachetnePolska/youtube/api/info')
def api_info():
    """Zwraca wersję aplikacji, status kluczy i listę dozwolonych kanałów."""
    global_key = get_global_api_key()
    discord_token = get_discord_bot_token()
    channels = load_allowed_channels()
    return jsonify({
        "version": APP_VERSION,
        "has_global_key": bool(global_key),
        "has_discord_token": bool(discord_token),
        "allowed_channels": channels
    })

@app.route('/api/channel-profile')
@app.route('/youtube/api/channel-profile')
@app.route('/MetaleSzlachetnePolska/youtube/api/channel-profile')
def channel_profile():
    """Zwraca baner, avatar, opis i statystyki aktualnie wybranego kanału."""
    api_key = resolve_api_key()
    channel_handle = resolve_channel_handle()
    profile = youtube_service.get_channel_profile_details(api_key, channel_handle=channel_handle)
    return jsonify(profile)

@app.route('/api/admin/set-global-key', methods=['POST'])
@app.route('/youtube/api/admin/set-global-key', methods=['POST'])
@app.route('/MetaleSzlachetnePolska/youtube/api/admin/set-global-key', methods=['POST'])
def set_global_key():
    """Endpoint administracyjny do ustawiania klucza globalnego przez POST JSON."""
    try:
        data = request.get_json(force=True, silent=True) or {}
        key = data.get("global_api_key", "").strip()
        if not key:
            return jsonify({"error": "Brak parametru global_api_key w żądaniu."}), 400
        
        save_global_api_key(key)
        return jsonify({
            "status": "success",
            "message": "Globalny klucz API został pomyślnie zapisany na serwerze.",
            "path": GLOBAL_CONFIG_PATH
        })
    except Exception as e:
        return jsonify({"error": f"Nie udało się zapisać klucza na serwerze: {str(e)}"}), 500

@app.route('/api/admin/set-discord-token', methods=['POST'])
@app.route('/youtube/api/admin/set-discord-token', methods=['POST'])
@app.route('/MetaleSzlachetnePolska/youtube/api/admin/set-discord-token', methods=['POST'])
def set_discord_token():
    """Endpoint administracyjny do ustawiania tokenu bota Discord przez POST JSON."""
    try:
        data = request.get_json(force=True, silent=True) or {}
        token = data.get("discord_bot_token", "").strip()
        if not token:
            return jsonify({"error": "Brak parametru discord_bot_token w żądaniu."}), 400
        
        save_discord_bot_token(token)
        return jsonify({
            "status": "success",
            "message": "Token bota Discord został pomyślnie zapisany na serwerze.",
            "path": GLOBAL_CONFIG_PATH
        })
    except Exception as e:
        return jsonify({"error": f"Nie udało się zapisać tokenu bota Discord: {str(e)}"}), 500

@app.route('/api/admin/channels', methods=['GET'])
@app.route('/youtube/api/admin/channels', methods=['GET'])
@app.route('/MetaleSzlachetnePolska/youtube/api/admin/channels', methods=['GET'])
def get_admin_channels():
    """Zwraca aktualną listę dozwolonych kanałów."""
    return jsonify({
        "status": "success",
        "allowed_channels": load_allowed_channels()
    })

@app.route('/api/admin/channels/add', methods=['POST'])
@app.route('/youtube/api/admin/channels/add', methods=['POST'])
@app.route('/MetaleSzlachetnePolska/youtube/api/admin/channels/add', methods=['POST'])
def add_admin_channel():
    """Endpoint administracyjny do dodawania nowego kanału do listy dozwolonych."""
    try:
        data = request.get_json(force=True, silent=True) or {}
        handle = data.get("handle", "").strip()
        title = data.get("title", "").strip()

        if not handle:
            return jsonify({"error": "Brak wymaganego parametru 'handle' (np. @ArturK92)."}), 400

        if not handle.startsWith("@") if hasattr(handle, "startsWith") else not handle.startswith("@"):
            handle = "@" + handle

        channels = load_allowed_channels()
        
        # Sprawdź czy kanał już istnieje
        existing = next((c for c in channels if c["handle"].lower() == handle.lower()), None)
        
        if not title:
            # Spróbuj pobrać nazwę z API jeśli dostępny jest klucz
            api_key = resolve_api_key()
            if api_key:
                try:
                    yt = youtube_service.get_youtube_client(api_key)
                    _, resolved_handle, resolved_title = youtube_service.resolve_channel_info(yt, handle)
                    if resolved_title:
                        title = resolved_title
                except Exception:
                    pass
            if not title:
                title = handle.replace("@", "")

        if existing:
            existing["title"] = title
            existing["handle"] = handle
        else:
            channels.append({"handle": handle, "title": title})

        save_allowed_channels(channels)
        return jsonify({
            "status": "success",
            "message": f"Kanał {handle} został pomyślnie dodany do dozwolonych.",
            "allowed_channels": channels
        })
    except Exception as e:
        return jsonify({"error": f"Błąd podczas dodawania kanału: {str(e)}"}), 500

@app.route('/api/admin/channels/remove', methods=['POST', 'DELETE'])
@app.route('/youtube/api/admin/channels/remove', methods=['POST', 'DELETE'])
@app.route('/MetaleSzlachetnePolska/youtube/api/admin/channels/remove', methods=['POST', 'DELETE'])
def remove_admin_channel():
    """Endpoint administracyjny do usuwania kanału z listy dozwolonych."""
    try:
        data = request.get_json(force=True, silent=True) or {}
        handle = data.get("handle", "").strip()
        if not handle:
            handle = request.args.get("handle", "").strip()

        if not handle:
            return jsonify({"error": "Brak parametru 'handle' do usunięcia."}), 400

        if not handle.startswith("@"):
            handle = "@" + handle

        channels = load_allowed_channels()
        initial_count = len(channels)
        channels = [c for c in channels if c["handle"].lower() != handle.lower()]

        if len(channels) == initial_count:
            return jsonify({"error": f"Nie odnaleziono kanału {handle} na liście."}), 444 if False else 404

        save_allowed_channels(channels)
        return jsonify({
            "status": "success",
            "message": f"Kanał {handle} został usunięty z listy dozwolonych.",
            "allowed_channels": channels
        })
    except Exception as e:
        return jsonify({"error": f"Błąd podczas usuwania kanału: {str(e)}"}), 500

@app.route('/api/videos')
@app.route('/youtube/api/videos')
@app.route('/MetaleSzlachetnePolska/youtube/api/videos')
def get_videos():
    api_key = resolve_api_key()
    if not api_key:
        return jsonify({"error": "Brak klucza API. Ustaw klucz globalny na serwerze lub podaj własny klucz w Ustawieniach."}), 400

    channel_handle = resolve_channel_handle()

    try:
        data = youtube_service.get_channel_videos(api_key, channel_handle=channel_handle, max_results=200)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/comments')
@app.route('/youtube/api/comments')
@app.route('/MetaleSzlachetnePolska/youtube/api/comments')
def get_comments():
    api_key = resolve_api_key()
    if not api_key:
        return jsonify({"error": "Brak klucza API."}), 400

    video_id = request.args.get('video_id')
    if not video_id:
        return jsonify({"error": "Brak parametru video_id"}), 400

    try:
        comments = youtube_service.get_all_comments_for_video(api_key, video_id)
        return jsonify({"video_id": video_id, "comments": comments})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/export-csv')
@app.route('/youtube/api/export-csv')
@app.route('/MetaleSzlachetnePolska/youtube/api/export-csv')
def export_csv():
    api_key = resolve_api_key()
    if not api_key:
        return "Brak klucza API", 400

    video_id = request.args.get('video_id')
    if not video_id:
        return "Brak parametru video_id", 400

    try:
        comments = youtube_service.get_all_comments_for_video(api_key, video_id)
        
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(['Lp', 'Autor', 'Komentarz', 'Data publikacji'])
        
        for idx, c in enumerate(comments, 1):
            writer.writerow([idx, c['author'], c['comment'], c['date']])
            
        csv_data = output.getvalue()
        
        return Response(
            csv_data,
            mimetype="text/csv",
            headers={"Content-disposition": f"attachment; filename=komentarze_{video_id}.csv"}
        )
    except Exception as e:
        return f"Błąd tworzenia pliku CSV: {str(e)}", 500

@app.route('/api/draw-result', methods=['POST'])
@app.route('/youtube/api/draw-result', methods=['POST'])
@app.route('/MetaleSzlachetnePolska/youtube/api/draw-result', methods=['POST'])
def record_draw_result():
    """
    Rejestruje wynik przeprowadzonego losowania, wypisuje szczegółowy log do konsoli HA
    oraz zapisuje wpis w archiwalnym pliku JSON.
    """
    from datetime import datetime
    try:
        data = request.get_json(silent=True) or {}
        
        # Pobieramy IP klienta z nagłówków proxy HA lub bezpośredniego połączenia
        client_ip = request.headers.get("X-Forwarded-For", request.remote_addr or "Nieznane IP")
        if client_ip and "," in client_ip:
            client_ip = client_ip.split(",")[0].strip()

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        channel_handle = data.get("channel_handle") or resolve_channel_handle()
        video_id = data.get("video_id", "")
        video_title = data.get("video_title", "Nieznany film")
        
        video_url = f"https://www.youtube.com/watch?v={video_id}" if video_id and video_id != "custom_list" else "Własna lista użytkowników"
        
        spin_duration_sec = data.get("spin_duration_sec", 15)
        power_level = data.get("power_level", 1)
        
        winner_data = data.get("winner", {})
        winner_author = winner_data.get("author", "Brak")
        winner_comment = winner_data.get("comment", "")
        
        participants = data.get("participants", [])
        participants_count = len(participants)

        filter_settings = data.get("filter_settings", {})
        channel_title = data.get("channel_title") or channel_handle

        entry = {
            "timestamp": now_str,
            "client_ip": client_ip,
            "channel_handle": channel_handle,
            "channel_title": channel_title,
            "video_id": video_id,
            "video_title": video_title,
            "video_url": video_url,
            "filter_settings": filter_settings,
            "spin_duration_sec": spin_duration_sec,
            "power_level": power_level,
            "winner": {
                "author": winner_author,
                "comment": winner_comment
            },
            "participants_count": participants_count,
            "participants": participants
        }

        # Trwałe zapisanie do historii losowań i do uniwersalnego dziennika aktywności
        save_draw_result_entry(entry)
        log_activity_entry('wheel_draw', details=entry, req=request)

        # Wypisanie czytelnego loga do konsoli HA (stdout / sys.stderr)
        sample_names = []
        for p in participants[:30]:
            if isinstance(p, dict):
                sample_names.append(str(p.get("author") or p.get("name") or p))
            else:
                sample_names.append(str(p))
        sample_participants = ", ".join(sample_names)
        if participants_count > 30:
            sample_participants += f" ... (+{participants_count - 30} więcej)"

        ha_log_entry = f"""
================================================================================
🎉 [KOŁO FORTUNY - WYGRANE LOSOWANIE]
--------------------------------------------------------------------------------
📅 Data i czas:      {now_str}
🌐 IP Klienta:       {client_ip}
📺 Kanał YouTube:    {channel_handle}
🎬 Materiał:         {video_title} ({video_url})
⏱️ Czas kręcenia:    {spin_duration_sec}s
⚡ Siła losowania:   {power_level} / 20
👥 Liczba osób:      {participants_count}
📋 Uczestnicy:       {sample_participants}
🏆 Wygrany autor:    {winner_author}
💬 Komentarz:        "{winner_comment}"
================================================================================
"""
        print(ha_log_entry, flush=True)
        app.logger.info(ha_log_entry)

        return jsonify({"status": "success", "message": "Losowanie zarejestrowane w logach HA", "entry": entry})
    except Exception as e:
        return jsonify({"error": f"Błąd rejestrowania losowania: {str(e)}"}), 500

@app.route('/api/admin/draw-history', methods=['GET'])
@app.route('/youtube/api/admin/draw-history', methods=['GET'])
@app.route('/MetaleSzlachetnePolska/youtube/api/admin/draw-history', methods=['GET'])
def get_draw_history():
    """Zwraca archiwalną listę zrealizowanych losowań z pliku json."""
    history = load_draw_history()
    return jsonify({
        "status": "success",
        "total": len(history),
        "history": history
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
