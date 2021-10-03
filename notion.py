from .source import Source
# from .event import Event
from .helpers import *

import datetime
import dateutil
import os
from pprint import pprint
import re

# Notion imports
from notion_client import Client
from notion_client import APIResponseError

import logging
logger = logging.getLogger(__name__)


class Notion(Source):
    """docstring for Notion."""

    def __init__(self, *args, **kwargs):
        super(Notion, self).__init__(*args, **kwargs)

        self.http_exception = APIResponseError

    def authenticate(self):
        self.client = Client(auth=self.token)

    def _process_response(self, response):
        if not response:
            return

        # pprint(response)

        properties = response.get('properties')

        date = None

        if properties.get(self.keys['date']):
            start = properties[self.keys['date']]['date']['start']
            end = properties[self.keys['date']]['date']['end']

            # try:
            #     start = parse_datetime_str(start)
            # except:
            #     pass

            # if end is not None:
            #     end_dt = parse_datetime_str(end)
            #
            #     if isinstance(end_dt, datetime.date):
            #         end_dt += timedelta(days=1)
            #         end = end_dt.isoformat()

            date = {'start': start, 'end': end}


        return {
            'title': ', '.join([a.get('plain_text', '')
                                for a in properties[self.keys['title']]['title']]),
            'description': ', '.join([a.get('plain_text', '')
                                      for a in properties[self.keys['description']]['rich_text']]),
            'date': date,
            'archived': response['archived'],
            'ids': {self.name: response['id']},
            'updated': response['last_edited_time'],
            'url': response['url'],
        }

    def _prepare_request(self, event):
        properties = {}





        if 'title' in event:
            title = {
                self.keys['title']: {
                    "title": [
                        {
                            "type": "text",
                            "text": {
                                "content": event['title']
                            }
                        }
                    ]
                }
            }

            properties.update(title)

        if 'description' in event:
            description = {
                self.keys['description']: {
                    "type": "rich_text",
                    "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": event['description']
                                }
                            }
                    ]
                }
            }

            properties.update(description)

        date = {}

        if 'date' in event:
            if event['date'] == None:
                pass
            else:
                start = event['date'].get('start')
                end = event['date'].get('end')

                # if end is not None:
                #     end_dt = parse_datetime_str(end)
                #
                #     if isinstance(end_dt, datetime.date):
                #         end_dt -= timedelta(days=1)
                #
                #     end = end_dt.isoformat()

                properties[self.keys['date']] = {
                    'date': {
                        'start': start,
                        'end': end
                    }
                }

        # logger.debug(f"{properties=}")

        attributes = {}

        if 'archived' in event:
            attributes['archived'] = event['archived']

        return {'properties': properties} | attributes

    def _get_query(self, **kwargs):
        return {
            'filter': {
                'property': self.keys['date'],
                'date': {
                    'on_or_after': kwargs['time_min']
                }
            }
        }

        return {
            'filter': {
                'property': self.keys['last_edited_time'],
                'last_edited_time': {
                    'on_or_after': updated_min
                }
            }
        }

    def _set_status_code(self, e):
        self.status_code = e.status
        # return e.status

    def _list(self, query):
        return self.client.databases.query(
            database_id=self.id,
            **query
        )['results']

    def _get(self, id):
        return self.client.pages.retrieve(
            page_id=id
        )

    def _create(self, properties, **attributes):
        return self.client.pages.create(
            parent={"database_id": self.id},
            properties=properties
        )

    # def _update(self, id, properties):
    #     return self.client.pages.update(
    #         page_id=id,
    #         properties=properties
    #     )

    def _patch(self, id, properties, **attributes):
        # logger.debug(f"{id=}")
        # logger.debug(f"{properties=}")
        # if archived

        return self.client.pages.update(
            page_id=id,
            properties=properties,
            **attributes
        )

    # def _delete(self, id):
    #     return self.client.pages.update(
    #         page_id=id,
    #         archived=True
    #     )
