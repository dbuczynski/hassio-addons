import csv
import io
import json
import os
from flask import Flask, jsonify, render_template, request, Response
import youtube_service

app = Flask(__name__)

APP_VERSION = "1.7.3"

# Lista dozwolonych kanałów YouTube dla których można listować filmy
ALLOWED_CHANNELS = [
    {"handle": "@UncjuszPatyniusz", "title": "Uncjusz Patyniusz"},
    {"handle": "@ZlotyBazyliszek", "title": "Złoty Bazyliszek"},
    {"handle": "@ArturK92", "title": "ArturK92"}
]

DATA_DIR = "/data" if os.path.exists("/data") else os.path.dirname(os.path.abspath(__file__))
GLOBAL_CONFIG_PATH = os.path.join(DATA_DIR, "global_config.json")

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
    return "@UncjuszPatyniusz"

@app.route('/')

@app.route('/youtube')
def index():
    return render_template('index.html')

@app.route('/api/info')
@app.route('/youtube/api/info')
def api_info():
    """Zwraca wersję aplikacji, status klucza globalnego i listę dozwolonych kanałów."""
    global_key = get_global_api_key()
    return jsonify({
        "version": APP_VERSION,
        "has_global_key": bool(global_key),
        "allowed_channels": ALLOWED_CHANNELS
    })

@app.route('/api/admin/set-global-key', methods=['POST'])
@app.route('/youtube/api/admin/set-global-key', methods=['POST'])
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

@app.route('/api/videos')
@app.route('/youtube/api/videos')
def get_videos():
    api_key = resolve_api_key()
    if not api_key:
        return jsonify({"error": "Brak klucza API. Ustaw klucz globalny na serwerze lub podaj własny klucz w Ustawieniach."}), 400

    channel_handle = resolve_channel_handle()

    try:
        data = youtube_service.get_channel_videos(api_key, channel_handle=channel_handle, max_results=12)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/comments')
@app.route('/youtube/api/comments')
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
