from .source import Source

import datetime
import dateutil
import os
from pprint import pprint

# Notion imports
from notion_client import Client
from notion_client import APIResponseError


class Notion(Source):
    """docstring for Notion."""

    def __init__(self, *args, **kwargs):
        super(Notion, self).__init__(*args, **kwargs)

        self.http_exception = APIResponseError

    def authenticate(self):
        self.client = Client(auth=self.token)

    def _read_response(self, response, **kwargs):
        if not response:
            return

        properties = response.get('properties')

        if properties.get(self.keys['date']):
            start = properties[self.keys['date']]['date']['start']
            end = properties[self.keys['date']]['date']['end']
        else:
            start = None
            end = None

        return {
            'title': ', '.join([a.get('plain_text', '')
                                for a in properties[self.keys['title']]['title']]),
            'description': ', '.join([a.get('plain_text', '')
                                      for a in properties[self.keys['description']]['rich_text']]),
            'start': start,
            'end': end,
            'archived': response['archived'],
            'ids': {self.name: response['id']},
            'updated': response['last_edited_time'],
            'url': response['url']
        }

    def _prepare_properties(self, properties, **kwargs):
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
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": properties['description']
                        }
                    }
                ]
            },
            self.keys['date']: {
                'date': {
                    'start': properties['start'],
                    'end': properties['end']
                }
            }
        }

    def _get_query(self, **kwargs):
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
            properties=self._prepare_properties(properties)
        )

    def _update(self, id, properties):
        return self.client.pages.update(
            page_id=id,
            properties=self._prepare_properties(properties)
        )

    def _delete(self, id):
        return self.client.pages.update(
            page_id=id,
            archived=True
        )
