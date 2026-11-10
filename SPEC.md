# NEXUS OS 2 Spec

The old tactical NEXUS OS (XFCE, Conky HUD, Windows-style Settings app, neon presets) is kept on the `tactical-v1` branch. This spec replaces it completely.

## Overview

NEXUS OS 2 is a fast, minimal, smooth Linux desktop in the style of Omarchy, filled with Elijah's own tools instead of Omarchy's web-developer kit.

- **Feel:** every window, workspace and pop-up glides or fades. Nothing pops in. Nothing stutters.
- **Look:** clean and calm. Flat dark themes, soft rounded corners, thin borders, gaps between windows, one accent colour. No neon, no grids, no HUD.
- **Speed first:** small install, few background services, fast boot straight to the lock screen.
- **Machines:** Dell OptiPlex 3060 SFF now (`BOARD=uefi-x86`). The cyberdeck board later (Pi 4/5, RK3566 or RK3588) by changing `config/board.conf`. Nothing may depend on one board except that file.
- **Priorities, in order:** smooth everyday use, coding and making (Godot, Pico, Python), gaming (Minecraft, retro), AI on the home PC.

## Base system and build pipeline

Unchanged from v1 except the desktop:

- Armbian build framework pinned to `v26.5.1`, Debian 13 "trixie", mainline kernel (`BRANCH=current`).
- Built with **no Armbian desktop** (`BUILD_DESKTOP=no`). Our setup script installs only what NEXUS needs.
- Built only on GitHub Actions. Never locally. The `.img.xz` is downloaded from the Actions tab (or Releases for `v*` tags).
- Debian **trixie-backports** is added, but only the Hyprland family is installed from it (`apt install -t trixie-backports ...`). Everything else comes from plain Debian stable. No testing or unstable repos.
- Hyprland in backports is 0.55.x. The config is written in **Lua** (`hyprland.lua`), because 0.57 removed the old `.conf` format and backports will move up.

### Build check before the long build

A quick job (about 10 minutes) runs before the image build and stops it early if anything is wrong:

1. Starts a clean Debian trixie container (amd64, plus arm64 under emulation) and installs the full package list exactly as the image will. Catches missing packages and the reported `libxkbcommon` version clash.
2. Runs Hyprland's config check on the NEXUS default config (`Hyprland --verify-config`, or the equivalent for the installed version).
3. Checks every shell, Python and JSON file for typos (shellcheck, `python3 -m py_compile`, `jq`).
4. Renders every theme and checks that no template placeholder is left over.

### Repository layout

v2 lives at the repo root. The `prototype/` folder and its workflow are removed from `main` (they stay on `tactical-v1`). Useful prototype code (Pico, battery, controller helper) is moved across.

| Path | What it holds |
| --- | --- |
| `config/board.conf` | Board and kernel branch, e.g. `BOARD=uefi-x86` |
| `config/packages.txt` | Debian stable packages to preinstall |
| `config/packages-backports.txt` | Packages installed from trixie-backports (Hyprland family only) |
| `config/downloads.txt` | Pinned downloads (Godot, Prism, ES-DE, emulator cores), with an `amd64` and `arm64` link per line |
| `config/install-menu.txt` | Apps offered in the NEXUS menu's Install list, with which machine types they support |
| `userpatches/customize-image.sh` | Runs inside the image during the build |
| `overlay/` | Files copied straight into the image |
| `overlay/usr/share/nexus/default/` | NEXUS default configs (Hyprland, Waybar, fuzzel, mako, foot, hypridle, hyprlock). Never edited by the user |
| `overlay/usr/share/nexus/themes/<name>/` | One folder per theme |
| `overlay/usr/share/nexus/templates/` | Config templates that themes are poured into |
| `overlay/usr/local/bin/nexus-*` | NEXUS commands |
| `overlay/opt/nexus/lib/nexus/` | Shared Python code (Pico, battery, controller) |
| `overlay/etc/skel/.config/` | Starter user configs that load the defaults, so user edits never get overwritten |
| `pico/lid-sensor/` | Pico firmware for the hinge sensor and battery voltage |
| `tools/` | Build helpers (download fetcher, wallpaper generator) |
| `.github/workflows/build.yml` | Build check + image build |

