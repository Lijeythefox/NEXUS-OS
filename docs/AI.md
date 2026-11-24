# Iris on NEXUS OS

**Iris is the AI on NEXUS OS.** It is Elijah's own desktop companion app, [Lijeythefox/IRIS](https://github.com/Lijeythefox/IRIS): an amber globe of light that lives on the screen, talks back, keeps reminders and to-do lists, draws answers beside what you're reading, and opens apps and files for you. It is built on [Roamies](https://github.com/KenKaiii/Roamies) by Ken Kai (AGPL-3.0).

NEXUS doesn't build its own AI app. It **ships the Iris app**, sets it up for Hyprland, and adds what the deck needs (keys, a local model server for offline use).

> This replaces the earlier plan of opening Open WebUI in a browser window (see [DECISIONS.md](DECISIONS.md) D-24).

## 1. What Iris already does

From the Iris repo (v1.0.2):

| Feature | How |
| --- | --- |
| Talk | Hold Ctrl + Alt and speak, or say "Hey Iris" (wake word runs on the machine) |
| Type | A small text box opens beside the globe |
| Spoken replies | Fish Audio or a Gemini voice (online, your own key) |
| Remembers | Commitments, reminders (once or repeating), facts about you, a to-do list |
| Draws on screen | Cards, steps, graphs, timelines, 3D models beside what you're reading |
| Does things | Opens apps, websites, files and folders; runs commands; searches the web |
| Brain (your choice) | Sign in with Claude or ChatGPT, an API key (Gemini, Grok, Kimi…), or a local model through Ollama, LM Studio or any OpenAI-compatible server (llama.cpp) |
| Lite mode | A lighter Iris for small local models: talk, reminders, to-do list, memory, open things, web search |

Iris is a Tauri app (Rust shell + web pages) with a Node.js helper ("sidecar") and a small voice helper. It already supports Linux, including Wayland sessions like Hyprland.

## 2. How Iris fits Hyprland

Iris's own Linux code (`showcase/tauri/src-tauri/src/linux.rs` in the Iris repo) runs every Iris window through **XWayland**, because a normal Wayland app can't place itself, stay on top or follow the cursor. NEXUS already includes XWayland.

What Wayland takes away, and how NEXUS fills the gap:

| Iris feature | On Hyprland | NEXUS's answer |
| --- | --- | --- |
| Global shortcuts (hold Ctrl + Alt to talk, Ctrl + Shift to type) | Not available to apps on Wayland | **Hyprland binds the keys** and calls Iris's built-in commands: `roamies --talk`, `--ask`, `--summon`, `--panel`, `--list` (made exactly for this) |
| Seeing the pointer over other apps | Not available | Iris knows (it checks the session) and plays drawn steps one after another instead of waiting for clicks |
| Screenshots ("what's on my screen?") | Through the desktop portal | `xdg-desktop-portal-hyprland` (already installed) answers Iris's screenshot request |
| Clicking and typing in other apps | Limited on Wayland | Iris opens apps, files and sites, and runs commands; it won't click inside other apps here |
| Tray icon | Needs a tray | Waybar gets a `tray` module (phase 4) |
| Saved keys and sign-ins | Needs a keyring | `gnome-keyring` + `libsecret-tools` (Iris uses `secret-tool`) |

### Shortcuts

| Shortcut | Calls | Does |
| --- | --- | --- |
| Super + I | `roamies --ask` | Text box to type a question |
| Super + Shift + I | `roamies --talk` | Listen now (press, speak, it stops when you stop) |
| Super + Alt + I | `roamies --panel` | Iris's settings panel |
| Super + Ctrl + I | `roamies --list` | Your to-do list |
| "Hey Iris" | (built in) | Wake word, if switched on in Iris's settings |

### Window rules (`overlay/usr/share/nexus/default/hypr/rules.lua`)

Iris's overlay is a transparent, always-on-top window covering the screen. Hyprland must leave it alone:

- float, pinned on every workspace, no border, no shadow, no blur, no rounding, no open/close animation, never dimmed;
- not focused automatically (so it never steals typing from the app you're in), except the ask box and panel;
- the settings panel is a normal floating window with the theme's border.

The exact window class names are read from `hyprctl clients` on the device in phase 4 and pinned in a test.

## 3. Where Iris's brain runs

```
                         Iris app (on the OptiPlex or the deck)
                                         │
             ┌───────────────────────────┼─────────────────────────────┐
             │                           │                             │
     online sign-in               home PC (Ollama)              on the deck (offline)
  Claude / ChatGPT / API key   over home Wi-Fi or Tailscale    llama-server on 127.0.0.1
   full Iris, best answers       full Iris, private, free       Lite mode, works anywhere
```

Iris has a model picker built in. NEXUS just makes sure the right servers are on the list:

| Brain | Set up by | Mode | When |
| --- | --- | --- | --- |
| Claude or ChatGPT sign-in, or an API key | You, in Iris's panel (Model page) | Full | Online |
| **Home PC**: Ollama on the RTX 4060 (Llama 3.1 8B now; a bigger model if the homelab gets a 3090) | NEXUS adds it as a server (`http://<pc-tailscale-name>:11434`) from NEXUS menu › Setup › Iris | Full (8B is the smallest that drives the full Iris well) | At home, or away through Tailscale |
| **On the deck**: `llama-server` (llama.cpp) running a small model | NEXUS (phase 7): server, model download, Iris server entry | **Lite** | Anywhere, no internet |

**Switching between them:** Iris uses the model you pick. Phase 7 adds a small NEXUS helper, `nexus-iris-brain`, that picks for you when the deck changes network: the home PC when it answers within 2 seconds, otherwise the deck's own model, and it tells Iris through its saved settings. The bar shows a small dot for which brain is active. (If Iris's settings can't be changed safely from outside, this becomes a change in the Iris repo instead; checked at the start of phase 7.)

### Ollama on the home PC

Ollama only listens on the PC itself by default. To let the deck reach it (one-time, on the home PC):

1. Set the environment variable `OLLAMA_HOST=0.0.0.0` (Windows: Settings › System › About › Advanced system settings › Environment Variables › New), then restart Ollama.
2. Set Ollama's context length to **32768** or more. Iris needs that much for the full agent (its instructions and tools alone are about 12.6k tokens): in Ollama's settings, or `OLLAMA_CONTEXT_LENGTH=32768`.
3. Install Tailscale on the PC and sign in. Only your own devices can then reach it.

## 4. Offline Iris on the deck (phase 7)

| Piece | File (NEXUS repo) | Does |
| --- | --- | --- |
| Model server | `overlay/usr/local/bin/nexus-ai-server` + user unit `nexus-ai.service` | Runs `llama-server` (llama.cpp) on `127.0.0.1:8088`, OpenAI-compatible, so Iris can use it like any local server. Starts when Iris first asks, stops after 10 idle minutes |
| Model manager | `nexus-ai-models`, `config/ai-models.txt` | Shows models that suit this board, downloads to `/mnt/sdcard/models/`, checks the SHA-256 |
| Iris entry | done by `nexus-ai-models` | Adds "This deck" (`http://127.0.0.1:8088/v1`) to Iris's server list with Lite mode on |
| Brain switch | `nexus-iris-brain` | See above |
| Benchmark | `nexus-bench --ai` | Tokens per second for the installed model |

On an RK3588 board, RKLLM (the NPU) is faster but isn't OpenAI-compatible out of the box. Phase 7 starts with llama.cpp on the CPU (about 22 tokens/s for a 1.5B model on RK3588 in public tests) and only adds RKLLM if that's too slow.

### Rules for the local model

- Runs only while used; stops after 10 idle minutes.
- Won't start under 20 % battery; pauses while a game is fullscreen.
- Models are downloaded from the menu to the SD card, never put in the image.
- Only listens on the deck itself (`127.0.0.1`).

### Which model

Iris's Lite mode needs a model that **uses tools** and a context of at least **16k tokens** (Iris checks both). Iris's own notes say a model of about 4B can't drive the full Iris, which is why Lite mode exists. Candidates (4-bit "Q4" files):

| Model | Size | Notes |
| --- | --- | --- |
| Qwen2.5 3B Instruct | ~2 GB | Good tool use for its size. Likely default on a Pi 5 |
| Qwen3 4B | ~2.5 GB | Better answers, slower. Likely default on RK3588 16 GB |
| Llama 3.2 3B Instruct | ~2 GB | Tool use supported |
| Qwen2.5 1.5B Instruct | ~1 GB | Fastest; tool use is weaker. Fallback for low memory |

The 16k context costs extra memory on top of the model (roughly 0.5–1 GB at this size), so **an 8 GB board is tight while the desktop and browser are open; 16 GB is recommended**. The default is picked in phase 7 by testing on the real board (decision D-22).

## 5. Getting Iris into the image

Iris's repo builds only a **Windows** installer today (`.github/workflows/build-windows.yml`). The code supports Linux and its fetch scripts already handle `x86_64-unknown-linux-gnu` and `aarch64-unknown-linux-gnu`, so:

1. **In the Iris repo (phase 4):** add `.github/workflows/build-linux.yml` that builds a `.deb` for **amd64** (OptiPlex) and **arm64** (deck), and attaches them to each Iris release.
2. **In NEXUS:** Iris is an extra in the app installer (`overlay/usr/share/nexus/apps.conf`, entry `[iris]`, not ticked by default). `nexus-apps` downloads the newest Iris `.deb` for the machine from the Iris releases, checks its fingerprint and installs it with its dependencies. Until the Iris repo publishes Linux builds, the installer says it can't find one.
3. **Updates:** Iris's own updater is turned off on NEXUS; reinstalling from the picker (or the Update menu, phase 2) gets the newest release.

### Extra packages Iris needs on NEXUS

Ask-first list (they aren't in `SPEC.md` yet; agreed with this plan):

| Package | Why |
| --- | --- |
| `libwebkit2gtk-4.1-0`, `libgtk-3-0` | Tauri draws its windows with WebKitGTK (the biggest addition: roughly 100 MB with its libraries) |
| `libayatana-appindicator3-1` | Iris's tray icon |
| `libasound2` | Voice and sound |
| `xdg-utils` | Opening links and files |
| `gnome-keyring`, `libsecret-tools` | Storing sign-ins and API keys safely |

The Debian package's own dependency list pulls most of these in; the GitHub check installs it in the clean container to prove the list is complete.

### Start-up and memory

Once installed, Iris starts with the desktop (after the lock screen), so the globe is there when you unlock. Its shell and helper are expected to use roughly 200–400 MB of memory, which is a large part of the idle budget (under 700 MB on the OptiPlex, under 600 MB on the deck). Phase 4 measures it with `nexus-bench`. If it doesn't fit, NEXUS menu › Setup › Iris gets a "Start Iris at login" switch (off on the deck), and Super + I starts it on demand.

## 6. Licence

Iris (and Roamies) are AGPL-3.0. Shipping the unchanged `.deb` in NEXUS is fine. NEXUS's `THIRD_PARTY` notes link the Iris source code, and any change NEXUS needs in Iris is made in the Iris repo, where the source is public.

## 7. Phase checklists

**Phase 4 (OptiPlex):**

- [ ] The amber globe appears after unlocking.
- [ ] Super + I opens the text box; Iris answers (sign-in or home PC brain).
- [ ] Super + Shift + I listens and answers.
- [ ] "Open Thunar" (typed or spoken) opens it.
- [ ] "What's on my screen?" works (portal screenshot).
- [ ] Reminders pop up at the right time, including after a restart.
- [ ] The globe never steals typing from the app you're in.
- [ ] Theme borders, blur and animations don't show on Iris's overlay.
- [ ] `nexus-bench` idle memory with Iris running is recorded.

**Phase 7 (deck):**

- [ ] With Wi-Fi off, Super + I gets an answer from the deck's own model (Lite mode).
- [ ] At home, Iris switches back to the home PC by itself.
- [ ] Local speed at least 5 words a second; desktop stays smooth while it answers.
- [ ] The model server stops after 10 idle minutes and memory goes back down.

## 8. Not planned (for now)

- Offline spoken replies (Iris's voices are online services). A local voice would be a change in the Iris repo.
- Clicking inside other apps on Wayland.
- Running AI on the breadboard module's Pico.
