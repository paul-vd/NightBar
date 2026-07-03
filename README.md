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

## Quick start

Requires macOS and Python 3. Uses a `Makefile` as the task runner (like
`package.json` scripts). Run `make` on its own to list every command.

```bash
make run     # run from source          (≈ npm run dev)
make build   # compile dist/NightBar.app (≈ npm run build)
make app     # build, then launch it
make dmg     # build a drag-to-Applications installer (dist/NightBar.dmg)
make clean   # remove build output
```

`make run` bootstraps everything on a fresh clone — it creates `.venv`,
installs dependencies, and launches. No manual venv steps needed.

<details>
<summary>Manual equivalent (no <code>make</code>)</summary>

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 nightbar.py
```
</details>

Once running, a `○ Off` item appears in the menu bar. Click it:

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
NIGHTBAR_DEBUG=1 make run
```

Logs each command and state change to stderr.

## Notifications

Start/stop/failure notifications work when the app is bundled (see below). When
run as a plain script macOS may suppress them — that's expected and the app
still functions.

## Package as a normal .app

```bash
make app     # builds a standalone dist/NightBar.app and launches it
```

Drag `dist/NightBar.app` to `/Applications` to launch it from Spotlight/Finder
like any other app.

## Build a drag-to-Applications installer (.dmg)

```bash
make dmg     # produces dist/NightBar.dmg
```

Open the `.dmg` and you get the familiar styled installer window — a curved
arrow pointing NightBar onto the **Applications** shortcut (big icons, custom
background). Attach `dist/NightBar.dmg` to a GitHub Release to give your team a
download link.

The styling step drives Finder via AppleScript. The first time you run
`make dmg`, macOS may ask for permission to control Finder — allow it. If it's
denied, the build still completes with a plain (unstyled) but fully working DMG.
To restyle the background/arrow, edit `assets/make_dmg_bg.py`
(`pip install pillow && python assets/make_dmg_bg.py`).

The bundle/DMG is **unsigned**, so on a *different* Mac Gatekeeper may block it
("damaged / unidentified developer") — right-click → Open the first time, or
build locally there with `make dmg`. A signed/notarized build that opens with a
plain double-click needs an Apple Developer ID (overkill for internal dev use).

## Change the app icon

The app icon lives at `assets/NightBar.icns` (committed, so builds just use it).
To use your own artwork, drop a **1024×1024 PNG** at `assets/NightBar.png` and run:

```bash
make icon    # PNG -> assets/NightBar.icns (uses built-in sips + iconutil)
make build   # rebuild the app with the new icon
```

The default icon is drawn by `assets/make_icon.py` (needs `pip install pillow`);
you only touch that if you want to tweak the generated artwork.

## Releasing (automated via release-please)

Releases are **not** cut on every merge. [release-please][rp] keeps a single
**Release PR** open that accumulates the next version bump and a `CHANGELOG.md`
entry, derived from [Conventional Commit][cc] messages on `main`:

1. **Merge PRs to `main`** using Conventional Commit titles (`feat: …`,
   `fix: …`, `docs: …`). release-please opens/updates a Release PR titled like
   *"chore(main): release 0.2.0"*.
2. **When you're ready to ship** → merge the Release PR. release-please creates
   the GitHub Release + tag and updates `CHANGELOG.md`.
3. A dependent macOS job then builds `NightBar.dmg` and **attaches it** to that
   release — all in `.github/workflows/release-please.yml`.

Version bumps follow the commits: `fix:` → patch, `feat:` → minor,
`feat!:`/`BREAKING CHANGE` → major. Download link for your team: **Releases**
tab or `github.com/paul-vd/NightBar/releases/latest`.

> Non-Conventional commits (and direct admin pushes) are ignored for
> versioning, so they won't appear in the changelog — route changes through PRs
> with Conventional titles.

> The CI runner has no GUI Finder session, so the attached DMG may be
> *unstyled* (functional drag-to-Applications, without the custom background).
> For the styled DMG, run `make dmg` locally and upload it to the release.

All GitHub Actions are **pinned to a commit SHA** (not a moving tag like `@v5`)
to prevent supply-chain tampering; the trailing `# vX.Y.Z` comment records the
readable version. To bump one, resolve the new tag to its SHA, e.g.
`gh api repos/actions/checkout/commits/v7 --jq .sha`.

[rp]: https://github.com/googleapis/release-please
[cc]: https://www.conventionalcommits.org/

## Contributing

`main` is protected: all changes go through a pull request that must pass CI
(`.github/workflows/ci.yml` builds the app on macOS). Outside contributors fork
the repo and open a PR; direct pushes to `main` are blocked.

```bash
# fork on GitHub, then:
git checkout -b fix/my-change
# ...edit, then:
make build          # sanity-check it bundles
git commit -am "fix: describe the change"   # Conventional Commit message
git push origin fix/my-change
# open a PR against paul-vd/NightBar
```

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
