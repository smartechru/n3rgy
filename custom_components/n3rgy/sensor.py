"""
Script file: sensor.py
Created on: Jan 29, 2021
Last modified on: Feb 9, 2021

Comments:
    Support for n3rgy data sensor
"""

import logging
import async_timeout

from datetime import datetime, timedelta
from requests.exceptions import ConnectionError as ConnectError, HTTPError, Timeout
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from homeassistant.const import(
    ATTR_ATTRIBUTION,
    CONF_HOST,
    CONF_API_KEY
)
from .const import (
    CONF_PROPERTY_ID,
    CONF_ENVIRONMENT,
    CONF_START,
    CONF_END,
    PLATFORM,
    ATTRIBUTION,
    DEFAULT_NAME,
    DEFAULT_LIVE_ENVIRONMENT,
    SENSOR_NAME,
    SENSOR_TYPE,
    ICON,
    INPUT_DATETIME_FORMAT,
    ATTR_DATETIME_FORMAT,
    ATTR_START_DATETIME,
    ATTR_END_DATETIME
)
from .n3rgy_api import N3rgyDataApi, N3rgyGrantConsent

_TIME_INTERVAL_SEC = 3600
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """
    Set up n3rgy data sensor
    :param hass: hass object
    :param entry: config entry
    :return: none
    """
    # in-line function
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
            response = await hass.async_add_executor_job(
                do_read_consumption,
                entry
            )
            return response

        except (TimeoutError) as timeout_err:
            raise UpdateFailed("Timeout communicating with API") from timeout_err
        except (ConnectError, HTTPError, Timeout, ValueError, TypeError) as err:
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
    async_add_entities([N3rgySensor(coordinator)], True)


def do_read_consumption(config_entry):
    """
    List consumption values for an utility type on the provided accessible 
    property, within a certain time frame
    :param config_entry: config entry
    :return: consumption data list
    """
    # read the configuration data
    host = None  # host base url
    api_key = None  # api key
    property_id = None  # authorized property id
    start = None  # start date/time of the period in the format YYYYMMDDHHmm
    end = None  # end date/time of the period in the format YYYYMMDDHHmm
    live_env = DEFAULT_LIVE_ENVIRONMENT  # live environment

    # return value
    data = None

    # check the input data
    if config_entry.data:
        host = config_entry.data.get(CONF_HOST)
        api_key = config_entry.data.get(CONF_API_KEY)
        property_id = config_entry.data.get(CONF_PROPERTY_ID)

    if config_entry.options:
        live_env = config_entry.options.get(CONF_ENVIRONMENT)
        start = config_entry.options.get(CONF_START)
        end = config_entry.options.get(CONF_END)

    try:
        # select get operation authorization base url
        consent_token_base_url = 'https://consentsandbox.data.n3rgy.com'
        if live_env:
            consent_token_base_url = 'https://consent.data.n3rgy.com'

        # call api
        consent = N3rgyGrantConsent(property_id, api_key)
        session_id = consent.get_operation_authorization_token(consent_token_base_url)
        if session_id:
            # select handover base URL
            handover_base_url = 'https://portal-consent-sandbox.data.n3rgy.com/'
            if live_env:
                handover_base_url = 'https://portal-consent.data.n3rgy.com'

            # define return/error url to be redirected
            return_url = 'https://cloudkb.co.uk'
            error_url = 'https://cloudkb.co.uk'
            if consent.invocation_endpoint_url(handover_base_url, session_id, 'ihdmac_full', return_url, error_url):
                # create n3rgy data api instance
                api = N3rgyDataApi(host, api_key, property_id)
                data = api.read_consumption(start, end)

    except ValueError as ex:
        # error handling
        _LOGGER.warning(f"Failed to initialize API: {str(ex)}")
    finally:
        return data


class N3rgySensor(Entity):
    """Implementation of a n3rgy data sensor"""

    def __init__(self, coordinator):
        """
        Initialize n3rgy data sensor class
        :param coordinator: data coordinator object
        :return: none
        """
        self._name = SENSOR_NAME
        self._type = SENSOR_TYPE
        self._state = None
        self._coordinator = coordinator

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
            return self._coordinator.data['unit']
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
        attributes = {
            ATTR_ATTRIBUTION: ATTRIBUTION,
        }
        if not self._coordinator.data:
            return attributes
        
        # reformat date/time
        try:
            str_start = self._coordinator.data['start']
            str_end = self._coordinator.data['end']
            dt_start = datetime.strptime(str_start, INPUT_DATETIME_FORMAT)
            dt_end = datetime.strptime(str_end, INPUT_DATETIME_FORMAT)
            attributes[ATTR_START_DATETIME] = datetime.strftime(dt_start, ATTR_DATETIME_FORMAT)
            attributes[ATTR_END_DATETIME] = datetime.strftime(dt_end, ATTR_DATETIME_FORMAT)
        except:
            _LOGGER.warning("Failed to reformat datetime object")
        
        return attributes

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
            # get consumption value
            value_list = self._coordinator.data['values']
            values = [v['value'] for v in value_list]
            
            # logging
            # _LOGGER.debug(f"Consumption values: {values}")
            self._state = f"{sum(values):.2f}"

    async def async_update(self):
        """
        Update the entity
        Only used by the generic entity update service
        :param: none
        :return: none
        """
        await self._coordinator.async_request_refresh()
