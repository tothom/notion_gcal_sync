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

from . import notion, gcal, io
from .registry import Registry
from .sources import *
import uuid

import logging

logging.basicConfig(
    filename='notion_gcal_sync.log',
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    encoding='utf-8',
    level=logging.DEBUG)

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


    sources = [
        Notion(config['sources']['notion']['id'], 'notion', config['sources']['notion']['token'], keys=config['sources']['notion']['keys']),
        GCal(config['sources']['gcal']['id'], 'gcal', config['sources']['gcal']['token'])
    ]


    registry = Registry(sources)

    print(registry.file_name)


    logger.info(f"Registry loaded from {registry.file_name}")

    pprint(registry.check_for_new_events())

    return

    # load_clients
    notion_client = notion.get_notion_client(config)
    gcal_client = gcal.get_google_calendar_client()

    utc_now = datetime.datetime.utcnow()
    datetime_min = utc_now - datetime.timedelta(days=config['max_age'])

    to_delete = []

    # Check for changes
    for entry_id, entry in registry.events.items():
        action, entry_update = io.check_for_changes(entry_id, entry, notion_client, gcal_client, config)
        if action == 'DELETED':
            registry.pending_deletions.append(entry_id)
        else:
            registry.events[entry_id].update(entry_update)

    # Check for new events
    events = io.fetch_events(registry, config, notion_client, gcal_client)

    for event in events:
        # print(event)
        result = io.check_for_new_event(event, registry, notion_client, gcal_client, config)

    # Update and save registry
    registry.apply_deletions()
    registry.last_checked = utc_now.isoformat() + 'Z'
    registry.save_table()

def run():
    main()
