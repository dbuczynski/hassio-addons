import re
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


def get_youtube_client(api_key):
    """Tworzy klienta YouTube Data API v3."""
    return build("youtube", "v3", developerKey=api_key)


def resolve_channel_info(youtube, channel_input):
    """
    Znajduje szczegóły kanału na podstawie ID kanału, handle (@nazwa) lub wyszukiwania.
    Zwraca (channel_id, uploads_playlist_id, channel_title).
    """
    channel_input = channel_input.strip()
    ch = None

    # 1. Próba wyszukania po handle (np. @UncjuszPatyniusz)
    handle_to_try = channel_input if channel_input.startswith("@") else f"@{channel_input}"
    try:
        response = youtube.channels().list(
            part="snippet,contentDetails",
            forHandle=handle_to_try
        ).execute()
        items = response.get("items", [])
        if items:
            ch = items[0]
    except Exception:
        pass

    # 2. Próba bezpośrednia po ID kanału (zazwyczaj zaczyna się od UC)
    if not ch:
        try:
            response = youtube.channels().list(
                part="snippet,contentDetails",
                id=channel_input
            ).execute()
            items = response.get("items", [])
            if items:
                ch = items[0]
        except Exception:
            pass

    # 3. Próba poprzez wyszukiwanie kanału (fallback)
    if not ch:
        try:
            search_res = youtube.search().list(
                q=channel_input,
                type="channel",
                part="snippet",
                maxResults=1
            ).execute()
            items = search_res.get("items", [])
            if items:
                found_id = items[0]["snippet"]["channelId"]
                response = youtube.channels().list(
                    part="snippet,contentDetails",
                    id=found_id
                ).execute()
                if response.get("items"):
                    ch = response["items"][0]
        except Exception:
            pass

    if ch:
        channel_id = ch["id"]
        uploads_id = ch.get("contentDetails", {}).get("relatedPlaylists", {}).get("uploads")
        if not uploads_id and channel_id.startswith("UC"):
            uploads_id = f"UU{channel_id[2:]}"
        title = ch.get("snippet", {}).get("title", channel_input)
        return channel_id, uploads_id, title

    raise ValueError(f"Nie znaleziono kanału YouTube dla: {channel_input}")


def get_channel_videos(api_key, channel_handle_or_id, max_results=50):
    """
    Pobiera listę najnowszych filmów ze wskazanego kanału wraz z datą publikacji
    oraz ilością komentarzy pod każdym filmem.
    """
    if not api_key:
        raise ValueError("Brak klucza API YouTube.")

    youtube = get_youtube_client(api_key)
    channel_id, uploads_playlist_id, channel_title = resolve_channel_info(youtube, channel_handle_or_id)

    video_items = []
    next_page_token = None
    
    request = youtube.playlistItems().list(
        part="snippet,contentDetails",
        playlistId=uploads_playlist_id,
        maxResults=min(max_results, 50),
        pageToken=next_page_token
    )
    response = request.execute()
    
    for item in response.get("items", []):
        snippet = item.get("snippet", {})
        vid_id = item.get("contentDetails", {}).get("videoId") or snippet.get("resourceId", {}).get("videoId")
        if not vid_id:
            continue

        title = snippet.get("title", "")
        published_at = snippet.get("publishedAt", "")
        thumbnails = snippet.get("thumbnails", {})
        thumb_url = thumbnails.get("medium", {}).get("url") or thumbnails.get("default", {}).get("url", "")
        
        video_items.append({
            "id": vid_id,
            "title": title,
            "publishedAt": published_at,
            "thumbnail": thumb_url,
            "channelId": channel_id,
            "channelTitle": channel_title,
            "commentCount": 0
        })

    if not video_items:
        return {"channel_title": channel_title, "channel_id": channel_id, "videos": []}

    video_ids = [v["id"] for v in video_items]
    stats_response = youtube.videos().list(
        part="statistics",
        id=",".join(video_ids)
    ).execute()

    stats_map = {}
    for item in stats_response.get("items", []):
        v_id = item["id"]
        comment_count = int(item.get("statistics", {}).get("commentCount", 0))
        stats_map[v_id] = comment_count

    for v in video_items:
        v["commentCount"] = stats_map.get(v["id"], 0)

    return {
        "channel_title": channel_title,
        "channel_id": channel_id,
        "videos": video_items
    }


def get_video_comments(api_key, video_id, allowed_channel_handle_or_id=None):
    """
    Pobiera wszystkie komentarze spod wskazanego filmu.
    Jeśli podano allowed_channel_handle_or_id, weryfikuje czy film należy do tego kanału.
    """
    if not api_key:
        raise ValueError("Brak klucza API YouTube.")

    youtube = get_youtube_client(api_key)

    if allowed_channel_handle_or_id:
        allowed_channel_id, _, _ = resolve_channel_info(youtube, allowed_channel_handle_or_id)
        video_check = youtube.videos().list(
            part="snippet",
            id=video_id
        ).execute()

        items = video_check.get("items", [])
        if not items:
            raise ValueError(f"Nie odnaleziono filmu o ID: {video_id}")
        
        video_channel_id = items[0]["snippet"].get("channelId")
        if video_channel_id != allowed_channel_id:
            raise PermissionError("Wybór tego filmu jest niedozwolony (film nie należy do skonfigurowanego użytkownika).")

    comments = []
    next_page_token = None

    try:
        while True:
            request = youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=100,
                pageToken=next_page_token,
                textFormat="plainText"
            )
            response = request.execute()

            for item in response.get("items", []):
                snippet = item["snippet"]["topLevelComment"]["snippet"]
                author = snippet.get("authorDisplayName", "")
                comment_text = snippet.get("textDisplay", "")
                published_at = snippet.get("publishedAt", "")
                author_channel_url = snippet.get("authorChannelUrl", "")

                comments.append({
                    "author": author,
                    "comment": comment_text,
                    "date": published_at,
                    "authorChannelUrl": author_channel_url
                })

            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                break

    except HttpError as e:
        raise RuntimeError(f"Błąd YouTube API przy pobieraniu komentarzy: {e}")

    return comments
