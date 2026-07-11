"""Button platform for Stiga BLE integration."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo

from .const import (
    DOMAIN,
    LOGGER,
    CMD_START,
    CMD_STOP,
    CMD_HOME,
)
from .coordinator import StigaBLECoordinator

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Stiga BLE buttons from a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: StigaBLECoordinator = data["coordinator"]

    async_add_entities([
        StigaCommandButton(coordinator, "Start", CMD_START, "mdi:play"),
        StigaCommandButton(coordinator, "Stop", CMD_STOP, "mdi:stop"),
        StigaCommandButton(coordinator, "Home", CMD_HOME, "mdi:home"),
        StigaRefreshButton(coordinator, "Refresh Status", "mdi:refresh"),
    ])

class StigaCommandButton(ButtonEntity):
    """Representation of a Stiga command button."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: StigaBLECoordinator,
        name: str,
        command: bytearray,
        icon: str,
    ) -> None:
        """Initialize the button."""
        self.coordinator = coordinator
        self._command = command
        self._attr_name = name
        self._attr_icon = icon
        
        mac_clean = coordinator.mac.replace(":", "").lower()
        self._attr_unique_id = f"stiga_cmd_{name.lower()}_{mac_clean}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, mac_clean)},
            name=f"Stiga Mower {coordinator.mac}",
            manufacturer="Stiga",
        )

    async def async_press(self) -> None:
        """Handle the button press."""
        LOGGER.debug("Pressing %s button", self._attr_name)
        await self.coordinator.send_command(self._command)

class StigaRefreshButton(ButtonEntity):
    """Representation of a Stiga refresh button."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: StigaBLECoordinator,
        name: str,
        icon: str,
    ) -> None:
        """Initialize the button."""
        self.coordinator = coordinator
        self._attr_name = name
        self._attr_icon = icon
        
        mac_clean = coordinator.mac.replace(":", "").lower()
        self._attr_unique_id = f"stiga_cmd_{name.replace(' ', '_').lower()}_{mac_clean}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, mac_clean)},
            name=f"Stiga Mower {coordinator.mac}",
            manufacturer="Stiga",
        )

    async def async_press(self) -> None:
        """Handle the button press."""
        LOGGER.debug("Pressing %s button", self._attr_name)
        await self.coordinator.async_request_refresh()
