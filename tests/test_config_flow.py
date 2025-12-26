"""Test config flow for Arvee."""
from unittest.mock import patch

import pytest

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.arvee.const import (
    DOMAIN,
    CONF_LATITUDE_ENTITY,
    CONF_LONGITUDE_ENTITY,
    CONF_UPDATE_THRESHOLD,
)


@pytest.mark.asyncio
class TestConfigFlow:
    """Test the config flow."""

    async def test_form(self, hass: HomeAssistant, mock_gps_entities):
        """Test we get the form."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "user"
        assert result["errors"] == {}

    async def test_form_valid_input(self, hass: HomeAssistant, mock_gps_entities, mock_tzfpy):
        """Test form with valid input creates entry."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_LATITUDE_ENTITY: "sensor.test_latitude",
                CONF_LONGITUDE_ENTITY: "sensor.test_longitude",
                CONF_UPDATE_THRESHOLD: 10.0,
            },
        )

        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["title"] == "Arvee"
        assert result["data"] == {
            CONF_LATITUDE_ENTITY: "sensor.test_latitude",
            CONF_LONGITUDE_ENTITY: "sensor.test_longitude",
            CONF_UPDATE_THRESHOLD: 10.0,
        }

    async def test_form_entity_not_found(self, hass: HomeAssistant):
        """Test form with non-existent entity shows error."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_LATITUDE_ENTITY: "sensor.nonexistent_lat",
                CONF_LONGITUDE_ENTITY: "sensor.nonexistent_lon",
                CONF_UPDATE_THRESHOLD: 10.0,
            },
        )

        assert result["type"] == FlowResultType.FORM
        assert result["errors"][CONF_LATITUDE_ENTITY] == "entity_not_found"
        assert result["errors"][CONF_LONGITUDE_ENTITY] == "entity_not_found"

    async def test_form_invalid_latitude(self, hass: HomeAssistant, mock_gps_entities_invalid):
        """Test form with invalid latitude value shows error."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_LATITUDE_ENTITY: "sensor.test_latitude",
                CONF_LONGITUDE_ENTITY: "sensor.test_longitude",
                CONF_UPDATE_THRESHOLD: 10.0,
            },
        )

        assert result["type"] == FlowResultType.FORM
        assert result["errors"][CONF_LATITUDE_ENTITY] == "invalid_latitude"

    async def test_already_configured(self, hass: HomeAssistant, mock_gps_entities, mock_tzfpy):
        """Test we abort if already configured."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_LATITUDE_ENTITY: "sensor.test_latitude",
                CONF_LONGITUDE_ENTITY: "sensor.test_longitude",
                CONF_UPDATE_THRESHOLD: 10.0,
            },
        )

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] == FlowResultType.ABORT
        assert result["reason"] == "already_configured"


@pytest.mark.asyncio
class TestOptionsFlow:
    """Test the options flow."""

    async def test_options_flow(self, hass: HomeAssistant, mock_gps_entities, mock_tzfpy):
        """Test options flow."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_LATITUDE_ENTITY: "sensor.test_latitude",
                CONF_LONGITUDE_ENTITY: "sensor.test_longitude",
                CONF_UPDATE_THRESHOLD: 10.0,
            },
        )
        await hass.async_block_till_done()

        entry = hass.config_entries.async_entries(DOMAIN)[0]

        result = await hass.config_entries.options.async_init(entry.entry_id)
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "init"

        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {
                CONF_LATITUDE_ENTITY: "sensor.test_latitude",
                CONF_LONGITUDE_ENTITY: "sensor.test_longitude",
                CONF_UPDATE_THRESHOLD: 25.0,
            },
        )

        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_UPDATE_THRESHOLD] == 25.0
