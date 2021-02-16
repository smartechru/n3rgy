"""
Script file: n3rgy_api.py
Created on: Jan Feb 4, 2021
Last modified on: Feb 17, 2021

Comments:
    n3rgy data api functions
"""

import re
import json
import logging
import base64
import requests
from requests.structures import CaseInsensitiveDict

_LOGGER = logging.getLogger(__name__)


class StatusCode:
    ST_OK = 200
    ST_CREATED = 201
    ST_PARTIAL_CONTENT = 206
    ST_BAD_REQUEST = 400
    ST_FORBIDDEN = 403
    ST_NOT_FOUND = 404


class N3rgyGrantConsent:
    """Integration with Grant Consent"""

    def __init__(self, mpxn, api_key):
        """
        Initialize Grant Consent client.
        :param mpxn: the MPxN property id getting from the customer (consumer)
        :param api_key: n3rgy data access key (API key)
        """
        self.mpxn = mpxn
        self.api_key = api_key

    def get_operation_authorization_token(self, base_url):
        """
        Request of an operation authorization token.
        :param base_url: base URL to get token
        :return: session id or None
        """
        # api request url
        url = f'{base_url}/consents/sessions'
        
        # api request headers
        headers = CaseInsensitiveDict()
        headers["Authorization"] = self.api_key

        # api request body
        data = {
            "mpxn": self.mpxn,
            "apiKey": self.api_key
        }

        # call n3rgy api
        res = None
        response = requests.post(url, headers=headers, json=data)

        # fetch data from response object
        if response.status_code == StatusCode.ST_CREATED:
            res = response.json()
            res = res['sessionId']
            _LOGGER.debug(f"[GET_TOKEN] Session ID: {res}")
        else:
            # bad request
            _LOGGER.warning(f"[GET_TOKEN] Bad request: {response.status_code}")
        
        return res

    def invocation_endpoint_url(self, base_url, session_id, consent_type, return_url, error_url):
        """
        Redirect the consumer to n3rgy data Grant Consent endpoint.
        The parameters must be encoded in Base64 and then URL Encoded.
        :param base_url: base URL to handover
        :param session_id: session id generated for a new grant consent process
        :param consent_type: consent type {cin, ihdmac_full, ihdmac_4}
        :param return_url: callback endpoint in a successful grant consent operation
        :param error_url: callback endpoint in an unsuccessful grant consent operation
        :return: True if successful, False otherwise
        """
        # encode query
        query = f"sessionId={session_id}&mpxn={self.mpxn}&consentType={consent_type}&returnUrl={return_url}&errorUrl={error_url}"
        encoded_bytes = base64.b64encode(query.encode())
        encoded_query = encoded_bytes.decode()

        # api request url
        url = f'{base_url}/consent/{encoded_query}'
        _LOGGER.debug(f"Consent URL: {url}")
        
        # api request headers
        headers = CaseInsensitiveDict()
        headers["Authorization"] = self.api_key

        # call n3rgy api
        response = requests.get(url, headers=headers)
        if response.status_code == StatusCode.ST_OK:
            # successful grant consent
            _LOGGER.debug("[HANDOVER] Successful")
            return True
        else:
            # grant consent failed
            _LOGGER.warning(f"[HANDOVER] Grant consent failed: {response.status_code}")
            return False


