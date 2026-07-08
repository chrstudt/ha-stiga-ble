"""Constants for the Stiga G1200 BLE integration."""
import logging

DOMAIN = "stiga_ble"
CONF_MAC = "mac"

LOGGER = logging.getLogger(__package__)

WRITE_CHAR_UUID = "ed2ada88-d595-11ea-87d0-0242ac130003"
KEEPALIVE_CHAR_UUID = "00002a19-0000-1000-8000-00805f9b34fb"

NOTIFY_CHAR_UUIDS = [
    "ed2ae29a-d595-11ea-87d0-0242ac130003",
    "ed2abe7b-d595-11ea-87d0-0242ac130003",
    "ed2ae1b8-d595-11ea-87d0-0242ac130003",
    "ed2af5d6-d595-11ea-87d0-0242ac130003",
    "ed2abe7a-d595-11ea-87d0-0242ac130003",
    "00002a19-0000-1000-8000-00805f9b34fb",
]

CMD_START = bytearray([0x08, 0x01])
CMD_STOP = bytearray([0x08, 0x00])
CMD_HOME = bytearray([0x08, 0x04])
