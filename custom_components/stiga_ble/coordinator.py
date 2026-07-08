"""Coordinator for Stiga BLE integration."""
import asyncio
from datetime import timedelta
from bleak import BleakClient
from bleak.exc import BleakError

from homeassistant.core import HomeAssistant, callback
from homeassistant.components.bluetooth import async_ble_device_from_address
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    LOGGER,
    WRITE_CHAR_UUID,
    NOTIFY_CHAR_UUIDS,
)

POLL_INTERVAL = timedelta(minutes=5)
WAIT_FOR_NOTIFICATIONS_SEC = 10.0

class StigaBLECoordinator(DataUpdateCoordinator):
    """Class to manage BLE connection and data for Stiga mower."""

    def __init__(self, hass: HomeAssistant, mac: str) -> None:
        """Initialize."""
        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            update_interval=POLL_INTERVAL,
        )
        self.mac = mac
        self._ble_lock = asyncio.Lock()
        self.connected = False
        
        self.data = {
            "battery": None,
            "status": None,
            "speed": None,
            "mode": None,
            "error": None,
        }

    async def _async_update_data(self):
        """Fetch data from device."""
        LOGGER.debug("Starting periodic data fetch for %s", self.mac)
        async with self._ble_lock:
            ble_device = async_ble_device_from_address(self.hass, self.mac, connectable=True)
            if not ble_device:
                raise UpdateFailed(f"Could not find BLE device for {self.mac}")

            try:
                self.connected = True
                async with BleakClient(ble_device) as client:
                    for uuid in NOTIFY_CHAR_UUIDS:
                        try:
                            await client.start_notify(uuid, self._notification_handler)
                        except Exception as e:
                            LOGGER.debug("Could not subscribe to %s: %s", uuid, e)
                    
                    LOGGER.info("Connected to %s, waiting for notifications...", self.mac)
                    await asyncio.sleep(WAIT_FOR_NOTIFICATIONS_SEC)
                    LOGGER.info("Finished collecting data from %s, disconnecting.", self.mac)
            except Exception as e:
                self.connected = False
                raise UpdateFailed(f"Error communicating with {self.mac}: {e}")
            finally:
                self.connected = False

        return self.data

    def _notification_handler(self, sender, data: bytearray) -> None:
        """Handle incoming BLE notifications."""
        if len(data) >= 3 and data[0] == 0x02:
            self.data["battery"] = data[1]
            states = {0: "Idle", 1: "Mowing", 2: "Charging", 3: "Paused", 4: "Error"}
            self.data["status"] = states.get(data[2], f"Unknown ({data[2]})")
        elif len(data) >= 6 and data[0] == 0x08 and data[1] == 0x01 and data[2] == 0x18 and data[4] == 0x28 and data[5] == 0x01:
            state_val = data[3]
            states = {
                0x01: "Mowing",
                0x03: "Charging",
                0x04: "Returning",
                0x06: "Blocked",
                0x08: "Lid Open",
                0x21: "Stopped"
            }
            self.data["status"] = states.get(state_val, f"Unknown (0x{state_val:02X})")
        elif len(data) >= 5 and data[0] == 0x08 and data[1] == 0x88 and data[2] == 0x27 and data[3] == 0x10:
            self.data["battery"] = data[4]
        elif len(data) >= 4 and data[0] == 0x03:
            self.data["speed"] = (data[1] << 8) | data[2]
            modes = {0: "Standard", 1: "Eco", 2: "Turbo"}
            self.data["mode"] = modes.get(data[3], f"Unknown ({data[3]})")
        elif len(data) >= 2 and data[0] == 0x04:
            errors = {0: "None", 1: "Blade Blocked"}
            if data[1] == 0:
                self.data["error"] = "None"
            else:
                self.data["error"] = errors.get(data[1], f"Unknown Error ({data[1]})")

    async def send_command(self, command: bytearray) -> None:
        """Send a command to the mower."""
        LOGGER.debug("Attempting to send command to %s", self.mac)
        async with self._ble_lock:
            ble_device = async_ble_device_from_address(self.hass, self.mac, connectable=True)
            if not ble_device:
                LOGGER.error("Could not find BLE device for %s", self.mac)
                return
                
            try:
                self.connected = True
                async with BleakClient(ble_device) as client:
                    await client.write_gatt_char(WRITE_CHAR_UUID, command, response=False)
                    LOGGER.info("Command sent successfully to %s", self.mac)
            except Exception as e:
                LOGGER.error("Error sending command to %s: %s", self.mac, e)
            finally:
                self.connected = False
        
        # After sending a command, wait a bit and trigger an update to refresh state
        self.hass.async_create_task(self._delayed_refresh())

    async def _delayed_refresh(self) -> None:
        await asyncio.sleep(2)
        await self.async_request_refresh()
