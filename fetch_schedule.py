import os
import requests
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

XSRF_TOKEN = os.getenv("XSRF_TOKEN")
COOKIE_HEADER = os.getenv("COOKIE_HEADER")

def fetch_schedule():
    today = datetime.now()
    start_date = (today - timedelta(days=1)).strftime("%Y-%m-%d")
    end_date = (today + timedelta(days=15)).strftime("%Y-%m-%d")

    url = "https://endeavourgroup-sso.prd.mykronos.com/myschedule/events"
    headers = {
        "Content-Type": "application/json",
        "X-XSRF-TOKEN": XSRF_TOKEN,
        "Cookie": COOKIE_HEADER,
        "Origin": "https://endeavourgroup-sso.prd.mykronos.com",
        "Referer": "https://endeavourgroup-sso.prd.mykronos.com/wfd/ess/myschedule",
        "User-Agent": "Mozilla/5.0",
    }
    payload = {
        "data": {
            "calendarConfigId": 3000002,
            "includedEntities": [
                "entity.openshift", "entity.transfershift", "entity.scheduletag",
                "entity.regularshift", "entity.paycodeedit", "entity.holiday",
                "entity.swaprequest", "entity.openshiftrequest", "entity.coverrequest",
                "entity.timeoffrequest"
            ],
            "includedCoverRequestsStatuses": [],
            "includedSwapRequestsStatuses": [],
            "includedTimeOffRequestsStatuses": [],
            "includedOpenShiftRequestsStatuses": [],
            "includedSelfScheduleRequestsStatuses": [],
            "includedAvailabilityRequestsStatuses": [],
            "includedAvailabilityPatternRequestsStatuses": [],
            "dateSpan": {"start": start_date, "end": end_date},
            "showJobColoring": True,
            "showOrgPathToDisplay": True,
            "includeEmployeePreferences": True,
            "includeNodeAddress": True,
            "removeDuplicatedEntities": True,
            "hideInvisibleTORPayCodes": True
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        data = response.json()
        with open("schedule.json", "w") as f:
            json.dump(data, f, indent=2)
        print("✅ Schedule saved to schedule.json")
    else:
        print(f"❌ Error {response.status_code}: {response.text}")

if __name__ == "__main__":
    fetch_schedule()