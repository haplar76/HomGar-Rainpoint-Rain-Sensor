"""Support for Homgar sensors."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, DEVICE_TYPE_MAPPING, SENSOR_TYPES


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Homgar sensors from a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = []
    for device_id, device_data in coordinator.data.items():
        device = device_data["device"]
        device_model = device.get("model", "")
        device_type = DEVICE_TYPE_MAPPING.get(device_model)

        if device_type and device_type in SENSOR_TYPES:
            for sensor_key, sensor_config in SENSOR_TYPES[device_type].items():
                entities.append(
                    HomgarSensor(
                        coordinator,
                        device_id,
                        sensor_key,
                        sensor_config,
                        device_data,
                    )
                )

    async_add_entities(entities)


class HomgarSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Homgar sensor."""

    def __init__(
        self,
        coordinator,
        device_id: str,
        sensor_key: str,
        sensor_config: dict,
        device_data: dict,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        
        self._device_id = device_id
        self._sensor_key = sensor_key
        self._sensor_config = sensor_config
        self._device_data = device_data
        
        device = device_data["device"]
        home = device_data["home"]
        
        # Entity attributes
        self._attr_name = f"{device['name']} {sensor_config['name']}"
        self._attr_unique_id = f"{device_id}_{sensor_key}"
        self._attr_native_unit_of_measurement = sensor_config.get("unit")
        self._attr_icon = sensor_config.get("icon")
        
        if sensor_config.get("device_class"):
            self._attr_device_class = getattr(SensorDeviceClass, sensor_config["device_class"].upper(), None)
        
        # Set state class for numeric sensors
        if sensor_config.get("unit"):
            self._attr_state_class = SensorStateClass.MEASUREMENT
        
        # Device info
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device["name"],
            "manufacturer": "RainPoint",
            "model": device.get("model", "Unknown"),
            "sw_version": device.get("firmware_version"),
            "suggested_area": home.get("name", "Garden"),
        }

    @property
    def native_value(self) -> str | int | float | None:
        """Return the state of the sensor."""
        if self._device_id not in self.coordinator.data:
            return None
            
        device_data = self.coordinator.data[self._device_id]
        status = device_data.get("status", {})
        
        # Map sensor keys to actual API response keys
        # This mapping will depend on the actual API response structure
        value_mapping = {
            "moisture": "soil_moisture",
            "temperature": "temperature",
            "humidity": "humidity",
            "battery": "battery_level",
            "rain_amount": "rain_amount",
            "rain_detected": "rain_detected",
            "signal_strength": "signal_strength",
            
        }
        
        api_key = value_mapping.get(self._sensor_key, self._sensor_key)
        return status.get(api_key)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            self.coordinator.last_update_success
            and self._device_id in self.coordinator.data
        )

    @property
    def extra_state_attributes(self) -> dict[str, str] | None:
        """Return additional state attributes."""
        if self._device_id not in self.coordinator.data:
            return None
            
        device_data = self.coordinator.data[self._device_id]
        status = device_data.get("status", {})
        
        attributes = {}
        
        # Add last seen timestamp if available
        if "last_seen" in status:
            attributes["last_seen"] = status["last_seen"]
            
        # Add device-specific attributes
        if "firmware_version" in status:
            attributes["firmware_version"] = status["firmware_version"]

        if "raw_status" in status:
            attributes["raw_status"] = status["raw_status"]

        if "raw_status_map" in status:
            attributes["raw_status_map"] = status["raw_status_map"]
            
        return attributes if attributes else None
