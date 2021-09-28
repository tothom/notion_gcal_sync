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
                if not 'date' in event.keys():
                    start = event['start']
                    end = event['end']

                    # if end:
                    #     end_dt = parse_datetime_str(end)
                    #     if isinstance(end_dt, datetime.date):
                    #         end_dt += timedelta(days=1)
                    #         end = end_dt.isoformat()

                    date = {
                        'start': event['start'],
                        'end': event['end']
                        }

                    event['date'] = date

                    del event['start']
                    del event['end']


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

        if not event.get('date'):
            # Event must have a date property to be valid
            return

        found_event = self.find_event_in_registry(event)

        if not found_event:
            logger.info("\tEvent is new. Adding to registry.")
            logger.debug(event)

            # for source in [self.sources[key] for key in self.sources.keys() - event['ids'].keys()]:
            #     new = source.create(events)
            #     # ids = event.ids | new.ids
            #     # event.update(new)
            #     event['ids'].update(new.ids)

            self.events.append(event)

    def clean_registry(self):
        deletions = []

        for event in self.events:

            if len(event['ids']) < len(self.sources):

                for source_name, source in self.sources.items():
                    if not source_name in event['ids'] and event['date']:
                        new = source.create(event)
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

            # Fetch remote events
            remotes = []

            deletions = []

            for name, id in reg_event['ids'].items():
                remote = self.sources[name].get(id)

                if remote:
                    remotes.append(remote)
                else: # No response from server because event is not found or have been deleted.
                    deletions.append(name)

            for deletion in deletions:
                del reg_event['ids'][name]

            diff = {}

            for remote in sorted(remotes, key=lambda x:x['updated']):
                for key in remote.keys() - 'ids':
                    value = remote[key]
                    if value != reg_event.get(key):
                        diff[key] = value

            logger.debug(diff)

            if diff:
                for source_name, event_id in reg_event['ids'].items():
                    source = self.sources[source_name]
                    source.patch(event_id, diff)

                reg_event.update(diff)

            # {key: value for key, value in diff.items() if value != reg_event.get(key)}

                    # else:
                    #     # if value != diff[key] and remove:
                    #     if remote['updated'] > diff['updated']:
                    #         diff[key] = value
                            # status = 'updated'


                # remotes.append(remote_event)
                # remotes = self._get_remote_events(reg_event)

            # TODO: What if remote event is not found?

            # latest_event = sorted(remote_events, key=lambda x: x['updated'],
            #                               reverse=True)[0]

            # other_sources = [self.sources[key] for key in
            #                  self.sources.keys() - latest_event['ids'].keys()]

            # if latest_event.get('archived'):
            #     logger.info("\tEvent is DELETED")
            #
            #     for source in other_sources:
            #         logger.info(f"\t\tDeleting event at {source.name}")
            #         source.delete(reg_event['ids'][source.name])
            #
            #     self.pending_removals.append(reg_event)

            # if not latest_event['date']:
            #     logger.info("\tEvent misses date property")
            #
            #     for source in other_sources:
            #         logger.info(f"\t\tDeleting event at {source.name}")
            #         source.delete(reg_event['ids'][source.name])
            #
            #     self.pending_removals.append(event)
            #
            # elif latest_event['updated'] > reg_event['updated']:
            #     logger.info("\tEvent has been UPDATED")
            #
            #     diff_event = {k: v for k, v in latest_event.items() if v != reg_event[k]}
            #
            #     for source in other_sources:
            #         logger.info(f"\t\tUpdating event at {source.name}")
            #
            #         new = source.patch(
            #             reg_event['ids'][source.name], diff_event)
            #
            #     reg_event.update(diff_event)
            #
            # elif False:
            #     pass
            #     # Event has expired from Registry
            # else:
            #     logger.info("\tNo changes")

        # self.apply_removals()

    def sync(self):
        now = datetime.datetime.now().isoformat() + 'Z'

        self.check_for_changes()

        self.check_for_new_events()

        self.clean_registry()

        self.last_checked = now

        self.save_table()
