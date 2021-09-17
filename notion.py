from .source import Source
from .event import Event

from datetime import datetime, timedelta
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

        properties = response.get('properties')

        event = Event(**{
            'title': ', '.join([a.get('plain_text', '')
                                for a in properties[self.keys['title']]['title']]),
            'description': ', '.join([a.get('plain_text', '')
                                      for a in properties[self.keys['description']]['rich_text']]),
            'archived': response['archived'],
            'ids': {self.name: response['id']},
            'updated': response['last_edited_time'],
            'url': response['url']
        })

        if properties.get(self.keys['date']):
            event.start = properties[self.keys['date']]['date']['start']
            event.end = properties[self.keys['date']]['date']['end']

            if event.end and event.datetime_format == 'date':
                event.end_dt -= timedelta(days=1)

        return event

    def _prepare_request_body(self, event):
        request_body = {
            self.keys['title']: {
                "title": [
                    {
                        "type": "text",
                        "text": {
                            "content": event.title}
                    }
                ]
            },

            self.keys['description']: {
                "type": "rich_text",
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": event.description
                        }
                    }
                ]
            }
        }

        date = {}

        date['start'] = event.start

        try:
            if event.datetime_format == 'date':
                event.end_dt -= timedelta(days=1)
        finally:
            date['end'] = end

        request_body[self.keys['date']] = {
            'date': date}

        logger.debug(f"{request_body=}")

        return request_body

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

    def _get_error_code(self, e):
        return e.status

    def _list(self, query):
        return self.client.databases.query(
            database_id=self.id,
            **query
        )['results']

    def _get(self, id):
        return self.client.pages.retrieve(
            page_id=id
        )

    def _create(self, properties):
        return self.client.pages.create(
            parent={"database_id": self.id},
            properties=properties
        )

    def _update(self, id, properties):
        return self.client.pages.update(
            page_id=id,
            properties=properties
        )

    def _patch(self, id, properties):
        logger.debug(f"{id=}")
        logger.debug(f"{properties=}")

        return self.client.pages.update(
            page_id=id,
            properties=properties
        )

    def _delete(self, id):
        return self.client.pages.update(
            page_id=id,
            archived=True
        )