## Desktop

| Part | Tool | Notes |
| --- | --- | --- |
| Window manager | Hyprland (backports) | Tiling, animations, rounded corners, gaps |
| Session start | Auto-login on the first screen (tty1) starts Hyprland through `uwsm`; Hyprland locks itself with hyprlock as its first action | No login manager program, so less to load. Disk is not encrypted, so this is the only password prompt |
| Top bar | Waybar (stable) | Thin, top edge, see layout below |
| App launcher | fuzzel (stable) | Pops up in the centre, type to search, works by touch |
| NEXUS menu | `nexus-menu` script using fuzzel | See below |
| Notifications | mako (stable) | Top-right, slide in, auto-hide |
| Volume / brightness pop-up | SwayOSD (stable) | Centre-bottom |
| Lock screen | hyprlock (backports) | Blurred wallpaper, clock, password box |
| Idle | hypridle (backports) | Dim at 4 min, lock at 5 min, screen off at 6 min, sleep never on the OptiPlex. Times change in the NEXUS menu |
| Wallpaper | swaybg (stable) | One per theme, cycle with a shortcut |
| Terminal | foot (stable) | Very light and fast to open |
| Files | Thunar | Already proven in v1 |
| Password prompts | hyprpolkitagent (backports) | |
| Screen sharing / file pickers | xdg-desktop-portal-hyprland (backports) + xdg-desktop-portal-gtk | |
| Screenshots | grim + slurp + wl-clipboard | Saved to `~/Pictures/Screenshots` and copied |
| Old X11 apps | XWayland | Needed for Minecraft, Thonny and a few others |

### Top bar layout

Left: NEXUS logo (click = NEXUS menu), workspace dots 1-5 (tap to switch).
Centre: clock and date (click = calendar pop-up).
Right: on-screen keyboard button (deck only), controller mouse mode indicator (only when on), Bluetooth, Wi-Fi, volume, battery (deck only), power button.

Every icon is at least 32 px tall to touch. Icons come from Font Awesome (`fonts-font-awesome`). Text is JetBrains Mono.

### Animations

Matched to Omarchy's feel, set in `overlay/usr/share/nexus/default/hypr/looknfeel.lua`:

- Windows open with a short pop-in from 90 % size plus fade, close with fade out. About 200 ms.
- Workspaces slide sideways.
- Fuzzel, mako and the NEXUS menu fade in.
- Easing curves: Omarchy-style ease-out (`0.23, 1, 0.32, 1`) for movement, near-linear for fades.
- Rounded corners 8 px, gaps 5 px inside / 10 px outside, 2 px border in the theme accent on the focused window.
- Blur behind the bar, launcher and notifications, and soft shadows, on the OptiPlex.

**Low-effects mode** (automatic on ARM boards, switchable in the NEXUS menu): blur and shadows off, animations kept but shortened. This keeps it smooth on a weak GPU.

## Keyboard shortcuts

Omarchy-style. `Super` is the Windows key.

| Shortcut | Action |
| --- | --- |
| Super + Space | App launcher |
| Super + Alt + Space | NEXUS menu |
| Super + K | Show all shortcuts |
| Super + Return | Terminal |
| Super + Shift + B | Browser |
| Super + Shift + F | Files |
| Super + Shift + C | VS Code |
| Super + G | Games (ES-DE) |
| Super + W | Close window |
| Super + F | Fullscreen |
| Super + V | Float / unfloat window |
| Super + J | Flip split direction |
| Super + arrow keys | Move focus |
| Super + Shift + arrow keys | Swap windows |
| Super + 1..5 | Go to workspace |
| Super + Shift + 1..5 | Send window to workspace |
| Super + Escape | Power menu (lock, sleep, restart, shut down, log out) |
| Super + Ctrl + Space | Next wallpaper |
| Super + Shift + Ctrl + Space | Theme picker |
| Super + Shift + K | On-screen keyboard |
| Print | Screenshot of the whole screen |
| Shift + Print | Screenshot of an area |
| Volume / brightness keys | Change level, SwayOSD shows it |

