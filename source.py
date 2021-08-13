# from .source import Source

import datetime
import dateutil
import os
from pprint import pprint

import logging

logger = logging.getLogger(__name__)


class Source():
    """docstring for Source."""
    def __init__(self, name, id, token, keys={}):
        self.id = id
        self.name = name
        self.token = token
        self.keys = keys

        self.authenticate()

        self.http_exception = None # Override with client HTTP Exception

    def authenticate(self):
        self.client = None

    def _read_response(self, response):
        return {}

    def _prepare_properties(self):
        return {}

    def _get_status_code(self, e):
        """Update to return http status codes
        """
        return e.status

    def _get_query(self, **kwargs):
        pass

    def _request(self, request_function, *args, **kwargs):
        logger.debug(args)

        try:
            response = request_function(*args, **kwargs)

        except self.http_exception as e:
            status_code = self._get_status_code(e)
            print(f"{status_code} {type(e)}: {e}")

            if status_code == 400:
                # Bad request
                raise e
            elif status_code == 404:
                # Not found
                pass

            response = {}

        # logger.debug(response)

        return response

    def list(self, **kwargs):
        query = self._get_query(**kwargs)

        response = self._request(self._list, query)

        return [self._read_response(a) for a in response]

    def get(self, id):
        response = self._request(self._get, id)

        return self._read_response(response)

    def create(self, properties):
        response = self._request(self._create, properties)

        return self._read_response(response)

    def update(self, id, properties):
        response = self._request(self._update, id, properties)

        return self._read_response(response)

    def delete(self, id):
        response = self._request(self._delete, id)

        return self._read_response(response)
