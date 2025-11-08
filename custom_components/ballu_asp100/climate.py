"""Climate platform for Ballu ASP-100."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.components.climate.const import HVACMode
from homeassistant.components import mqtt
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, FAN_MODE_MAPPING, MODE_MAPPING, PRESET_MODES

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Ballu ASP-100 climate entity from config entry."""
    data = config_entry.data
    
    entity = BalluASP100Climate(
        hass,
        data["device_id"],
        data["device_type"],
        data["name"],
        config_entry.entry_id,
    )
    
    async_add_entities([entity])

class BalluASP100Climate(ClimateEntity):
    """Representation of Ballu ASP-100 climate device."""

    _attr_has_entity_name = True
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_target_temperature_step = 1
    _attr_min_temp = 5
    _attr_max_temp = 25
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.FAN_ONLY]
    _attr_fan_modes = list(FAN_MODE_MAPPING.keys())
    _attr_preset_modes = PRESET_MODES
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.FAN_MODE
        | ClimateEntityFeature.PRESET_MODE
        | ClimateEntityFeature.TURN_OFF
        | ClimateEntityFeature.TURN_ON
    )

    def __init__(
        self,
        hass: HomeAssistant,
        device_id: str,
        device_type: str,
        name: str,
        entry_id: str,
    ) -> None:
        """Initialize the climate device."""
        self.hass = hass
        self._device_id = device_id
        self._device_type = device_type
        self._attr_name = name
        self._attr_unique_id = f"ballu_asp100_{device_id}_climate"
        self._entry_id = entry_id

        # State attributes
        self._current_temperature = None
        self._target_temperature = 20
        self._hvac_mode = HVACMode.OFF
        self._fan_mode = "Off"
        self._preset_mode = "comfort"
        self._available = True

        # MQTT topics
        self._command_topic_base = f"rusclimate/{device_type}/{device_id}/control"
        self._state_topic_base = f"rusclimate/{device_type}/{device_id}/state"

    @property
    def device_info(self):
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._device_id)},
            "name": self._attr_name,
            "manufacturer": "Ballu",
            "model": "ONEAIR ASP-100",
        }

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._available

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        return self._current_temperature

    @property
    def target_temperature(self) -> float | None:
        """Return the temperature we try to reach."""
        return self._target_temperature

    @property
    def hvac_mode(self) -> HVACMode:
        """Return current operation mode."""
        return self._hvac_mode

    @property
    def fan_mode(self) -> str:
        """Return the fan setting."""
        return self._fan_mode

    @property
    def preset_mode(self) -> str:
        """Return the preset mode."""
        return self._preset_mode

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        _LOGGER.debug("Setting temperature: %s", kwargs)
        
        if (temperature := kwargs.get(ATTR_TEMPERATURE)) is not None:
            topic = f"{self._command_topic_base}/temperature"
            
            await mqtt.async_publish(
                self.hass,
                topic,
                str(int(temperature)),
                qos=1,
                retain=False,
            )
            
            self._target_temperature = temperature
            self.async_write_ha_state()

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set new fan mode."""
        _LOGGER.debug("Setting fan mode: %s", fan_mode)
        
        topic = f"{self._command_topic_base}/speed"
        fan_value = FAN_MODE_MAPPING.get(fan_mode, 0)
        
        await mqtt.async_publish(
            self.hass,
            topic,
            str(fan_value),
            qos=1,
            retain=False,
        )
        
        self._fan_mode = fan_mode
        self.async_write_ha_state()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new operation mode."""
        _LOGGER.debug("Setting HVAC mode: %s", hvac_mode)
        
        topic = f"{self._command_topic_base}/mode"
        
        if hvac_mode == HVACMode.OFF:
            mode_value = 0
        else:
            # При включении используем текущий preset mode
            mode_value = MODE_MAPPING.get(self._preset_mode, 1)
        
        await mqtt.async_publish(
            self.hass,
            topic,
            str(mode_value),
            qos=1,
            retain=False,
        )
        
        self._hvac_mode = hvac_mode
        self.async_write_ha_state()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        _LOGGER.debug("Setting preset mode: %s", preset_mode)
        
        topic = f"{self._command_topic_base}/mode"
        mode_value = MODE_MAPPING.get(preset_mode, 1)
        
        await mqtt.async_publish(
            self.hass,
            topic,
            str(mode_value),
            qos=1,
            retain=False,
        )
        
        self._preset_mode = preset_mode
        
        # Если устройство включено, обновляем HVAC mode
        if self._hvac_mode != HVACMode.OFF:
            self._hvac_mode = HVACMode.FAN_ONLY
            
        self.async_write_ha_state()

    async def async_turn_on(self) -> None:
        """Turn the device on."""
        await self.async_set_hvac_mode(HVACMode.FAN_ONLY)

    async def async_turn_off(self) -> None:
        """Turn the device off."""
        await self.async_set_hvac_mode(HVACMode.OFF)

    async def async_added_to_hass(self) -> None:
        """Subscribe to MQTT topics when entity is added to hass."""
        _LOGGER.debug("Setting up MQTT subscriptions for device %s", self._device_id)
        
        # Temperature state
        await mqtt.async_subscribe(
            self.hass,
            f"{self._state_topic_base}/temperature",
            self._temperature_message_received,
        )
        
        # Current temperature from sensor
        await mqtt.async_subscribe(
            self.hass,
            f"{self._state_topic_base}/sensor/temperature", 
            self._current_temperature_message_received,
        )
        
        # Fan mode state
        await mqtt.async_subscribe(
            self.hass,
            f"{self._state_topic_base}/speed",
            self._fan_mode_message_received,
        )
        
        # Mode state (используется и для HVAC mode и для preset mode)
        await mqtt.async_subscribe(
            self.hass,
            f"{self._state_topic_base}/mode",
            self._mode_message_received,
        )

    def _temperature_message_received(self, message):
        """Handle temperature state messages."""
        try:
            self._target_temperature = float(message.payload)
            _LOGGER.debug("Received target temperature: %s", self._target_temperature)
            self.async_write_ha_state()
        except ValueError as err:
            _LOGGER.error("Invalid temperature value: %s - %s", message.payload, err)

    def _current_temperature_message_received(self, message):
        """Handle current temperature messages."""
        try:
            self._current_temperature = float(message.payload)
            _LOGGER.debug("Received current temperature: %s", self._current_temperature)
            self.async_write_ha_state()
        except ValueError as err:
            _LOGGER.error("Invalid current temperature value: %s - %s", message.payload, err)

    def _fan_mode_message_received(self, message):
        """Handle fan mode state messages."""
        try:
            fan_value = int(message.payload)
            _LOGGER.debug("Received fan mode value: %s", fan_value)
            
            # Reverse mapping from value to mode name
            for mode, value in FAN_MODE_MAPPING.items():
                if value == fan_value:
                    self._fan_mode = mode
                    break
                    
            self.async_write_ha_state()
        except ValueError as err:
            _LOGGER.error("Invalid fan mode value: %s - %s", message.payload, err)

    def _mode_message_received(self, message):
        """Handle mode state messages."""
        try:
            mode_value = int(message.payload)
            _LOGGER.debug("Received mode value: %s", mode_value)
            
            if mode_value == 0:
                self._hvac_mode = HVACMode.OFF
                self._preset_mode = "comfort"
            else:
                self._hvac_mode = HVACMode.FAN_ONLY
                # Reverse mapping from value to preset name
                for preset, value in MODE_MAPPING.items():
                    if value == mode_value:
                        self._preset_mode = preset
                        break
                        
            self.async_write_ha_state()
        except ValueError as err:
            _LOGGER.error("Invalid mode value: %s - %s", message.payload, err)