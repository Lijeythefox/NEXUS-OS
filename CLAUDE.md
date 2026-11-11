# NEXUS OS: instructions for Claude Code

Read this file, `SPEC.md` and `PROGRESS.md` at the start of every session before doing anything.

## What this project is

NEXUS OS 2 is a fast, minimal, smooth Linux desktop in the style of Omarchy (Hyprland, tiling, calm themes), filled with Elijah's own tools. `SPEC.md` is the source of truth for what the OS must do and look like. If something here and `SPEC.md` disagree, `SPEC.md` wins. Never change `SPEC.md` without asking first.

The old tactical version (XFCE, Conky HUD, Settings app) is on the `tactical-v1` branch. Port code from there when a phase needs it (Pico, battery, controller helper).

## The hardware

- **Now:** Dell OptiPlex 3060 SFF (`BOARD=uefi-x86`). This is the only machine that can be tested.
- **Later:** the cyberdeck. Board undecided (Radxa Zero 3W, Pi 4/5 or RK3588). Nothing may depend on a board except `config/board.conf`.
- Deck screen: Waveshare 7" 1024x600 capacitive touchscreen (H), HDMI.
- Deck input: custom 40% keyboard, trackball, touchscreen, Bluetooth controller trays, swappable breadboard module (see `SPEC.md`).

## Hard constraints

- Elijah's PC runs Windows with no Linux and no WSL. The image is NEVER built locally. All builds run in GitHub Actions, and the finished `.img.xz` is downloaded from the Actions tab or Releases.
- You cannot test on the real device. Elijah flashes the image and reports back. Anything you can't verify without hardware must be marked "needs device test" in `PROGRESS.md`.
- Base is Armbian (no Armbian desktop), Debian stable, Hyprland. Do not switch base OS or desktop without asking.
- Only the Hyprland family comes from Debian backports (`config/packages-backports.txt`). No testing or unstable repos.
- Hyprland's config is Lua (`hyprland.lua`). The old `.conf` format is gone in newer versions.
- No hard-coded colours anywhere. Every themed file is a template in `overlay/usr/share/nexus/templates/` filled from `overlay/usr/share/nexus/themes/<name>/theme.conf`.
- Keep the system small: packages are installed without apt's "recommended" extras, so list everything that is needed.
- Keep the GitHub Actions build within free-runner limits.

## How Elijah wants you to work

- Explain things in plain words, without jargon, and always give exact file and folder paths.
- When changing a file, show the full updated file, not just the changed lines.
- Keep explanations short once the context is clear.
- Ask before adding packages or features that are not in `SPEC.md`.

## Build in phases

Only work on the current phase (see `SPEC.md` > Build phases). Do not start the next phase until Elijah confirms the image boots and the current phase works on the device.

1. Smooth desktop on the OptiPlex.
2. NEXUS menu.
3. Themes.
4. Apps.
5. Deck.
6. Polish and speed pass.

## Checks before every image build

Develop on a branch. Every push to a branch runs **Check NEXUS OS** (`.github/workflows/check.yml`, about 3 minutes):

- `ci/check-static.sh`: syntax of every script and config, then the unit tests in `ci/tests.sh`. Run it locally too: `bash ci/check-static.sh`.
- `ci/desktop-check.sh`: installs the real package lists in a clean Debian container and runs `Hyprland --verify-config` on the NEXUS config.

Write the test first for anything with logic (see `ci/tests.sh`). Only merge to `main` when the check is green: a push to `main` runs the check again and then the 2-hour image build (`.github/workflows/build.yml`).

## After every change

1. Update `PROGRESS.md` with: the current phase, what changed, what still needs doing, known issues, and anything marked "needs device test".
2. Commit with a clear message and push so GitHub Actions starts a build.
3. Give Elijah a short test checklist: the exact things to try once he flashes the new image, written as steps he can tick off.

## When Elijah reports a problem

He will paste error text or describe what he saw, sometimes with photos of the screen. Useful things to ask for: the output of `nexus-bench`, `hyprctl configerrors`, and the file `~/.cache/nexus/hyprland.log`. Fix the cause, explain the fix in one or two sentences, update `PROGRESS.md`, and give a new test checklist.

## Repo layout

| Path | What it holds |
| --- | --- |
| `CLAUDE.md` | This file |
| `SPEC.md` | The full OS spec (source of truth) |
| `PROGRESS.md` | Current phase, changes, issues, things to test |
| `config/board.conf` | Board and kernel branch, e.g. `BOARD=uefi-x86` |
| `config/packages.txt` | Debian stable packages to preinstall |
| `config/packages-backports.txt` | The Hyprland family, from backports |
| `userpatches/customize-image.sh` | Script that runs inside the image during the build |
| `tools/install-packages.sh` | Installs both package lists (used by the image build and the check) |
| `tools/make-wallpapers.py` | Makes each theme's wallpapers from its colours |
| `overlay/` | Files copied straight into the image |
| `overlay/usr/share/nexus/default/` | NEXUS default configs (Hyprland Lua files, Waybar, hypridle, shortcut list) |
| `overlay/usr/share/nexus/themes/` | One folder per theme (`theme.conf`) |
| `overlay/usr/share/nexus/templates/` | Config templates the theme colours are poured into |
| `overlay/usr/local/bin/nexus-*` | NEXUS commands |
| `overlay/etc/skel/` | Starter files for a new user |
| `pico/lid-sensor/` | MicroPython code for the Pico hinge sensor (deck, phase 5) |
| `ci/` | Check scripts and unit tests |
| `.github/workflows/` | `check.yml` (fast check) and `build.yml` (image build) |
| `docs/` | Install guides, plans |
