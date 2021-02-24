"""
Script file: sensor.py
Created on: Jan 29, 2021
Last modified on: Feb 24, 2021

Comments:
    Support for n3rgy data sensor
"""

import logging

from datetime import datetime, timedelta
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from homeassistant.const import(
    ATTR_ATTRIBUTION,
    CONF_HOST,
    CONF_API_KEY,
    CONF_NAME
)
from .const import (
    CONF_PROPERTY_ID,
    CONF_ENVIRONMENT,
    CONF_DAILY_UPDATE,
    CONF_UTILITY,
    CONF_START,
    CONF_END,

    PLATFORM,
    ATTRIBUTION,
    SENSOR_NAME,
    SENSOR_TYPE,
    ICON,

    DEFAULT_NAME,
    DEFAULT_LIVE_ENVIRONMENT,
    DEFAULT_DAILY_UPDATE,
    DEFAULT_DEVICE_TYPE,
    UTILITY_ELECTRICITY,

    INPUT_DATETIME_FORMAT,
    ATTR_DATETIME_FORMAT,

    ATTR_START_DATETIME,
    ATTR_END_DATETIME,
    ATTR_DEVICE_TYPE,

    GRANT_CONSENT_READY
)
from .n3rgy_api import N3rgyDataApi, N3rgyGrantConsent

# set scan interval as 2 mins
SCAN_INTERVAL = timedelta(seconds=120)
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
        Fetch data from n3rgy API
        This is the place to pre-process the data to lookup tables so entities can quickly look up their data
        :param: none
        :return: power consumption data
        """
        return await hass.async_add_executor_job(read_consumption, api, entry)

    async def async_initialize():
        """
        Initialize objects from n3rgy API
        :param: none
        :return: data coordinator, device type
        """
        coordinator = DataUpdateCoordinator(
            hass,
            _LOGGER,
            name=PLATFORM,
            update_method=async_update_data
        )

        # fetch initial data so we have data when entities subscribe
        sensor_name, device_type = await hass.async_add_executor_job(get_device_info, api, entry)
        await coordinator.async_refresh()
        return (coordinator, sensor_name, device_type)

    # initialize n3rgy API
    device_type = None
    api = init_api_client(entry)

    # grant consent options
    if GRANT_CONSENT_READY:
        # grant consent is enabled for live environment
        if process_grant_consent(entry):
            coordinator, sensor_name, device_type = await async_initialize()
    else:
        # grant consent is disabled
        coordinator, sensor_name, device_type = await async_initialize()

    # add sensor
    async_add_entities([N3rgySensor(coordinator, sensor_name, device_type)], False)


def init_api_client(config_entry):
    """
    Initialize n3rgy data API client
    :param config_entry: config entry
    :return n3rgy data api client instance
    """
    # read the configuration data
    host = None
    api_key = None
    property_id = None

    # check the input data
    if config_entry.data:
        host = config_entry.data.get(CONF_HOST)
        api_key = config_entry.data.get(CONF_API_KEY)
        property_id = config_entry.data.get(CONF_PROPERTY_ID)
    
    # initialize n3rgy data API client
    api_instance = None
    try:
        api_instance = N3rgyDataApi(host, api_key, property_id)
    except ValueError as err:
        _LOGGER.warning(f"[INIT_API_CLIENT] Error: {str(err)}")
    finally:
        return api_instance


def get_device_info(api, config_entry):
    """
    Get sensor information
    :param api: n3rgy api client
    :param config_entry: config entry
    :return: (device name, smarte meter type)
    """
    # get the property id
    property_id = None
    sensor_name = DEFAULT_NAME

    # check the input data
    if config_entry.data:
        property_id = config_entry.data.get(CONF_PROPERTY_ID)
        sensor_name = config_entry.data.get(CONF_NAME)

    # get smart meter type
    device_type = None
    try:
        device_type = api.find_mxpn(property_id)
    except ValueError as err:
        _LOGGER.warning(f"[GET_TYPE] Error: {str(err)}")
    finally:
        return (sensor_name, device_type)


def process_grant_consent(config_entry):
    """
    Grant consent process
    :param config_entry: config entry
    :return: True if successful, False otherwise
    """
    # read the configuration data
    api_key = None
    property_id = None
    live_env = DEFAULT_LIVE_ENVIRONMENT

    # check the input data
    if config_entry.data:
        api_key = config_entry.data.get(CONF_API_KEY)
        property_id = config_entry.data.get(CONF_PROPERTY_ID)

    if config_entry.options:
        live_env = config_entry.options.get(CONF_ENVIRONMENT)

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
        return consent.invocation_endpoint_url(handover_base_url, session_id, 'ihdmac_full', return_url, error_url)

    # failed
    return False


def read_consumption(api, config_entry):
    """
    List consumption values for an utility type on the provided accessible property, within a certain time frame
    :param api: n3rgy api client
    :param config_entry: config entry
    :return: consumption data list
    """
    # read the configuration data
    utility = UTILITY_ELECTRICITY
    daily_update = DEFAULT_DAILY_UPDATE
    start = None
    end = None

    # check options
    if config_entry.options:
        utility = config_entry.options.get(CONF_UTILITY)
        daily_update = config_entry.options.get(CONF_DAILY_UPDATE)
        if not daily_update:
            start = config_entry.options.get(CONF_START)
            end = config_entry.options.get(CONF_END)

    # get power consumption data
    data = None
    try:
        data = api.read_consumption(utility, start, end)
        _LOGGER.info(f"[READ_CONSUMPTION] Grabbed consumption data: ({start}-{end})")
    except ValueError as ex:
        _LOGGER.warning(f"[READ_CONSUMPTION] Error: {str(err)}")
    finally:
        return data


class N3rgySensor(Entity):
    """Implementation of a n3rgy data sensor"""

    def __init__(self, coordinator, sensor_name, device_type):
        """
        Initialize n3rgy data sensor class
        :param coordinator: data coordinator object
        :param sensor_name: device name
        :param device_type: smart meter type
        :return: none
        """
        self._name = sensor_name
        self._type = SENSOR_TYPE
        self._state = None
        self._coordinator = coordinator
        self._device_type = DEFAULT_DEVICE_TYPE

        # parameter validation
        if device_type is not None:
            self._device_type = device_type

    @property
    def name(self):
        """
        Return the name of the sensor
        :param: none
        :return: sensor name
        """
        return self._name

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
        Need to poll.
        Coordinator notifies entity of updates
        :param: none
        :return: false
        """
        return True

    @property
    def device_state_attributes(self):
        """
        Return the state attributes
        :param: none
        :return: state attributes
        """
        attributes = {
            ATTR_DEVICE_TYPE: self._device_type,
            ATTR_ATTRIBUTION: ATTRIBUTION
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

    def update_state(self):
        """
        Calculate the consumption data
        :param: none
        :return: none
        """
        if self._coordinator.data:
            # get consumption value
            value_list = self._coordinator.data['values']
            values = [v['value'] for v in value_list]
            self._state = f"{sum(values):.2f}"

    async def async_added_to_hass(self):
        """
        When entity is added to hass
        :param: none
        :return: none
        """
        self.async_on_remove(
            self._coordinator.async_add_listener(self.async_write_ha_state)
        )
        self.update_state()

    async def async_update(self):
        """
        Update the entity
        Only used by the generic entity update service
        :param: none
        :return: none
        """
        _LOGGER.info("[ENTITY] Async updated")
        await self._coordinator.async_request_refresh()
        self.update_state()
