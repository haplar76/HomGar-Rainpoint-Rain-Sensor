"""The Homgar integration."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import HomgarAPI
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]
UPDATE_INTERVAL = timedelta(seconds=15)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Homgar from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    session = async_get_clientsession(hass)
    api = HomgarAPI(
        email=entry.data[CONF_EMAIL],
        password=entry.data[CONF_PASSWORD],
        session=session,
    )

    coordinator = HomgarDataUpdateCoordinator(hass, api)
    await coordinator.async_config_entry_first_refresh()
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


class HomgarDataUpdateCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Manage fetching data from the Homgar API."""

    def __init__(self, hass: HomeAssistant, api: HomgarAPI) -> None:
        self.api = api
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        """Fetch latest data from the API."""
        try:
            if not self.api.is_authenticated:
                await self.api.async_login()

            homes = await self.api.async_get_homes()
            devices_data: dict[str, dict[str, Any]] = {}

            for home in homes:
                for device in await self.api.async_get_devices(home["id"]):
                    device_id = device["id"]
                    device_status = await self.api.async_get_device_status(device)
                    devices_data[device_id] = {
                        "device": device,
                        "status": device_status,
                        "home": home,
                    }

            return devices_data
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
