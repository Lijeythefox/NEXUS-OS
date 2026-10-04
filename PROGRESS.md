# NEXUS OS progress

## Current phase

**Phase 1: Repo skeleton and bare image.** Waiting for the first GitHub build and a device test.

## Prototype (all phases at once, separate from the phased build)

Elijah asked for the whole OS as a prototype in `prototype/`, plus a check that it has every everyday app Windows has. Details, the Windows app table and every difference from `SPEC.md` are in `prototype/README.md`.

- Built by its own workflow, `.github/workflows/build-prototype.yml` ("Build NEXUS OS prototype"). It runs only when `prototype/` changes. The main build ignores `prototype/`.
- A quick check job runs first (about 5 minutes). It catches typos in Python, shell, Lua and XML, and test-generates all themes before the long build starts.
- Image name: `NEXUS-OS-prototype_<version>_radxa-zero3.img.xz` (Actions artifact only, no release).
- Status: written, not yet built successfully. **Everything in it needs device test.**
- Build #2 failed (2026-10-02): Chromium asked an interactive question during install (Armbian already ships `/etc/chromium/master_preferences`). Nobody could answer it, so Chromium was left half-installed and every later install failed, including Armbian's own `armbian-config` step. Fix: `customize-image.sh` now tells apt to always keep existing config files, repairs half-installed packages after any failure, and stops with a clear message if anything is still broken.
- Phase 1 main build #1 succeeded (2026-10-02).
- Approved for the main build: the built-in controller helper, PPSSPP/Flycast as RetroArch cores, nightly libretro cores, and the extra packages. The other differences in `prototype/README.md` (Timeshift folder, weather source, Hotspot tile, menu sound, window corners) are still open.
- `SPEC.md` updated (with Elijah's OK): the Pico also reads the battery voltage.

## Hardware change (2026-10-04)

The board is now a Radxa Zero 3W with 8GB RAM and **no eMMC**. Armbian pin (`v26.5.1`), board (`radxa-zero3`) and kernel branch (`current`) are unchanged.

1. **OS on the micro SD, personal files on a USB drive.** The flashed micro SD is the boot card for good (no copy-to-eMMC step). Games, files, Minecraft and snapshots move to a USB flash drive labelled `NEXUS-SD` in the internal USB hub. The fstab line, the `/mnt/sdcard` mount point and the `ROMs`, `Files`, `Minecraft`, `Snapshots` folders are unchanged, so ES-DE, Prism, Samba and Timeshift work as before.
2. **RAM.** 8GB confirmed. Prism stays at `MaxMemAlloc=3072` (slider 1024 to 6144 MB). Nothing else assumes a RAM size; the About page reads it live.
3. **Deck buttons.** The Pico now also reads the 8 built-in buttons (D-pad on GP2 to GP5, A/B/X/Y on GP6 to GP9) and NEXUS turns them into a controller called "NEXUS Deck Buttons". This is a prototype addition, not in `SPEC.md` yet (listed in `prototype/README.md`).

Files changed for this:

- `CLAUDE.md`, `SPEC.md`: board line, storage table, flashing step, storage settings row, deck file share; all eMMC wording removed.
- `docs/FLASHING.md`: no `armbian-install` step; 64GB+ A2 card recommended; reflashing wipes the OS card but never the NEXUS-SD drive; step 6 now sets up the USB drive.
- `prototype/overlay/opt/nexus/lib/nexus/storage.py` (new): finds removable USB drives and refuses the disk holding `/` or `/boot`, any `mmcblk` device, and anything not on USB.
- `prototype/overlay/usr/local/sbin/nexus-root`: `sd-format`/`sd-setup` became `storage-format`/`storage-setup`, and the format command re-checks the safety rules itself before erasing.
- `prototype/overlay/opt/nexus/settings/nexus_settings/pages/system.py`: Storage page shows "Boot microSD card" and "Storage drive (NEXUS-SD)"; "Prepare storage drive" lists USB drives only, asks you to pick one, then asks you to type ERASE; "Mount" button if the drive is plugged in but not mounted.
- `prototype/overlay/opt/nexus/settings/nexus_settings/pages/gaming.py`, `pages/update.py`, `overlay/etc/samba/smb.conf`, `overlay/usr/share/applications/nexus-games.desktop`: wording now says storage drive.
- `prototype/pico/lid-sensor/main.py`: 8 buttons with pull-ups, active low, 10 ms debounce; a message on every press and release; full button state in every status message; existing pins and the `"nexus": "lid-sensor"` key unchanged.
- `prototype/pico/lid-sensor/README.md`: button wiring table.
- `prototype/overlay/opt/nexus/lib/nexus/pico.py`: creates the "NEXUS Deck Buttons" virtual gamepad (D-pad on the hat, A/B/X/Y on south/east/west/north); releases every button when the Pico disconnects, goes quiet for 5 seconds, or is paused.
- `prototype/overlay/etc/skel/.config/retroarch/autoconfig/udev/NEXUS_Deck_Buttons.cfg` (new), `retroarch.cfg`: RetroArch recognises the deck buttons.
- `prototype/overlay/usr/share/nexus/input/sdl-controllers.txt` (new), `overlay/usr/local/bin/nexus-games`, `overlay/etc/X11/Xsession.d/90nexus-environment`: SDL controller mapping so ES-DE (and other SDL games) recognise the deck buttons. ES-DE needs no separate input file.
- `prototype/overlay/opt/nexus/settings/nexus_settings/pages/devices.py`, `ui.py`: Settings > Bluetooth & devices > Controller has a "Deck button test" that lights each button while it's held (colours come from the active preset).
- `prototype/overlay/etc/xdg/autostart/nexus-pico.desktop`, `pages/system.py` (Pico sensor row): wording mentions the deck buttons.
- `prototype/README.md`: deck buttons added to the differences-from-spec table.

## Decisions made

| Topic | Decision |
| --- | --- |
| Base | Armbian build framework pinned to `v26.5.1`, Debian 13 "trixie" (current stable) |
| Kernel | Mainline (`BRANCH=current` in `config/board.conf`) |
| Desktop | XFCE, Armbian's `minimal` desktop tier (apps are added by us in Phase 2) |
| Flashing | Etcher straight to the boot micro SD card (64GB+, A2-rated). The board has no eMMC, so the deck always runs from that card (see `docs/FLASHING.md`) |
| Personal storage | USB flash drive labelled `NEXUS-SD` in the internal hub, mounted at `/mnt/sdcard`. Formatted by Settings > System > Storage > Prepare storage drive |
| First boot | Keep Armbian's setup wizard for now (root password, user, locale) |
| Battery level | The Pico will read battery voltage as well as the lid sensor (Phase 6) |
| Deck buttons | The Pico reads the 8 built-in buttons; NEXUS exposes them as the "NEXUS Deck Buttons" controller (prototype, 2026-10-04) |
| Repo | Public, so GitHub Actions minutes are free |
| Branding | Armbian `VENDOR` is set to `NEXUS-OS`; hostname is `nexus` |
| Controller mouse mode | Built-in helper `nexus-pad` instead of AntiMicroX (no ARM build). Approved 2026-10-02 |
| PSP and Dreamcast | PPSSPP and Flycast as RetroArch cores (standalone apps not in Debian 13 for ARM). Approved 2026-10-02 |
| Emulator cores | libretro nightly builds for ARM (no stable ARM builds exist). Approved 2026-10-02 |
| Extra packages | The extra packages listed in `prototype/README.md` (Samba, ufw, light-locker, etc.). Approved 2026-10-02 |

## What changed (Phase 1)

- `config/board.conf`: board (`radxa-zero3`) and kernel branch (`current`).
- `config/packages.txt`: empty for now; the build already reads it.
- `userpatches/customize-image.sh`: runs inside the image during the build. Copies `overlay/`, installs `packages.txt`, sets hostname `nexus`, writes `/etc/nexus/version`.
- `overlay/etc/nexus/.keep`: placeholder so the overlay folder exists.
- `.github/workflows/build.yml`: builds the image on every push to `main` (or the manual **Run workflow** button). Frees runner disk space, caches Armbian's rootfs and apt downloads, uploads `NEXUS-OS_<version>_radxa-zero3.img.xz` under Actions. Pushing a tag like `v0.1` also publishes it under Releases.
- `.gitattributes`: forces Linux line endings so scripts written on Windows don't break the build.
- `.gitignore`: ignores build output and Windows clutter.
- `docs/FLASHING.md`: full install guide: push in GitHub Desktop, wait for the build, download, flash to the boot micro SD, first boot, set up the NEXUS-SD USB drive.

## Still to do in Phase 1

- First GitHub build must go green.
- Elijah flashes it and confirms it boots to the XFCE desktop.

## Known issues and risks

- Armbian clones its desktop definitions (`armbian/configng`) from its `main` branch during the build, so that part isn't pinned. If a build suddenly breaks without us changing anything, this is a likely cause.
- Wi-Fi/Bluetooth chip (AIC8800) on the mainline kernel comes from an Armbian extension. Might be less solid than on the vendor kernel.
- The OS now runs from the micro SD card all the time, so a slow card makes the whole deck feel slow. Use an A2-rated card.
- The Python, shell and theme checks for the 2026-10-04 changes could not be run on Elijah's PC (no Python or bash on Windows). The prototype workflow's check job runs them on GitHub.

## Needs device test

- [ ] Boots from the micro SD card to the Armbian setup wizard, then to the XFCE desktop
- [ ] Restarts fine from the same card (second boot also reaches the desktop)
- [ ] Screen shows 1024x600 correctly
- [ ] Touchscreen moves the pointer / taps
- [ ] Keyboard and trackpad work
- [ ] Wi-Fi connects
- [ ] Bluetooth finds devices
- [ ] Sound plays through the headphone jack
- [ ] Hostname is `nexus` and `/etc/nexus/version` exists

## Prototype: needs device test

- [ ] Prototype build goes green on GitHub
- [ ] Boots with the amber grid-sweep boot animation (from the second boot; the first boot sets it up)
- [ ] Themed login screen with the callsign header
- [ ] Desktop: bottom taskbar, NEXUS start button, HUD widgets top-left and top-right
- [ ] Super opens the start menu; Super + I/A/H/G/T/K/L, Print and Super + Shift + S work
- [ ] Every app in the prototype README table opens
- [ ] Settings: each of the 11 categories opens; Wi-Fi connect, Bluetooth pair, volume, colour preset switch
- [ ] Quick Settings tiles and sliders
- [ ] Controller: Select + Start held 2 seconds toggles mouse mode
- [ ] Touch: long-press gives a right-click
- [ ] Storage page shows "Boot microSD card" usage and a "Storage drive (NEXUS-SD)" section, with no eMMC wording
- [ ] USB drive: Prepare storage drive lists only the USB drive (never the boot micro SD), formats it after typing ERASE, and `ROMs`, `Files`, `Minecraft`, `Snapshots` appear on it
- [ ] USB drive: after logging out and in, Documents/Downloads/Pictures point at the drive, and the `ROMs` share is reachable from Windows
- [ ] USB drive: restart with it plugged in, it mounts at `/mnt/sdcard` by itself; unplugged, the deck still boots normally
- [ ] USB drive: plugged in after boot, Storage page shows "Mount" and it works
- [ ] Snapshots: Settings > Update & backup > Take one now saves to the drive
- [ ] Pico lid sensor and battery level (once the Pico is wired)
- [ ] Deck button test (Settings > Bluetooth & devices > Controller): D-pad up lights
- [ ] Deck button test: D-pad down lights
- [ ] Deck button test: D-pad left lights
- [ ] Deck button test: D-pad right lights
- [ ] Deck button test: A lights
- [ ] Deck button test: B lights
- [ ] Deck button test: X lights
- [ ] Deck button test: Y lights
- [ ] Deck buttons move through the ES-DE game list and A opens a game, B goes back
- [ ] Deck buttons work in a RetroArch game (D-pad moves, A/B/X/Y match their positions)
- [ ] Unplugging the Pico while holding a deck button doesn't leave it stuck pressed
- [ ] Pausing the Pico sensor stops the deck buttons; Resume brings them back

## Questions to settle in later phases

- Third-party app sources (FreeTube, Legcord, ES-DE, Prism, VS Code, Tailscale, libretro cores): OK to use pinned versions from the makers' own sites/repos? (Phase 2)
- Extra packages implied by the spec: Samba, gvfs-backends, openssh-server, ufw, unattended-upgrades, RustDesk (Phase 2)
- Preset "style" differences (rounded vs sharp, rings, scope sweep): only HUD + wallpaper, windows always square? (Phase 3)
- Timeshift saves to `/mnt/sdcard/timeshift/`, not `/mnt/sdcard/Snapshots/`: OK?
- Quick Settings "hotspot" tile: connect to phone hotspot, or make the deck a hotspot? (Phase 5)
- Weather source: Open-Meteo (free, no account)? (Phase 4)
- Deck buttons in `SPEC.md`: add them to the Desktop and controls section when the main build reaches Phase 6?
