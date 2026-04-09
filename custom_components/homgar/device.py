"""Device registry helper for Homgar integration."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN, DEVICE_TYPE_MAPPING


def get_device_info(device_data: dict) -> DeviceInfo:
    """Get device info for device registry."""
    device = device_data["device"]
    home = device_data["home"]
    device_id = device["id"]
    
    # Get device type for better naming
    device_model = device.get("model", "Unknown")
    device_type = DEVICE_TYPE_MAPPING.get(device_model, "device")
    
    # Create a more user-friendly model name
    model_names = {
        "HWS019WRF-V2": "Smart+ Irrigation Display Hub",
        "HTV213FRF": "Smart+ 2-Zone Water Timer",
        "HCS021FRF": "Smart+ Soil & Moisture Sensor",
        "HCS012ARF": "Smart+ High Precision Rain Sensor",
        "HCS014ARF": "Smart+ Outdoor Air Humidity Sensor",
    }
    
    friendly_model = model_names.get(device_model, device_model)
    
    return DeviceInfo(
        identifiers={(DOMAIN, device_id)},
        name=device.get("name", f"RainPoint {friendly_model}"),
        manufacturer="RainPoint",
        model=friendly_model,
        sw_version=device.get("firmware_version"),
        suggested_area=home.get("name", "Garden"),
        configuration_url="https://www.rainpointonline.com/",
    )
