
async def check_google_event(google_event):

    if google_event['id'] not in [a['google_id'] for a in tracker['events'].values()]:

        properties = read_google_event(google_event)
        notion_event = prepare_notion_event(properties, **NOTION_KEYS)

        # pprint(notion_event)


        tracker['events'][str(uuid.uuid4())] = {
            'last_modified_time': response['last_edited_time'],
            'notion_id': response['id'],
            'google_id': google_event['id'],
            'properties': properties
        }

        print(f"New event {properties['title']} COPIED from Google to Notion")


async def check_for_changes():
    global ids_to_delete
    ids_to_delete = []

    for repo_event in tracker['events'].items():
        await sync_repo_event(repo_event)

    for event_id in ids_to_delete:
        try:
            del tracker['events'][event_id]
        except KeyError as e:
            print(e)


async def check_for_new_events():
    # Fetch events
    notion_events = await fetch_notion_events()
    check_notion_events(notion_events)

    google_events = fetch_google_events()
    await check_google_events(google_events)


def setup_time(day_delta=30):
    global TIME_MIN
    global TIME_MIN_DT

    time_min = datetime.datetime.utcnow() - datetime.timedelta(days=day_delta)
    TIME_MIN = time_min.isoformat() + 'Z'  # 'Z' indicates UTC time
    # datetime.fromisoformat(date_string)
    TIME_MIN_DT = dateutil.parser.parse(TIME_MIN)

    print(datetime.datetime.utcnow())


def clean_tracker():
    pass
    # Check for duplicates

    # Check for expired items


async def sync_event(repo_event):
    event_id, event = repo_event

    event_dt = dateutil.parser.parse(event['last_modified_time'])

    try:
        # notion_event = next(iter(filter(notion_events), lambda x: x['id'] == event['notion_id']), None) or
        notion_event = await notion.pages.retrieve(event['notion_id'])

    except APIResponseError:
        notion_event = None
        # event['archived'] = True

    except Exception as e:
        print(type(e), e)

    else:
        notion_dt = dateutil.parser.parse(notion_event['last_edited_time'])

        if notion_event['archived'] == True:
            event['archived'] = True
        elif event_dt < notion_dt:
            event['modified'] = True

        notion_properties = notion.read_response(notion_event, **NOTION_KEYS)

    try:
        assert event['google_id'], "Empty Google ID value"

        google_event = google.events().get(
            calendarId=GOOGLE_CALENDAR_ID,
            eventId=event['google_id']
        ).execute()

    except HttpError as e:
        print(type(e), e)

    except Exception as e:
        print(type(e), e)
        google_event = None

    else:
        google_dt = dateutil.parser.parse(google_event['updated'])

        if google_event['status'] == 'cancelled':
            event['archived'] = True
        elif event_dt < google_dt:
            event['modified'] = True

        google_properties = read_google_event(google_event)

    # pprint(event)

    if event.get('modified'):

        if notion_dt > google_dt:
            properties = notion.read_response(notion_event, **NOTION_KEYS)

            request = google.events().update(
                calendarId=GOOGLE_CALENDAR_ID,
                eventId=event['google_id'],
                body=google.prepare_properties(properties)
            )

            response = request.execute()

            event.update(
                {
                    'last_modified_time': datetime.datetime.utcnow().isoformat() + 'Z',
                    'modified': False,
                    'properties': read_google_event(response)
                }
            )

            print(f"Event {event_id} UPDATED from Notion to Google")

        else:
            properties = read_google_event(google_event)

            request = notion.pages.update(
                page_id=event['notion_id'],
                properties=prepare_notion_event(properties, **NOTION_KEYS)
            )

            response = await request

            event.update(
                {
                    'last_modified_time': response['last_edited_time'],
                    'modified': False,
                    'properties': notion.read_response(response, **NOTION_KEYS)
                }
            )

            print(f"Event {event_id} UPDATED from Google to Notion")

    elif event.get('archived'):
        try:
            request = google.events().delete(
                calendarId=GOOGLE_CALENDAR_ID,
                eventId=google_event['id']
            )

            response = request.execute()

        except Exception as e:
            print(type(e), e)

        try:
            request = notion.pages.update(
                page_id=notion_event['id'],
                archived=True
            )

            response = await request

        except Exception as e:
            print(type(e), e)

        ids_to_delete.append(event_id)

        print(f"Event {event_id} DELETED")

    elif not notion_event and not google_event:
        ids_to_delete.append(event_id)

        print(f"Event {event_id} REMOVED because no events found.")

    else:
        print(f"Event {event_id} NOT MODIFIED")

    pprint(event)
    repository['events'][event_id].update(event)
    print("\n")
