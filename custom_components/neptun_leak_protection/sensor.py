"""Sensor platform for Neptun Leak Protection."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfVolume,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import NeptunCoordinator
from .const import (
    ATTR_BATTERY_LEVEL,
    ATTR_SIGNAL_STRENGTH,
    DOMAIN,
    ENTITY_CATEGORY_DIAGNOSTIC,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor entities."""
    coordinator: NeptunCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = []
    
    # System state sensors
    entities.append(NeptunSystemStateSensor(coordinator))
    
    # Wireless sensor sensors (battery, signal, state)
    for i in range(1, 4):  # Sensors 1, 2, 3
        entities.append(NeptunWirelessSensorSensor(coordinator, i))
        entities.append(NeptunWirelessBatterySensor(coordinator, i))
        entities.append(NeptunWirelessSignalSensor(coordinator, i))
    
    # Counter sensors (for wired lines in counter mode)
    for i in range(1, 5):  # Lines 1, 2, 3, 4
        entities.append(NeptunCounterSensor(coordinator, i))

    async_add_entities(entities, True)


class NeptunSensorEntity(CoordinatorEntity, SensorEntity):
    """Base class for Neptun sensors."""

    def __init__(self, coordinator: NeptunCoordinator, sensor_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._sensor_id = sensor_id
        self._attr_has_entity_name = True

    @property
    def device_info(self) -> Dict[str, Any]:
        """Return device information."""
        return self.coordinator.device.get_device_info_dict()

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.available


class NeptunSystemStateSensor(NeptunSensorEntity):
    """System state sensor."""

    def __init__(self, coordinator: NeptunCoordinator) -> None:
        """Initialize the system state sensor."""
        super().__init__(coordinator, "system_state")
        self._attr_name = "System State"
        self._attr_unique_id = f"{coordinator.device.host}_system_state"
        self._attr_icon = "mdi:information"

    @property
    def native_value(self) -> Optional[str]:
        """Return the system state."""
        if not self.coordinator.data:
            return None
        
        system_state = self.coordinator.data.get("system_state", {})
        valve_open = system_state.get("valve_open", False)
        dry_mode = system_state.get("dry_mode", False)
        auto_close = system_state.get("auto_close", False)
        
        if dry_mode:
            return "Dry Mode"
        elif auto_close:
            return "Auto Close Enabled"
        elif valve_open:
            return "Normal (Valves Open)"
        else:
            return "Normal (Valves Closed)"

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return extra state attributes."""
        if not self.coordinator.data:
            return {}
        
        system_state = self.coordinator.data.get("system_state", {})
        return {
            "valve_open": system_state.get("valve_open", False),
            "dry_mode": system_state.get("dry_mode", False),
            "auto_close": system_state.get("auto_close", False),
            "sensor_1_state": system_state.get("sensor_1_state", 0),
            "sensor_2_state": system_state.get("sensor_2_state", 0),
            "sensor_3_state": system_state.get("sensor_3_state", 0),
        }


class NeptunWirelessSensorSensor(NeptunSensorEntity):
    """Wireless sensor state sensor."""

    def __init__(self, coordinator: NeptunCoordinator, sensor_number: int) -> None:
        """Initialize the wireless sensor state sensor."""
        super().__init__(coordinator, f"sensor_{sensor_number}")
        self._sensor_number = sensor_number
        self._attr_name = f"Wireless Sensor {sensor_number}"
        self._attr_unique_id = f"{coordinator.device.host}_sensor_{sensor_number}"
        self._attr_icon = "mdi:water"

    @property
    def native_value(self) -> Optional[str]:
        """Return the sensor state."""
        if not self.coordinator.data:
            return None
        
        system_state = self.coordinator.data.get("system_state", {})
        state = system_state.get(f"sensor_{self._sensor_number}_state", 0)
        
        if state == 0x00:
            return "Disconnected"
        elif state == 0x02:
            return "Triggered"
        elif state == 0x03:
            return "Normal"
        else:
            return "Unknown"

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return extra state attributes."""
        if not self.coordinator.data:
            return {}
        
        system_state = self.coordinator.data.get("system_state", {})
        return {
            "sensor_number": self._sensor_number,
            "raw_state": system_state.get(f"sensor_{self._sensor_number}_state", 0),
            "battery_level": system_state.get(f"sensor_{self._sensor_number}_battery", 0),
            "flag": system_state.get(f"sensor_{self._sensor_number}_flag", 0),
        }


class NeptunCounterSensor(NeptunSensorEntity):
    """Counter sensor for wired lines."""

    def __init__(self, coordinator: NeptunCoordinator, line_number: int) -> None:
        """Initialize the counter sensor."""
        super().__init__(coordinator, f"counter_{line_number}")
        self._line_number = line_number
        self._attr_name = f"Counter Line {line_number}"
        self._attr_unique_id = f"{coordinator.device.host}_counter_{line_number}"
        self._attr_icon = "mdi:counter"

    @property
    def native_value(self) -> Optional[int]:
        """Return the counter data."""
        if not self.coordinator.data:
            return None
        
        system_state = self.coordinator.data.get("system_state", {})
        return system_state.get(f"counter_{self._line_number}_data", 0)

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return extra state attributes."""
        if not self.coordinator.data:
            return {}
        
        system_state = self.coordinator.data.get("system_state", {})
        return {
            "line_number": self._line_number,
            "raw_data": system_state.get(f"counter_{self._line_number}_data", 0),
        }


class NeptunWirelessBatterySensor(NeptunSensorEntity):
    """Wireless sensor battery level."""

    def __init__(self, coordinator: NeptunCoordinator, sensor_number: int) -> None:
        """Initialize the battery sensor."""
        super().__init__(coordinator, f"sensor_{sensor_number}_battery")
        self._sensor_number = sensor_number
        self._attr_device_class = SensorDeviceClass.BATTERY
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        
        self._attr_name = f"Wireless Sensor {sensor_number} Battery"
        self._attr_unique_id = f"{coordinator.device.host}_sensor_{sensor_number}_battery"

    @property
    def native_value(self) -> Optional[int]:
        """Return the battery level."""
        if not self.coordinator.data:
            return None
        
        system_state = self.coordinator.data.get("system_state", {})
        battery = system_state.get(f"sensor_{self._sensor_number}_battery", 0)
        
        # Convert battery level using signed 8-bit interpretation
        # Position mapping: sensor_1=53, sensor_2=57, sensor_3=61
        import struct
        battery_signed = struct.unpack('b', bytes([battery]))[0]
        
        # Handle negative values (like 0xD6 = -42, which means 42%)
        if battery_signed < 0:
            # Convert negative to positive (e.g., -42 -> 42)
            return abs(battery_signed)
        else:
            return battery_signed

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return extra state attributes."""
        if not self.coordinator.data:
            return {}
        
        system_state = self.coordinator.data.get("system_state", {})
        return {
            "sensor_number": self._sensor_number,
            "raw_battery": system_state.get(f"sensor_{self._sensor_number}_battery", 0),
        }


class NeptunWirelessSignalSensor(NeptunSensorEntity):
    """Wireless sensor signal state (0=no signal, 1=good signal)."""

    def __init__(self, coordinator: NeptunCoordinator, sensor_number: int) -> None:
        """Initialize the signal sensor."""
        super().__init__(coordinator, f"sensor_{sensor_number}_signal")
        self._sensor_number = sensor_number
        # No device_class for signal state (0/1)
        self._attr_state_class = SensorStateClass.MEASUREMENT
        # No unit of measurement for signal state
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        
        self._attr_name = f"Wireless Sensor {sensor_number} Signal State"
        self._attr_unique_id = f"{coordinator.device.host}_sensor_{sensor_number}_signal"

    @property
    def native_value(self) -> Optional[int]:
        """Return the signal state (0=no signal, 1=good signal)."""
        if not self.coordinator.data:
            return None
        
        system_state = self.coordinator.data.get("system_state", {})
        state = system_state.get(f"sensor_{self._sensor_number}_state", 0)
        
        # Convert signal strength (0x02 = 2/4, 0x03 = 3/4)
        if state == 0x02:
            return 50  # 2/4 = 50%
        elif state == 0x03:
            return 75  # 3/4 = 75%
        else:
            return 0

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return extra state attributes."""
        if not self.coordinator.data:
            return {}
        
        system_state = self.coordinator.data.get("system_state", {})
        return {
            "sensor_number": self._sensor_number,
            "raw_state": system_state.get(f"sensor_{self._sensor_number}_state", 0),
            "signal_level": f"{system_state.get(f'sensor_{self._sensor_number}_state', 0)}/4",
        }
