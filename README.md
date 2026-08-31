# Productive OS - Focus & Enforcement System
# FocusGuard 

**FocusGuard** is a lightweight, system-level process monitoring and productivity enforcement tool. It tracks foreground window activity, calculates dynamic usage quotas against daily limits and task deadlines, and enforces soft (SIGTERM) or hard (SIGKILL) process terminations when distraction budgets are exceeded.

---

##  System Architecture & Workflow

FocusGuard operates through three core sequence flows:
1. **Rule Configuration**: Setup application monitoring rules, execution paths, and daily time quotas via the UI dashboard.
2. **Active Window Monitoring**: Polls the OS window manager in real-time intervals to track active process names, categorize app usage, and increment activity logs.
3. **Quota Evaluation & Enforcement**: Evaluates cumulative distraction time against task urgency deadlines. If quota thresholds are breached, a grace period countdown triggers before escalating signal termination to the OS kernel.

---

## 🛠️ Project Structure

```text
FocusGuard/
├── docs/                 # UML Sequence Diagrams (.mdj, PNGs) and architecture specs
├── src/
│   ├── ui/               # UI Dashboard & Configuration panels
│   ├── rules/            # Rule database & category filters
│   ├── monitor/          # OS Foreground window poller
│   ├── quota/            # Dynamic quota calculator & deadline registry
│   └── enforcement/      # Process signal dispatcher (SIGTERM/SIGKILL)
├── .gitignore            # Excluded build artifacts and logs
├── LICENSE               # License information
└── README.md             # Project documentation
