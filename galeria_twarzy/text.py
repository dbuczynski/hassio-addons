"""Text platform for Galeria Twarzy."""
from homeassistant.components.text import TextEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN
from .coordinator import GaleriaTwarzyCoordinator

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the text platform."""
    coordinator: GaleriaTwarzyCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([
        GaleriaTwarzyTelegramChatId(coordinator),
        GaleriaTwarzyTelegramConfigId(coordinator)
    ])


class GaleriaTwarzyTelegramChatId(TextEntity, RestoreEntity):
    """Text entity for Telegram Chat IDs (comma separated)."""

    def __init__(self, coordinator: GaleriaTwarzyCoordinator):
        """Initialize the entity."""
        self.coordinator = coordinator
        self._attr_name = "Galeria Twarzy Telegram Chat IDs"
        self._attr_unique_id = "galeria_twarzy_telegram_chat_ids"
        self._attr_icon = "mdi:account-multiple"
        self._attr_native_value = ""

    @property
    def name(self):
        return self._attr_name
        
    @property
    def unique_id(self):
        return self._attr_unique_id

    async def async_added_to_hass(self) -> None:
        """Handle entity which will be added."""
        await super().async_added_to_hass()
        if (state := await self.async_get_last_state()) is not None:
            if state.state not in (None, "unknown", "unavailable"):
                self._attr_native_value = state.state

    async def async_set_value(self, value: str) -> None:
        """Update the value."""
        self._attr_native_value = value
        self.async_write_ha_state()


class GaleriaTwarzyTelegramConfigId(TextEntity, RestoreEntity):
    """Text entity for Telegram Config Entry ID."""

    def __init__(self, coordinator: GaleriaTwarzyCoordinator):
        """Initialize the entity."""
        self.coordinator = coordinator
        self._attr_name = "Galeria Twarzy Telegram Config ID"
        self._attr_unique_id = "galeria_twarzy_telegram_config_id"
        self._attr_icon = "mdi:identifier"
        self._attr_native_value = ""

    @property
    def name(self):
        return self._attr_name
        
    @property
    def unique_id(self):
        return self._attr_unique_id

    async def async_added_to_hass(self) -> None:
        """Handle entity which will be added."""
        await super().async_added_to_hass()
        if (state := await self.async_get_last_state()) is not None:
            if state.state not in (None, "unknown", "unavailable"):
                self._attr_native_value = state.state

    async def async_set_value(self, value: str) -> None:
        """Update the value."""
        self._attr_native_value = value
        self.async_write_ha_state()
