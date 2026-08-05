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


def parse_iso8601_duration(duration_str):
    """Przekształca czas ISO 8601 (np. PT1M30S, PT45S) na sekundowe wartości numeryczne."""
    if not duration_str:
        return 0
    pattern = re.compile(r'PT(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?')
    match = pattern.match(duration_str)
    if not match:
        return 0
    parts = match.groupdict()
    hours = int(parts['hours'] or 0)
    minutes = int(parts['minutes'] or 0)
    seconds = int(parts['seconds'] or 0)
    return hours * 3600 + minutes * 60 + seconds


def classify_video_type(item):
    """
    Klasyfikuje film na: 'live' (transmisja na żywo - aktualna, zaplanowana lub archiwalny zapis live),
    'short' (Shorts <= 60s), 'video' (zwykły film / opublikowana premiera).
    """
    snippet = item.get("snippet", {})
    content_details = item.get("contentDetails", {})
    live_details = item.get("liveStreamingDetails")
    
    live_broadcast = snippet.get("liveBroadcastContent", "none")
    title = snippet.get("title", "").lower()

    # 1. Trwająca lub zaplanowana transmisja na żywo
    if live_broadcast in ["live", "upcoming"]:
        return "live"

    # 2. Archiwalna transmisja na żywo (posiada liveStreamingDetails oraz słowo kluczowe w tytule lub aktywny czat)
    if live_details:
        has_live_keyword = any(kw in title for kw in ["live", "stream", "transmisja", "na żywo", "na zywo"])
        has_chat = bool(live_details.get("activeLiveChatId"))
        if has_live_keyword or has_chat:
            return "live"

    # 3. Shorts (krótkie pionowe filmy <= 60s lub #shorts w tytule)
    duration_str = content_details.get("duration", "")
    duration_sec = parse_iso8601_duration(duration_str)
    
    if (0 < duration_sec <= 60) or "#shorts" in title:
        return "short"

    # 4. Standardowy film (w tym zakończona premiera)
    return "video"


def get_channel_videos(api_key, channel_handle_or_id=None, channel_handle=None, max_results=50):
    """
    Pobiera listę najnowszych filmów ze wskazanego kanału wraz z datą publikacji,
    klasyfikacją typu (video, short, live) oraz ilością komentarzy pod każdym filmem.
    """
    target_handle = channel_handle or channel_handle_or_id or "@UncjuszPatyniusz"
    if not api_key:
        raise ValueError("Brak klucza API YouTube.")

    youtube = get_youtube_client(api_key)
    channel_id, uploads_playlist_id, channel_title = resolve_channel_info(youtube, target_handle)

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
            "commentCount": 0,
            "videoType": "video"
        })

    if not video_items:
        return {"channel_title": channel_title, "channel_id": channel_id, "videos": []}

    video_ids = [v["id"] for v in video_items]
    details_response = youtube.videos().list(
        part="snippet,statistics,contentDetails,liveStreamingDetails",
        id=",".join(video_ids)
    ).execute()

    details_map = {}
    for item in details_response.get("items", []):
        v_id = item["id"]
        comment_count = int(item.get("statistics", {}).get("commentCount", 0))
        v_type = classify_video_type(item)
        details_map[v_id] = {
            "commentCount": comment_count,
            "videoType": v_type
        }

    for v in video_items:
        info = details_map.get(v["id"], {"commentCount": 0, "videoType": "video"})
        v["commentCount"] = info["commentCount"]
        v["videoType"] = info["videoType"]

    return {
        "channel_title": channel_title,
        "channel_id": channel_id,
        "videos": video_items
    }


def get_all_comments_for_video(api_key, video_id):
    """
    Pobiera wszystkie komentarze (top-level) z danego filmu na YouTube.
    Zwraca listę słowników: [{"author": "...", "comment": "...", "date": "..."}, ...]
    """
    if not api_key:
        raise ValueError("Brak klucza API YouTube.")

    youtube = get_youtube_client(api_key)
    comments = []
    next_page_token = None

    while True:
        try:
            req = youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=100,
                pageToken=next_page_token,
                textFormat="plainText"
            )
            res = req.execute()

            for item in res.get("items", []):
                snippet = item["snippet"]["topLevelComment"]["snippet"]
                author = snippet.get("authorDisplayName", "Anonim")
                text = snippet.get("textDisplay", "")
                pub_at = snippet.get("publishedAt", "")

                comments.append({
                    "author": author,
                    "comment": text,
                    "date": pub_at
                })

            next_page_token = res.get("nextPageToken")
            if not next_page_token:
                break
        except HttpError as err:
            if "commentsDisabled" in str(err):
                raise ValueError("Komentarze pod tym filmem zostały wyłączone.")
            raise err

    return comments
