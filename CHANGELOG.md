# Changelog

## [2.1.13] - 2025-10-21

### Fixed
- Fixed control commands to use exact working hex commands from real tests
- Commands now use pre-calculated CRC values that are known to work
- Removed custom CRC calculation that was causing command failures
- All control commands now use verified working hex strings

## [2.1.12] - 2025-10-21

### Fixed
- Improved connection stability after HA restart
- Increased all timeouts for better reliability
- Added graceful error handling to prevent integration failures
- Increased scan interval to 2 minutes for stability
- Extended device online timeout to 10 minutes

## [2.1.11] - 2025-10-21

### Fixed
- Fixed control command structure to match working examples
- Corrected data length from 7 to 6 bytes in control commands
- Added debug logging for sent commands
- Commands now use proper structure from control_commands_summary.json

## [2.1.10] - 2025-10-21

### Fixed
- Fixed missing _calculate_crc16_ccitt method in NeptunDevice class
- Switch buttons now work correctly (Main Valve, Auto Close, Dry Mode)
- Added proper CRC16-CCITT calculation for control commands

## [2.1.9] - 2025-10-21

### Fixed
- Fixed non-working switch buttons (Main Valve, Auto Close, Dry Mode)
- Added missing control command methods in protocol.py
- Implemented proper valve control commands based on protocol specification
- Enhanced logging for switch operations

## [2.1.8] - 2025-10-21

### Fixed
- Enhanced error logging for better debugging
- Added detailed connection attempt logging
- Improved error messages with specific error types and errno

## [2.1.7] - 2025-10-21

### Fixed
- Increased connection and receive timeouts for better stability
- Increased default scan interval from 30 to 60 seconds
- Improved connection reliability with slower devices

## [2.1.6] - 2025-10-21

### Fixed
- Fixed signal sensor unit of measurement warnings
- Removed invalid device_class and unit for signal state sensors
- Updated signal sensor to show state (0/1) instead of percentage

## [2.1.5] - 2025-10-21

### Fixed
- Fixed EntityCategory validation errors
- Updated sensor.py and switch.py to use proper EntityCategory instances
- All entities should now load without validation errors

## [2.1.4] - 2025-10-21

### Fixed
- Fixed device_info coroutine error in all entity files
- Fixed sensor.py, switch.py, binary_sensor.py device_info methods
- All entities should now load without coroutine errors

## [2.1.3] - 2025-10-21

### Fixed
- Fixed critical device_info coroutine error
- Fixed deprecated config_entry assignment
- Fixed entity creation errors
- All entities should now load properly

## [2.1.2] - 2025-10-21

### Fixed
- Fixed HACS version detection issues
- Updated hacs.json for proper version display

## [2.1.1] - 2025-10-21

### Fixed
- Fixed config flow error with async method call
- Fixed device info retrieval in configuration

## [2.0.0] - 2025-09-24

### Added
- Complete protocol rewrite based on real Neptun N4106 analysis
- Support for all 3 wireless sensors with real-time monitoring
- Valve control (open/close) with 15-second operation delay
- Dry mode (cleaning mode) that ignores sensor alarms
- Auto-close mode for automatic valve closure when sensors are lost
- Real-time battery level monitoring for all sensors
- Signal strength monitoring (2/4, 3/4 levels)
- Counter support for wired lines
- Line mode control (sensor/counter switching)
- Counter value setting for individual lines
- CRC16-CCITT checksum validation
- Retry logic for reliable communication
- Optimal timing for stable operation

### Changed
- **BREAKING**: Complete rewrite of protocol implementation
- **BREAKING**: Changed entity structure and naming
- **BREAKING**: Updated data structure and attributes
- Improved error handling and logging
- Enhanced device state monitoring
- Better integration with Home Assistant

### Fixed
- Fixed CRC calculation algorithm
- Fixed command timing issues
- Fixed sensor state parsing
- Fixed battery level interpretation
- Fixed signal strength calculation

### Technical Details
- Protocol: Neptun N4106 with commands 0x52, 0x57, 0x58
- Sensor states: 0x00 (disconnected), 0x02 (triggered), 0x03 (normal)
- Battery levels: 0x00 (0%), 0x02 (2%), 0x03 (3%), 0x64 (100%)
- Signal strength: 0x02 (2/4), 0x03 (3/4)
- Valve operation delay: 15 seconds
- Retry attempts: 3 with 2-second delay

## [1.0.0] - 2025-09-22

### Added
- Initial version
- Basic protocol implementation
- Valve control
- Sensor monitoring
- Counter support