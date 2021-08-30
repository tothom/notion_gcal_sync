import uuid
from pprint import pprint

import logging
logger = logging.getLogger(__name__)


class Event():
    """docstring for Event."""

    def __init__(self, ids={}, title=None, start=None, end=None,
                 description=None, url=None, updated=None, archived=False
                 ):
        self.ids = ids
        # self.id = id or str(uuid.uuid4())
        self.updated = updated
        self.title = title
        self.start = start
        self.end = end
        self.description = description
        self.url = url
        self.archived = archived


    @property
    def properties(self):
        return {
            'title': self.title,
            'start': self.start,
            'end': self.end,
            'description': self.description,
            'archived': self.archived
        }

    def update(self, delta):
        if not delta:
            return
        try:
            for source_name, id in delta.pop('ids').items():
                self.ids[source_name] = id
        except:
            pass
        finally:
            self.__dict__.update(delta)

    def __sub__(self, other):
        return Event(**{k:v for k, v in
            set(self.properties.items()) - set(other.properties.items())})

    def __eq__(self, other):
        return self.properties == other.properties

    def __ne__(self, other):
        return self.properties != other.properties

    def __str__(self):
        return f"Event: {self.title}: {self.start} - {self.end}"
