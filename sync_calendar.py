import json
from datetime import datetime, timedelta
from calendar_auth import get_calendar_service
import pytz


def get_shift_key(shift):
    return (
        datetime.fromisoformat(shift["startDateTime"]).astimezone(pytz.timezone('Australia/Sydney')).replace(tzinfo=None),
        datetime.fromisoformat(shift["endDateTime"]).astimezone(pytz.timezone('Australia/Sydney')).replace(tzinfo=None)
    )


def sync_all_shifts(shifts, service, calendar_id='primary'):
    tz = pytz.timezone('Australia/Sydney')
    today = datetime.now(tz)
    start_range = (today - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    end_range = (today + timedelta(days=15)).replace(hour=0, minute=0, second=0, microsecond=0)

    # Create a set of all shift start/end pairs from the fetched data (without tzinfo for clean comparison)
    fetched_shift_keys = set(get_shift_key(s) for s in shifts)

    # Fetch all existing calendar events in the same time range
    events = service.events().list(
        calendarId=calendar_id,
        timeMin=start_range.isoformat(),
        timeMax=end_range.isoformat(),
        singleEvents=True,
        orderBy='startTime'
    ).execute().get('items', [])

    # Remove outdated calendar events not in the fetched list
    for event in events:
        if event.get('summary') != 'Work Shift':
            continue

        start_dt = datetime.fromisoformat(event['start']['dateTime']).astimezone(tz).replace(tzinfo=None)
        end_dt = datetime.fromisoformat(event['end']['dateTime']).astimezone(tz).replace(tzinfo=None)
        event_key = (start_dt, end_dt)

        if event_key not in fetched_shift_keys:
            service.events().delete(calendarId=calendar_id, eventId=event['id']).execute()
            print("🗑️ Deleted removed shift:", start_dt, "-", end_dt)

    # Re-fetch updated calendar to avoid duplicate inserts
    events = service.events().list(
        calendarId=calendar_id,
        timeMin=start_range.isoformat(),
        timeMax=end_range.isoformat(),
        singleEvents=True,
        orderBy='startTime'
    ).execute().get('items', [])

    existing_keys = set()
    for event in events:
        if event.get('summary') != 'Work Shift':
            continue
        start_dt = datetime.fromisoformat(event['start']['dateTime']).astimezone(tz).replace(tzinfo=None)
        end_dt = datetime.fromisoformat(event['end']['dateTime']).astimezone(tz).replace(tzinfo=None)
        existing_keys.add((start_dt, end_dt))

    # Now add any new shifts not already on the calendar
    for shift in shifts:
        shift_start = tz.localize(datetime.fromisoformat(shift["startDateTime"]))
        shift_end = tz.localize(datetime.fromisoformat(shift["endDateTime"]))
        shift_key = get_shift_key(shift)

        if shift_key in existing_keys:
            print("✅ Shift already exists, skipping:", shift_key)
            continue

        event = {
            'summary': 'Work Shift',
            'start': {'dateTime': shift_start.isoformat(), 'timeZone': 'Australia/Sydney'},
            'end': {'dateTime': shift_end.isoformat(), 'timeZone': 'Australia/Sydney'},
            'colorId': '11'
        }
        service.events().insert(calendarId=calendar_id, body=event).execute()
        print("📅 New shift added:", shift_start, "-", shift_end)


if __name__ == "__main__":
    with open("schedule.json", "r") as f:
        data = json.load(f)

    service = get_calendar_service()
    sync_all_shifts(data.get("regularShifts", []), service)
