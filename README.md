# Neptun N4106 Leak Protection

Home Assistant integration for Neptun N4106 leak protection devices.

## Features

- **Water leak detection** - 3 wireless sensors with real-time monitoring
- **Valve control** - Open/close main water valve
- **Dry mode** - Cleaning mode that ignores sensor alarms
- **Auto-close mode** - Automatically close valves when sensors are lost
- **Battery monitoring** - Real-time battery levels for all sensors
- **Signal strength monitoring** - Signal quality for wireless sensors
- **Counter support** - Water usage counters for wired lines
- **Line mode control** - Switch wired lines between sensor and counter modes

## Installation

1. Copy this folder to `custom_components/neptun_leak_protection/` in your Home Assistant configuration directory
2. Restart Home Assistant
3. Add the integration via the UI

## Configuration

The integration can be configured via the Home Assistant UI. You will need:

- **Host IP address** of the Neptun device (e.g., YOUR_IP_ADDRESS)
- **Port** (default: 6350)
- **Scan interval** (default: 30 seconds)

## Entities

### Switches
- **Main Valve** - Control the main water valve (open/close)
- **Dry Mode** - Enable/disable cleaning mode
- **Auto Close** - Enable/disable automatic valve closure when sensors are lost

### Binary Sensors
- **System Alarm** - Overall system alarm status
- **Wireless Sensor 1/2/3** - Individual wireless sensor leak detection

### Sensors
- **System State** - Current system state (Normal, Dry Mode, Auto Close Enabled)
- **Wireless Sensor 1/2/3** - Sensor state (Normal, Triggered, Disconnected)
- **Wireless Sensor 1/2/3 Battery** - Battery levels (0%, 2%, 3%, 100%)
- **Wireless Sensor 1/2/3 Signal** - Signal strength (0%, 50%, 75%)
- **Counter Line 1/2/3/4** - Counter data for wired lines

## 🔋 Структура данных датчиков

### 📊 Расположение батареи в SYSTEM_STATE (112 байт):

| Позиция | Датчик | Описание | Формат |
|---------|--------|----------|--------|
| 53 | Первый датчик | Уровень батареи | Знаковое 8-бит |
| 57 | Второй датчик | Уровень батареи | Знаковое 8-бит |
| 61 | Третий датчик | Уровень батареи | Знаковое 8-бит |

### 🔍 Интерпретация значений батареи:

| Hex | Беззнаковое | Знаковое | Уровень батареи |
|-----|-------------|----------|-----------------|
| 0x64 | 100 | 100 | 100% |
| 0xD6 | 214 | -42 | 42% (показывается как -42%) |

### ⚠️ Важно:
- **Используйте знаковую интерпретацию** для правильного определения уровня батареи
- **Значение 0xD6 = -42** означает реальный уровень 42% (не -42%)
- **Интервал между датчиками:** 4 байта

## Protocol

This integration uses the **Neptun N4106 protocol** for communication with the device.

### Key Features:
- **CRC16-CCITT** checksum validation
- **Retry logic** for reliable communication
- **Optimal timing** for stable operation
- **Real-time monitoring** of all sensor states

### Commands Supported:
- **0x52** - Device info and system state
- **0x57** - System control (valves, modes, line configuration)
- **0x58** - Counter value setting

## Technical Details

### Sensor States:
- **0x00** - Disconnected
- **0x02** - Triggered (leak detected)
- **0x03** - Normal

### Signal Strength:
- **0x02** - 2/4 (50%)
- **0x03** - 3/4 (75%)

### Battery Levels:
- **0x00** - 0% (disconnected)
- **0x02** - 2% (low)
- **0x03** - 3% (low)
- **0x64** - 100% (normal)

## Troubleshooting

### Common Issues:
1. **Connection timeouts** - Check network connectivity and device IP
2. **Unknown command errors** - Device may be in error state, try restarting
3. **CRC errors** - Check network stability and device status

### Debug Mode:
Enable debug logging in Home Assistant to see detailed protocol communication.

## Support

For issues and feature requests, please visit the GitHub repository.

## Version History

- **v2.0.0** - Complete rewrite based on real protocol analysis
- **v1.0.0** - Initial version