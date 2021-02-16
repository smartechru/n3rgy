"""
Script file: const.py
Created on: Jan 29, 2021
Last modified on: Feb 17, 2021

Comments:
    Constants for the n3rgy data integration
"""

DOMAIN = "n3rgy"
DATA_LISTENER = "listener"

# config options
CONF_PROPERTY_ID = "property_id"
CONF_ENVIRONMENT = "environment"
CONF_UTILITY = "utility"
CONF_START = "start"
CONF_END = "end"

# properties
PLATFORM = "sensor"
ATTRIBUTION = "Energy consumption data from https://data.n3rgy.com, delivered by n3rgy data Ltd."
SENSOR_NAME = "data"
SENSOR_TYPE = "usage"
ICON = "mdi:flash"

# default values
DEFAULT_NAME = "n3rgy"
DEFAULT_HOST = "https://sandboxapi.data.n3rgy.com"
DEFAULT_PROPERTY_ID = "1234567891008"
DEFAULT_LIVE_ENVIRONMENT = False
DEFAULT_DEVICE_TYPE = "Not specified"
UTILITY_ELECTRICITY = "electricity"
UTILITY_GAS = "gas"

# attributes
ATTR_START_DATETIME = "Start datetime"
ATTR_END_DATETIME = "End datetime"
ATTR_DEVICE_TYPE = "Smart meter type"

# date/time formatter
INPUT_DATETIME_FORMAT = "%Y%m%d%H%M"
ATTR_DATETIME_FORMAT = "%m/%d/%Y %H:%M"

# debug flag
GRANT_CONSENT_READY = False
