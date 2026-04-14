"""Binary sensor platform for Galeria Twarzy."""
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import GaleriaTwarzyCoordinator

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the binary sensor platform."""
    coordinator: GaleriaTwarzyCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([GaleriaTwarzyNewCastingBinarySensor(coordinator)])


class GaleriaTwarzyNewCastingBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor that indicates if a new casting was found."""

    def __init__(self, coordinator: GaleriaTwarzyCoordinator):
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._attr_name = "Galeria Twarzy New Casting Alert"
        self._attr_unique_id = "galeria_twarzy_new_casting_alert"
        self._attr_icon = "mdi:bell-ring"
        
    @property
    def name(self):
        """Return the name of the binary sensor."""
        return self._attr_name
        
    @property
    def unique_id(self):
        return self._attr_unique_id

    @property
    def is_on(self):
        """Return true if there's a new casting since last check."""
        # Coordinator has_new will be False if the current poll hasn't found new distinct ids.
        # It guarantees the sensor will return to OFF if no new casting popped up in the last hour.
        return self.coordinator.data.get("has_new", False)

