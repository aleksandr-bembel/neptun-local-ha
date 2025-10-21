"""Switch platform for Neptun Leak Protection."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import NeptunCoordinator
from .const import (
    DOMAIN,
    ENTITY_CATEGORY_CONFIG,
    STATE_ON,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up switch entities."""
    coordinator: NeptunCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = [
        NeptunValveSwitch(coordinator),
        NeptunDryModeSwitch(coordinator),
        NeptunAutoCloseSwitch(coordinator),
    ]

    async_add_entities(entities, True)


class NeptunSwitchEntity(CoordinatorEntity, SwitchEntity):
    """Base class for Neptun switches."""

    def __init__(self, coordinator: NeptunCoordinator, switch_id: str) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._switch_id = switch_id
        self._attr_has_entity_name = True

    @property
    def device_info(self) -> Dict[str, Any]:
        """Return device information."""
        return self.coordinator.device.get_device_info_dict()

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.available


class NeptunValveSwitch(NeptunSwitchEntity):
    """Main water valve switch."""

    def __init__(self, coordinator: NeptunCoordinator) -> None:
        """Initialize the valve switch."""
        super().__init__(coordinator, "valve")
        self._attr_name = "Main Valve"
        self._attr_unique_id = f"{coordinator.device.host}_valve"
        self._attr_icon = "mdi:valve"

    @property
    def is_on(self) -> bool:
        """Return true if valve is open."""
        if not self.coordinator.data:
            return False
        
        system_state = self.coordinator.data.get("system_state", {})
        return system_state.get("valve_open", False)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the valve (open)."""
        success = await self.coordinator.async_set_valve_state(True)
        if not success:
            _LOGGER.error("Failed to open valve")

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the valve (close)."""
        success = await self.coordinator.async_set_valve_state(False)
        if not success:
            _LOGGER.error("Failed to close valve")

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return extra state attributes."""
        if not self.coordinator.data:
            return {}
        
        system_state = self.coordinator.data.get("system_state", {})
        return {
            "valve_state": "open" if system_state.get("valve_open", False) else "closed",
            "sensor_count": system_state.get("sensor_count", 0),
            "relay_count": system_state.get("relay_count", 0),
        }


class NeptunDryModeSwitch(NeptunSwitchEntity):
    """Dry mode (cleaning mode) switch."""

    def __init__(self, coordinator: NeptunCoordinator) -> None:
        """Initialize the dry mode switch."""
        super().__init__(coordinator, "dry_mode")
        self._attr_name = "Dry Mode"
        self._attr_unique_id = f"{coordinator.device.host}_dry_mode"
        self._attr_icon = "mdi:broom"
        self._attr_entity_category = EntityCategory.CONFIG

    @property
    def is_on(self) -> bool:
        """Return true if dry mode is enabled."""
        if not self.coordinator.data:
            return False
        
        system_state = self.coordinator.data.get("system_state", {})
        return system_state.get("dry_mode", False)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on dry mode."""
        success = await self.coordinator.async_set_dry_mode(True)
        if not success:
            _LOGGER.error("Failed to enable dry mode")

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off dry mode."""
        success = await self.coordinator.async_set_dry_mode(False)
        if not success:
            _LOGGER.error("Failed to disable dry mode")

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return extra state attributes."""
        if not self.coordinator.data:
            return {}
        
        system_state = self.coordinator.data.get("system_state", {})
        return {
            "dry_mode": system_state.get("dry_mode", False),
            "description": "Cleaning mode - ignores sensor alarms",
        }


class NeptunAutoCloseSwitch(NeptunSwitchEntity):
    """Auto-close mode switch."""

    def __init__(self, coordinator: NeptunCoordinator) -> None:
        """Initialize the auto-close switch."""
        super().__init__(coordinator, "auto_close")
        self._attr_name = "Auto Close"
        self._attr_unique_id = f"{coordinator.device.host}_auto_close"
        self._attr_icon = "mdi:shield-alert"
        self._attr_entity_category = EntityCategory.CONFIG

    @property
    def is_on(self) -> bool:
        """Return true if auto-close is enabled."""
        if not self.coordinator.data:
            return False
        
        system_state = self.coordinator.data.get("system_state", {})
        return system_state.get("auto_close", False)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on auto-close mode."""
        success = await self.coordinator.async_set_auto_close(True)
        if not success:
            _LOGGER.error("Failed to enable auto-close mode")

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off auto-close mode."""
        success = await self.coordinator.async_set_auto_close(False)
        if not success:
            _LOGGER.error("Failed to disable auto-close mode")

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return extra state attributes."""
        if not self.coordinator.data:
            return {}
        
        system_state = self.coordinator.data.get("system_state", {})
        return {
            "auto_close": system_state.get("auto_close", False),
            "description": "Automatically close valves when wireless sensors are lost",
        }
