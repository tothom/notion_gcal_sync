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
        self.events = []
        self.last_checked = None
        self.pending_removals = []

        self.file_name = "table_" + "_".join([a.id for a in self.sources]) + ".json"

        self.load_from_file(self.file_name)

    def load_from_file(self, file_name):
        # self.file_name = f"table_{self.config['notion']['id']}_{self.config['gcal']['id']}.json"

        if os.path.exists(file_name):
            print("File found")

            with open(file_name, 'r') as file:
                table = json.load(file)

            logger.debug(table)

            for id, properties in table['events'].items():
                event = Event.from_id_and_properties(id, properties)
                self.events.append(event)

            self.last_checked = table['last_checked']

            logger.info(f"Registry table loaded from {self.file_name}, last_checked: {self.last_checked}.")


    def save_table(self):
        with open(self.file_name, 'w') as file:
            json.dump({
                'last_checked': self.last_checked,
                'events': self.events
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

    def check_if_event_is_new(self, event):
        found_event = self.find_table_entry(event)

        if not found_event:





    # def load_sources(self):
    #     for source in self.config['sources']:
    #         s =
