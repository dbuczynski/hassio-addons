"""Sensor platform for Galeria Twarzy."""
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import GaleriaTwarzyCoordinator

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the sensor platform."""
    coordinator: GaleriaTwarzyCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([
        GaleriaTwarzyLastSeenSensor(coordinator),
        GaleriaTwarzyDetailsSensor(coordinator),
        GaleriaTwarzyLastCheckSensor(coordinator),
        GaleriaTwarzyTelegramStatusSensor(coordinator)
    ])


class GaleriaTwarzyLastSeenSensor(CoordinatorEntity, SensorEntity):
    """Sensor that reports total number of seen castings and details as attributes."""

    def __init__(self, coordinator: GaleriaTwarzyCoordinator):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "Galeria Twarzy All Castings"
        self._attr_unique_id = "galeria_twarzy_all_castings"
        self._attr_icon = "mdi:format-list-bulleted"

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._attr_name
        
    @property
    def unique_id(self):
        return self._attr_unique_id

    @property
    def native_value(self):
        """Return the state of the sensor (count of castings)."""
        castings = self.coordinator.data.get("castings", [])
        return len(castings)

    @property
    def extra_state_attributes(self):
        """Return entity specific state attributes."""
        return {
            "castings": self.coordinator.data.get("castings", [])
        }


class GaleriaTwarzyDetailsSensor(CoordinatorEntity, SensorEntity):
    """Sensor that reports details of all new castings from last poll."""

    def __init__(self, coordinator: GaleriaTwarzyCoordinator):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "Galeria Twarzy Ostatnio Dodane Castingi"
        self._attr_unique_id = "galeria_twarzy_nowe_castingi"
        self._attr_icon = "mdi:new-box"

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._attr_name
        
    @property
    def unique_id(self):
        return self._attr_unique_id

    @property
    def native_value(self):
        """Return the state of the sensor (Count of new castings)."""
        new_castings = self.coordinator.data.get("new_castings", [])
        return len(new_castings)

    @property
    def extra_state_attributes(self):
        """Return entity specific state attributes."""
        return {
            "castings": self.coordinator.data.get("new_castings", [])
        }


class GaleriaTwarzyLastCheckSensor(CoordinatorEntity, SensorEntity):
    """Sensor that reports when the last check was performed."""

    def __init__(self, coordinator: GaleriaTwarzyCoordinator):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "Galeria Twarzy Ostatnie Sprawdzenie"
        self._attr_unique_id = "galeria_twarzy_ostatnie_sprawdzenie"
        self._attr_device_class = SensorDeviceClass.TIMESTAMP
        self._attr_icon = "mdi:clock-check-outline"

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._attr_name
        
    @property
    def unique_id(self):
        return self._attr_unique_id

    @property
    def native_value(self):
        """Return the state of the sensor (last check timestamp)."""
        return self.coordinator.data.get("last_checked")


class GaleriaTwarzyTelegramStatusSensor(CoordinatorEntity, SensorEntity):
    """Sensor that reports when the last telegram notification was sent and its status."""

    def __init__(self, coordinator: GaleriaTwarzyCoordinator):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "Galeria Twarzy Status Notyfikacji"
        self._attr_unique_id = "galeria_twarzy_telegram_status"
        self._attr_icon = "mdi:message-badge"

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._attr_name
        
    @property
    def unique_id(self):
        return self._attr_unique_id

    @property
    def native_value(self):
        """Return the state of the sensor (last telegram notification status)."""
        # Trimming just to make sure UI is not too bloated, but typically it fits.
        val = self.coordinator.data.get("telegram_status", "Oczekuje")
        return val[:255]

