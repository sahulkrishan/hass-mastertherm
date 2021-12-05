"""The MasterTherm integration."""
from __future__ import annotations

import logging

import async_timeout
import masterthermconnect
from aiohttp import ClientSession
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from masterthermconnect.auth import Auth
from masterthermconnect.exceptions import (
    MasterThermAuthenticationError,
    MasterThermConnectionError,
    MasterThermResponseFormatError,
    MasterThermTokenInvalid,
    MasterThermUnsupportedRole,
)

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

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
