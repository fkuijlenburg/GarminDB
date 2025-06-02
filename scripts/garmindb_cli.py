import os
import json
import datetime
import requests
from pathlib import Path
from garminconnect import Garmin

def save_garmin_data_as_json(data, output_dir="data", filename="garmin_data.json"):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    full_path = output_path / filename
    with full_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✅ Garmin data saved to {full_path}")

def upload_to_supabase(table_name, records):
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_KEY"]
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }
    for record in records:
        res = requests.post(f"{url}/rest/v1/{table_name}", headers=headers, json=[record])
        if res.status_code >= 300:
            print(f"❌ Upload to {table_name} failed: {res.status_code} {res.text}")
        else:
            print(f"✅ Uploaded to {table_name}")

def main():
    username = os.environ.get("GARMIN_USERNAME")
    password = os.environ.get("GARMIN_PASSWORD")

    if not username or not password:
        raise Exception("Missing GARMIN_USERNAME or GARMIN_PASSWORD")

    client = Garmin(username, password)
    client.login()

    today = datetime.date.today()
    week_ago = today - datetime.timedelta(days=7)

    data = {}

    print("🔄 Fetching Garmin data...")

    # 1. Activities
    try:
        activities = client.get_activities(0, 10)
        data["activities"] = activities
        upload_to_supabase("activities", [{"data": a} for a in activities])
    except Exception as e:
        print(f"⚠️ Activities: {e}")

    # 2. Monitoring
    try:
        monitoring = []
        for i in range(7):
            day = (today - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
            stat = client.get_stats(day)
            monitoring.append({"date": day, "data": stat})
        data["monitoring"] = monitoring
        upload_to_supabase("monitoring", monitoring)
    except Exception as e:
        print(f"⚠️ Monitoring: {e}")

    # 3. Sleep
    try:
        sleep_data = []
        for i in range(7):
            day = (today - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
            entry = client.get_sleep_data(day)
            sleep_data.append({"date": day, "data": entry})
        data["sleep"] = sleep_data
        upload_to_supabase("sleep", sleep_data)
    except Exception as e:
        print(f"⚠️ Sleep: {e}")

    # 4. Weight
    try:
        weight_data = client.get_body_composition(week_ago.isoformat(), today.isoformat())
        wrapped_weight = [{"data": w} for w in weight_data]
        data["weight"] = wrapped_weight
        upload_to_supabase("weight", wrapped_weight)
    except Exception as e:
        print(f"⚠️ Weight: {e}")

    save_garmin_data_as_json(data)

if __name__ == "__main__":
    main()
