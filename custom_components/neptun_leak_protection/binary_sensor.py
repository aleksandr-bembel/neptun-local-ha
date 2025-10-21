"""Binary sensor platform for Neptun Leak Protection."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import NeptunCoordinator
from .const import (
    ATTR_BATTERY_LEVEL,
    ATTR_SIGNAL_STRENGTH,
    DOMAIN,
    ENTITY_CATEGORY_DIAGNOSTIC,
    STATE_ON,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensor entities."""
    coordinator: NeptunCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = []
    
    # System alarm sensor
    entities.append(NeptunAlarmSensor(coordinator))
    
    # Wireless leak sensors (3 sensors)
    for i in range(1, 4):  # Sensors 1, 2, 3
        entities.append(NeptunWirelessLeakSensor(coordinator, i))

    async_add_entities(entities, True)


class NeptunBinarySensorEntity(CoordinatorEntity, BinarySensorEntity):
    """Base class for Neptun binary sensors."""

    def __init__(self, coordinator: NeptunCoordinator, sensor_id: str) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._sensor_id = sensor_id
        self._attr_has_entity_name = True

    @property
    def device_info(self) -> Dict[str, Any]:
        """Return device information."""
        return self.coordinator.device.get_device_info()

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.available


class NeptunAlarmSensor(NeptunBinarySensorEntity):
    """System alarm binary sensor."""

    def __init__(self, coordinator: NeptunCoordinator) -> None:
        """Initialize the alarm sensor."""
        super().__init__(coordinator, "alarm")
        self._attr_name = "System Alarm"
        self._attr_device_class = BinarySensorDeviceClass.PROBLEM
        self._attr_unique_id = f"{coordinator.device.host}_alarm"

    @property
    def is_on(self) -> bool:
        """Return true if alarm is active."""
        if not self.coordinator.data:
            return False
        
        system_state = self.coordinator.data.get("system_state", {})
        
        # Check if any sensor is triggered or disconnected
        for i in range(1, 4):  # Sensors 1, 2, 3
            state = system_state.get(f"sensor_{i}_state", 0)
            if state == 0x02:  # Triggered
                return True
            elif state == 0x00:  # Disconnected
                return True
        
        return False

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return extra state attributes."""
        if not self.coordinator.data:
            return {}
        
        system_state = self.coordinator.data.get("system_state", {})
        return {
            "sensor_1_state": system_state.get("sensor_1_state", 0),
            "sensor_2_state": system_state.get("sensor_2_state", 0),
            "sensor_3_state": system_state.get("sensor_3_state", 0),
            "valve_open": system_state.get("valve_open", False),
            "dry_mode": system_state.get("dry_mode", False),
            "auto_close": system_state.get("auto_close", False),
        }


class NeptunWirelessLeakSensor(NeptunBinarySensorEntity):
    """Wireless leak sensor."""

    def __init__(self, coordinator: NeptunCoordinator, sensor_number: int) -> None:
        """Initialize the wireless leak sensor."""
        super().__init__(coordinator, f"sensor_{sensor_number}")
        self._sensor_number = sensor_number
        self._attr_device_class = BinarySensorDeviceClass.MOISTURE
        
        self._attr_name = f"Wireless Sensor {sensor_number}"
        self._attr_unique_id = f"{coordinator.device.host}_sensor_{sensor_number}"

    @property
    def is_on(self) -> bool:
        """Return true if leak is detected."""
        if not self.coordinator.data:
            return False
        
        system_state = self.coordinator.data.get("system_state", {})
        state = system_state.get(f"sensor_{self._sensor_number}_state", 0)
        
        # State 0x02 means triggered (leak detected)
        return state == 0x02

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
            "state_description": self._get_state_description(system_state.get(f"sensor_{self._sensor_number}_state", 0)),
        }

    def _get_state_description(self, state: int) -> str:
        """Get human-readable state description."""
        if state == 0x00:
            return "Disconnected"
        elif state == 0x02:
            return "Triggered (Leak Detected)"
        elif state == 0x03:
            return "Normal"
        else:
            return "Unknown"
