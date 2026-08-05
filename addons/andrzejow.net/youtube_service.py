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


def get_channel_profile_details(api_key, channel_handle="@UncjuszPatyniusz"):
    """
    Pobiera pełne metadane profilu kanału YouTube (banner, avatar, opis, statystyki).
    """
    if not api_key:
        return {
            "title": "Uncjusz Patyniusz",
            "handle": channel_handle,
            "description": "Jest to kanał który ma na celu popularyzację numizmatyki, poszerzanie wiedzy kolekcjonerskiej...",
            "subscribers": "8,67 tys. subskrybentów",
            "video_count": "297 filmów",
            "avatar_url": "",
            "banner_url": ""
        }

    try:
        youtube = get_youtube_client(api_key)
        handle_to_try = channel_handle if channel_handle.startswith("@") else f"@{channel_handle}"
        
        response = youtube.channels().list(
            part="snippet,brandingSettings,statistics",
            forHandle=handle_to_try
        ).execute()

        items = response.get("items", [])
        if not items:
            # Fallback po zapytaniu search
            channel_id, _, _ = resolve_channel_info(youtube, channel_handle)
            response = youtube.channels().list(
                part="snippet,brandingSettings,statistics",
                id=channel_id
            ).execute()
            items = response.get("items", [])

        if items:
            ch = items[0]
            snippet = ch.get("snippet", {})
            branding = ch.get("brandingSettings", {}).get("image", {})
            stats = ch.get("statistics", {})

            title = snippet.get("title", channel_handle)
            handle = snippet.get("customUrl") or channel_handle
            if not handle.startswith("@"):
                handle = "@" + handle

            desc = snippet.get("description", "")
            
            thumbnails = snippet.get("thumbnails", {})
            avatar_url = thumbnails.get("high", {}).get("url") or thumbnails.get("medium", {}).get("url") or thumbnails.get("default", {}).get("url", "")
            
            banner_url = branding.get("bannerExternalUrl", "")
            if banner_url:
                banner_url += "=w1707-fcrop64=1,00005a57ffffa5a8-k-c0xffffffff-no-nd-rj"

            raw_subs = int(stats.get("subscriberCount", 0))
            if raw_subs >= 1000000:
                subs_str = f"{raw_subs / 1000000:.2f} mln subskrybentów".replace(".", ",")
            elif raw_subs >= 1000:
                subs_str = f"{raw_subs / 1000:.2f} tys. subskrybentów".replace(".", ",")
            else:
                subs_str = f"{raw_subs} subskrybentów"

            video_count_str = f"{stats.get('videoCount', '0')} filmów"

            return {
                "title": title,
                "handle": handle,
                "description": desc,
                "subscribers": subs_str,
                "video_count": video_count_str,
                "avatar_url": avatar_url,
                "banner_url": banner_url
            }
    except Exception as e:
        print(f"Błąd pobierania profilu kanału {channel_handle}: {e}", flush=True)

    return {
        "title": channel_handle.replace("@", ""),
        "handle": channel_handle,
        "description": "Kanał YouTube",
        "subscribers": "Subskrybenci YouTube",
        "video_count": "Filmy YouTube",
        "avatar_url": "",
        "banner_url": ""
    }


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
    Klasyfikuje film na: 'live' (transmisja na żywo - aktualna, zaplanowana lub archiwalny zapis streamu),
    'short' (Shorts <= 60s), 'video' (zwykły film / opublikowana premiera).
    """
    snippet = item.get("snippet", {})
    content_details = item.get("contentDetails", {})
    live_details = item.get("liveStreamingDetails")
    
    live_broadcast = snippet.get("liveBroadcastContent", "none")
    title = snippet.get("title", "").lower()

    # 1. Jeżeli występuje liveStreamingDetails lub status transmisji - jest to transmisja na żywo
    if live_details is not None or live_broadcast in ["live", "upcoming", "completed"]:
        return "live"

    # 2. Shorts (krótkie pionowe filmy <= 60s lub #shorts w tytule)
    duration_str = content_details.get("duration", "")
    duration_sec = parse_iso8601_duration(duration_str)
    
    if (0 < duration_sec <= 60) or "#shorts" in title:
        return "short"

    # 3. Standardowy film
    return "video"


def get_channel_videos(api_key, channel_handle_or_id=None, channel_handle=None, max_results=200):
    """
    Pobiera listę najnowszych filmów ze wskazanego kanału (co najmniej 200 pozycji)
    wraz z datą publikacji, klasyfikacją typu (video, short, live) oraz ilością komentarzy.
    """
    target_handle = channel_handle or channel_handle_or_id or "@UncjuszPatyniusz"
    if not api_key:
        raise ValueError("Brak klucza API YouTube.")

    youtube = get_youtube_client(api_key)
    channel_id, uploads_playlist_id, channel_title = resolve_channel_info(youtube, target_handle)

    video_items = []
    next_page_token = None
    
    while len(video_items) < max_results:
        pageSize = min(50, max_results - len(video_items))
        request = youtube.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=uploads_playlist_id,
            maxResults=pageSize,
            pageToken=next_page_token
        )
        response = request.execute()
        
        items = response.get("items", [])
        if not items:
            break

        for item in items:
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

        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break

    if not video_items:
        return {"channel_title": channel_title, "channel_id": channel_id, "videos": []}

    video_ids = [v["id"] for v in video_items]
    details_map = {}

    for i in range(0, len(video_ids), 50):
        chunk_ids = video_ids[i:i+50]
        details_response = youtube.videos().list(
            part="snippet,statistics,contentDetails,liveStreamingDetails",
            id=",".join(chunk_ids)
        ).execute()

        for item in details_response.get("items", []):
            v_id = item["id"]
            comment_count = int(item.get("statistics", {}).get("commentCount", 0))
            v_type = classify_video_type(item)
            
            snippet = item.get("snippet", {})
            real_title = snippet.get("title", "")
            real_published_at = snippet.get("publishedAt", "")

            details_map[v_id] = {
                "commentCount": comment_count,
                "videoType": v_type,
                "realTitle": real_title,
                "realPublishedAt": real_published_at
            }

    for v in video_items:
        info = details_map.get(v["id"], {})
        v["commentCount"] = info.get("commentCount", 0)
        v["videoType"] = info.get("videoType", "video")
        if info.get("realTitle"):
            v["title"] = info["realTitle"]
        if info.get("realPublishedAt"):
            v["publishedAt"] = info["realPublishedAt"]

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
