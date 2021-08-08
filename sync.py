from __future__ import print_function

import yaml
from types import SimpleNamespace

# global imports
import datetime

import os.path
import json

import dateutil
import time
from pprint import pprint

from . import notion, gcal, io, table_utils
import uuid

import logging

logging.basicConfig(
    filename='notion_gcal_sync.log',
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    encoding='utf-8',
    level=logging.INFO)
logger = logging.getLogger(__name__)

def nested_simple_namespace(d):
    simple_namespace = SimpleNamespace()
    for k, v in d.items():
        if isinstance(v, dict):
            setattr(simple_namespace, k, nested_simple_namespace(v))
        else:
            setattr(simple_namespace, k, v)
    return simple_namespace

def init():
    pass


def main():
    # logger.info('Loading config.yaml')
    global config
    with open('config.yaml', 'r') as file:
        config = yaml.load(file, Loader=yaml.loader.SafeLoader)
        # config = nested_simple_namespace(config_dict)
    logger.info('Config loaded.')

    # return


    # load_clients
    notion_client = notion.get_notion_client(config)
    gcal_client = gcal.get_google_calendar_client()
    table = table_utils.get_table(config)

    # return

    #print(notion_client, gcal_client, table)

    utc_now = datetime.datetime.utcnow()
    datetime_min = utc_now - datetime.timedelta(days=config['max_age'])

    to_delete = []

    # Check for changes
    for entry_id, entry in table['events'].items():
        action, entry_update = io.check_for_changes(entry_id, entry, notion_client, gcal_client, config)
        if action == 'DELETED':
            to_delete.append(entry_id)
        else:
            table['events'][entry_id].update(entry_update)

    # Check for new events
    events = io.fetch_events(table, config, notion_client, gcal_client)

    for event in events:
        # print(event)
        result = io.check_for_new_event(event, table, notion_client, gcal_client, config)

    # Update and save table
    for a in to_delete:
        try:
            del table['events'][a]
        except:
            pass

    table['last_checked'] = utc_now.isoformat() + 'Z'

    table_utils.save_table(table, config)

def run():
    main()
