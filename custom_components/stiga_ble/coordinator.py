"""Coordinator for Stiga BLE integration."""
import asyncio
from datetime import timedelta
from bleak import BleakClient
from bleak.exc import BleakError
from bleak_retry_connector import BleakClientWithServiceCache, establish_connection

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
WAIT_FOR_NOTIFICATIONS_SEC = 5.0

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
        self.client = None
        
        self.data = {
            "battery": None,
            "status": None,
            "speed": None,
            "mode": None,
            "error": None,
            "raw_rx": None,
        }

    def _get_ble_device(self):
        """Get the best BLE device, explicitly avoiding Shelly proxies if possible."""
        ble_device = None
        try:
            from homeassistant.components.bluetooth import async_scanner_devices_by_address
            devices = async_scanner_devices_by_address(self.hass, self.mac, connectable=True)
            for d in devices:
                scanner = getattr(d, "scanner", None)
                source = getattr(scanner, "source", "") if scanner else ""
                name = getattr(scanner, "name", "") if scanner else ""
                # Ignore Shelly proxies as they often fail to maintain the connection
                if "shelly" not in str(source).lower() and "shelly" not in str(name).lower():
                    ble_device = getattr(d, "ble_device", d)
                    break
        except Exception as e:
            LOGGER.debug("Could not filter scanners: %s", e)
        
        if not ble_device:
            # Fallback to the default HA behavior
            ble_device = async_ble_device_from_address(self.hass, self.mac, connectable=True)
            
        return ble_device

    async def _async_update_data(self):
        """Fetch data from device."""
        LOGGER.debug("Starting periodic data fetch for %s", self.mac)
        async with self._ble_lock:
            ble_device = self._get_ble_device()
            if not ble_device:
                raise UpdateFailed(f"Could not find BLE device for {self.mac}")

            try:
                self.connected = True
                client = await establish_connection(
                    BleakClientWithServiceCache,
                    ble_device,
                    self.mac,
                )
                try:
                    # Dynamically subscribe to all notify characteristics
                    # like the TUI tool does, to ensure we don't miss state updates
                    # sent on new or unlisted characteristics.
                    for service in client.services:
                        for char in service.characteristics:
                            if "notify" in char.properties:
                                try:
                                    await client.start_notify(char.uuid, self._notification_handler)
                                except Exception as e:
                                    LOGGER.debug("Could not subscribe to %s: %s", char.uuid, e)
                    
                    LOGGER.info("Connected to %s, waiting for notifications...", self.mac)
                    await asyncio.sleep(WAIT_FOR_NOTIFICATIONS_SEC)
                    LOGGER.info("Finished collecting data from %s, disconnecting.", self.mac)
                finally:
                    await client.disconnect()
            except Exception as e:
                self.connected = False
                raise UpdateFailed(f"Error communicating with {self.mac}: {e}")
            finally:
                self.connected = False

        return self.data

    def _notification_handler(self, sender, data: bytearray) -> None:
        """Handle incoming BLE notifications."""
        self.data["raw_rx"] = data.hex(" ").upper()

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

        LOGGER.info("Stiga received notification: %s -> Parsed status: %s", data.hex(' ').upper(), self.data.get('status'))

        # Push the updated data instantly to the Home Assistant sensors
        self.async_set_updated_data(self.data)

    async def send_command(self, command: bytearray) -> None:
        """Send a command to the mower."""
        LOGGER.debug("Attempting to send command to %s", self.mac)
        async with self._ble_lock:
            client = self.client
            disconnect_after = False

            if not client or not client.is_connected:
                ble_device = self._get_ble_device()
                if not ble_device:
                    LOGGER.error("Could not find BLE device for %s", self.mac)
                    return
                try:
                    client = await establish_connection(
                        BleakClientWithServiceCache,
                        ble_device,
                        self.mac,
                    )
                    disconnect_after = True
                except Exception as e:
                    LOGGER.error("Error connecting to send command to %s: %s", self.mac, e)
                    return

            try:
                await client.write_gatt_char(WRITE_CHAR_UUID, command, response=False)
                LOGGER.info("Command sent successfully to %s", self.mac)
            except Exception as e:
                LOGGER.error("Error sending command to %s: %s", self.mac, e)
            finally:
                if disconnect_after and client:
                    await client.disconnect()
        
        # After sending a command, wait a bit and trigger an update to refresh state
        self.hass.async_create_task(self._delayed_refresh())

    async def _delayed_refresh(self) -> None:
        await asyncio.sleep(2)
        await self.async_request_refresh()
