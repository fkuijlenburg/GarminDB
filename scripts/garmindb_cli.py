import os
import json
import datetime
import requests
import time
from pathlib import Path
from garminconnect import Garmin

# === Helpers ===
def to_int(value):
    try:
        return int(float(value)) if value is not None else None
    except (ValueError, TypeError):
        return None

def to_float(value):
    try:
        return float(value) if value is not None else None
    except (ValueError, TypeError):
        return None

def to_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() == "true"
    return None

def save_json(data, filename="garmin_full_backup.json"):
    Path("data").mkdir(parents=True, exist_ok=True)
    with open(f"data/{filename}", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def upload_to_supabase(table_name, records):
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_KEY"]
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates"
    }
    for record in records:
        res = requests.post(f"{url}/rest/v1/{table_name}", headers=headers, json=[record])
        if res.status_code >= 300:
            print(f"❌ Upload to {table_name} failed: {res.status_code} {res.text}")
        else:
            print(f"✅ Uploaded to {table_name}")

def daterange(start_date, end_date):
    for n in range((end_date - start_date).days + 1):
        yield start_date + datetime.timedelta(n)

def fetch_all_activities(client):
    all_activities = []
    start = 0
    batch = 100
    while True:
        activities = client.get_activities(start, batch)
        if not activities:
            break
        all_activities.extend(activities)
        start += batch
        print(f"📦 {len(all_activities)} total activities fetched...")
        time.sleep(1)
    return all_activities

def transform_activity(a):
    return {
        "activity_id": to_int(a.get("activityId")),
        "activity_name": a.get("activityName"),
        "activity_type": a.get("activityType", {}).get("typeKey"),
        "sport_type_id": to_int(a.get("sportTypeId")),
        "duration": to_float(a.get("duration")),
        "elapsed_duration": to_float(a.get("elapsedDuration")),
        "moving_duration": to_float(a.get("movingDuration")),
        "lap_count": to_int(a.get("lapCount")),
        "manual_activity": to_bool(a.get("manualActivity")),
        "purposeful": to_bool(a.get("purposeful")),
        "average_hr": to_int(a.get("averageHR")),
        "max_hr": to_int(a.get("maxHR")),
        "hrTimeInZone_1": to_float(a.get("hrTimeInZone_1")),
        "hrTimeInZone_2": to_float(a.get("hrTimeInZone_2")),
        "hrTimeInZone_3": to_float(a.get("hrTimeInZone_3")),
        "hrTimeInZone_4": to_float(a.get("hrTimeInZone_4")),
        "hrTimeInZone_5": to_float(a.get("hrTimeInZone_5")),
        "calories": to_int(a.get("calories")),
        "start_time_local": a.get("startTimeLocal"),
        "end_time_local": a.get("endTimeLocal"),
        "data": a
    }

def main():
    username = os.environ.get("GARMIN_USERNAME")
    password = os.environ.get("GARMIN_PASSWORD")
    client = Garmin(username, password)
    client.login()

    full_data = {
        "activities": [],
        "daily_stats": [],
        "sleep": [],
        "sleep_summary": []
    }

    # === 1. Fetch All Activities ===
    activities = fetch_all_activities(client)
    full_data["activities"] = activities
    upload_to_supabase("activities", [transform_activity(a) for a in activities])

    # === 2. Monitoring to daily_stats ===
    start = datetime.date(2020, 1, 1)
    end = datetime.date.today()
    for day in daterange(start, end):
        ds = day.strftime("%Y-%m-%d")
        print(f"📅 Processing {ds}")
        try:
            stat = client.get_stats(ds)
            stat["calendar_date"] = ds
            full_data["daily_stats"].append(stat)
            upload_to_supabase("daily_stats", [stat])
        except:
            pass

        try:
            sleep = client.get_sleep_data(ds)
            full_data["sleep"].append({"date": ds, "data": sleep})
            dto = sleep.get("dailySleepDTO", {})
            if dto.get("calendarDate"):
                row = {
                    "calendar_date": dto.get("calendarDate"),
                    "sleep_seconds": to_int(dto.get("sleepTimeSeconds")),
                    "deep_sleep_seconds": to_int(dto.get("deepSleepSeconds")),
                    "light_sleep_seconds": to_int(dto.get("lightSleepSeconds")),
                    "rem_sleep_seconds": to_int(dto.get("remSleepSeconds")),
                    "awake_sleep_seconds": to_int(dto.get("awakeSleepSeconds")),
                    "average_spo2": to_float(dto.get("averageSpO2Value")),
                    "average_respiration": to_float(dto.get("averageRespirationValue"))
                }
                full_data["sleep_summary"].append(row)
                upload_to_supabase("sleep_summary", [row])
        except:
            pass

        time.sleep(1)

    # === Save JSON backup ===
    save_json(full_data)

if __name__ == "__main__":
    main()
