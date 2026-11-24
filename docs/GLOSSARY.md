# Glossary

Plain-word meanings of the terms used in the NEXUS docs.

| Term | Meaning |
| --- | --- |
| **Armbian** | A build system that makes Debian Linux images for small boards and PCs. NEXUS uses it to make its image |
| **Artifact (GitHub)** | A file a GitHub Actions run produces, like the `.img.xz`. Downloaded from the run's page |
| **Artifact (Claude)** | A web page Claude publishes, like the simulator |
| **apt** | Debian's tool for installing and updating software |
| **Backports** | A Debian repository with newer versions of some programs, built for the stable release. NEXUS only takes the Hyprland family from it |
| **balenaEtcher** | A Windows program that writes an image to a USB stick or SD card |
| **Bar / Waybar** | The thin strip along the top of the screen (clock, workspaces, icons) |
| **Board** | The main computer circuit board (OptiPlex motherboard, Raspberry Pi, RK3588 board…) |
| **`board.conf`** | The only file allowed to name which board the image is for |
| **Buck-boost converter** | A small circuit that turns one voltage into another, higher or lower. Each adjustable breadboard rail has one |
| **Build check / Check NEXUS OS** | The 3-minute GitHub test that runs on every push before the long build |
| **CI** | "Continuous integration": GitHub automatically checking and building the code on every push |
| **CRLF / LF** | The invisible characters at the end of each line. Windows uses CRLF, Linux uses LF. Linux scripts break with CRLF |
| **Debian 13 "trixie"** | The version of Debian Linux NEXUS is built on |
| **Dispatcher** | A Hyprland action, like "close window" or "go to workspace 3" |
| **eMMC** | Storage chip soldered on (or plugged into) a small board, faster than an SD card |
| **ES-DE** | EmulationStation Desktop Edition: the menu for picking retro games |
| **fuzzel** | The pop-up search list used for the launcher and NEXUS menus |
| **GPIO** | General-purpose input/output: the pins on a Pico you can wire things to |
| **Hall sensor** | A tiny chip that notices a magnet nearby. Used to know when the lid is closed |
| **Hyprland** | The program that draws and arranges windows, with the animations. The heart of the NEXUS desktop |
| **hypridle** | Watches for no activity and dims, locks and turns off the screen |
| **hyprlock** | The lock screen |
| **Image (`.img.xz`)** | The whole operating system packed into one compressed file, ready to write to a USB stick or SD card |
| **Iris** | Elijah's AI assistant |
| **llama.cpp** | A program that runs language models on ordinary processors; used for offline Iris |
| **Low-effects mode** | A NEXUS setting with no blur or shadows and shorter animations, for weaker graphics chips |
| **Lua** | A small programming language. Hyprland's settings files are written in it |
| **mako** | Shows notifications (the pop-ups in the top-right) |
| **Mesa** | The open-source graphics drivers |
| **Model (AI)** | The "brain" file of an AI. "1B" means about 1 billion parameters; bigger is smarter but slower |
| **NPU** | A chip made for running AI quickly with little power (the RK3588 has one) |
| **Open WebUI** | The chat web page Iris runs in on the home PC |
| **Overlay** | The `overlay/` folder: files copied straight into the image (`overlay/etc/x` becomes `/etc/x`) |
| **Phase** | One stage of the roadmap. Only one is worked on at a time |
| **Pico / Pico 2 W** | Raspberry Pi's small microcontroller boards. The 2 W has Wi-Fi |
| **Pogo connector** | Spring-loaded pins that touch flat pads; with magnets, modules snap on and connect |
| **Polkit agent** | The pop-up that asks for your password when something needs admin rights |
| **Q4 / quantised** | An AI model squeezed to 4 bits per number so it's smaller and faster, with slightly lower quality |
| **Rail (breadboard)** | The long strips along the edges for power (+) and ground (−) |
| **RKLLM** | Rockchip's software for running language models on the RK3588's NPU |
| **Root** | The admin account that can change anything |
| **Shellcheck** | A tool that finds mistakes in bash scripts |
| **SHA-256** | A fingerprint of a file. If even one byte changes, the fingerprint changes, so downloads can be checked |
| **SPEC** | `SPEC.md`: the description of what NEXUS must do. The final word |
| **Super** | The Windows key |
| **SwayOSD** | The volume/brightness pop-up |
| **systemd** | The part of Linux that starts and stops services |
| **Tailscale** | A private network between your own devices, so the deck can reach the home PC from anywhere |
| **Template** | A config file with `{{placeholders}}` that `nexus-theme` fills with a theme's colours |
| **Theme** | A set of colours in a `theme.conf` file |
| **Tiling** | Windows arranged side by side automatically, instead of overlapping |
| **Token** | A piece of a word an AI reads or writes (about ¾ of a word). "t/s" = tokens per second |
| **TOPS** | Trillion operations per second: a rough measure of an AI chip's speed |
| **tty1** | The first text screen of the computer; NEXUS starts the desktop from it |
| **udev rule** | A rule that runs something when a device is plugged in |
| **UEFI** | The modern start-up firmware in PCs. The OptiPlex uses it |
| **`.uf2`** | The firmware file format you drag onto a Pico in BOOT mode |
| **VM** | Virtual machine: a pretend computer running inside Windows |
| **Wayland** | The modern way Linux programs draw on screen. Hyprland is a Wayland compositor |
| **Workspace** | One of five separate screens you can switch between |
| **XWayland** | Lets older programs (Minecraft, Thonny) run on Wayland |
| **zram** | Compressed memory used as swap, so the system copes better when RAM is full |
