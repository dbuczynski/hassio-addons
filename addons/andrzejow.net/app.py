import csv
import io
import json
import os
from flask import Flask, jsonify, render_template, request, Response, redirect
import youtube_service

app = Flask(__name__)

APP_VERSION = "1.9.1"

DEFAULT_ALLOWED_CHANNELS = [
    {"handle": "@UncjuszPatyniusz", "title": "Uncjusz Patyniusz"},
    {"handle": "@ZlotyBazyliszek", "title": "Złoty Bazyliszek"},
    {"handle": "@ArturK92", "title": "ArturK92"}
]

DATA_DIR = "/data" if os.path.exists("/data") else os.path.dirname(os.path.abspath(__file__))
GLOBAL_CONFIG_PATH = os.path.join(DATA_DIR, "global_config.json")
LABELS_DB_PATH = os.path.join(DATA_DIR, "labels_db.json")
DEFAULT_LABELS_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "labels_db.json")

def load_labels_db():
    target_path = LABELS_DB_PATH
    if not os.path.exists(target_path) and os.path.exists(DEFAULT_LABELS_DB_PATH):
        target_path = DEFAULT_LABELS_DB_PATH
    if os.path.exists(target_path):
        try:
            with open(target_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

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
    """Pobiera globalny klucz API z pliku global_config.json jeśli istnieje."""
    if os.path.exists(GLOBAL_CONFIG_PATH):
        try:
            with open(GLOBAL_CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("global_api_key", "").strip()
        except Exception:
            pass
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
    if os.path.exists(GLOBAL_CONFIG_PATH):
        try:
            with open(GLOBAL_CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "allowed_channels" in data and isinstance(data["allowed_channels"], list):
                    return data["allowed_channels"]
        except Exception:
            pass
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

@app.route('/MetaleSzlachetnePolska/etykiety/admin/add')
@app.route('/MetaleSzlachetnePolska/etykiety/admin/add/')
def admin_add_labels():
    """Ukryta strona administracyjna do masowego dodawania monet z pliku CSV."""
    return render_template('MetaleSzlachetnePolska/etykiety/admin_add.html')

@app.route('/MetaleSzlachetnePolska/etykiety/admin/template-csv')
def download_csv_template():
    """Endpoint do pobrania wzorcowego pliku CSV do uzupełniania monet."""
    csv_content = "\ufeffRok;Seria;Nazwa;Nakład;Nominał;WalutaPo;Stop;WalutaPrzed\n" \
                  "2008;;Zbigniew Herbert (1924–1998);1510000;2;zł;NG;\n" \
                  "2024;Britannia;King Charles III;50000;5;;Ag999;£\n" \
                  "2026;seria cc;Nowa moneta;45000000;2;;Nordic Gold;$\n"
    return Response(
        csv_content,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-disposition": "attachment; filename=wzor_etykiet.csv"}
    )

@app.route('/api/labels', methods=['GET'])
@app.route('/MetaleSzlachetnePolska/etykiety/api/labels', methods=['GET'])
def get_labels():
    """Zwraca bazę etykiet z dynamicznym wyszukiwaniem wielosłowowym (AND) i limitem max 50 wyników (chyba że podano wyższy limit)."""
    labels = load_labels_db()
    query = request.args.get('q', '').strip().lower()
    limit = request.args.get('limit', 50, type=int)

    if not query:
        if limit > 50:
            return jsonify({
                "status": "success",
                "total_matches": len(labels),
                "labels": labels[:limit]
            })
        return jsonify({
            "status": "success",
            "total_matches": 0,
            "labels": []
        })

    tokens = [t for t in query.split() if t]
    matching = []

    for item in labels:
        item_text = " ".join([str(x) for x in item]).lower()
        if all(token in item_text for token in tokens):
            matching.append(item)

    return jsonify({
        "status": "success",
        "total_matches": len(matching),
        "labels": matching[:limit]
    })

@app.route('/api/admin/labels', methods=['POST'])
@app.route('/MetaleSzlachetnePolska/etykiety/api/admin/labels', methods=['POST'])
def update_admin_labels():
    """
    Endpoint administracyjny do edycji bazy etykiet.
    Można przekazać nową całą listę {"labels": [[...], [...]]} lub pojedynczy wpis.
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
                str(data.get("currency_before", ""))
            ]
            labels.append(item)
        else:
            return jsonify({"error": "Nieprawidłowy format danych. Przekaż 'labels' (tablica) lub dane etykiety."}), 400

        save_labels_db(labels)
        return jsonify({
            "status": "success",
            "message": "Baza etykiet została pomyślnie zaktualizowana na serwerze.",
            "total": len(labels),
            "labels": labels
        })
    except Exception as e:
        return jsonify({"error": f"Błąd aktualizacji bazy etykiet: {str(e)}"}), 500

@app.route('/api/admin/labels', methods=['DELETE'])
@app.route('/MetaleSzlachetnePolska/etykiety/api/admin/labels', methods=['DELETE'])
def delete_admin_label():
    """Endpoint administracyjny do usuwania wpisu z bazy etykiet."""
    try:
        data = request.get_json(force=True, silent=True) or {}
        index = data.get("index")
        name = data.get("name")
        labels = load_labels_db()

        if index is not None and isinstance(index, int) and 0 <= index < len(labels):
            labels.pop(index)
        elif name:
            initial = len(labels)
            labels = [l for l in labels if len(l) > 2 and l[2].lower() != str(name).lower()]
            if len(labels) == initial:
                return jsonify({"error": f"Nie odnaleziono etykiety o nazwie '{name}'."}), 404
        else:
            return jsonify({"error": "Brak parametru 'index' lub 'name' do usunięcia."}), 400

        save_labels_db(labels)
        return jsonify({
            "status": "success",
            "message": "Etykieta została usunięta z bazy serwera.",
            "total": len(labels),
            "labels": labels
        })
    except Exception as e:
        return jsonify({"error": f"Błąd usuwania etykiety: {str(e)}"}), 500

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

        entry = {
            "timestamp": now_str,
            "client_ip": client_ip,
            "channel_handle": channel_handle,
            "video_id": video_id,
            "video_title": video_title,
            "video_url": video_url,
            "spin_duration_sec": spin_duration_sec,
            "power_level": power_level,
            "winner": {
                "author": winner_author,
                "comment": winner_comment
            },
            "participants_count": participants_count,
            "participants": participants
        }

        # Trwałe zapisanie do pliku JSON
        save_draw_result_entry(entry)

        # Wypisanie czytelnego loga do konsoli HA (stdout / sys.stderr)
        sample_participants = ", ".join(participants[:30])
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