class N3rgyDataApi:
    """
    Provides a RESTful API that can access the energy smart metering estate (electricity and gas)
    available within Great Britain with direct access to data extracted from the energy smart meters,
    processed into an easy to consume format.
    """

    def __init__(self, host, api_key, property_id):
        """
        Initialize n3rgy data api client.
        :param host: host URL
        :param api_key: API key (MPxN)
        :param property_id: authorized property id

        """
        # base url validation
        if host is None:
            raise ValueError("API host URL error")
        
        if api_key is None:
            raise ValueError("API key error")

        # property_id validation
        if not re.search(r'[0-9]{13}||[0-9]{9}', property_id):
            raise ValueError("Invalid property id, must be either an MPAN or MPRN")

        # store information
        self.base_url = host
        self.api_key = api_key
        self.mpxn = property_id

    def find_mxpn(self, mpxn):
        """
        Searches the n3rgy database for the given MPxN.
        If not found in the n3rgy database, tries to provision the MPxN using Secure's SMSO.
        :param mpxn: MPxN requested by the user
        :return: json data that includes the mpxn and smart meter type
        """
        # validate MPxN
        if not re.search(r'[0-9]{13}||[0-9]{9}', mpxn):
            raise ValueError("Invalid MPxN")

        # api request url
        url = f'{self.base_url}/find-mpxn/{mpxn}'

        # api request headers
        headers = CaseInsensitiveDict()
        headers["Authorization"] = self.api_key

        # call n3rgy api
        data = None
        response = requests.get(url, headers=headers)

        # fetch data from response object
        if response.status_code == StatusCode.ST_OK:
            try:
                data = json.loads(response.text)
            except ValueError:
                data = response.text

            # logging response data
            data = data['deviceType']
            _LOGGER.debug(f"[GET_TYPE] Device type: {data}")
        elif response.status_code == StatusCode.ST_NOT_FOUND:
            # MPxN not found
            _LOGGER.debug(f"[GET_TYPE] MPxN not found: {response.status_code}")
        else:
            # forbidden error
            _LOGGER.warning(f"[GET_TYPE] Invalid API request: {response.status_code}")

        return data

    def call_api(self, utility=None, reading_type=None, element=None, payload=None, tag=None):
        """
        n3rgy data API call base function.
        :param utility: utility associated with the request {'electricity', 'gas', ...}
        :param reading_type: reading type {'consumption', 'production', 'tariff')}
        :param element: element for which prices are returned, only applies to electric meters, ignored otherwise
        :param payload: payload data for GET request
        :param tag: tag for debug
        :return: response of API request
        """
        # api request url
        url = f'{self.base_url}/{self.mpxn}'

        # utility is not empty
        if utility is not None:
            url = f'{url}/{utility}'

            # reading type is not empty
            if reading_type is not None:
                url = f'{url}/{reading_type}'

                # element is not empty
                if element is not None:
                    url = f'{url}/{element}'

        # api request headers
        headers = CaseInsensitiveDict()
        headers["Authorization"] = self.api_key

        # call n3rgy api
        data = None
        response = requests.get(url, params=payload, headers=headers)

        # fetch data from response object
        if response.status_code in [StatusCode.ST_OK, StatusCode.ST_PARTIAL_CONTENT]:
            try:
                data = json.loads(response.text)
            except ValueError:
                data = response.text

            # logging response data
            if tag is not None:
                _LOGGER.debug(f"[{tag}] Response: {data}")
        else:
            # logging error
            if tag is not None:
                _LOGGER.warning(f"[{tag}] Invalid API request: {response.status_code}")

        return data

    def get_valid_date(self, start, end):
        """
        Validate given date/time objects using regex.
        :param start: start date/time of the period, in the format YYYYMMDDHHmm
        :param end: end date/time of the period, in the format YYYYMMDDHHmm
        :return: valid payload data
        """
        payload = None

        # with query params
        if start and end:
            # start date/time validation and exception handler
            if not re.search(r'[0-9]{12}', start):
                raise ValueError("Invalid value for `start`, must conform to the pattern `YYYYMMDDHHmm`")

            # end date/time validation and exception handler
            if not re.search(r'[0-9]{12}', end):
                raise ValueError("Invalid value for `end`, must conform to the pattern `YYYYMMDDHHmm`")

            # n3rgy data api request with query params
            payload = {
                "start": start,
                "end": end
            }

        # return valid payload
        return payload

    def read_consumption(self, utility, start, end, granularity='halfhour'):
        """
        Returns values for the consumption of the specified utility at the property identified by the given MPxN.
        Unless otherwise specified using optional parameters, returns the consumption values for every half-hour of the previous day.
        Accepts as optional parameters a start date/time, an end date/time, and granularity (either halfhourly or daily).
        :param utility: utility associated with the request
        :param start: start date/time of the period, in the format YYYYMMDDHHmm
        :param end: end date/time of the period, in the format YYYYMMDDHHmm
        :param granularity: granularity of the consumption data
        :return: consumption data list
        """
        payload = self.get_valid_date(start, end)
        payload['granularity'] = granularity
        return self.call_api(utility, 'consumption', '1', payload=payload, tag='READ_CONSUMPTION')

    def read_tariff(self, utility, start, end):
        """
        Returns values for the tariff applied to the specified utility at the property identified by the given MPxN.
        Unless otherwise specified using optional parameters, returns the tariff values for every half-hour of the previous day.
        Accepts as optional parameters a start date and an end date.
        Always returns the tariff for at least a whole day
        :param utility: utility associated with the request
        :param start: start date/time of the period, in the format YYYYMMDDHHmm
        :param end: end date/time of the period, in the format YYYYMMDDHHmm
        :return: tariff data list
        """
        payload = self.get_valid_date(start, end)
        return self.call_api(utility, 'tariff', '1', payload=payload, tag='READ_TARIFF')

    def read_export(self, utility, start, end):
        """
        Returns the amount of exported energy for the specified property.
        Unless otherwise specified using optional parameters, returns the energy values for every half-hour of the previous day.
        Accepts as optional parameters a start date/time, an end date/time.
        :param utility: utility associated with the request
        :param start: start date/time of the period, in the format YYYYMMDDHHmm
        :param end: end date/time of the period, in the format YYYYMMDDHHmm
        """
        payload = self.get_valid_date(start, end)
        return self.call_api(utility, 'production', '1', payload=payload, tag='READ_EXPORT')

    def get_supported_elements(self, utility, reading_type):
        """
        Returns a list of the available meter elements of the specified meter.
        This uniquely identifies by the triplet {mpxn}/{utility}/{reading type}.
        :param utility: utility associated with the request
        :param reading_type: reading type associated with the request
        :return: list of available meter elements
        """
        return self.call_api(utility, reading_type)

    def get_reading_types(self, utility):
        """
        Returns a list of the reading types (types of data) available for that property/meter pair.
        Information on reading types may not yet be available for Live MPxN/meter pairs already registered on n3rgy's database.
        In those cases, *entries* in the response may be empty.
        :param utility: utility associated with the request
        :return: list of available reading types
        """
        return self.call_api(utility, tag='GET_READING_TYPES')

    def get_utility_types(self):
        """
        Returns a list of the smart meters available at that property.
        "Sandbox" only has data for electricity meters.
        "Sandbox" will always receive 'electricity' as a response for this request.
        :param: none
        :return: list of available utility types
        """
        return self.call_api(tag='GET_UTILITY')
