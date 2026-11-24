# NEXUS OS 2 architecture

How NEXUS OS is put together: what each part does, which file it lives in, and how the parts talk to each other. Read this before changing anything that isn't a single small script.

## The big picture

```
 GitHub repo (this one)                     GitHub Actions (free runners)
 ┌──────────────────────────┐   push   ┌────────────────────────────────────────┐
 │ config/   package lists  │ ───────► │ check.yml   3 min   syntax + tests +    │
 │ overlay/  NEXUS files    │          │                     real install +      │
 │ userpatches/ build hook  │          │                     Hyprland config ok  │
 │ tools/  ci/  pico/ docs/ │          │ build.yml   ~2 h    Armbian image       │
 └──────────────────────────┘          │ vm-disk.yml ~15 min VMware machine      │
                                       └───────────────┬────────────────────────┘
                                                       │ .img.xz / .zip
                                                       ▼
                                  Elijah: flash with balenaEtcher → OptiPlex / deck
                                          or open the VM in VMware
```

On the running machine:

```
 power on → UEFI → kernel → systemd
            → getty@tty1 (auto-login via nexus-getty)
            → /etc/profile.d/zz-nexus-session.sh
            → nexus-session → start-hyprland → Hyprland
                 → nexus.lua (defaults + theme colours)
                 → nexus-autostart → hyprlock first, then bar, notifications, …
```

## 1. Layers

| Layer | What | Who owns it |
| --- | --- | --- |
| Hardware | OptiPlex 3060 now; deck board later | `config/board.conf` only |
| Base OS | Armbian, Debian 13 "trixie", no Armbian desktop | Armbian build framework |
| Packages | Debian stable + the Hyprland family from trixie-backports | `config/packages*.txt` |
| NEXUS files | Configs, scripts, themes, templates | `overlay/` |
| Per-user state | Current theme files, user overrides, logs | `~/.config/`, `~/.cache/nexus/` |

The rule that keeps this clean: **anything NEXUS ships lives in `/usr/share/nexus/`, `/usr/local/bin/`, `/usr/local/sbin/` or `/etc/nexus/`**, so an update can replace it. **Anything the user changes lives in their home folder**, so an update never touches it.

## 2. The build

### 2.1 Package lists

| File | Source | Install style |
| --- | --- | --- |
| `config/packages.txt` | Debian 13 stable | `apt-get install --no-install-recommends` |
| `config/packages-backports.txt` | trixie-backports | `apt-get install --no-install-recommends -t trixie-backports` (all at once, so matching libraries come from backports too) |

Both are installed by **one** script, `tools/install-packages.sh`, which the image build *and* the GitHub check both run. That way the check tests exactly what the image will get.

