# UKG Pro GCal Sync

This project logs in to your UKG Pro portal via Microsoft SSO, fetches your rostered shifts, and syncs them to your Google Calendar. It's currently setup for the endeavour link so change the destination based on your use case,

## 🔧 Setup

1. Clone the repo and navigate to the folder:

   ```bash
   git clone <repo-url>
   cd kronos_calendar_sync
   ```

2. Create a virtual environment and install dependencies:

   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   playwright install
   ```

3. Set up Google Calendar API:

   - Visit [Google Cloud Console](https://console.cloud.google.com/)
   - Enable Calendar API and create OAuth credentials
   - Download the credentials as `credentials.json`

4. Store login credentials

   - Create a `.env` file at the root
   - Fill `EMAIL` and `PASSWORD` fields

5. Fetch your schedule:

   ```bash
   python fetch_schedule.py
   ```

   - This will open a browser for Microsoft login if your login state isn't valid
   - Then will save your schedule in `schedule.json`.

6. Sync your shifts to Google Calendar:
   ```bash
   python sync_calendar.py
   ```

## 🛡️ Security

- `.env`, `token.json`, and `credentials.json`, `auth_state.json` and `schedule.json` are ignored via `.gitignore` to prevent leaking sensitive information.

## ✅ Features

- Auth via real browser session (Playwright)
- Google Calendar sync with duplicate protection
- Automatically fetches from yesterday to 16 days ahead
- Syncs only regularShifts using datetime module
- Deletes and replaces only misaligned "Work Shift" events
- Inserts shifts with red color coding
- Supports short-term cookie persistence

## 📅 Output Example

```
🗑️ Deleted removed shift: 2025-04-23T13:00:00+10:00 - 2025-04-23T18:00:00+10:00
✅ Shift already exists, skipping: 2025-04-14T15:15:00+10:00 - 2025-04-14T20:15:00+10:00
📅 New shift added: 2025-04-24 13:00:00+10:00 - 2025-04-24 18:00:00+10:00
```
