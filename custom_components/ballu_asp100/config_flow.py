"""Config flow for Ballu ASP-100 integration."""
from __future__ import annotations

import logging
import re
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult

_LOGGER = logging.getLogger(__name__)

DOMAIN = "ballu_asp100"

def validate_device_id(device_id: str) -> bool:
    """Validate device ID format (32 hex characters)."""
    device_id = device_id.lower().replace(":", "").replace("-", "").replace(" ", "")
    return len(device_id) == 32 and all(c in "0123456789abcdef" for c in device_id)

class BalluASP100ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Ballu ASP-100."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._device_id: str | None = None
        self._device_type: str | None = None
        self._name: str | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate device_id
            if not validate_device_id(user_input["device_id"]):
                errors["base"] = "invalid_device_id"
            else:
                # Format device_id
                device_id = user_input["device_id"].lower().replace(":", "").replace("-", "").replace(" ", "")
                device_type = user_input.get("device_type", "69").strip()
                name = user_input.get("name", f"Ballu ASP-100 {device_id[-6:].upper()}").strip()

                # Check if already configured
                await self.async_set_unique_id(f"ballu_asp100_{device_id}")
                self._abort_if_unique_id_configured()

                # Create entry
                return self.async_create_entry(
                    title=name,
                    data={
                        "device_id": device_id,
                        "device_type": device_type,
                        "name": name,
                    },
                )

        # Show form
        schema = vol.Schema({
            vol.Required("device_id"): str,
            vol.Optional("device_type", default="69"): str,
            vol.Optional("name", default="Ballu ASP-100"): str,
        })

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "instructions": "Device ID можно найти в логах MQTT брокера (32 hex символа)"
            }
        )