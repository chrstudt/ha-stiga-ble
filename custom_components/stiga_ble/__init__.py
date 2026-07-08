"""The Stiga G1200 BLE integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN, LOGGER
from .coordinator import StigaBLECoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BUTTON]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Stiga G1200 BLE from a config entry."""
    LOGGER.debug("Setting up Stiga BLE entry for %s", entry.data.get("mac"))
    
    mac_address = entry.data.get("mac")
    if not mac_address:
        return False

    coordinator = StigaBLECoordinator(hass, mac_address)
    
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "mac": mac_address,
        "coordinator": coordinator
    }

    # Fetch initial data and start periodic polling
    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
