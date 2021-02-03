"""
Script file: config_flow.py
Created on: Jan 31, 2021
Last modified on: Feb 3, 2021

Comments:
    Config flow for n3rgy data
"""

import logging
import voluptuous as vol
import n3rgyDataApi as n3rgy

from homeassistant import config_entries
from homeassistant.const import (
    CONF_NAME,
    CONF_HOST,
    CONF_API_KEY
)
from .const import (
    CONF_PROPERTY_ID,
    DEFAULT_NAME,
    DOMAIN
)

_LOGGER = logging.getLogger(__name__)


class N3rgyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for n3rgy data"""

    VERSION = 1.0
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    config = {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_API_KEY): str,
        vol.Required(CONF_PROPERTY_ID): str,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): str
    }

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
                # load configuration
                config = n3rgy.Configuration()
                config.api_key['Authorization'] = user_input[CONF_API_KEY]
                config.host = user_input[CONF_HOST]
                
                # client initialization
                n3rgy_client = n3rgy.DefaultApi(n3rgy.ApiClient(config))
                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data=user_input
                )

                # error handler
                errors["base"] = "invalid_api_key"

            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(self.config),
            errors=errors
        )

    async def async_step_import(self, import_config):
        """
        Import from config
        :param import_config: import config values
        :return: config form data
        """
        # validate config values
        return await self.async_step_user(user_input=import_config)