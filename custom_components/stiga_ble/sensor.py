"""Sensor platform for Stiga BLE integration."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.components.bluetooth import (
    BluetoothCallbackMatcher,
    BluetoothChange,
    BluetoothScanningMode,
    BluetoothServiceInfoBleak,
    async_register_callback,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN, CONF_MAC, LOGGER

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Stiga BLE sensors from a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    mac_address = data.get(CONF_MAC)

    if not mac_address:
        return

    battery_sensor = StigaBatterySensor(mac_address)
    status_sensor = StigaStatusSensor(mac_address)

    async_add_entities([battery_sensor, status_sensor])

    @callback
    def update_ble_data(
        service_info: BluetoothServiceInfoBleak,
        change: BluetoothChange,
    ) -> None:
        """Handle new BLE data."""
        # Find all manufacturer data and service data
        payloads = list(service_info.manufacturer_data.values()) + list(service_info.service_data.values())
        
        battery_updated = False
        status_updated = False
        
        for data_bytes in payloads:
            data = bytearray(data_bytes)
            
            # Pattern 1: 0x02 cmd (Battery & Status)
            if len(data) >= 3 and data[0] == 0x02:
                battery_sensor.update_battery(data[1])
                states = {0: "Idle", 1: "Mowing", 2: "Charging", 3: "Paused", 4: "Error"}
                status_sensor.update_status(states.get(data[2], f"Unknown ({data[2]})"))
                battery_updated = True
                status_updated = True
                
            # Pattern 2: 0x08 cmd (Status)
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
                status_sensor.update_status(states.get(state_val, f"Unknown (0x{state_val:02X})"))
                status_updated = True
                
            # Pattern 3: 0x08 cmd (Battery)
            elif len(data) >= 5 and data[0] == 0x08 and data[1] == 0x88 and data[2] == 0x27 and data[3] == 0x10:
                battery_sensor.update_battery(data[4])
                battery_updated = True

        if battery_updated:
            battery_sensor.async_write_ha_state()
        if status_updated:
            status_sensor.async_write_ha_state()

    # Register BLE callback
    entry.async_on_unload(
        async_register_callback(
            hass,
            update_ble_data,
            BluetoothCallbackMatcher(address=mac_address),
            BluetoothScanningMode.PASSIVE,
        )
    )

class StigaMowerSensor(SensorEntity):
    """Base class for Stiga BLE sensors."""

    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(self, mac: str) -> None:
        """Initialize the sensor."""
        self._mac = mac
        mac_clean = mac.replace(":", "").lower()
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, mac_clean)},
            name=f"Stiga Mower {mac}",
            manufacturer="Stiga",
        )

class StigaBatterySensor(StigaMowerSensor):
    """Representation of the Stiga battery sensor."""

    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "%"

    def __init__(self, mac: str) -> None:
        """Initialize the battery sensor."""
        super().__init__(mac)
        mac_clean = mac.replace(":", "").lower()
        self._attr_unique_id = f"stiga_battery_{mac_clean}"
        self._attr_name = "Battery"
        self._attr_native_value = None

    def update_battery(self, level: int) -> None:
        """Update the battery level."""
        self._attr_native_value = level

class StigaStatusSensor(StigaMowerSensor):
    """Representation of the Stiga status sensor."""

    _attr_icon = "mdi:robot-mower"

    def __init__(self, mac: str) -> None:
        """Initialize the status sensor."""
        super().__init__(mac)
        mac_clean = mac.replace(":", "").lower()
        self._attr_unique_id = f"stiga_status_{mac_clean}"
        self._attr_name = "Status"
        self._attr_native_value = None

    def update_status(self, status: str) -> None:
        """Update the status string."""
        self._attr_native_value = status
