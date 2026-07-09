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
        StigaSpeedSensor(coordinator),
        StigaModeSensor(coordinator),
        StigaErrorSensor(coordinator),
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

class StigaSpeedSensor(StigaMowerSensor):
    """Representation of the Stiga speed sensor."""
    _attr_icon = "mdi:speedometer"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "RPM"

    def __init__(self, coordinator: StigaBLECoordinator) -> None:
        super().__init__(coordinator)
        mac_clean = self._mac.replace(":", "").lower()
        self._attr_unique_id = f"stiga_speed_{mac_clean}"
        self._attr_name = "Speed"

    @property
    def native_value(self) -> int | None:
        return self.coordinator.data.get("speed")

class StigaModeSensor(StigaMowerSensor):
    """Representation of the Stiga mode sensor."""
    _attr_icon = "mdi:leaf"

    def __init__(self, coordinator: StigaBLECoordinator) -> None:
        super().__init__(coordinator)
        mac_clean = self._mac.replace(":", "").lower()
        self._attr_unique_id = f"stiga_mode_{mac_clean}"
        self._attr_name = "Mode"

    @property
    def native_value(self) -> str | None:
        return self.coordinator.data.get("mode")

class StigaErrorSensor(StigaMowerSensor):
    """Representation of the Stiga error sensor."""
    _attr_icon = "mdi:alert-circle"

    def __init__(self, coordinator: StigaBLECoordinator) -> None:
        super().__init__(coordinator)
        mac_clean = self._mac.replace(":", "").lower()
        self._attr_unique_id = f"stiga_error_{mac_clean}"
        self._attr_name = "Error Status"

    @property
    def native_value(self) -> str | None:
        return self.coordinator.data.get("error")

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
