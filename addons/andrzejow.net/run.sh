#!/usr/bin/env bash

# Tworzenie trwałego katalogu konfiguracji jeśli istnieje /config (w HA)
CONFIG_DIR="/config/youtube_kolo_fortuny"
if [ -d "/config" ]; then
    mkdir -p "$CONFIG_DIR"
    export CONFIG_PATH="$CONFIG_DIR/config.json"
else
    export CONFIG_PATH="/app/config.json"
fi

# Synchroniczny odczyt opcji z Home Assistant (/data/options.json) jeśli plik istnieje
if [ -f "/data/options.json" ]; then
    echo "Wczytywanie opcji z Home Assistant (/data/options.json)..."
    API_KEY=$(jq --raw-output '.api_key // ""' /data/options.json)
    CHANNEL_HANDLE=$(jq --raw-output '.channel_handle // ""' /data/options.json)
    TARGET_USERS=$(jq -c '.target_users // []' /data/options.json)

    if [ ! -f "$CONFIG_PATH" ] || [ "$API_KEY" != "" ]; then
        echo "Updating config at $CONFIG_PATH..."
        jq -n \
            --arg api_key "$API_KEY" \
            --arg channel_handle "$CHANNEL_HANDLE" \
            --argjson target_users "$TARGET_USERS" \
            '{api_key: $api_key, channel_handle: $channel_handle, target_users: $target_users}' > "$CONFIG_PATH"
    fi
fi

echo "Rozpoczynam serwer WWW YouTube Koło Fortuny Online na porcie 8080..."
cd /app
exec python3 -u app.py
