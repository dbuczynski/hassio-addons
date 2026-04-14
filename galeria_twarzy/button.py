"""Button platform for Galeria Twarzy."""
from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import GaleriaTwarzyCoordinator

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the button platform."""
    coordinator: GaleriaTwarzyCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([
        GaleriaTwarzyRefreshButton(coordinator),
        GaleriaTwarzyDevResetButton(coordinator),
        GaleriaTwarzyTestTelegramButton(coordinator)
    ])


class GaleriaTwarzyRefreshButton(CoordinatorEntity, ButtonEntity):
    """Button to force refresh Galeria Twarzy castings."""

    def __init__(self, coordinator: GaleriaTwarzyCoordinator):
        """Initialize the button."""
        super().__init__(coordinator)
        self._attr_name = "Galeria Twarzy Wymuś Sprawdzenie"
        self._attr_unique_id = "galeria_twarzy_wymus_sprawdzenie"
        self._attr_icon = "mdi:account-search"

    @property
    def name(self):
        """Return the name of the button."""
        return self._attr_name
        
    @property
    def unique_id(self):
        return self._attr_unique_id

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.coordinator.async_request_refresh()

class GaleriaTwarzyDevResetButton(CoordinatorEntity, ButtonEntity):
    """Button to clear storage and memory for dev purposes."""

    def __init__(self, coordinator: GaleriaTwarzyCoordinator):
        """Initialize the button."""
        super().__init__(coordinator)
        self._attr_name = "Galeria Twarzy Kasuj Pamiec"
        self._attr_unique_id = "galeria_twarzy_kasuj_pamiec"
        self._attr_icon = "mdi:delete-alert"

    @property
    def name(self):
        """Return the name of the button."""
        return self._attr_name
        
    @property
    def unique_id(self):
        return self._attr_unique_id

    async def async_press(self) -> None:
        """Handle the action."""
        await self.coordinator.clear_storage()

class GaleriaTwarzyTestTelegramButton(CoordinatorEntity, ButtonEntity):
    """Button to test Telegram notifications."""

    def __init__(self, coordinator: GaleriaTwarzyCoordinator):
        """Initialize the button."""
        super().__init__(coordinator)
        self._attr_name = "Galeria Twarzy Test Notyfikacji"
        self._attr_unique_id = "galeria_twarzy_test_telegram"
        self._attr_icon = "mdi:message-fast-outline"

    @property
    def name(self):
        """Return the name of the button."""
        return self._attr_name
        
    @property
    def unique_id(self):
        return self._attr_unique_id

    async def async_press(self) -> None:
        """Handle the action."""
        await self.coordinator.async_send_test_telegram()
