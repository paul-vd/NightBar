# NightBar ☕

A tiny macOS menu bar app that controls `caffeinate` for **overnight agent
runs**. It keeps the **system** awake so long-running Claude Code / agent
sessions keep going, while letting the **display sleep** — so nothing is forced
on all night and you avoid burn-in.

- **Active:** title shows `● Awake` (or `● 3h` with a timer)
- **Inactive:** title shows `○ Off`

## Exact commands the app runs

All defined at the top of [`nightbar.py`](nightbar.py):

| Action | Command |
|---|---|
| Keep awake, allow display sleep | `caffeinate -i -m` |
| Keep awake with a timer | `caffeinate -i -m -t <seconds>` |
| Sleep display now | `pmset displaysleepnow` |
| Detect power source | `pmset -g batt` |

### Why these flags

- `-i` — prevent **system** idle sleep. This is the whole point.
- `-m` — prevent **disk** idle sleep (harmless; helps sustained I/O overnight).
- **No `-d`** — `-d` prevents *display* sleep. We deliberately omit it so the
  screen can turn off.
- **No `-s`** — `-s` only keeps the system awake on AC power; on battery the
  Mac could sleep mid-run. We want it awake regardless, so we skip it. The app
  instead just *shows* your current power source in the menu.
- `-t <seconds>` — used only for the timed presets; caffeinate exits on its own
  when the timer elapses.

## Install

Requires macOS and Python 3.

```bash
cd NightBar
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python3 nightbar.py
```

A `○ Off` item appears in the menu bar. Click it:

- **Keep Mac Awake, Allow Display Sleep** — start (runs until stopped)
- **Start with Timer** → 1 hour / 4 hours / Until Stopped
- **Stop** — terminate caffeinate cleanly
- **Sleep Display Now** — turn the screen off immediately (caffeinate keeps running)
- **Launch at Login** — toggle a LaunchAgent
- **Quit** — quits the app (and stops caffeinate so nothing is orphaned)

The menu bar polls every few seconds, so if caffeinate exits for any reason the
title flips back to `○ Off` on its own.

### Debug mode

```bash
NIGHTBAR_DEBUG=1 python3 nightbar.py
```

Logs each command and state change to stderr.

## Notifications

Start/stop/failure notifications work when the app is bundled (see below). When
run as a plain script macOS may suppress them — that's expected and the app
still functions.

## Package as a normal .app (optional, no signing headaches)

```bash
pip install py2app
python3 setup.py py2app -A     # -A = alias/development build, fast, unsigned
open dist/NightBar.app
```

The `-A` build runs from your local files (no code signing required). For a
distributable bundle drop `-A`. Gatekeeper may still ask you to right-click →
Open the first time for an unsigned app.

## Launch at login

Use the **Launch at Login** menu toggle. It writes a LaunchAgent to
`~/Library/LaunchAgents/com.nightbar.keepawake.plist` and `launchctl load`s it
(and removes it when toggled off).

## Notes

- Starting twice is safe — it never spawns a duplicate caffeinate; it checks the
  tracked PID is alive first.
- Stopping when already stopped is a no-op.
- Quitting the app terminates caffeinate so you never leave an invisible process
  holding the Mac awake.
