"""Constants for the Homgar integration."""

DOMAIN = "homgar"

# Config flow
CONF_EMAIL = "email"
CONF_PASSWORD = "password"

# Device types and their corresponding entity types
DEVICE_TYPE_MAPPING = {
    "HWS019WRF-V2": "hub",  # RainPoint Smart+ Irrigation Display Hub
    "HTV213FRF": "water_timer",  # RainPoint Smart+ 2-Zone Water Timer
    "HCS021FRF": "soil_sensor",  # RainPoint Smart+ Soil&Moisture Sensor
    "HCS012ARF": "rain_sensor",  # RainPoint Smart+ High Precision Rain Sensor
    "HCS014ARF": "humidity_sensor",  # RainPoint Smart+ Outdoor Air Humidity Sensor
}

# Sensor types for different devices
SENSOR_TYPES = {
    "soil_sensor": {
        "moisture": {
            "name": "Soil Moisture",
            "unit": "%",
            "icon": "mdi:water-percent",
            "device_class": "humidity",
        },
        "temperature": {
            "name": "Soil Temperature",
            "unit": "°C",
            "icon": "mdi:thermometer",
            "device_class": "temperature",
        },
        "battery": {
            "name": "Battery",
            "unit": "%",
            "icon": "mdi:battery",
            "device_class": "battery",
        },
    },
    "rain_sensor": {
        "rain_amount": {
            "name": "Rain Amount",
            "unit": "mm",
            "icon": "mdi:weather-rainy",
            "device_class": None,
        },
        "rain_hourly": {
            "name": "Rain Past Hour",
            "unit": "mm",
            "icon": "mdi:weather-rainy",
        },
        "rain_daily": {
            "name": "Rain Past 24 Hours",
            "unit": "mm",
            "icon": "mdi:weather-rainy",
        },
        "rain_7days": {
            "name": "Rain Past 7 Days",
            "unit": "mm",
            "icon": "mdi:weather-rainy",
        },
        "rain_total": {
            "name": "Rain Total",
            "unit": "mm",
            "icon": "mdi:chart-line",
        },
        "battery": {
            "name": "Battery",
            "unit": "%",
            "icon": "mdi:battery",
            "device_class": "battery",
        },
    },
    "humidity_sensor": {
        "humidity": {
            "name": "Humidity",
            "unit": "%",
            "icon": "mdi:water-percent",
            "device_class": "humidity",
        },
        "temperature": {
            "name": "Temperature",
            "unit": "°C",
            "icon": "mdi:thermometer",
            "device_class": "temperature",
        },
        "battery": {
            "name": "Battery",
            "unit": "%",
            "icon": "mdi:battery",
            "device_class": "battery",
        },
    },
    "water_timer": {
        "battery": {
            "name": "Battery",
            "unit": "%",
            "icon": "mdi:battery",
            "device_class": "battery",
        },
    },
    "hub": {
        "signal_strength": {
            "name": "Signal Strength",
            "unit": "dBm",
            "icon": "mdi:wifi",
        },
    },
}

# Binary sensor types
BINARY_SENSOR_TYPES = {
    "water_timer": {
        "watering_zone1": {
            "name": "Watering Zone 1",
            "icon": "mdi:sprinkler",
            "device_class": None,
        },
        "watering_zone2": {
            "name": "Watering Zone 2",
            "icon": "mdi:sprinkler",
            "device_class": None,
        },
    },
    "rain_sensor": {
        "rain_detected": {
            "name": "Rain Detected",
            "icon": "mdi:weather-rainy",
            "device_class": "moisture",
        },
    },
}