Because recommended extras are off, **every** needed package must be listed (for example `librsvg2-common` so SVG icons draw, `fonts-font-awesome` so bar icons aren't boxes, `rtkit` so sound gets real-time priority).

Phase 1 package groups:

| Group | Packages |
| --- | --- |
| Hyprland family (backports) | hyprland, hyprlock, hypridle, hyprpolkitagent, xdg-desktop-portal-hyprland |
| Desktop pieces | waybar, fuzzel, mako-notifier, swayosd, swaybg, foot, thunar, gvfs, xwayland |
| Screenshots and keys | grim, slurp, wl-clipboard, brightnessctl, playerctl, libnotify-bin |
| Portals and folders | xdg-desktop-portal, xdg-desktop-portal-gtk, xdg-user-dirs |
| Sound | pipewire, pipewire-audio, pipewire-pulse, wireplumber, rtkit |
| Graphics | libgl1-mesa-dri, libegl1, libgles2, mesa-vulkan-drivers |
| Fonts and icons | fonts-jetbrains-mono, fonts-font-awesome, fonts-noto-core, fonts-noto-color-emoji, adwaita-icon-theme, librsvg2-common |
| Plumbing | gsettings-desktop-schemas, dconf-gsettings-backend, dbus-user-session, polkitd, pkexec, network-manager, wpasupplicant, jq, procps, python3 |

### 2.2 The Armbian build (`.github/workflows/build.yml`)

1. Runs `check.yml` first (as a reusable workflow). If the check fails, no image is built.
2. Reads `config/board.conf` (`BOARD=uefi-x86`, `BRANCH=current`).
3. Checks out the Armbian build framework at a pinned version (v26.5.1).
4. For `uefi-x86`, deletes Armbian's MacBook-only kernel patches (`[1-4]xxx-*.patch`) that break the generic x86 kernel build.
5. Stages `overlay/`, the package lists and `tools/install-packages.sh` into `userpatches/overlay/.nexus-build/`.
6. Runs `tools/make-wallpapers.py` to draw each theme's wallpapers from its colours into the overlay.
7. Runs `./compile.sh` with `BUILD_DESKTOP=no BUILD_MINIMAL=no RELEASE=trixie`.
8. Inside the image, Armbian runs **`userpatches/customize-image.sh`**:
   - fixes any half-installed packages, adds trixie-backports, runs `install-packages.sh`;
   - copies `overlay/` onto `/` (root-owned, keeps existing folder links);
   - switches off CUPS, Avahi, ModemManager and the SSH server; delays apt's daily timers to 10 minutes after boot;
   - enables NetworkManager and the SwayOSD input service;
   - holds the kernel packages so an `apt upgrade` can't break boot;
   - writes `/etc/nexus/version`.
9. Compresses the image to `NEXUS-OS_<version>_<board>.img.xz` and uploads it as a workflow artifact (and to a GitHub Release on `v*` tags).

Docs-only pushes (`**.md`, `docs/**`, `pico/**`) don't start the build (`paths-ignore`).

The Armbian cache is saved between runs so later builds are faster and stay within the free-runner time limit.

### 2.3 The VM build (`.github/workflows/vm-disk.yml`)

After every successful image build (or when started by hand), converts the image into a 32 GB VMware disk (`qemu-img`, `monolithicSparse`), writes a `.vmx` (UEFI, 4 GB RAM, 2 CPUs, 3D graphics, vmxnet3 network, NVMe disk) and a `READ-ME-FIRST.txt`, and uploads the zip. See [TEST-IN-VM.md](TEST-IN-VM.md).

## 3. Starting the desktop

There is **no login manager** (no LightDM or GDM). The lock screen is the only password prompt. This saves memory and a few seconds of boot.

### 3.1 Auto-login (`overlay/usr/local/sbin/nexus-getty`)

A drop-in, `overlay/etc/systemd/system/getty@tty1.service.d/zz-nexus.conf`, makes screen 1's login prompt run `nexus-getty` instead of asking for a name. It decides who to log in:

| Situation | Logs in |
| --- | --- |
| `/etc/nexus/no-autologin` exists | Nobody: normal login prompt |
| `/root/.not_logged_in_yet` exists (Armbian first-run setup not done) | `root`, so Armbian's setup questions appear |
| `/etc/nexus/autologin-user` names a user | That user |
| Otherwise | The first normal user (UID 1000) |
| No such user | Normal login prompt |

### 3.2 Handover (`overlay/etc/profile.d/zz-nexus-session.sh`)

Runs at every login shell:

- **Root on tty1, setup just finished, marker `/var/lib/nexus/desktop-handover-done` missing:** writes the marker and logs out, so `nexus-getty` runs again and logs the new user in. This happens once.
- **A normal user (UID ≥ 1000) on tty1, no desktop running yet:** runs `nexus-session`.
- Anything else (SSH, other screens): does nothing.

### 3.3 `nexus-session` (`overlay/usr/local/bin/nexus-session`)

1. `nexus-theme ensure` makes sure `~/.config/nexus/current/` exists for the current theme.
2. Starts `start-hyprland` (Hyprland's own launcher script; falls back to `Hyprland` if missing). Output goes to `~/.cache/nexus/hyprland.log` (the previous one is kept as `hyprland.log.old`).
3. **Crash guard:** if Hyprland exits within 10 seconds (`NEXUS_FAST_FAIL_SECS`) it counts as a failure. After 3 in a row, it stops, prints what to do, and leaves you at a working shell, instead of flickering forever. A normal log-out (longer run) resets the count.

### 3.4 Inside Hyprland

`~/.config/hypr/hyprland.lua` (the user's file) has one line that matters: `dofile("/usr/share/nexus/default/hypr/nexus.lua")`. Anything the user adds **below** it overrides the defaults.

`nexus.lua` loads, in this order:

| File (`/usr/share/nexus/default/hypr/`) | What it sets |
| --- | --- |
| `bindings.lua` | Every shortcut (first, so the keyboard works even if a later file breaks) |
| `input.lua` | Keyboard layout, mouse, touchpad, touch, focus follows mouse |
| `looknfeel.lua` | Monitors, gaps, rounding, blur, shadows, animation curves and speeds |
| `rules.lua` | Window rules (which windows float, sizes, opacity) and layer rules (blur behind bar, launcher, notifications) |
| `events.lua` | Hooks: tells the bar to redraw workspace dots when windows or workspaces change |
| `autostart.lua` | Environment variables (cursor, GTK dark, Wayland for Qt/Electron); runs `nexus-autostart` on start |
| `~/.config/nexus/current/hyprland.lua` | Theme colours (borders, shadow), made from the template |

Each file is loaded inside a safety net (`pcall`): a mistake in one file is reported as a critical notification and the rest still load. In the GitHub check, `NEXUS_STRICT=1` turns the safety net off so any mistake fails the check.

### 3.5 `nexus-autostart`

Order matters: **lock first**, so nothing is ever visible before the password.

1. Shares the desktop's settings (display name, cursor, GTK theme) with background services, so file pickers and portals work.
2. `nexus-lock` → hyprlock. Skipped if `NEXUS_NO_LOCK=1` or `~/.config/nexus/no-lock-on-login` exists.
3. `nexus-wallpaper apply` → swaybg with the theme's wallpaper
4. `nexus-bar` (Waybar with the theme CSS)
5. `mako` (notifications)
6. `nexus-osd start` → swayosd-server (volume/brightness pop-up)
7. `hypridle` (dim 240 s, lock 300 s, screen off 360 s)
8. `hyprpolkitagent` as a user service (password pop-ups for admin actions)
9. `xdg-user-dirs-update` (Documents, Pictures… folders)

The user's `~/.config/hypr/hyprland.lua` comes from `/etc/skel` when the account is made.

## 4. The theme system

The single most important rule in the project: **no colour is typed anywhere except a `theme.conf`.**

```
 themes/tokyo-night/theme.conf ─┐
                                ├─► nexus-theme render ─► ~/.config/nexus/current/
 templates/*  ({{accent}} …) ───┘                          hyprland.lua  waybar.css
                                                           fuzzel.ini    mako
                                                           foot.ini      hyprlock.conf
                                                           swayosd.css
```

### 4.1 `theme.conf`

Plain `key=value`. `name` is text; every other key must be a `#rrggbb` colour. Keys:

| Key | Used for |
| --- | --- |
| `bg`, `surface`, `raised` | Background, panels, raised panels (darkest → lighter) |
| `fg`, `muted` | Main text, secondary text |
| `accent`, `accent2` | Focus border, highlights, active workspace pill |
| `urgent`, `green`, `yellow` | Errors/critical, success, warnings |
| `shadow` | Window shadows |
| `color0` … `color15` | The 16 terminal colours |

### 4.2 Templates

Each file in `overlay/usr/share/nexus/templates/` is a normal config file with placeholders:

| Placeholder | Becomes | Example for `accent=#7aa2f7` |
| --- | --- | --- |
| `{{accent}}` | `#rrggbb` | `#7aa2f7` |
| `{{accent_hex}}` | `rrggbb` (no `#`, for foot, fuzzel, Hyprland) | `7aa2f7` |
| `{{accent_rgb}}` | `r, g, b` (for CSS `rgba()`) | `122, 162, 247` |
| `{{name}}` | Theme name | `Tokyo Night` |

An unknown placeholder makes `nexus-theme` stop with an error (and the GitHub check fails), so a typo can never ship.

### 4.3 `nexus-theme` (`overlay/usr/local/bin/nexus-theme`, Python)

| Command | Does |
| --- | --- |
| `list` | Themes installed in `/usr/share/nexus/themes/` |
| `current` | The theme in use (`~/.config/nexus/theme`, else `/etc/nexus/default-theme`) |
| `render NAME DIR` | Fills every template into `DIR` (the check uses this) |
| `ensure` | Renders the current theme if the files are missing or older than the theme/templates |
| `set NAME` | Renders, saves the choice, and reloads the running desktop (Hyprland, Waybar, mako, wallpaper) |

Writes go to a temporary folder first and then swap in, so a half-written theme is never live.

### 4.4 Wallpapers

`tools/make-wallpapers.py` draws 3 wallpapers per theme at build time from the theme's colours (soft gradients and simple shapes), into `/usr/share/nexus/themes/<name>/wallpapers/`. No downloaded images, so no licence issues and the repo stays small. `nexus-wallpaper next|apply` cycles them and remembers the choice in `~/.config/nexus/wallpaper-index`.

## 5. The top bar

Waybar, config in `overlay/usr/share/nexus/default/waybar/config.json`, style from the theme's `waybar.css`.

**Workspace dots are custom.** Waybar's built-in Hyprland workspace module sends commands in the old text format, which Hyprland rejects when the config is Lua. So:

- `custom/ws1` … `custom/ws5` each run `nexus-ws-state N`, which asks `hyprctl -j` for the active workspace and which workspaces have windows, and prints `active`, `occupied` or `empty` as a CSS class.
- They only refresh on signal `RTMIN+8`. `events.lua` sends that signal (`pkill -RTMIN+8 -x waybar`) whenever a workspace or window changes. No polling.
- Clicking a dot runs `nexus-workspace N`, which switches using the Lua dispatcher.

Everything else polled in the bar is 5 seconds or slower.

## 6. NEXUS commands

All in `overlay/usr/local/bin/`. Each is small, does one thing, and has a short help at the top.

| Command | Does | Phase |
| --- | --- | --- |
| `nexus-session` | Starts Hyprland with the crash guard | 1 |
| `nexus-autostart` | Starts lock, bar, notifications, … | 1 |
| `nexus-theme` | Theme system (see above) | 1, 3 |
| `nexus-wallpaper` | Next wallpaper, or show the saved one at start-up | 1 |
| `nexus-bar` | (Re)starts Waybar with the theme CSS | 1 |
| `nexus-launcher` | fuzzel app launcher with theme | 1 |
| `nexus-pick` | Shared helper: show a list in fuzzel, print the choice | 1 |
| `nexus-menu` | Phase 1: small menu (power, theme, shortcuts). Phase 2: the full NEXUS menu | 1, 2 |
| `nexus-power` | Lock / sleep / restart / shut down / log out | 1 |
| `nexus-lock` | Locks unless already locked | 1 |
| `nexus-screenshot` | `full` or `area`; saves, copies, notifies | 1 |
| `nexus-osd` | Volume/brightness through SwayOSD | 1 |
| `nexus-keys` | Shows the shortcut list | 1 |
| `nexus-open` | Opens the browser, code editor, games, keyboard (or "coming in phase N") | 1, 4 |
| `nexus-screen` | Screen off/on for hypridle | 1 |
| `nexus-workspace`, `nexus-ws-state` | Bar workspace dots | 1 |
| `nexus-bench` | Boot time, idle memory, five slowest services | 1 |
| `nexus-apps` | App installer: picker, first-login question, installs/removes from `apps.conf` (Python) | 1 (built early) |
| `nexus-getty` (`/usr/local/sbin/`) | Auto-login decision | 1 |

Planned commands are listed per phase in [ROADMAP.md](ROADMAP.md).

## 7. Apps (`nexus-apps`)

No apps are in the image (D-25). The desktop is the image; apps arrive afterwards.

```
 first unlock ─► nexus-autostart ─► nexus-apps first-run
                                      │ waits for hyprlock to close, checks internet
                                      ▼
                         picker (fuzzel, nexus-pick --index)
                                      │ Go
                                      ▼
            foot terminal ─► sudo nexus-apps apply --install … --remove … --user <you>
                                      │
     ┌──────────────┬─────────────────┼───────────────────┬──────────────────┐
  extra repos    apt-get update    apt-get install       downloads          pipx (as you)
  (key + list)                     (one call, no         (GitHub/GitLab     services off
                                    recommends)           newest release,    setup steps
                                                          fingerprint check)
                                      ▼
                    /var/lib/nexus/apps/<id>   (marks what's installed)
```

| Part | Where |
| --- | --- |
| App list | `/usr/share/nexus/apps.conf` (INI: one `[id]` per app; settings explained at the top of the file) |
| Installed marks | `/var/lib/nexus/apps/<id>`, plus `<id>.json` for downloads (files made, `.deb` package name) so removal is exact |
| Unpacked AppImages and zip apps | `/opt/nexus-apps/<id>/`, started by `/usr/local/bin/<command>`, listed by `/usr/share/applications/nexus-<id>.desktop` |
| Asked-once mark | `~/.config/nexus/apps-asked` |
| Extra repositories | `/etc/apt/sources.list.d/nexus-<id>.list` + the key file named in the list |

How downloads work: the newest non-draft release (test releases only when the app says `prerelease = yes`) with a file matching `amd64_file` / `arm64_file`. GitHub publishes a SHA-256 fingerprint for release files; when present the download must match it or it's deleted. AppImages are unpacked with `--appimage-extract` **as the user** in a temporary folder, then moved into `/opt` as root, so no downloaded program runs as root and FUSE isn't needed.

If one app fails, the rest carry on; the summary at the end names what wasn't done and why, and only finished apps are marked installed.

## 8. Board independence

Only `config/board.conf` may name a board. From phase 5 this becomes `config/boards/<board>.conf` and the build makes one image per board. Anything a board needs (kernel branch, firmware, display scale, low-effects default) goes in that file. Scripts that need to know read `/etc/nexus/board` at run time, never guess from the CPU.

## 9. The deck parts (phases 6–7, planned)

```
                      ┌─────────────── deck board ───────────────┐
 Waveshare 7" ──HDMI──┤ Hyprland                                 │
   touch ─────USB─────┤   lisgd (swipes)   wvkbd (keyboard)      │
 keyboard, trackball ─┤                                          │
 Pico (lid, battery) ─┤ nexus-pico ──► Waybar battery, lid sleep │
 USB hub ─┬─ slot A ──┤ nexus-modules (udev, on plug-in only)    │
          └─ slot B ──┤   ├─ controller tray (Bluetooth)         │
                      │   └─ breadboard module: Pico 2 W +       │
                      │      helper chip ► BB bar chip, fuse     │
 micro SD ────────────┤ /mnt/sdcard  ROMs/ Files/ models/        │
                      │ Iris app ◄ llama-server (on demand)      │
                      └──────────────────────────────────────────┘
```

Rules for the deck parts: nothing runs all the time unless it must (the Pico helper and the module service start on plug-in; the AI server starts on first question and stops after 10 idle minutes).

## 10. Testing layers

| Layer | Where | Catches |
| --- | --- | --- |
| Static check | `ci/check-static.sh` | Syntax errors in every shell, Python, Lua, JSON file; Windows line endings; logic bugs (unit tests) |
| Desktop check | `ci/desktop-check.sh` | Package conflicts, missing commands, Hyprland rejecting the config, foot/fuzzel config errors |
| Simulator | Browser artifact | Look, feel and flow before an image exists |
| VM | VMware on Windows | Boot, first-run, login, most of the desktop |
| Device | OptiPlex, then deck | Real graphics, speed, sound, Wi-Fi, Bluetooth, hardware |

Details: [TESTING.md](TESTING.md).
