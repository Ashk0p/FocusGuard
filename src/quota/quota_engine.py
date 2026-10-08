import json
import os
from typing import Dict, Any


class QuotaEngine:
    """UC2 & UC3: Tracks accumulated focus time and evaluates rule quotas."""

    def __init__(self, rule_controller=None, log_db_path: str = "activity_logs.json"):
        self.rule_controller = rule_controller
        self.log_db_path = log_db_path
        self.activity_logs = self._load_logs()

    def _load_logs(self) -> Dict[str, int]:
        """Loads activity duration logs (in seconds) from D2 JSON store."""
        if os.path.exists(self.log_db_path):
            try:
                with open(self.log_db_path, "r") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                pass
        return {}

    def _save_logs(self) -> None:
        """Persists updated usage durations to activity_logs.json."""
        with open(self.log_db_path, "w") as f:
            json.dump(self.activity_logs, f, indent=4)

    def log_activity(self, exec_name: str, duration_seconds: int) -> None:
        """Increments spent active time for a specific application."""
        clean_exec = exec_name.strip().lower()
        self.activity_logs[clean_exec] = self.activity_logs.get(clean_exec, 0) + duration_seconds
        self._save_logs()

    def read_focus_duration(self, exec_name: str) -> int:
        """Returns total active seconds logged for a given executable."""
        clean_exec = exec_name.strip().lower()
        return self.activity_logs.get(clean_exec, 0)

    def compute_dynamic_quota_allowance(self, exec_name: str) -> bool:
        """
        Evaluates whether active time has met or breached configured quota limits.
        Returns True if quota is breached, False otherwise.
        """
        if not self.rule_controller:
            return False

        clean_exec = exec_name.strip().lower()
        rule = self.rule_controller.fetch_executable_rule(clean_exec)
        quota_minutes = rule.get("quota_minutes", 0)

        if quota_minutes == 0:
            return False

        spent_seconds = self.read_focus_duration(clean_exec)
        quota_seconds = quota_minutes * 60

        return spent_seconds >= quota_seconds
