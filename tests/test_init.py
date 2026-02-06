"""Test component setup."""
from unittest.mock import patch

import pytest

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from custom_components.arvee.const import (
    DOMAIN,
    SERVICE_SET_TIMEZONE,
    SERVICE_SET_GEO_TIMEZONE,
    ATTR_LATITUDE,
    ATTR_LONGITUDE,
    ATTR_ELEVATION,
    ATTR_ELEVATION_UNIT,
    ATTR_TIMEZONE,
    UNIT_FEET,
    FEET_TO_METERS,
)
from custom_components.arvee import _haversine_miles
from custom_components.arvee.config_flow import _is_numeric


@pytest.mark.asyncio
class TestAsyncSetup:
    """Test component setup."""

    async def test_async_setup(self, hass: HomeAssistant):
        """Test the component gets setup."""
        assert await async_setup_component(hass, DOMAIN, {}) is True

    async def test_services_registered(self, hass: HomeAssistant):
        """Test services are registered after setup."""
        await async_setup_component(hass, DOMAIN, {})
        await hass.async_block_till_done()

        assert hass.services.has_service(DOMAIN, SERVICE_SET_TIMEZONE)
        assert hass.services.has_service(DOMAIN, SERVICE_SET_GEO_TIMEZONE)


class TestHaversine:
    """Test haversine distance calculation."""

    def test_same_location(self):
        """Test distance is zero for same location."""
        distance = _haversine_miles(40.7128, -74.0060, 40.7128, -74.0060)
        assert distance == 0.0

    def test_known_distance(self):
        """Test distance between NYC and LA (approx 2,451 miles)."""
        distance = _haversine_miles(40.7128, -74.0060, 34.0522, -118.2437)
        assert 2400 < distance < 2500

    def test_short_distance(self):
        """Test short distance calculation."""
        distance = _haversine_miles(40.7128, -74.0060, 40.7273, -74.0060)
        assert 0.9 < distance < 1.1


class TestIsNumeric:
    """Test _is_numeric helper function."""

    def test_valid_float(self):
        """Test valid float string."""
        assert _is_numeric("40.7128") is True

    def test_valid_negative(self):
        """Test valid negative float string."""
        assert _is_numeric("-74.0060") is True

    def test_valid_integer(self):
        """Test valid integer string."""
        assert _is_numeric("40") is True

    def test_unknown(self):
        """Test unknown state."""
        assert _is_numeric("unknown") is False

    def test_unavailable(self):
        """Test unavailable state."""
        assert _is_numeric("unavailable") is False

    def test_none(self):
        """Test None value."""
        assert _is_numeric(None) is False

    def test_invalid_string(self):
        """Test invalid string."""
        assert _is_numeric("not_a_number") is False


@pytest.mark.asyncio
class TestSetTimezoneService:
    """Test set_timezone service."""

    async def test_set_timezone(self, hass: HomeAssistant):
        """Test setting timezone via service."""
        await async_setup_component(hass, DOMAIN, {})
        await hass.async_block_till_done()

        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_TIMEZONE,
            {ATTR_TIMEZONE: "America/Los_Angeles"},
            blocking=True,
        )

        assert hass.config.time_zone == "America/Los_Angeles"


@pytest.mark.asyncio
class TestSetGeoTimezoneService:
    """Test set_geo_timezone service."""

    async def test_set_geo_timezone(self, hass: HomeAssistant, mock_tzfpy):
        """Test setting timezone via coordinates."""
        await async_setup_component(hass, DOMAIN, {})
        await hass.async_block_till_done()

        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_GEO_TIMEZONE,
            {ATTR_LATITUDE: 40.7128, ATTR_LONGITUDE: -74.0060},
            blocking=True,
        )

        assert hass.config.latitude == 40.7128
        assert hass.config.longitude == -74.0060
        assert hass.config.time_zone == "America/New_York"
        mock_tzfpy.assert_called_once_with(-74.0060, 40.7128)

    async def test_set_geo_timezone_with_elevation(self, hass: HomeAssistant, mock_tzfpy):
        """Test setting timezone via coordinates with elevation."""
        await async_setup_component(hass, DOMAIN, {})
        await hass.async_block_till_done()

        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_GEO_TIMEZONE,
            {ATTR_LATITUDE: 40.7128, ATTR_LONGITUDE: -74.0060, ATTR_ELEVATION: 100},
            blocking=True,
        )

        assert hass.config.latitude == 40.7128
        assert hass.config.longitude == -74.0060
        assert hass.config.elevation == 100
        assert hass.config.time_zone == "America/New_York"
        mock_tzfpy.assert_called_once_with(-74.0060, 40.7128)

    async def test_set_geo_timezone_with_elevation_feet(self, hass: HomeAssistant, mock_tzfpy):
        """Test setting timezone via coordinates with elevation in feet."""
        await async_setup_component(hass, DOMAIN, {})
        await hass.async_block_till_done()

        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_GEO_TIMEZONE,
            {
                ATTR_LATITUDE: 40.7128,
                ATTR_LONGITUDE: -74.0060,
                ATTR_ELEVATION: 328,
                ATTR_ELEVATION_UNIT: UNIT_FEET,
            },
            blocking=True,
        )

        assert hass.config.latitude == 40.7128
        assert hass.config.longitude == -74.0060
        # 328 feet * 0.3048 = 99.9744 meters
        assert abs(hass.config.elevation - (328 * FEET_TO_METERS)) < 0.01
        assert hass.config.time_zone == "America/New_York"
        mock_tzfpy.assert_called_once_with(-74.0060, 40.7128)
