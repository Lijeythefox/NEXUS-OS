# NEXUS OS 2 developer guide

How to change NEXUS OS safely: the workflow, the rules, and step-by-step recipes for the most common jobs. For how the parts fit together, read [ARCHITECTURE.md](ARCHITECTURE.md) first.

This guide is written for Elijah and for Claude. Claude also follows [`CLAUDE.md`](../CLAUDE.md).

## 1. The rules

These come from [`SPEC.md`](../SPEC.md) and [`CLAUDE.md`](../CLAUDE.md). Breaking one usually breaks the image.

| # | Rule | Why |
| --- | --- | --- |
| 1 | `SPEC.md` decides what the OS does. Change it only after asking Elijah | One source of truth |
| 2 | Work on one roadmap phase at a time | Small, testable steps |
| 3 | Never build the image locally; GitHub Actions builds it | Elijah's PC is Windows only |
| 4 | Only the Hyprland family comes from trixie-backports. No testing or unstable | Stable base, fewer surprises |
| 5 | Hyprland's config is Lua (`hl.*`), never the old `.conf` format | Newer Hyprland removed `.conf` |
| 6 | No colour typed anywhere except a `theme.conf` | Themes must switch everything |
| 7 | List every package; recommended extras are off | Small image |
| 8 | Nothing names a board except `config/board.conf` (later `config/boards/`) | Deck board isn't chosen |
| 9 | Test first for anything with logic (`ci/tests.sh`) | Bugs caught before a 2-hour build |
| 10 | Merge to `main` only when the check is green | `main` always builds |
| 11 | Ask before adding packages or features not in `SPEC.md` | Keeps it minimal |
| 12 | Anything not testable without hardware is marked "needs device test" in `PROGRESS.md` | Honest status |
| 13 | Files have Unix line endings (LF), never Windows (CRLF) | Scripts with CRLF fail to run |

## 2. The workflow

```
 branch ──► edit ──► bash ci/check-static.sh ──► push ──► Check NEXUS OS (3 min)
                                                              │ green
                                                              ▼
            Elijah tests ◄── VMware zip ◄── image (2 h) ◄── merge to main
                 │
                 └──► PROGRESS.md + test checklist
```

1. **Branch:** `git checkout -b phase2-menu` (name it after the phase and job).
2. **Write the test first** if the change has logic (see section 4).
3. **Make the change.**
4. **Run the fast check** (if you have Linux or a container): `bash ci/check-static.sh`. It needs `bash`, `shellcheck`, `python3`, `luac5.4` (or `luac`), `jq`. Claude runs this in its own workspace.
5. **Push the branch.** GitHub runs **Check NEXUS OS** (`.github/workflows/check.yml`): the static check plus the desktop check (real package install in a clean Debian 13 container, `Hyprland --verify-config`, foot and fuzzel config checks, every command present).
6. **Green? Merge to `main`.** That runs the check again, then the image build (`build.yml`, about 2 hours), then the VMware machine (`vm-disk.yml`).
7. **Update `PROGRESS.md`** with the phase, what changed, what's left, known issues and "needs device test" items.
8. **Give Elijah a test checklist** (steps he can tick off).

### Getting the image

GitHub → **Actions** → the latest green **Build NEXUS OS** run → **Artifacts** → `NEXUS-OS_<version>_uefi-x86` (a zip with the `.img.xz` inside). The VM is under the **Make VMware disk** run. Tagged releases (`v2.0.0`) are under **Releases**.

### Starting a workflow by hand

- In the browser: Actions → pick the workflow → **Run workflow**.
- From a terminal with `gh`: `gh api -X POST repos/Lijeythefox/NEXUS-OS/actions/workflows/vm-disk.yml/dispatches -f ref=main` (the REST form; Claude's environment can't use `gh workflow run`).

### Commit messages

Short, plain, present tense, saying what changed for the user: `menu: add Wi-Fi connect with password prompt`. Prefix with the area (`menu:`, `theme:`, `build:`, `ci:`, `docs:`, `deck:`).

## 3. Where things go

