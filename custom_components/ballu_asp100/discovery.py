"""Discovery helper for Ballu ASP-100."""
from __future__ import annotations

import asyncio
import logging
import re
from typing import Any

from homeassistant.components import mqtt

_LOGGER = logging.getLogger(__name__)

async def discover_ballu_devices(hass: HomeAssistant) -> list[dict[str, str]]:
    """Discover Ballu ASP-100 devices via MQTT with better validation."""
    devices = {}
    discovery_complete = asyncio.Event()
    
    async def message_received(msg: mqtt.ReceiveMessage) -> None:
        """Handle incoming MQTT messages for discovery."""
        topic = msg.topic
        payload = msg.payload
        
        # Pattern: rusclimate/{device_type}/{device_id}/state/#
        pattern = r"rusclimate/([^/]+)/([a-f0-9]{32})/state/(.+)"
        match = re.match(pattern, topic)
        
        if match:
            device_type = match.group(1)
            device_id = match.group(2)
            state_key = match.group(3)
            
            # Only process certain state topics to confirm it's a Ballu device
            if state_key in ["temperature", "speed", "mode", "sensor/temperature", "diag/rssi"]:
                device_key = f"{device_type}_{device_id}"
                
                if device_key not in devices:
                    devices[device_key] = {
                        "device_id": device_id,
                        "device_type": device_type,
                        "name": f"Ballu ASP-100 {device_id[-6:].upper()}",
                        "last_seen": asyncio.get_event_loop().time(),
                        "topics_found": set()
                    }
                
                devices[device_key]["topics_found"].add(state_key)
                devices[device_key]["last_seen"] = asyncio.get_event_loop().time()
                
                # If we found multiple key topics, we're confident it's a Ballu device
                if len(devices[device_key]["topics_found"]) >= 3:
                    discovery_complete.set()

    # Subscribe to all Ballu state topics
    subscription = await mqtt.async_subscribe(
        hass, "rusclimate/+/+/state/#", message_received, 1
    )
    
    try:
        # Wait for discovery to complete or timeout after 10 seconds
        await asyncio.wait_for(discovery_complete.wait(), timeout=10.0)
    except asyncio.TimeoutError:
        _LOGGER.debug("Device discovery timeout")
    finally:
        subscription()
    
    # Filter devices that we're confident about
    confident_devices = []
    for device in devices.values():
        if len(device["topics_found"]) >= 2:  # At least 2 different state topics
            confident_devices.append({
                "device_id": device["device_id"],
                "device_type": device["device_type"],
                "name": device["name"]
            })
    
    return confident_devices