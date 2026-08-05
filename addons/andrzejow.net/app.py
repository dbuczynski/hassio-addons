import csv
import io
import json
import os
from flask import Flask, jsonify, render_template, request, Response
import youtube_service

app = Flask(__name__)

APP_VERSION = "1.5.8"

# Lista dozwolonych kanałów YouTube dla których można listować filmy
ALLOWED_CHANNELS = [
    {"handle": "@UncjuszPatyniusz", "title": "Uncjusz Patyniusz"},
]


def get_possible_config_paths():
    """Zwraca listę możliwych ścieżek zapisu pliku global_config.json z obsługą fallbacków."""
    paths = []
    # Ścieżka 1: Trwały katalog danych Home Assistant Add-on
    if os.path.exists("/data"):
        paths.append("/data/global_config.json")

    # Ścieżka 2: Katalog aplikacji
    base_dir = os.path.dirname(os.path.abspath(__file__))
    paths.append(os.path.join(base_dir, "global_config.json"))
    paths.append(os.path.join(base_dir, "data", "global_config.json"))
    return paths


def load_global_api_key():
    """Wczytuje serwerowy (globalny) klucz API z pliku lokalnego."""
    for path in get_possible_config_paths():
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    key = data.get("global_api_key", "").strip()
                    if key:
                        return key
            except Exception as e:
                print(f"Błąd odczytu {path}:", e)
    return ""


def save_global_api_key(key):
    """Zapisuje serwerowy (globalny) klucz API w pliku lokalnym z próbą wszystkich dostępnych ścieżek."""
    last_error = None
    for path in get_possible_config_paths():
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"global_api_key": key}, f, indent=2)
            print(f"Pomyślnie zapisano klucz globalny w: {path}")
            return True, None
        except Exception as e:
            last_error = str(e)
            print(f"Nie udało się zapisać w {path}:", e)
    return False, last_error


def get_request_credentials():
    """
    Pobiera klucz API oraz nazwę kanału z nagłówków żądania HTTP (lub parametrów URL).
    Jeśli użytkownik nie podał własnego klucza API, używa klucza globalnego zapisanego na serwerze.
    """
    api_key = request.headers.get("X-Api-Key") or request.args.get("api_key", "").strip()
    channel_handle = request.headers.get("X-Channel-Handle") or request.args.get("channel_handle", "").strip()

    # Jeśli brak własnego klucza użytkownika -> użyj klucza globalnego z serwera
    if not api_key:
        api_key = load_global_api_key()

    return api_key, channel_handle


def is_channel_allowed(channel_handle):
    """Sprawdza czy kanał znajduje się na liście dozwolonych kanałów (jeśli lista jest zdefiniowana)."""
    if not ALLOWED_CHANNELS:
        return True
    clean_req = channel_handle.lower().replace("@", "").strip()
    for item in ALLOWED_CHANNELS:
        clean_allowed = item["handle"].lower().replace("@", "").strip()
        if clean_req == clean_allowed:
            return True
    return False


@app.route("/")
def home():
    """Domyślna strona pod adresem głównym (z pliku default.html)."""
    return render_template("default.html")


@app.route("/youtube")
@app.route("/youtube/")
def youtube_app():
    """Aplikacja Koło Fortuny by Weekendowy Detektorysta dostępna pod adresem /youtube."""
    return render_template("index.html")


@app.route("/api/info", methods=["GET"])
@app.route("/youtube/api/info", methods=["GET"])
def info_endpoint():
    """Zwraca metadane aplikacji: wersję, status klucza globalnego i listę dozwolonych kanałów."""
    global_key = load_global_api_key()
    return jsonify({
        "version": APP_VERSION,
        "has_global_key": bool(global_key),
        "allowed_channels": ALLOWED_CHANNELS
    })


@app.route("/api/admin/set-global-key", methods=["POST"])
@app.route("/youtube/api/admin/set-global-key", methods=["POST"])
def set_global_key_endpoint():
    """Umożliwia ustawienie serwerowego klucza globalnego przez API."""
    data = request.get_json(silent=True) or {}
    key = data.get("global_api_key", "").strip() or request.form.get("global_api_key", "").strip()

    if not key:
        return jsonify({"error": "Brak wymaganego parametru 'global_api_key'."}), 400

    success, err_msg = save_global_api_key(key)
    if success:
        return jsonify({
            "success": True,
            "message": "Globalny klucz API został pomyślnie zapisany na serwerze."
        })
    else:
        return jsonify({"error": f"Nie udało się zapisać klucza na serwerze: {err_msg}"}), 500


@app.route("/api/videos", methods=["GET"])
@app.route("/youtube/api/videos", methods=["GET"])
def list_videos_endpoint():
    api_key, channel_handle = get_request_credentials()

    if not api_key:
        return jsonify({
            "error": "Brak klucza YouTube API. Serwer nie posiada skonfigurowanego klucza globalnego. Otwórz Ustawienia ⚙️ i wprowadź swój klucz API."
        }), 400

    if not channel_handle:
        return jsonify({"error": "Brak nazwy/ID kanału. Otwórz Ustawienia ⚙️ i wybierz lub wpisz nazwę kanału."}), 400

    if not is_channel_allowed(channel_handle):
        return jsonify({
            "error": f"Kanał '{channel_handle}' nie znajduje się na liście dozwolonych kanałów."
        }), 403

    try:
        data = youtube_service.get_channel_videos(api_key, channel_handle)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/comments", methods=["GET"])
@app.route("/youtube/api/comments", methods=["GET"])
def get_comments_endpoint():
    video_id = request.args.get("video_id", "").strip()
    if not video_id:
        return jsonify({"error": "Brak wymaganego parametru video_id."}), 400

    api_key, channel_handle = get_request_credentials()

    if not api_key:
        return jsonify({"error": "Brak klucza YouTube API."}), 400

    if not is_channel_allowed(channel_handle):
        return jsonify({"error": f"Kanał '{channel_handle}' nie znajduje się na liście dozwolonych kanałów."}), 403

    try:
        comments = youtube_service.get_video_comments(
            api_key=api_key,
            video_id=video_id,
            allowed_channel_handle_or_id=channel_handle
        )
        return jsonify({
            "video_id": video_id,
            "channel_handle": channel_handle,
            "total_comments": len(comments),
            "comments": comments
        })
    except PermissionError as pe:
        return jsonify({"error": str(pe)}), 403
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/export-csv", methods=["GET"])
@app.route("/youtube/api/export-csv", methods=["GET"])
def export_csv_endpoint():
    video_id = request.args.get("video_id", "").strip()
    if not video_id:
        return jsonify({"error": "Brak parametru video_id."}), 400

    api_key, channel_handle = get_request_credentials()

    try:
        comments = youtube_service.get_video_comments(
            api_key=api_key,
            video_id=video_id,
            allowed_channel_handle_or_id=channel_handle
        )

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=["Autor", "Komentarz", "Data"])
        writer.writeheader()
        for c in comments:
            writer.writerow({
                "Autor": c["author"],
                "Komentarz": c["comment"],
                "Data": c["date"]
            })

        csv_content = output.getvalue()
        output.close()

        return Response(
            csv_content,
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment; filename=komentarze-{video_id}.csv"}
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
