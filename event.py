import uuid
from pprint import pprint

import logging
logger = logging.getLogger(__name__)


class Event():
    """docstring for Event."""

    def __init__(self, source_ids={}, title="", start="", end="", description="", url="", updated="", id=None, archived=""):
        self.source_ids = source_ids
        self.id = id or str(uuid.uuid4())
        self.updated = updated
        self.title = title
        self.start = start
        self.end = end
        self.description = description
        self.url = url
        self.archived = archived


    @classmethod
    def from_id_and_properties(cls, id, properties):
        updated = properties['updated']
        title = properties['title']
        url = properties['url']

        start = properties.get('start')
        end = properties.get('end')

        archived = properties.get('archived', False)

        description = properties.get('description', '')

        try:
            source_ids = properties['source_ids']
        except:
            source_ids = {}
            source_ids['notion'] = properties['notion_id']
            source_ids['gcal'] = properties['gcal_id']
        #
        #
        # try:
        #     status = properties['status']
        # except:
        #     if properties['archived']:
        #         status = 'deleted'

        return cls(source_ids=source_ids, title=title, start=start, end=end,
            description=description, url=url, updated=updated, id=id)

    def to_dict(self, d):
        return self.__dict__

    def add_source(self, source_name, source_id):
        self.source_ids[source_name] = source_id

    def update(self, delta):
        try:
            for source_name, source_id in delta.pop('source_ids').items():
                self.add_source(source_name, source_id)
        finally:
            self.__dict__.update(delta)
