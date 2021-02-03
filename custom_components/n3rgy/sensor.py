"""
Script file: sensor.py
Created on: Jan 29, 2021
Last modified on: Feb 3, 2021

Comments:
    Support for n3rgy data sensor

Notes:
    This API was not published to PyPI store yet.
    We can use simple request function.
"""

import logging
import async_timeout
import re
import requests

from requests.structures import CaseInsensitiveDict
from datetime import timedelta
from requests.exceptions import ConnectionError as ConnectError, HTTPError, Timeout
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from homeassistant.const import(
    ATTR_ATTRIBUTION,
)
from .const import (
    CONF_PROPERTY_ID,
    ATTRIBUTION,
    DEFAULT_NAME,
    SENSOR_NAME,
    SENSOR_TYPE,
    ICON,
    PLATFORM
)

_TIME_INTERVAL_SEC = 3600
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """
    Set up n3rgy data sensor
    :param hass: hass object
    :param entry: config entry
    :return: none
    """
    # read the configuration data
    host = None
    api_key = None
    property_id = None
    if entry and entry.data:
        host = entry.data.get(CONF_HOST)
        api_key = entry.data.get(CONF_API_KEY)
        property_id = entry.data.get(CONF_PROPERTY_ID)

    async def async_update_data():
        """
        Fetch data from API endpoint.
        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        :param: none
        :return: consumption value
        """
        try:
            # fetch n3rgy data
            start_at = datetime.now() + timedelta(minutes=-30)
            end_at = datetime.now()
            with async_timeout.timeout(_TIME_INTERVAL_SEC):
                response = await hass.async_add_executor_job(
                    do_read_consumption,
                    host,
                    api_key,
                    property_id,
                    start_at.strftime("%Y%m%d%H%M"),
                    end_at.strftime("%Y%m%d%H%M"),
                )

                # logging
                _LOGGER.info("Response from the host: %s", response.resource)
                return response
        
        except (TimeoutError) as timeout_err:
            _LOGGER.error(f"Timeout communicating with API: {str(timeout_err)}")
            raise UpdateFailed("Timeout communicating with API") from timeout_err
        except (ConnectError, HTTPError, Timeout, ValueError, TypeError) as err:
            _LOGGER.error(f"Error communicating with API: {str(err)}")
            raise UpdateFailed(f"Error communicating with API: {err}") from err
        
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=PLATFORM,
        update_method=async_update_data,
        update_interval=timedelta(seconds=100),
    )

    # fetch initial data so we have data when entities subscribe
    await coordinator.async_refresh()

    # add sensor
    async_add_entities([N3rgySensor(coordinator)])


def do_read_consumption(host, api_key, property_id, start_at, end_at):
    """
    List consumption values for an utility type on the provided accessible 
    property, within a certain time frame
    :param host: host URL
    :param api_key: API key
    :param property_id: authorized property id
    :param start_at: start date/time of the period in the format YYYYMMDDHHmm
    :param end_at: end date/time of the period in the format YYYYMMDDHHmm
    :return: consumption data list
    """
    # API validation
    if host is None:
        _LOGGER.error("API host URL not specified")
        raise ValueError("API host URL error")
    
    if api_key is None:
        _LOGGER.error("API key not specified")
        raise ValueError("API key error")

    # property_id validation
    if not re.search(r'[0-9]{13}||[0-9]{9}', property_id):
        _LOGGER.error("Invalid value for `property_id`, must conform to the pattern `/[0-9]{13}||[0-9]{9}/`")
        raise ValueError("Invalid value for parameter `property_id`, must conform to the pattern `/[0-9]{13}||[0-9]{9}/`")

    # n3rgy data api request
    url = f'{host}/{property_id}/electricity/consumption/1?start={start_at}&end={end_at}&granularity=halfhour'
    headers = CaseInsensitiveDict()
    headers["Authorization"] = api_key
    response = requests.get(url, headers=headers)
    return response


class N3rgySensor(Entity):
    """Implementation of a n3rgy data sensor"""

    def __init__(self, coordinator):
        """
        Initialize for n3rgy data sensor class
        :param coordinator: data coordinator object
        :return: none
        """
        self._name = SENSOR_NAME
        self._type = SENSOR_TYPE
        self._state = None
        self._unit_of_measurement = None
        self._coordinator = coordinator
        self._attributes = {
            ATTR_ATTRIBUTION: ATTRIBUTION,
        }

    @property
    def name(self):
        """
        Return the name of the sensor
        :param: none
        :return: sensor name
        """
        return f"{DEFAULT_NAME} {self._name}"

    @property
    def unique_id(self):
        """
        Return sensor unique id
        :param: none
        :return: unique id
        """
        return self._type

    @property
    def state(self):
        """
        Return the state of the sensor
        :param: none
        :return: sensor state
        """
        return self._state
    
    @property
    def icon(self):
        """
        Icon for each sensor
        :param: none
        :return: sensor icon
        """
        return ICON

    @property
    def unit_of_measurement(self):
        """
        Return the unit of measurement of this entity, if any
        :param: none
        :return: data unit
        """
        if self._coordinator.data:
            return self._coordinator.data.unit
        return None

    @property
    def should_poll(self):
        """
        No need to poll.
        Coordinator notifies entity of updates
        :param: none
        :return: false
        """
        return False

    @property
    def device_state_attributes(self):
        """
        Return the state attributes
        :param: none
        :return: state attributes
        """
        if not self._coordinator.data:
            return None
        return self._attributes

    @property
    def available(self):
        """
        Return if entity is available
        :param: none
        :return: true is sensor is available, false otherwise
        """
        return self._coordinator.last_update_success

    async def async_added_to_hass(self):
        """
        When entity is added to hass
        :param: none
        :return: none
        """
        self.async_on_remove(
            self._coordinator.async_add_listener(self.async_write_ha_state)
        )
        if self._coordinator.data:
            self._state = self._coordinator.data.values

    async def async_update(self):
        """
        Update the entity
        Only used by the generic entity update service
        :param: none
        :return: none
        """
        await self._coordinator.async_request_refresh()