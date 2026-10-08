import sys
import os
import argparse
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


def enable_windows_dpi_awareness():
    """Enables High-DPI scaling on Windows 11 to ensure crisp CustomTkinter rendering."""
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Per-monitor DPI aware
        except Exception:
            try:
                import ctypes
                ctypes.windll.user32.SetProcessDPIAware()  # Legacy fallback
            except Exception:
                pass


def launch_gui() -> bool:
    """Attempts to launch the CustomTkinter GUI desktop application."""
    try:
        from gui.app import FocusGuardGUI
    except ImportError as e:
        print(f"[WARN] Failed to launch GUI mode: {e}")
        print("[HINT] Run 'pip install customtkinter pystray Pillow' to enable GUI support.")
        print("[INFO] Falling back to CLI mode...\n")
        return False

    enable_windows_dpi_awareness()
    app = FocusGuardGUI()
    app.mainloop()
    return True


class FocusGuardCLI:
    """Interactive terminal control panel fallback."""

    def __init__(self):
        self.rule_controller = RuleController()
        if FULL_SYSTEM_AVAILABLE:
            self.poller = ActiveWindowPoller(self.rule_controller)
            self.quota_engine = QuotaEngine(self.rule_controller)
            self.enforcement_controller = EnforcementController()

    def add_rule_interactive(self):
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

        if self.rule_controller.validate_and_save_rule(exec_name, category, quota):
            print(f"[SUCCESS] Saved: {exec_name} | Category: {category} | Quota: {quota}m")
        else:
            print("[REJECTED] Validation failed. Ensure executable ends in '.exe'.")

    def view_rules_interactive(self):
        print("\n--- Configured Rules Database (rules.json) ---")
        rules = self.rule_controller.get_all_rules()
        if not rules:
            print("No rules configured yet.")
            return
        for app, config in rules.items():
            print(f" -> Process: {app:<16} | Category: {config.get('category'):<11} | Quota: {config.get('quota_minutes')}m")

    def run_live_monitor_loop(self):
        if not FULL_SYSTEM_AVAILABLE:
            print("\n[NOTICE] Complete UC2 and UC3 modules to unlock live monitoring.")
            return

        print("\n--- Real-Time Monitor Loop (Ctrl+C to stop) ---")
        try:
            while True:
                exec_name, category, is_idle = self.poller.poll_cycle()
                if is_idle:
                    print("[IDLE] System inactive (>300s). Focus logging paused...", end="\r")
                else:
                    self.quota_engine.log_activity(exec_name, 1)
                    spent = self.quota_engine.read_focus_duration(exec_name)
                    rule = self.rule_controller.fetch_executable_rule(exec_name)
                    quota_sec = rule.get("quota_minutes", 0) * 60

                    print(
                        f"[MONITORING] Active: {exec_name:<16} | Spent: {spent:<4}s / {quota_sec:<4}s | Cat: {category:<11}",
                        end="\r",
                    )

                    if self.quota_engine.compute_dynamic_quota_allowance(exec_name):
                        print(f"\n[QUOTA BREACH] Executable '{exec_name}' exceeded quota!")
                        self.enforcement_controller.trigger_enforcement(exec_name)

                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[STOPPED] Monitoring loop stopped.")

    def start(self):
        while True:
            mode_str = "Full System Ready" if FULL_SYSTEM_AVAILABLE else "UC1 Mode Only"
            print("\n==================================================")
            print(f"         FocusGuard Control Panel ({mode_str})     ")
            print("==================================================")
            print("1. Configure / Add Executable Rule (UC1)")
            print("2. View All Stored Rules (D1 Database)")
            if FULL_SYSTEM_AVAILABLE:
                print("3. Start Continuous Real-Time Monitoring Loop (UC2/UC3)")
                print("4. Exit")
            else:
                print("3. Exit")

            choice = input("\nSelect an option: ").strip()
            if choice == "1":
                self.add_rule_interactive()
            elif choice == "2":
                self.view_rules_interactive()
            elif choice == "3" and FULL_SYSTEM_AVAILABLE:
                self.run_live_monitor_loop()
            elif choice == "4" or (choice == "3" and not FULL_SYSTEM_AVAILABLE):
                print("Exiting FocusGuard.")
                break
            else:
                print("[ERROR] Invalid selection.")


def main():
    parser = argparse.ArgumentParser(description="FocusGuard Desktop Process & Quota Monitor")
    parser.add_argument("--cli", action="store_true", help="Launch in terminal CLI mode instead of GUI")
    args = parser.parse_args()

    if args.cli:
        cli_app = FocusGuardCLI()
        cli_app.start()
    else:
        success = launch_gui()
        if not success:
            cli_app = FocusGuardCLI()
            cli_app.start()


if __name__ == "__main__":
    main()
