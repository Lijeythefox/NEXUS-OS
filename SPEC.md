# NEXUS OS Spec

## Overview

NEXUS OS is a stable, themed Linux desktop for the folding cyberdeck. It is flashed as one ready-made image and built so the same recipe works if the board is upgraded later.

- **Target board now:** Radxa Zero 3W (RK3566, 8GB RAM, 64GB eMMC, no GPIO).
- **Upgrade path:** Raspberry Pi 5 or an RK3588 board (e.g. Orange Pi 5), by changing one line in the build recipe.
- **Screen and input:** Waveshare 7" 1024x600 capacitive touchscreen (H) over HDMI, plus a mini keyboard + trackpad and a Bluetooth controller, all used together.
- **Priorities, in order:** normal computer use, coding and tinkering, retro gaming, local AI (via a home machine).
- **Unplugged:** performance over battery life.
- **Install style:** plug and play. Flash, boot, log in, and everything is already set up.

## Base system and build pipeline

The OS is Armbian (Debian stable underneath) with an XFCE desktop, customised and built automatically on GitHub. Armbian supports the Zero 3W, the Pi 4/5 and RK3588 boards from the same build framework, so upgrading is a one-line change.

Why XFCE: it is light enough to stay quick on the RK3566, does a Windows-style taskbar and start menu out of the box, and themes heavily. KDE Plasma looks slicker but is noticeably slower on this board.

How the image gets made:

