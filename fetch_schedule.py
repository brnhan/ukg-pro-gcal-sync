import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

# Load .env file
load_dotenv()

EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")

if not EMAIL or not PASSWORD:
    raise ValueError("❌ EMAIL and PASSWORD must be set in your environment or .env file.")

STATE_PATH = Path("auth_state.json")
TARGET_URL = "https://endeavourgroup-sso.prd.mykronos.com/"
FINAL_SCHEDULE_URL = "https://endeavourgroup-sso.prd.mykronos.com/wfd/ess/myschedule/"
SCHEDULE_API_URL_PREFIX = "https://endeavourgroup-sso.prd.mykronos.com/myschedule/events"

def is_schedule_request(response):
    return (
        response.url.startswith(SCHEDULE_API_URL_PREFIX)
        and response.request.resource_type == "xhr"
    )

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

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)

    # Validate the saved auth state
    if STATE_PATH.exists() and STATE_PATH.stat().st_size > 0:
        try:
            json.loads(STATE_PATH.read_text())
            context = browser.new_context(storage_state=str(STATE_PATH))
        except json.JSONDecodeError:
            print("⚠️ auth_state.json is invalid — deleting.")
            STATE_PATH.unlink()
            context = browser.new_context()
    else:
        context = browser.new_context()

    page = context.new_page()

    # Log in and save state if needed
    if not STATE_PATH.exists():
        page.goto(TARGET_URL)
        perform_login(page)
        context.storage_state(path=STATE_PATH)
    else:
        page.goto(TARGET_URL)
        page.wait_for_url("**/wfd/home", timeout=60000)

    # Go to the final schedule page
    print("➡️ Navigating to final schedule page...")
    page.goto(FINAL_SCHEDULE_URL)
    page.wait_for_url("**/myschedule**")

    # Capture only responses AFTER reaching the correct page
    captured_data = {}

    def handle_response(response):
        if is_schedule_request(response):
            print(f"📡 Captured schedule JSON: {response.url}")
            try:
                captured_data["json"] = response.json()
            except Exception as e:
                print("⚠️ Failed to parse JSON:", e)

    page.on("response", handle_response)

    print("⏳ Waiting for schedule request to complete...")
    page.wait_for_timeout(5000)  # Wait a bit for data to load

    if "json" in captured_data:
        with open("schedule.json", "w", encoding="utf-8") as f:
            json.dump(captured_data["json"], f, indent=2)
        print("✅ schedule.json saved!")
    else:
        print("❌ No schedule data was captured.")

    browser.close()