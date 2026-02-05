"""Fixtures for Arvee tests."""
from unittest.mock import patch, MagicMock

import pytest

from homeassistant.core import HomeAssistant


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests."""
    yield


@pytest.fixture
def mock_tzfpy():
    """Mock tzfpy.get_tz function."""
    mock_get_tz = MagicMock(return_value="America/New_York")
    with patch.dict("sys.modules", {"tzfpy": MagicMock(get_tz=mock_get_tz)}):
        with patch("custom_components.arvee.get_tz", mock_get_tz, create=True):
            with patch("custom_components.arvee.TZFPY_AVAILABLE", True):
                yield mock_get_tz


@pytest.fixture
async def mock_gps_entities(hass: HomeAssistant):
    """Create mock GPS entities."""
    hass.states.async_set("sensor.test_latitude", "40.7128")
    hass.states.async_set("sensor.test_longitude", "-74.0060")
    return {
        "latitude": "sensor.test_latitude",
        "longitude": "sensor.test_longitude",
    }


@pytest.fixture
async def mock_gps_entities_with_elevation(hass: HomeAssistant):
    """Create mock GPS entities including elevation."""
    hass.states.async_set("sensor.test_latitude", "40.7128")
    hass.states.async_set("sensor.test_longitude", "-74.0060")
    hass.states.async_set("sensor.test_elevation", "100")
    return {
        "latitude": "sensor.test_latitude",
        "longitude": "sensor.test_longitude",
        "elevation": "sensor.test_elevation",
    }


@pytest.fixture
async def mock_gps_entities_invalid(hass: HomeAssistant):
    """Create mock GPS entities with invalid values."""
    hass.states.async_set("sensor.test_latitude", "unknown")
    hass.states.async_set("sensor.test_longitude", "-74.0060")
    return {
        "latitude": "sensor.test_latitude",
        "longitude": "sensor.test_longitude",
    }


@pytest.fixture
async def mock_gps_entities_invalid_elevation(hass: HomeAssistant):
    """Create mock GPS entities with invalid elevation."""
    hass.states.async_set("sensor.test_latitude", "40.7128")
    hass.states.async_set("sensor.test_longitude", "-74.0060")
    hass.states.async_set("sensor.test_elevation", "unknown")
    return {
        "latitude": "sensor.test_latitude",
        "longitude": "sensor.test_longitude",
        "elevation": "sensor.test_elevation",
    }
