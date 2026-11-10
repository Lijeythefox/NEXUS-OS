# NEXUS OS 2 Phase 1 (Smooth Desktop on the OptiPlex) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A flashable `uefi-x86` image that boots straight into a locked, animated Hyprland desktop with the top bar, launcher, notifications, terminal, files, all shortcuts and the Tokyo Night theme.

**Architecture:** Armbian CLI image (no Armbian desktop) built on GitHub Actions. `userpatches/customize-image.sh` installs Debian stable packages plus the Hyprland family from trixie-backports, then copies `overlay/`. Every themed config is a template filled from one `theme.conf` by `nexus-theme`. A fast `check` job installs the real packages in a Debian container, verifies the Hyprland config and runs the desktop headless before the 2-hour image build.

**Tech Stack:** Armbian build `v26.5.1`, Debian 13 trixie, Hyprland 0.55+ (Lua config), Waybar, fuzzel, mako, SwayOSD, foot, hyprlock, hypridle, swaybg, bash, Python 3 (stdlib only).

**Spec:** `SPEC.md` (sections: Base system, Desktop, Top bar layout, Animations, Keyboard shortcuts, Themes, Speed targets, Build phases item 1).

## Global Constraints

- Never build locally. Verification = the `check` job on GitHub, then the image build, then Elijah's device test.
- Only the Hyprland family comes from `trixie-backports` (`config/packages-backports.txt`). Everything else from Debian stable. No testing/unstable.
- No colour typed anywhere except `overlay/usr/share/nexus/themes/<name>/theme.conf`.
- Hyprland config is Lua (`hyprland.lua`); defaults live in `/usr/share/nexus/default/` and are never edited by the user.
- Nothing may depend on the board except `config/board.conf`.
- Plain-words docs, exact paths; update `PROGRESS.md`; everything unverified on hardware is listed as "needs device test".
- Phase 1 only: no NEXUS menu sections beyond Apps / Shortcuts / Wallpaper / Power, no extra themes, no apps from the Apps table, no deck features.

## Review Focus

1. Hyprland fails to start (bad GPU driver, config error): the user must not be trapped in a login loop. `nexus-session` stops after 3 fast failures and leaves a shell with the log path.
2. First boot runs Armbian's setup wizard as root on tty1: auto-login must not start the desktop for root or before a user exists.
3. A theme template with a missing colour key must fail the build check, not ship `{{...}}` text into a config.
4. The lock screen shows before anything else; if hyprlock is missing or crashes the session must still be reachable from tty2.
5. Backports dependency clashes (reported `libxkbcommon`): caught by the package install step of the `check` job.

---

## File Structure

| Path | Responsibility |
| --- | --- |
| `config/packages.txt`, `config/packages-backports.txt` | Package lists (one name per line) |
| `userpatches/customize-image.sh` | Image setup: repos, packages, overlay, services |
| `overlay/usr/share/nexus/themes/tokyo-night/theme.conf` | The only place colours live |
| `overlay/usr/share/nexus/templates/*` | Themed config templates with `{{key}}` placeholders |
| `overlay/usr/share/nexus/default/hypr/*.lua` | Hyprland defaults: `nexus.lua` (entry), `looknfeel.lua`, `input.lua`, `bindings.lua`, `rules.lua`, `autostart.lua` |
| `overlay/usr/share/nexus/default/waybar/config.json`, `default/hypr/hypridle.conf`, `default/keys.txt` | Non-themed defaults |
| `overlay/usr/local/bin/nexus-theme` | `render`, `set`, `ensure`, `current`, `list` (Python) |
| `overlay/usr/local/bin/nexus-session` | Starts Hyprland from tty1 with the crash guard |
| `overlay/usr/local/bin/nexus-{bar,lock,menu,power,keys,wallpaper,screenshot,bench}` | Small bash commands |
| `overlay/usr/local/sbin/nexus-getty`, `overlay/etc/systemd/system/getty@tty1.service.d/zz-nexus.conf`, `overlay/etc/profile.d/90-nexus-session.sh` | Auto-login chain |
| `overlay/etc/skel/.config/hypr/hyprland.lua` | User config that loads the defaults |
| `tools/make-wallpapers.py` | Generates wallpapers from `theme.conf` (SVG to PNG via `rsvg-convert`) |
| `ci/check-static.sh`, `ci/check-packages.sh`, `ci/smoke-desktop.sh` | The check job's steps |
| `.github/workflows/check.yml`, `.github/workflows/build.yml` | Check (any branch, reusable) and image build (main) |

