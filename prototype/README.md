# NEXUS OS prototype

This folder is a **full first draft of all six phases at once**: every app, the five colour presets, HUD widgets, taskbar and start menu, shortcuts, the Settings app and Quick Settings, boot animation, themed login, tactical sounds and the Pico lid sensor.

The phase-by-phase build in the main repo is untouched. The prototype has its own GitHub build (**Actions > Build NEXUS OS prototype**), and its image is called `NEXUS-OS-prototype_<version>_radxa-zero3.img.xz`. Flash it the same way as the normal image (see `docs/FLASHING.md`).

Nothing here has run on real hardware yet. Treat every feature as "needs device test". The parts that work get copied into the main build phase by phase.

## Everyday apps check (Windows → NEXUS)

| On Windows | In NEXUS prototype | Opens with |
| --- | --- | --- |
| File Explorer | Thunar (+ zip/rar handling, Windows shares) | Super + E |
| Settings | NEXUS Settings | Super + I |
| Quick Settings / Action Center | NEXUS Quick Settings | Super + A, or the status text on the taskbar |
| Notepad | Mousepad | Start menu |
| Calculator | MATE Calculator | Start menu |
| Paint | Drawing | Start menu |
| Photos | Viewnior | Double-click a picture |
| Camera | guvcview (for a USB webcam) | Start menu |
| Snipping Tool | Screenshot (full screen or area, copied to clipboard) | Print Screen, Super + Shift + S |
| Command Prompt / Terminal | Xfce Terminal | Super + T |
| Task Manager | Task Manager | Ctrl + Shift + Esc |
| Media Player | mpv (video and music) | Double-click a file |
| Edge | Chromium (Firefox ESR one tap away in the App Center) | Taskbar |
| PDF reader | Evince | Double-click a PDF |
| Clipboard history (Win + V) | Clipman | Taskbar tray |
| Disk Management | Disks (format, check drives) | Start menu |
| Volume mixer | Volume control (pavucontrol) | Settings > Sound |
| On-screen keyboard | Onboard | Super + K, keyboard button on taskbar |
| Office | LibreOffice Writer, Calc, Impress | Start menu |
| Remote Desktop | Remmina | Start menu |
| System Restore / Backup | Timeshift snapshots | Settings > Update & backup |
| Printers | System Config Printer (from Armbian) | Start menu |
| Lock screen | Light Locker with the themed login screen | Super + L |
| Emoji | Noto Color Emoji font | Works in every app |
| Microsoft Store | App Center (extra browsers, games and game systems) | Settings > Apps > App Center |
| Edge "install this site as an app" | Web apps | Settings > Apps > Web apps |
| Snap layouts / tiling | Window layout: Stack (Windows style) or Split (Omarchy style) | Super + Space, or Quick Settings |

Left out on purpose (bloat, or no use on the deck): Mail, Calendar app, Maps, Sound Recorder, Sticky Notes, News, Tips, Xbox app, Clipchamp, Copilot. Any of them can be added later.

## Things the prototype does differently from SPEC.md

These are suggestions. Each one needs your OK before it goes into the main build.

| SPEC.md says | Prototype does | Why |
| --- | --- | --- |
| AntiMicroX for controller mouse mode | A small built-in helper (`nexus-pad`) | AntiMicroX has no ARM build and isn't in Debian 13 |
| PPSSPP and Flycast as separate apps | The RetroArch versions (PPSSPP core, Flycast core) | Not in Debian 13 for ARM. ES-DE picks them automatically |
| Snapshots in `/mnt/sdcard/Snapshots/` | Timeshift's own `/mnt/sdcard/timeshift/`, with `Snapshots` as a shortcut to it | Timeshift always uses that folder name |
| Battery level | Read by the Pico (GP26) along with the lid sensor | The Zero 3W can't measure the battery itself |
| Click sound on menu open | Plays when the start menu opens with the Super key | XFCE has no general menu-open sound hook |
| Hotspot tile | Connects to your saved phone hotspot | The spec's "saved phone hotspots" |
| Weather | Open-Meteo (free, no account) | Needs no sign-up |
| Callsign | `NEXUS` until you pick one | Still an open decision |
| Window corners | Always square. "Rounded" in a preset rounds the HUD widgets and Settings tiles only | Spec says square windows and rounded panels |
| PSX / arcade / N64 emulators | PCSX ReARMed, MAME 2003-Plus, ParaLLEl N64 | Lighter cores that suit the RK3566 |

## Customising your deck (added 2026-10-22)

Everything below was approved by Elijah on 2026-10-22 and is now in `SPEC.md`.

| Feature | Where | What it does |
| --- | --- | --- |
| App Center | Settings > Apps > App Center | Install or remove extra apps with one tap. Browsers: Firefox ESR, GNOME Web, Falkon. Games: SuperTuxKart, SuperTux, Luanti, OpenTTD, Wesnoth, Neverball, Extreme Tux Racer, Hedgewars. Casual: Solitaire, Mines, Sudoku, Mahjongg, Chess, 2048. Game systems: Atari 2600/7800/Lynx, PC Engine, WonderSwan, Nintendo DS, DOS, ScummVM (they show up in ES-DE once their ROM folder has files). Also lets you make any browser the default. |
| Web apps | Settings > Apps > Web apps | Turns a website (YouTube Music, Discord...) into a start menu app with its own window. Uses your default browser. |
| Custom colour preset | Settings > Personalization > Custom colour preset | Pick your own five colours, wallpaper pattern, corners and sounds. It builds a sixth preset called Custom, with the full set (window theme, icons, wallpaper, login, boot animation) like the other five. |
| Window layout | Settings > Personalization > Window layout, Quick Settings tile, Super + Space | **Stack**: normal overlapping windows like Windows. **Split**: windows tile side by side automatically like Omarchy (the newest gets the big left half, the rest stack on the right). |
| Your own shortcuts | Settings > Bluetooth & devices > Keyboard | Add a key combination that opens any app, web app or command. Warns if the keys are already used. |
| Welcome tour | Opens on first login; again from the start menu or Settings > System > About | Six steps: colours, window layout, browser, extra games, then a shortcut cheat sheet. |

