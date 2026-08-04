import csv
import io
import os
from flask import Flask, jsonify, render_template, request, Response
import youtube_service

app = Flask(__name__)


def get_request_credentials():
    """
    Pobiera klucz API oraz nazwę kanału z nagłówków żądania HTTP (lub parametrów URL),
    zapewniając bezstanowość i niezależność sesji każdego użytkownika.
    """
    api_key = request.headers.get("X-Api-Key") or request.args.get("api_key", "").strip()
    channel_handle = request.headers.get("X-Channel-Handle") or request.args.get("channel_handle", "").strip()
    return api_key, channel_handle


@app.route("/")
def home():
    """Domyślna strona pod adresem głównym (z pliku default.html)."""
    return render_template("default.html")


@app.route("/youtube")
@app.route("/youtube/")
def youtube_app():
    """Aplikacja YouTube Koło Fortuny dostępna pod adresem /youtube."""
    return render_template("index.html")


@app.route("/api/videos", methods=["GET"])
@app.route("/youtube/api/videos", methods=["GET"])
def list_videos_endpoint():
    api_key, channel_handle = get_request_credentials()

    if not api_key:
        return jsonify({"error": "Brak klucza YouTube API. Otwórz Ustawienia ⚙️ i wprowadź swój indywidualny klucz API."}), 400

    if not channel_handle:
        return jsonify({"error": "Brak nazwy/ID kanału. Otwórz Ustawienia ⚙️ i wpisz nazwę kanału (np. @UncjuszPatyniusz)."}), 400

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
        return jsonify({"error": "Brak klucza YouTube API. Otwórz Ustawienia ⚙️ i wprowadź swój klucz API."}), 400

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
