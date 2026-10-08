import sys
import os
import time

# Ensure local imports work relative to src directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rules.rule_controller import RuleController

# Dynamic feature detection for UC2 & UC3 modules
try:
    from monitor.poller import ActiveWindowPoller
    from quota.quota_engine import QuotaEngine
    from enforcement.enforcement_controller import EnforcementController
    FULL_SYSTEM_AVAILABLE = True
except ImportError:
    FULL_SYSTEM_AVAILABLE = False


class FocusGuardApp:
    def __init__(self):
        self.rule_controller = RuleController()
        if FULL_SYSTEM_AVAILABLE:
            self.poller = ActiveWindowPoller(self.rule_controller)
            self.quota_engine = QuotaEngine(self.rule_controller)
            self.enforcement_controller = EnforcementController()

    def add_rule_interactive(self):
        """Manual rule configuration prompt (UC1)."""
        print("\n--- Add / Update Executable Rule ---")
        exec_name = input("Enter executable name (e.g., chrome.exe): ").strip()

        print("Categories: [1] Distracting  [2] Productive  [3] Neutral")
        cat_choice = input("Select category (1-3): ").strip()
        category_map = {"1": "Distracting", "2": "Productive", "3": "Neutral"}
        category = category_map.get(cat_choice, "Distracting")

        try:
            quota = int(input("Enter daily time quota in minutes: ").strip())
        except ValueError:
            print("[ERROR] Quota must be a valid integer.")
            return

        success = self.rule_controller.validate_and_save_rule(exec_name, category, quota)
        if success:
            print(f"[SUCCESS] Saved: {exec_name} | Category: {category} | Quota: {quota}m")
        else:
            print("[REJECTED] Validation failed. Ensure executable ends in '.exe' and inputs are valid.")

    def view_rules_interactive(self):
        """Display all configured rules from D1 database."""
        print("\n--- Configured Rules Database (rules.json) ---")
        rules = self.rule_controller.get_all_rules()
        if not rules:
            print("No rules configured yet.")
            return

        for app, config in rules.items():
            print(f" -> Process: {app:<16} | Category: {config.get('category'):<11} | Quota: {config.get('quota_minutes')}m")

    def run_single_poll_interactive(self):
        """Executes a single foreground window poll and quota evaluation cycle (UC2/UC3)."""
        if not FULL_SYSTEM_AVAILABLE:
            print("\n[NOTICE] Full system pipeline unavailable. Complete UC2 and UC3 modules to unlock.")
            return

        print("\n--- Executing Active Window Poll & Quota Evaluation ---")
        exec_name, category, is_idle = self.poller.poll_cycle()

        if is_idle:
            print("[STATUS] System Idle > 300s. Focus tracking paused.")
            return

        print(f" -> Active Foreground Window: '{exec_name}' (Category: {category})")

        # Log 1-second active interval tick
        self.quota_engine.log_activity(exec_name, 1)
        spent_sec = self.quota_engine.read_focus_duration(exec_name)
        rule = self.rule_controller.fetch_executable_rule(exec_name)
        quota_min = rule.get("quota_minutes", 0)

        print(f" -> Tracked Duration: {spent_sec}s / {quota_min * 60}s quota allowance")

        if self.quota_engine.compute_dynamic_quota_allowance(exec_name):
            print(f"[ALERT] Quota limit reached for '{exec_name}'. Initializing enforcement sequence...")
            self.enforcement_controller.trigger_enforcement(exec_name)
        else:
            print("[STATUS] Usage within configured limit.")

    def run_live_monitor_loop(self):
        """Runs continuous real-time polling (1000ms loop) with automated logging and enforcement."""
        if not FULL_SYSTEM_AVAILABLE:
            print("\n[NOTICE] Full system pipeline unavailable. Complete UC2 and UC3 modules to unlock.")
            return

        print("\n==================================================")
        print("   Starting Real-Time FocusGuard Monitor Loop   ")
        print("   Press Ctrl+C to stop monitoring and return   ")
        print("==================================================")

        try:
            while True:
                exec_name, category, is_idle = self.poller.poll_cycle()

                if is_idle:
                    print("[IDLE] System inactive (>300s). Focus logging paused...", end="\r")
                else:
                    self.quota_engine.log_activity(exec_name, 1)
                    spent = self.quota_engine.read_focus_duration(exec_name)
                    rule = self.rule_controller.fetch_executable_rule(exec_name)
                    quota_min = rule.get("quota_minutes", 0)

                    print(
                        f"[MONITORING] Active: {exec_name:<16} | Spent: {spent:<4}s / {quota_min*60:<4}s | Cat: {category:<11}",
                        end="\r",
                    )

                    if self.quota_engine.compute_dynamic_quota_allowance(exec_name):
                        print(f"\n[QUOTA BREACH] Executable '{exec_name}' exceeded quota!")
                        self.enforcement_controller.trigger_enforcement(exec_name)

                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[STOPPED] Background monitoring loop stopped.")


def main():
    app = FocusGuardApp()

    while True:
        mode_str = "Full System Ready" if FULL_SYSTEM_AVAILABLE else "UC1 Mode Only"
        print("\n==================================================")
        print(f"         FocusGuard Control Panel ({mode_str})     ")
        print("==================================================")
        print("1. Configure / Add Executable Rule (UC1)")
        print("2. View All Stored Rules (D1 Database)")
        if FULL_SYSTEM_AVAILABLE:
            print("3. Single Active Window Poll & Check (UC2)")
            print("4. Start Continuous Real-Time Monitoring Loop (UC2/UC3)")
            print("5. Exit")
        else:
            print("3. Exit")

        choice = input("\nSelect an option: ").strip()

        if choice == "1":
            app.add_rule_interactive()
        elif choice == "2":
            app.view_rules_interactive()
        elif choice == "3" and FULL_SYSTEM_AVAILABLE:
            app.run_single_poll_interactive()
        elif choice == "4" and FULL_SYSTEM_AVAILABLE:
            app.run_live_monitor_loop()
        elif choice == "5" or (choice == "3" and not FULL_SYSTEM_AVAILABLE):
            print("Exiting FocusGuard system.")
            break
        else:
            print("[ERROR] Invalid selection. Please try again.")


if __name__ == "__main__":
    main()
