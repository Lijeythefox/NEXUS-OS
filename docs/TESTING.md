# Testing NEXUS OS

NEXUS OS is tested in five layers, from fastest and cheapest to slowest and most real. Each layer catches problems the one before can't. A feature is only "done" after the last layer: Elijah on real hardware.

| # | Layer | Where | Time | Who | Catches |
| --- | --- | --- | --- | --- | --- |
| 1 | Static check | `ci/check-static.sh` | ~30 s | GitHub (and Claude locally) | Syntax errors, Windows line endings, logic bugs |
| 2 | Desktop check | `ci/desktop-check.sh` | ~3 min | GitHub | Bad package names, package clashes, Hyprland rejecting the config, missing commands |
| 3 | Simulator | Browser | Instant | Elijah | Look, feel, menus, flow |
| 4 | Virtual machine | VMware on Windows | ~15 min setup | Elijah | Boot, first-run, auto-login, lock screen, most of the desktop |
| 5 | Real hardware | OptiPlex, later the deck | ~10 min flash | Elijah | Real graphics and smoothness, speed, sound, Wi-Fi, Bluetooth, deck hardware |

## 1. Static check

Runs on every push to any branch (job **static** in `.github/workflows/check.yml`, in a `debian:trixie` container).

`ci/check-static.sh` checks:

- every bash script: `bash -n` (syntax) and `shellcheck -S error` (real mistakes);
- every Python file: parses it;
- every Lua file under `overlay/`: `luac -p`;
- every JSON file under `overlay/` and `config/`: `jq`;
- no Windows line endings in `overlay/ ci/ config/ userpatches/ tools/`;
- then runs the unit tests in `ci/tests.sh`.

Run it yourself from the repo root (needs Linux or a container): `bash ci/check-static.sh`.

### Unit tests (`ci/tests.sh`)

There are 34 tests covering:

| Area | What's tested |
| --- | --- |
| `nexus-theme` (6) | Every template fills with no `{{` left; unknown placeholder fails and names it; `#rrggbb` / `rrggbb` / `r, g, b` forms; a bad colour is refused; `ensure` renders the default theme on first run; `ensure` keeps the saved theme |
| `nexus-session` (4) | Gives up after 3 fast failures and shows the log path; a long run resets the count; output goes to `~/.cache/nexus/hyprland.log`; says so when Hyprland isn't installed |
| `nexus-getty` (4) | Root while first-run setup is pending; the desktop user after; plain prompt when auto-login is off; never root once setup is done |
| `nexus-apps` (16) | The real app list has no mistakes; unknown settings and empty apps refused; PC-only apps hidden and refused on ARM; Elijah's ticked list; installed marks; one apt call without recommended extras; repositories added first; SSH switched off; pipx as the user; unknown app named; right release file per machine; test releases skipped; missing file names the app; wrong fingerprint refused and deleted |
| `nexus-ws-state` (4) | Active, occupied, empty; valid output when Hyprland doesn't answer |

