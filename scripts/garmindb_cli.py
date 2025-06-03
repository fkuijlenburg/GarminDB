import os
import json
import datetime
import requests
import time
from pathlib import Path
from garminconnect import Garmin

# === ENV ===
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

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

def daterange(start_date, end_date):
    for n in range((end_date - start_date).days + 1):
        yield start_date + datetime.timedelta(n)

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
        "calories": to_int(a.get("calories")),
        "start_time_local": a.get("startTimeLocal"),
        "end_time_local": a.get("endTimeLocal"),
        "data": a
    }

def transform_stat_keys(stat):
    def snake_case(k):
        return ''.join(['_' + c.lower() if c.isupper() else c for c in k]).lstrip('_')
    return {snake_case(k): v for k, v in stat.items() if not isinstance(v, dict)}

# === Supabase Upload ===
TABLE_COLUMNS_CACHE = {}

def get_table_columns(table_name):
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }

    resp = requests.post(
        f"{SUPABASE_URL}/rest/v1/rpc/get_columns",
        headers=headers,
        json={ "tablename": table_name }
    )

    if resp.status_code != 200:
        raise Exception(f"Failed to fetch schema for {table_name}: {resp.status_code} {resp.text}")

    return {row["column_name"] for row in resp.json()}

def upload_to_supabase(table_name, records):
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates"
    }

    if table_name not in TABLE_COLUMNS_CACHE:
        TABLE_COLUMNS_CACHE[table_name] = get_table_columns(table_name)
    allowed_keys = TABLE_COLUMNS_CACHE[table_name]

    for record in records:
        filtered = {k: v for k, v in record.items() if k in allowed_keys}
        res = requests.post(f"{SUPABASE_URL}/rest/v1/{table_name}", headers=headers, json=[filtered])
        if res.status_code >= 300:
            print(f"❌ Upload to {table_name} failed: {res.status_code} {res.text}")
        else:
            print(f"✅ Uploaded to {table_name}")

# === Main ===
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

    # === 1. Activities ===
    activities = client.get_activities(0, 10)
    full_data["activities"] = activities
    upload_to_supabase("activities", [transform_activity(a) for a in activities])

    # === 2. Daily Stats & Sleep ===
    start = datetime.date(2020, 1, 1)
    end = datetime.date.today()
    for day in daterange(start, end):
        ds = day.strftime("%Y-%m-%d")
        print(f"📅 Processing {ds}")
        try:
            stat = client.get_stats(ds)
            if not isinstance(stat, dict):
                raise ValueError("Garmin get_stats() did not return a dict")

            rule = stat.get("rule") if isinstance(stat.get("rule"), dict) else {}
            stat["rule_type"] = rule.get("typeKey")

            stat = transform_stat_keys(stat)
            stat["calendar_date"] = stat.get("calendar_date") or ds

            full_data["daily_stats"].append(stat)
            upload_to_supabase("daily_stats", [stat])
        except Exception as e:
            print(f"⚠️ Stats failed for {ds}: {e}")

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
        except Exception as e:
            print(
