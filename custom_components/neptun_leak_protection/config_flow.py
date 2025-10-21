"""Config flow for Neptun Leak Protection integration."""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv

from .const import (
    CONF_DISCOVERY,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    ERROR_CANNOT_CONNECT,
    ERROR_INVALID_HOST,
    ERROR_TIMEOUT,
    ERROR_UNKNOWN,
)
from .protocol import NeptunDevice

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): cv.positive_int,
        vol.Optional(CONF_DISCOVERY, default=True): cv.boolean,
    }
)


async def validate_input(hass: HomeAssistant, data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    host = data[CONF_HOST]
    port = data[CONF_PORT]

    device = NeptunDevice(host, port)
    
    try:
        # Try to connect and get basic system state
        success = await device.get_system_state()
        if not success:
            raise ValueError("Cannot connect to device")
        
        # Get device info for unique ID
        device_info = device.get_device_info()
        
        return {
            "title": device_info.get("name", f"Equation Device {host}"),
            "device_info": device_info,
            "host": host,
            "port": port,
        }
        
    except asyncio.TimeoutError:
        raise ValueError("timeout")
    except OSError:
        raise ValueError("cannot_connect")
    except Exception as err:
        _LOGGER.exception("Unexpected exception: %s", err)
        raise ValueError("unknown")


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Neptun Leak Protection."""

    VERSION = 1

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except ValueError as err:
                if str(err) == "cannot_connect":
                    errors["base"] = ERROR_CANNOT_CONNECT
                elif str(err) == "timeout":
                    errors["base"] = ERROR_TIMEOUT
                elif str(err) == "invalid_host":
                    errors["base"] = ERROR_INVALID_HOST
                else:
                    errors["base"] = ERROR_UNKNOWN
            else:
                # Create unique ID based on host
                await self.async_set_unique_id(user_input[CONF_HOST])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=info["title"],
                    data={
                        CONF_HOST: user_input[CONF_HOST],
                        CONF_PORT: user_input[CONF_PORT],
                        CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL],
                        CONF_DISCOVERY: user_input[CONF_DISCOVERY],
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_zeroconf(
        self, discovery_info: Dict[str, Any]
    ) -> FlowResult:
        """Handle zeroconf discovery."""
        host = discovery_info.get("host")
        port = discovery_info.get("port", DEFAULT_PORT)
        
        if not host:
            return self.async_abort(reason="invalid_discovery_info")

        # Set unique ID to prevent duplicate entries
        await self.async_set_unique_id(host)
        self._abort_if_unique_id_configured()

        # Try to connect to validate the device
        try:
            device = NeptunDevice(host, port)
            success = await device.get_system_state()
            if not success:
                return self.async_abort(reason="cannot_connect")
                
            device_info = device.get_device_info()
            
        except Exception:
            return self.async_abort(reason="cannot_connect")

        self.context.update({
            "title_placeholders": {
                "name": device_info.get("name", f"Equation Device {host}"),
                "host": host,
            }
        })

        return await self.async_step_zeroconf_confirm()

    async def async_step_zeroconf_confirm(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Confirm discovery."""
        if user_input is not None:
            host = self.context["title_placeholders"]["host"]
            
            return self.async_create_entry(
                title=self.context["title_placeholders"]["name"],
                data={
                    CONF_HOST: host,
                    CONF_PORT: DEFAULT_PORT,
                    CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
                    CONF_DISCOVERY: True,
                },
            )

        return self.async_show_form(
            step_id="zeroconf_confirm",
            description_placeholders=self.context["title_placeholders"],
        )

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> OptionsFlowHandler:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=self.config_entry.options.get(
                            CONF_SCAN_INTERVAL,
                            self.config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
                        ),
                    ): cv.positive_int,
                    vol.Optional(
                        CONF_DISCOVERY,
                        default=self.config_entry.options.get(
                            CONF_DISCOVERY,
                            self.config_entry.data.get(CONF_DISCOVERY, True)
                        ),
                    ): cv.boolean,
                }
            ),
        )
