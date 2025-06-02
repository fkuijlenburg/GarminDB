import os
import json
import datetime
import requests
from pathlib import Path
from garminconnect import Garmin

# === Helpers for safe type conversion ===
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

# === JSON Export ===
def save_garmin_data_as_json(data, output_dir="data", filename="garmin_data.json"):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    full_path = output_path / filename
    with full_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✅ Garmin data saved to {full_path}")

# === Supabase Upload ===
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

# === Activity Parser (updated) ===
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
        "aerobic_training_effect": to_float(a.get("aerobicTrainingEffect")),
        "anaerobic_training_effect": to_float(a.get("anaerobicTrainingEffect")),
        "aerobic_te_message": a.get("aerobicTrainingEffectMessage"),
        "anaerobic_te_message": a.get("anaerobicTrainingEffectMessage"),
        "calories": to_int(a.get("calories")),
        "bmr_calories": to_int(a.get("bmrCalories")),
        "auto_calc_calories": to_bool(a.get("autoCalcCalories")),
        "moderate_intensity_minutes": to_int(a.get("moderateIntensityMinutes")),
        "vigorous_intensity_minutes": to_int(a.get("vigorousIntensityMinutes")),
        "distance": to_float(a.get("distance")),
        "average_speed": to_float(a.get("averageSpeed")),
        "avg_stride_length": to_float(a.get("avgStrideLength")),
        "steps": to_int(a.get("steps")),
        "max_running_cadence": to_int(a.get("maxRunningCadenceInStepsPerMinute")),
        "avg_running_cadence": to_int(a.get("averageRunningCadenceInStepsPerMinute")),
        "max_double_cadence": to_int(a.get("maxDoubleCadence")),
        "start_time_gmt": a.get("startTimeGMT"),
        "end_time_gmt": a.get("endTimeGMT"),
        "start_time_local": a.get("startTimeLocal"),
        "begin_timestamp": to_int(a.get("beginTimestamp")),
        "min_lap_duration": to_float(a.get("minActivityLapDuration")),
        "water_estimated": to_float(a.get("waterEstimated")),
        "pr": to_bool(a.get("pr")),
        "favorite": to_bool(a.get("favorite")),
        "has_splits": to_bool(a.get("hasSplits")),
        "has_polyline": to_bool(a.get("hasPolyline")),
        "has_heat_map": to_bool(a.get("hasHeatMap")),
        "has_images": to_bool(a.get("hasImages")),
        "has_video": to_bool(a.get("hasVideo")),
        "event_type": a.get("eventType", {}).get("typeKey"),
        "device_id": to_int(a.get("deviceId")),
        "manufacturer": a.get("manufacturer"),
        "owner_id": to_int(a.get("ownerId")),
        "owner_full_name": a.get("ownerFullName"),
        "owner_display_name": a.get("ownerDisplayName"),
        "user_pro": to_bool(a.get("userPro")),
        "user_roles": a.get("userRoles"),
        "privacy": a.get("privacy", {}).get("typeKey"),
        "profile_img_small": a.get("ownerProfileImageUrlSmall"),
        "profile_img_medium": a.get("ownerProfileImageUrlMedium"),
        "profile_img_large": a.get("ownerProfileImageUrlLarge"),
        "deco_dive": to_bool(a.get("decoDive")),
        "qualifying_dive": to_bool(a.get("qualifyingDive")),
        "dive_gases": a.get("summarizedDiveInfo", {}).get("summarizedDiveGases"),
        "data": a
    }

# === Main ===
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
        activities = client.get_activities(0, 20)
        data["activities"] = activities
        structured = [transform_activity(a) for a in activities]
        upload_to_supabase("activities", structured)
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

    # 3. Sleep (summarized)
    try:
        sleep_data = []
        sleep_summaries = []
        for i in range(7):
            day = (today - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
            entry = client.get_sleep_data(day)
            sleep_data.append({"date": day, "data": entry})

            dto = entry.get("dailySleepDTO", {})
            if dto.get("calendarDate"):
                sleep_summaries.append({
                    "calendar_date": dto.get("calendarDate"),
                    "sleep_seconds": to_int(dto.get("sleepTimeSeconds")),
                    "deep_sleep_seconds": to_int(dto.get("deepSleepSeconds")),
                    "light_sleep_seconds": to_int(dto.get("lightSleepSeconds")),
                    "rem_sleep_seconds": to_int(dto.get("remSleepSeconds")),
                    "awake_sleep_seconds": to_int(dto.get("awakeSleepSeconds")),
                    "average_spo2": to_float(dto.get("averageSpO2Value")),
                    "average_respiration": to_float(dto.get("averageRespirationValue"))
                })

        data["sleep"] = sleep_data
        upload_to_supabase("sleep_summary", sleep_summaries)
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
