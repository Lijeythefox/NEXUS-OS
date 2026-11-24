# NEXUS OS 2 roadmap

The full plan for NEXUS OS 2, from the first smooth desktop to a finished cyberdeck OS with offline AI.

- **What** each feature must do is in [`SPEC.md`](../SPEC.md). This file is **when** and **how**.
- Work happens **one phase at a time**. A phase is only finished when Elijah has tested it on real hardware and ticked its device checklist.
- Each phase gets its own step-by-step build plan in [`docs/superpowers/plans/`](superpowers/plans/) when it starts. The phase sections below are the brief for those plans.
- Where things stand today: [`PROGRESS.md`](../PROGRESS.md).

## Overview

| Phase | Name | Machine | Depends on | Status |
| --- | --- | --- | --- | --- |
| 1 | Smooth desktop | OptiPlex | none | **Built, needs device test** |
| 2 | NEXUS menu | OptiPlex | 1 | Not started |
| 3 | Themes | OptiPlex | 2 | Not started |
| 4 | Apps (and the Iris app) | OptiPlex | 2 | Installer built early; rest not started |
| 5 | Deck board: choose and bring up | Deck board on a desk | 1–4, board bought | Not started |
| 6 | Deck hardware features | Cyberdeck | 5, case built | Not started |
| 7 | Offline AI on the deck | Cyberdeck | 4, 5 | Not started |
| 8 | Polish, speed and the 2.0 release | Both | 1–7 | Not started |

Phases 3 and 4 can swap order if Elijah wants apps before themes: neither depends on the other.

```
 1 ──► 2 ──┬──► 3 ──┐
           └──► 4 ──┼──► 5 ──► 6 ──┐
                    │        └──► 7 ┼──► 8
                    └───────────────┘
```

## How every phase runs

The same loop, every time. It keeps mistakes small and makes sure nothing ships untested.

1. **Plan.** Claude reads `SPEC.md`, this roadmap and `PROGRESS.md`, writes the phase's build plan into `docs/superpowers/plans/YYYY-MM-DD-<phase>.md`, and Elijah reads it.
2. **Build on a branch.** All work happens on a branch called `phaseN-<name>`, never directly on `main`.
3. **Test first.** Anything with logic (scripts, the theme system, menus) gets an automatic test in `ci/tests.sh` that fails before the code is written.
4. **Check on GitHub.** Every push runs the **Check NEXUS OS** workflow (about 3 minutes): syntax of every file, unit tests, a clean install of every package, and Hyprland's own config check. It must be green before merging.
5. **Try it early.** Visual changes are also added to the browser simulator so Elijah can click around before any image exists.
6. **Merge and build.** Merging into `main` starts the image build (about 2 hours), then the VMware machine (about 15 minutes).
7. **Device test.** Elijah tries the image (VM first, then the real machine) and works through the phase's device checklist below.
8. **Fix and close.** Problems get fixed with a failing test first, then a new build. When the checklist is all ticked, `PROGRESS.md` is updated and the phase is closed.

### Definition of done (every phase)

- [ ] Every task in the phase is merged into `main`.
- [ ] The Check NEXUS OS workflow is green on `main`.
- [ ] The image builds, and the VM image builds.
- [ ] Every item in the phase's **device checklist** is ticked by Elijah on real hardware.
- [ ] `PROGRESS.md`, `docs/USER-GUIDE.md` and any affected doc are updated.
- [ ] No new hard-coded colours (all colours come from `theme.conf`).
- [ ] Nothing new depends on one board, except `config/board.conf`.
- [ ] Idle memory and boot time are no worse than the last phase (`nexus-bench`).

### Size guide

Effort is given as **S** (one session), **M** (2–3 sessions) or **L** (a week or more of sessions). A "session" is one sitting with Claude plus one image build.

---

## Phase 1: Smooth desktop (built, needs device test)

**Goal:** boot the OptiPlex straight into a locked, animated Hyprland desktop that feels smooth.

**What was built** (details in [ARCHITECTURE.md](ARCHITECTURE.md)):

- Armbian CLI image for `uefi-x86`, Debian 13, with only the Hyprland family from backports.
- Hyprland Lua config: gaps, rounded corners, blur, shadows, Omarchy-style animations, all SPEC shortcuts.
- Waybar top bar with NEXUS logo, five clickable workspace dots, clock, Bluetooth, network, volume, power.
- fuzzel launcher and small menu, mako notifications, SwayOSD pop-ups, foot terminal, Thunar, hyprlock, hypridle, screenshots.
- Tokyo Night theme through the template system; three generated wallpapers.
- Auto-login on screen 1, lock screen first, 3-failure safety stop.
- GitHub check workflow, image build, VMware machine build, browser simulator.

