import homeassistant.core as ha

import voluptuous as vol

from homeassistant import core
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.service import async_register_admin_service
from .const import DOMAIN, ATTR_TIMEZONE, SERVICE_SET_TIMEZONE

async def async_setup(hass: core.HomeAssistant, config: dict) -> bool:
    """Set up the Arvee component."""

    async def async_set_timezone(call: ha.ServiceCall) -> None:
        """Service handler to set timezone."""
        await hass.config.async_update(
            time_zone=call.data[ATTR_TIMEZONE]
        )

    async_register_admin_service(
        hass,
        DOMAIN,
        SERVICE_SET_TIMEZONE,
        async_set_timezone,
        vol.Schema({ATTR_TIMEZONE: cv.time_zone}),
    )

    return True
