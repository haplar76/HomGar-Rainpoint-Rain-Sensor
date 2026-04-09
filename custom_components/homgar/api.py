"""Homgar API wrapper for Home Assistant."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

from .homgar_api.homgarapi import HomgarApi as HomgarAPIBase
from .homgar_api.homgarapi import HomgarApiException

_LOGGER = logging.getLogger(__name__)


class HomgarConnectionError(Exception):
    """Error to indicate a connection problem."""


class HomgarAuthError(Exception):
    """Error to indicate an authentication problem."""


class HomgarAPI:
    """Wrapper around the bundled Homgar API library."""

    def __init__(self, email: str, password: str, session: aiohttp.ClientSession) -> None:
        self.email = email
        self.password = password
        self.session = session
        self._api: HomgarAPIBase | None = None
        self._authenticated = False
        self._last_rain_by_device: dict[str, float] = {}

    @property
    def is_authenticated(self) -> bool:
        return self._authenticated

    async def async_login(self) -> None:
        """Log in to the Homgar API."""
        try:
            self._api = HomgarAPIBase()
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._api.login, self.email, self.password)
            self._authenticated = True
        except HomgarApiException as err:
            _LOGGER.error("Failed to login to Homgar API: %s", err)
            raise HomgarAuthError("Invalid credentials") from err
        except Exception as err:
            _LOGGER.error("Failed to login to Homgar API: %s", err)
            raise HomgarConnectionError("Connection failed") from err

    async def async_get_homes(self) -> list[dict[str, Any]]:
        """Get list of homes as dictionaries."""
        if not self._authenticated:
            await self.async_login()

        try:
            loop = asyncio.get_running_loop()
            homes = await loop.run_in_executor(None, self._api.get_homes)
            return [{"id": str(home.hid), "name": home.name} for home in homes]
        except Exception as err:
            _LOGGER.error("Failed to get homes: %s", err)
            raise HomgarConnectionError("Failed to get homes") from err

    async def async_get_devices(self, home_id: str) -> list[dict[str, Any]]:
        """Get devices for a home as flattened dictionaries."""
        if not self._authenticated:
            await self.async_login()

        try:
            loop = asyncio.get_running_loop()
            hubs = await loop.run_in_executor(None, self._api.get_devices_for_hid, home_id)
            devices: list[dict[str, Any]] = []
            for hub in hubs:
                devices.append(
                    {
                        "id": str(hub.did),
                        "name": hub.name,
                        "model": hub.model,
                        "firmware_version": None,
                        "is_hub": True,
                        "hub_object": hub,
                    }
                )
                for subdevice in getattr(hub, "subdevices", []):
                    devices.append(
                        {
                            "id": str(subdevice.did),
                            "name": subdevice.name,
                            "model": subdevice.model,
                            "firmware_version": None,
                            "is_hub": False,
                            "hub_object": hub,
                            "device_object": subdevice,
                        }
                    )
            return devices
        except Exception as err:
            _LOGGER.error("Failed to get devices for home %s: %s", home_id, err)
            raise HomgarConnectionError("Failed to get devices") from err

    async def async_get_device_status(self, device: dict[str, Any]) -> dict[str, Any]:
        """Get current status for a device dict returned by async_get_devices."""
        if not self._authenticated:
            await self.async_login()

        try:
            hub = device["hub_object"]
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._api.get_device_status, hub)
            obj = device.get("device_object", hub)

            raw = getattr(obj, "raw_status", None)

            rain_hourly = None
            rain_daily = None
            rain_7days = None
            rain_total = None
            rain_detected = None

            if raw:
                try:
                    hex_part = raw.split("#", 1)[1]
                    data = bytes.fromhex(hex_part)

                    tagged_values: dict[int, int] = {}
                    i = 0
                    while i <= len(data) - 4:
                        if data[i] == 0xFD:
                            tag = data[i + 1]
                            value = int.from_bytes(data[i + 2:i + 4], byteorder="little")
                            tagged_values[tag] = value
                            i += 4
                        else:
                            i += 1

                    # Tentative mapping for model 289, values in tenths of mm
                    if tagged_values.get(4) is not None:
                        rain_hourly = tagged_values[4] / 10.0
                    if tagged_values.get(5) is not None:
                        rain_daily = tagged_values[5] / 10.0
                    if tagged_values.get(6) is not None:
                        rain_7days = tagged_values[6] / 10.0

                    # For now, use the largest known counter as total fallback
                    known = [v for v in (rain_hourly, rain_daily, rain_7days) if v is not None]
                    if known:
                        rain_total = max(known)

                    # Use past-hour rain as the best current rain indicator available
                    rain_detected = rain_hourly > 0 if rain_hourly is not None else None

                except Exception as e:
                    _LOGGER.warning("Failed to decode rain payload: %s", e)

            return {
                "raw_status": raw,
                "raw_status_map": getattr(obj, "raw_status_map", None),
                "signal_strength": getattr(obj, "rf_rssi", None)
                if getattr(obj, "rf_rssi", None) is not None
                else getattr(hub, "rf_rssi", None),
                "battery_level": getattr(obj, "battery_state", None)
                if getattr(obj, "battery_state", None) is not None
                else getattr(hub, "battery_state", None),
                "temperature": _mk_to_c(getattr(obj, "temp_mk_current", None)),
                "humidity": getattr(obj, "hum_current", None),
                "soil_moisture": getattr(obj, "moist_percent_current", None),
                "rain_amount": rain_daily,
                "rain_hourly": rain_hourly,
                "rain_daily": rain_daily,
                "rain_7days": rain_7days,
                "rain_total": rain_total,
                "rain_detected": rain_detected,
            }

        except Exception as err:
            _LOGGER.error("Failed to get device status for %s: %s", device.get("id"), err)
            raise HomgarConnectionError("Failed to get device status") from err

            return {
                "raw_status": raw,
                "raw_status_map": getattr(obj, "raw_status_map", None),
                "signal_strength": getattr(obj, "rf_rssi", None)
                if getattr(obj, "rf_rssi", None) is not None
                else getattr(hub, "rf_rssi", None),
                "battery_level": getattr(obj, "battery_state", None)
                if getattr(obj, "battery_state", None) is not None
                else getattr(hub, "battery_state", None),
                "temperature": _mk_to_c(getattr(obj, "temp_mk_current", None)),
                "humidity": getattr(obj, "hum_current", None),
                "soil_moisture": getattr(obj, "moist_percent_current", None),
                "rain_amount": rain_daily,
                "rain_hourly": rain_hourly,
                "rain_daily": rain_daily,
                "rain_7days": rain_7days,
                "rain_total": rain_total,
                "rain_detected": rain_detected,
            }

        except Exception as err:
            _LOGGER.error("Failed to get device status for %s: %s", device.get("id"), err)
            raise HomgarConnectionError("Failed to get device status") from err


def _mk_to_c(value: Any) -> float | None:
    """Convert milli-kelvin to Celsius."""
    if value is None:
        return None
    try:
        return round((float(value) / 1000.0) - 273.15, 1)
    except (TypeError, ValueError):
        return None
