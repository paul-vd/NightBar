#!/usr/bin/env python3
"""
NightBar — a tiny macOS menu bar app to control `caffeinate` for overnight
agent runs.

Goal: keep the *system* awake so long-running Claude Code / agent sessions
keep going, while still allowing the *display* to sleep (avoids OLED/backlight
burn-in on an unattended machine overnight).

The exact commands this app runs are defined as constants below so they are
easy to read and audit.
"""

import os
import shutil
import subprocess
import sys
import time

import rumps

# ---------------------------------------------------------------------------
# Commands — kept as constants so the exact behavior is visible and auditable.
# ---------------------------------------------------------------------------
#
# caffeinate flag choice (see `man caffeinate`):
#   -i  Prevent the *system* from idle sleeping.        <- what we want
#   -m  Prevent the disk from idle sleeping.            <- harmless, helps long I/O
#   -s  Prevent system sleep only while on AC power.    <- NOT used (would let the
#                                                          Mac sleep on battery mid-run)
#   -d  Prevent the *display* from sleeping.            <- deliberately NOT used
#                                                          (we WANT the display to sleep)
#   -t <sec>  Run for a fixed number of seconds, then exit.
#
# So "keep system awake, allow display to sleep" == `caffeinate -i -m`.
# For a timed run we append `-t <seconds>`.
CAFFEINATE = shutil.which("caffeinate") or "/usr/bin/caffeinate"
CAFFEINATE_BASE = [CAFFEINATE, "-i", "-m"]

# Immediately turn the display off without affecting the running caffeinate.
PMSET = shutil.which("pmset") or "/usr/bin/pmset"
DISPLAY_SLEEP_CMD = [PMSET, "displaysleepnow"]

# Power-source detection (nice-to-have): `pmset -g batt` reports AC vs battery.
POWER_QUERY_CMD = [PMSET, "-g", "batt"]

# How often (seconds) the menu bar refreshes its state.
POLL_INTERVAL = 5

# Preset durations, in seconds. None == run until manually stopped.
PRESETS = {
    "1 hour": 3600,
    "4 hours": 4 * 3600,
    "Until Stopped": None,
}

# Launch-at-login LaunchAgent.
LAUNCH_AGENT_LABEL = "com.nightbar.keepawake"
LAUNCH_AGENT_PATH = os.path.expanduser(
    f"~/Library/LaunchAgents/{LAUNCH_AGENT_LABEL}.plist"
)

DEBUG = os.environ.get("NIGHTBAR_DEBUG") == "1"


def log(*args):
    if DEBUG:
        print("[nightbar]", *args, file=sys.stderr, flush=True)


