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

    @classmethod
    def from_dict(cls, d):
        return cls(**d)

    # def to_dict(self, d):
    #     return self.__dict__

    @staticmethod
    def diff(a, b):
        return {k:v for k, v in
            set(a.properties.items()) - set(b.properties.items())}
        # for key in master_event.properties:
        #     if master_event.properties[key] != slave_event.properties[key]:
        #         yield {key: slave_event.properties[key]}

    # @staticmethod
    # def diff2(event_a, event_b):
    #     for key_a, key_b in zip(event_a.properties, event_b.properties):
    #         if event_a.properties[key_a] != event_b.properties[key_b]:
    #             yield {key_a: (event_a.properties[key_a], event_b.properties[key_b])}
    #
    # @staticmethod
    # def diff3(master_event, event_a, event_b):
    #     for key in master_event.properties:
    #         if event_a.properties[key] != event_b.properties[key]:
    #             yield {key: (event_a.properties[key_a], event_b.properties[key])}

    def add_source_id(self, source_name, id):
        self.ids[source_name] = id

    def update(self, delta):
        if not delta:
            return
        try:
            for source_name, id in delta.pop('ids').items():
                self.add_source_id(source_name, id)
        except:
            pass
        finally:
            self.__dict__.update(delta)
