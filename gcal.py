import datetime
import dateutil
from pprint import pprint
import os.path

# Google imports
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError


# If modifying these scopes, delete the file token.json.
SCOPES = [
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/calendar.events'
]


def authenticate():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
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

    return creds

def get_google_calendar_client():
    creds = authenticate()

    # Call the Calendar API
    google_client = build('calendar', 'v3', credentials=creds)

    return google_client

def read_response_datetime(response):
    # pprint(response)
    if not response.get('start'):
        return {'start': None, 'end': None}

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

    return {'start': start, 'end': end}


def read_response(response):
    properties = {
        'title': response.get('summary', ''),
        'description': response.get('description', ''),
        'date': read_response_datetime(response),
        'archived': response['status'] == 'cancelled',
        'source': 'gcal',
        'updated': response.get('updated'),
        'id': response['id']
    }

    return properties


def prepare_properties(properties):
    gcal_properties = {
        'summary': properties['title'],
        'description': properties['description']
    }

    # Notion and Google seem to interpret event lengths differently
    start = properties['date']['start']
    end = properties['date']['end']

    end = end or start

    try:
        dt = datetime.datetime.strptime(start, '%Y-%m-%d')
    except ValueError as e:
        gcal_datetime_key = 'dateTime'
    else:
        gcal_datetime_key = 'date'

        if start != end:
            new_datetime = dateutil.parser.parse(end) + datetime.timedelta(days=1)
            end = new_datetime.strftime('%Y-%m-%d')

    gcal_properties.update(
        {'start': {gcal_datetime_key: start},
        'end': {gcal_datetime_key: end}
        }
    )

    return gcal_properties


def get_init_query(config, datetime_min):
    query = {
        'calendarId': config['gcal']['id'],
        'timeMin': datetime_min.isoformat() + 'Z',
        'singleEvents': True,
        'orderBy': 'updated',
    }

    return query


def get_updates_query(config, last_checked):
    query = {
        'calendarId': config['gcal']['id'],
        'updatedMin': last_checked,
        'singleEvents': True,
        'orderBy': 'updated',
    }

    return query