1. A GitHub repository (`nexus-os`) holds the recipe: a board setting, a package list, theme files, configs and a setup script.
2. Pushing a change triggers GitHub Actions, which runs the Armbian build in the cloud for free.
3. The finished `.img` file appears under the repo's **Actions** tab (or **Releases**) to download on Windows.
4. Flash it to a spare micro SD card with balenaEtcher or Raspberry Pi Imager, boot the deck from it, then copy the system onto the eMMC with `armbian-install` (the eMMC is soldered on, so Windows can't write to it directly). Step by step in `docs/FLASHING.md`.

Repository layout:

| Path | What it holds |
| --- | --- |
| `config/board.conf` | The one line that picks the board, e.g. `BOARD=radxa-zero3` |
| `config/packages.txt` | Every app to preinstall |
| `userpatches/customize-image.sh` | Script that runs inside the image during the build |
| `overlay/` | Files copied straight into the image (themes, configs, sounds, wallpapers) |
| `.github/workflows/build.yml` | The GitHub Actions job that builds the image |

Switching boards later = edit `config/board.conf`, push, download the new image. Files on the micro SD carry over untouched.

## Look and feel

Military / tactical HUD in one of five switchable colour presets on near-black (default: Amber), thin grid lines, monospace type, every screen from boot to desktop in the same style.

| Element | Spec |
| --- | --- |
| Colours | Set by the active colour preset (see Colour presets below) |
| Font | Share Tech Mono for UI and HUD, JetBrains Mono for terminal |
| Boot animation | Custom Plymouth theme: grid sweep, callsign fades in, "SYSTEM ONLINE" progress bar |
| Login screen | LightDM, themed: grid wallpaper, callsign header, password box styled as an access terminal |
| Desktop | Grid/topographic wallpaper, preset-coloured icons, square window corners, preset-coloured title bars |
| Terminal | Follows the active colour preset |
| Sounds | Tactical sound theme: short click on menu open, beep on notification, two-tone alert on low battery, startup chirp after login |
| Callsign | Shown on boot animation, login screen and HUD; set in one file, `/etc/nexus/callsign` (callsign still to be decided) |

All theme files live in `overlay/usr/share/` in the repo, so changing a colour means editing one file and rebuilding.

## Colour presets

Five presets, picked in Settings > Personalization. Switching one recolours everything at once: HUD widgets, taskbar, start menu, windows, terminal, icons, wallpaper tint, login screen and boot animation (boot animation updates from the next restart).

| Preset | Style | Background | Primary | Secondary | Grid | Alert |
| --- | --- | --- | --- | --- | --- | --- |
| Amber (default) | Warm tactical HUD, orange glow, rounded panels | `#0B0D08` | `#FFB000` | `#556B2F` olive | `#2A2210` | `#FF3B30` |
| Green | Phosphor wireframe, thin vector lines, old radar terminal | `#050A05` | `#39FF6A` | `#1FAF4B` | `#12301A` | `#FFB000` |
| Red | Threat radar, sweeping scope, sharp critical-mode look | `#0D0505` | `#FF2A2A` | `#B31212` | `#3A0E0E` | `#FFD60A` |
| Blue | Holographic sci-fi, glowing rings, cyan on navy | `#04101A` | `#2EC5FF` | `#0A6CFF` | `#0E2A3D` | `#FF4D4D` |
| Pink / Purple | Neon synthwave, magenta lines with violet accents | `#0E0612` | `#FF3EC8` | `#9B4DFF` | `#2C1235` | `#FFD60A` |

Each preset is one file in the repo, `overlay/usr/share/nexus/presets/<name>.conf`, holding those five colours plus a wallpaper and sound-pack choice. Adding a sixth preset later = copy a file, change the colours, rebuild. No colour is ever hard-coded anywhere else.

## Desktop and controls

A Windows-style desktop that works equally well with touch, keyboard/trackpad and controller.

- **Taskbar and start menu:** XFCE panel along the bottom, Whisker Menu as the start menu, open apps shown on the taskbar, tray on the right.
- **HUD widgets:** Conky widgets for battery and charging, CPU temp and usage, Wi-Fi and Bluetooth, and clock/date/weather. Each widget is its own file in `~/.config/conky/`, so any one can be turned on or off, moved, or set always-on-top.
- **On-screen keyboard:** Onboard, off by default, with a keyboard button on the taskbar to bring it up.
- **Controller as mouse:** AntiMicroX runs in the background. Hold Select + Start for 2 seconds to toggle mouse mode (left stick moves, A clicks, B right-clicks). In games, mouse mode is off.
- **Touch:** tap to click, long-press to right-click, larger touch targets on the panel and menus.
- **Lid sleep:** folding the screen arm closed puts it to sleep; opening it wakes it to the themed lock screen. Needs a magnet (hall) sensor in the hinge read by a small Raspberry Pi Pico over USB, since the Zero 3W has no GPIO. The same Pico also reads the battery voltage (the Zero 3W can't measure it), which feeds the battery widget, battery % and the low-battery alert. See Known limits.

Keyboard shortcuts:

| Shortcut | Action |
| --- | --- |
| Super | Open start menu |
| Super + I | Open Settings |
| Super + A | Open Quick Settings |
| Super + H | Show/hide the HUD widgets |
| Super + G | Launch the game launcher |
| Super + T | Terminal |
| Super + K | Toggle on-screen keyboard |
| Super + L | Lock |
| Print Screen | Screenshot |
| Super + Shift + S | Area screenshot |

## Settings app

One Settings app laid out like Windows 11: a sidebar of categories on the left, pages on the right, a search box at the top, all drawn in the active colour preset. It replaces XFCE's scattered settings windows, so nothing ever needs a terminal.

- **Open it:** Super + I, or the gear in the start menu.
- **Quick Settings:** Super + A, or click the Wi-Fi/volume/battery icons on the taskbar. A Windows 11-style pop-up with tiles for Wi-Fi, Bluetooth, hotspot, VPN, on-screen keyboard, controller mouse mode and HUD on/off, plus volume and brightness sliders and a colour-preset picker.
- **Built as:** a Python + GTK app in the repo at `overlay/opt/nexus/settings/`, launched by `/usr/local/bin/nexus-settings`. Each page is a front end for the normal Linux tool underneath (NetworkManager, BlueZ, PipeWire, xrandr, xfconf, Conky configs, Timeshift), so settings stay compatible with the rest of the system.
- **Touch and controller:** large rows and toggles, fully usable by finger or with the controller in mouse mode.

| Category | Pages and options |
| --- | --- |
| System | Display (resolution, scale, rotation, brightness, night light), Sound (output/input device, volume, test speakers), Notifications (on/off, do not disturb), Power & battery (battery %, sleep timer, lid close action, performance mode), Storage (eMMC and micro SD usage, cleanup), About (callsign, board, OS version) |
| Bluetooth & devices | Bluetooth (pair, connect, forget), Controller (pair, test buttons, mouse-mode combo, stick sensitivity), Keyboard (layout, repeat speed, shortcuts editor), Mouse & trackpad (speed, tap to click, scroll direction, natural scrolling), Touchscreen (calibrate, long-press time) |
| Network & internet | Wi-Fi (scan, connect, saved networks), Hotspot (saved phone hotspots, auto-connect), VPN (Tailscale on/off, sign in, devices), Network shares (saved Windows shares), Airplane mode |
| Personalization | Colour preset (five tiles with a live preview), Wallpaper, HUD widgets (pick which show, position, size, always-on-top), Taskbar (icon size, pinned apps, auto-hide), Start menu (pinned apps), Lock screen and login look, Boot animation (on/off), Sound theme (tactical / quiet / off), Fonts and text size |
| Apps | Installed apps (open, uninstall), Default apps (browser, video player, text editor), Startup apps (on/off) |
| Accounts | Password, Callsign, Auto-lock time |
| Time & language | Time zone, 12/24-hour clock, date format, weather location |
| Gaming | Game launcher folder (`/mnt/sdcard/ROMs/`), Emulator performance mode, Controller layout per system, Minecraft memory limit |
| Accessibility | Text size, high-contrast preset, on-screen keyboard always available, reduce animations |
| Privacy & security | SSH access to the deck (on/off), Firewall (on/off), Location for weather (on/off) |
| Update & backup | Security updates status, Check for updates, Snapshots (take now, list, restore), Rebuild/flash guide link |

Brightness depends on the Waveshare 7" (H) accepting brightness control from software. If it doesn't, the slider is hidden and the screen's own buttons are used instead. Needs a device test.

## Apps

Everything below is preinstalled in the image.

| Category | App | Notes |
| --- | --- | --- |
| Browser | Chromium | Best hardware acceleration on ARM |
| Video | FreeTube + mpv | Smoother YouTube than the browser on this board (hardware decoding) |
| Chat | Legcord | Discord client that runs on ARM; web Discord in Chromium as backup |
| Office | LibreOffice | Docs, spreadsheets, slides |
| Files | Thunar | Network shares built in |
| Code editor | VS Code (ARM64) | Python and general coding |
| Python | Python 3, pip, venv | |
| Pico | Thonny, mpremote, picotool | Flash and program the Pico over USB |
| Terminal | xfce4-terminal + OpenSSH | SSH into the Minecraft server and other machines |
| Game launcher | ES-DE (EmulationStation Desktop Edition) | Opened from the desktop like any app, controller-friendly |
| Emulators | RetroArch (NES, SNES, GB/GBA, Mega Drive, MAME, Neo Geo, PS1, N64), PPSSPP (PSP), Flycast (Dreamcast) | ES-DE picks the right one per system |
| Minecraft | Prism Launcher + Java 21 | Fabric with Sodium and other performance mods |
| AI | Open WebUI in Chromium, pinned as an app | Talks to a bigger model (e.g. Ollama) on the home PC |
| Snapshots | Timeshift | See Storage, updates and backups |
| Remote desktop | Remmina | See Networking |
| VPN | Tailscale | See Networking |

## Networking

Tailscale ties it together: once the home PC, the Minecraft server and the deck are on it, everything below works the same at home or on a phone hotspot, with no port forwarding.

| Feature | How |
| --- | --- |
| Phone hotspot | Built-in Wi-Fi manager; saved hotspot connects automatically |
| VPN home | Tailscale on the deck, home PC and Minecraft server |
| Shared folders | Thunar opens Windows shares (`smb://<pc-name>/<share>`), bookmarked in the sidebar |
| Remote desktop | Remmina over RDP if the PC runs Windows Pro; RustDesk if it runs Windows Home (Home can't host RDP) |
| AI | Open WebUI points at the home PC's Tailscale address, so it works away from home too |
| Deck file share | The deck shares its micro SD `ROMs` folder over the network, so games can be dropped in from Windows |

## Storage, updates and backups

The OS lives on the internal eMMC; personal files live on the micro SD, so reflashing or upgrading the board never touches them.

| Location | Contents |
| --- | --- |
| Internal eMMC (64GB) | OS and apps |
| `/mnt/sdcard/ROMs/` | Games, one folder per system (`snes`, `psx`, `psp`…) as ES-DE expects |
| `/mnt/sdcard/Files/` | Documents, downloads, screenshots (linked into the home folder) |
| `/mnt/sdcard/Minecraft/` | Prism Launcher instances and worlds |
| `/mnt/sdcard/Snapshots/` | Timeshift system snapshots |

The micro SD is formatted ext4 (Linux format) so snapshots work; files get on and off it over the network share or USB.

- **Updates:** stable only. Security updates install automatically; kernel and board firmware are frozen and only change when the image is rebuilt on purpose.
- **Backups:** Timeshift takes a full system snapshot daily (keeps 5) and before any manual update. Restore from the Timeshift app, or from a terminal if the desktop won't start.

## Known limits on the Zero 3W

Most of the spec runs fine on the Zero 3W; these are the parts it will struggle with, and what a stronger board changes. Figures are approximate and need testing on the real board.

| Want | On the Zero 3W | After upgrading (Pi 5 / RK3588) |
| --- | --- | --- |
| Smooth YouTube | Fine in FreeTube/mpv up to 720p–1080p; choppy in the browser | Smooth in the browser too |
| Retro up to PS1, arcade | Full speed | Full speed |
| N64, PSP | Many games playable, some slow | Most games full speed |
| Dreamcast | Some lighter games only | Most games playable |
| Minecraft Java | Needs testing: the GPU driver may lack the OpenGL version modern Minecraft wants; if it runs, expect low settings and short render distance | Playable on low–medium, especially RK3588 |
| Instant sleep on lid close | Needs the hinge sensor + Pico, and Rockchip sleep is unreliable; fallback is screen off + low-power mode | Better sleep support on Pi 5 |
| Desktop speed | Usable with XFCE; heavy multitasking will lag | Snappy |

## Open decisions

- [x] Name the OS: NEXUS OS
- [ ] Pick the callsign
- [ ] Re-source the Radxa Zero 3W (8GB/64GB) or choose the upgrade board now
- [ ] Check whether the home PC runs Windows Home or Pro (decides Remmina vs RustDesk)
- [ ] Pick the AI model and set up Ollama on the home PC
- [ ] Add the hinge magnet sensor + Pico to the case and interconnect board design
