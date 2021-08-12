from __future__ import print_function

from .registry import Registry
from .sources import *

# global imports
import yaml
import os.path
from pprint import pprint


import logging

logging.basicConfig(
    filename='notion_gcal_sync.log',
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    encoding='utf-8',
    level=logging.INFO)

logger = logging.getLogger(__name__)

def init():
    with open('config.yaml', 'r') as file:
        config = yaml.load(file, Loader=yaml.loader.SafeLoader)
    logger.info('Config loaded.')

    sources = [
        # Notion(config['sources']['notion']['id'], 'notion', config['sources']['notion']['token'], keys=config['sources']['notion']['keys']),
        Notion('notion', **config['sources']['notion']),
        GCal('gcal', **config['sources']['gcal']),
        # GCal(config['sources']['gcal']['id'], 'gcal', config['sources']['gcal']['token'])
    ]

    return Registry(sources, max_age=config['max_age'])

def main():
    registry = init()

    registry.sync()


def run():
    main()
