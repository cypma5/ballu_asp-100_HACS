"""Constants for Ballu ASP-100 integration."""

DOMAIN = "ballu_asp100"
MANUFACTURER = "Ballu"
MODEL = "ONEAIR ASP-100"

# Modes mapping - обновлено согласно конфигу
MODE_MAPPING = {
    "off": 0,
    "comfort": 1,      # Ручной режим
    "Auto": 2,         # Автоматический по СО2
    "sleep": 3,        # Ночной режим
    "boost": 4,        # Турбо режим
    "eco": 5           # Эко проветривание
}

FAN_MODE_MAPPING = {
    "Off": 0,
    "S1": 1,
    "S2": 2,
    "S3": 3,
    "S4": 4,
    "S5": 5,
    "S6": 6,
    "S7": 7
}

SOUND_MAPPING = {
    "Выключено": 0,
    "Дождь": 1,
    "Море": 2,
    "Лес": 3,
    "Птицы": 4,
    "Костер": 5
}

# HVAC modes based on device capabilities
HVAC_MODES = ["off", "fan_only"]
PRESET_MODES = ["comfort", "Auto", "sleep", "boost", "eco"]