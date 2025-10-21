"""Constants for the Neptun Leak Protection integration."""
from __future__ import annotations

from typing import Final

# Integration domain
DOMAIN: Final = "neptun_leak_protection"

# Configuration
CONF_HOST: Final = "host"
CONF_PORT: Final = "port"
CONF_SCAN_INTERVAL: Final = "scan_interval"
CONF_DISCOVERY: Final = "discovery"

# Default values
DEFAULT_PORT: Final = 6350
DEFAULT_SCAN_INTERVAL: Final = 120  # Increased to 2 minutes for stability
DEFAULT_TIMEOUT: Final = 20  # Increased timeout
DEFAULT_PRE_CONNECT_DELAY: Final = 0.5  # Increased delay for stability
DEFAULT_POST_SEND_DELAY: Final = 0.2  # Increased delay
DEFAULT_RECEIVE_TIMEOUT: Final = 20.0  # Increased receive timeout
DEFAULT_CONNECTION_TIMEOUT: Final = 15.0  # Increased connection timeout
DEFAULT_VALVE_OPERATION_DELAY: Final = 20.0  # Increased valve operation delay
DEFAULT_RETRY_ATTEMPTS: Final = 5  # Increased retry attempts
DEFAULT_RETRY_DELAY: Final = 3.0  # Increased retry delay

# Protocol constants
PROTOCOL_HEADER: Final = bytes.fromhex("025451")
PACKET_SYSTEM_STATE: Final = 0x52  # Only working command - gets both device info and system state
PACKET_SET_SYSTEM_STATE: Final = 0x57
PACKET_SET_COUNTER_VALUE: Final = 0x58

# Response codes
RESPONSE_SUCCESS: Final = 0x025441
RESPONSE_UNKNOWN_COMMAND: Final = 0x025441FB
RESPONSE_CRC_ERROR: Final = 0x025441FE

# Device states
STATE_ON: Final = "on"
STATE_OFF: Final = "off"
STATE_OPEN: Final = "open"
STATE_CLOSED: Final = "closed"
STATE_ALARM: Final = "alarm"
STATE_NORMAL: Final = "normal"

# Attributes
ATTR_VALVE_STATE: Final = "valve_state"
ATTR_DRY_MODE: Final = "dry_mode"
ATTR_AUTO_CLOSE: Final = "auto_close"
ATTR_OPERATING_MODE: Final = "operating_mode"
ATTR_SENSOR_COUNT: Final = "sensor_count"
ATTR_COUNTER_VALUE: Final = "counter_value"
ATTR_BATTERY_LEVEL: Final = "battery_level"
ATTR_SIGNAL_STRENGTH: Final = "signal_strength"
ATTR_DEVICE_TYPE: Final = "device_type"
ATTR_FIRMWARE_VERSION: Final = "firmware_version"
ATTR_MAC_ADDRESS: Final = "mac_address"
ATTR_LINE_CONFIG: Final = "line_config"
ATTR_SENSOR_STATE: Final = "sensor_state"
ATTR_SENSOR_INDEX: Final = "sensor_index"
ATTR_SENSOR_FLAG: Final = "sensor_flag"

# Device classes
DEVICE_CLASS_LEAK: Final = "moisture"
DEVICE_CLASS_WATER: Final = "water"
DEVICE_CLASS_BATTERY: Final = "battery"

# Entity categories
ENTITY_CATEGORY_DIAGNOSTIC: Final = "diagnostic"
ENTITY_CATEGORY_CONFIG: Final = "config"

# Error codes
ERROR_CANNOT_CONNECT: Final = "cannot_connect"
ERROR_INVALID_HOST: Final = "invalid_host"
ERROR_TIMEOUT: Final = "timeout"
ERROR_UNKNOWN: Final = "unknown"

# Platforms
PLATFORMS: Final = ["binary_sensor", "sensor", "switch"]
