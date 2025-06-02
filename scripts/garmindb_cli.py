import os

class GarminConnectConfigManager:
    def __init__(self, config_path=None):
        self._base_dir = os.environ.get("GARMINDATA_DIR", os.path.join(os.getcwd(), "data"))
        self._db_dir = os.path.join(self._base_dir, "db")
        self._activities_dir = os.path.join(self._base_dir, "activities")
        self._monitoring_dir = os.path.join(self._base_dir, "monitoring")
        self._sleep_dir = os.path.join(self._base_dir, "sleep")
        self._weight_dir = os.path.join(self._base_dir, "weight")
        self._rhr_dir = os.path.join(self._base_dir, "rhr")
        self._fit_files_dir = os.path.join(self._base_dir, "fit")
        self._backup_dir = os.path.join(self._base_dir, "backup")
        self._plugins_dir = os.path.join(self._base_dir, "plugins")

        os.makedirs(self._db_dir, exist_ok=True)
        os.makedirs(self._activities_dir, exist_ok=True)
        os.makedirs(self._monitoring_dir, exist_ok=True)
        os.makedirs(self._sleep_dir, exist_ok=True)
        os.makedirs(self._weight_dir, exist_ok=True)
        os.makedirs(self._rhr_dir, exist_ok=True)
        os.makedirs(self._fit_files_dir, exist_ok=True)
        os.makedirs(self._backup_dir, exist_ok=True)
        os.makedirs(self._plugins_dir, exist_ok=True)

    def get_plugins_dir(self):
        return self._plugins_dir

    def get_db_params(self):
        return {"db_path": os.path.join(self._db_dir, "garmin.db")}

    def get_activities_dir(self):
        return self._activities_dir

    def get_monitoring_dir(self, year):
        return os.path.join(self._monitoring_dir, str(year))

    def get_monitoring_base_dir(self):
        return self._monitoring_dir

    def get_sleep_dir(self):
        return self._sleep_dir

    def get_weight_dir(self):
        return self._weight_dir

    def get_rhr_dir(self):
        return self._rhr_dir

    def get_fit_files_dir(self):
        return self._fit_files_dir

    def get_backup_dir(self):
        return self._backup_dir

    def get_db_dir(self):
        return self._db_dir

    def stat_start_date(self, stat_name):
        return (datetime.date.today() - datetime.timedelta(days=7), 7)

    def enabled_stats(self):
        return [
            Statistics.activities,
            Statistics.monitoring,
            Statistics.sleep,
            Statistics.weight,
            Statistics.rhr
        ]

    def latest_activity_count(self):
        return int(os.environ.get("GARMIN_LATEST_ACTIVITY_COUNT", 5))

    def all_activity_count(self):
        return int(os.environ.get("GARMIN_ALL_ACTIVITY_COUNT", 30))
