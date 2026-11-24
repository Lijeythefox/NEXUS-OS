# NEXUS OS

A fast, minimal, smooth Linux desktop for Elijah's handheld **cyberdeck**, in the style of [Omarchy](https://omarchy.org): tiling windows that glide into place, calm themes, keyboard-first, and filled with his own tools (Godot, Pico, Minecraft, retro games, AI).

It is built entirely on GitHub (never on a home PC) and comes out as one image file you flash to a USB stick or SD card.

| | |
| --- | --- |
| **Version** | NEXUS OS 2 (development builds `2.0-dev-…`) |
| **Runs on now** | Dell OptiPlex 3060 SFF (normal PC, `uefi-x86`) |
| **Runs on later** | The cyberdeck (ARM board, chosen before roadmap phase 5) |
| **Built from** | Armbian build framework + Debian 13 "trixie" + Hyprland |
| **Current phase** | Phase 1 (smooth desktop) built, waiting for a real-hardware test. See [`PROGRESS.md`](PROGRESS.md) |

## Start here

| I want to… | Read |
| --- | --- |
| Install it on the OptiPlex | [`docs/INSTALL-OPTIPLEX.md`](docs/INSTALL-OPTIPLEX.md) |
| Try it without a USB stick | [`docs/TEST-IN-VM.md`](docs/TEST-IN-VM.md) (VMware) or the browser simulator (link in [`docs/TESTING.md`](docs/TESTING.md)) |
| Learn how to use it | [`docs/USER-GUIDE.md`](docs/USER-GUIDE.md) |
| See what's planned and in what order | [`docs/ROADMAP.md`](docs/ROADMAP.md) |
| Understand how it's built | [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) |
| Change something / add a feature | [`docs/DEVELOPER-GUIDE.md`](docs/DEVELOPER-GUIDE.md) |
| Everything else | [`docs/README.md`](docs/README.md) (full index) |

## The rules in one place

- [`SPEC.md`](SPEC.md) says **what** NEXUS OS must do. It wins any disagreement.
- [`docs/ROADMAP.md`](docs/ROADMAP.md) says **in what order** it gets built.
- [`PROGRESS.md`](PROGRESS.md) says **where things are right now**.
- [`CLAUDE.md`](CLAUDE.md) is the instruction sheet Claude Code reads before working on the repo.

## Old version

The first, "tactical" NEXUS OS (XFCE desktop, amber HUD, Windows-style Settings app) is kept on the [`tactical-v1`](https://github.com/Lijeythefox/NEXUS-OS/tree/tactical-v1) branch.