How to write one: [DEVELOPER-GUIDE.md § 4](DEVELOPER-GUIDE.md#4-writing-tests).

## 2. Desktop check

Job **desktop** in `check.yml`. Runs `ci/desktop-check.sh` in a clean `debian:trixie` Docker container:

1. Adds trixie-backports and installs both package lists with `tools/install-packages.sh` (exactly what the image does). Fails on a wrong name or a clash.
2. Renders the default theme into a test home folder.
3. Runs `Hyprland --verify-config` on the NEXUS config with `NEXUS_STRICT=1` (no safety net, so any Lua error fails). Must print `config ok`.
4. **Self-test:** runs the same check on a deliberately broken config and makes sure it *fails*, so a check that always passes can't slip through.
5. `foot --check-config` and `fuzzel --check-config` on the rendered theme files.
6. Checks every command the desktop needs exists (waybar, mako, swayosd-server and -client, swaybg, hyprlock, hypridle, grim, slurp, wl-copy, notify-send, brightnessctl, playerctl, thunar, start-hyprland, hyprctl, Xwayland, wpctl, nmcli, jq, pkill).

7. **App installer:** `nexus-apps check` on the real list, then a dry run (`apt-get install -s`) of every Debian package in it, so a wrong name fails the check. Then it really installs terminal tools, Godot (zip) and Prism Launcher (AppImage) to prove the install paths work; that part depends on GitHub, so a failure is reported but doesn't block.

What it **can't** check: whether the desktop actually draws, animations, real hardware. That's layers 3 to 5. (A screenless desktop run in the check was tried and dropped; see [DECISIONS.md](DECISIONS.md) D-05.)

## 3. Simulator

The **NEXUS OS 2 Simulator** artifact (<https://claude.ai/artifact/MpYe89VXg6JFHRpzAhPhq8>) runs the desktop's look and behaviour in a browser tab: boot text, first-run questions, lock screen, tiling windows, workspace dots, launcher, menus, shortcuts, notifications, screenshots, themes.

Use it to:

- try a new phase's look before any image is built;
- decide on changes ("make the gaps bigger", "different menu order");
- learn the shortcuts.

It is a model, not the real thing: it can't show real speed, real apps or hardware.

## 4. Virtual machine

Full steps: [TEST-IN-VM.md](TEST-IN-VM.md). Short version:

1. Install VMware Workstation Pro (free for personal use).
2. GitHub → Actions → latest **Make VMware disk** run → download the zip → unzip.
3. Double-click the `.vmx` file, press Power on.

What works in the VM: boot, Armbian first-run, auto-login, lock screen, desktop, launcher, windows, workspaces, shortcuts, screenshots, notifications, wired network, theme files.

What doesn't prove anything in the VM: smoothness (virtual graphics), sleep, brightness, Bluetooth, Wi-Fi, real boot time.

## 5. Real hardware

### 5.1 OptiPlex (phases 1–4, 8)

Install: [INSTALL-OPTIPLEX.md](INSTALL-OPTIPLEX.md). Each phase has a **device checklist** in [ROADMAP.md](ROADMAP.md). Tick every box, then report.

### 5.2 Deck board (phases 5–8)

Flashing: [FLASHING.md](FLASHING.md) (written in phase 5 for the chosen board).

### 5.3 Regression run (before every release, and phase 8)

Run **every** earlier phase's device checklist again on the newest image. Things that worked before must still work.

### 5.4 Speed measurement

```
nexus-bench
```

Prints time from power on to the lock screen, idle memory after login, and the five slowest services. Run it three times after a fresh boot (leave the computer alone for 1 minute after unlocking) and record the middle result in `PROGRESS.md`.

| Target | OptiPlex | Deck board |
| --- | --- | --- |
| Power on → lock screen (after firmware) | under 12 s | under 30 s |
| Idle memory after login | under 700 MB | under 600 MB |
| Terminal opens | under 0.3 s | under 0.5 s |

Smoothness has no number, so judge it: open and close 10 windows quickly, switch workspaces back and forth, drag a floating window in circles. Any visible stutter = report it.

## Reporting a problem

Send Claude:

1. **What you did** (the steps) and **what you expected**.
2. **What happened** instead. A phone photo of the screen is great.
3. The output of these, run in a terminal (Super + Return), photo or copy-paste:
   ```
   nexus-bench
   hyprctl configerrors
   tail -n 60 ~/.cache/nexus/hyprland.log
   ```
4. If the desktop didn't start at all: press Ctrl + Alt + F2, log in, and run
   `cat ~/.cache/nexus/hyprland.log ~/.cache/nexus/hyprland.log.old`
5. Which image: `cat /etc/nexus/version`.

Claude then: writes a failing test that shows the problem (when it can be tested without hardware), fixes it, updates `PROGRESS.md`, and gives you a new checklist.

## Test status tracking

`PROGRESS.md` has a **Needs device test** list. Every feature is on it until Elijah confirms it on real hardware; then it moves to **Confirmed on device** with the date and image version.
