from .source import Source
# from .event import Event
from .helpers import *


import os
from pprint import pprint
import re
import datetime  # import date, datetime, timedelta

# Google imports
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError  # , RefreshError

import logging
logger = logging.getLogger(__name__)


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

    def _process_response(self, response):
        if not response:
            return

        if not response.get('start'):
            start = None
            end = None
        elif response['start'].get('date'):
            start = response['start']['date']
            end = response['end']['date']

            end_dt = parse_datetime_str(end)
            end_dt -= datetime.timedelta(days=1)
            end = end_dt.isoformat()

            # if end == start:
            #     end == None
        else:
            start = response['start']['dateTime']
            end = response['end']['dateTime']

        if end == start:
            end == None

        return {
            'title': response.get('summary', ''),
            'description': response.get('description', ''),
            'date': {'start': start, 'end': end},
            'archived': response['status'] == 'cancelled',
            'ids': {self.name: response['id']},
            'updated': response.get('updated'),
        }

    def _prepare_request_body(self, event):
        request_body = {}

        if 'title' in event:
            request_body['summary'] = event['title']

        if 'description' in event:
            request_body['description'] = event['description']

        if 'date' in event:
            if event['date'] == None:
                request_body['status'] = 'cancelled'

            else:
                # if 'start' in event['date']:
                start = event['date']['start']
                end = event['date']['end']

                if start:
                    # request_body['status'] = 'cancelled'
                    # end = event['date']['end']
                    if end == None:
                        # dt = parse_datetime_str(start) + timedelta(days=)
                        end = start
                # if start:
                    dt = parse_datetime_str(start)

                    # format_dict = {datetime.date: 'date',
                    #           datetime.datetime: 'dateTime'}

                    if isinstance(dt, datetime.date):
                        format = 'date'
                        other_format = 'dateTime'
                    elif isinstance(dt, datetime.datetime):
                        format = 'dateTime'
                        other_format = 'date'


                    if format == 'date':
                        end_dt = parse_datetime_str(end)
                        end_dt += datetime.timedelta(days=1)
                        end = end_dt.isoformat()

                    request_body['start'] = {
                        format: start,
                        other_format: None
                    }

                    request_body['end'] = {
                        format: end,
                        other_format: None
                    }

        # logger.debug(f"{request_body=}")
        if 'archived' in event:
            if event['archived']:
                request_body['status'] = 'cancelled'
            if not event['archived']:
                request_body['status'] = 'confirmed'

        logger.debug(f"{request_body=}")

        return request_body

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
            body=properties
        ).execute()

    def _update(self, id, properties):
        return self.client.events().update(
            calendarId=self.id,
            eventId=id,
            body=properties
        ).execute()

    def _patch(self, id, properties):
        return self.client.events().patch(
            calendarId=self.id,
            eventId=id,
            body=properties
        ).execute()

    def _delete(self, id):
        return self.client.events().delete(
            calendarId=self.id,
            eventId=id,
        ).execute()
