"""Config flow for Arvee integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (
    DOMAIN,
    CONF_LATITUDE_ENTITY,
    CONF_LONGITUDE_ENTITY,
    CONF_UPDATE_THRESHOLD,
    DEFAULT_UPDATE_THRESHOLD,
)

_LOGGER = logging.getLogger(__name__)


def get_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    """Get the config schema with optional defaults."""
    defaults = defaults or {}
    return vol.Schema({
        vol.Required(
            CONF_LATITUDE_ENTITY,
            default=defaults.get(CONF_LATITUDE_ENTITY, ""),
        ): selector.EntitySelector(
            selector.EntitySelectorConfig(domain=["sensor", "device_tracker", "input_number"]),
        ),
        vol.Required(
            CONF_LONGITUDE_ENTITY,
            default=defaults.get(CONF_LONGITUDE_ENTITY, ""),
        ): selector.EntitySelector(
            selector.EntitySelectorConfig(domain=["sensor", "device_tracker", "input_number"]),
        ),
        vol.Optional(
            CONF_UPDATE_THRESHOLD,
            default=defaults.get(CONF_UPDATE_THRESHOLD, DEFAULT_UPDATE_THRESHOLD),
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=0.1,
                max=100,
                step=0.1,
                unit_of_measurement="miles",
                mode=selector.NumberSelectorMode.BOX,
            ),
        ),
    })


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Arvee."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        # Only allow one instance
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            # Validate that entities exist and have numeric values
            lat_entity = user_input[CONF_LATITUDE_ENTITY]
            lon_entity = user_input[CONF_LONGITUDE_ENTITY]

            lat_state = self.hass.states.get(lat_entity)
            lon_state = self.hass.states.get(lon_entity)

            if lat_state is None:
                errors[CONF_LATITUDE_ENTITY] = "entity_not_found"
            elif not _is_numeric(lat_state.state):
                errors[CONF_LATITUDE_ENTITY] = "invalid_latitude"

            if lon_state is None:
                errors[CONF_LONGITUDE_ENTITY] = "entity_not_found"
            elif not _is_numeric(lon_state.state):
                errors[CONF_LONGITUDE_ENTITY] = "invalid_longitude"

            if not errors:
                return self.async_create_entry(title="Arvee", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=get_schema(),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> OptionsFlowHandler:
        """Get the options flow for this handler."""
        return OptionsFlowHandler()


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Arvee."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            lat_entity = user_input[CONF_LATITUDE_ENTITY]
            lon_entity = user_input[CONF_LONGITUDE_ENTITY]

            lat_state = self.hass.states.get(lat_entity)
            lon_state = self.hass.states.get(lon_entity)

            if lat_state is None:
                errors[CONF_LATITUDE_ENTITY] = "entity_not_found"
            elif not _is_numeric(lat_state.state):
                errors[CONF_LATITUDE_ENTITY] = "invalid_latitude"

            if lon_state is None:
                errors[CONF_LONGITUDE_ENTITY] = "entity_not_found"
            elif not _is_numeric(lon_state.state):
                errors[CONF_LONGITUDE_ENTITY] = "invalid_longitude"

            if not errors:
                return self.async_create_entry(title="", data=user_input)

        # Use current config as defaults
        current_config = {**self.config_entry.data, **self.config_entry.options}

        return self.async_show_form(
            step_id="init",
            data_schema=get_schema(current_config),
            errors=errors,
        )


def _is_numeric(value: str) -> bool:
    """Check if a string value is numeric."""
    if value in ("unknown", "unavailable", None):
        return False
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False