Shortcuts live in `overlay/usr/share/nexus/default/hypr/bindings.lua`. Users add their own in `~/.config/hypr/bindings.lua`, which loads after the defaults.

## NEXUS menu

One keyboard- and touch-friendly menu replaces the old Settings app. Built as `overlay/usr/local/bin/nexus-menu` on top of fuzzel, so it looks like the launcher. Each entry runs a normal Linux tool underneath.

| Section | Entries |
| --- | --- |
| Apps | Opens the app launcher |
| Style | Theme (picker with colour preview), Wallpaper (next / pick), Font size, Low-effects mode on/off, Animations on/off |
| Setup | Wi-Fi (`nexus-wifi`: list networks, tap to connect, password prompt, using `nmcli`), Bluetooth (`nexus-bluetooth`: scan, pair, connect, forget, using `bluetoothctl`), Sound (`pavucontrol`), Display (`wdisplays`), Idle and lock times, Keyboard layout, Time zone |
| Install | Install or remove the optional apps in `config/install-menu.txt` (only those that support this machine are shown) |
| Update | Install updates now (`apt` with a terminal showing progress), Show NEXUS version |
| Tools | Screenshot, Colour picker (hyprpicker, backports), Show shortcuts, Restart the bar |
| Power | Lock, Sleep, Restart, Shut down, Log out |

## Themes

Six themes, picked from the NEXUS menu or Super + Shift + Ctrl + Space. **Tokyo Night** is the default.

| Theme | Feel |
| --- | --- |
| Tokyo Night (default) | Deep navy, soft blue and purple |
| Catppuccin Mocha | Warm dark, pastel accents |
| Gruvbox Dark | Retro brown and orange |
| Nord | Cool grey-blue |
| Everforest | Muted green |
| Rosé Pine | Dusky purple and rose |

How it works:

- Each theme is one folder, `overlay/usr/share/nexus/themes/<name>/`, holding `theme.conf` (named colours: `bg`, `surface`, `fg`, `muted`, `accent`, `accent2`, `urgent`, plus `color0`..`color15` for the terminal) and its wallpapers.
- Wallpapers are **generated during the build** from the theme's colours by `tools/make-wallpapers.py` (soft gradients and simple shapes, two or three per theme). No downloaded images, so no licence problems.
- Templates in `overlay/usr/share/nexus/templates/` hold every themed config with placeholders like `{{accent}}`. `nexus-theme set <name>` fills them in, writes the results to `~/.config/nexus/current/`, and reloads Hyprland, Waybar, mako, foot, fuzzel, hyprlock, SwayOSD, btop and VS Code's colour theme. Switching takes about a second with no logout.
- GTK apps follow with Adwaita-dark plus the accent colour. Chromium follows the system dark mode.
- No colour is typed anywhere except a `theme.conf`. Adding a seventh theme = copy a folder, change the colours, push.

## Apps

### Preinstalled

| Use | App | Source |
| --- | --- | --- |
| Browser | Chromium (Wayland mode) | Debian |
| Code | VS Code | Microsoft's repo |
| Game dev | Godot 4 | Official build, pinned in `downloads.txt` |
| Pico | Thonny, mpremote, picotool | Debian |
| Python | python3, pip, venv, pipx | Debian |
| Minecraft | Prism Launcher + Java 21 | Official AppImage (unpacked) + Debian |
| Retro games | ES-DE + RetroArch + cores | Official AppImage + Debian + libretro builds |
| VPN | Tailscale | Tailscale's repo |
| Remote shell | OpenSSH client and server (server off by default) | Debian |
| AI | "Iris" shortcut: Open WebUI in a Chromium app window, address set in the NEXUS menu | Built in |
| Terminal tools | btop, fastfetch, lazygit, git, ripgrep, fd-find, bat, fzf, curl | Debian |
| Everyday | Thunar, imv (pictures), mpv (video and music), Evince (PDF), Mousepad (notes), gnome-calculator | Debian |

