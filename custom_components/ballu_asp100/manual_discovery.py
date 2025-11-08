"""Services for Ballu ASP-100 manual discovery."""
import logging

import voluptuous as vol

from homeassistant.components import mqtt
from homeassistant.core import ServiceCall
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SERVICE_DISCOVER_DEVICES = "discover_devices"
SERVICE_SCHEMA = vol.Schema({})

async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up services for Ballu ASP-100."""
    
    async def async_handle_discover(call: ServiceCall) -> None:
        """Handle discover devices service call."""
        from .config_flow import discover_ballu_devices
        
        devices = await discover_ballu_devices(hass)
        
        if devices:
            _LOGGER.info("Обнаружено устройств Ballu: %d", len(devices))
            for device in devices:
                _LOGGER.info(
                    "Устройство: %s, ID: %s, Тип: %s", 
                    device["name"], device["device_id"], device["device_type"]
                )
            
            # Store discovered devices for potential notification
            hass.data.setdefault(DOMAIN, {})["discovered_devices"] = devices
        else:
            _LOGGER.warning("Устройства Ballu не обнаружены")
            
        # Trigger reload of config flows to show discovered devices
        await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}, data=None
        )

    hass.services.async_register(
        DOMAIN, SERVICE_DISCOVER_DEVICES, async_handle_discover, schema=SERVICE_SCHEMA
    )

async def async_unload_services(hass: HomeAssistant) -> None:
    """Unload Ballu ASP-100 services."""
    hass.services.async_remove(DOMAIN, SERVICE_DISCOVER_DEVICES)