import threading
import time
import customtkinter as ctk
from rules.rule_controller import RuleController
from quota.quota_engine import QuotaEngine
from monitor.poller import ActiveWindowPoller
from enforcement.enforcement_controller import EnforcementController

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class FocusGuardGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("FocusGuard - Process & Quota Control")
        self.geometry("600x450")

        # Core Engines
        self.rule_controller = RuleController()
        self.quota_engine = QuotaEngine(self.rule_controller)
        self.poller = ActiveWindowPoller(self.rule_controller)
        self.enforcement = EnforcementController()

        self.is_monitoring = False

        # Build UI Components
        self._build_ui()

    def _build_ui(self):
        # Header
        self.header_label = ctk.CTkLabel(self, text="FocusGuard Dashboard", font=("Helvetica", 20, "bold"))
        self.header_label.pack(pady=15)

        # Active App Display Card
        self.status_frame = ctk.CTkFrame(self)
        self.status_frame.pack(fill="x", padx=20, pady=10)

        self.active_app_label = ctk.CTkLabel(
            self.status_frame, 
            text="Active Process: Idle / Paused", 
            font=("Helvetica", 14)
        )
        self.active_app_label.pack(pady=15)

        # Control Buttons
        self.btn_frame = ctk.CTkFrame(self)
        self.btn_frame.pack(fill="x", padx=20, pady=10)

        self.toggle_btn = ctk.CTkButton(
            self.btn_frame, 
            text="Start Background Monitoring", 
            command=self.toggle_monitoring,
            fg_color="green"
        )
        self.toggle_btn.pack(side="left", padx=10, pady=10, expand=True)

        # Rules List Display
        self.rules_box = ctk.CTkTextbox(self, width=540, height=180)
        self.rules_box.pack(padx=20, pady=10)
        self.refresh_rules_display()

    def refresh_rules_display(self):
        self.rules_box.delete("1.0", "end")
        rules = self.rule_controller.get_all_rules()
        self.rules_box.insert("end", "Configured Rules:\n" + "-" * 50 + "\n")
        for app, config in rules.items():
            self.rules_box.insert(
                "end", 
                f"• {app:<18} | Category: {config.get('category'):<12} | Quota: {config.get('quota_minutes')}m\n"
            )

    def toggle_monitoring(self):
        if not self.is_monitoring:
            self.is_monitoring = True
            self.toggle_btn.configure(text="Stop Monitoring", fg_color="red")
            # Start background thread
            threading.Thread(target=self._monitor_loop, daemon=True).start()
        else:
            self.is_monitoring = False
            self.toggle_btn.configure(text="Start Background Monitoring", fg_color="green")
            self.active_app_label.configure(text="Active Process: Idle / Paused")

    def _monitor_loop(self):
        while self.is_monitoring:
            exec_name, category, is_idle = self.poller.poll_cycle()

            if is_idle:
                self.active_app_label.configure(text="System Idle (>300s)")
            else:
                self.quota_engine.log_activity(exec_name, 1)
                spent = self.quota_engine.read_focus_duration(exec_name)
                rule = self.rule_controller.fetch_executable_rule(exec_name)
                quota_sec = rule.get("quota_minutes", 0) * 60

                display_text = f"Active: {exec_name} | Used: {spent}s / {quota_sec}s | Category: {category}"
                self.active_app_label.configure(text=display_text)

                if self.quota_engine.compute_dynamic_quota_allowance(exec_name):
                    self.enforcement.trigger_enforcement(exec_name)

            time.sleep(1)


if __name__ == "__main__":
    app = FocusGuardGUI()
    app.mainloop()
