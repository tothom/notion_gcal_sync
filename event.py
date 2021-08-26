import uuid
from pprint import pprint

import logging
logger = logging.getLogger(__name__)


class Event():
    """docstring for Event."""

    def __init__(self, ids={}, title="", start="", end="",
                 description="", url="", updated="", archived=""
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

    @staticmethod
    def diff(a, b):
        return {k:v for k, v in
            set(a.properties.items()) - set(b.properties.items())}

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
