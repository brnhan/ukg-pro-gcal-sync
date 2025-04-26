import json
import os
from pathlib import Path
from datetime import datetime, timedelta

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, Browser, BrowserContext
import requests

# Load credentials
load_dotenv()
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")
if not EMAIL or not PASSWORD:
    raise ValueError("❌ EMAIL and PASSWORD must be set in your environment or .env file.")

STATE_PATH = Path("cookies.json")
TARGET_URL = "https://endeavourgroup-sso.prd.mykronos.com/"
SCHEDULE_API_URL = "https://endeavourgroup-sso.prd.mykronos.com/myschedule/events"

def get_date_range():
    start_date = datetime.now() - timedelta(days=1)
    end_date = start_date + timedelta(days=17)
    return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")

def perform_login(page):
    print("📧 Filling email...")
    page.fill('input[type="email"]', EMAIL)
    page.click('input[type="submit"]')

    print("🔐 Waiting for password field...")
    page.wait_for_selector('input[type="password"]', timeout=10000)
    password_input = page.locator('input[type="password"]')
    password_input.wait_for(state="visible", timeout=15000)

    print("🔑 Filling password...")
    password_input.fill(PASSWORD)
    page.click('input[type="submit"]')

    print("⏳ Waiting for manual 2FA...")
    page.wait_for_url("**/wfd/home", timeout=180000)
    print("✅ Logged in and redirected!")

def perform_schedule_request(xsrf_token, cookie_header) -> bool:
    print("🔄 Attempting request with existing cookies.")
    start_date, end_date = get_date_range()
    payload = {
        "data": {
            "calendarConfigId": 3000002,
            "includedEntities": [
                "entity.openshift", "entity.transfershift", "entity.scheduletag", "entity.regularshift",
                "entity.paycodeedit", "entity.holiday", "entity.swaprequest", "entity.openshiftrequest",
                "entity.coverrequest", "entity.timeoffrequest"
            ],
            "includedCoverRequestsStatuses": [],
            "includedSwapRequestsStatuses": [],
            "includedTimeOffRequestsStatuses": [],
            "includedOpenShiftRequestsStatuses": [],
            "includedSelfScheduleRequestsStatuses": [],
            "includedAvailabilityRequestsStatuses": [],
            "includedAvailabilityPatternRequestsStatuses": [],
            "dateSpan": {
                "start": start_date,
                "end": end_date
            },
            "showJobColoring": True,
            "showOrgPathToDisplay": True,
            "includeEmployeePreferences": True,
            "includeNodeAddress": True,
            "removeDuplicatedEntities": True,
            "hideInvisibleTORPayCodes": True
        }
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*",
        "X-XSRF-TOKEN": xsrf_token,
        "Cookie": cookie_header,
        "Origin": "https://endeavourgroup-sso.prd.mykronos.com",
        "Referer": "https://endeavourgroup-sso.prd.mykronos.com/wfd/ess/myschedule",
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Mobile Safari/537.36"
    }

    response = requests.post(SCHEDULE_API_URL, headers=headers, json=payload)

    if response.status_code != 200:
        print(f"❌ Failed to fetch schedule. Status: {response.status_code}")
        print(response.text)
    else:
        try:
            data = response.json()

            if not data:
                print("❌ Empty response received. Possible invalid credentials or expired session.")
                print(response.text)
            else:
                with open("schedule.json", "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                print("✅ schedule.json saved via direct API request!")
                return True

        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON: {e}")
            print("Response content was:")
            print(response.text)

    print("🗑️ Deleting stale existing Cookies")
    STATE_PATH.unlink()
    print("🔐 Attempting fresh request")
    return False

def init_browser_context(browser: Browser) -> BrowserContext:
    if STATE_PATH.exists() and STATE_PATH.stat().st_size > 0:
        try:
            json.loads(STATE_PATH.read_text())
            return browser.new_context(storage_state=str(STATE_PATH))
        except json.JSONDecodeError:
            print("⚠️ browser_cookies.json is invalid — deleting.")
            STATE_PATH.unlink()
            return browser.new_context()
    else:
        return browser.new_context()


with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)

    while True:
        context = init_browser_context(browser)

        page = context.new_page()

        if not STATE_PATH.exists():
            page.goto(TARGET_URL)
            perform_login(page)
            context.storage_state(path=STATE_PATH)
        else:
            page.goto("https://endeavourgroup-sso.prd.mykronos.com/wfd/home")
            page.wait_for_url("**/wfd/home", timeout=60000)

        # Extract XSRF-TOKEN and cookies
        cookies = context.cookies()
        cookie_header = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
        xsrf_token = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), None)

        if not xsrf_token:
            raise RuntimeError("❌ XSRF-TOKEN not found in cookies.")

        print("🧪 Making API call directly with session cookies and XSRF-TOKEN...")
        if perform_schedule_request(xsrf_token, cookie_header):
            break

    browser.close()