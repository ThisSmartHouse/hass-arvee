"""
Arvee - Mobile Home Assistant timezone management.

Automatically updates Home Assistant's location and timezone
based on GPS coordinates from configured entities.
"""
from __future__ import annotations

import logging
import math
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import HomeAssistant, ServiceCall, callback, Event
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.typing import ConfigType

from .const import (
    DOMAIN,
    SERVICE_SET_TIMEZONE,
    SERVICE_SET_GEO_TIMEZONE,
    CONF_LATITUDE_ENTITY,
    CONF_LONGITUDE_ENTITY,
    CONF_ELEVATION_ENTITY,
    CONF_UPDATE_THRESHOLD,
    DEFAULT_UPDATE_THRESHOLD,
    ATTR_LATITUDE,
    ATTR_LONGITUDE,
    ATTR_ELEVATION,
    ATTR_ELEVATION_UNIT,
    ATTR_TIMEZONE,
    UNIT_METERS,
    UNIT_FEET,
    FEET_TO_METERS,
)

_LOGGER = logging.getLogger(__name__)

# Try to import tzfpy
try:
    from tzfpy import get_tz
    TZFPY_AVAILABLE = True
except ImportError:
    TZFPY_AVAILABLE = False
    _LOGGER.warning("tzfpy not available, timezone lookups will not work")


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Arvee component from YAML (services only)."""
    await _async_register_services(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Arvee from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    # Store config
    hass.data[DOMAIN][entry.entry_id] = {
        "config": entry.data,
        "last_lat": None,
        "last_lon": None,
        "last_elev": None,
        "unsub": None,
    }

    # Register services if not already done
    await _async_register_services(hass)

    # Set up entity listeners after HA is fully started
    async def async_startup(event: Event) -> None:
        """Set up listeners after startup."""
        await _async_setup_listeners(hass, entry)

    if hass.is_running:
        await _async_setup_listeners(hass, entry)
    else:
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, async_startup)

    # Listen for options updates
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Arvee config entry."""
    data = hass.data[DOMAIN].pop(entry.entry_id, {})
    
    # Unsubscribe from state changes
    if unsub := data.get("unsub"):
        unsub()

    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def _async_register_services(hass: HomeAssistant) -> None:
    """Register Arvee services."""
    if hass.services.has_service(DOMAIN, SERVICE_SET_TIMEZONE):
        return  # Already registered

    async def async_set_timezone(call: ServiceCall) -> None:
        """Service to set timezone directly."""
        timezone = call.data[ATTR_TIMEZONE]
        await hass.config.async_update(time_zone=timezone)
        _LOGGER.info("Timezone updated to: %s", timezone)

    async def async_set_geo_timezone(call: ServiceCall) -> None:
        """Service to set timezone based on coordinates."""
        latitude = call.data[ATTR_LATITUDE]
        longitude = call.data[ATTR_LONGITUDE]
        elevation = call.data.get(ATTR_ELEVATION)
        elevation_unit = call.data.get(ATTR_ELEVATION_UNIT, UNIT_METERS)

        if not TZFPY_AVAILABLE:
            _LOGGER.error("tzfpy not available, cannot look up timezone")
            return

        timezone = await hass.async_add_executor_job(get_tz, longitude, latitude)

        if timezone is None:
            _LOGGER.error(
                "Could not determine timezone for coordinates: %s, %s",
                latitude,
                longitude,
            )
            return

        # Convert elevation to meters if provided in feet
        if elevation is not None and elevation_unit == UNIT_FEET:
            elevation = elevation * FEET_TO_METERS
            _LOGGER.debug(
                "Converted elevation from feet to meters: %.1f m",
                elevation,
            )

        update_kwargs = {
            "latitude": latitude,
            "longitude": longitude,
            "time_zone": timezone,
        }
        if elevation is not None:
            update_kwargs["elevation"] = elevation

        await hass.config.async_update(**update_kwargs)

        if elevation is not None:
            _LOGGER.info(
                "Location updated to: %s, %s, elevation %s m (timezone: %s)",
                latitude,
                longitude,
                elevation,
                timezone,
            )
        else:
            _LOGGER.info(
                "Location updated to: %s, %s (timezone: %s)",
                latitude,
                longitude,
                timezone,
            )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_TIMEZONE,
        async_set_timezone,
        schema=vol.Schema({vol.Required(ATTR_TIMEZONE): cv.time_zone}),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_GEO_TIMEZONE,
        async_set_geo_timezone,
        schema=vol.Schema({
            vol.Required(ATTR_LATITUDE): cv.latitude,
            vol.Required(ATTR_LONGITUDE): cv.longitude,
            vol.Optional(ATTR_ELEVATION): vol.Coerce(float),
            vol.Optional(ATTR_ELEVATION_UNIT, default=UNIT_METERS): vol.In(
                [UNIT_METERS, UNIT_FEET]
            ),
        }),
    )


