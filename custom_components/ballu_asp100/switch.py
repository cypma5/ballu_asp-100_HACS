"""Switch platform for Ballu ASP-100."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.components import mqtt
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SWITCH_TYPES = {
    "volume": {
        "name": "Button Volume",
        "key": "volume",
        "icon": "mdi:volume-high",
        "payload_on": "1",
        "payload_off": "0",
        "enabled_default": True,
    },
    "backlight": {
        "name": "Auto-off Indication", 
        "key": "backlight",
        "icon": "mdi:brightness-6",
        "payload_on": "1",
        "payload_off": "0",
        "enabled_default": True,
    }
}

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Ballu ASP-100 switches from config entry."""
    data = config_entry.data
    
    switches = []
    for switch_key, switch_config in SWITCH_TYPES.items():
        switches.append(
            BalluASP100Switch(
                hass,
                data["device_id"],
                data["device_type"],
                data["name"],
                switch_key,
                switch_config,
                config_entry.entry_id,
            )
        )
    
    async_add_entities(switches)

class BalluASP100Switch(SwitchEntity):
    """Representation of a Ballu ASP-100 switch."""

    def __init__(
        self,
        hass: HomeAssistant,
        device_id: str,
        device_type: str,
        device_name: str,
        switch_key: str,
        switch_config: dict,
        entry_id: str,
    ) -> None:
        """Initialize the switch."""
        self.hass = hass
        self._device_id = device_id
        self._device_type = device_type
        self._device_name = device_name
        self._switch_key = switch_key
        self._switch_config = switch_config
        self._entry_id = entry_id
        
        self._attr_name = f"{switch_config['name']}"
        self._attr_unique_id = f"ballu_asp100_{device_id}_{switch_key}"
        self._attr_icon = switch_config["icon"]
        self._attr_entity_registry_enabled_default = switch_config.get("enabled_default", True)
        
        self._is_on = False
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
    def is_on(self) -> bool:
        """Return true if switch is on."""
        return self._is_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        topic = f"{self._command_topic_base}/{self._switch_config['key']}"
        
        await mqtt.async_publish(
            self.hass,
            topic,
            self._switch_config["payload_on"],
            qos=1,
            retain=False,
        )
        self._is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        topic = f"{self._command_topic_base}/{self._switch_config['key']}"
        
        await mqtt.async_publish(
            self.hass,
            topic,
            self._switch_config["payload_off"],
            qos=1,
            retain=False,
        )
        self._is_on = False
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Subscribe to MQTT topics when entity is added to hass."""
        topic = f"{self._state_topic_base}/{self._switch_config['key']}"
        
        await mqtt.async_subscribe(
            self.hass,
            topic,
            self._message_received,
        )

    def _message_received(self, message):
        """Handle new MQTT messages."""
        try:
            self._is_on = message.payload == self._switch_config["payload_on"]
            self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error("Error processing message for %s: %s", self.name, err)