| You're adding | Put it in |
| --- | --- |
| An app (anything that isn't part of the desktop itself) | `overlay/usr/share/nexus/apps.conf` (installed by `nexus-apps`, never in the image) |
| A Debian package the desktop itself needs | `config/packages.txt` (with a `# why` comment above its group) |
| A Hyprland-family package | `config/packages-backports.txt` |
| A NEXUS command | `overlay/usr/local/bin/nexus-<name>` (bash or Python, `#!/bin/bash` or `#!/usr/bin/python3`, help text at the top) |
| A shortcut | `overlay/usr/share/nexus/default/hypr/bindings.lua` **and** `overlay/usr/share/nexus/default/keys.txt` **and** the table in `SPEC.md` and `docs/USER-GUIDE.md` |
| A window rule | `overlay/usr/share/nexus/default/hypr/rules.lua` |
| Look/animation change | `overlay/usr/share/nexus/default/hypr/looknfeel.lua` (no colours!) |
| A themed config file | `overlay/usr/share/nexus/templates/<file>` with `{{key}}` placeholders |
| A theme | `overlay/usr/share/nexus/themes/<name>/theme.conf` |
| Something that runs at login | `overlay/usr/local/bin/nexus-autostart` |
| A system file | `overlay/etc/…` (copied to `/etc/…`) |
| A starter file for new users | `overlay/etc/skel/…` |
| Build-time setup (services, repos) | `userpatches/customize-image.sh` (in a small named function) |
| A unit test | `ci/tests.sh` |
| A new check | `ci/check-static.sh` (no packages needed) or `ci/desktop-check.sh` (needs the real packages) |

## 4. Writing tests

Tests live in `ci/tests.sh` and run in a plain container with no desktop. The pattern:

```bash
echo "nexus-example"                       # section heading
example_does_the_thing() {                 # one function = one behaviour
	run_something "$T/in" >"$T/out" || return 1
	grep -q 'expected text' "$T/out"
}
check "a clear sentence saying what should happen" example_does_the_thing
```

- `$T` is a fresh temporary folder, `$BIN` is `overlay/usr/local/bin`, `$SHARE` is `overlay/usr/share/nexus`.
- A function passes when it returns 0. On failure, the last 3 lines it printed are shown.
- **Fake the outside world** by putting a fake command first in `PATH`. Example from the workspace-dot tests: a fake `hyprctl` script in `$T/hy` prints fixed JSON, then the test runs `PATH="$T/hy:$PATH" bash "$BIN/nexus-ws-state" 2`.
- Scripts should accept overrides for anything they read from the system (like `nexus-theme --share DIR`), so tests can point them at test files.

**Order:** write the test → run `bash ci/check-static.sh` and see it **fail** for the right reason → write the code → see it **pass** → push.

## 5. Recipes

### 5.1 Add a keyboard shortcut

1. `overlay/usr/share/nexus/default/hypr/bindings.lua`: add a line next to similar ones, e.g.
   `hl.bind(mod .. " + N", run("nexus-notes"))`
2. `overlay/usr/share/nexus/default/keys.txt`: add the line shown by Super + K (keep the columns lined up).
3. `SPEC.md` (ask first) and `docs/USER-GUIDE.md` section 5: add the row.
4. Push. The desktop check runs `Hyprland --verify-config`, which fails on a bad key name or dispatcher.

### 5.2 Add a NEXUS command

1. Test first in `ci/tests.sh` (section 4).
2. Create `overlay/usr/local/bin/nexus-<name>`:
   ```bash
   #!/bin/bash
   # nexus-<name>: one line saying what it does.
   #   nexus-<name> ARG    what ARG does
   set -euo pipefail
   ```
3. Use `nexus-pick` for any list the user chooses from (it gives the theme look and touch support).
4. Use `notify-send` for results the user should see.
5. If the command must exist for the desktop to work, add it to the "commands that must exist" list in `ci/desktop-check.sh`.

### 5.3 Add a package

1. Ask Elijah if it isn't in `SPEC.md`.
2. Find the exact Debian 13 package name on <https://packages.debian.org/trixie/>.
3. Add it to `config/packages.txt` in the right group with a short `# why` comment.
4. Push. The desktop check installs the full list in a clean container; a wrong name or a conflict fails there in about 3 minutes instead of 2 hours into the build.
5. Note the size: `apt-cache show <pkg> | grep Installed-Size`. If it's an app rather than part of the desktop, it belongs in `apps.conf` instead (recipe 5.9).

### 5.4 Add a themed config

1. Copy the program's normal config into `overlay/usr/share/nexus/templates/<file>`.
2. Replace every colour with a placeholder: `{{accent}}`, `{{bg_hex}}`, `{{fg_rgb}}` (see [ARCHITECTURE.md § 4.2](ARCHITECTURE.md#42-templates)).
3. Point the program at `~/.config/nexus/current/<file>` (in its start command or a symlink).
4. If it needs a reload on theme change, add it to `nexus-theme set`.
5. The test `theme_fills_everything` checks no `{{` is left in any rendered file.

### 5.5 Make a new theme

1. Copy `overlay/usr/share/nexus/themes/tokyo-night/` to `overlay/usr/share/nexus/themes/<new-name>/` (lowercase, dashes).
2. Edit `theme.conf`: change `name=` and every colour. Keep all 28 keys; `nexus-theme` refuses a theme with a missing or bad colour.
3. Tips: `bg` darkest, `surface` and `raised` a little lighter each; `fg` should read easily on `bg` (aim for a contrast ratio of at least 7:1); `accent` is the colour you'll see most.
4. Push. Wallpapers are generated during the build. Try it with `nexus-theme set <new-name>`.

### 5.6 Change how the desktop looks or moves

Edit `overlay/usr/share/nexus/default/hypr/looknfeel.lua`. Values are in pixels and milliseconds-ish (Hyprland animation speed is in tenths of a second: `speed = 2` ≈ 200 ms). Keep the low-effects mode in mind: anything heavy (blur passes, big shadows) must be switched off there.

### 5.7 Change what's switched off at boot

`userpatches/customize-image.sh`, function `trim_services`. Measure before and after with `nexus-bench` on the device and record the numbers in `PROGRESS.md`.

### 5.9 Add an app to the installer

1. Open `overlay/usr/share/nexus/apps.conf`. The top of the file explains every setting.
2. Add a section. Examples:
   ```ini
   [blender]
   name = Blender
   about = 3D modelling
   default = no
   apt = blender
   ```
   ```ini
   [obsidian]
   name = Obsidian
   about = notes
   default = no
   github = obsidianmd/obsidian-releases
   amd64_file = _amd64\.deb$
   arm64_file = _arm64\.deb$
   kind = deb
   ```
   Use `arch = amd64` for PC-only apps. `kind = appimage` and `kind = zip` also need `command = <name>`.
3. Check it: `python3 overlay/usr/local/bin/nexus-apps --conf overlay/usr/share/nexus/apps.conf check`, and see what it would do: `... --arch amd64 plan --install blender`.
4. For a download, see which file it would pick: `... --arch arm64 resolve obsidian`.
5. Push. The GitHub check dry-runs every Debian package in the list.
6. If it's one of Elijah's usual apps, set `default = yes` and update the test `apps_defaults_are_elijahs_list` in `ci/tests.sh`.

### 5.8 Add a board (phase 5)

1. `config/boards/<board>.conf`: `BOARD=`, `BRANCH=`, any quirks (display scale, low-effects default, extra firmware).
2. The build matrix picks it up and makes a separate image.
3. Add an arm64 run of the desktop check.
4. Write a flashing section in `docs/FLASHING.md`.

## 6. Hyprland Lua cheat sheet

Hyprland's Lua config is new and changes between versions. Write for the exact version in trixie-backports (0.55.x when phase 1 was built) and let the desktop check prove it.

| Job | Lua |
| --- | --- |
| Settings | `hl.config({ general = { gaps_in = 5 } })` |
| Shortcut | `hl.bind("SUPER + Return", hl.dsp.exec_cmd("foot"))` |
| Window action | `hl.dsp.window.close()`, `hl.dsp.window.float({ action = "toggle" })`, `hl.dsp.window.move({ workspace = 2 })` |
| Focus | `hl.dsp.focus({ direction = "left" })`, `hl.dsp.focus({ workspace = 3 })` |
| Mouse drag | `hl.bind("SUPER + mouse:272", hl.dsp.window.drag(), { mouse = true })` |
| Works on lock screen | add `{ locked = true }` (and `repeating = true` for held keys) |
| Monitor | `hl.monitor({ output = "", mode = "preferred", position = "auto", scale = "auto" })` |
| Environment | `hl.env("XCURSOR_SIZE", "24")` |
| Run on start | `hl.on("hyprland.start", function() hl.exec_cmd("…") end)` |
| React to events | `hl.on("workspace.active", fn)` |
| Window rule | `hl.window_rule({ … })` (see `rules.lua`) |
| Animation | `hl.curve("easeOut", …)`, `hl.animation({ … })` (see `looknfeel.lua`) |

Debug on the device: `hyprctl configerrors`, `~/.cache/nexus/hyprland.log`. Locally: the desktop check's `Hyprland --verify-config` output in the GitHub run log.

**Don't** use `hyprctl dispatch workspace 2`-style text commands from scripts; Hyprland rejects them under a Lua config. Pass a Lua dispatcher instead: `hyprctl dispatch "hl.dsp.focus({ workspace = 2 })"` (see `nexus-workspace`).

## 7. The simulator

The browser simulator (an artifact, `/home/claude/nexus-sim/index.html` in Claude's workspace) copies the desktop's look and behaviour in one HTML page, so Elijah can try changes on any device before an image exists. When a phase changes something visible (menus, themes, bar), update the simulator in the same phase. Its colours come from the same `theme.conf` values.

## 8. Releasing

1. All phase checklists ticked, `PROGRESS.md` up to date.
2. `git tag v2.0.0 && git push origin v2.0.0`.
3. The build publishes the images to **Releases** with their checksums.
4. Write release notes on the release page: what's new, what's known not to work.

Version numbers: `v2.<phase>.<fix>` during development (for example `v2.2.1` = phase 2, first fix), `v2.0.0` for the finished release. (Before the first tag, images are named `2.0-dev-<date>-<commit>`.)
