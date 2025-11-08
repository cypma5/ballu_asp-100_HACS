"""Select platform for Ballu ASP-100."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.components import mqtt
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, SOUND_MAPPING

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Ballu ASP-100 select from config entry."""
    data = config_entry.data
    
    select_entity = BalluASP100Select(
        hass,
        data["device_id"],
        data["device_type"],
        data["name"],
        config_entry.entry_id,
    )
    
    async_add_entities([select_entity])

class BalluASP100Select(SelectEntity):
    """Representation of Ballu ASP-100 sounds select."""

    def __init__(
        self,
        hass: HomeAssistant,
        device_id: str,
        device_type: str,
        device_name: str,
        entry_id: str,
    ) -> None:
        """Initialize the select."""
        self.hass = hass
        self._device_id = device_id
        self._device_type = device_type
        self._device_name = device_name
        self._entry_id = entry_id
        
        self._attr_name = "Sounds"
        self._attr_unique_id = f"ballu_asp100_{device_id}_sounds"
        self._attr_icon = "mdi:music"
        self._attr_options = list(SOUND_MAPPING.keys())
        self._attr_entity_registry_enabled_default = False
        
        self._current_option = "Выключено"
        self._command_topic_base = f"rusclimate/{device_type}/{device_id}/control"
        self._state_topic_base = f"rusclimate/{device_type}/{device_id}/state"

    @property
    def device_info(self):
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._device_id)},
            "name": self._device_name,
            "manufacturer": "Ballu",
            "model": "ONEAIR ASP-100",
        }

    @property
    def current_option(self) -> str:
        """Return the selected option."""
        return self._current_option

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        topic = f"{self._command_topic_base}/amount"
        sound_value = SOUND_MAPPING.get(option, 0)
        
        await mqtt.async_publish(
            self.hass,
            topic,
            str(sound_value),
            qos=1,
            retain=False,
        )
        self._current_option = option
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Subscribe to MQTT topics when entity is added to hass."""
        topic = f"{self._state_topic_base}/amount"
        
        await mqtt.async_subscribe(
            self.hass,
            topic,
            self._message_received,
        )

    def _message_received(self, message):
        """Handle new MQTT messages."""
        try:
            sound_value = int(message.payload)
            for option, value in SOUND_MAPPING.items():
                if value == sound_value:
                    self._current_option = option
                    break
            self.async_write_ha_state()
        except (ValueError, KeyError) as err:
            _LOGGER.error("Error processing message for %s: %s", self.name, err)