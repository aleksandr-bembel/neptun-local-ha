"""
🔋 КАРТА ПОЛЕЙ ДАТЧИКОВ NEPTUN

Документирует структуру данных для всех трех беспроводных датчиков
в ответе команды SYSTEM_STATE (112 байт).
"""

# Позиции батареи датчиков в SYSTEM_STATE (112 байт)
SENSOR_BATTERY_POSITIONS = {
    1: 53,  # Первый датчик
    2: 57,  # Второй датчик  
    3: 61,  # Третий датчик
}

# Позиции состояния датчиков
SENSOR_STATE_POSITIONS = {
    1: 51,  # Первый датчик
    2: 55,  # Второй датчик
    3: 59,  # Третий датчик
}

# Позиции индексов датчиков
SENSOR_INDEX_POSITIONS = {
    1: 52,  # Первый датчик
    2: 56,  # Второй датчик
    3: 60,  # Третий датчик
}

# Позиции сигнала датчиков
SENSOR_SIGNAL_POSITIONS = {
    1: 54,  # Первый датчик
    2: 58,  # Второй датчик
    3: 62,  # Третий датчик
}

# Интервал между датчиками
SENSOR_INTERVAL = 4  # байта

def get_sensor_battery_position(sensor_number: int) -> int:
    """Получить позицию батареи для указанного датчика."""
    if sensor_number not in SENSOR_BATTERY_POSITIONS:
        raise ValueError(f"Invalid sensor number: {sensor_number}")
    return SENSOR_BATTERY_POSITIONS[sensor_number]

def get_sensor_state_position(sensor_number: int) -> int:
    """Получить позицию состояния для указанного датчика."""
    if sensor_number not in SENSOR_STATE_POSITIONS:
        raise ValueError(f"Invalid sensor number: {sensor_number}")
    return SENSOR_STATE_POSITIONS[sensor_number]

def get_sensor_index_position(sensor_number: int) -> int:
    """Получить позицию индекса для указанного датчика."""
    if sensor_number not in SENSOR_INDEX_POSITIONS:
        raise ValueError(f"Invalid sensor number: {sensor_number}")
    return SENSOR_INDEX_POSITIONS[sensor_number]

def get_sensor_signal_position(sensor_number: int) -> int:
    """Получить позицию сигнала для указанного датчика."""
    if sensor_number not in SENSOR_SIGNAL_POSITIONS:
        raise ValueError(f"Invalid sensor number: {sensor_number}")
    return SENSOR_SIGNAL_POSITIONS[sensor_number]

def parse_battery_level(battery_byte: int) -> int:
    """
    Парсит уровень батареи из байта с учетом знаковой интерпретации.
    
    Args:
        battery_byte: Байт с уровнем батареи
        
    Returns:
        Уровень батареи в процентах (0-100)
        
    Examples:
        parse_battery_level(0x64) -> 100  # 100%
        parse_battery_level(0xD6) -> 42   # 42% (0xD6 = -42 знаковое)
    """
    import struct
    battery_signed = struct.unpack('b', bytes([battery_byte]))[0]
    
    # Обрабатываем отрицательные значения (например, 0xD6 = -42 означает 42%)
    if battery_signed < 0:
        return abs(battery_signed)
    else:
        return battery_signed

def parse_sensor_state(state_byte: int) -> str:
    """
    Парсит состояние датчика из байта.
    
    Args:
        state_byte: Байт с состоянием датчика
        
    Returns:
        Строковое описание состояния
    """
    state_map = {
        0x00: "disconnected",  # Отключен
        0x02: "triggered",     # Сработал
        0x03: "normal",        # Нормальное состояние
    }
    
    return state_map.get(state_byte, f"unknown_{state_byte:02X}")

def parse_signal_level(signal_byte: int) -> str:
    """
    Парсит уровень сигнала из байта.
    
    Args:
        signal_byte: Байт с уровнем сигнала
        
    Returns:
        Строковое описание уровня сигнала
    """
    signal_map = {
        0x00: "no_signal",     # Нет сигнала
        0x01: "good_signal",   # Хороший сигнал
    }
    
    return signal_map.get(signal_byte, f"unknown_{signal_byte:02X}")

def get_sensor_data(system_state_data: bytes, sensor_number: int) -> dict:
    """
    Извлекает данные для указанного датчика из системного состояния.
    
    Args:
        system_state_data: Данные системного состояния (112 байт)
        sensor_number: Номер датчика (1, 2, 3)
        
    Returns:
        Словарь с данными датчика
    """
    if len(system_state_data) < 112:
        raise ValueError("System state data too short")
    
    if sensor_number not in [1, 2, 3]:
        raise ValueError("Invalid sensor number")
    
    battery_pos = get_sensor_battery_position(sensor_number)
    state_pos = get_sensor_state_position(sensor_number)
    index_pos = get_sensor_index_position(sensor_number)
    signal_pos = get_sensor_signal_position(sensor_number)
    
    return {
        "sensor_number": sensor_number,
        "battery_level": parse_battery_level(system_state_data[battery_pos]),
        "battery_raw": system_state_data[battery_pos],
        "state": parse_sensor_state(system_state_data[state_pos]),
        "state_raw": system_state_data[state_pos],
        "index": system_state_data[index_pos],
        "signal_level": parse_signal_level(system_state_data[signal_pos]),
        "signal_raw": system_state_data[signal_pos],
        "positions": {
            "battery": battery_pos,
            "state": state_pos,
            "index": index_pos,
            "signal": signal_pos,
        }
    }

def get_all_sensors_data(system_state_data: bytes) -> dict:
    """
    Извлекает данные для всех датчиков из системного состояния.
    
    Args:
        system_state_data: Данные системного состояния (112 байт)
        
    Returns:
        Словарь с данными всех датчиков
    """
    sensors_data = {}
    
    for sensor_number in [1, 2, 3]:
        sensors_data[f"sensor_{sensor_number}"] = get_sensor_data(
            system_state_data, sensor_number
        )
    
    return sensors_data

# Пример использования
if __name__ == "__main__":
    # Пример данных из дампа с низким зарядом первого датчика
    example_data = bytes.fromhex(
        "0254415200684900054E343130364D001136303A43353A41383A36463A35363A3641410001005300070103000000000473000C0301D60003026400020364004C000402000000430014000000000100000000010000000001000000000144000A31343932333836313033570001043F0E"
    )
    
    print("🔋 ДАННЫЕ ДАТЧИКОВ:")
    print("=" * 50)
    
    for sensor_number in [1, 2, 3]:
        sensor_data = get_sensor_data(example_data, sensor_number)
        print(f"\nДатчик {sensor_number}:")
        print(f"  Батарея: {sensor_data['battery_level']}% (0x{sensor_data['battery_raw']:02X})")
        print(f"  Состояние: {sensor_data['state']} (0x{sensor_data['state_raw']:02X})")
        print(f"  Индекс: {sensor_data['index']}")
        print(f"  Сигнал: {sensor_data['signal_level']} (0x{sensor_data['signal_raw']:02X})")
        print(f"  Позиции: {sensor_data['positions']}")
