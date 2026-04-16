#!/usr/bin/env bash

# Wczytanie konfiguracji z okablowania Home Assistant Add-ons
POWER_SENSOR=$(jq --raw-output '.power_sensor' /data/options.json)
CHEAP_SENSOR=$(jq --raw-output '.cheapest_sensor' /data/options.json)
EXP_SENSOR=$(jq --raw-output '.expensive_sensor' /data/options.json)

export POWER_SENSOR
export CHEAP_SENSOR
export EXP_SENSOR

# Upewnienie się że katalog docelowy istnieje
mkdir -p /config/www/pstryk_chart_generator

echo "Rozpoczynam serwis Pstryk Chart Generator..."
echo "Power Sensor: $POWER_SENSOR"

# Uruchomienie skryptu głównego
python3 -u /generator.py
