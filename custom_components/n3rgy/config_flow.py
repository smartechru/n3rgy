"""
Script file: config_flow.py
Created on: Jan 31, 2021
Last modified on: Feb 20, 2021

Comments:
    Config flow for n3rgy data
"""

import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.const import (
    CONF_NAME,
    CONF_HOST,
    CONF_API_KEY
)
from .const import (
    CONF_PROPERTY_ID,
    CONF_ENVIRONMENT,
    CONF_DAILY_UPDATE,
    CONF_UTILITY,
    CONF_START,
    CONF_END,
    DEFAULT_NAME,
    DEFAULT_HOST,
    UTILITY_ELECTRICITY,
    UTILITY_GAS,
    DOMAIN
)

_LOGGER = logging.getLogger(__name__)


class N3rgyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for n3rgy data"""

    VERSION = 1.0
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """
        Handle a flow initialized by the user
        :param user_input: user input
        :return: config form
        """
        errors = {}

        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            try:
                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data=user_input
                )
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        # schema
        config = {
            vol.Required(CONF_HOST, default=DEFAULT_HOST): str,
            vol.Required(CONF_API_KEY): str,
            vol.Required(CONF_PROPERTY_ID): str,
            vol.Optional(CONF_NAME, default=DEFAULT_NAME): str
        }

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(config),
            errors=errors
        )

    async def async_step_import(self, import_config):
        """
        Import from config
        :param import_config: import config values
        :return: config form
        """
        # validate config values
        return await self.async_step_user(user_input=import_config)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """
        Options callback for n3rgy data
        :param config_entry: config entry
        :return: option form
        """
        return N3rgyOptionsFlow(config_entry)


class N3rgyOptionsFlow(config_entries.OptionsFlow):
    """Config flow options for AccuWeather."""

    def __init__(self, config_entry):
        """
        Initialize n3rgy options flow
        :param config_entry: config entry
        :return: none
        """
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """
        Manage the options
        :param user_input: user input
        :return: option form
        """
        return await self.async_step_user()

    async def async_step_user(self, user_input=None):
        """
        Handle a flow initialized by the user
        :param user_input: user input
        :return: option form
        """
        errors = {}

        if user_input is not None:
            try:
                return self.async_create_entry(
                    title="",
                    data=user_input
                )
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        # schema
        config = {
            vol.Optional(CONF_ENVIRONMENT, default=self.config_entry.options.get(CONF_ENVIRONMENT)): bool,
            vol.Optional(CONF_DAILY_UPDATE, default=self.config_entry.options.get(CONF_DAILY_UPDATE)): bool,
            vol.Optional(CONF_UTILITY, default=self.config_entry.options.get(CONF_UTILITY)): vol.In([UTILITY_ELECTRICITY, UTILITY_GAS]),
            vol.Optional(CONF_START, default=self.config_entry.options.get(CONF_START)): str,
            vol.Optional(CONF_END, default=self.config_entry.options.get(CONF_END)): str
        }

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(config),
            errors=errors
        )
