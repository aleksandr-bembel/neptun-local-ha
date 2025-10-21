"""Protocol client for Neptun N4106 leak protection devices."""
from __future__ import annotations

import asyncio
import logging
import socket
import struct
from datetime import datetime
from typing import Any, Dict, List, Optional

from .const import (
    DEFAULT_PORT,
    DEFAULT_TIMEOUT,
    DEFAULT_PRE_CONNECT_DELAY,
    DEFAULT_POST_SEND_DELAY,
    DEFAULT_RECEIVE_TIMEOUT,
    DEFAULT_CONNECTION_TIMEOUT,
    DEFAULT_VALVE_OPERATION_DELAY,
    DEFAULT_RETRY_ATTEMPTS,
    DEFAULT_RETRY_DELAY,
    PACKET_DEVICE_INFO,
    PACKET_SYSTEM_STATE,
    PACKET_SET_SYSTEM_STATE,
    PACKET_SET_COUNTER_VALUE,
    PROTOCOL_HEADER,
    RESPONSE_SUCCESS,
    RESPONSE_UNKNOWN_COMMAND,
    RESPONSE_CRC_ERROR,
    STATE_OFF,
    STATE_ON,
)

_LOGGER = logging.getLogger(__name__)


def crc16(data: bytes) -> tuple[int, int]:
    """Calculate CRC16-CCITT checksum using the correct algorithm from neptun2mqtt."""
    polynom = 0x1021
    crc16ret = 0xFFFF
    
    for byte_val in data:
        crc16ret ^= byte_val << 8
        crc16ret &= 0xFFFF
        for _ in range(8):
            if (crc16ret & 0x8000):
                crc16ret = (crc16ret << 1) ^ polynom
            else:
                crc16ret = crc16ret << 1
            crc16ret &= 0xFFFF
    
    crc_hi = (crc16ret >> 8) & 0xFF
    crc_lo = crc16ret & 0xFF
    return crc_hi, crc_lo


def create_command(command_code: int, data_payload: bytes = b'') -> bytes:
    """Create command packet with CRC."""
    # Command structure: 0x02 0x54 0x51 [COMMAND] [LEN_HI] [LEN_LO] [DATA] [CRC_HI] [CRC_LO]
    command_bytes = bytearray([0x02, 0x54, 0x51, command_code])
    
    # Add length (2 bytes, big-endian)
    length = len(data_payload)
    command_bytes.extend(length.to_bytes(2, 'big'))
    
    # Add data payload
    command_bytes.extend(data_payload)
    
    # Calculate and add CRC
    crc_hi, crc_lo = crc16(command_bytes)
    command_bytes.append(crc_hi)
    command_bytes.append(crc_lo)
    
    return bytes(command_bytes)


def create_control_command(
    valve_state_open: bool = False,
    flag_dry: bool = False,
    flag_cl_valve: bool = False,
    line_in_config: int = 0x00
) -> bytes:
    """Create control command (0x57) for system settings."""
    # Data payload: 0x53 0x00 0x04 [valve_state_open] [flag_dry] [flag_cl_valve] [line_in_config]
    data_payload = bytearray([0x53, 0x00, 0x04, 0x00, 0x00, 0x00, 0x00])
    
    if valve_state_open:
        data_payload[3] = 1
    if flag_dry:
        data_payload[4] = 1
    if flag_cl_valve:
        data_payload[5] = 1
    data_payload[6] = line_in_config
    
    return create_command(PACKET_SET_SYSTEM_STATE, data_payload)


def create_counter_command(line_number: int, counter_value: int) -> bytes:
    """Create counter value command (0x58) for setting counter values."""
    # Data payload: 0x53 0x00 0x04 [line_number] [0x00] [0x00] [0x00] [value_32bit_le]
    data_payload = bytearray([0x53, 0x00, 0x04, line_number, 0x00, 0x00, 0x00])
    data_payload.extend(counter_value.to_bytes(4, 'little'))
    
    return create_command(PACKET_SET_COUNTER_VALUE, data_payload)


