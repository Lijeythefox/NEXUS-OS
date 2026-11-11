# NEXUS OS Progress

## Current phase

**NEXUS OS 2, Phase 1: smooth desktop on the OptiPlex.** Built and pushed. Waiting for the GitHub image build and Elijah's first test on the OptiPlex 3060.

The old tactical version (XFCE, HUD, Settings app) and its progress notes are on the `tactical-v1` branch.

## What phase 1 contains

- **Base:** Armbian `v26.5.1` CLI image (no Armbian desktop), Debian 13 trixie, `BOARD=uefi-x86`.
- **Desktop:** Hyprland 0.55.2 from Debian backports, with a Lua config. Tiling, gaps, rounded corners, blur, shadows, Omarchy-style animations (windows pop in, workspaces slide, menus fade).
- **Top bar (Waybar):** NEXUS logo (opens the menu), five clickable workspace dots, clock, Bluetooth, network, volume, power.
- **Launcher and menus (fuzzel):** Super + Space for apps. Super + Alt + Space for a small NEXUS menu (Apps, Shortcuts, Next wallpaper, Screenshot, Power). The full menu is phase 2.
- **Also:** notifications (mako), volume/brightness pop-up (SwayOSD), terminal (foot), files (Thunar), lock screen (hyprlock), idle dim/lock/screen-off (hypridle), screenshots, three generated wallpapers.
- **Theme:** Tokyo Night. Every colour comes from `overlay/usr/share/nexus/themes/tokyo-night/theme.conf` through templates in `overlay/usr/share/nexus/templates/`.
- **All shortcuts from `SPEC.md`.** Ones for apps that arrive later (browser, VS Code, games, on-screen keyboard) show a short "arrives in phase N" notification.
- **Start-up:** after Armbian's first-run setup, the desktop user is logged in automatically on the first screen and the desktop starts locked. If the desktop fails to start 3 times in a row it stops trying and leaves a text prompt with the log location, so the machine can't get stuck in a loop.
- **Speed work:** no login manager, apt "recommended" extras off, printing/Avahi/ModemManager/SSH server off, automatic updates held back for the first 10 minutes after boot. `nexus-bench` prints boot time and memory use.

## Checked on GitHub (not on hardware)

The **Check NEXUS OS** workflow runs on every push (about 3 minutes):

- All 48 packages install in a clean Debian 13 (43 from stable, 5 from backports). The reported `libxkbcommon` clash did not happen.
- `Hyprland --verify-config` on the NEXUS config: `config ok` (real Hyprland 0.55.2). A deliberately broken config is rejected, so the check can fail.
- foot and fuzzel accept their generated configs. Every command the desktop calls exists.
- 18 unit tests: theme rendering (missing colours and bad colours are refused), session start and the 3-failures guard, auto-login rules, workspace dot states.

## Needs device test

Nothing below could be run without a screen and GPU. Everything visual is untested.

- [ ] Image boots on the OptiPlex and Armbian's first-run setup appears
- [ ] After setup, the lock screen appears without typing `exit`
- [ ] Password unlocks the lock screen
- [ ] Bar, wallpaper and animations appear and feel smooth
- [ ] Workspace dots: click to switch, active one is a wide pill
- [ ] Bar icons show as icons, not empty boxes (font check)
- [ ] Super + Space, Super + Return, Super + W, Super + 1..5 and the other shortcuts
- [ ] Notifications (try a screenshot: Print key)
- [ ] Volume keys show the pop-up and sound works
- [ ] Network: wired connection comes up by itself
- [ ] Idle: dims at 4 min, locks at 5 min, screen off at 6 min
- [ ] `nexus-bench` numbers against the targets (under 12 s to lock screen, under 700 MB)

## Decisions made while building

- **`start-hyprland` instead of `uwsm`.** `SPEC.md` says the session starts through `uwsm`. Phase 1 uses Hyprland's own `start-hyprland` launcher because it has fewer parts that can't be tested without hardware. Needs Elijah's OK to keep, or switch back later.
- **Workspace dots are NEXUS's own.** Waybar's built-in Hyprland workspace buttons send old-style commands that Hyprland refuses when it uses a Lua config, so clicks would do nothing. The dots are five small custom bar items, refreshed by Hyprland events (no background program).
- **No screenless desktop test on GitHub.** Hyprland needs a real display device and login session there. The check verifies packages and configs instead.
- **Quiet boot and boot splash are left for phase 6**, so boot messages stay visible while early images are being debugged.
- **Support packages** not named in `SPEC.md` but needed for the listed pieces to work: sound (pipewire), graphics drivers (mesa), fonts, icons, `dbus-user-session`, `polkitd`, `network-manager`, `wpasupplicant`, `jq`, `procps`. Full list: `config/packages.txt`.

## Known gaps (later phases)

- No browser, VS Code, Godot, Minecraft or emulators yet (phase 4).
- Wi-Fi and Bluetooth have no menu yet (phase 2). Wired network works by itself. Wi-Fi from a terminal: `nmcli device wifi connect "NAME" password "PASSWORD"`.
- One theme (phase 3 adds five more and the theme picker).
- Deck features (touch, on-screen keyboard, controller, Pico, breadboard module) are phase 5.
- The Pico firmware is in `pico/lid-sensor/`. The Python helpers for it are still on `tactical-v1`.

## If the desktop does not start

- Press **Ctrl + Alt + F2** for a text login. Log in with your user name and password.
- The log is `~/.cache/nexus/hyprland.log`. Show the end of it with `tail -n 40 ~/.cache/nexus/hyprland.log` and send Claude a photo.
- To stop the desktop starting by itself: `touch ~/.config/nexus/no-desktop`. Delete that file to turn it back on.
