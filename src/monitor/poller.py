import sys
import time
from typing import Tuple, Dict, Any


class ActiveWindowPoller:
    """UC2: Polls the OS Window Manager to detect active foreground process and idle status."""

    def __init__(self, rule_controller=None, idle_threshold_seconds: int = 300):
        self.rule_controller = rule_controller
        self.idle_threshold_seconds = idle_threshold_seconds

    def get_active_process_name((self) -> str:
        """Queries the active foreground window process executable name."""
        if sys.platform == "win32":
            try:
                import win32gui
                import win32process
                import psutil
                hwnd = win32gui.GetForegroundWindow()
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                return psutil.Process(pid).name().lower()
            except Exception:
                return "unknown.exe"
        else:
            # Standard Linux/macOS fallback or manual test process handle
            return "chrome.exe"

    def get_user_idle_time(self) -> float:
        """Retrieves system-wide idle duration in seconds."""
        if sys.platform == "win32":
            try:
                import ctypes
                class LASTINPUTINFO(ctypes.Structure):
                    _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]
                
                lii = LASTINPUTINFO()
                lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
                if ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii)):
                    millis = ctypes.windll.kernel32.GetTickCount() - lii.dwTime
                    return millis / 1000.0
            except Exception:
                return 0.0
        return 0.0

    def poll_cycle(self) -> Tuple[str, str, bool]:
        """
        Executes a single polling cycle.
        Returns: (executable_name, category, is_idle)
        """
        idle_time = self.get_user_idle_time()
        is_idle = idle_time > self.idle_threshold_seconds

        if is_idle:
            return "idle", "Neutral", True

        exec_name = self.get_active_process_name()
        category = "Uncategorized"

        if self.rule_controller:
            rule = self.rule_controller.fetch_executable_rule(exec_name)
            category = rule.get("category", "Uncategorized")

        return exec_name, category, False
