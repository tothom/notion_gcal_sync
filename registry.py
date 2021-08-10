from .event import Event

import os
import json
from pprint import pprint


import logging
logger = logging.getLogger(__name__)

# Table, tracker, registry, hash table, index, master


class Registry():
    def __init__(self, sources):
        self.sources = sources
        self.sources_dict = {source.name: source for source in sources}
        self.events = []
        self.last_checked = None
        self.pending_removals = []

        self.file_name = "table_" + \
            "_".join([a.id for a in self.sources]) + ".json"

        self.load_from_file(self.file_name)

    def load_from_file(self, file_name):
        # self.file_name = f"table_{self.config['notion']['id']}_{self.config['gcal']['id']}.json"

        if os.path.exists(file_name):
            print("File found")

            with open(file_name, 'r') as file:
                table = json.load(file)

            logger.debug(table)

            # for id, properties in table['events'].items():
            #     # event = Event.from_id_and_properties(id, properties)
            #     self.events.append(event)

            self.events = [Event.from_dict(d) for d in table['events']]

            self.last_checked = table['last_checked']

            print(self.events)

            logger.info(
                f"Registry table loaded from {self.file_name}, last_checked: {self.last_checked}.")

    def save_table(self):
        with open(self.file_name, 'w') as file:
            json.dump({
                'last_checked': self.last_checked,
                'events': [a.__dict__ for a in self.events]
            }, file, indent=4)
            logger.info(f"Table written to {self.file_name}...")

    def find_table_entry(self, search_id):
        logger.info(f"SEARCHING for id '{search_id}' in Registry.")

        for event in self.events:
            for source, source_id in event.source_ids.items():
                if search_id == source_id:
                    logger.info(f"FOUND event with id '{event.id}.'")
                    return event

        logger.info(f"Id NOT FOUND in Registry.")
        return None

    def remove_event(self, event):
        try:
            self.events.remove(event)
        except:
            logger.info(f"Event {event.id} not removed from registry")

    def apply_removals(self):
        for event in self.pending_removals:
            self.remove_event(event)
        self.pending_removals = []

    def fetch_updated_events(self):
        events = []

        for source in self.sources:
            response = source.list_updated(self.last_checked)

            for item in response:
                # pprint(item)
                events.append(Event(**item))

            # events.extend(response)

        return events

    def check_for_new_events(self):
        events = self.fetch_updated_events()

        for event in events:
            result = self.check_if_event_is_new(event)

    def check_if_event_is_new(self, event):
        if not event.start:
            return

        found_event = self.find_table_entry(event)

        if not found_event:
            logger.debug(event.__dict__)

            for source in self._other_sources(event):
                new = source.create(event.properties)
                event.update(new)

            self.events.append(Event(**event))


    def _other_sources(self, event):
        return [a for a in self.sources if not a.name in event.source_ids.keys()]


    def check_for_changes(self):
        print("Checking for changes.")
        for event in self.events:
            remote_events = [self.sources_dict[name].get(id) for
                name, id in event.source_ids.items()]

            latest_updated_event = sorted(remote_events, key=lambda x:x['updated'], reverse=True)[0]

            other_sources = self._other_sources(event)

            if latest_updated_event['archived'] or not latest_updated_event['start']:
                print("Event is deleted or misses date property")
                for source in other_sources:
                    new = source.delete(event.properties)
                self.pending_removals.append(event)

            elif latest_updated_event['updated'] > event.updated:
                print("Event has changed")
                for source in other_sources:
                    new = source.update(event.properties)

            else:
                print("No changes")
                new = {}

            event.update(new)

        self.apply_removals()
