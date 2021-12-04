"""Platform for climate integration."""
import logging

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    HVAC_MODE_AUTO,
    HVAC_MODE_COOL,
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    SUPPORT_TARGET_TEMPERATURE,
)

HVAC_MODE_MAP = {
    "cooling": HVAC_MODE_COOL,
    "heating": HVAC_MODE_HEAT,
    "auto": HVAC_MODE_AUTO,
}

from masterthermconnect.exceptions import (
    MasterThermAuthenticationError,
    MasterThermConnectionError,
    MasterThermUnsupportedRole,
    MasterThermResponseFormatError,
    MasterThermTokenInvalid,
)
from masterthermconnect.auth import Auth
from masterthermconnect.thermostat import Thermostat

from .const import AUTH, DOMAIN
from homeassistant.const import ATTR_TEMPERATURE, TEMP_CELSIUS

_LOGGER = logging.getLogger(__name__)

SUPPORTED_HVAC_MODES = [HVAC_MODE_AUTO, HVAC_MODE_COOL, HVAC_MODE_HEAT, HVAC_MODE_OFF]
SUPPORTED_TARGET_TEMPERATURE_STEP = 0.5


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up entry."""
    auth: Auth = hass.data[DOMAIN][config_entry.entry_id][AUTH]
    if not (modules := auth.getModules()):
        _LOGGER.info("No modules found")
        return

    entities = []
    for devices in modules.values():
        for device in devices.values():
            entities.append(MasterThermClimate(auth, device))

    async_add_entities(entities, True)


class MasterThermClimate(ClimateEntity):
    """Representation of a MasterTherm climate device."""

    _attr_icon = "mdi:thermostat"
    _attr_hvac_mode = HVAC_MODE_HEAT
    _attr_hvac_modes = SUPPORTED_HVAC_MODES
    _attr_supported_features = SUPPORT_TARGET_TEMPERATURE
    _attr_target_temperature_step = SUPPORTED_TARGET_TEMPERATURE_STEP
    _attr_temperature_unit = TEMP_CELSIUS
    _attr_should_poll = True

    def __init__(self, auth, device):
        """Initialize the entity."""
        self._thermostat = Thermostat(auth, device["module_id"], device["device_id"])
        self._attr_name = device["module_name"]
        self._module_id = device["module_id"]
        self._device_id = device["device_id"]
        self._device_name = device["device_id"]

    # @property
    # def device_info(self):
    #     return {
    #         "identifiers": {
    #             # Serial numbers are unique identifiers within a specific domain
    #             (hue.DOMAIN, self.unique_id)
    #         },
    #         "name": self.name,
    #         "manufacturer": self.light.manufacturername,
    #         "model": self.light.productname,
    #         "sw_version": self.light.swversion,
    #         "via_device": (hue.DOMAIN, self.api.bridgeid),
    #     }

    # async def async_will_remove_from_hass(self) -> None:
    #     """Cancel refresh callback when entity is being removed from hass."""
    #     self.async_cancel_refresh_callback()

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        await self._thermostat.setTemperature(kwargs.get(ATTR_TEMPERATURE))

    async def async_update(self):
        """Retrieve latest state."""
        return await self._thermostat.getData()

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return True

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._thermostat.getCurrentTemperature()

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._thermostat.getTemperature()

    @property
    def hvac_mode(self):
        """Return current operation ie. heat, cool, fan."""

        mode = self._thermostat.getHVACMode()
        return HVAC_MODE_MAP.get(mode)

    # @property
    # def hvac_mode(self):
    #     """Return current operation ie. heat, cool, fan."""
    #     if not self._aircon.get_power_on():
    #         return HVAC_MODE_OFF

    #     mode: AirconMode = self._aircon.get_mode()
    #     return AIRCON_MODE_MAP.get(mode)

    # async def async_set_hvac_mode(self, hvac_mode):
    #     """Set HVAC mode."""
    #     if hvac_mode == HVAC_MODE_OFF:
    #         await self._aircon.set_power_on(False)
    #         return

    #     if not (mode := HVAC_MODE_TO_AIRCON_MODE.get(hvac_mode)):
    #         raise ValueError(f"Invalid hvac mode {hvac_mode}")

    #     await self._aircon.set_mode(mode)
    #     if not self._aircon.get_power_on():
    #         await self._aircon.set_power_on(True)

    # async def async_turn_on(self):
    #     """Turn device on."""
    #     await self._aircon.set_power_on(True)

    # async def async_turn_off(self):
    #     """Turn device off."""
    #     await self._aircon.set_power_on(False)
