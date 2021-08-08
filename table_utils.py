import os
import json
import logging

logger = logging.getLogger(__name__)

# Table, tracker, registry, hash table, index, master

def init_table():
    logger.info('Initialising table')
    table = {
        'last_checked': None,
        'events': {}
    }

    return table


def get_table(config):
    # logger.info('Getting table')

    table_file_name = f"table_{config['notion']['id']}_{config['gcal']['id']}.json"

    if os.path.exists(table_file_name):
        with open(table_file_name, 'r') as file:
            table = json.load(file)

        logger.info(f"Table loaded from {table_file_name}.")
    else:
        table = init_table()

    return table


def load_table(table_file_path):
    with open(table_file_path, 'r') as file:
        table = json.load(file)

    return table


def save_table(table, config):
    table_file_name = f"table_{config['notion']['id']}_{config['gcal']['id']}.json"

    with open(table_file_name, 'w') as file:
        json.dump(table, file, indent=4)
        logger.info(f"Table written to {table_file_name}...")


def find_table_entry(search_id, table):
    for entry_id, entry in table['events'].items():
        if search_id in [entry['notion_id'], entry['gcal_id']]:
            return entry_id, entry

    return None, {}

# def add_table_entry(event):
#     table_update = {
#         'updated': new_event['updated'],
#         'notion_id': new_event['id'],
#         'gcal_id': event['id'],
#         'title': new_event['title'],
#         'url': new_event['url'],
#         'archived': False
#     }
#
#     table_id = str(uuid.uuid4())
#     table_dict['events'][table_id] = table_update

def clean_table(file_name):
    table = load_table(file_name)

    for event in table['events']:
        pass

# def print_table():
#     global TRACKER
#     print(TRACKER)
