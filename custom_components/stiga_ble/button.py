"""Button platform for Stiga BLE integration."""
from __future__ import annotations

import asyncio
from bleak import BleakClient, BleakError

from homeassistant.components.button import ButtonEntity
from homeassistant.components.bluetooth import async_ble_device_from_address
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN, 
    CONF_MAC, 
    STIGA_CHARACTERISTIC_UUID, 
    PAYLOAD_START,
    LOGGER
)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Stiga BLE button from a config entry."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    mac_address = data.get(CONF_MAC)
    
    if mac_address:
        async_add_entities([StigaStartButton(hass, mac_address)])


class StigaStartButton(ButtonEntity):
    """Representation of a Stiga Start Button."""

    def __init__(self, hass: HomeAssistant, mac: str) -> None:
        """Initialize the button."""
        self.hass = hass
        self._mac = mac
        
        # Clean MAC for unique ID (e.g. 34:AB:95:47:B2:E6 -> 34ab9547b2e6)
        mac_clean = mac.replace(":", "").lower()
        self._attr_unique_id = f"stiga_start_{mac_clean}"
        self._attr_name = "Stiga G1200 Start"
        self._attr_icon = "mdi:robot-mower"

    async def async_press(self) -> None:
        """Handle the button press."""
        LOGGER.info("Attempting to start Stiga Mower at %s", self._mac)
        
        mac_upper = self._mac.upper()
        # Resolve best path to the mower via Bluetooth Proxys
        ble_device = async_ble_device_from_address(self.hass, mac_upper, connectable=True)
        
        if not ble_device:
            # Fallback: Sometimes devices advertise as non-connectable but can still be connected to,
            # or HA cached them without the connectable flag.
            ble_device = async_ble_device_from_address(self.hass, mac_upper, connectable=False)
            
        if not ble_device:
            LOGGER.error(
                "Could not find BLE device with MAC %s. "
                "Make sure it is in range of an active Shelly Bluetooth proxy and is currently advertising (z.B. nicht im Tiefschlaf).",
                mac_upper
            )
            return

        from bleak_retry_connector import establish_connection
        
        try:
            client = await establish_connection(
                client_class=BleakClient,
                device=ble_device,
                name=mac_upper,
            )
            
            try:
                LOGGER.debug("Connected to %s, sending START command.", mac_upper)
                
                await client.write_gatt_char(
                    STIGA_CHARACTERISTIC_UUID, 
                    PAYLOAD_START, 
                    response=False
                )
                
                LOGGER.info("START command sent successfully to Stiga Mower.")
            finally:
                await client.disconnect()
                
        except BleakError as err:
            LOGGER.error("Bleak error connecting to %s: %s", mac_upper, err)
        except asyncio.TimeoutError:
            LOGGER.error("Timeout connecting to %s", self._mac)
        except Exception as err:
            LOGGER.exception("Unexpected error when sending command to %s: %s", self._mac, err)
