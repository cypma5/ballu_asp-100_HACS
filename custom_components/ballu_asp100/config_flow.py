"""Config flow for Ballu ASP-100 integration."""
from __future__ import annotations

import asyncio
import logging
import re
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components import mqtt
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("device_id"): str,
        vol.Optional("device_type", default="69"): str,
        vol.Required("name", default="Ballu ASP-100"): str,
    }
)

STEP_DISCOVERY_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("discovered_device"): vol.In([]),  # Will be populated dynamically
    }
)

def validate_device_id(device_id: str) -> bool:
    """Validate device ID format (32 hex characters)."""
    device_id = device_id.lower().replace(":", "").replace("-", "").replace(" ", "")
    return len(device_id) == 32 and all(c in "0123456789abcdef" for c in device_id)

async def discover_ballu_devices(hass: HomeAssistant) -> list[dict[str, str]]:
    """Discover Ballu ASP-100 devices via MQTT."""
    devices = []
    
    # Subscribe to all state topics to find devices
    def message_received(msg):
        topic = msg.topic
        # Pattern: rusclimate/{device_type}/{device_id}/state/#
        pattern = r"rusclimate/([^/]+)/([^/]+)/state/.+"
        match = re.match(pattern, topic)
        if match:
            device_type = match.group(1)
            device_id = match.group(2)
            # Only add if it's a valid device_id (32 hex chars)
            if validate_device_id(device_id):
                devices.append({
                    "device_id": device_id,
                    "device_type": device_type,
                    "name": f"Ballu ASP-100 {device_id[-6:]}"
                })
    
    # Subscribe to all Ballu topics
    subscription = await mqtt.async_subscribe(
        hass, "rusclimate/+/+/state/#", message_received, 1
    )
    
    # Wait for messages
    await asyncio.sleep(5)
    subscription()
    
    # Remove duplicates
    unique_devices = []
    seen_ids = set()
    for device in devices:
        if device["device_id"] not in seen_ids:
            unique_devices.append(device)
            seen_ids.add(device["device_id"])
    
    return unique_devices

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Ballu ASP-100."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self.discovered_devices: list[dict[str, str]] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            # Try to discover devices automatically
            self.discovered_devices = await discover_ballu_devices(self.hass)
            
            if self.discovered_devices:
                return await self.async_step_discovery()
            
            # No devices found, show manual entry
            return self.async_show_form(
                step_id="user", 
                data_schema=STEP_USER_DATA_SCHEMA,
                description_placeholders={
                    "instructions": "Device ID можно найти в логах MQTT брокера или в мобильном приложении"
                }
            )

        errors = {}

        # Validate device_id (32 hex characters)
        if not validate_device_id(user_input["device_id"]):
            errors["device_id"] = "invalid_device_id"

        if not errors:
            return await self._create_entry(user_input)

        return self.async_show_form(
            step_id="user", 
            data_schema=STEP_USER_DATA_SCHEMA, 
            errors=errors
        )

    async def async_step_discovery(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle discovered devices."""
        if user_input is None:
            # Create schema with discovered devices
            device_options = {
                device["device_id"]: f"{device['name']} (Type: {device['device_type']})" 
                for device in self.discovered_devices
            }
            
            schema = vol.Schema({
                vol.Required("discovered_device"): vol.In(device_options)
            })
            
            return self.async_show_form(
                step_id="discovery",
                data_schema=schema,
                description_placeholders={
                    "count": str(len(self.discovered_devices))
                }
            )

        # Find the selected device
        selected_device_id = user_input["discovered_device"]
        selected_device = next(
            device for device in self.discovered_devices 
            if device["device_id"] == selected_device_id
        )
        
        user_input = {
            "device_id": selected_device["device_id"],
            "device_type": selected_device["device_type"],
            "name": selected_device["name"],
        }
        
        return await self._create_entry(user_input)

    async def _create_entry(self, user_input: dict[str, Any]) -> FlowResult:
        """Create config entry from user input."""
        # Format device_id consistently
        device_id = user_input["device_id"].lower().replace(":", "").replace("-", "").replace(" ", "")
        device_type = user_input["device_type"].strip() or "69"
        
        # Use device_id as unique_id
        unique_id = f"ballu_asp100_{device_id}"
        
        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured()

        # Store the formatted data
        data = {
            "device_id": device_id,
            "device_type": device_type,
            "name": user_input["name"].strip(),
            "mac_address": device_id,
        }

        return self.async_create_entry(title=data["name"], data=data)