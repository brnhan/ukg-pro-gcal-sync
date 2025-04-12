import json
from datetime import datetime, timedelta
from calendar_auth import get_calendar_service
import pytz

def sync_shift_to_calendar(shift, service, calendar_id='primary'):
    tz = pytz.timezone('Australia/Sydney')
    shift_start = tz.localize(datetime.fromisoformat(shift["startDateTime"]))
    shift_end = tz.localize(datetime.fromisoformat(shift["endDateTime"]))
    shift_title = "Work Shift"

    # Get events for the whole day
    start_of_day = shift_start.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)

    events = service.events().list(
        calendarId=calendar_id,
        timeMin=start_of_day.isoformat(),
        timeMax=end_of_day.isoformat(),
        singleEvents=True,
        orderBy='startTime'
    ).execute().get('items', [])

    for event in events:
        if event['summary'] != shift_title:
            continue

        existing_start = datetime.fromisoformat(event['start']['dateTime']).astimezone(tz)
        existing_end = datetime.fromisoformat(event['end']['dateTime']).astimezone(tz)

        if existing_start == shift_start and existing_end == shift_end:
            print("✅ Shift already exists, skipping.")
            return
        else:
            service.events().delete(calendarId=calendar_id, eventId=event['id']).execute()
            print("🗑️ Deleted outdated shift on:", shift_start.date())
            break

    event = {
        'summary': shift_title,
        'start': {'dateTime': shift_start.isoformat(), 'timeZone': 'Australia/Sydney'},
        'end': {'dateTime': shift_end.isoformat(), 'timeZone': 'Australia/Sydney'},
        'colorId': '11'  # Red
    }
    service.events().insert(calendarId=calendar_id, body=event).execute()
    print("📅 New shift added:", shift_start, "-", shift_end)

if __name__ == "__main__":
    with open("schedule.json", "r") as f:
        data = json.load(f)

    service = get_calendar_service()
    for shift in data.get("regularShifts", []):
        sync_shift_to_calendar(shift, service)