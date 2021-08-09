import datetime

# Notion imports
from notion_client import Client
from notion_client import APIResponseError

# Set up notion client
def get_notion_client(config):
    notion_client = Client(auth=config['notion']['token'])

    return notion_client


def read_response(response, title="Title", description="Description", date="Date", **kwargs):
    properties = {
        'title': ', '.join([a.get('plain_text', '')
                            for a in response['properties'][title]['title']]),
        'description': ', '.join([a.get('plain_text', '')
                                  for a in response['properties'][description]['rich_text']]),
        'date': response['properties'].get(date, {}).get('date'),
        'archived': response['archived'],
        'source': 'notion',
        'updated': response['last_edited_time'],
        'id': response['id'],
        'url': response['url']
    }

    return properties


def prepare_properties(properties, title="Title", description="Description", date="Date", **kwargs):
    notion_properties = {
        title: {
            "title": [
                {
                    "type": "text",
                     "text": {
                         "content": properties['title']
                     }
                }
            ]
        },
        description: {
            "type": "rich_text",
            "rich_text": [{
                "type": "text",
                "text": {"content": properties['description']}
                }
            ]
        },
        date: {'date': properties['date']}
    }

    return notion_properties

def get_init_query(config, datetime_min):
    query = {
        "database_id": config['notion']['id'],
        'filter': {
            'property': config['notion']['keys']['date'],
            'date': {
                'on_or_after': datetime_min.isoformat() + 'Z'
            }
        }
    }

    return query


def get_updates_query(config, last_checked):
    query = {
        "database_id": config['notion']['id'],
        'filter': {
            'property': config['notion']['keys']['last_edited_time'],
            'last_edited_time': {
                'on_or_after': last_checked
            }
        }
    }

    return query
