import json
import os
from typing import Dict, Any


class RuleController:
    """UC1: Manages application monitoring rules, categories, and time quotas (D1 Database interface)."""

    def __init__(self, db_path: str = "rules.json"):
        self.db_path = db_path
        self.rules = self._load_rules()

    def _load_rules(self) -> Dict[str, Dict[str, Any]]:
        """Loads rules from JSON storage or initializes default configuration."""
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                print(f"[WARN] Corrupted or unreadable {self.db_path}. Initializing defaults.")

        # Default fallback rules
        default_rules = {
            "chrome.exe": {"category": "Distracting", "quota_minutes": 60},
            "discord.exe": {"category": "Distracting", "quota_minutes": 30},
            "steam.exe": {"category": "Distracting", "quota_minutes": 15},
            "code.exe": {"category": "Productive", "quota_minutes": 480}
        }
        self._save(default_rules)
        return default_rules

    def validate_and_save_rule(self, exec_name: str, category: str, quota_minutes: int) -> bool:
        """Validates input formats and saves/updates the rule in the database."""
        if not exec_name or not isinstance(exec_name, str):
            return False

        clean_exec = exec_name.strip().lower()
        if not clean_exec.endswith(".exe"):
            return False

        if category not in ["Distracting", "Productive", "Neutral"]:
            return False

        # Ensure quota_minutes is strictly an int (rejecting booleans) and non-negative
        if type(quota_minutes) is not int or quota_minutes < 0:
            return False

        # Update local state and persist to D1 JSON store
        self.rules[clean_exec] = {
            "category": category,
            "quota_minutes": quota_minutes
        }
        self._save(self.rules)
        return True

    def delete_rule(self, exec_name: str) -> bool:
        """Removes a configured rule for a specific executable."""
        clean_exec = exec_name.strip().lower()
        if clean_exec in self.rules:
            del self.rules[clean_exec]
            self._save(self.rules)
            return True
        return False

    def _save(self, data: Dict[str, Dict[str, Any]]) -> None:
        """Persists current rule dictionary to rules.json."""
        with open(self.db_path, "w") as f:
            json.dump(data, f, indent=4)

    def fetch_executable_rule(self, exec_name: str) -> Dict[str, Any]:
        """Queries rule definition for a specific process name."""
        clean_exec = exec_name.strip().lower()
        return self.rules.get(clean_exec, {"category": "Uncategorized", "quota_minutes": 0})

    def get_all_rules(self) -> Dict[str, Dict[str, Any]]:
        """Returns all currently configured rules."""
        return self.rules
