# NEXUS OS documentation

Every document, what it is for, and who it is written for.

## For using NEXUS OS

| Document | What's in it |
| --- | --- |
| [USER-GUIDE.md](USER-GUIDE.md) | Everyday use: unlocking, the bar, launcher, menu, shortcuts, windows, workspaces, files, Wi-Fi, screenshots, updates, what to do when something breaks |
| [INSTALL-OPTIPLEX.md](INSTALL-OPTIPLEX.md) | Downloading the image, flashing it, BIOS settings, first boot, installing to the internal drive |
| [FLASHING.md](FLASHING.md) | Putting NEXUS onto the cyberdeck (draft until the deck board is chosen) |
| [TEST-IN-VM.md](TEST-IN-VM.md) | Running each new build in VMware on Windows |

## For building and changing NEXUS OS

| Document | What's in it |
| --- | --- |
| [../SPEC.md](../SPEC.md) | The specification: what NEXUS OS must do and look like (source of truth) |
| [ROADMAP.md](ROADMAP.md) | The full plan, phase by phase: tasks, files, tests, device checklists, "done when" |
| [ARCHITECTURE.md](ARCHITECTURE.md) | How it fits together: build pipeline, image contents, boot chain, session start, config layers, theme system, every `nexus-*` command |
| [DEVELOPER-GUIDE.md](DEVELOPER-GUIDE.md) | How to make changes: add a theme, an app, a shortcut, a command; tests; releases; working with Claude Code |
| [TESTING.md](TESTING.md) | The four ways to test (GitHub check, browser simulator, VM, real hardware) and how to report a problem |
| [HARDWARE.md](HARDWARE.md) | OptiPlex, the cyberdeck parts, choosing the deck board, breadboard module, Pico lid sensor |
| [AI.md](AI.md) | How Iris (the AI assistant) works: home PC first, small model on the deck when offline |
| [DECISIONS.md](DECISIONS.md) | Every important decision, why it was made, and what would change it |
| [GLOSSARY.md](GLOSSARY.md) | Plain-words meanings of the technical terms used in these docs |
| [../PROGRESS.md](../PROGRESS.md) | Where the project is right now |
| [superpowers/plans/](superpowers/plans/) | Step-by-step build plans Claude writes for each phase |

## Reading order for someone new

1. [`../README.md`](../README.md): what NEXUS OS is.
2. [USER-GUIDE.md](USER-GUIDE.md): what it is like to use.
3. [ROADMAP.md](ROADMAP.md): what is finished and what comes next.
4. [ARCHITECTURE.md](ARCHITECTURE.md), then [DEVELOPER-GUIDE.md](DEVELOPER-GUIDE.md): before changing anything.
