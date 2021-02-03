"""
Script file: __init__.py
Created on: Jan 29, 2021
Last modified on: Feb 3, 2021

Comments:
    n3rgy data API integration
"""

import logging
import n3rgyDataApi as n3rgy

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.const import (
    CONF_API_KEY,
    CONF_HOST
)
from .const import (
    DOMAIN,
    PLATFORM
)

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """
    Old way of setting up n3rgy component using YAML
    :param hass: home assistant object
    :param config: config file
    :return: true (expired)
    """
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """
    Set up n3rgy component from a config entry
    :param hass: home assistant object
    :param entry: config entry
    :return: true if successful
    """
    # store an n3rgyDataApi object for n3rgy to access
    try:
        config = n3rgy.Configuration()
        config.api_key['Authorization'] = entry.data.get(CONF_API_KEY)
        config.host = entry.data.get(CONF_HOST)
        
        # load configuration
        n3rgy_client = n3rgy.DefaultApi(n3rgy.ApiClient(config))
        hass.data[DOMAIN][entry.entry_id] = n3rgy_client
    except Exception as ex:
        _LOGGER.error(f"Unable to connect to n3rgyDataApi: {str(ex)}")
        raise ConfigEntryNotReady from ex

    # add sensor
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, PLATFORM)
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """
    Unload a config entry
    :param hass: home assistant object
    :param entry: config entry
    :return: true if successful, false otherwise
    """
    # unload n3rgyDataApi client
    hass.data[DOMAIN][entry.entry_id] = None
    
    # remove config entry
    try:
        await hass.config_entries.async_forward_entry_unload(entry, PLATFORM)
        _LOGGER.info("Successfully removed sensor from the n3rgy integration!")
        return True
    except ValueError as ex:
        _LOGGER.error(f"Failed to remove sensor: {str(ex)}")
        return False
