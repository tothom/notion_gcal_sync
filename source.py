from pprint import pprint
import logging
logger = logging.getLogger(__name__)

# from .event import Event


class Source():
    """
    Base class for database sources.
    """

    def __init__(self, name, id, token, keys={}):
        self.id = id
        self.name = name
        self.token = token
        self.keys = keys

        self.exclusive_end_date = True

        self.authenticate()
        self.http_exception = None  # Override with client HTTP Exception

    def _request(self, request_method, *args, **kwargs):
        logger.debug(f"{args=}")
        logger.debug(f"{kwargs=}")

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
            elif status_code == 410:
                # Event deleted
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
            return [self._process_response(a) for a in response]

    def get(self, id):
        response = self._request(self._get, id)

        if not response:
            return {}
        else:
            return self._process_response(response)

    def create(self, properties):
        properties = self._prepare_request_body(properties)

        # logger.debug(f"{properties=}")

        response = self._request(self._create, properties)

        if not response:
            return {}
        else:
            return self._process_response(response)

    def update(self, id, properties):
        properties = self._prepare_request_body(properties)

        response = self._request(self._update, id, properties)

        if not response:
            return {}
        else:
            return self._process_response(response)

    def patch(self, id, properties):
        properties = self._prepare_request_body(properties)
        # properties = self._clean_dict(properties)

        response = self._request(self._patch, id, properties)

        if not response:
            return {}
        else:
            return self._process_response(response)

    def delete(self, id):
        response = self._request(self._delete, id)

        if not response:
            return {}
        else:
            return self._process_response(response)

    def _clean_dict(self, _dict):
        """
        https://stackoverflow.com/questions/33797126/proper-way-to-remove-keys-in-dictionary-with-none-values-in-python
        """
        for key, value in list(_dict.items()):
            if isinstance(value, dict):
                self._clean_dict(value)
            elif value is None:
                del _dict[key]
            elif isinstance(value, list):
                for v in value:
                    self._clean_dict(v)

        return _dict

    """All methods below must be overridden"""

    def authenticate(self):
        """Should return a http client. Must be overridden"""
        self.client = None

    def _process_response(self, response):
        """Read client response and return an event dictionary.
        Please override... Must return an Event"""
        return {
            'title': response.get('title', ''),
            'description': response.get('description', ''),
            'archived': response.get('archived', False),
            'ids': {self.name: response['id']},
            'updated': response.get('updated'),
            'start': response.get('start'),
            'end': reponse.get('end')
        }

    def _prepare_request_body(self, event):
        """Please override..."""
        return {}

    def _get_status_code(self, e):
        """Update to return http status codes. Override if status code is in
        other attribute.
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
            properties=properties
        )

    def _update(self, id, properties):
        """Override this class with custom client method."""
        return self.client.update(
            id=id,
            properties=properties
        )

    def _delete(self, id):
        """Override this class with custom client method."""
        return self.client.delete(
            id=id
        )
