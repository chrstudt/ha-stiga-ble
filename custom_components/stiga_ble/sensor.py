"""Sensor platform for Stiga BLE integration."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, LOGGER
from .coordinator import StigaBLECoordinator

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Stiga BLE sensors from a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: StigaBLECoordinator = data["coordinator"]

    async_add_entities([
        StigaBatterySensor(coordinator),
        StigaStatusSensor(coordinator),
        StigaTriggerSensor(coordinator),
        StigaBatteryCapacitySensor(coordinator),
        StigaBatteryVoltageSensor(coordinator),
        StigaBatteryCyclesSensor(coordinator),
        StigaRemainingTimeSensor(coordinator),
        StigaRawSensor(coordinator),
    ])

class StigaMowerSensor(CoordinatorEntity, SensorEntity):
    """Base class for Stiga BLE sensors."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: StigaBLECoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.coordinator = coordinator
        self._mac = coordinator.mac
        mac_clean = self._mac.replace(":", "").lower()
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, mac_clean)},
            name=f"Stiga Mower {self._mac}",
            manufacturer="Stiga",
        )

class StigaBatterySensor(StigaMowerSensor):
    """Representation of the Stiga battery sensor."""
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "%"

    def __init__(self, coordinator: StigaBLECoordinator) -> None:
        super().__init__(coordinator)
        mac_clean = self._mac.replace(":", "").lower()
        self._attr_unique_id = f"stiga_battery_{mac_clean}"
        self._attr_name = "Battery"

    @property
    def native_value(self) -> int | None:
        return self.coordinator.data.get("battery")

class StigaStatusSensor(StigaMowerSensor):
    """Representation of the Stiga status sensor."""
    _attr_icon = "mdi:robot-mower"

    def __init__(self, coordinator: StigaBLECoordinator) -> None:
        super().__init__(coordinator)
        mac_clean = self._mac.replace(":", "").lower()
        self._attr_unique_id = f"stiga_status_{mac_clean}"
        self._attr_name = "Status"

    @property
    def native_value(self) -> str | None:
        return self.coordinator.data.get("status")

class StigaTriggerSensor(StigaMowerSensor):
    """Representation of the Stiga trigger sensor."""
    _attr_icon = "mdi:robot"

    def __init__(self, coordinator: StigaBLECoordinator) -> None:
        super().__init__(coordinator)
        mac_clean = self._mac.replace(":", "").lower()
        self._attr_unique_id = f"stiga_trigger_{mac_clean}"
        self._attr_name = "Trigger Mode"

    @property
    def native_value(self) -> str | None:
        val = self.coordinator.data.get("automatic_trigger")
        if val is None:
            return None
        return "Automatic" if val else "Manual"

class StigaBatteryCapacitySensor(StigaMowerSensor):
    """Representation of the Stiga battery capacity sensor."""
    _attr_icon = "mdi:battery-high"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "mAh"

    def __init__(self, coordinator: StigaBLECoordinator) -> None:
        super().__init__(coordinator)
        mac_clean = self._mac.replace(":", "").lower()
        self._attr_unique_id = f"stiga_battery_capacity_{mac_clean}"
        self._attr_name = "Battery Capacity"

    @property
    def native_value(self) -> int | None:
        return self.coordinator.data.get("battery_capacity")

class StigaBatteryVoltageSensor(StigaMowerSensor):
    """Representation of the Stiga battery voltage sensor."""
    _attr_device_class = SensorDeviceClass.VOLTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "V"

    def __init__(self, coordinator: StigaBLECoordinator) -> None:
        super().__init__(coordinator)
        mac_clean = self._mac.replace(":", "").lower()
        self._attr_unique_id = f"stiga_battery_voltage_{mac_clean}"
        self._attr_name = "Battery Voltage"

    @property
    def native_value(self) -> float | None:
        return self.coordinator.data.get("battery_voltage")

class StigaBatteryCyclesSensor(StigaMowerSensor):
    """Representation of the Stiga battery cycles sensor."""
    _attr_icon = "mdi:battery-sync"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "cycles"

    def __init__(self, coordinator: StigaBLECoordinator) -> None:
        super().__init__(coordinator)
        mac_clean = self._mac.replace(":", "").lower()
        self._attr_unique_id = f"stiga_battery_cycles_{mac_clean}"
        self._attr_name = "Battery Cycles"

    @property
    def native_value(self) -> int | None:
        return self.coordinator.data.get("battery_cycles")

class StigaRemainingTimeSensor(StigaMowerSensor):
    """Representation of the Stiga remaining time sensor."""
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "s"

    def __init__(self, coordinator: StigaBLECoordinator) -> None:
        super().__init__(coordinator)
        mac_clean = self._mac.replace(":", "").lower()
        self._attr_unique_id = f"stiga_remaining_time_{mac_clean}"
        self._attr_name = "Remaining Time"

    @property
    def native_value(self) -> float | None:
        return self.coordinator.data.get("remaining_time")

class StigaRawSensor(StigaMowerSensor):
    """Representation of the Stiga raw debug sensor."""
    _attr_icon = "mdi:bluetooth"

    def __init__(self, coordinator: StigaBLECoordinator) -> None:
        super().__init__(coordinator)
        mac_clean = self._mac.replace(":", "").lower()
        self._attr_unique_id = f"stiga_raw_{mac_clean}"
        self._attr_name = "Raw BLE Data"

    @property
    def native_value(self) -> str | None:
        return self.coordinator.data.get("raw_rx")