### Remaining work

| # | Task | Size |
| --- | --- | --- |
| 1.1 | Elijah boots the image on the OptiPlex and ticks the checklist below | S |
| 1.2 | Fix whatever the test finds (failing test first for each fix) | S–M |
| 1.3 | Record `nexus-bench` results in `PROGRESS.md` as the speed baseline | S |

### Device checklist

- [ ] Boots from USB (F12) and Armbian's first-run setup appears.
- [ ] After setup, the lock screen appears without typing anything else.
- [ ] Your password unlocks it; a wrong one shows a red border.
- [ ] Bar, wallpaper and animations appear. Opening and closing windows looks smooth (no stutter).
- [ ] Bar icons show as icons, not empty boxes.
- [ ] Workspace dots: click to switch; the one you are on is a wide pill.
- [ ] Super + Space, Super + Return, Super + W, Super + 1..5, Super + K work.
- [ ] Print takes a screenshot and a notification pops up.
- [ ] Volume keys show the pop-up and sound plays.
- [ ] Wired network connects by itself.
- [ ] Left alone: dims at 4 min, locks at 5, screen off at 6.
- [ ] Log out from the power menu returns to the lock screen.
- [ ] `nexus-bench`: under 12 s to the lock screen, under 700 MB idle memory.

**Done when:** all boxes ticked, baseline numbers recorded.

---

## Phase 2: NEXUS menu (M–L)

**Goal:** one menu (Super + Alt + Space, or the ◆ logo) that does every everyday setting, replacing the old Settings app. SPEC section: *NEXUS menu*.

### Design

- `nexus-menu` becomes a small menu engine: each menu is a plain text file in `overlay/usr/share/nexus/menu/`, one entry per line (`label | hint | command`), so menus can be read, tested and changed without touching code.
- All menus use fuzzel in list mode (same look as the launcher), work with keyboard, mouse and touch, and close with Escape. "‹ Back" is always first in a sub-menu.
- Every action calls a normal Linux tool underneath (`nmcli`, `bluetoothctl`, `wpctl`, `hyprctl`), so it can be tested on a PC without the menu.
- Settings the user changes are saved in `~/.config/nexus/settings.conf` (simple `key=value`), read by the scripts that need them.

### Tasks

| # | Task | Files | Size |
| --- | --- | --- | --- |
| 2.1 | Menu engine: reads menu files, shows them, runs the chosen command, handles Back and sub-menus. Tests: parsing, missing file, bad line, Back | `overlay/usr/local/bin/nexus-menu`, `overlay/usr/share/nexus/menu/*.menu`, `ci/tests.sh` | M |
| 2.2 | Settings store: `nexus-setting get/set KEY [VALUE]` with defaults in `/usr/share/nexus/default/settings.conf`. Tests: default, override, unknown key | `overlay/usr/local/bin/nexus-setting` | S |
| 2.3 | Wi-Fi: list networks with signal bars, tap to connect, ask for password (fuzzel password mode), forget, show connected one. Notification on success or failure | `overlay/usr/local/bin/nexus-wifi` | M |
| 2.4 | Bluetooth: power on/off, scan for 10 s, pair, connect, disconnect, forget; shows battery % where the device reports it | `overlay/usr/local/bin/nexus-bluetooth` | M |
| 2.5 | Sound: output and input picker, mute toggles; "Advanced" opens `pavucontrol` | `nexus-sound`, add `pavucontrol` to packages | S |
| 2.6 | Display: scale (100/125/150 %), "Advanced" opens `wdisplays` | `nexus-display`, add `wdisplays` | S |
| 2.7 | Idle and lock times: pick dim/lock/screen-off minutes, writes a user `hypridle.conf` and restarts hypridle | `nexus-idle` | S |
| 2.8 | Keyboard layout and time zone pickers (`hyprctl keyword`, `timedatectl`) | `nexus-keyboard`, `nexus-timezone` | S |
| 2.9 | Update: "Install updates now" opens a terminal running `apt` with clear messages; "NEXUS version" shows `/etc/nexus/version` | `nexus-update` | S |
| 2.10 | Tools: screenshot, colour picker (`hyprpicker`, backports), show shortcuts, restart the bar | menu file, add `hyprpicker` to backports list | S |
| 2.11 | Power sub-menu (reuse `nexus-power`) | menu file | S |
| 2.12 | Bar icons open the matching sub-menu (Wi-Fi icon → Wi-Fi, Bluetooth → Bluetooth) | `waybar/config.json` | S |
| 2.13 | Simulator: full menu behaviour matches the real one | simulator artifact | S |
| 2.14 | Docs: menu chapter in USER-GUIDE | `docs/USER-GUIDE.md` | S |
| 2.15 | Load the user's own `~/.config/hypr/bindings.lua` after the defaults, as `SPEC.md` says (phase 1 does not load it yet). Test: a user binding overrides a default | `overlay/usr/share/nexus/default/hypr/nexus.lua` | S |

