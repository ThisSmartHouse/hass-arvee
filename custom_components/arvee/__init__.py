import homeassistant.core as ha

import voluptuous as vol

import aiohttp
from homeassistant import core
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.service import async_register_admin_service
from .const import (
    DOMAIN,
    ATTR_TIMEZONE,
    ATTR_LATITUDE,
    ATTR_LONGITUDE,
    SERVICE_SET_TIMEZONE, 
    SERVICE_SET_TIMEZONE_GEO
)

async def async_setup(hass: core.HomeAssistant, config: dict) -> bool:
    """Set up the Arvee component."""

    async def async_set_timezone_geo(call: ha.ServiceCall) -> None:
        """Service handler to set timezone by lat/lng"""
        async with aiohttp.ClientSession() as session:
            async with session.get("https://timeapi.io/api/TimeZone/coordinate", params={"latitude": call.data[ATTR_LATITUDE], "longitude": call.data[ATTR_LONGITUDE]}) as response:
                json_data = await response.json()
        result = json_data.get("timeZone")
        
        if result is None:
            return

        await hass.config.async_update(
            time_zone=result
        )

    async_register_admin_service(
        hass,
        DOMAIN,
        SERVICE_SET_TIMEZONE_GEO,
        async_set_timezone_geo,
        vol.Schema({
            ATTR_LATITUDE: cv.latitude,
            ATTR_LONGITUDE: cv.longitude
        })
    )

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
