from .event import Event

import os
import json
from pprint import pprint
import datetime


import logging
logger = logging.getLogger(__name__)

# Table, tracker, registry, hash table, index, master


class Registry():
    def __init__(self, sources, max_age=30):
        self.sources = {s.name: s for s in sources}
        # self.sources_dict = {source.name: source for source in sources}
        self.events = []
        self.last_checked = None
        self.max_age = max_age
        self.pending_removals = []

        self.file_name = "table_" + \
            "_".join([a.id for a in self.sources.values()]) + ".json"

        self.load_from_file(self.file_name)


    def load_from_file(self, file_name):
        # self.file_name = f"table_{self.config['notion']['id']}_{self.config['gcal']['id']}.json"

        if os.path.exists(file_name):
            with open(file_name, 'r') as file:
                table = json.load(file)

            self.events = [Event.from_dict(d) for d in table['events']]
            self.last_checked = table['last_checked']

            print(
                f"Registry table loaded from {self.file_name}, last_checked: {self.last_checked}.")


    def save_table(self):
        with open(self.file_name, 'w') as file:
            json.dump({
                'last_checked': self.last_checked,
                'events': [a.__dict__ for a in self.events]
            }, file, indent=4)
            print(f"Table written to {self.file_name}...")


    def find_event(self, event):
        logger.info(f"SEARCHING for event '{event.title}' in Registry.")

        for registry_event in self.events:
            if set(event.ids.values()) & set(registry_event.ids.values()) :
                logger.info(f"FOUND event '{registry_event.title}'.")

                return registry_event

        logger.info(f"Id NOT FOUND in Registry.")
        return None

    def remove_event(self, event):
        try:
            self.events.remove(event)
        except:
            logger.info(f"Event {event.title} not removed from registry")

    def apply_removals(self):
        for event in self.pending_removals:
            self.remove_event(event)
        self.pending_removals = []


    def fetch_events(self, *args, **kwargs):
        print(kwargs)
        events = []

        for source in self.sources.values():
            response = source.list(**kwargs)

            for item in response:
                # pprint(item)
                events.append(Event(**item))

        print(f"Fetched {len(events)} events from sources")

        return events


    def check_for_new_events(self):
        print("Checking for new events")

        time_min = datetime.datetime.now() - datetime.timedelta(days=self.max_age)
        time_min = time_min.isoformat() + 'Z'

        events = self.fetch_events(time_min=time_min)

        for event in events:
            result = self.check_if_event_is_new(event)


    def check_if_event_is_new(self, event):
        print(f"Checking if event is new: {event.title}")
        if not event.start:
            return

        found_event = self.find_event(event)

        if not found_event:
            print("Event is new. Adding to registry.")
            logger.debug(event.__dict__)

            for source in [self.sources[key] for key in self.sources.keys() - event.ids.keys()]:
                new = source.create(event.properties)
                event.update(new)

            self.events.append(event)


    def _get_remote_events(self, event):
        remote_events = []

        for name, id in event.ids.items():
            properties = self.sources[name].get(id)
            remote_event = Event(**properties)
            remote_events.append(remote_event)

        return remote_events


    def check_for_changes(self):
        print("Checking registry for changes.")

        for event in self.events:
            print(f"Checking event {event.title}")

            remote_events = self._get_remote_events(event)
            latest_updated_event = sorted(remote_events, key=lambda x:x.updated, reverse=True)[0]
            other_sources = [self.sources[key] for key in self.sources.keys() - latest_updated_event.ids.keys()]

            if latest_updated_event.archived or not latest_updated_event.start:
                print("Event is deleted or misses date property")

                for source in other_sources:
                    print(f"Deleting event at {source.name}")
                    new = source.delete(event.ids[source.name])

                self.pending_removals.append(event)

            elif latest_updated_event.updated > event.updated:
                print("Event has changed")

                for source in other_sources:
                    print(f"Updating event at {source.name}")

                    new = source.update(event.ids[source.name], event.properties)

            else:
                print("No changes")
                new = {}

            event.update(new)

        self.apply_removals()


    def sync(self):
        now = datetime.datetime.now().isoformat() + 'Z'

        self.check_for_changes()


        self.check_for_new_events()


        self.last_checked = now

        self.save_table()
