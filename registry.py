import os
import json
import logging

logger = logging.getLogger(__name__)

# Table, tracker, registry, hash table, index, master

class Registry():
    def __init__(self, sources):
        # for source in sources:
        self.sources = sources

        self.file_name = "table_" + "_".join([a.id for a in self.sources]) + ".json"

        # self.file_name = f"table_{self.config['notion']['id']}_{self.config['gcal']['id']}.json"

        if os.path.exists(self.file_name):
            print("File found")
            with open(self.file_name, 'r') as file:
                table = json.load(file)

            logger.info(f"Registry table loaded from {self.file_name}, last_checked: {table['last_checked']}.")
        else:
            table = {
                'last_checked': None,
                'events': {}
            }

        logger.debug(table)

        self.events = table['events']
        self.last_checked = table['last_checked']
        self.pending_deletions = []

    def save_table(self):
        with open(self.file_name, 'w') as file:
            json.dump({
                'last_checked': self.last_checked,
                'events': self.events
                }, file, indent=4)
            logger.info(f"Table written to {self.file_name}...")


    def find_table_entry(self, search_id):
        logger.info(f"SEARCHING for id '{search_id}' in Registry.")

        for entry_id, entry in self.events.items():
            if search_id in [entry['notion_id'], entry['gcal_id']]:
                logger.info(f"FOUND event with id '{entry_id}.'")
                return entry_id, entry

        logger.info(f"Id NOT FOUND in Registry.")
        return None, {}

    def remove_event(self, event_id):
        if event_id in self.events:
            del self.events[event_id]

    def apply_deletions(self):
        for event_id in self.pending_deletions:
            self.remove_event(event_id)
        self.pending_deletions = []

    def fetch_updated_events(self):
        events = []
        for source in self.sources:
            response = source.list_updated(self.last_checked)
            events.extend(response)

        return events

    def check_event_is_new(self, event):
        entry_id, entry = self.find_table_entry(event['id'])

        if not entry_id:
            other_




    # def load_sources(self):
    #     for source in self.config['sources']:
    #         s =