### Install menu (one tap, not in the base image)

| App | Machines |
| --- | --- |
| KiCad | All |
| Arduino IDE 2 | PC only (no official ARM build) |
| Bambu Studio | PC only (no official ARM build) |
| LibreOffice | All |
| FreeTube | All |
| Legcord (Discord) | All |
| Remmina (remote desktop) | All |
| Timeshift (snapshots) | All |
| Samba share for the `ROMs` folder | All |

## Speed targets

Measured with `systemd-analyze` and `free -m`, and reported by `nexus-bench` (prints boot time, idle memory and the five slowest services).

| | OptiPlex 3060 | ARM deck board |
| --- | --- | --- |
| Power on to lock screen (after firmware) | under 12 s | under 30 s |
| Idle memory after login | under 700 MB | under 600 MB |
| Terminal opens | under 0.3 s | under 0.5 s |

How:

- No login manager, no XFCE, no Conky, no Python daemons running all the time (the Pico helper only runs on the deck).
- Services switched off by default: printing (CUPS), Avahi, ModemManager, Armbian's motd and first-run extras that aren't needed, apt timers during the first 10 minutes after boot. SSH server off until turned on in the menu.
- Compressed RAM swap (zram) on.
- Quiet boot: no scrolling text. A small NEXUS logo splash (Plymouth, simple theme) on the OptiPlex; skipped on ARM if it slows boot.
- Waybar modules update on events where possible instead of polling; anything polled is 5 s or slower.

## Deck extras

Built into the image, switched on only when `BOARD` is not `uefi-x86`:

- **Touch:** Hyprland handles taps and scrolling. Swipe in from the left/right screen edge to change workspace and from the bottom edge to open the launcher, using `lisgd` (Debian). Three-finger trackpad swipe also changes workspace (built into Hyprland).
- **On-screen keyboard:** `wvkbd` (Debian), toggled by the bar button or Super + Shift + K, themed from the active theme.
- **Controller mouse mode:** the v1 helper `nexus-pad` (moved to `overlay/opt/nexus/lib/nexus/pad.py`). Hold Select + Start for 2 seconds. Left stick moves, A clicks, B right-clicks. Off inside games.
- **Lid sleep and battery:** the v1 Pico firmware in `pico/lid-sensor/`. Lid closed = screen off and sleep (or low-power fallback). Battery level shows in the bar and warns at 15 % and 5 % through mako.
- **Storage:** OS on eMMC, personal files and games on the micro SD at `/mnt/sdcard` (`ROMs/`, `Files/`, `Minecraft/`), set up from NEXUS menu > Setup > Prepare SD card.

### Swappable modules

The deck has two module slots along the hinge edge. Each slot takes a controller tray (one 8BitDo Zero 2, wireless, no connection needed). Both slots together take the **breadboard module**. Modules are held in by magnets and connect through a 4-pin magnetic pogo connector (5V, GND, USB data) to the deck's USB hub.

Breadboard module hardware (designed separately, custom PCB):

- Full 830-hole breadboard.
- Pin section next to it: every Pico pin (26 GPIO, 3V3, 5V, ADJ A, ADJ B, GND, RUN) has its own labelled strip of 4 connected holes (precision female headers).
- Raspberry Pi Pico 2 W soldered flat on the PCB. Its USB comes from the test pads under the board and goes to the pogo connector, so the deck sees a normal Pico.
- Breadboard minus strips are always GND. Each plus strip (top rail and bottom rail) has its own 3-way switch, **3.3V / ADJ / 5V**, and its own knob. In the ADJ position that rail follows its own knob (separate buck-boost converter per rail, about 1.2 to 5.5V), so the two rails can be two different custom voltages at once.
- Separate helper chip with an electronic fuse, rail on/off and a voltage/current sensor per rail. It keeps working while the Pico is reflashed or crashed, and reports to the deck over USB.
- BOOT and RESET buttons on the module edge.

