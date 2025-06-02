import os
import json
import datetime
from pathlib import Path
from garminconnect import Garmin
from GarminConnectConfigManager import GarminConnectConfigManager  # assuming it's in the same dir or adjust import

def save_garmin_data_as_json(data, config: GarminConnectConfigManager, filename="garmin_data.json"):
    output_path = Path(config._base_dir) / filename
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✅ Garmin data saved to {output_path}")

def main():
    # Load credentials from environment
    username = os.environ.get("GARMIN_USERNAME")
    password = os.environ.get("GARMIN_PASSWORD")

    if not username or not password:
        raise Exception("Missing GARMIN_USERNAME or GARMIN_PASSWORD")

    # Set up config and Garmin client
    config = GarminConnectConfigManager()
    client = Garmin(username, password)
    client.login()

    # Fetch data
    print("🔄 Fetching Garmin data...")

    data = {}
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    week_ago = today - datetime.timedelta(days=7)

    # 1. Activities
    try:
        count = config.latest_activity_count()
        activities = client.get_activities(0, count)
        data["activities"] = activities
    except Exception as e:
        print(f"⚠️ Failed to fetch activities: {e}")

    # 2. Monitoring (steps, calories, etc.)
    try:
        monitoring = []
        for i in range(7):
            day = (today - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
            day_data = client.get_stats(day)
            monitoring.append({"date": day, "data": day_data})
        data["monitoring"] = monitoring
    except Exception as e:
        print(f"⚠️ Failed to fetch monitoring data: {e}")

    # 3. Sleep
    try:
        sleep_data = []
        for i in range(7):
            day = (today - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
            entry = client.get_sleep_data(day)
            sleep_data.append({"date": day, "data": entry})
        data["sleep"] = sleep_data
    except Exception as e:
        print(f"⚠️ Failed to fetch sleep data: {e}")

    # 4. Weight
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

    # Save all data to JSON
    save_garmin_data_as_json(data, config)

if __name__ == "__main__":
    main()
