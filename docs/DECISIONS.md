# Decisions

Every important choice about NEXUS OS 2, why it was made, and what it would take to change it. New decisions go at the bottom with the next number. A decision is never deleted; if it changes, it gets a new entry and the old one is marked **Replaced by D-xx**.

Status: **Decided** (Elijah agreed) · **Provisional** (made while building, Elijah's OK still needed) · **Open** (not decided yet)

| # | Decision | Status |
| --- | --- | --- |
| D-01 | Rebuild as an Omarchy-style calm tiling desktop | Decided |
| D-02 | Keep Armbian + Debian 13 + GitHub Actions as the base | Decided |
| D-03 | Hyprland from trixie-backports with a Lua config | Decided |
| D-04 | No login manager: auto-login, then the lock screen | Decided |
| D-05 | No screenless desktop run in the GitHub check | Provisional |
| D-06 | Custom workspace dots in the bar | Provisional |
| D-07 | `start-hyprland` instead of `uwsm` | Provisional |
| D-08 | Quiet boot and splash left for the polish phase | Provisional |
| D-09 | Support packages not named in the spec | Provisional |
| D-10 | Wallpapers generated from theme colours | Decided |
| D-11 | VMware (not VirtualBox) for testing on Windows | Decided |
| D-12 | Browser simulator for trying the look | Decided |
| D-13 | Swappable module slots and the breadboard module | Decided |
| D-14 | Self-designed case, built as a Fusion 360 script | Decided |
| D-15 | Deck board decided later, before the deck phase | Decided |
| D-16 | Offline AI on the deck as well as the home PC | Decided |
| D-17 | Eight phases instead of six | Decided |
| D-18 | Documentation lives in this repo | Decided |
| D-19 | Case files kept under `docs/hardware/case/` | Provisional |
| D-20 | Which deck board | **Open** |
| D-21 | Iris address on the home PC | **Open** |
| D-22 | Default offline model | **Open** |
| D-23 | Home PC Windows Home or Pro (remote desktop choice) | **Open** |

---

### D-01 Omarchy-style calm tiling desktop

- **Decided:** November 2026, Elijah: *"make it rlly smooth and not that tactical neon look make it like an omarchy clone … using my preferences and what I like."* Chose tiling like real Omarchy.
- **What it means:** Hyprland, gaps, rounded corners, soft animations, calm themes (Tokyo Night default), a launcher and a keyboard-first workflow, filled with Elijah's own tools (Pico, Godot, Minecraft, retro games, Iris).
- **Replaces:** v1's XFCE + neon tactical HUD (kept on the `tactical-v1` branch).

### D-02 Keep the existing base

- **Decided:** Elijah chose "clone it on the current base".
- **Why:** The Armbian + GitHub Actions pipeline already worked in v1, builds for both x86 and ARM boards, and Elijah's Windows PC can't build images. Switching to Arch (what Omarchy uses) would mean starting the pipeline from zero and losing ARM board support.
- **Cost:** Debian stable is older than Arch, so Hyprland comes from backports (D-03).

### D-03 Hyprland from trixie-backports, Lua config

- **Why:** Debian 13's own Hyprland is too old for the look; backports has 0.55.x. Only the Hyprland family comes from backports, to keep the rest stable. Newer Hyprland replaced the old `.conf` format with Lua, so NEXUS is written in Lua from the start.
- **Risk:** The Lua API is young and changes between versions. The GitHub check runs `Hyprland --verify-config` against the exact packaged version on every push.

### D-04 No login manager

- **Why:** Saves memory and boot time; the disk isn't encrypted, so a separate login screen *and* a lock screen would be two passwords for no gain. Auto-login on screen 1, Hyprland locks itself before anything else shows.
- **Safety:** `/etc/nexus/no-autologin` switches auto-login off. The 3-failure guard stops a broken desktop from looping.

### D-05 No screenless desktop run in the GitHub check (provisional)

- **What happened:** A test that would start the full desktop on a virtual screen inside GitHub's container was tried during phase 1. It was dropped: Hyprland needs a real display device and login session that the container doesn't have, and the approach couldn't be made to work reliably there.
- **Instead:** the check proves packages install, the config is accepted (`--verify-config`), foot and fuzzel configs are valid, and every command exists. Drawing and smoothness are tested in the VM and on the device.
- **Revisit:** if GitHub ever offers GPU runners, or a reliable headless method appears.

### D-06 Custom workspace dots (provisional)

- **Why:** Waybar's built-in Hyprland workspace module switches workspaces by sending old text-format commands, which Hyprland refuses under a Lua config, so clicking a workspace would do nothing.
- **Instead:** five `custom/ws1..5` bar items, drawn by `nexus-ws-state`, refreshed only when Hyprland reports a change (signal from `events.lua`), switching through `nexus-workspace` with the Lua dispatcher. No polling, no background program.
- **Revisit:** if Waybar adds Lua dispatcher support.

### D-07 `start-hyprland` instead of `uwsm` (provisional)

- **SPEC says:** the session starts through `uwsm`.
- **Built:** Hyprland's own `start-hyprland` launcher, run by `nexus-session`.
- **Why:** fewer moving parts that can't be tested without hardware; `uwsm` adds systemd user-session plumbing that's hard to debug from photos of a screen.
- **Cost:** apps don't get their own systemd scopes (only matters for advanced resource control).
- **Needs:** Elijah's OK to keep it (and then `SPEC.md` updated), or a switch to `uwsm` in any later phase. It's a contained change in `nexus-session`.

### D-08 Quiet boot later (provisional)

- **Why:** While the first images are being debugged, boot messages are useful in photos. Plymouth splash and quiet boot come in the polish phase (phase 8).

### D-09 Support packages (provisional)

- **What:** Packages `SPEC.md` doesn't name but the named parts need with "recommended extras" off: PipeWire and WirePlumber (sound), Mesa (graphics), fonts and icons, `librsvg2-common` (SVG icons), `dbus-user-session`, `polkitd`/`pkexec`, `network-manager`, `wpasupplicant`, `jq`, `procps`, `rtkit`. Full list: `config/packages.txt`.
- **Why:** Without them the desktop starts without sound, icons, network or password prompts.

### D-10 Generated wallpapers

- **Why:** No downloaded images means no licence questions, a smaller repo, and wallpapers that always match the theme. `tools/make-wallpapers.py` draws them during the build.

### D-11 VMware for VM testing

- **Why:** VMware Workstation Pro is free for personal use, has better 3D support for Hyprland than VirtualBox, and opens a `.vmx` with one double-click. GitHub builds the VM (`vm-disk.yml`) so Elijah doesn't convert anything.

### D-12 Browser simulator

- **Why:** Elijah asked for a test environment "like the old NEXUS OS artifact". A browser page anyone can open on any device is the fastest way to try the look and flow before a 2-hour build.
- **Limit:** a model only; real behaviour is tested in the VM and on hardware.

### D-13 Swappable modules and the breadboard module

- **Decided:** Elijah: controller slots become swappable modules; a double-width breadboard module with a full 830-hole breadboard, a built-in microcontroller whose pins form their own section, powered rails, and per-rail 3-way switches (3.3V / ADJ / 5V) each with its own knob.
- **Choices made from that:** Raspberry Pi Pico 2 W as the built-in microcontroller (most general use, MicroPython and C, Wi-Fi), a separate helper chip for safety (e-fuse, sensors) so the rails stay protected when the Pico is reflashed or crashes, magnetic 4-pin pogo connection.
- **Details:** [HARDWARE.md § 4](HARDWARE.md#4-breadboard-module).

### D-14 Self-designed case in Fusion 360

- **Decided:** Elijah: build the case ourselves for creative freedom; *"make it in fusion 360"*.
- **How:** a Fusion 360 Python script (`docs/hardware/case/fusion/NexusCase/NexusCase.py`) with every size in one table, so changing a measurement and re-running rebuilds the parts. Breadboard clips harvested from a bought breadboard.

### D-15 Deck board decided later

- **Decided:** Elijah chose "decide later" (November 2026).
- **Rule:** the plan stays board-neutral; only `config/board.conf` (later `config/boards/`) names a board. The decision is a gate at the start of phase 5.

### D-16 Offline AI on the deck too

- **Decided:** Elijah chose "small model on the deck too" (November 2026).
- **Means:** Iris uses the home PC when reachable and a small local model otherwise ([AI.md](AI.md)). The deck board must be strong enough (RK3588 or Pi 5, see [HARDWARE.md § 3](HARDWARE.md#3-choosing-the-deck-board)); the Radxa Zero 3W is ruled out for this.

### D-17 Eight phases

- **Why:** The original six phases put the board choice, all deck hardware and the breadboard module into one "Deck" phase, and had no place for offline AI. Split into: 5 board choice and bring-up, 6 deck hardware, 7 offline AI, 8 polish. Phases 1–4 are unchanged. Details: [ROADMAP.md](ROADMAP.md).

### D-18 Docs in the repo

- **Decided:** Elijah chose "in the GitHub repo". Docs live in `docs/` next to the code they describe, so they change together. Docs-only pushes don't start the 2-hour build.

### D-19 Case files under `docs/hardware/case/` (provisional)

- **Why:** The case files belong with the project, and anything under `docs/` is skipped by the image build, so updating a print file never starts a 2-hour build. Large STEP files are left out (the script makes them in Fusion).

### D-20 to D-23 Open

| # | Question | Needed by | Options |
| --- | --- | --- | --- |
| D-20 | Deck board | Phase 5 | RK3588 board (recommended) · Raspberry Pi 5 · Pi 5 + AI HAT+ 2 |
| D-21 | Open WebUI address/port on the home PC | Phase 4.7 | Tailscale name + port |
| D-22 | Default offline model | Phase 7.2 | Chosen by testing on the board (see [AI.md](AI.md#which-model)) |
| D-23 | Home PC Windows edition | Only if remote desktop is installed | Home → RustDesk · Pro → Remmina (RDP) |