class NeptunDevice:
    """Represents a Neptun N4106 device."""
    
    def __init__(self, host: str, port: int = DEFAULT_PORT):
        """Initialize device."""
        self.host = host
        self.port = port
        self.device_info: Dict[str, Any] = {}
        self.sensors: Dict[str, Any] = {}
        self.counters: Dict[str, Any] = {}
        self.system_state: Dict[str, Any] = {}
        self.last_update: Optional[datetime] = None
        self._lock = asyncio.Lock()

    def _calculate_crc16_ccitt(self, data: bytes) -> int:
        """Calculate CRC16-CCITT checksum for data."""
        return crc16(data)[0] << 8 | crc16(data)[1]

    async def send_command_with_retries(
        self, 
        command: bytes, 
        timeout: float = DEFAULT_RECEIVE_TIMEOUT,
        max_retries: int = DEFAULT_RETRY_ATTEMPTS,
        retry_delay: float = DEFAULT_RETRY_DELAY
    ) -> tuple[Optional[bytes], int]:
        """Send command with retry logic."""
        for attempt in range(max_retries):
            try:
                _LOGGER.debug("Sending command to %s:%d (attempt %d/%d)", self.host, self.port, attempt + 1, max_retries)
                response = await self._send_command(command, timeout)
                if response:
                    _LOGGER.debug("Command successful on attempt %d, received %d bytes", attempt + 1, len(response))
                    return response, attempt + 1
                
                _LOGGER.warning("Command returned no response on attempt %d/%d", attempt + 1, max_retries)
                if attempt < max_retries - 1:
                    _LOGGER.debug("Retrying in %s seconds", retry_delay)
                    await asyncio.sleep(retry_delay)
                    
            except Exception as e:
                _LOGGER.error("Command failed on attempt %d/%d: %s", attempt + 1, max_retries, e)
                if attempt < max_retries - 1:
                    _LOGGER.debug("Retrying in %s seconds", retry_delay)
                    await asyncio.sleep(retry_delay)
        
        return None, max_retries

    async def _send_command(self, command: bytes, timeout: float) -> Optional[bytes]:
        """Send command to device with optimal timing."""
        try:
            # Pre-connect delay for stability
            await asyncio.sleep(DEFAULT_PRE_CONNECT_DELAY)
            
            _LOGGER.debug("Connecting to %s:%d with timeout %s", self.host, self.port, DEFAULT_CONNECTION_TIMEOUT)
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port),
                timeout=DEFAULT_CONNECTION_TIMEOUT
            )
            _LOGGER.debug("Connected successfully, sending %d bytes", len(command))
            
            writer.write(command)
            await writer.drain()
            
            # Post-send delay for stability
            await asyncio.sleep(DEFAULT_POST_SEND_DELAY)
            
            # Wait for response
            response = await asyncio.wait_for(
                reader.read(1024),
                timeout=timeout
            )
            
            writer.close()
            await writer.wait_closed()
            
            return response
            
        except asyncio.TimeoutError as err:
            _LOGGER.error("Timeout communicating with device %s:%d - %s", self.host, self.port, err)
            return None
        except OSError as err:
            _LOGGER.error("Network error communicating with device %s:%d - %s (errno: %s)", self.host, self.port, err, getattr(err, 'errno', 'unknown'))
            return None
        except Exception as err:
            _LOGGER.error("Unexpected error communicating with device %s:%d - %s", self.host, self.port, err)
            return None

    def _parse_system_state(self, data: bytes) -> None:
        """Parse system state response according to our documentation."""
        if len(data) < 112:  # Expected minimum length
            _LOGGER.warning("System state response too short: %d bytes", len(data))
            return
        
        # Parse key bytes according to our analysis
        self.system_state.update({
            # Byte 41: Valve state (0x01 = open, 0x00 = closed)
            "valve_open": data[41] == 0x01,
            
            # Byte 46: Operating mode (0x0F = dry mode, 0x00 = normal)
            "dry_mode": data[46] == 0x0F,
            
            # Byte 47: Auto-close flag (0x08 = enabled, 0x00 = disabled)
            "auto_close": data[47] == 0x08,
            
            # Bytes 51, 55, 59: Sensor states (0x00=disconnected, 0x02=triggered, 0x03=normal)
            "sensor_1_state": data[51],
            "sensor_2_state": data[55], 
            "sensor_3_state": data[59],
            
            # Bytes 53, 57, 61: Battery levels (signed 8-bit interpretation)
            "sensor_1_battery": data[53],
            "sensor_2_battery": data[57],
            "sensor_3_battery": data[61],
            
            # Bytes 54, 58, 62: Signal levels (0=no signal, 1=good signal)
            "sensor_1_signal": data[54],
            "sensor_2_signal": data[58],
            "sensor_3_signal": data[62],
            
            # Bytes 52, 56, 60: Sensor indices (0x01, 0x02, 0x03)
            "sensor_1_index": data[52],
            "sensor_2_index": data[56],
            "sensor_3_index": data[60],
            
            # Bytes 53, 57, 61: Battery levels (always 0x64 = 100%)
            "sensor_1_battery": data[53],
            "sensor_2_battery": data[57],
            "sensor_3_battery": data[61],
            
            # Bytes 54, 58, 62: Sensor flags (0x00, 0x01)
            "sensor_1_flag": data[54],
            "sensor_2_flag": data[58],
            "sensor_3_flag": data[62],
            
            # Bytes 66-68: Counter data (0x00, 0x02)
            "counter_1_data": data[66],
            "counter_2_data": data[67],
            "counter_3_data": data[68],
        })
        
        # Parse sensor information
        self._parse_sensor_data()
        
        # Parse counter information
        self._parse_counter_data()
        
        self.last_update = datetime.now()

    def _parse_sensor_data(self) -> None:
        """Parse sensor data from system state."""
        for i in range(1, 4):  # Sensors 1, 2, 3
            sensor_key = f"sensor_{i}"
            state = self.system_state.get(f"sensor_{i}_state", 0)
            battery = self.system_state.get(f"sensor_{i}_battery", 0)
            flag = self.system_state.get(f"sensor_{i}_flag", 0)
            
            # Determine sensor status
            if state == 0x00:
                status = "disconnected"
                battery_level = 0
            elif state == 0x02:
                status = "triggered"
                battery_level = 2
            elif state == 0x03:
                status = "normal"
                battery_level = 3
            else:
                status = "unknown"
                battery_level = 0
            
            self.sensors[sensor_key] = {
                "state": status,
                "battery_level": battery_level,
                "battery_percent": battery,  # Always 100% (0x64)
                "flag": flag,
                "index": i,
                "wireless": True
            }

    def _parse_counter_data(self) -> None:
        """Parse counter data from system state."""
        for i in range(1, 4):  # Counters 1, 2, 3
            counter_key = f"counter_{i}"
            data = self.system_state.get(f"counter_{i}_data", 0)
            
            self.counters[counter_key] = {
                "data": data,
                "line_number": i,
                "wire": True
            }

    async def get_device_info(self) -> bool:
        """Get device information."""
        async with self._lock:
            command = create_command(PACKET_DEVICE_INFO)
            response, attempts = await self.send_command_with_retries(command)
            
            if not response:
                _LOGGER.error("Failed to get device info after %d attempts", attempts)
                return False
            
            # Parse device info (basic implementation)
            self.device_info.update({
                "host": self.host,
                "port": self.port,
                "last_update": datetime.now()
            })
            
            return True

    async def get_system_state(self) -> bool:
        """Get system state."""
        async with self._lock:
            command = create_command(PACKET_SYSTEM_STATE)
            response, attempts = await self.send_command_with_retries(command)
            
            if not response:
                _LOGGER.error("Failed to get system state after %d attempts", attempts)
                return False
            
            # Check response code
            response_hex = response.hex()
            if response_hex.startswith("025441fb"):
                _LOGGER.warning("Unknown command response - device may be in error state")
                return False
            elif response_hex.startswith("025441fe"):
                _LOGGER.warning("CRC/format error response")
                return False
            elif not response_hex.startswith("025441"):
                _LOGGER.warning("Unexpected response format: %s", response_hex[:12])
                return False
            
            self._parse_system_state(response)
            return True

    async def set_valve_state(self, open_valve: bool) -> bool:
        """Set valve state (open/close)."""
        async with self._lock:
            # Get current state first
            await self.get_system_state()
            
            dry_mode = self.system_state.get("dry_mode", False)
            auto_close = self.system_state.get("auto_close", False)
            line_config = 0x00  # Default: all lines in sensor mode
            
            command = create_control_command(open_valve, dry_mode, auto_close, line_config)
            response, attempts = await self.send_command_with_retries(
                command, 
                timeout=20.0,  # Longer timeout for valve operations
                max_retries=3,
                retry_delay=2.0
            )
            
            if not response:
                _LOGGER.error("Failed to set valve state after %d attempts", attempts)
                return False
            
            # Wait for valve operation to complete
            await asyncio.sleep(DEFAULT_VALVE_OPERATION_DELAY)
            
            # Verify the change
            await self.get_system_state()
            current_state = self.system_state.get("valve_open", False)
            
            if current_state == open_valve:
                _LOGGER.info("Valve state successfully set to %s", "open" if open_valve else "closed")
                return True
            else:
                _LOGGER.warning("Valve state change not confirmed. Expected: %s, Got: %s", 
                              open_valve, current_state)
                return False

    async def set_dry_mode(self, dry_mode: bool) -> bool:
        """Set dry mode."""
        async with self._lock:
            # Get current state first
            await self.get_system_state()
            
            valve_open = self.system_state.get("valve_open", True)
            auto_close = self.system_state.get("auto_close", False)
            line_config = 0x00  # Default: all lines in sensor mode
            
            command = create_control_command(valve_open, dry_mode, auto_close, line_config)
            response, attempts = await self.send_command_with_retries(command)
            
            if not response:
                _LOGGER.error("Failed to set dry mode after %d attempts", attempts)
                return False
            
            # Update local state
            self.system_state["dry_mode"] = dry_mode
            return True

    async def set_auto_close(self, auto_close: bool) -> bool:
        """Set auto-close mode."""
        async with self._lock:
            # Get current state first
            await self.get_system_state()
            
            valve_open = self.system_state.get("valve_open", True)
            dry_mode = self.system_state.get("dry_mode", False)
            line_config = 0x00  # Default: all lines in sensor mode
            
            command = create_control_command(valve_open, dry_mode, auto_close, line_config)
            response, attempts = await self.send_command_with_retries(command)
            
            if not response:
                _LOGGER.error("Failed to set auto-close mode after %d attempts", attempts)
                return False
            
            # Update local state
            self.system_state["auto_close"] = auto_close
            return True

    async def set_line_mode(self, line_number: int, counter_mode: bool) -> bool:
        """Set line mode (sensor or counter)."""
        async with self._lock:
            # Get current state first
            await self.get_system_state()
            
            valve_open = self.system_state.get("valve_open", True)
            dry_mode = self.system_state.get("dry_mode", False)
            auto_close = self.system_state.get("auto_close", False)
            
            # Calculate line configuration
            line_config = 0x00
            if counter_mode:
                line_config = 1 << (line_number - 1)  # Set bit for this line
            
            command = create_control_command(valve_open, dry_mode, auto_close, line_config)
            response, attempts = await self.send_command_with_retries(command)
            
            if not response:
                _LOGGER.error("Failed to set line mode after %d attempts", attempts)
                return False
            
            return True

    async def set_counter_value(self, line_number: int, value: int) -> bool:
        """Set counter value for a specific line."""
        async with self._lock:
            # First, set the line to counter mode
            await self.set_line_mode(line_number, True)
            
            # Then set the counter value
            command = create_counter_command(line_number, value)
            response, attempts = await self.send_command_with_retries(command)
            
            if not response:
                _LOGGER.error("Failed to set counter value after %d attempts", attempts)
                return False
            
            return True

    async def update_all(self) -> bool:
        """Update all device data."""
        try:
            success = await self.get_system_state()
            if success:
                await self.get_device_info()
            return success
        except Exception as err:
            _LOGGER.error("Error updating device %s: %s", self.host, err)
            return False

    def is_online(self) -> bool:
        """Check if device is online."""
        if self.last_update is None:
            return False
        
        # Consider device offline if no update in the last 10 minutes
        # This gives more time for the device to recover from temporary issues
        return (datetime.now() - self.last_update).total_seconds() < 600

    def get_device_info_dict(self) -> Dict[str, Any]:
        """Get device information for Home Assistant."""
        return {
            "identifiers": {("neptun_leak_protection", self.host)},
            "name": f"Neptun N4106 {self.host}",
            "manufacturer": "Neptun",
            "model": "N4106",
            "sw_version": "Unknown",
            "configuration_url": f"http://{self.host}",
        }

    async def set_valve_state(self, open_valve: bool) -> bool:
        """Set valve state (open/close)."""
        try:
            # Use exact working commands from control_commands_summary.json
            if open_valve:
                # Open valves: "0254515700075300040100000089A5"
                command = bytes.fromhex("0254515700075300040100000089A5")
            else:
                # Close valves: "0254515700075300040000000032B9"
                command = bytes.fromhex("0254515700075300040000000032B9")
            
            _LOGGER.debug("Sending valve command: %s", command.hex().upper())
            response, attempts = await self.send_command_with_retries(command)
            if response:
                _LOGGER.info("Valve state command sent successfully")
                return True
            else:
                _LOGGER.error("Failed to send valve state command")
                return False
        except Exception as err:
            _LOGGER.error("Error setting valve state: %s", err)
            return False

    async def set_dry_mode(self, dry_mode: bool) -> bool:
        """Set dry mode (cleaning mode)."""
        try:
            # Use exact working commands from control_commands_summary.json
            if dry_mode:
                # Enable dry mode: "02545157000753000400010000EEE3"
                command = bytes.fromhex("02545157000753000400010000EEE3")
            else:
                # Disable dry mode: "0254515700075300040000000032B9"
                command = bytes.fromhex("0254515700075300040000000032B9")
            
            _LOGGER.debug("Sending dry mode command: %s", command.hex().upper())
            response, attempts = await self.send_command_with_retries(command)
            if response:
                _LOGGER.info("Dry mode command sent successfully")
                return True
            else:
                _LOGGER.error("Failed to send dry mode command")
                return False
        except Exception as err:
            _LOGGER.error("Error setting dry mode: %s", err)
            return False

    async def set_auto_close(self, auto_close: bool) -> bool:
        """Set auto-close mode."""
        try:
            # Use exact working commands from control_commands_summary.json
            if auto_close:
                # Enable auto-close: "02545157000753000400000100EAA0"
                command = bytes.fromhex("02545157000753000400000100EAA0")
            else:
                # Disable auto-close: "0254515700075300040000000032B9"
                command = bytes.fromhex("0254515700075300040000000032B9")
            
            _LOGGER.debug("Sending auto-close command: %s", command.hex().upper())
            response, attempts = await self.send_command_with_retries(command)
            if response:
                _LOGGER.info("Auto-close command sent successfully")
                return True
            else:
                _LOGGER.error("Failed to send auto-close command")
                return False
        except Exception as err:
            _LOGGER.error("Error setting auto-close mode: %s", err)
            return False