async def _async_setup_listeners(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Set up state change listeners for GPS entities."""
    config = {**entry.data, **entry.options}
    lat_entity = config[CONF_LATITUDE_ENTITY]
    lon_entity = config[CONF_LONGITUDE_ENTITY]
    elev_entity = config.get(CONF_ELEVATION_ENTITY)
    threshold = config.get(CONF_UPDATE_THRESHOLD, DEFAULT_UPDATE_THRESHOLD)

    data = hass.data[DOMAIN][entry.entry_id]

    # Initialize with current HA config
    data["last_lat"] = hass.config.latitude
    data["last_lon"] = hass.config.longitude
    data["last_elev"] = hass.config.elevation

    @callback
    def async_handle_state_change(event: Event) -> None:
        """Handle state changes of GPS entities."""
        hass.async_create_task(_async_process_location_update(hass, entry, threshold))

    # Track lat/lon entities, and optionally elevation
    entities_to_track = [lat_entity, lon_entity]
    if elev_entity:
        entities_to_track.append(elev_entity)

    unsub = async_track_state_change_event(
        hass,
        entities_to_track,
        async_handle_state_change,
    )
    data["unsub"] = unsub

    # Do an initial update
    await _async_process_location_update(hass, entry, threshold)


async def _async_process_location_update(
    hass: HomeAssistant,
    entry: ConfigEntry,
    threshold: float,
) -> None:
    """Process a location update from GPS entities."""
    config = {**entry.data, **entry.options}
    lat_entity = config[CONF_LATITUDE_ENTITY]
    lon_entity = config[CONF_LONGITUDE_ENTITY]
    elev_entity = config.get(CONF_ELEVATION_ENTITY)

    data = hass.data[DOMAIN][entry.entry_id]

    # Get current values
    lat_state = hass.states.get(lat_entity)
    lon_state = hass.states.get(lon_entity)

    if lat_state is None or lon_state is None:
        _LOGGER.debug("GPS entities not available yet")
        return

    try:
        new_lat = float(lat_state.state)
        new_lon = float(lon_state.state)
    except (ValueError, TypeError):
        _LOGGER.debug(
            "Invalid GPS values: lat=%s, lon=%s",
            lat_state.state,
            lon_state.state,
        )
        return

    # Get elevation if configured
    new_elev = None
    if elev_entity:
        elev_state = hass.states.get(elev_entity)
        if elev_state is not None:
            try:
                new_elev = float(elev_state.state)
                # Convert feet to meters if needed (HA uses meters)
                unit = elev_state.attributes.get("unit_of_measurement", "").lower()
                if unit in (UNIT_FEET, "feet"):
                    new_elev = new_elev * FEET_TO_METERS
                    _LOGGER.debug(
                        "Converted elevation from feet to meters: %.1f m",
                        new_elev,
                    )
            except (ValueError, TypeError):
                _LOGGER.debug(
                    "Invalid elevation value: %s",
                    elev_state.state,
                )

    # Check if we've moved enough
    last_lat = data.get("last_lat")
    last_lon = data.get("last_lon")

    if last_lat is not None and last_lon is not None:
        distance = _haversine_miles(last_lat, last_lon, new_lat, new_lon)
        if distance < threshold:
            _LOGGER.debug(
                "Movement of %.2f miles is below threshold of %.2f miles",
                distance,
                threshold,
            )
            return
        _LOGGER.debug("Movement of %.2f miles exceeds threshold", distance)

    # Update stored position
    data["last_lat"] = new_lat
    data["last_lon"] = new_lon
    if new_elev is not None:
        data["last_elev"] = new_elev

    # Look up timezone
    if not TZFPY_AVAILABLE:
        _LOGGER.error("tzfpy not available, cannot look up timezone")
        return

    timezone = await hass.async_add_executor_job(get_tz, new_lon, new_lat)

    if timezone is None:
        _LOGGER.warning(
            "Could not determine timezone for coordinates: %s, %s",
            new_lat,
            new_lon,
        )
        # Still update location even if timezone lookup fails
        update_kwargs = {"latitude": new_lat, "longitude": new_lon}
        if new_elev is not None:
            update_kwargs["elevation"] = new_elev
        await hass.config.async_update(**update_kwargs)
        return

    # Update Home Assistant config
    update_kwargs = {
        "latitude": new_lat,
        "longitude": new_lon,
        "time_zone": timezone,
    }
    if new_elev is not None:
        update_kwargs["elevation"] = new_elev

    await hass.config.async_update(**update_kwargs)

    if new_elev is not None:
        _LOGGER.info(
            "Arvee updated location to: %s, %s, elevation %s m (timezone: %s)",
            new_lat,
            new_lon,
            new_elev,
            timezone,
        )
    else:
        _LOGGER.info(
            "Arvee updated location to: %s, %s (timezone: %s)",
            new_lat,
            new_lon,
            timezone,
        )


def _haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the distance between two points in miles using Haversine formula."""
    R = 3959  # Earth's radius in miles

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c
