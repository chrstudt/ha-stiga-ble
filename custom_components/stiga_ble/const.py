"""Constants for the Stiga G1200 BLE integration."""
import logging

DOMAIN = "stiga_ble"
CONF_MAC = "mac"

# Service and Characteristic UUIDs for Stiga G1200 BLE
STIGA_SERVICE_UUID = "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
STIGA_CHARACTERISTIC_UUID = "ed2ada88-d595-11ea-87d0-0242ac130003"

# Payloads for commands
PAYLOAD_START = bytearray([0x08, 0x01])
PAYLOAD_STOP = bytearray([0x08, 0x00])
PAYLOAD_HOME = bytearray([0x08, 0x03])

LOGGER = logging.getLogger(__package__)
