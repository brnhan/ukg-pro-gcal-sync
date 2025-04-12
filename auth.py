from playwright.sync_api import sync_playwright
import os

def save_env(xsrf_token, cookie_header):
    with open(".env", "w") as f:
        f.write(f'XSRF_TOKEN={xsrf_token}\n')
        f.write(f'COOKIE_HEADER="{cookie_header}"\n')

def login_and_save_cookies():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        page.goto("https://endeavourgroup-sso.prd.mykronos.com/")
        input("Login via Microsoft SSO and press Enter...")

        cookies = context.cookies()
        cookie_header = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
        xsrf_token = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), None)

        save_env(xsrf_token, cookie_header)
        print("✅ Cookies saved to .env")
        browser.close()

if __name__ == "__main__":
    login_and_save_cookies()
