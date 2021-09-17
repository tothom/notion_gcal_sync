from datetime import date, datetime, timedelta
import dateutil.parser
import re

from pprint import pprint

import logging
logger = logging.getLogger(__name__)


class Event():
    """docstring for Event."""

    def __init__(self, ids={}, title=None, start=None, end=None,
                 description=None, url=None, updated=None, archived=None
                 ):
        self.ids = ids
        self.updated = updated
        self.title = title

        self.start = start
        self.end = end # End property is exclusive

        self.description = description
        self.url = url
        self.archived = archived

    @property
    def attributes(self):
        return {
            'ids': self.ids,
            'updated': self.updated,
            'url': self.url
        }

    @property
    def properties(self):
        return {
            'title': self.title,
            'start': self.start,
            'end': self.end,
            'description': self.description,
            'archived': self.archived
        }

    def _isoformat(self, dt):
        print(type(dt))
        if not dt:
            return None
        elif self.datetime_format == 'date':
            return dt.strftime('%Y-%m-%d')
        elif self.datetime_format == 'dateTime':
            return dt.isoformat()

    @property
    def start(self):
        return self._isoformat(self.start_dt)

    @start.setter
    def start(self, value):
        self.start_dt = self.validate_datetime_string(value)

    @property
    def end(self):
        return self._isoformat(self.end_dt)

    @end.setter
    def end(self, value):
        self.end_dt = self.validate_datetime_string(value)

    @property
    def datetime_format(self):
        dt = self.start_dt or self.end_dt or None

        if not dt:
            return None
        elif isinstance(dt, date):
            return 'date'
        elif isinstance(dt, datetime):
            return 'dateTime'

    def validate_datetime_string(self, dt_str):
        # print(f"{dt_str=}")
        if dt_str:
            try:
                dt = date.fromisoformat(dt_str)
            except:
                try:
                    dt = dateutil.parser.parse(dt_str)
                except:
                    dt = None
                    raise ValueError(
                        f"Datetime string '{dt_str}' has unknown format")

            # print(f"{dt=}")
            return dt

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
        return Event(**{k: v for k, v in
                        set(self.properties.items()) - set(other.properties.items())})

    def __eq__(self, other):
        return self.properties == other.properties

    def __ne__(self, other):
        return self.properties != other.properties

    def __str__(self):
        return f"<Event={self.title}: {self.start} - {self.end}>"

    def __repr__(self):
        return f"<Event={self.properties}>"