What NEXUS OS does with it:

- **Connect pop-up:** when the module snaps in, a notification "Breadboard module connected" with buttons for Thonny, a terminal running `mpremote`, and Flash `.uf2` (picks a file and copies it to the Pico in BOOT mode).
- **Bar chip:** a `BB` chip in the top bar shows each rail's voltage (e.g. `5V · 1.8V`, top rail first). Clicking it opens a small panel with voltage and current per rail, a rails on/off switch and the Pico tools.
- **Over-current:** if the fuse trips, a red notification names the rail. Rails are switched back on from the bar chip or the module.
- **Slot status:** the NEXUS menu (Setup > Modules) shows what is in each slot.
- Built as `nexus-modules` (one small service started on USB plug-in by a udev rule, not running all the time) plus a Waybar custom module.

### Case

The case is designed and 3D-printed from scratch (no bought case), sized around the screen, keyboard, trackball, battery and the double module slot.

## Changes from v1

| v1 | v2 |
| --- | --- |
| XFCE, taskbar, start menu | Hyprland tiling, top bar, launcher |
| Tactical HUD look, five neon presets | Six calm themes (Tokyo Night default) |
| Conky HUD widgets | Removed; the bar shows what matters |
| Windows-11-style Settings app | NEXUS menu |
| LightDM login + light-locker | Auto-login straight into hyprlock |
| Tactical sound theme | Removed (quiet by default) |
| LibreOffice, FreeTube, Legcord, Remmina, Timeshift, Samba preinstalled | Moved to the Install menu |
| Callsign | Removed |
| - | Godot 4, lazygit, btop, fastfetch added |

## Build phases

Only one phase at a time. The next starts after Elijah confirms the current one works on the OptiPlex (and later the deck).

1. **Smooth desktop on the OptiPlex.** Remove `prototype/`, rework the workflow (build check + image build with `BUILD_DESKTOP=no`), backports set up, Hyprland + auto-login + hyprlock, Waybar, fuzzel, mako, SwayOSD, foot, Thunar, Tokyo Night hard-wired through the template system, all shortcuts, animations, service trimming, `nexus-bench`. Update `CLAUDE.md` to match this spec.
2. **NEXUS menu.** All sections except Install, plus `nexus-wifi`, `nexus-bluetooth`, power menu, screenshots, idle settings.
3. **Themes.** All six themes, generated wallpapers, theme picker, live switching, low-effects mode switch.
4. **Apps.** Everything in the Preinstalled table, then the Install menu.
5. **Deck.** Deck board build, automatic low-effects mode, touch swipes, on-screen keyboard, controller mouse mode, Pico lid/battery, SD card setup.
6. **Polish and speed pass.** Measure against the speed targets on both machines and fix the slow parts, Plymouth splash, Minecraft and emulator tuning.

## Known risks

| Risk | Plan |
| --- | --- |
| Backports Hyprland needs newer libraries than Debian stable (one report of a `libxkbcommon` clash) | Build check catches it. Install the Hyprland family together with `-t trixie-backports` so matching libraries come from backports too |
| Hyprland's Lua config is new and changes between versions | Write for the exact version in backports; the build check verifies the config |
| Smoothness on a small ARM GPU is unproven | Low-effects mode; test on the deck in phase 5 |
| Minecraft on Wayland | Runs through XWayland; needs device test |
| Touch edge swipes (`lisgd`) and `wvkbd` behaviour under Hyprland | Needs device test in phase 5 |
| Nothing can be tested without hardware | Every feature is listed as "needs device test" in `PROGRESS.md` until Elijah confirms it |

## Open decisions

- [ ] Deck board (Radxa Zero 3W re-order, Pi 4/5 or RK3588)
- [ ] Iris / Open WebUI address on the home PC
- [ ] Home PC Windows Home or Pro (Remmina vs RustDesk, only if remote desktop is installed)
