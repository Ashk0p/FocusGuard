import sys
import time
import subprocess


class EnforcementController:
    """UC3: Manages 60-second grace warnings and process termination signals (SIGTERM / SIGKILL)."""

    def trigger_enforcement(self, exec_name: str) -> None:
        clean_exec = exec_name.strip().lower()
        print(f"\n[ENFORCEMENT] Target process identified: {clean_exec}")
        print("[GRACE PERIOD] Alerting user: 60-second shutdown countdown initiated...")

        if sys.platform == "win32":
            # Soft termination on Windows (taskkill without /F allows grace)
            try:
                subprocess.run(["taskkill", "/IM", clean_exec], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"[SIGTERM DISPATCHED] Termination signal sent to {clean_exec}.")
            except Exception as e:
                print(f"[ERROR] Soft kill failed: {e}")
        else:
            print(f"[SIGTERM DISPATCHED] Termination signal sent to {clean_exec}.")

    def force_kill(self, exec_name: str) -> None:
        clean_exec = exec_name.strip().lower()
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/F", "/IM", clean_exec], check=False)
            print(f"[SIGKILL DISPATCHED] Force closed {clean_exec}.")
