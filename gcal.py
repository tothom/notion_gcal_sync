from .source import Source

import datetime
import dateutil
import os
from pprint import pprint

# Google imports
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError


class GCal(Source):
    """docstring"""

    def __init__(self, *args, **kwargs):
        super(GCal, self).__init__(*args, **kwargs)

        self.http_exception = HttpError

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
                    'credentials.json', self.SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())

        self.creds = creds

        self.client = build('calendar', 'v3', credentials=self.creds)

    def _get_status_code(self, e):
        return e.status_code

    def _read_response(self, response, **kwargs):
        if not response:
            return

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

        return {
            'title': response.get('summary', ''),
            'description': response.get('description', ''),
            'archived': response['status'] == 'cancelled',
            'ids': {self.name: response['id']},
            'updated': response.get('updated'),
            'start': start,
            'end': end
        }

    def _prepare_properties(self, properties):
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
        query = {
            'singleEvents': True,
            'orderBy': 'updated'
        }

        if 'time_min' in kwargs:
            query['timeMin'] = kwargs['time_min']

        if 'updated_min' in kwargs:
            query['updatedMin'] = kwargs['updated_min']

        return query


    def _list(self, query):
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
            body=self._prepare_properties(properties)
        ).execute()

    def _update(self, id, properties):
        return self.client.events().update(
            calendarId=self.id,
            eventId=id,
            body=self._prepare_properties(properties)
        ).execute()

    def _delete(self, id):
        return self.client.events().delete(
            calendarId=self.id,
            eventId=id,
        ).execute()
