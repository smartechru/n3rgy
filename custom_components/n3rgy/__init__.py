"""
Script file: __init__.py
Created on: Jan 29, 2021
Last modified on: Feb 9, 2021

Comments:
    n3rgy data API integration
"""

import logging

from .const import (
    DOMAIN,
    PLATFORM,
    DATA_LISTENER
)

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass, config) -> bool:
    """
    Old way of setting up n3rgy component using YAML
    :param hass: home assistant object
    :param config: config file
    :return: true (expired)
    """
    hass.data[DOMAIN] = {DATA_LISTENER: {}}
    return True


async def async_setup_entry(hass, config_entry):
    """
    Set up n3rgy component from a config entry
    :param hass: home assistant object
    :param config_entry: config entry
    :return: true if successful
    """
    # update options
    hass.data[DOMAIN][DATA_LISTENER][config_entry.entry_id] = config_entry.add_update_listener(async_reload_entry)
    
    # add sensor
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(config_entry, PLATFORM)
    )
    return True


async def async_unload_entry(hass, config_entry):
    """
    Unload a config entry
    :param hass: home assistant object
    :param config_entry: config entry
    :return: true if successful, false otherwise
    """
    # remove config entry
    try:
        await hass.config_entries.async_forward_entry_unload(config_entry, PLATFORM)
        remove_listener = hass.data[DOMAIN][DATA_LISTENER].pop(config_entry.entry_id)
        remove_listener()
        _LOGGER.debug("Successfully removed sensor from the n3rgy integration!")
        return True
    except ValueError as ex:
        _LOGGER.warning(f"Failed to remove sensor: {str(ex)}")
        return False


async def async_reload_entry(hass, config_entry):
    """
    Handle an options update
    :param hass: home assistant object
    :param config_entry: config entry
    :return: none
    """
    await hass.config_entries.async_reload(config_entry.entry_id)
    _LOGGER.debug("Options parameter updated!")
