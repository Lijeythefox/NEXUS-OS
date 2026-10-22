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
- `SPEC.md` updated (with Elijah's OK): flashing now goes through a spare SD card, and the Pico also reads the battery voltage.
- 2026-10-22, "more customisable and user friendly" (prototype only, details in `prototype/README.md` > Customising your deck):
  - **App Center** (Settings > Apps): one-tap install/remove of Firefox ESR and extra emulator systems (Atari 2600/7800/Lynx, PC Engine, WonderSwan, Nintendo DS, DOS, ScummVM). Nothing extra is baked into the image. The list is `prototype/overlay/usr/share/nexus/appcenter.conf`.
  - **Web apps** (Settings > Apps): turn a website into a start menu app.
  - **Custom colour preset** (Settings > Personalization): pick your own five colours; builds a sixth preset on the deck.
  - **Window layout**: Stack (Windows style) or Split (Omarchy-style auto tiling). Super + Space, a Quick Settings tile, or Settings > Personalization > Window layout. Runs as a small background helper, `nexus-tiler`.
  - **Your own shortcuts** (Settings > Bluetooth & devices > Keyboard).
  - **Welcome tour** on first login (colours, layout, browser, game systems, shortcut cheat sheet).
  - New package: `gir1.2-wnck-3.0` (needed by the window layout helper).
  - The prototype check job now also test-builds a custom preset and checks the App Center list.
  - Tested on the build server: tiling places windows to the pixel at 1024x600 with the real XFCE window manager; every new Settings page and every welcome step opens; core download and error messages work. Not tested: anything that needs the deck (pkexec password prompts, real installs, touch).

## Decisions made

| Topic | Decision |
| --- | --- |
| Base | Armbian build framework pinned to `v26.5.1`, Debian 13 "trixie" (current stable) |
| Kernel | Mainline (`BRANCH=current` in `config/board.conf`) |
| Desktop | XFCE, Armbian's `minimal` desktop tier (apps are added by us in Phase 2) |
| Flashing | Etcher to a spare micro SD, boot it, copy to eMMC with `armbian-install` (see `docs/FLASHING.md`) |
| First boot | Keep Armbian's setup wizard for now (root password, user, locale) |
| Battery level | The Pico will read battery voltage as well as the lid sensor (Phase 6) |
| Repo | Public, so GitHub Actions minutes are free |
| Branding | Armbian `VENDOR` is set to `NEXUS-OS`; hostname is `nexus` |
| Controller mouse mode | Built-in helper `nexus-pad` instead of AntiMicroX (no ARM build). Approved 2026-10-02 |
| PSP and Dreamcast | PPSSPP and Flycast as RetroArch cores (standalone apps not in Debian 13 for ARM). Approved 2026-10-02 |
| Emulator cores | libretro nightly builds for ARM (no stable ARM builds exist). Approved 2026-10-02 |
| Extra packages | The extra packages listed in `prototype/README.md` (Samba, ufw, light-locker, etc.). Approved 2026-10-02 |
| Extra apps | Installed on demand from an App Center, not preinstalled. Firefox ESR plus extra emulator systems. Approved 2026-10-22 |
| Customisation | Custom colour preset, your own shortcuts, web apps, first-login welcome tour, Stack/Split window layout. Approved 2026-10-22. Not yet in `SPEC.md` |

## What changed

- `config/board.conf`: board (`radxa-zero3`) and kernel branch (`current`).
- `config/packages.txt`: empty for now; the build already reads it.
- `userpatches/customize-image.sh`: runs inside the image during the build. Copies `overlay/`, installs `packages.txt`, sets hostname `nexus`, writes `/etc/nexus/version`.
- `overlay/etc/nexus/.keep`: placeholder so the overlay folder exists.
- `.github/workflows/build.yml`: builds the image on every push to `main` (or the manual **Run workflow** button). Frees runner disk space, caches Armbian's rootfs and apt downloads, uploads `NEXUS-OS_<version>_radxa-zero3.img.xz` under Actions. Pushing a tag like `v0.1` also publishes it under Releases.
- `.gitattributes`: forces Linux line endings so scripts written on Windows don't break the build.
- `.gitignore`: ignores build output and Windows clutter.
- `docs/FLASHING.md`: full install guide: push in GitHub Desktop, wait for the build, download, flash to SD, first boot, copy to eMMC, set up the personal micro SD card.

## Still to do in Phase 1

- First GitHub build must go green.
- Elijah flashes it and confirms it boots to the XFCE desktop.

## Known issues and risks

- Armbian clones its desktop definitions (`armbian/configng`) from its `main` branch during the build, so that part isn't pinned. If a build suddenly breaks without us changing anything, this is a likely cause.
- Wi-Fi/Bluetooth chip (AIC8800) on the mainline kernel comes from an Armbian extension. Might be less solid than on the vendor kernel.
- The board might prefer a bootloader already on the eMMC over the SD card.
- Prototype: Split layout moves windows with the window manager's normal "move/resize" requests. A few apps with a large minimum size (e.g. LibreOffice) may not shrink fully into a small stack slot on 1024x600.
- Prototype: App Center emulator cores are libretro nightlies, fetched at install time, so two decks can end up with slightly different core versions.
- Prototype: GTK's blue "suggested action" button colour still shows in some older confirm dialogs (not from a preset). New buttons use the preset colour instead.

## Needs device test

- [ ] Boots from SD card to the Armbian setup wizard, then to the XFCE desktop
- [ ] Screen shows 1024x600 correctly
- [ ] Touchscreen moves the pointer / taps
- [ ] Keyboard and trackpad work
- [ ] Wi-Fi connects
- [ ] Bluetooth finds devices
- [ ] Sound plays through the headphone jack
- [ ] Hostname is `nexus` and `/etc/nexus/version` exists
- [ ] `armbian-install` copies the system to the eMMC and it boots without the SD card

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
- [ ] Micro SD: Settings > System > Storage > Prepare card, then games/files/snapshots folders appear
- [ ] Pico lid sensor and battery level (once the Pico is wired)
- [ ] Welcome tour appears on first login and each step works
- [ ] App Center: Firefox ESR installs, opens, becomes default, removes
- [ ] App Center: an emulator pack installs and its games show in ES-DE
- [ ] Web apps: add one, it appears in the start menu and opens in its own window
- [ ] Custom colour preset: save, everything recolours, remove again
- [ ] Window layout: Split tiles windows, Super + Arrows/Enter/F/W/Space work, Quick Settings tile works
- [ ] Your own shortcut: add one that opens an app, it works, remove it

## Questions to settle in later phases

- Third-party app sources (FreeTube, Legcord, ES-DE, Prism, VS Code, Tailscale, libretro cores): OK to use pinned versions from the makers' own sites/repos? (Phase 2)
- Extra packages implied by the spec: Samba, gvfs-backends, openssh-server, ufw, unattended-upgrades, RustDesk (Phase 2)
- Preset "style" differences (rounded vs sharp, rings, scope sweep): only HUD + wallpaper, windows always square? (Phase 3)
- Timeshift saves to `/mnt/sdcard/timeshift/`, not `/mnt/sdcard/Snapshots/`: OK?
- Quick Settings "hotspot" tile: connect to phone hotspot, or make the deck a hotspot? (Phase 5)
- Weather source: Open-Meteo (free, no account)? (Phase 4)
- How the micro SD gets formatted to ext4 (first-boot step or Settings > Storage)