New keyboard shortcuts for the window layout:

| Shortcut | Stack | Split |
| --- | --- | --- |
| Super + Space | Switch to Split | Switch to Stack |
| Super + Arrows | Snap left/right half, maximise, minimise | Jump to the window on that side |
| Super + Shift + Arrows | (nothing) | Swap with the window on that side |
| Super + Enter | (nothing) | Make this the main (big) window |
| Super + F | (nothing) | Float this window above the others; press again to tile it |
| Super + W | Close the window | Close the window |

Brave and Vivaldi were left out on purpose: both are Chromium underneath (already built in) and would need outside software sources added at install time, which goes against the stable-sources-only rule.

To offer another app in the App Center, add a section to `overlay/usr/share/nexus/appcenter.conf` and push. The file explains the format. Debian apps use `kind=apt`; RetroArch systems use `kind=core`.

Extra emulator cores come from libretro's nightly build server when you press Install (like the built-in ones, which are downloaded during the build). The ES-DE picks for the new systems: Beetle PCE FAST for PC Engine and melonDS for Nintendo DS (lighter than ES-DE's defaults).

## Extra packages (not listed in SPEC.md)

Needed for spec features: `gir1.2-wnck-3.0` (window layout helper, added 2026-10-22), `samba` (ROMs share), `ufw` (firewall), `unattended-upgrades`, `openssh-server`, `lightdm-gtk-greeter` and `light-locker` (themed login/lock), `plymouth` (boot animation), `conky-all` (HUD), `onboard`, `xcape` (Super key alone opens the menu), `xinput-calibrator`, `xserver-xorg-input-evdev` (long-press right-click), `xfce4-docklike-plugin` (Windows-style taskbar), `xfce4-genmon-plugin` (status text), `mate-polkit` (password prompts), `brightnessctl`, `papirus-icon-theme`, `fonts-jetbrains-mono`, `librsvg2-bin`, `python3-evdev`, `python3-serial`, `gnome-keyring`, `cron`.

Everyday apps from the check above: `mate-calc`, `drawing`, `guvcview`, `xfce4-screenshooter`, `xfce4-taskmanager`, `xfce4-clipman-plugin`, `xarchiver`, `thunar-archive-plugin`, `7zip`, `fonts-noto-color-emoji`.

Downloaded during the build (pinned versions in `config/downloads.txt`):
- FreeTube 0.25.3 and Legcord 1.3.0 (official `.deb` files).
- ES-DE 3.5.0 and Prism Launcher 11.1.1 (official AppImages, unpacked so they start faster).
- RetroArch cores from libretro's build server. These are nightly builds, because libretro publishes no stable ARM builds.
- Share Tech Mono font from Google Fonts.

## Folder layout

| Path | What it holds |
| --- | --- |
| `config/board.conf` | Board and kernel, same as the main build |
| `config/packages.txt` | Every package installed from Debian, VS Code's and Tailscale's repos |
| `config/downloads.txt` | Apps, emulator cores, fonts and keys downloaded during the build |
| `userpatches/customize-image.sh` | Runs inside the image during the build |
| `tools/fetch-downloads.sh` | Downloads everything in `downloads.txt` on the GitHub runner |
| `tools/minecraft-template.py` | Builds the tuned Fabric + Sodium Minecraft instance |
| `overlay/opt/nexus/lib/nexus/` | Shared Python code: presets, theme generator, HUD, controller, Pico, Wi-Fi/Bluetooth helpers, App Center, web apps, window layout (`tiler.py`) |
| `overlay/opt/nexus/settings/` | The Settings app, Quick Settings and the welcome tour |
| `overlay/usr/share/nexus/appcenter.conf` | The App Center list |
| `overlay/usr/share/nexus/presets/` | The five colour presets, plus a hidden high-contrast one |
| `overlay/usr/local/bin/`, `overlay/usr/local/sbin/` | The `nexus-*` commands |
| `overlay/etc/skel/` | Default desktop setup for new users (taskbar, start menu, HUD, ES-DE, RetroArch, Prism) |
| `pico/lid-sensor/` | Pico firmware and wiring guide |

## How the colours work

No colour is typed anywhere except the preset files. During the build, `nexus.assets` reads each preset and generates its window theme, title bars, icons, wallpaper, login picture, boot animation, terminal colours, on-screen keyboard colours and sounds. Picking a preset in Settings points everything at that preset's generated files, then recolours the login screen and boot animation.

To add a sixth preset: copy `overlay/usr/share/nexus/presets/amber.conf` to a new name, change the colours, push. Or make one on the deck in Settings > Personalization > Custom colour preset, which builds the same files there and then.
