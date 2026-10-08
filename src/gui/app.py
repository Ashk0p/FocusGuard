import os
import sys
import time
import threading
import customtkinter as ctk
from PIL import Image, ImageDraw
import pystray
from pystray import MenuItem as item

# Ensure src root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rules.rule_controller import RuleController
from quota.quota_engine import QuotaEngine
from monitor.poller import ActiveWindowPoller
from enforcement.enforcement_controller import EnforcementController

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class FocusGuardGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window Setup
        self.title("FocusGuard - Process & Quota Monitor")
        self.geometry("750x550")
        self.minsize(700, 500)

        # Core System Controllers
        self.rule_controller = RuleController()
        self.quota_engine = QuotaEngine(self.rule_controller)
        self.poller = ActiveWindowPoller(self.rule_controller)
        self.enforcement = EnforcementController()

        # Monitoring & Thread State
        self.is_monitoring = False
        self.monitor_thread = None
        self.tray_icon = None

        # Build UI & Tray Setup
        self._setup_system_tray()
        self._build_ui()

        # Override close button to minimize to tray instead of hard kill
        self.protocol("WM_DELETE_WINDOW", self.hide_to_tray)

    # ==========================================
    # UI CONSTRUCTION
    # ==========================================
    def _build_ui(self):
        # Header Banner
        self.header_frame = ctk.CTkFrame(self, corner_radius=10)
        self.header_frame.pack(fill="x", padx=20, pady=(15, 10))

        self.title_label = ctk.CTkLabel(
            self.header_frame, 
            text="🛡️ FocusGuard Engine", 
            font=("Segoe UI", 22, "bold")
        )
        self.title_label.pack(side="left", padx=20, pady=15)

        self.status_badge = ctk.CTkLabel(
            self.header_frame,
            text="STATUS: STOPPED",
            font=("Segoe UI", 12, "bold"),
            fg_color="#D32F2F",
            corner_radius=6,
            padx=12,
            pady=4
        )
        self.status_badge.pack(side="right", padx=20, pady=15)

        # Tabview navigation
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        self.tab_dashboard = self.tabview.add("Dashboard")
        self.tab_rules = self.tabview.add("Rule Management")
        self.tab_logs = self.tabview.add("Activity Logs")

        self._setup_dashboard_tab()
        self._setup_rules_tab()
        self._setup_logs_tab()

    # --- TAB 1: DASHBOARD ---
    def _setup_dashboard_tab(self):
        # Active Window Status Card
        self.card_active = ctk.CTkFrame(self.tab_dashboard, corner_radius=10)
        self.card_active.pack(fill="x", padx=15, pady=15)

        self.lbl_active_title = ctk.CTkLabel(
            self.card_active, 
            text="CURRENT ACTIVE WINDOW", 
            font=("Segoe UI", 11, "bold"), 
            text_color="gray"
        )
        self.lbl_active_title.pack(anchor="w", padx=15, pady=(12, 2))

        self.lbl_active_app = ctk.CTkLabel(
            self.card_active, 
            text="System Idle / Unmonitored", 
            font=("Segoe UI", 18, "bold")
        )
        self.lbl_active_app.pack(anchor="w", padx=15, pady=(0, 5))

        self.lbl_app_metrics = ctk.CTkLabel(
            self.card_active, 
            text="Category: None | Time Spent Today: 0s / Quota: 0m", 
            font=("Segoe UI", 12)
        )
        self.lbl_app_metrics.pack(anchor="w", padx=15, pady=(0, 12))

        # Action Button Frame
        self.btn_frame = ctk.CTkFrame(self.tab_dashboard, fg_color="transparent")
        self.btn_frame.pack(fill="x", padx=15, pady=10)

        self.btn_toggle_monitor = ctk.CTkButton(
            self.btn_frame,
            text="Start Real-Time Monitoring",
            font=("Segoe UI", 14, "bold"),
            height=40,
            fg_color="#2E7D32",
            hover_color="#1B5E20",
            command=self.toggle_monitoring
        )
        self.btn_toggle_monitor.pack(fill="x")

    # --- TAB 2: RULE MANAGEMENT ---
    def _setup_rules_tab(self):
        # Input Form
        self.form_frame = ctk.CTkFrame(self.tab_rules)
        self.form_frame.pack(fill="x", padx=15, pady=15)

        self.entry_exec = ctk.CTkEntry(self.form_frame, placeholder_text="Executable (e.g. chrome.exe)", width=220)
        self.entry_exec.grid(row=0, column=0, padx=10, pady=10)

        self.combo_cat = ctk.CTkOptionMenu(self.form_frame, values=["Distracting", "Productive", "Neutral"], width=140)
        self.combo_cat.grid(row=0, column=1, padx=10, pady=10)

        self.entry_quota = ctk.CTkEntry(self.form_frame, placeholder_text="Quota (mins)", width=100)
        self.entry_quota.grid(row=0, column=2, padx=10, pady=10)

        self.btn_add_rule = ctk.CTkButton(self.form_frame, text="Save Rule", width=100, command=self.add_rule)
        self.btn_add_rule.grid(row=0, column=3, padx=10, pady=10)

        self.lbl_rule_msg = ctk.CTkLabel(self.form_frame, text="", font=("Segoe UI", 11))
        self.lbl_rule_msg.grid(row=1, column=0, columnspan=4, pady=(0, 5))

        # Rules Display Table / Scrollable Frame
        self.scroll_rules = ctk.CTkScrollableFrame(self.tab_rules, label_text="Configured Rules (rules.json)")
        self.scroll_rules.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self.refresh_rules_list()

    def refresh_rules_list(self):
        for widget in self.scroll_rules.winfo_children():
            widget.destroy()

        rules = self.rule_controller.get_all_rules()
        if not rules:
            ctk.CTkLabel(self.scroll_rules, text="No executable rules defined.").pack(pady=20)
            return

        for exec_name, info in rules.items():
            row = ctk.CTkFrame(self.scroll_rules, fg_color="transparent")
            row.pack(fill="x", pady=4, padx=5)

            lbl_name = ctk.CTkLabel(row, text=f"• {exec_name}", font=("Segoe UI", 13, "bold"), width=180, anchor="w")
            lbl_name.pack(side="left")

            cat_color = "#E53935" if info["category"] == "Distracting" else "#43A047" if info["category"] == "Productive" else "#FB8C00"
            lbl_cat = ctk.CTkLabel(row, text=info["category"], font=("Segoe UI", 12), text_color=cat_color, width=120, anchor="w")
            lbl_cat.pack(side="left")

            lbl_quota = ctk.CTkLabel(row, text=f"{info['quota_minutes']} min quota", font=("Segoe UI", 12), width=120, anchor="w")
            lbl_quota.pack(side="left")

            btn_del = ctk.CTkButton(
                row, 
                text="Delete", 
                width=70, 
                fg_color="#C62828", 
                hover_color="#8E0000",
                command=lambda e=exec_name: self.delete_rule(e)
            )
            btn_del.pack(side="right", padx=5)

    def add_rule(self):
        exec_name = self.entry_exec.get().strip()
        category = self.combo_cat.get()
        quota_str = self.entry_quota.get().strip()

        try:
            quota = int(quota_str)
        except ValueError:
            self.lbl_rule_msg.configure(text="❌ Quota must be a valid integer.", text_color="#FF5252")
            return

        success = self.rule_controller.validate_and_save_rule(exec_name, category, quota)
        if success:
            self.lbl_rule_msg.configure(text=f"✓ Rule saved for {exec_name.lower()}", text_color="#66BB6A")
            self.entry_exec.delete(0, "end")
            self.entry_quota.delete(0, "end")
            self.refresh_rules_list()
            self.refresh_logs_list()
        else:
            self.lbl_rule_msg.configure(text="❌ Invalid executable format (must end with .exe).", text_color="#FF5252")

    def delete_rule(self, exec_name: str):
        if self.rule_controller.delete_rule(exec_name):
            self.refresh_rules_list()
            self.refresh_logs_list()

    # --- TAB 3: ACTIVITY LOGS ---
    def _setup_logs_tab(self):
        self.scroll_logs = ctk.CTkScrollableFrame(self.tab_logs, label_text="Logged Active Usage (activity_logs.json)")
        self.scroll_logs.pack(fill="both", expand=True, padx=15, pady=15)
        self.refresh_logs_list()

    def refresh_logs_list(self):
        for widget in self.scroll_logs.winfo_children():
            widget.destroy()

        logs = self.quota_engine.activity_logs
        if not logs:
            ctk.CTkLabel(self.scroll_logs, text="No usage data recorded yet.").pack(pady=20)
            return

        for app, seconds in logs.items():
            row = ctk.CTkFrame(self.scroll_logs, fg_color="transparent")
            row.pack(fill="x", pady=4, padx=5)

            minutes = round(seconds / 60, 1)
            ctk.CTkLabel(row, text=f"• {app}", font=("Segoe UI", 13, "bold"), width=220, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=f"{seconds} seconds ({minutes} mins logged)", font=("Segoe UI", 12)).pack(side="left")

    # ==========================================
    # SYSTEM TRAY & NOTIFICATION LOGIC
    # ==========================================
    def _generate_tray_icon_image(self):
        """Generates a dynamic 64x64 shield image for the system tray icon."""
        image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        # Outer shield
        draw.polygon([(32, 4), (58, 16), (58, 42), (32, 60), (6, 42), (6, 16)], fill="#1E88E5")
        # Inner accent
        draw.polygon([(32, 12), (50, 21), (50, 40), (32, 53), (14, 40), (14, 21)], fill="#1565C0")
        return image

    def _setup_system_tray(self):
        menu = pystray.Menu(
            item("Show FocusGuard", self.show_from_tray, default=True),
            item("Toggle Monitoring", lambda: self.after(0, self.toggle_monitoring)),
            pystray.Menu.SEPARATOR,
            item("Exit FocusGuard", lambda: self.after(0, self.graceful_exit))
        )
        self.tray_icon = pystray.Icon(
            "FocusGuard", 
            self._generate_tray_icon_image(), 
            "FocusGuard - Background Active", 
            menu
        )
        # Run pystray in a daemon background thread
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def send_tray_notification(self, title: str, message: str):
        """Triggers a native Windows system tray balloon notification."""
        if self.tray_icon and self.tray_icon.has_notification:
            self.tray_icon.notify(message, title)

    def hide_to_tray(self):
        self.withdraw()
        self.send_tray_notification("FocusGuard Minimized", "FocusGuard is running in the background system tray.")

    def show_from_tray(self):
        self.deiconify()
        self.focus_force()

    # ==========================================
    # MONITORING & ENFORCEMENT LOOP
    # ==========================================
    def toggle_monitoring(self):
        if not self.is_monitoring:
            self.is_monitoring = True
            self.status_badge.configure(text="STATUS: ACTIVE", fg_color="#2E7D32")
            self.btn_toggle_monitor.configure(
                text="Stop Real-Time Monitoring", 
                fg_color="#C62828", 
                hover_color="#8E0000"
            )
            self.monitor_thread = threading.Thread(target=self._monitor_worker_loop, daemon=True)
            self.monitor_thread.start()
            self.send_tray_notification("Monitoring Started", "Active process window polling initiated.")
        else:
            self.is_monitoring = False
            self.status_badge.configure(text="STATUS: STOPPED", fg_color="#D32F2F")
            self.btn_toggle_monitor.configure(
                text="Start Real-Time Monitoring", 
                fg_color="#2E7D32", 
                hover_color="#1B5E20"
            )
            self.lbl_active_app.configure(text="System Idle / Unmonitored")
            self.lbl_app_metrics.configure(text="Category: None | Time Spent Today: 0s / Quota: 0m")
            self.send_tray_notification("Monitoring Stopped", "Process polling paused.")

    def _monitor_worker_loop(self):
        breached_apps_notified = set()

        while self.is_monitoring:
            exec_name, category, is_idle = self.poller.poll_cycle()

            if is_idle:
                self.after(0, lambda: self.lbl_active_app.configure(text="System Idle (>300s)"))
                self.after(0, lambda: self.lbl_app_metrics.configure(text="Tracking paused due to user inactivity."))
            else:
                self.quota_engine.log_activity(exec_name, 1)
                spent_sec = self.quota_engine.read_focus_duration(exec_name)
                rule = self.rule_controller.fetch_executable_rule(exec_name)
                quota_min = rule.get("quota_minutes", 0)
                quota_sec = quota_min * 60

                metrics_str = f"Category: {category} | Time Spent Today: {spent_sec}s / Quota: {quota_min}m ({quota_sec}s)"

                # Safe UI Thread Update
                self.after(0, lambda e=exec_name: self.lbl_active_app.configure(text=e))
                self.after(0, lambda m=metrics_str: self.lbl_app_metrics.configure(text=m))
                self.after(0, self.refresh_logs_list)

                # Quota Breach Check
                if self.quota_engine.compute_dynamic_quota_allowance(exec_name):
                    if exec_name not in breached_apps_notified:
                        breached_apps_notified.add(exec_name)
                        warning_title = f"⚠️ Quota Breach: {exec_name}"
                        warning_msg = f"Application '{exec_name}' exceeded daily limit ({quota_min}m). Initiating SIGTERM enforcement!"

                        self.send_tray_notification(warning_title, warning_msg)

                    self.enforcement.trigger_enforcement(exec_name)

            time.sleep(1)

    # ==========================================
    # CLEAN SHUTDOWN
    # ==========================================
    def graceful_exit(self):
        """Stops thread loops, removes system tray icon, and destroys Tkinter instance cleanly."""
        self.is_monitoring = False

        if self.tray_icon:
            self.tray_icon.stop()

        self.quit()
        self.destroy()


if __name__ == "__main__":
    app = FocusGuardGUI()
    app.mainloop()
