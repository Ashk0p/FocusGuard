import sys
import os
import time

# Ensure src directory is on sys.path for direct module imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rules.rule_controller import RuleController
from monitor.poller import ActiveWindowPoller
from quota.quota_engine import QuotaEngine
from enforcement.enforcement_controller import EnforcementController


class FocusGuardApp:
    """Core application orchestrator coordinating UC1, UC2, and UC3 workflows."""
    def __init__(self):
        self.rule_controller = RuleController()
        self.poller = ActiveWindowPoller(self.rule_controller)
        self.quota_engine = QuotaEngine(self.rule_controller)
        self.enforcement_controller = EnforcementController()

    def run_rule_configuration_phase(self):
        """UC1: Configure Rules & Quotas"""
        print("\n--- [PHASE 1] Rule Configuration (UC1) ---")
        targets = [
            ("chrome.exe", "Distracting", 1),   # 1 minute quota for demonstration
            ("discord.exe", "Distracting", 30),
            ("code.exe", "Productive", 480)
        ]
        
        for exec_name, category, quota in targets:
            success = self.rule_controller.validate_and_save_rule(exec_name, category, quota)
            status = "Saved" if success else "Failed"
            print(f" -> Rule Setup: {exec_name} | Category: {category} | Quota: {quota}m [{status}]")

    def run_monitoring_phase(self, cycles=3):
        """UC2: Active Window Polling & Logging"""
        print("\n--- [PHASE 2] Active Window Polling (UC2) ---")
        
        for cycle in range(1, cycles + 1):
            exec_name, category, is_idle = self.poller.poll_cycle()
            
            if is_idle:
                print(f" [Cycle {cycle}] User Idle > 300s -> Pausing logging timer.")
            else:
                # Log 20 seconds of activity per polling interval
                self.quota_engine.log_activity(exec_name, duration_sec=20)
                spent = self.quota_engine.read_focus_duration(exec_name)
                print(f" [Cycle {cycle}] Active App: '{exec_name}' ({category}) | Logged: {spent}s")
            
            time.sleep(0.4)

    def run_enforcement_phase(self, target_app="chrome.exe"):
        """UC3: Quota Evaluation & Process Signal Enforcement"""
        print("\n--- [PHASE 3] Quota Evaluation & Enforcement (UC3) ---")
        
        # Simulate additional usage pushing past the 60s quota limit
        print(f" -> Injecting focus activity to trigger quota boundary for '{target_app}'...")
        self.quota_engine.log_activity(target_app, duration_sec=45)
        
        total_time = self.quota_engine.read_focus_duration(target_app)
        quota_breached = self.quota_engine.compute_dynamic_quota_allowance(target_app)
        
        print(f" -> Evaluated '{target_app}': Total Usage = {total_time}s | Limit Breached = {quota_breached}")
        
        if quota_breached:
            self.enforcement_controller.trigger_enforcement(target_app)
        else:
            print(f" -> Usage within limits. Continuing standard monitoring.")


def main():
    print("==================================================")
    print("        FocusGuard - Core System Engine           ")
    print("==================================================")
    
    app = FocusGuardApp()
    app.run_rule_configuration_phase()
    app.run_monitoring_phase(cycles=3)
    app.run_enforcement_phase("chrome.exe")
    
    print("\n==================================================")
    print("        FocusGuard Pipeline Completed             ")
    print("==================================================")


if __name__ == "__main__":
    main()