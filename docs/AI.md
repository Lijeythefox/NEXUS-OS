# Iris on NEXUS OS

Iris is Elijah's AI assistant. On NEXUS OS it works in two ways:

1. **Home PC (big model).** The home PC (RTX 4060) runs the full Iris through Open WebUI. NEXUS opens it in its own window. Best answers. Needs a connection to the PC (home network, or Tailscale when away).
2. **On the deck (small model).** A small language model running on the deck itself. Works with no internet at all. Shorter, simpler answers, but always there.

NEXUS picks automatically: home PC when it can be reached, otherwise the deck's own model.

```
            Super + I  or  the Iris app
                       │
                nexus-iris / nexus-ask
                       │
        home PC reachable within 2 s? ──── yes ──► Open WebUI on the home PC
                       │                          (via home Wi-Fi or Tailscale)
                       no
                       │
        offline model installed? ───────── no ──► "Iris can't reach the home PC,
                       │                           and no offline model is installed"
                      yes
                       │
        battery over 20 %? ──────────────── no ──► "Battery too low for offline Iris"
                       │
                      yes
                       ▼
        nexus-ai-server (starts if needed) ──► small model on the deck
```

## Stage 1: Iris through the home PC (phase 4)

### What gets built

| Piece | File | Does |
| --- | --- | --- |
| Iris app | `overlay/usr/share/applications/nexus-iris.desktop` | Launcher entry "Iris" |
| `nexus-iris` | `overlay/usr/local/bin/nexus-iris` | Opens the Open WebUI address in a Chromium app window (`chromium --app=URL`, own window, no tabs or address bar) |
| Setting | `iris_url` in `~/.config/nexus/settings.conf` | The address, e.g. `http://elijah-pc:3000` (Tailscale name) |
| Menu entry | NEXUS menu › Setup › Iris | Set the address, test the connection |
| Tailscale | Preinstalled (phase 4) | Reaches the home PC from anywhere with no port forwarding |

### Setting it up

On the home PC (once):

1. Open WebUI running and reachable on the PC's network (it usually listens on port 3000 or 8080).
2. Install Tailscale on the PC and sign in.

On NEXUS:

1. Open a terminal: `sudo tailscale up`, open the link it shows, sign in with the same account.
2. NEXUS menu › Setup › Iris › Address: type `http://<pc-tailscale-name>:<port>`.
3. "Test connection" shows ✓ or what went wrong.

**Open decision:** the exact address and port of Open WebUI on the home PC. Needed for phase 4.7.

## Stage 2: offline Iris on the deck (phase 7)

### What gets built

| Piece | File | Does |
| --- | --- | --- |
| Model server | `nexus-ai-server` + a systemd **user** unit `nexus-ai.service` | Runs the local model with an OpenAI-style web API on `127.0.0.1:8088` (only the deck itself can reach it). Starts on the first question, stops after 10 idle minutes to give the memory back |
| Engine | `llama.cpp` (`llama-server`) on every board; on RK3588 also **RKLLM** (uses the NPU) | Picked from the board file |
| Model manager | `nexus-ai-models` + `config/ai-models.txt` | Lists models that suit this board, downloads to `/mnt/sdcard/models/`, checks the SHA-256, removes |
| Auto-switch | `nexus-iris` | Home PC if it answers within 2 s, else local. Window title says "Iris · home PC" or "Iris · on this deck" |
| Quick ask | `nexus-ask`, Super + I | One-line prompt (fuzzel). Answer appears as a notification with "Open in Iris" |
| Local chat window | `nexus-iris` (local mode) | Open WebUI pointed at the local server, **or** a small built-in chat page if Open WebUI is too heavy for the deck (decided in phase 7 after measuring) |
| Benchmark | `nexus-bench --ai` | Tokens per second for the installed model |

### Rules for the local model

- **Nothing runs until you ask.** No background AI eating memory or battery.
- **Stops after 10 idle minutes.**
- **Won't start under 20 % battery** (says so instead).
- **Pauses while a game is fullscreen** so games stay smooth.
- **Models are never in the image.** They're big (1–2.5 GB), so they're downloaded from the menu onto the SD card. The image stays small.
- **Private by design:** the server only listens on the deck itself (`127.0.0.1`).

### Which model

Small models that run well on deck-class hardware (1–3 billion parameters, 4-bit compressed "Q4" versions):

| Model | Size on disk (Q4) | Good at | Fits |
| --- | --- | --- | --- |
| Llama 3.2 1B Instruct | ~0.8 GB | Quick answers, fastest | Every candidate board |
| Qwen2.5 1.5B Instruct | ~1 GB | General chat, a bit of code | Every candidate board |
| DeepSeek-R1-Distill-Qwen 1.5B | ~1 GB | Step-by-step reasoning (slower answers) | Every candidate board |
| Qwen2.5 3B Instruct | ~2 GB | Better answers, slower | RK3588, Pi 5 (8 GB+) |
| Phi-3 Mini 3.8B | ~2.3 GB | Best quality of the small ones | RK3588 |

The first model offered (default) is chosen in phase 7 after testing on the real board: the best model that reaches the speed target. Rough speeds per board are in [HARDWARE.md § 3.2](HARDWARE.md#32-the-candidates).

**Open decision:** which model is the default (phase 7.2).

### Targets

| | Target |
| --- | --- |
| Speed | 5+ words a second (about 7 tokens a second) |
| First word appears | under 3 s after the server is running; under 15 s from cold (model loading) |
| Desktop while answering | Still smooth (the server runs at lower priority) |
| Memory | Back to normal idle within 1 minute of the server stopping |

### Iris personality

Iris's name and personality (system prompt) are kept the same in both modes, in `/usr/share/nexus/default/iris-system-prompt.txt`, so the local model feels like the same assistant. The user can override it in `~/.config/nexus/iris-system-prompt.txt`.

## Phase 7 device checklist

Copied from [ROADMAP.md](ROADMAP.md#phase-7-offline-ai-on-the-deck-ml):

- [ ] With Wi-Fi off, Super + I answers using the local model.
- [ ] With the home PC reachable, Iris uses the PC.
- [ ] Local speed at least 5 words a second.
- [ ] Desktop stays smooth while the model answers.
- [ ] Server stops by itself after 10 idle minutes.

## Not planned (for now)

- Voice input/output (could come after 2.0; would need a microphone in the deck).
- Iris controlling the desktop (opening apps, changing settings). Possible later through `nexus-*` commands, but it needs careful limits.
- Running the AI on the breadboard module's Pico.