The **Install** section of the menu comes in phase 4 (it needs the app lists).

### Device checklist

- [ ] Super + Alt + Space and the ◆ logo open the menu; Escape closes it.
- [ ] Wi-Fi: connect to a network with a password; wrong password gives a clear message; forget works.
- [ ] Bluetooth: pair an 8BitDo controller and headphones; reconnect after a restart.
- [ ] Sound: switch between speakers and headphones.
- [ ] Display scale changes and stays after a restart.
- [ ] Idle times change and are kept.
- [ ] Update runs and finishes without errors.
- [ ] Every entry works with only the mouse, and with only the keyboard.

### Risks

| Risk | Plan |
| --- | --- |
| fuzzel password entry shows text | Use fuzzel's password mode; test on device |
| Bluetooth pairing needs a PIN for some devices | Show the PIN in a notification; fall back to "open a terminal with bluetoothctl" |

---

## Phase 3: Themes (M)

**Goal:** the six themes from the SPEC, a picker, live switching in about a second, and low-effects mode. SPEC section: *Themes*.

### Tasks

| # | Task | Files | Size |
| --- | --- | --- | --- |
| 3.1 | Five more `theme.conf` files: Catppuccin Mocha, Gruvbox Dark, Nord, Everforest, Rosé Pine (all 28 colour keys each). Test: every theme renders with no unknown keys | `overlay/usr/share/nexus/themes/*/theme.conf` | S |
| 3.2 | Theme picker in the menu with a colour preview strip, and Super + Shift + Ctrl + Space | `nexus-menu`, menu file | S |
| 3.3 | Live reload of everything: Hyprland borders, Waybar, mako, fuzzel, foot (new and open windows), hyprlock, SwayOSD, wallpaper. Test: `nexus-theme set` changes every rendered file | `nexus-theme` | M |
| 3.4 | GTK apps follow: Adwaita-dark plus accent colour (`gtk.css` template); Chromium follows dark mode | template `gtk.css` | S |
| 3.5 | btop and VS Code colour files per theme (VS Code only once it is installed in phase 4) | templates | S |
| 3.6 | Low-effects mode: no blur, no shadows, shorter animations; switch in Style menu; saved in settings | `templates/hyprland.lua`, `nexus-setting` | S |
| 3.7 | Animations on/off and font size (Style menu) | same | S |
| 3.8 | Wallpaper picker (3 per theme), remembered per theme | `nexus-wallpaper` | S |
| 3.9 | Docs: how to make a seventh theme (DEVELOPER-GUIDE) | docs | S |

### Device checklist

- [ ] All six themes switch from the menu in about a second, with no logout.
- [ ] After switching, nothing still shows the old colours (bar, borders, notifications, terminal, lock screen, volume pop-up).
- [ ] Theme and wallpaper are kept after a restart.
- [ ] Low-effects mode visibly removes blur and shadows and feels at least as smooth.

---

## Phase 4: Apps and the Iris app (M)

**Goal:** every app in `apps.conf` installs and works through `nexus-apps`, and the Iris desktop companion runs on Hyprland with the home PC as a brain. SPEC sections: *Apps*, *Iris (AI)*, and [AI.md](AI.md).

**Already done early (25 Nov 2026):** the installer itself. `nexus-apps` (`overlay/usr/local/bin/nexus-apps`), the list (`overlay/usr/share/nexus/apps.conf`), the first-login picker, the menu entry, 16 tests, and a GitHub check that every Debian package in the list exists and that a Debian app, a zip download and an AppImage download really install. Apps are never in the image (decision D-25).

### Tasks

