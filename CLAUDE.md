# NEXUS OS: instructions for Claude Code

Read this file, `SPEC.md` and `PROGRESS.md` at the start of every session before doing anything.

## What this project is

NEXUS OS is a custom Linux image for Elijah's handheld cyberdeck. `SPEC.md` is the source of truth for what the OS must do and look like. If something here and `SPEC.md` disagree, `SPEC.md` wins. Never change `SPEC.md` without asking first.

## The hardware

- Board: Radxa Zero 3W (RK3566, 8GB RAM, 64GB eMMC, no GPIO). May be swapped later for a Raspberry Pi 5 or RK3588 board, so nothing may depend on this board except `config/board.conf`.
- Screen: Waveshare 7" 1024x600 capacitive touchscreen (H), HDMI, built-in 3.5mm headphone jack.
- Input: mini keyboard + trackpad, Bluetooth controller (8BitDo-style), touchscreen. All three are used together.
- Storage: OS on internal eMMC, personal files and games on micro SD mounted at `/mnt/sdcard`.
- Ports: USB-C power, micro SD, 2x USB-A via a Simplecom CH385 hub.
- Case: folding handheld in a Tactix technician case. A Raspberry Pi Pico over USB will read a hinge magnet sensor for lid-close sleep.

## Hard constraints

- Elijah's PC runs Windows with no Linux and no WSL. The image is NEVER built locally. All builds run in GitHub Actions (`.github/workflows/build.yml`), and the finished `.img` is downloaded from the Actions tab or Releases.
- You cannot test on the real device. Elijah flashes the image and reports back. Anything you can't verify without hardware must be marked "needs device test" in `PROGRESS.md`.
- Base is Armbian, Debian stable, XFCE. Do not switch base OS or desktop without asking.
- Stability over new features. No unstable or testing repos.
- No hard-coded colours anywhere. Every themed file reads its colours from the active preset in `overlay/usr/share/nexus/presets/<name>.conf`.
- Keep the GitHub Actions build within free-runner limits (clean up disk space in the workflow, cache what can be cached).

## How Elijah wants you to work

- Explain things in plain words, without jargon, and always give exact file and folder paths.
- When changing a file, show the full updated file, not just the changed lines.
- Keep explanations short once the context is clear.
- Ask before adding packages or features that are not in `SPEC.md`.

## Build in phases

Only work on the current phase. Do not start the next phase until Elijah confirms the image boots and the current phase works on the device.

1. Repo skeleton, `config/board.conf`, GitHub Actions workflow, bare Armbian XFCE image that builds on GitHub and boots to a desktop.
2. All apps from the Apps table in `SPEC.md` installed and launching.
3. Theme system and the five colour presets (get Amber fully working first, then add the other four).
4. HUD widgets (Conky), taskbar and start menu layout, keyboard shortcuts, on-screen keyboard toggle, controller mouse-mode toggle.
5. Settings app and Quick Settings (Python + GTK, `overlay/opt/nexus/settings/`, launched by `/usr/local/bin/nexus-settings`). Build it one category at a time.
6. Extras: Plymouth boot animation, themed LightDM login, tactical sound theme, lid sensor (Pico firmware in `pico/lid-sensor/`), Minecraft and emulator tuning.

## After every change

1. Update `PROGRESS.md` with: the current phase, what changed, what still needs doing, known issues, and anything marked "needs device test".
2. Commit with a clear message and push so GitHub Actions starts a build.
3. Give Elijah a short test checklist: the exact things to try on the deck once he flashes the new image, written as steps he can tick off.

## When Elijah reports a problem

He will paste error text or describe what he saw, sometimes with photos of the screen. Fix the cause, explain the fix in one or two sentences, update `PROGRESS.md`, and give a new test checklist.

## Repo layout

| Path | What it holds |
| --- | --- |
| `CLAUDE.md` | This file |
| `SPEC.md` | The full OS spec (source of truth) |
| `PROGRESS.md` | Current phase, changes, issues, things to test |
| `config/board.conf` | The one line that picks the board, e.g. `BOARD=radxa-zero3` |
| `config/packages.txt` | Every app to preinstall |
| `userpatches/customize-image.sh` | Script that runs inside the image during the build |
| `overlay/` | Files copied straight into the image (themes, presets, configs, sounds, wallpapers, Settings app) |
| `pico/lid-sensor/` | MicroPython code for the Pico hinge sensor |
| `.github/workflows/build.yml` | The GitHub Actions job that builds the image |
