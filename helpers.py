from types import SimpleNamespace
import yaml
from datetime import date  # , datetime, timedelta
import dateutil.parser
import re
# import sys

import logging

logging.basicConfig(
    filename='notion_gcal_sync.log',
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    # stream=sys.stdout,
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


def load_config(file_name='config.yaml'):
    with open(file_name, 'r') as file:
        config = yaml.load(file, Loader=yaml.loader.SafeLoader)
    logger.info('Config loaded.')

    return config


def create_config(file_name='config.yaml'):
    pass


def parse_datetime_str(dt_str):
    if re.fullmatch('\d{4}-\d{2}-\d{2}', dt_str):
        return date.fromisoformat(dt_str)
    else:
        return dateutil.parser.parse(dt_str)


def dict_diff(a, b):
    for key in b.keys():
        if a[key] != b[key]:
            a[key] = b[key]

    return a