## Tasks

### Task 1: Repo reset and check workflow skeleton
- [ ] Remove `prototype/` and `.github/workflows/build-prototype.yml`; move `prototype/pico/` to `pico/`.
- [ ] Write `ci/check-static.sh` (bash -n, shellcheck -S error, `python3 -m py_compile`, `luac -p`, `jq`) and `.github/workflows/check.yml` running it in a `debian:trixie` container.
- [ ] Verify: push the branch, `gh run watch` shows the check job green.

### Task 2: Theme system
- [ ] `theme.conf` for Tokyo Night with keys `bg surface raised fg muted accent accent2 urgent green yellow color0..color15`.
- [ ] `nexus-theme render <theme> <outdir>`: fills `{{key}}` (as `#rrggbb`), `{{key_hex}}` (no `#`), `{{key_rgb}}` (`r,g,b`); exits 1 naming any unknown placeholder.
- [ ] Test in `ci/check-static.sh`: render to a temp dir; `grep -r '{{'` finds nothing; a template with `{{nope}}` makes the command exit 1.
- [ ] `tools/make-wallpapers.py <theme.conf> <outdir>` writes `1.png 2.png 3.png` (1920x1080).

### Task 3: Desktop configs
- [ ] Hyprland Lua defaults per SPEC (gaps 5/10, rounding 8, border 2, blur + shadow, Omarchy-style curves, workspaces slide, dwindle), all SPEC shortcuts, autostart (lock first, bar, mako, swayosd, hypridle, wallpaper, polkit agent, environment import).
- [ ] Templates: `hyprland.lua` (border colours), `waybar.css`, `fuzzel.ini`, `mako`, `foot.ini`, `hyprlock.conf`, `swayosd.css`.
- [ ] Waybar layout per SPEC (logo, workspaces 1-5, clock, bluetooth, network, volume, power).
- [ ] Verify: `ci/smoke-desktop.sh` runs `Hyprland --verify-config` on the skel config as a normal user: no errors.

### Task 4: Session start and commands
- [ ] `nexus-getty`: root auto-login while `/root/.not_logged_in_yet` exists, else auto-login UID 1000, else normal prompt.
- [ ] `90-nexus-session.sh`: only UID >= 1000, only `/dev/tty1`, only when no display is set and `NEXUS_NO_DESKTOP` is unset.
- [ ] `nexus-session`: `nexus-theme ensure`, start `start-hyprland` (fallback `Hyprland`), log to `~/.cache/nexus/hyprland.log`; a run shorter than 10 s counts as a failure; after 3 in a row print the log path and `exec bash` with `NEXUS_NO_DESKTOP=1`.
- [ ] Test in `ci/check-static.sh`: with a fake `start-hyprland` that exits at once, three `nexus-session` runs leave the failure counter at 3 and the third prints the log path.
- [ ] Commands `nexus-bar lock menu power keys wallpaper screenshot bench`.

### Task 5: Package lists and image script
- [ ] Fill the two package lists; `ci/check-packages.sh` adds backports and installs both lists in the container (amd64 gating, arm64 informational).
- [ ] Rewrite `customize-image.sh`: non-interactive apt, backports source, both lists, overlay copy, service trimming (cups, avahi, ModemManager, ssh off; apt timers delayed 10 min), hostname, `/etc/nexus/version`.
- [ ] `ci/smoke-desktop.sh`: headless Hyprland (`HYPRLAND_HEADLESS_ONLY=1`) with bar, terminal and launcher; `hyprctl configerrors` empty; screenshot uploaded as an artifact.

### Task 6: Image build workflow, docs, ship
- [ ] `build.yml`: `check` (reusable) then `build` with `BUILD_DESKTOP=no`, wallpaper generation, MacBook patch removal for `uefi-x86`, cache, artifact `NEXUS-OS_<version>_<board>.img.xz`.
- [ ] Update `CLAUDE.md`, `PROGRESS.md`, `docs/FLASHING.md`, `docs/INSTALL-OPTIPLEX.md`.
- [ ] Merge to `main`, confirm the image build starts, give Elijah the test checklist.
