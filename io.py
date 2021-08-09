import datetime
import dateutil
import uuid
from pprint import pprint

from . import registry, notion, gcal

import logging

logger = logging.getLogger(__name__)


def sync_event(event, table_dict, notion_client, gcal_client, config):
    """"""
    logger.info(f"Checking event {event}...")

    table_id, table_entry = table_utils.find_table_entry(
        event['id'], table_dict)

    # update = None

    if not table_id and not event['archived']:
        action = 'NEW'
        if event['source'] == 'notion':
            request = gcal_client.events().insert(
                calendarId=config['gcal']['id'],
                body=gcal.prepare_properties(event))

            response = request.execute()

            new_event = gcal.read_response(response)

            update = {
                'updated': new_event['updated'],
                'notion_id': event['id'],
                'gcal_id': new_event['id'],
                'title': new_event['title'],
                'url': event['url'],
                'archived': False
            }

        elif event['source'] == 'gcal':
            request = notion_client.pages.create(
                parent={"database_id": config['notion']['id']},
                properties=notion.prepare_properties(
                    event, **config['notion']['keys'])
            )

            response = request

            new_event = notion.read_response(
                response, **config['notion']['keys'])

            update = {
                'updated': new_event['updated'],
                'notion_id': new_event['id'],
                'gcal_id': event['id'],
                'title': new_event['title'],
                'url': new_event['url'],
                'archived': False
            }

        table_id = str(uuid.uuid4())
        table_dict['events'][table_id] = update

    elif event['archived'] == True:
        action = 'DELETED'
        if event['source'] == 'notion':
            request = gcal_client.events().delete(
                calendarId=config['gcal']['id'],
                eventId=table_entry['gcal_id']
            )

            response = request.execute()

            new_event = gcal.read_response(response)

        elif event['source'] == 'gcal':
            try:
                response = notion_client.pages.update(
                    page_id=table_entry['notion_id'],
                    archived=True
                )
            except:
                pass
            else:

                new_event = notion.read_response(
                    response, **config['notion']['keys'])

        update = {
            'updated': event['updated'],
            'archived': True
        }

        table_dict['events'][table_id].update(update)

    # print()

    elif dateutil.parser.parse(event['updated']) > dateutil.parser.parse(table_entry['updated']):
        action = 'MODIFIED'
        if event['source'] == 'notion':
            request = gcal_client.events().update(
                calendarId=config['gcal']['id'],
                eventId=event['gcal_id'],
                body=gcal.prepare_properties(properties)
            )

            response = request.execute()

            new_event = gcal.read_response(response)

        elif event['source'] == 'gcal':
            try:
                response = notion_client.pages.update(
                    page_id=event['notion_id'],
                    properties=notion.prepare_properties(
                        properties, **config['notion']['keys'])
                )
            except:
                pass
            else:
                new_event = notion.read_response(
                    response, **config['notion']['keys'])

        update = {
            'updated': event['updated'],
            'title': event['title']
        }
        table_dict['events'][table_id].update(update)

    else:
        action = None

    logger.info(f"{action} event...\n")

    return action

def fetch_events(registry, config, notion_client, gcal_client):
    logger.info('Fetching events from sources')

    if registry.last_checked:
        notion_query = notion.get_updates_query(config, registry.last_checked)
        gcal_query = gcal.get_updates_query(config, registry.last_checked)
    else:
        notion_query = notion.get_init_query(config, datetime_min)
        gcal_query = gcal.get_init_query(config, datetime_min)

    notion_response = notion_client.databases.query(**notion_query)
    gcal_response = gcal_client.events().list(**gcal_query).execute()

    notion_events = [notion.read_response(
        a, **config['notion']['keys']) for a in notion_response['results']]
    gcal_events = [gcal.read_response(
        a) for a in gcal_response['items']]

    logger.info(f"Fetched {len(notion_events)} Notion events and {len(gcal_events)} Google Calendar events")

    return notion_events + gcal_events


def check_for_new_event(event, registry, notion_client, gcal_client, config):
    logger.info(f"Checking if new: event {event['id']} {event['title']}.")

    entry_id, entry = registry.find_table_entry(event['id'])

    # logger.info(f"Found event {entry.get('id')} in table")

    logger.debug(entry)

    if not event['date']:
        return

    if not entry_id:
        action = 'NEW'
        logger.info(f"Event is NEW. Sync between sources.")
        if event['source'] == 'notion':
            logger.info("Inserting event into Google Calendar")
            request = gcal_client.events().insert(
                calendarId=config['gcal']['id'],
                body=gcal.prepare_properties(event))

            response = request.execute()

            new_event = gcal.read_response(response)

            update = {
                'updated': datetime.datetime.now().isoformat() + 'Z',
                'notion_id': event['id'],
                'gcal_id': new_event['id'],
                'title': new_event['title'],
                'url': event['url'],
                'archived': False
            }

        elif event['source'] == 'gcal':
            logger.info("Creating event in Notion")
            request = notion_client.pages.create(
                parent={"database_id": config['notion']['id']},
                properties=notion.prepare_properties(
                    event, **config['notion']['keys'])
            )

            response = request

            new_event = notion.read_response(
                response, **config['notion']['keys'])

            update = {
                'updated': datetime.datetime.now().isoformat() + 'Z',
                'notion_id': new_event['id'],
                'gcal_id': event['id'],
                'title': new_event['title'],
                'url': new_event['url'],
                'archived': False
            }

        table_id = str(uuid.uuid4())
        registry.events[table_id] = update
    else:
        logger.info(f"Event is not new. Already in Registry.")
        action = None

    return action#, update

