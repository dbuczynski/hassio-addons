"""The Galeria Twarzy integration."""
import logging
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN
from .coordinator import GaleriaTwarzyCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.BUTTON, Platform.TEXT]

CLEAR_MEMORY_SCHEMA = vol.Schema({
    vol.Required("flushstoreddata"): cv.boolean
})

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Galeria Twarzy from a config entry."""
    session = async_get_clientsession(hass)
    coordinator = GaleriaTwarzyCoordinator(hass)
    
    await coordinator.async_init()

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    async def handle_clear_memory(call: ServiceCall):
        if call.data.get("flushstoreddata"):
            await coordinator.clear_storage()

    hass.services.async_register(
        DOMAIN, "clear_memory", handle_clear_memory, schema=CLEAR_MEMORY_SCHEMA
    )

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
