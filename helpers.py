from types import SimpleNamespace
import yaml

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


def load_config(file_name='config.yaml'):
    with open(file_name, 'r') as file:
        config = yaml.load(file, Loader=yaml.loader.SafeLoader)
    logger.info('Config loaded.')

    return config

def create_config(file_name='config.yaml'):
    pass
