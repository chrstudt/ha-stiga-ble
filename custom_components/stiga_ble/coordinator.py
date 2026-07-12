"""Coordinator for Stiga BLE integration."""
import asyncio
import struct
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
            "battery_capacity": None,
            "battery_voltage": None,
            "battery_cycles": None,
            "remaining_time": None,
            "automatic_trigger": None,
            "raw_rx": None,
        }
        self._data_received = asyncio.Event()

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
                    self._data_received.clear()
                    try:
                        await asyncio.wait_for(
                            self._data_received.wait(), 
                            timeout=WAIT_FOR_NOTIFICATIONS_SEC
                        )
                    except (asyncio.TimeoutError, TimeoutError):
                        LOGGER.debug("Timeout reached while waiting for data notifications")
                    
                    LOGGER.info("Finished collecting data from %s, disconnecting.", self.mac)
                finally:
                    await client.disconnect()
            except Exception as e:
                self.connected = False
                raise UpdateFailed(f"Error communicating with {self.mac}: {e}")
            finally:
                self.connected = False

        return self.data

def parse_varint(data: bytearray, offset: int) -> tuple[int, int]:
    result = 0
    shift = 0
    while offset < len(data):
        byte = data[offset]
        offset += 1
        result |= (byte & 0x7f) << shift
        if not (byte & 0x80):
            break
        shift += 7
    return result, offset

def extract_protobuf_fields(data: bytearray) -> dict[int, any]:
    fields = {}
    offset = 0
    while offset < len(data):
        if offset >= len(data):
            break
        key, offset = parse_varint(data, offset)
        field_num = key >> 3
        wire_type = key & 0x07
        
        if wire_type == 0: # Varint
            val, offset = parse_varint(data, offset)
            fields[field_num] = val
        elif wire_type == 1: # 64-bit
            if offset + 8 <= len(data):
                offset += 8
            else:
                break
        elif wire_type == 2: # Length-delimited
            length, offset = parse_varint(data, offset)
            offset += length
        elif wire_type == 5: # 32-bit float
            if offset + 4 <= len(data):
                val = struct.unpack('<f', data[offset:offset+4])[0]
                fields[field_num] = val
                offset += 4
            else:
                break
        else:
            # Unknown wire type, can't reliably continue parsing
            break
    return fields

    def _notification_handler(self, sender, data: bytearray) -> None:
        """Handle incoming BLE notifications."""
        self.data["raw_rx"] = data.hex(" ").upper()

        uuid = getattr(sender, "uuid", "").lower()
        handle = getattr(sender, "handle", 0)

        try:
            fields = extract_protobuf_fields(data)
        except Exception as e:
            LOGGER.debug("Could not parse protobuf: %s", e)
            fields = {}

        if "ed2abe7b" in uuid or handle == 48 or (3 in fields and 1 in fields and fields.get(1) == 1):
            if 3 in fields:
                state_val = fields[3]
                states = {
                    1: "Mowing",
                    3: "Charging",
                    4: "Idle / Full",
                    6: "Error: Blocked",
                    8: "Error: Flap open",
                    13: "Returning",
                    33: "Waiting"
                }
                self.data["status"] = states.get(state_val, f"Unknown ({state_val})")
            
            if 2 in fields:
                self.data["automatic_trigger"] = bool(fields[2])
            else:
                self.data["automatic_trigger"] = False
        
        elif "00002a19" in uuid or handle == 43 or (1 in fields and 2 in fields and fields.get(1, 0) > 100):
            if 1 in fields:
                self.data["battery_capacity"] = fields[1]
            if 2 in fields:
                self.data["battery"] = fields[2]
            if 7 in fields:
                self.data["battery_voltage"] = round(fields[7], 2)
            if 8 in fields:
                self.data["battery_cycles"] = fields[8]
            if 9 in fields:
                self.data["remaining_time"] = round(fields[9], 1)

        LOGGER.info("Stiga received notification: %s -> Parsed status: %s", data.hex(' ').upper(), self.data.get('status'))

        # Check if we have received at least basic status or battery info
        if self.data.get("status") is not None or self.data.get("battery") is not None:
            self._data_received.set()

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
