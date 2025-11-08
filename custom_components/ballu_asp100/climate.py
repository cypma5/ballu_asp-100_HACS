"""Climate platform for Ballu ASP-100."""
from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import HVACMode
from homeassistant.const import UnitOfTemperature

class BalluASP100Climate(ClimateEntity):
    """Representation of Ballu ASP-100 climate device."""

    def __init__(self, device_id, device_type, name):
        """Initialize the climate device."""
        self._device_id = device_id
        self._device_type = device_type
        self._attr_name = name
        self._attr_unique_id = f"ballu_asp100_{device_id}_climate"
        self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_hvac_mode = HVACMode.OFF
        self._attr_hvac_modes = [HVACMode.OFF, HVACMode.FAN_ONLY]

    @property
    def device_info(self):
        """Return device info."""
        return {
            "identifiers": {("ballu_asp100", self._device_id)},
            "name": self._attr_name,
            "manufacturer": "Ballu",
            "model": "ONEAIR ASP-100",
        }

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Ballu ASP-100 climate entity from config entry."""
    data = config_entry.data
    entity = BalluASP100Climate(
        data["device_id"],
        data["device_type"],
        data["name"]
    )
    async_add_entities([entity])