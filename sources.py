# from .source import Source
from .event import Event

import datetime
import os

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

    def __init__(self, id, name, token, keys={}):
        self.id = id
        self.name = name
        self.token = token
        self.keys = keys

        self.authenticate()

    def authenticate(self):
        self.client = None

    def read_response(self, response):
        return {}

    def prepare_properties(self):
        return {}

    def _get_init_query(config, datetime_min):
        return {}

    def _get_updates_query(config, last_edited):
        return {}

    def list_updated(self, last_edited):
        query = self._get_updates_query(last_edited)
        return self.list(query)

    def list_since_datetime_min(self, datetime_min):
        # if isinstance(datetime_min, datetime.datetime)
        query = self._get_init_query(datetime_min)
        return self.list(query)

    def list(self, query):
        try:
            response = self._list(query)
        except Exception as e:
            logger.info(f"{type(e)}: {e}")
            response = {}
        else:
            logger.debug(response)

        return [self.read_response(a) for a in response]

    def get(self, id):
        try:
            response = self._get(id)
        except Exception as e:
            logger.info(f"{type(e)}: {e}")
            event = {}
        else:
            logger.debug(response)
            event = self.read_response(response)

        return event

    def create(self, properties):
        try:
            response = self._create(properties)
        except Exception as e:
            logger.info(f"{type(e)}: {e}")
            event = {}
        else:
            logger.debug(response)
            event = self.read_response(response)

        return event

    def update(self, id, properties):
        try:
            response = self._update(id, properties)
        except Exception as e:
            logger.info(f"{type(e)}: {e}")
            event = {}
        else:
            logger.debug(response)
            event = self.read_response(response)

    def delete(self, id):
        try:
            response = self._delete(id)
        except Exception as e:
            logger.info(f"{type(e)}: {e}")
            event = {}
        else:
            logger.debug(response)
            event = self.read_response(response)

        return event


class Notion(Source):
    """docstring for Notion."""

    def __init__(self, *args, **kwargs):
        super(Notion, self).__init__(*args, **kwargs)

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
            # 'date': response['properties'].get(self.keys['date'], {}).get('date'),
            'start': start,
            'end': end,
            'archived': response['archived'],
            'source_ids': {self.name: response['id']},
            'updated': response['last_edited_time'],
            # 'id': ,
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
            self.keys['date']: {'date': properties['date']}
        }

    def _get_init_query(self, datetime_min):
        return {
            'filter': {
                'property': self.keys['date'],
                'date': {
                    'on_or_after': datetime_min
                }
            }
        }

    def _get_updates_query(self, last_edited):
        return {
            'filter': {
                'property': self.keys['last_edited_time'],
                'last_edited_time': {
                    'on_or_after': last_edited
                }
            }
        }

    def _list(self, query={}):
        return self.client.databases.query(
            database_id=self.id,
            **query
        )['results']

    def _get(self, id):
        return self.client.pages.retrieve(
            page_id=id
        )

    def _create(self, properties):
        return notion_client.pages.create(
            parent={"database_id": self.id},
            properties=notion.prepare_properties(properties)
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
        if not response.get('start'):
            start = None
            end = None
        else:
            try:
                dt_start = dateutil.parser.parse(response['start']['date'])
                start = dt_start.strftime('%Y-%m-%d')

                dt_end = dateutil.parser.parse(response['end']['date'])
                dt_end = dt_end - datetime.timedelta(days=1)

                if dt_start >= dt_end:
                    end = None
                else:
                    end = dt_end.strftime('%Y-%m-%d')
            except:
                start = response['start']['dateTime']
                end = response['end']['dateTime']

            # date = {'start': start, 'end': end}

        return {
            'title': response.get('summary', ''),
            'description': response.get('description', ''),
            # 'date': date,
            'archived': response['status'] == 'cancelled',
            'source_ids': {self.name: response['id']},
            'updated': response.get('updated'),
            'start': start,
            'end': end
            # 'id': response['id']
        }

    def prepare_properties(self, properties):
        # Notion and Google seem to interpret event lengths differently
        start = properties['date']['start']
        end = properties['date']['end']

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

    def _get_init_query(self, datetime_min):
        return {
            'timeMin': datetime_min,
            'singleEvents': True,
            'orderBy': 'updated',
        }

    def _get_updates_query(self, last_edited):
        return {
            'updatedMin': last_edited,
            'singleEvents': True,
            'orderBy': 'updated',
        }

    def _list(self, query={}):
        return self.client.events().list(
            calendarId=self.id,
            **query
        ).execute()['items']

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