def check_for_changes(entry_id, entry, notion_client, gcal_client, config):
    logger.info(f"Checking event {entry_id} '{entry['title']}' for changes.")
    # get_notion_event
    try:
        response = notion_client.pages.retrieve(
            page_id=entry['notion_id']
        )
    except Exception as e:
        logger.info(f"{type(e)}: {e}")
        notion_event = {}
    else:
        logger.debug(response)
        notion_event = notion.read_response(response, **config['notion']['keys'])

    # get_gcal_event
    try:
        response = gcal_client.events().get(
            calendarId=config['gcal']['id'],
            eventId=entry['gcal_id']
        ).execute()
    except Exception as e:
        logger.info(f"{type(e)}: {e}")
        gcal_event = {}
    else:
        gcal_event = gcal.read_response(response)

    logger.debug(entry)
    logger.debug(notion_event)
    logger.debug(gcal_event)

    # if not notion_event and not gcal_event:
    #     action = 'DELETED'

    if not notion_event or not gcal_event \
        or notion_event.get('archived') or gcal_event.get('archived') \
        or not notion_event.get('date'):
        action = 'DELETED'
        if not notion_event or notion_event.get('archived') or not notion_event.get('date'):
            try:
                request = gcal_client.events().delete(
                    calendarId=config['gcal']['id'],
                    eventId=entry['gcal_id']
                )

                response = request.execute()
            except Exception as e:
                logger.info(f"{type(e)}: {e}")

            # new_event = gcal.read_response(response)

        elif not gcal_event or gcal_event.get('archived'):
            try:
                response = notion_client.pages.update(
                    page_id=entry['notion_id'],
                    archived=True
                )
            except Exception as e:
                logger.info(f"{type(e)}: {e}")
            else:
                pass
                # new_event = notion.read_response(
                #     response, **config['notion']['keys'])

        update = {
            'updated': datetime.datetime.utcnow().isoformat() + 'Z',
            'archived': True
        }

        # table['events'][table_id].update(update)


    # elif dateutil.parser.parse(notion_event['updated']) > dateutil.parser.parse(entry['updated']) or
    #  dateutil.parser.parse(gcal_event['updated']) > dateutil.parser.parse(entry['updated']):
    elif notion_event['updated'] > entry['updated'] or gcal_event['updated'] > entry['updated']:
        action = 'MODIFIED'

        if notion_event['updated'] > gcal_event['updated']:

            request = gcal_client.events().update(
                calendarId=config['gcal']['id'],
                eventId=entry['gcal_id'],
                body=gcal.prepare_properties(notion_event)
            )

            response = request.execute()

            new_event = gcal.read_response(response)

        elif gcal_event['updated'] > notion_event['updated']:
            try:
                response = notion_client.pages.update(
                    page_id=entry['notion_id'],
                    properties=notion.prepare_properties(
                        gcal_event, **config['notion']['keys'])
                )
            except Exception as e:
                logger.info(f"{type(e)}: {e}")
            else:
                new_event = notion.read_response(
                    response, **config['notion']['keys'])

        update = {
            'updated': datetime.datetime.utcnow().isoformat() + 'Z',
            'title': new_event['title']
        }

    else:
        action = None
        update = {}
        # table['events'][table_id].update(update)

    logger.info(f"Event action: {action}")

    return action, update

def check_for_deletion(entry_id, entry, notion_client, gcal_client, config):
    try:
        notion_event = notion_client.pages.retrieve(
            page_id=entry['notion_id']
        )
    except Exception as e:
        logger.info(f"{type(e)}: {e}")
    else:
        if notion_event['archived']:
            try:
                response = gcal_client.events().delete(
                    calendarId=config['gcal']['id'],
                    eventId=entry['gcal_id']
                ).execute()
            except Exception as e:
                logger.info(f"{type(e)}: {e}")
            else:
                logger.info(f"DELETED")
                return entry_id

    try:
        google_event = gcal_client.events().get(
            calendarId=config['gcal']['id'],
            eventId=entry['gcal_id']
        ).execute()
    except Exception as e:
        logger.info(f"{type(e)}: {e}")
    else:

        if google_event['status'] == 'cancelled':
            try:
                response = notion_client.pages.update(
                    page_id=entry['notion_id'],
                    archived=True
                )
            except Exception as e:
                logger.info(f"{type(e)}: {e}")
            else:
                logger.info(f"DELETED")
                return entry_id
