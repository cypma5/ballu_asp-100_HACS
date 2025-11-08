"""Sensor platform for Ballu ASP-100."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature, SIGNAL_STRENGTH_DECIBELS_MILLIWATT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SENSOR_TYPES = {
    "co2": {
        "name": "CO2",
        "key": "sensor/co2",
        "unit": "ppm",
        "icon": "mdi:molecule-co2",
        "enabled_default": False,
    },
    "filter_life": {
        "name": "Filter Remaining Life",
        "key": "expendables", 
        "unit": "%",
        "icon": "mdi:air-filter",
        "enabled_default": True,
    },
    "fan_speed": {
        "name": "Fan Speed",
        "key": "speed",
        "unit": "x",
        "icon": "mdi:fan",
        "enabled_default": False,
    },
    "temperature": {
        "name": "Air Temperature",
        "key": "sensor/temperature",
        "unit": UnitOfTemperature.CELSIUS,
        "icon": "mdi:thermometer",
        "enabled_default": False,
    },
    "rssi": {
        "name": "RSSI",
        "key": "diag/rssi",
        "unit": SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        "icon": "mdi:wifi",
        "enabled_default": False,
    },
    "mqtt_latency": {
        "name": "MQTT Latency", 
        "key": "diag/mqtt_latency",
        "unit": "ms",
        "icon": "mdi:speedometer",
        "enabled_default": False,
    },
    "gw_latency": {
        "name": "Gateway Latency",
        "key": "diag/gw_latency",
        "unit": "ms",
        "icon": "mdi:router-wireless",
        "enabled_default": False,
    },
    "gw_loss": {
        "name": "Gateway Loss",
        "key": "diag/gw_loss",
        "unit": "%",
        "icon": "mdi:connection",
        "enabled_default": False,
    },
    "turbo_timer": {
        "name": "Turbo Mode Timer",
        "key": "time",
        "unit": None,  # Форматированное время MM:SS
        "icon": "mdi:timer",
        "enabled_default": False,
    }
}

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Ballu ASP-100 sensors from config entry."""
    data = config_entry.data
    
    sensors = []
    for sensor_key, sensor_config in SENSOR_TYPES.items():
        sensors.append(
            BalluASP100Sensor(
                data["device_id"],
                data["device_type"],
                data["name"],
                sensor_key,
                sensor_config,
                config_entry.entry_id,
            )
        )
    
    async_add_entities(sensors)

class BalluASP100Sensor(SensorEntity):
    """Representation of a Ballu ASP-100 sensor."""

    def __init__(
        self,
        device_id: str,
        device_type: str,
        device_name: str,
        sensor_key: str,
        sensor_config: dict,
        entry_id: str,
    ) -> None:
        """Initialize the sensor."""
        self._device_id = device_id
        self._device_type = device_type
        self._device_name = device_name
        self._sensor_key = sensor_key
        self._sensor_config = sensor_config
        self._entry_id = entry_id
        
        self._attr_name = f"{sensor_config['name']}"
        self._attr_unique_id = f"ballu_asp100_{device_id}_{sensor_key}"
        self._attr_icon = sensor_config["icon"]
        self._attr_native_unit_of_measurement = sensor_config["unit"]
        self._attr_entity_registry_enabled_default = sensor_config["enabled_default"]
        
        self._state = None

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
    def native_value(self):
        """Return the state of the sensor."""
        return self._state

    async def async_added_to_hass(self) -> None:
        """Subscribe to MQTT topics when entity is added to hass."""
        topic = f"rusclimate/{self._device_type}/{self._device_id}/state/{self._sensor_config['key']}"
        
        await self.hass.components.mqtt.async_subscribe(
            topic,
            self._message_received,
        )

    def _message_received(self, message):
        """Handle new MQTT messages."""
        try:
            value = message.payload
            
            # Special handling for different sensor types
            if self._sensor_key == "filter_life":
                # Фильтр приходит как [85] - убираем скобки
                value = value.strip("[]")
            elif self._sensor_key == "turbo_timer":
                # Таймер форматируется как MM:SS
                from datetime import datetime
                seconds = int(value)
                minutes = seconds // 60
                remaining_seconds = seconds % 60
                value = f"{minutes:02d}:{remaining_seconds:02d}"
                
            # Convert to appropriate type
            if self._sensor_config["unit"] in ["ppm", "ms", "%", "x"]:
                self._state = int(float(value))
            elif self._sensor_config["unit"] == UnitOfTemperature.CELSIUS:
                self._state = float(value)
            else:
                self._state = value
                
            self.async_write_ha_state()
        except (ValueError, TypeError) as err:
            _LOGGER.error("Error processing message for %s: %s", self.name, err)