class NightBar(rumps.App):
    def __init__(self):
        super().__init__("NightBar", title="○ Off", quit_button=None)

        self.proc = None            # subprocess.Popen for caffeinate, or None
        self.end_time = None        # epoch seconds when a timed run ends, or None

        # Build the menu once; we mutate item titles/state on refresh.
        self.status_item = rumps.MenuItem("Inactive")
        self.status_item.set_callback(None)  # non-clickable status line

        self.start_item = rumps.MenuItem(
            "Keep Mac Awake, Allow Display Sleep", callback=self.start_until_stopped
        )

        preset_menu = rumps.MenuItem("Start with Timer")
        for label, seconds in PRESETS.items():
            preset_menu.add(
                rumps.MenuItem(label, callback=self._make_preset_cb(seconds))
            )

        self.stop_item = rumps.MenuItem("Stop", callback=self.stop)
        self.sleep_display_item = rumps.MenuItem(
            "Sleep Display Now", callback=self.sleep_display
        )
        self.login_item = rumps.MenuItem(
            "Launch at Login", callback=self.toggle_login
        )

        self.menu = [
            self.status_item,
            None,
            self.start_item,
            preset_menu,
            self.stop_item,
            None,
            self.sleep_display_item,
            None,
            self.login_item,
            None,
            rumps.MenuItem("Quit", callback=self.quit),
        ]

        self.refresh(None)  # initial paint
        rumps.Timer(self.refresh, POLL_INTERVAL).start()

    # -- state helpers ------------------------------------------------------

    def is_active(self):
        """True if our caffeinate process exists and is still running."""
        if self.proc is None:
            return False
        return self.proc.poll() is None  # poll() returns None while alive

    def remaining_seconds(self):
        if self.end_time is None:
            return None
        return max(0, int(self.end_time - time.time()))

    @staticmethod
    def _fmt_short(seconds):
        """Compact title label: '3h', '45m', or '<1m'."""
        if seconds >= 3600:
            return f"{round(seconds / 3600)}h"
        if seconds >= 60:
            return f"{round(seconds / 60)}m"
        return "<1m"

    # -- actions ------------------------------------------------------------

    def start(self, duration=None):
        """Start caffeinate. No-op (and no duplicate process) if already active."""
        if self.is_active():
            log("start ignored — already active")
            return

        cmd = list(CAFFEINATE_BASE)
        if duration is not None:
            cmd += ["-t", str(int(duration))]

        log("running:", " ".join(cmd))
        try:
            self.proc = subprocess.Popen(cmd)
        except OSError as e:
            self.proc = None
            self.end_time = None
            self._notify("NightBar", "Failed to start", str(e))
            return

        self.end_time = (time.time() + duration) if duration else None
        self.refresh(None)

        if duration:
            self._notify(
                "NightBar", "Keeping Mac awake",
                f"Display may sleep · {self._fmt_short(duration)} timer · pid {self.proc.pid}",
            )
        else:
            self._notify(
                "NightBar", "Keeping Mac awake",
                f"Display may sleep · until stopped · pid {self.proc.pid}",
            )

    def start_until_stopped(self, _):
        self.start(duration=None)

    def _make_preset_cb(self, seconds):
        return lambda _: self.start(duration=seconds)

    def stop(self, _):
        """Terminate caffeinate. No-op if not running."""
        if not self.is_active():
            log("stop ignored — not active")
            self.proc = None
            self.end_time = None
            self.refresh(None)
            return

        pid = self.proc.pid
        log("terminating pid", pid)
        self.proc.terminate()
        try:
            self.proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self.proc.kill()  # last resort
        self.proc = None
        self.end_time = None
        self.refresh(None)
        self._notify("NightBar", "Stopped", f"caffeinate {pid} terminated")

    def sleep_display(self, _):
        """Turn the display off now. Does NOT touch the caffeinate session."""
        log("running:", " ".join(DISPLAY_SLEEP_CMD))
        try:
            subprocess.run(DISPLAY_SLEEP_CMD, check=True)
        except (OSError, subprocess.CalledProcessError) as e:
            self._notify("NightBar", "Sleep display failed", str(e))

    def toggle_login(self, _):
        if os.path.exists(LAUNCH_AGENT_PATH):
            self._uninstall_login_agent()
        else:
            self._install_login_agent()
        self.refresh(None)

    def quit(self, _):
        # Leave caffeinate running? No — quitting the controller should stop it,
        # otherwise an orphaned process keeps the Mac awake with no UI to stop it.
        if self.is_active():
            self.proc.terminate()
        rumps.quit_application()

    # -- refresh / polling --------------------------------------------------

    def refresh(self, _):
        """Recompute UI from real process state. Runs on the poll timer."""
        was_tracking = self.proc is not None
        active = self.is_active()

        # Detect unexpected exit: we had a process, it's gone, and it wasn't a
        # timed run that reached zero on purpose.
        if was_tracking and not active:
            remaining = self.remaining_seconds()
            expected = remaining is not None and remaining <= 0
            log("caffeinate exited", "(timer done)" if expected else "(unexpected)")
            if not expected:
                self._notify("NightBar", "caffeinate exited", "Mac may now sleep")
            self.proc = None
            self.end_time = None
            active = False

        if active:
            remaining = self.remaining_seconds()
            if remaining is not None:
                self.title = f"● {self._fmt_short(remaining)}"
                self.status_item.title = (
                    f"Active — pid {self.proc.pid} — {self._fmt_short(remaining)} remaining"
                )
            else:
                self.title = "● Awake"
                self.status_item.title = f"Active — pid {self.proc.pid}"
        else:
            self.title = "○ Off"
            self.status_item.title = f"Inactive — {self._power_source()}"

        # Enable/disable actions to match state.
        self.start_item.set_callback(None if active else self.start_until_stopped)
        self.stop_item.set_callback(self.stop if active else None)
        self.login_item.state = os.path.exists(LAUNCH_AGENT_PATH)

    # -- misc ---------------------------------------------------------------

    def _power_source(self):
        """'AC power' or 'battery' — best effort, never raises."""
        try:
            out = subprocess.run(
                POWER_QUERY_CMD, capture_output=True, text=True, timeout=2
            ).stdout
            return "AC power" if "AC Power" in out else "battery"
        except (OSError, subprocess.SubprocessError):
            return "power: unknown"

    def _notify(self, title, subtitle, message):
        """Desktop notification; silently ignored if unavailable (unsigned run)."""
        try:
            rumps.notification(title, subtitle, message)
        except Exception as e:  # notifications need a bundled/signed app
            log("notification unavailable:", e)

    def _install_login_agent(self):
        python = sys.executable
        script = os.path.abspath(__file__)
        plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>{LAUNCH_AGENT_LABEL}</string>
  <key>ProgramArguments</key>
  <array>
    <string>{python}</string>
    <string>{script}</string>
  </array>
  <key>RunAtLoad</key><true/>
</dict>
</plist>
"""
        os.makedirs(os.path.dirname(LAUNCH_AGENT_PATH), exist_ok=True)
        with open(LAUNCH_AGENT_PATH, "w") as f:
            f.write(plist)
        subprocess.run(["launchctl", "load", LAUNCH_AGENT_PATH])
        self._notify("NightBar", "Launch at Login", "Enabled")

    def _uninstall_login_agent(self):
        subprocess.run(["launchctl", "unload", LAUNCH_AGENT_PATH])
        try:
            os.remove(LAUNCH_AGENT_PATH)
        except OSError:
            pass
        self._notify("NightBar", "Launch at Login", "Disabled")


if __name__ == "__main__":
    NightBar().run()
