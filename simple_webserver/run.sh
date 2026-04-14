#!/bin/bash

echo "Starting Simple Web Server..."

CONFIG_PATH=/data/options.json
DOCUMENT_ROOT=$(jq --raw-output '.document_root' $CONFIG_PATH)

echo "Configured document_root is: $DOCUMENT_ROOT"

# Ensure the document root directory actually exists before linking
if [ ! -d "$DOCUMENT_ROOT" ]; then
    echo "Warning: Directory $DOCUMENT_ROOT does not exist! Creating it..."
    mkdir -p "$DOCUMENT_ROOT"
fi

# Remove default html dir if exists and link to document root
rm -rf /var/www/html
ln -s "$DOCUMENT_ROOT" /var/www/html

echo "Symlink created. Starting Apache..."

# Execute the default apache CMD
exec apache2-foreground
