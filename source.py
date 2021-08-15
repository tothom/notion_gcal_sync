from pprint import pprint
import logging
logger = logging.getLogger(__name__)


class Source():
    """
    Base class for database sources.
    """

    def __init__(self, name, id, token, keys={}):
        self.id = id
        self.name = name
        self.token = token
        self.keys = keys

        self.authenticate()
        self.http_exception = None  # Override with client HTTP Exception

    def _request(self, request_method, *args, **kwargs):
        logger.debug(args)

        try:
            response = request_method(*args, **kwargs)

        except self.http_exception as e:
            status_code = self._get_status_code(e)
            print(f"{status_code} {type(e)}: {e}")

            if status_code == 400:
                # Bad request
                raise e
            elif status_code == 404:
                # Not found
                pass
            else:
                raise e

            response = {}

        # logger.debug(response)

        return response

    def list(self, **kwargs):
        query = self._get_query(**kwargs)

        response = self._request(self._list, query)

        if not response:
            return {}
        else:
            return [self._read_response(a) for a in response]

    def get(self, id):
        response = self._request(self._get, id)

        if not response:
            return {}
        else:
            return self._read_response(response)

    def create(self, properties):
        response = self._request(self._create, properties)

        if not response:
            return {}
        else:
            return self._read_response(response)

    def update(self, id, properties):
        response = self._request(self._update, id, properties)

        if not response:
            return {}
        else:
            return self._read_response(response)

    def delete(self, id):
        response = self._request(self._delete, id)

        if not response:
            return {}
        else:
            return self._read_response(response)

    """All methods below must be overridden"""

    def authenticate(self):
        """Should return a http client"""
        self.client = None

    def _read_response(self, response):
        """Read client response and return an event dictionary.
        Please override..."""
        return {
            'title': response.get('title', ''),
            'description': response.get('description', ''),
            'archived': response.get('archived', False),
            'ids': {self.name: response['id']},
            'updated': response.get('updated'),
            'start': response.get('start'),
            'end': reponse.get('end')
        }

    def _prepare_properties(self, properties):
        return {}

    def _get_status_code(self, e):
        """Update to return http status codes
        """
        return e.status

    def _get_query(self, **kwargs):
        pass

    def _list(self, query):
        """Override this class with custom client method."""

        return self.client.list(
            id=self.id,
            **query
        )

    def _get(self, id):
        """Override this class with custom client method."""

        return self.client.get(
            id=id
        )

    def _create(self, properties):
        """Override this class with custom client method."""

        return self.client.create(
            properties=self._prepare_properties(properties)
        )

    def _update(self, id, properties):
        """Override this class with custom client method."""

        return self.client.update(
            id=id,
            properties=self._prepare_properties(properties)
        )

    def _delete(self, id):
        """Override this class with custom client method."""

        return self.client.delete(
            id=id
        )
