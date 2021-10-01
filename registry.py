# from .event import Event
from .helpers import *

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
        self.events = []
        self.last_checked = None
        self.max_age = max_age

        self.pending_removals = []

        self.file_name = "table_" + \
            "_".join([a.id for a in self.sources.values()]) + ".json"

        self.load_table(self.file_name)

    def load_table(self, file_name):
        # self.file_name = f"table_{self.config['notion']['id']}_{self.config['gcal']['id']}.json"

        if os.path.exists(file_name):
            with open(file_name, 'r') as file:
                table = json.load(file)

            for event in table['events']:
                self.events.append(event)

            # self.events = [a for a in table['events']]

            self.last_checked = table['last_checked']

            logger.info(
                f"Registry table loaded from {self.file_name}, last_checked: {self.last_checked}.")

    def save_table(self):
        with open(self.file_name, 'w') as file:

            json.dump({
                'last_checked': self.last_checked,
                'events': [a for a in self.events]
            }, file, indent=4)

            logger.info(f"Table written to {self.file_name}...")

    def find_event_in_registry(self, event):
        logger.info(f"Searching for event '{event['title']}' in Registry.")

        for registry_event in self.events:
            if set(event['ids'].values()) & set(registry_event['ids'].values()):
                logger.info(f"\tFound event '{registry_event['title']}'.")

                return registry_event

        logger.info(f"\tDid not find event in Registry.")

        return None

    # Removals
    # def remove_event(self, event):
    #     try:
    #         self.events.remove(event) ## TODO: Maybe wrong...
    #     except:
    #         logger.info(f"Event {event['title']} not removed from registry")
    #
    # def apply_removals(self):
    #     for event in self.pending_removals:
    #         self.remove_event(event)
    #     self.pending_removals = []

    def fetch_events(self, *args, **kwargs):
        logger.info(f"Fetching events from sources: {self.sources.keys()}")

        events = []

        for source in self.sources.values():
            response = source.list(**kwargs)

            for item in response:
                events.append(item)

        logger.info(f"Fetched {len(events)} events from sources")

        return events

    @property
    def time_min(self):
        time_min = datetime.datetime.now() - datetime.timedelta(days=self.max_age)
        time_min = time_min.isoformat() + 'Z'

        return time_min

    def check_for_new_events(self):
        logger.info("Checking for new events")

        events = self.fetch_events(time_min=self.time_min)

        for event in events:
            result = self.check_if_event_is_new(event)

    def check_if_event_is_new(self, event):
        logger.info(f"Checking if event is new: {event['title']}")

        if not event.get('date') or event.get('archived'):
            # Event must have a date property to be valid
            return

        found_event = self.find_event_in_registry(event)

        if not found_event:
            logger.info("\tEvent is new. Adding to registry.")
            logger.debug(event)

            # for source in [self.sources[key] for key in self.sources.keys() - event['ids'].keys()]:
            #     new = source.create(event)
            #     # ids = event.ids | new.ids
            #     # event.update(new)
            #     event['ids'].update(new['ids'])

            self.events.append(event)

    def clean_registry(self):
        logger.info(f"Cleaning registry")

        deletions = []

        for event in self.events:
            logger.debug(f"{event=}")

            # logger.debug()
            missing_event_source_keys = self.sources.keys() - event['ids'].keys()

            if missing_event_source_keys:
                for key in missing_event_source_keys:
                    new = self.sources[key].create(event)
                    event['ids'].update(new['ids'])

            elif event['date']['start'] < self.time_min:
                deletions.append(event)

        for deletion in deletions:
            self.events.remove(deletion)


    def _get_remote_events(self, event):
        remote_events = []

        for name, id in event['ids'].items():
            remote_event = self.sources[name].get(id)
            # remote_event = Event(**properties)
            remote_events.append(remote_event)

        return remote_events

    def check_for_changes(self):
        logger.info("Checking registry for changes.")

        for reg_event in self.events:
            logger.info(f"Checking event {reg_event['title']}")

            logger.debug(f"{reg_event=}")

            # Fetch remote events
            remotes = []

            deletions = []

            for name, id in reg_event['ids'].items():
                remote = self.sources[name].get(id)

                logger.debug(f"{remote=}")

                if remote:
                    remotes.append(remote)
                else: # No response from server because event is not found or have been deleted.
                    deletions.append(name)

            for deletion in deletions:
                del reg_event['ids'][name]

            diff = {}

            for remote in sorted(remotes, key=lambda x:x['updated']):
                for key in ['title', 'description', 'date', 'archived']:
                    value = remote[key]
                    if value != reg_event.get(key):
                        diff[key] = value

            logger.debug(f"{diff=}")

            if diff:
                for source_name, event_id in reg_event['ids'].items():
                    source = self.sources[source_name]
                    source.patch(event_id, diff)

                reg_event.update(diff)

    def sync(self):
        now = datetime.datetime.now().isoformat() + 'Z'

        self.check_for_changes()

        self.check_for_new_events()

        self.clean_registry()

        self.last_checked = now

        self.save_table()
