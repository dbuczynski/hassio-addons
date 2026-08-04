import csv
import io
import json
import os
from flask import Flask, jsonify, render_template, request, Response
import youtube_service

app = Flask(__name__)

CONFIG_PATH = os.environ.get("CONFIG_PATH", os.path.join(os.path.dirname(__file__), "config.json"))


def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Błąd odczytu {CONFIG_PATH}: {e}")
    
    return {
        "api_key": "",
        "channel_handle": "",
        "target_users": []
    }


def save_config(config_data):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config_data, f, ensure_ascii=False, indent=2)


@app.route("/")
def home():
    """Domyślna strona pod adresem głównym (z pliku default.html)."""
    return render_template("default.html")


@app.route("/youtube")
@app.route("/youtube/")
def youtube_app():
    """Aplikacja YouTube Koło Fortuny dostępna pod adresem /youtube."""
    return render_template("index.html")


@app.route("/api/config", methods=["GET"])
@app.route("/youtube/api/config", methods=["GET"])
def get_config_endpoint():
    config = load_config()
    masked_key = ""
    if config.get("api_key"):
        key = config["api_key"]
        masked_key = key[:4] + "*" * (len(key) - 8) + key[-4:] if len(key) > 8 else "****"

    return jsonify({
        "channel_handle": config.get("channel_handle", ""),
        "target_users": config.get("target_users", []),
        "is_api_key_set": bool(config.get("api_key")),
        "masked_api_key": masked_key
    })


@app.route("/api/config", methods=["POST"])
@app.route("/youtube/api/config", methods=["POST"])
def update_config_endpoint():
    data = request.json or {}
    config = load_config()

    new_api_key = data.get("api_key", "").strip()
    if new_api_key and "*" not in new_api_key:
        config["api_key"] = new_api_key

    if "channel_handle" in data:
        config["channel_handle"] = data["channel_handle"].strip()

    if "target_users" in data:
        raw_targets = data["target_users"]
        if isinstance(raw_targets, str):
            targets = [t.strip() for t in raw_targets.split(",") if t.strip()]
        elif isinstance(raw_targets, list):
            targets = [str(t).strip() for t in raw_targets if str(t).strip()]
        else:
            targets = []
        config["target_users"] = targets

    save_config(config)
    return jsonify({"success": True, "message": "Konfiguracja została pomyślnie zapisana."})


@app.route("/api/videos", methods=["GET"])
@app.route("/youtube/api/videos", methods=["GET"])
def list_videos_endpoint():
    config = load_config()
    api_key = config.get("api_key")
    channel_handle = config.get("channel_handle")

    if not api_key:
        return jsonify({"error": "Brak skonfigurowanego klucza YouTube API. Przejdź do ustawień i wprowadź klucz."}), 400

    if not channel_handle:
        return jsonify({"error": "Brak skonfigurowanej nazwy/ID kanału w ustawieniach."}), 400

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

    config = load_config()
    api_key = config.get("api_key")
    channel_handle = config.get("channel_handle")

    if not api_key:
        return jsonify({"error": "Brak skonfigurowanego klucza YouTube API."}), 400

    try:
        comments = youtube_service.get_video_comments(
            api_key=api_key,
            video_id=video_id,
            allowed_channel_handle_or_id=channel_handle
        )
        return jsonify({
            "video_id": video_id,
            "target_users": config.get("target_users", []),
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

    config = load_config()
    api_key = config.get("api_key")
    channel_handle = config.get("channel_handle")

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
