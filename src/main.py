import sys
import os

# Ensure local imports work relative to src directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rules.rule_controller import RuleController

# Dynamic feature detection for UC2 & UC3 modules
FULL_SYSTEM_AVAILABLE = True
try:
    from monitor.poller import ActiveWindowPoller
    from quota.quota_engine import QuotaEngine
    from enforcement.enforcement_controller import EnforcementController
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
            print(f"[REJECTED] Validation failed. Ensure executable ends in '.exe' and inputs are valid.")

    def view_rules_interactive(self):
        """Display all configured rules from D1 database."""
        print("\n--- Configured Rules Database (rules.json) ---")
        rules = self.rule_controller.get_all_rules()
        if not rules:
            print("No rules configured yet.")
            return
        
        for app, config in rules.items():
            print(f" -> Process: {app:<16} | Category: {config.get('category'):<11} | Quota: {config.get('quota_minutes')}m")

    def run_pipeline_interactive(self):
        """Execute monitoring and evaluation cycle (Requires UC2/UC3 modules)."""
        if not FULL_SYSTEM_AVAILABLE:
            print("\n[NOTICE] Full system pipeline unavailable. Complete UC2 and UC3 modules to unlock.")
            return

        print("\n--- Running Active Window Monitoring & Quota Evaluation ---")
        target_app = input("Enter active process name to evaluate (e.g., chrome.exe): ").strip()
        
        exec_name, category, is_idle = self.poller.poll_cycle()
        if is_idle:
            print("[STATUS] System Idle > 300s. Logging paused.")
            return

        try:
            duration = int(input(f"Enter active seconds spent on '{target_app}': ").strip())
        except ValueError:
            print("[ERROR] Duration must be a valid integer.")
            return

        self.quota_engine.log_activity(target_app, duration)
        spent = self.quota_engine.read_focus_duration(target_app)
        print(f" -> Total tracked time for '{target_app}': {spent} seconds.")

        if self.quota_engine.compute_dynamic_quota_allowance(target_app):
            print(f"[ALERT] Quota limit reached for '{target_app}'. Initializing enforcement...")
            self.enforcement_controller.trigger_enforcement(target_app)
        else:
            print(f"[STATUS] Usage within quota limits. Continuing monitoring.")


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
            print("3. Run Active Monitoring & Quota Evaluation Pipeline (UC2/UC3)")
        print("4. Exit")
        
        choice = input("\nSelect an option: ").strip()

        if choice == "1":
            app.add_rule_interactive()
        elif choice == "2":
            app.view_rules_interactive()
        elif choice == "3" and FULL_SYSTEM_AVAILABLE:
            app.run_pipeline_interactive()
        elif choice == "4" or (choice == "3" and not FULL_SYSTEM_AVAILABLE and input("Exit application? (y/n): ").lower() == 'y'):
            print("Exiting FocusGuard system.")
            break
        else:
            print("[ERROR] Invalid selection. Please try again.")


if __name__ == "__main__":
    main()