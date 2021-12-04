"""The MasterTherm integration."""
from __future__ import annotations
import logging
import async_timeout
from aiohttp import ClientSession

import masterthermconnect
from masterthermconnect.auth import Auth
from masterthermconnect.exceptions import (
    MasterThermUnsupportedRole,
    MasterThermAuthenticationError,
    MasterThermConnectionError,
    MasterThermResponseFormatError,
    MasterThermTokenInvalid,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import AUTH, DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = ["climate"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up MasterTherm from a config entry."""

    auth = Auth(entry.data["username"], entry.data["password"], ClientSession())

    try:
        await auth.connect()
    except (
        MasterThermUnsupportedRole,
        MasterThermConnectionError,
        MasterThermAuthenticationError,
    ) as ex:
        raise ConfigEntryNotReady("Cannot connect") from ex

    hass.data.setdefault(DOMAIN, {})

    hass.data[DOMAIN][entry.entry_id] = {AUTH: auth}

    async def async_update_data():
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        try:
            # Note: asyncio.TimeoutError and aiohttp.ClientError are already
            # handled by the data update coordinator.
            async with async_timeout.timeout(10):
                return await api.fetch_data()
        except ApiAuthError as err:
            # Raising ConfigEntryAuthFailed will cancel future updates
            # and start a config flow with SOURCE_REAUTH (async_step_reauth)
            raise ConfigEntryAuthFailed from err
        except ApiError as err:
            raise UpdateFailed(f"Error communicating with API: {err}")

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
