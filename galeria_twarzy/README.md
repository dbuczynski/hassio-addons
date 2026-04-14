# Galeria Twarzy - Home Assistant Custom Component

A custom component for Home Assistant to scrape and monitor new casting opportunities from [Galeria Twarzy](https://galeriatwarzy.pl/castingi). 

This integration actively extracts casting data directly from the website, stores history persistently across reboots, and provides natively styled dashboard entities. It also comes equipped with an internal, robust Telegram notification engine that alerts you instantly of any new castings.

## Features

- **Automated Web Scraping:** Checks for new casting updates periodically (default: 1 hour).
- **Persistent Storage:** Memorizes seen castings so duplicate notifications are completely suppressed, even after Home Assistant restarts.
- **Native Telegram Integration:** Sends beautiful, HTML-formatted messages with casting titles, locations, dates, and direct links without needing complex separate HA Automations.
- **Developer & Control Buttons:** 
  - **Force Refresh:** Checks the website on-demand.
  - **Clear Memory:** Dev functionality to wipe the internal integration database to test triggers locally.
  - **Test Notification:** Safely evaluate your Telegram Bot connectivity.
- **Advanced Dashboard:** Included `dashboard.yaml` code snippet providing a complete and beautiful Lovelace layout (including a dynamic CSS analog clock).

## Installation

### Manual Installation

1. Using your tool of choice, open your Home Assistant configuration directory (where `configuration.yaml` is located).
2. Look for a folder named `custom_components` in the root space. If it doesn't exist, create it.
3. Inside the `custom_components` directory, create a new folder called `galeria_twarzy`.
4. Copy all Python and JSON files (`__init__.py`, `manifest.json`, `sensor.py`, etc.) from this repository into the newly created `galeria_twarzy` folder.
5. Restart Home Assistant.
6. In the Home Assistant UI, go to **Settings > Devices & Services > Integrations**.
7. Click **+ Add Integration** and search for `Galeria Twarzy`.

## Configuration

This integration uses UI configuration for easy interaction:

1. Add the integration from the UI. It will initialize the core services and sensors.
2. Edit your Lovelace Dashboard and copy-paste the contents of the provided `dashboard.yaml` into a Manual Card or as a raw dashboard view configuration.
3. Once the dashboard layout is visible, use the text input boxes exposed by the integration directly in the UI to configure Telegram:
   - **(Opcj.) Telegram Config ID**: Provide the config entry ID of your generic Telegram Bot integration. *(Optional if you don't use Telegram)*
   - **(Opcj.) Telegram Odbiorcy**: Provide a comma-separated list of Chat ID numbers that should receive new casting alerts (e.g., `123456789, 987654321`).
4. Hit the **"Wyślij test na Telegram"** (Send Telegram Test) button to confirm that everything is working. 

## Included Entities

- `sensor.galeria_twarzy_all_castings`: Displays the total number of downloaded castings. (All casting data is available in the entity attributes).
- `sensor.galeria_twarzy_ostatnio_dodane_castingi`: The number of new castings discovered in the last check loop.
- `sensor.galeria_twarzy_ostatnie_sprawdzenie`: Timestamp denoting the exact time of the last web scrape.
- `sensor.galeria_twarzy_status_notyfikacji`: Diagnostic string keeping track of Telegram dispatch success.
- `binary_sensor.galeria_twarzy_new_casting_alert`: A binary sensor that stays `ON` during the update run if new castings were found.
- `button.galeria_twarzy_wymus_sprawdzenie`: Actionable button to poll the website immediately.
- `button.galeria_twarzy_kasuj_pamiec`: Resets the underlying JSON storage and memory list for debugging.
- `button.galeria_twarzy_test_telegram`: Instructs the bot to send a hard-coded test mechanism.
- `text.galeria_twarzy_telegram_config_id`: Live configuration variable component.
- `text.galeria_twarzy_telegram_chat_ids`: Live configuration variable component for recipients.

---

> **Note:** This integration relies on web scraping utilizing BeautifulSoup4. If the HTML structure of the *Galeria Twarzy* website changes in the future, the scraping logic in `coordinator.py` may need to be updated.