| # | Task | Files | Size |
| --- | --- | --- | --- |
| 4.1 | Device-test the installer on the OptiPlex: first-login picker, every ticked app, every extra | `apps.conf` fixes as found | M |
| 4.2 | Check every app opens from the launcher with a proper icon; fix desktop entries if not | `nexus-apps` | S |
| 4.3 | Chromium in Wayland mode by default (`/etc/chromium.d/nexus` flags) | overlay file, added to the `chromium` entry | S |
| 4.4 | `nexus-open` picks the installed apps (already points to the installer when missing) | `nexus-open` | S |
| 4.5 | ES-DE finds RetroArch and the ROMs folder | ES-DE settings in `apps.conf` setup step | S |
| 4.6 | SSH server switch in the menu | `nexus-ssh` | S |
| 4.7a | **In the Iris repo:** add `.github/workflows/build-linux.yml` building `.deb` packages for amd64 and arm64 and attaching them to each Iris release | `Lijeythefox/IRIS` | M |
| 4.7b | Iris entry in `apps.conf` installs that `.deb` plus what it needs (`gnome-keyring`, `libsecret-tools`); Iris's own updater off | `apps.conf` | S |
| 4.7c | Hyprland setup: window rules for Iris's overlay and panel (class names read from `hyprctl clients` on the device, pinned in a test); keys Super + I / Shift + I / Alt + I / Ctrl + I → `roamies --ask/--talk/--panel/--list`; Waybar `tray` module; start Iris from `nexus-autostart` when installed | `rules.lua`, `bindings.lua`, `keys.txt`, `waybar/config.json`, `nexus-autostart` | M |
| 4.7d | NEXUS menu › Setup › Iris: add the home PC's Ollama (`http://<name>:11434`) to Iris's server list, test the connection, "Start Iris at login" switch | `nexus-iris-setup`, menu file | S |
| 4.7e | Measure Iris's idle memory with `nexus-bench`; decide the login default | `PROGRESS.md` | S |
| 4.8 | Image size check: the build fails if the image grows past a set limit | `build.yml` | S |
| 4.9 | Docs: apps chapter, Iris setup | `USER-GUIDE.md`, `AI.md` | S |

### Device checklist

