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
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates"
    }
    for record in records:
        res = requests.post(f"{url}/rest/v1/{table_name}", headers=headers, json=[record])
        if res.status_code >= 300:
            print(f"❌ Upload to {table_name} failed: {res.status_code} {res.text}")
        else:
            print(f"✅ Uploaded to {table_name}")

def transform_activity(a):
    return {
        "activity_id": a.get("activityId"),
        "activity_name": a.get("activityName"),
        "activity_type": a.get("activityType", {}).get("typeKey"),
        "sport_type_id": a.get("sportTypeId"),
        "duration": a.get("duration"),
        "elapsed_duration": a.get("elapsedDuration"),
        "moving_duration": a.get("movingDuration"),
        "lap_count": a.get("lapCount"),
        "manual_activity": a.get("manualActivity"),
        "purposeful": a.get("purposeful"),

        "average_hr": a.get("averageHR"),
        "max_hr": a.get("maxHR"),
        "hr_zone_1_secs": a.get("hrTimeInZone1"),
        "hr_zone_2_secs": a.get("hrTimeInZone2"),
        "hr_zone_3_secs": a.get("hrTimeInZone3"),
        "hr_zone_4_secs": a.get("hrTimeInZone4"),
        "hr_zone_5_secs": a.get("hrTimeInZone5"),

        "aerobic_training_effect": a.get("aerobicTrainingEffect"),
        "anaerobic_training_effect": a.get("anaerobicTrainingEffect"),
        "aerobic_te_message": a.get("aerobicTrainingEffectMessage"),
        "anaerobic_te_message": a.get("anaerobicTrainingEffectMessage"),

        "calories": a.get("calories"),
        "bmr_calories": a.get("bmrCalories"),
        "auto_calc_calories": a.get("autoCalcCalories"),
        "moderate_intensity_minutes": a.get("moderateIntensityMinutes"),
        "vigorous_intensity_minutes": a.get("vigorousIntensityMinutes"),

        "distance": a.get("distance"),
        "average_speed": a.get("averageSpeed"),
        "avg_stride_length": a.get("avgStrideLength"),

        "steps": a.get("steps"),
        "max_running_cadence": a.get("maxRunningCadenceInStepsPerMinute"),
        "avg_running_cadence": a.get("averageRunningCadenceInStepsPerMinute"),
        "max_double_cadence": a.get("maxDoubleCadence"),

        "start_time_gmt": a.get("startTimeGMT"),
        "end_time_gmt": a.get("endTimeGMT"),
        "start_time_local": a.get("startTimeLocal"),
        "begin_timestamp": a.get("beginTimestamp"),
        "min_lap_duration": a.get("minActivityLapDuration"),

        "water_estimated": a.get("waterEstimated"),

        "pr": a.get("pr"),
        "favorite": a.get("favorite"),
        "has_splits": a.get("hasSplits"),
        "has_polyline": a.get("hasPolyline"),
        "has_heat_map": a.get("hasHeatMap"),
        "has_images": a.get("hasImages"),
        "has_video": a.get("hasVideo"),
        "event_type": a.get("eventType", {}).get("typeKey"),
        "device_id": a.get("deviceId"),
        "manufacturer": a.get("manufacturer"),
        "owner_id": a.get("ownerId"),
        "owner_full_name": a.get("ownerFullName"),
        "owner_display_name": a.get("ownerDisplayName"),

        "user_pro": a.get("userPro"),
        "user_roles": a.get("userRoles"),
        "privacy": a.get("privacy", {}).get("typeKey"),

        "profile_img_small": a.get("ownerProfileImageUrlSmall"),
        "profile_img_medium": a.get("ownerProfileImageUrlMedium"),
        "profile_img_large": a.get("ownerProfileImageUrlLarge"),

        "deco_dive": a.get("decoDive"),
        "qualifying_dive": a.get("qualifyingDive"),
        "dive_gases": a.get("summarizedDiveInfo", {}).get("summarizedDiveGases"),

        "data": a  # full JSON backup
    }

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
