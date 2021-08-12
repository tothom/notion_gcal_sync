import uuid
from pprint import pprint

import logging
logger = logging.getLogger(__name__)


class Event():
    """docstring for Event."""

    def __init__(self, ids={}, title="", start="", end="", description="", url="", updated="", id=None, archived=""):
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

    @classmethod
    def from_dict(cls, d):
        return cls(**d)

    # def to_dict(self, d):
    #     return self.__dict__

    def add_source_id(self, source_name, id):
        self.ids[source_name] = id

    def update(self, delta):
        try:
            for source_name, id in delta.pop('ids').items():
                self.add_source_id(source_name, id)
        except:
            pass
        finally:
            self.__dict__.update(delta)
