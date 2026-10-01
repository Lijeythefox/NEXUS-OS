# NEXUS OS progress

## Current phase

**Phase 1: Repo skeleton and bare image.** Waiting for the first GitHub build and a device test.

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

## What changed

- `config/board.conf`: board (`radxa-zero3`) and kernel branch (`current`).
- `config/packages.txt`: empty for now; the build already reads it.
- `userpatches/customize-image.sh`: runs inside the image during the build. Copies `overlay/`, installs `packages.txt`, sets hostname `nexus`, writes `/etc/nexus/version`.
- `overlay/etc/nexus/.keep`: placeholder so the overlay folder exists.
- `.github/workflows/build.yml`: builds the image on every push to `main` (or the manual **Run workflow** button). Frees runner disk space, caches Armbian's rootfs and apt downloads, uploads `NEXUS-OS_<version>_radxa-zero3.img.xz` under Actions. Pushing a tag like `v0.1` also publishes it under Releases.
- `.gitattributes`: forces Linux line endings so scripts written on Windows don't break the build.
- `.gitignore`: ignores build output and Windows clutter.
- `docs/FLASHING.md`: how to get the image onto the deck.

## Still to do in Phase 1

- First GitHub build must go green.
- Elijah flashes it and confirms it boots to the XFCE desktop.

## Known issues and risks

- Armbian clones its desktop definitions (`armbian/configng`) from its `main` branch during the build, so that part isn't pinned. If a build suddenly breaks without us changing anything, this is a likely cause.
- Wi-Fi/Bluetooth chip (AIC8800) on the mainline kernel comes from an Armbian extension. Might be less solid than on the vendor kernel.
- The board might prefer a bootloader already on the eMMC over the SD card.
- `SPEC.md` still says "flash to the eMMC with balenaEtcher". This needs updating to the SD-card route (waiting for Elijah's OK to edit `SPEC.md`).

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

## Questions to settle in later phases

- Third-party app sources (FreeTube, Legcord, ES-DE, Prism, VS Code, Tailscale, libretro cores): OK to use pinned versions from the makers' own sites/repos? (Phase 2)
- Extra packages implied by the spec: Samba, gvfs-backends, openssh-server, ufw, unattended-upgrades, RustDesk (Phase 2)
- Preset "style" differences (rounded vs sharp, rings, scope sweep): only HUD + wallpaper, windows always square? (Phase 3)
- Timeshift saves to `/mnt/sdcard/timeshift/`, not `/mnt/sdcard/Snapshots/`: OK?
- Quick Settings "hotspot" tile: connect to phone hotspot, or make the deck a hotspot? (Phase 5)
- Weather source: Open-Meteo (free, no account)? (Phase 4)
- How the micro SD gets formatted to ext4 (first-boot step or Settings > Storage)
