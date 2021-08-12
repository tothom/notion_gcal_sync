# from .source import Source

import datetime
import dateutil
import os
from pprint import pprint

# Notion imports
from notion_client import Client
from notion_client import APIResponseError

# Google imports
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError


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

        self.exception = None

    def authenticate(self):
        self.client = None

    def read_response(self, response):
        return {}

    def prepare_properties(self):
        return {}

    def _get_error_code(self, error):
        pass

    def _get_query(self, **kwargs):
        pass

    def _request(self, method, query):
        try:
            response = method(query)
        except self.http_exception as e:
            error_code = self._get_error_code(e)
            print(f"{error_code} {type(e)}: {e}")
            response = {}
        else:
            logger.debug(response)

        return response

    def list(self, **kwargs):
        query = self._get_query(**kwargs)

        try:
            response = self._list(query)
        except self.http_exception as e:
            print(f"{type(e)}: {e}")
            response = {}
        else:
            logger.debug(response)

        return [self.read_response(a) for a in response]

    def get(self, id):
        try:
            response = self._get(id)
        except self.http_exception as e:
            print(f"{type(e)}: {e}")
            event = {}
        else:
            # print(response)
            event = self.read_response(response)

        return event

    def create(self, properties):
        try:
            # pprint(properties)
            response = self._create(properties)
        except self.http_exception as e:
            print(f"{type(e)}: {e}")
            event = {}
        else:
            # print(response)
            event = self.read_response(response)

        return event

    def update(self, id, properties):
        try:
            response = self._update(id, properties)
        except self.http_exception as e:
            print(f"{type(e)}: {e}")
            event = {}
        else:
            # print(response)
            event = self.read_response(response)

        return event

    def delete(self, id):
        try:
            response = self._delete(id)
        except self.http_exception as e:
            print(f"{type(e)}: {e}")
            event = {}
        else:
            # print(response)
            event = self.read_response(response)

        return event


class Notion(Source):
    """docstring for Notion."""

    def __init__(self, *args, **kwargs):
        super(Notion, self).__init__(*args, **kwargs)

        self.exception = APIResponseError

    def authenticate(self):
        self.client = Client(auth=self.token)

    def read_response(self, response, **kwargs):
        if response['properties'].get(self.keys['date']):
            start = response['properties'][self.keys['date']]['date']['start']
            end = response['properties'][self.keys['date']]['date']['end']
        else:
            start = None
            end = None

        return {
            'title': ', '.join([a.get('plain_text', '')
                                for a in response['properties'][self.keys['title']]['title']]),
            'description': ', '.join([a.get('plain_text', '')
                                      for a in response['properties'][self.keys['description']]['rich_text']]),
            'start': start,
            'end': end,
            'archived': response['archived'],
            'ids': {self.name: response['id']},
            'updated': response['last_edited_time'],
            'url': response['url']
        }

    def prepare_properties(self, properties, **kwargs):
        return {
            self.keys['title']: {
                "title": [
                    {
                        "type": "text",
                        "text": {
                            "content": properties['title']
                        }
                    }
                ]
            },
            self.keys['description']: {
                "type": "rich_text",
                "rich_text": [{
                    "type": "text",
                    "text": {"content": properties['description']}
                }
                ]
            },
            self.keys['date']: {'date': {
                'start': properties['start'],
                'end': properties['end']}
            }
        }

    def _get_query(self, **kwargs):
        # pprint(kwargs)

        return {
            'filter': {
                'property': self.keys['date'],
                'date': {
                    'on_or_after': kwargs['time_min']
                }
            }
        }

        pass


        return {
            'filter': {
                'property': self.keys['last_edited_time'],
                'last_edited_time': {
                    'on_or_after': updated_min
                }
            }
        }



    def list(self, **kwargs):
        query = self._get_query(**kwargs)
        # pprint(query)

        response = self.client.databases.query(
            database_id=self.id,
            **query
        )['results']

        return [self.read_response(a) for a in response]

    def _get(self, id):
        return self.client.pages.retrieve(
            page_id=id
        )

    def _create(self, properties):
        return self.client.pages.create(
            parent={"database_id": self.id},
            properties=self.prepare_properties(properties)
        )

    def _update(self, id, properties):
        return self.client.pages.update(
            page_id=id,
            properties=self.prepare_properties(properties)
        )

    def _delete(self, id):
        return self.client.pages.update(
            page_id=id,
            archived=True
        )


class GCal(Source):
    """docstring"""

    def __init__(self, *args, **kwargs):
        super(GCal, self).__init__(*args, **kwargs)

    def authenticate(self):
        """"""
        self.SCOPES = [
            'https://www.googleapis.com/auth/calendar.readonly',
            'https://www.googleapis.com/auth/calendar.events'
        ]

        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file(
                'token.json', self.SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())

        self.creds = creds

        self.client = build('calendar', 'v3', credentials=self.creds)

    def read_response(self, response, **kwargs):
        # pprint(response)
        if not response.get('start'):
            start = None
            end = None
        elif response['start'].get('date'):
            start = response['start']['date']

            dt_end = dateutil.parser.parse(response['end']['date'])
            dt_end = dt_end - datetime.timedelta(days=1)
            end = dt_end.strftime('%Y-%m-%d')

            if start >= end:
                end = None
        else:
            start = response['start']['dateTime']
            end = response['end']['dateTime']

            # date = {'start': start, 'end': end}

        return {
            'title': response.get('summary', ''),
            'description': response.get('description', ''),
            'archived': response['status'] == 'cancelled',
            'ids': {self.name: response['id']},
            'updated': response.get('updated'),
            'start': start,
            'end': end
        }

    def prepare_properties(self, properties):
        # Notion and Google seem to interpret event lengths differently
        start = properties['start']
        end = properties['end']

        end = end or start  # End time cannot be empty

        try:
            dt = datetime.datetime.strptime(start, '%Y-%m-%d')
        except ValueError as e:
            gcal_datetime_key = 'dateTime'
        else:
            gcal_datetime_key = 'date'

            if start != end:
                new_datetime = dateutil.parser.parse(
                    end) + datetime.timedelta(days=1)
                end = new_datetime.strftime('%Y-%m-%d')

        return {
            'summary': properties['title'],
            'description': properties['description'],
            'start': {gcal_datetime_key: start},
            'end': {gcal_datetime_key: end}
        }

    def _get_query(self, **kwargs):
            return {
                    'timeMin': kwargs['time_min'],
                    'singleEvents': True,
                    'orderBy': 'updated'
                }

            return {
                'updatedMin': last_edited,
                'singleEvents': True,
                'orderBy': 'updated'
            }

    def list(self, **kwargs):

        query = self._get_query(**kwargs)
        # pprint(query)

        response = self.client.events().list(
            calendarId=self.id,
            **query
        ).execute()['items']

        return [self.read_response(a) for a in response]

    def _get(self, id):
        return self.client.events().get(
            calendarId=self.id,
            eventId=id
        ).execute()

    def _create(self, properties):
        return self.client.events().insert(
            calendarId=self.id,
            body=self.prepare_properties(properties)
        ).execute()

    def _update(self, id, properties):
        return self.client.events().update(
            calendarId=self.id,
            eventId=id,
            body=self.prepare_properties(properties)
        ).execute()

    def _delete(self, id):
        return self.client.events().delete(
            calendarId=self.id,
            eventId=id,
        ).execute()
