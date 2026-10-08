import sys
import subprocess
import psutil


class EnforcementController:
    """UC3: Manages process termination signals (SIGTERM / SIGKILL) across process trees."""

    def force_kill_process(self, exec_name: str) -> bool:
        """Force kills all running instances and sub-processes of the target executable."""
        clean_exec = exec_name.strip().lower()
        killed_any = False

        # Method 1: Kill via psutil process iteration
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'] and proc.info['name'].lower() == clean_exec:
                    # Kill child processes first
                    parent = psutil.Process(proc.info['pid'])
                    for child in parent.children(recursive=True):
                        child.kill()
                    parent.kill()
                    killed_any = True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        # Method 2: Fallback Windows taskkill with Force (/F) and Tree (/T) flags
        if sys.platform == "win32":
            try:
                result = subprocess.run(
                    ["taskkill", "/F", "/T", "/IM", clean_exec],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                if result.returncode == 0:
                    killed_any = True
            except Exception:
                pass

        return killed_any

    def trigger_enforcement(self, exec_name: str) -> bool:
        """Executes process termination."""
        return self.force_kill_process(exec_name)
