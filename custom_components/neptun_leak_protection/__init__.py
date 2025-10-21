"""The Neptun Leak Protection integration."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN, PLATFORMS
from .protocol import NeptunDevice

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Equation Leak Protection from a config entry."""
    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]
    scan_interval = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    device = NeptunDevice(host, port)
    coordinator = NeptunCoordinator(hass, device, scan_interval)

    # Initial data fetch
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Set up options update listener
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


class NeptunCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the Neptun device."""

    def __init__(
        self, 
        hass: HomeAssistant, 
        device: NeptunDevice, 
        scan_interval: int
    ) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        self.device = device
        self._available = True

    @property
    def available(self) -> bool:
        """Return if device is available."""
        return self._available and self.device.is_online()

    async def _async_update_data(self) -> dict:
        """Fetch data from device."""
        try:
            success = await self.device.update_all()
            if not success:
                self._available = False
                raise UpdateFailed("Failed to communicate with device")
            
            self._available = True
            
            # Return combined data
            return {
                "device_info": self.device.get_device_info_dict(),
                "system_state": self.device.system_state,
                "sensors": self.device.sensors,
                "counters": self.device.counters,
                "last_update": self.device.last_update,
            }
            
        except Exception as err:
            self._available = False
            raise UpdateFailed(f"Error communicating with device: {err}")

    async def async_set_valve_state(self, open_valve: bool) -> bool:
        """Set valve state."""
        try:
            success = await self.device.set_valve_state(open_valve)
            if success:
                # Trigger immediate update
                await self.async_request_refresh()
            return success
        except Exception as err:
            _LOGGER.error("Error setting valve state: %s", err)
            return False

    async def async_set_dry_mode(self, dry_mode: bool) -> bool:
        """Set dry mode."""
        try:
            success = await self.device.set_dry_mode(dry_mode)
            if success:
                # Trigger immediate update
                await self.async_request_refresh()
            return success
        except Exception as err:
            _LOGGER.error("Error setting dry mode: %s", err)
            return False

    async def async_set_auto_close(self, auto_close: bool) -> bool:
        """Set auto-close mode."""
        try:
            success = await self.device.set_auto_close(auto_close)
            if success:
                # Trigger immediate update
                await self.async_request_refresh()
            return success
        except Exception as err:
            _LOGGER.error("Error setting auto-close mode: %s", err)
            return False

    async def async_set_line_mode(self, line_number: int, counter_mode: bool) -> bool:
        """Set line mode (sensor or counter)."""
        try:
            success = await self.device.set_line_mode(line_number, counter_mode)
            if success:
                # Trigger immediate update
                await self.async_request_refresh()
            return success
        except Exception as err:
            _LOGGER.error("Error setting line mode: %s", err)
            return False

    async def async_set_counter_value(self, line_number: int, value: int) -> bool:
        """Set counter value for a specific line."""
        try:
            success = await self.device.set_counter_value(line_number, value)
            if success:
                # Trigger immediate update
                await self.async_request_refresh()
            return success
        except Exception as err:
            _LOGGER.error("Error setting counter value: %s", err)
            return False
