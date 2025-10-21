# Changelog

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