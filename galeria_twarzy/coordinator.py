"""DataUpdateCoordinator for Galeria Twarzy."""
import logging
from datetime import timedelta, datetime

import aiohttp
from bs4 import BeautifulSoup
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.storage import Store

from .const import DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)
URL = "https://galeriatwarzy.pl/castingi"

class GaleriaTwarzyCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Galeria Twarzy data."""

    def __init__(self, hass: HomeAssistant):
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )
        self.last_castings_ids = []
        self._memory_cleared = False
        self.store = Store(hass, 1, "galeria_twarzy_castings")
        
    async def async_init(self):
        """Asynchronously load stored data before first refresh."""
        stored_data = await self.store.async_load()
        if stored_data and "last_castings_ids" in stored_data:
            self.last_castings_ids = stored_data["last_castings_ids"]

    async def clear_storage(self):
        """Service call handler to clear memory and storage."""
        try:
            self.last_castings_ids = []
            self._memory_cleared = True
            await self.store.async_save({"last_castings_ids": []})
            if self.data:
                # Copy dict to avoid MappingProxyType mutability crashes over strict HA versions
                new_data = dict(self.data)
                new_data["castings"] = []
                new_data["new_castings"] = []
                new_data["has_new"] = False
                new_data["telegram_status"] = "Wyczyszczono pamięć"
                self.async_set_updated_data(new_data)
            _LOGGER.warning("Galeria Twarzy: Hard memory storage flushed by service call.")
        except Exception as e:
            _LOGGER.error("Galeria Twarzy: clear_storage crashed: %s", e)
            raise
        
    async def async_send_test_telegram(self):
        """Send a test message to Telegram."""
        chat_id_state = self.hass.states.get("text.galeria_twarzy_telegram_chat_ids")
        config_id_state = self.hass.states.get("text.galeria_twarzy_telegram_config_id")
        
        telegram_status = self.data.get("telegram_status", "Oczekuje") if self.data else "Inicjalizacja"

        if chat_id_state and config_id_state:
            chat_ids_raw = chat_id_state.state
            config_id = config_id_state.state
            
            if chat_ids_raw and config_id and chat_ids_raw not in ("unknown", "unavailable", "") and config_id not in ("unknown", "unavailable", ""):
                chat_ids = [cid.strip() for cid in chat_ids_raw.split(',') if cid.strip()]
                
                sent_count = 0
                error_msg = ""
                msg = "🛠️ <b>Test powiadomień Galeria Twarzy</b>\nJeśli widzisz tę wiadomość, integracja działa prawidłowo i jest gotowa na nowe castingi!"
                
                for chat_id in chat_ids:
                    try:
                        await self.hass.services.async_call('telegram_bot', 'send_message', {
                            'chat_id': chat_id,
                            'config_entry_id': config_id,
                            'message': msg,
                            'parse_mode': 'html'
                        }, blocking=True)
                        sent_count += 1
                    except Exception as e:
                        error_msg = str(e)
                        _LOGGER.error("Failed to send test telegram message: %s", error_msg)
                
                if error_msg:
                    telegram_status = f"Błąd testu (Wysłano {sent_count}): {error_msg}"
                else:
                    telegram_status = f"Test wysłano do {sent_count} odbiorców ({dt_util.now().strftime('%H:%M:%S')})"
            else:
                telegram_status = "Błąd testu: Brak odbiorców/configu"
        else:
            telegram_status = "Błąd testu: Encje niedostępne"

        if self.data:
            new_data = dict(self.data)
            new_data["telegram_status"] = telegram_status
            self.async_set_updated_data(new_data)

    async def _async_update_data(self):
        """Fetch data from API."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(URL) as response:
                    response.raise_for_status()
                    html = await response.text()
                    
            soup = BeautifulSoup(html, 'html.parser')
            castings = []
            
            links = soup.find_all('a', class_='casting-link')
            for link in links:
                url = "https://galeriatwarzy.pl" + link.get('href') if link.get('href', '').startswith('/') else link.get('href')
                c_id = url.split('/')[-1] if url else ""
                
                box = link.find('div', class_='casting-box')
                if box:
                    title_tag = box.find('h6')
                    title = title_tag.get_text(strip=True) if title_tag else "Brak tytułu"
                    
                    loc_tag = box.find('div', class_='location')
                    location = loc_tag.find('p').get_text(strip=True) if loc_tag and loc_tag.find('p') else "Brak miejscowości"
                    
                    date_tag = box.find('div', class_='date')
                    day = date_tag.find('span', class_='day').get_text(strip=True) if date_tag and date_tag.find('span', class_='day') else ""
                    month = date_tag.find('strong', class_='month').get_text(strip=True) if date_tag and date_tag.find('strong', class_='month') else ""
                    year = date_tag.find('span', class_='year').get_text(strip=True) if date_tag and date_tag.find('span', class_='year') else ""
                    
                    full_date = f"{day} {month} {year}".strip()
                    
                    castings.append({
                        "id": c_id,
                        "title": title,
                        "location": location,
                        "date": full_date,
                        "url": url
                    })
            
            current_ids = [c['id'] for c in castings if c['id']]
            new_ids = [cid for cid in current_ids if cid not in self.last_castings_ids]
            
            # If this is not the very first initialization, check if we found any new casting.
            # If it is the first init, no new casting logic will be triggered.
            # However, if memory was cleared manually (_memory_cleared flag), treat all as new.
            if self._memory_cleared:
                has_new = len(new_ids) > 0
                self._memory_cleared = False  # reset flag after use
            elif self.last_castings_ids:
                has_new = len(new_ids) > 0
            else:
                has_new = False
                
            self.last_castings_ids = current_ids
            self.hass.async_create_task(self.store.async_save({"last_castings_ids": current_ids}))

            new_castings = [c for c in castings if c['id'] in new_ids]

            if self.data is None:
                telegram_status = "Inicjalizacja"
            else:
                telegram_status = self.data.get("telegram_status", "Oczekuje")
                if telegram_status == "Inicjalizacja":
                    telegram_status = "Czyszczenie/Brak nowych"

            if has_new:
                chat_id_state = self.hass.states.get("text.galeria_twarzy_telegram_chat_ids")
                config_id_state = self.hass.states.get("text.galeria_twarzy_telegram_config_id")
                
                if chat_id_state and config_id_state:
                    chat_ids_raw = chat_id_state.state
                    config_id = config_id_state.state
                    
                    if chat_ids_raw and config_id and chat_ids_raw not in ("unknown", "unavailable", "") and config_id not in ("unknown", "unavailable", ""):
                        chat_ids = [cid.strip() for cid in chat_ids_raw.split(',') if cid.strip()]
                        
                        sent_count = 0
                        error_msg = ""
                        
                        import html
                        
                        for casting in new_castings:
                            # Format explicitly for HTML parse_mode
                            safe_title = html.escape(casting.get('title', 'Brak tytułu'))
                            safe_loc = html.escape(casting.get('location', 'Brak'))
                            safe_date = html.escape(casting.get('date', 'Brak'))
                            safe_url = casting.get('url', '')
                            
                            msg = f"<b>{safe_title}</b>\n📍 Miejscowość: {safe_loc}\n🕒 Data: {safe_date}\n<a href=\"{safe_url}\">🔗 Link do castingu</a>"
                            
                            for chat_id in chat_ids:
                                try:
                                    await self.hass.services.async_call('telegram_bot', 'send_message', {
                                        'chat_id': chat_id,
                                        'config_entry_id': config_id,
                                        'message': msg,
                                        'parse_mode': 'html'
                                    }, blocking=True)
                                    sent_count += 1
                                except Exception as e:
                                    error_msg = str(e)
                                    _LOGGER.error("Failed to send telegram message: %s", error_msg)
                        
                        if error_msg:
                            telegram_status = f"Błąd (Wysłano {sent_count}): {error_msg}"
                        else:
                            telegram_status = f"Wysłano {sent_count} powiadomień ({dt_util.now().strftime('%H:%M:%S')})"
                    else:
                        telegram_status = "Pominięto (Brak skonfigurowanych odbiorców)"
                else:
                    telegram_status = "Pominięto (Encje konfiguracji niedostępne)"

            return {
                "castings": castings,
                "has_new": has_new,
                "new_castings": new_castings,
                "last_checked": dt_util.now(),
                "telegram_status": telegram_status
            }
            
        except Exception as err:
            raise UpdateFailed(f"Error scraping data: {err}")
