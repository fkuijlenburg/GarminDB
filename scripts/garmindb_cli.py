import os
import json
import datetime
from pathlib import Path
from garminconnect import Garmin

def save_garmin_data_as_json(data, output_dir="data", filename="garmin_data.json"):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    full_path = output_path / filename
    with full_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✅ Garmin data saved to {full_path}")

def main():
    # Load credentials from environment
    username = os.environ.get("GARMIN_USERNAME")
    password = os.environ.get("GARMIN_PASSWORD")

    if not username or not password:
        raise Exception("Missing GARMIN_USERNAME or GARMIN_PASSWORD environment variables.")

    # Initialize Garmin client
    client = Garmin(username, password)
    client.login()

    # Define dates
    today = datetime.date.today()
    week_ago = today - datetime.timedelta(days=7)

    data = {}

    print("🔄 Fetching Garmin data...")

    # 1. Activities
    try:
        activities = client.get_activities(0, 10)  # Fetch 10 latest
        data["activities"] = activities
    except Exception as e:
        print(f"⚠️ Failed to fetch activities: {e}")

    # 2. Monitoring stats (daily steps, calories, etc.)
    try:
        monitoring = []
        for i in range(7):
            day = (today - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
            day_data = client.get_stats(day)
            monitoring.append({"date": day, "data": day_data})
        data["monitoring"] = monitoring
    except Exception as e:
        print(f"⚠️ Failed to fetch monitoring data: {e}")

    # 3. Sleep data
    try:
        sleep_data = []
        for i in range(7):
            day = (today - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
            entry = client.get_sleep_data(day)
            sleep_data.append({"date": day, "data": entry})
        data["sleep"] = sleep_data
    except Exception as e:
        print(f"⚠️ Failed to fetch sleep data: {e}")

    # 4. Weight / body composition
    try:
        weight_data = client.get_body_composition(week_ago.isoformat(), today.isoformat())
        data["weight"] = weight_data
    except Exception as e:
        print(f"⚠️ Failed to fetch weight data: {e}")

    # 5. Resting Heart Rate (RHR)
    try:
        rhr_data = []
        for i in range(7):
            day = (today - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
            entry = client.get_rhr(day)
            rhr_data.append({"date": day, "rhr": entry})
        data["rhr"] = rhr_data
    except Exception as e:
        print(f"⚠️ Failed to fetch RHR data: {e}")

    # Save to JSON
    save_garmin_data_as_json(data)

if __name__ == "__main__":
    main()