- [ ] After the first unlock (with internet), the app picker appears with your usual apps ticked.
- [ ] Go opens a terminal, asks for your password, installs, and a notification says what's ready.
- [ ] Every ticked app opens from the launcher (Super + Space).
- [ ] Super + Shift + B / C open Chromium and VS Code.
- [ ] NEXUS menu › Install apps: install Godot, Prism Launcher, Thonny, RetroArch and ES-DE; each opens. Remove one; it's gone.
- [ ] Minecraft (Prism) starts and you can join the Fabric server.
- [ ] A Pico shows up in Thonny; `mpremote` runs a file (after logging out and in once).
- [ ] With no internet at first login: a notification says to connect, and the picker appears at the next login.
- [ ] Iris's globe appears after unlocking; Super + I and Super + Shift + I work; it answers from a sign-in and from the home PC's Ollama. Full list: [AI.md § 7](AI.md#7-phase-checklists).
- [ ] `nexus-bench` idle memory still under 700 MB.

### Risks

| Risk | Plan |
| --- | --- |
| A project renames its release files, so the pattern stops matching | The installer says which app and where it looked; fix the pattern in `apps.conf` (no image rebuild needed if fixed on the device) |
| Some projects publish no fingerprint (GitLab, older GitHub files) | Downloaded over HTTPS only; the log says so (D-26) |
| Iris uses too much idle memory | Measure (4.7e); "Start Iris at login" switch, Super + I starts it on demand |
| Iris's overlay misbehaves under Hyprland (focus, stacking, transparency) | Window rules; fixes made in the Iris repo; needs device test |
| A Debian package name is wrong | The GitHub check dry-runs every Debian package in the list on each push |

---

## Phase 5: Deck board, choose and bring up (M–L)

**Goal:** pick the cyberdeck's board and get the same NEXUS desktop running on it, on a desk, before the case exists.

### 5A. Choose the board (decision gate)

The board must be bought before this phase starts. Elijah chose **"offline AI on the deck too"**, so the board must be able to run a small language model at a usable speed. The comparison and the reasoning are in [HARDWARE.md › Choosing the deck board](HARDWARE.md#3-choosing-the-deck-board).

Short version: an **RK3588 board** (built-in AI chip, about 6 TOPS) or a **Raspberry Pi 5 (8 GB)**, optionally with the AI HAT+ 2. The Radxa Zero 3W is too weak for offline AI.

### 5B. Bring-up tasks

| # | Task | Files | Size |
| --- | --- | --- | --- |
| 5.1 | Second build target: the build workflow builds a matrix of boards from `config/boards/*.conf` (OptiPlex stays). Each board gets its own image and VM/flash notes | `build.yml`, `config/boards/` | M |
| 5.2 | Board quirks file: anything one board needs (kernel branch, firmware, display settings) lives in `config/boards/<board>.conf` only | same | S |
| 5.3 | Automatic low-effects on ARM boards (set at first login from the board file) | `nexus-setting` defaults | S |
| 5.4 | Display: Waveshare 7" 1024×600 over HDMI; scale 1.0; bar and menus fit; touch input works as a pointer | `looknfeel.lua` per-board override | S |
| 5.5 | eMMC/NVMe install path (`armbian-install`) documented for the board | `docs/FLASHING.md` | S |
| 5.6 | Arm64 package check in the GitHub check (packages + config verify for arm64) | `check.yml` | S |
| 5.7 | Speed pass on the board: `nexus-bench`, trim services that only matter there | `customize-image.sh` | M |

### Device checklist (board on a desk, Waveshare screen)

- [ ] Image flashes and boots to the lock screen.
- [ ] Desktop is smooth in low-effects mode at 1024×600.
- [ ] Touch taps work as clicks.
- [ ] Wi-Fi and Bluetooth work.
- [ ] Sound through the screen's headphone jack.
- [ ] `nexus-bench`: under 30 s to the lock screen, under 600 MB idle memory.

---

## Phase 6: Deck hardware features (L)

**Goal:** everything that makes the deck a handheld: touch gestures, on-screen keyboard, controller as a mouse, lid sleep, battery, SD card, and the swappable modules including the breadboard module. SPEC sections: *Deck extras*, *Swappable modules*.

Needs: the case printed and the parts fitted (see [HARDWARE.md](HARDWARE.md)).

### Tasks

| # | Task | Files | Size |
| --- | --- | --- | --- |
| 6.1 | Touch: edge swipes (left/right = workspace, bottom = launcher) with `lisgd`; three-finger swipes on the trackpad/trackball if supported | `nexus-touch`, autostart | M |
| 6.2 | On-screen keyboard (`wvkbd`) themed from the theme; bar button and Super + Shift + K | `nexus-osk`, template | M |
| 6.3 | Controller mouse mode: port `pad.py` from `tactical-v1`; hold Select + Start 2 s; off inside games | `overlay/opt/nexus/lib/nexus/pad.py` | M |
| 6.4 | Pico lid sensor and battery: firmware in `pico/lid-sensor/` (already written); deck service reads it, lid closed = sleep, battery in the bar, warnings at 15 % and 5 % | `nexus-pico`, Waybar module | M |
| 6.5 | SD card: "Prepare SD card" in the menu (format, create `ROMs/ Files/ Minecraft/ models/`), mounted at `/mnt/sdcard` | `nexus-sdcard` | M |
| 6.6 | Module slots: detect what is in each slot; Setup › Modules shows it | `nexus-modules`, udev rule | M |
| 6.7 | Breadboard module support: connect pop-up (Thonny / terminal / flash `.uf2`), `BB` bar chip with each rail's voltage and current, over-current warning. Needs the module's helper-chip firmware (separate repo/folder) | `nexus-modules`, `pico/breadboard-helper/` | L |
| 6.8 | Battery profiles: plugged in = full effects, battery = low effects + dimmer, big warning at 10 % | `nexus-power-profile` | S |
| 6.9 | Docs: deck chapter in USER-GUIDE, wiring in HARDWARE | docs | S |

### Device checklist

- [ ] Swipes change workspace and open the launcher.
- [ ] On-screen keyboard types into the terminal and the lock screen.
- [ ] Controller mouse mode moves the pointer and clicks; turns itself off in a game.
- [ ] Closing the lid sleeps; opening it shows the lock screen.
- [ ] Battery shows in the bar and warns at 15 % and 5 %.
- [ ] Prepare SD card works; ES-DE finds ROMs there.
- [ ] Breadboard module: pop-up on insert; bar chip shows the right voltages (check with a multimeter); a deliberate short trips the fuse and shows the warning without crashing the deck.

---

## Phase 7: Offline AI on the deck (M–L)

**Goal:** the Iris app keeps working with no internet by using a small model running on the deck itself (Iris's Lite mode), and switches automatically between the home PC and the local model. Full design: [AI.md § 4](AI.md#4-offline-iris-on-the-deck-phase-7).

### Tasks

| # | Task | Files | Size |
| --- | --- | --- | --- |
| 7.1 | Local model server: `llama.cpp`'s `llama-server` on `127.0.0.1:8088` (OpenAI-compatible, so Iris can use it), at least 16k context, as a user service that only starts when needed and stops after 10 idle minutes. RKLLM only if llama.cpp is too slow | `nexus-ai-server`, systemd user unit | M |
| 7.2 | Model download from the menu (Setup › Iris › Offline model) to `/mnt/sdcard/models/`, with size and SHA-256 shown; nothing preinstalled | `nexus-ai-models`, `config/ai-models.txt` | M |
| 7.3 | Add "This deck" to Iris's server list with Lite mode on; `nexus-iris-brain` picks the home PC if it answers within 2 s, otherwise the deck's model, and shows a bar dot. If Iris's settings can't be changed safely from outside, make the change in the Iris repo instead | `nexus-iris-brain` | M |
| 7.4 | Pick the default model by testing on the board (tool use, 16k context, 5+ words a second) | `config/ai-models.txt`, `DECISIONS.md` D-22 | S |
| 7.5 | Limits: local AI refuses to start under 20 % battery and pauses when a game is fullscreen | `nexus-ai-server` | S |
| 7.6 | Benchmark: `nexus-bench --ai` prints tokens per second for the installed model | `nexus-bench` | S |

### Device checklist

- [ ] With Wi-Fi off, Super + I gets an answer from the deck's own model (Lite mode).
- [ ] At home, Iris switches back to the home PC by itself.
- [ ] Local model speed at least 5 words a second (target from AI.md).
- [ ] Desktop stays smooth while the model answers.
- [ ] Server stops by itself after 10 idle minutes (memory goes back down).

---

## Phase 8: Polish, speed and the 2.0 release (M)

**Goal:** meet every speed target on both machines, add the finishing touches, and publish NEXUS OS 2.0 as a GitHub release.

### Tasks

| # | Task | Size |
| --- | --- | --- |
| 8.1 | Speed pass against SPEC targets on both machines; fix the five slowest services | M |
| 8.2 | Image size pass: find what takes space (the first image was about 1.7 GB compressed) and remove what isn't needed | M |
| 8.3 | Quiet boot and a simple NEXUS logo splash (Plymouth) on the OptiPlex; skip on ARM if it slows boot | S |
| 8.4 | Minecraft tuning (Java flags, memory) and emulator tuning per board | S |
| 8.5 | First-boot welcome: a one-time window with the 6 most useful shortcuts | S |
| 8.6 | Full docs review: every doc matches the release | S |
| 8.7 | Tag `v2.0.0`: the build publishes images for every board to GitHub Releases | S |

### Release checklist

- [ ] All earlier phase checklists still pass on the release image (regression run).
- [ ] Speed targets met on both machines.
- [ ] Release notes written (what's new since tactical-v1).
- [ ] Images and checksums attached to the GitHub release.

---

## After 2.0 (ideas, not planned yet)

Ideas from [`SPEC.md`](../SPEC.md) conversations that are out of scope for 2.0. Each needs a SPEC change before it is planned:

- Project launcher (Super + P): open a folder from `~/Projects` in VS Code or Godot plus a terminal.
- Game mode: launching a game turns off animations and blur and hides the bar.
- Clipboard history (Super + V is taken by float; another key).
- Drop-down scratchpad terminal.
- Minecraft server status dot in the bar.
- Workspace overview (zoom out to see all workspaces).
- Night light on a schedule.
- `uwsm` session start (see [DECISIONS.md](DECISIONS.md) D-07).

## Open decisions that block phases

| Decision | Blocks | Where it's discussed |
| --- | --- | --- |
| Which deck board | Phase 5 | [HARDWARE.md](HARDWARE.md#3-choosing-the-deck-board) |
| Home PC's Ollama address for Iris (Tailscale name) | Phase 4.7d | [AI.md](AI.md) |
| Which offline model | Phase 7.2 | [AI.md](AI.md#which-model) |
| Breadboard module switch, knob and pogo connector part numbers | Phase 6.7 | [HARDWARE.md](HARDWARE.md#4-breadboard-module) |
| Keep `start-hyprland` or switch to `uwsm` | Nothing (can be any time) | [DECISIONS.md](DECISIONS.md) D-07 |
