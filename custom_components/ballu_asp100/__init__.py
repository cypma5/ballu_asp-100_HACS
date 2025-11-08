"""The Ballu ASP-100 integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN, MANUFACTURER, MODEL

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.CLIMATE,
    Platform.SENSOR, 
    Platform.SWITCH,
    Platform.SELECT
]

async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up the Ballu ASP-100 component."""
    # Set up services
    from .services import async_setup_services
    await async_setup_services(hass)
    
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Ballu ASP-100 from a config entry."""
    
    # Create device registry entry
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.data["device_id"])},
        name=entry.data["name"],
        manufacturer=MANUFACTURER,
        model=MODEL,
    )

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

async def async_unload(hass: HomeAssistant) -> bool:
    """Unload Ballu ASP-100 services."""
    from .services import async_unload_services
    await async_unload_services(hass)
    return True