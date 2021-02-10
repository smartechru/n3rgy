"""
Script file: n3rgy_api.py
Created on: Jan Feb 4, 2021
Last modified on: Feb 10, 2021

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
    ST_BAD_REQUEST = 400
    ST_FORBIDDEN = 403


class N3rgyGrantConsent:
    """Integration with Grant Consent"""

    def __init__(self, mpxn, api_key):
        """
        Initialize Grant Consent client
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
            _LOGGER.debug(f"Session ID: {res}")
        else:
            # bad request
            _LOGGER.warning(f"Bad request: {response.status_code}")
        
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
            _LOGGER.debug("Handover done")
            return True
        else:
            # grant consent failed
            _LOGGER.warning(f"Grant consent failed: {response.status_code}")
            return False


class N3rgyDataApi:
    """
    Provides a RESTful API that can access the energy smart metering estate (electricity and gas)
    available within Great Britain with direct access to data extracted from the energy smart meters,
    processed into an easy to consume format.
    """

    def __init__(self, host, api_key, property_id):
        """
        Initialize n3rgy data api client
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

    def read_consumption(self, start, end):
        """
        List consumption values for an utility type on the provided accessible 
        property, within a certain time frame
        :param start: start date/time of the period in the format YYYYMMDDHHmm
        :param end: end date/time of the period in the format YYYYMMDDHHmm
        :return: consumption data list
        """
        # api request url
        url = f'{self.base_url}/{self.mpxn}/electricity/consumption/1'
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
                "end": end,
                "granularity": "halfhour"
            }
        
        # api request headers
        headers = CaseInsensitiveDict()
        headers["Authorization"] = self.api_key

        # call n3rgy api
        data = None
        response = requests.get(url, params=payload, headers=headers)

        # fetch data from response object
        if response.status_code == StatusCode.ST_OK:
            try:
                data = json.loads(response.text)
            except ValueError:
                data = response.text

            # logging response data
            _LOGGER.debug(f"Resource: {data['resource']}")
        else:
            # logging error
            _LOGGER.warning(f"Invalid API request: {response.status_code}")

        return data
