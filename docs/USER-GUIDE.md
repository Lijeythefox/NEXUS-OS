# NEXUS OS 2 user guide

How to use NEXUS OS day to day. No Linux knowledge needed.

Chapters marked **(coming in phase N)** describe features that are planned but not in the current image yet. See [ROADMAP.md](ROADMAP.md) for when they arrive.

## Contents

1. [First start](#1-first-start)
2. [The screen](#2-the-screen)
3. [Windows and tiling](#3-windows-and-tiling)
4. [Workspaces](#4-workspaces)
5. [All keyboard shortcuts](#5-all-keyboard-shortcuts)
6. [Opening apps](#6-opening-apps)
7. [Lock screen, sleep and power](#7-lock-screen-sleep-and-power)
8. [Screenshots](#8-screenshots)
9. [Volume and brightness](#9-volume-and-brightness)
10. [Network](#10-network)
11. [The NEXUS menu](#11-the-nexus-menu-coming-in-phase-2) (phase 2)
12. [Themes and wallpapers](#12-themes-and-wallpapers)
13. [Apps and the Install menu](#13-apps-and-the-install-menu-coming-in-phase-4) (phase 4)
14. [Iris (AI)](#14-iris-ai-coming-in-phase-4-and-7) (phases 4 and 7)
15. [Deck features](#15-deck-features-coming-in-phase-6) (phase 6)
16. [Making it your own](#16-making-it-your-own)
17. [Where your files are](#17-where-your-files-are)
18. [When something goes wrong](#18-when-something-goes-wrong)

---

## 1. First start

The install steps for the OptiPlex are in [INSTALL-OPTIPLEX.md](INSTALL-OPTIPLEX.md). To try it on your Windows PC first, see [TEST-IN-VM.md](TEST-IN-VM.md).

The very first time NEXUS starts, Armbian asks a few questions in a black text screen:

1. **New root password.** Root is the all-powerful admin account. Pick a strong password and write it down. You will rarely need it.
2. **Shell:** choose `bash` (press `1`).
3. **Your user account:** your name (for example `elijah`) and a password. This is the password you use on the lock screen every day.
4. **Language and time zone:** it guesses from the internet; press Enter to accept, or pick yours (Hobart is `Australia/Hobart`).

After the last question NEXUS logs the admin account out by itself, logs your account in and shows the **lock screen**. Type your password and press Enter. You are in.

From then on, every start goes straight to the lock screen.

## 2. The screen

```
┌──────────────────────────────────────────────────────────────────────┐
│ ◆  ● ━━ ● ● ●             Tue 25 Nov  14:32            ᛒ  📶  🔊  ⏻  │  ← top bar
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│     ┌───────────────────────┐  ┌───────────────────────────┐         │
│     │                       │  │                           │         │
│     │   window              │  │   window                  │         │
│     │                       │  │                           │         │
│     └───────────────────────┘  └───────────────────────────┘         │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

**Top bar, left:**

- **◆ NEXUS logo.** Click it to open the menu (the small power/tools menu in phase 1, the full NEXUS menu from phase 2).
- **Workspace dots.** Five dots, one per workspace. The one you are on is a wide pill. Dim dots are empty, bright dots have windows in them. Click a dot to go there.

**Top bar, centre:** clock and date. Hover for a calendar.

**Top bar, right:**

| Icon | Shows | Click it to |
| --- | --- | --- |
| Bluetooth ᛒ | On, off or connected device | (phase 2) open Bluetooth settings |
| Network | Wired, Wi-Fi strength or disconnected | (phase 2) open Wi-Fi settings |
| Volume | Level, or muted | Mute / unmute. Scroll on it to change volume |
| Power ⏻ | | Open the power menu |

On the deck, the bar also gets a keyboard button, a battery level and a `BB` chip when the breadboard module is in (phase 6).

## 3. Windows and tiling

NEXUS **tiles** windows: instead of piling up on top of each other, open windows share the screen side by side, with small gaps between them, and resize themselves to fit.

- Open one window: it fills the screen.
- Open a second: the screen splits in two.
- Open a third: the newest half splits again, and so on.
- Close one: the others grow to fill the space.

**Moving around:**

| You want to | Do this |
| --- | --- |
| Pick a window | Move the mouse onto it (focus follows the mouse), or Super + arrow keys |
| Swap two windows | Super + Shift + arrow key |
| Flip a split from side-by-side to top-and-bottom | Super + J |
| Make a window float (free, on top) | Super + V. Again to put it back in the tiles |
| Move a window with the mouse | Hold Super and drag with the left button |
| Resize with the mouse | Hold Super and drag with the right button |
| Fullscreen | Super + F. Again to go back |
| Close | Super + W |

The window you are using has a thin coloured border in the theme's accent colour.

Some small windows float by themselves (pop-ups, the calculator, file pickers, the volume mixer).

## 4. Workspaces

Workspaces are like five separate screens. Keep your code on 1, the browser on 2, music on 3, and so on.

| You want to | Do this |
| --- | --- |
| Go to workspace 3 | Super + 3, or click the third dot |
| Send the current window to workspace 3 | Super + Shift + 3 |
| (Deck, phase 6) next / previous workspace | Swipe in from the right / left screen edge |

Switching slides the screen sideways.

## 5. All keyboard shortcuts

`Super` is the Windows key. Press **Super + K** any time to see this list on screen.

| Shortcut | Action | Works from |
| --- | --- | --- |
| Super + Space | App launcher | Phase 1 |
| Super + Alt + Space | NEXUS menu | Phase 1 (small menu), phase 2 (full) |
| Super + K | Show all shortcuts | Phase 1 |
| Super + Return | Terminal | Phase 1 |
| Super + Shift + B | Browser | Phase 4 |
| Super + Shift + F | Files | Phase 1 |
| Super + Shift + C | VS Code | Phase 4 |
| Super + G | Games (ES-DE) | Phase 4 |
| Super + I | Ask Iris a quick question | Phase 7 |
| Super + W | Close window | Phase 1 |
| Super + F | Fullscreen | Phase 1 |
| Super + V | Float / unfloat window | Phase 1 |
| Super + J | Flip split direction | Phase 1 |
| Super + arrow keys | Move focus | Phase 1 |
| Super + Shift + arrow keys | Swap windows | Phase 1 |
| Super + 1..5 | Go to workspace | Phase 1 |
| Super + Shift + 1..5 | Send window to workspace | Phase 1 |
| Super + mouse drag | Move window (right button resizes) | Phase 1 |
| Super + Escape | Power menu | Phase 1 |
| Super + Ctrl + Space | Next wallpaper | Phase 1 |
| Super + Shift + Ctrl + Space | Theme picker | Phase 3 |
| Super + Shift + K | On-screen keyboard | Phase 6 (deck) |
| Print | Screenshot of the whole screen | Phase 1 |
| Shift + Print | Screenshot of an area | Phase 1 |
| Volume / brightness keys | Change level, a pop-up shows it | Phase 1 |

Shortcuts for things that are not in the image yet show a small "coming in phase N" notification instead of doing nothing.

## 6. Opening apps

Press **Super + Space** (or click nothing and start typing after pressing it):

1. A search box appears in the middle of the screen.
2. Type part of the app's name, like `ter` for Terminal or `thu` for Thunar (files).
3. Press Enter, or click it.

The launcher learns: apps you open often move to the top.

## 7. Lock screen, sleep and power

**Lock screen:** blurred wallpaper, big clock, password box. Type your password, press Enter. A wrong password turns the box's border red.

**Locks by itself** when you leave the computer alone:

| After | What happens |
| --- | --- |
| 4 minutes | Screen dims |
| 5 minutes | Locks |
| 6 minutes | Screen turns off (move the mouse or press a key to wake it) |

The OptiPlex never sleeps by itself. Times can be changed from phase 2 (NEXUS menu › Setup › Idle and lock times).

**Power menu** (Super + Escape, or the ⏻ icon): Lock, Sleep, Restart, Shut down, Log out. Log out takes you back to the lock screen.

## 8. Screenshots

| Key | What it takes |
| --- | --- |
| Print | The whole screen |
| Shift + Print | An area: drag a box with the mouse. Escape cancels |

Every screenshot is saved to `~/Pictures/Screenshots/` (the `Pictures/Screenshots` folder in your home folder) **and** copied, so you can paste it straight into a chat or document. A notification confirms it.

## 9. Volume and brightness

The keyboard's volume keys (or the deck's) change the volume, and a pop-up near the bottom of the screen shows the level. Mute shows a crossed-out speaker. You can also scroll on the volume icon in the bar.

Brightness keys work the same way on screens that support it (laptops and the deck; normal monitors use their own buttons).

## 10. Network

- **Wired:** plug in a cable; it connects by itself.
- **Wi-Fi in phase 1:** open a terminal (Super + Return) and type `nmtui`, then pick "Activate a connection". Use the arrow keys and Enter. From phase 2 this is in the NEXUS menu.

## 11. The NEXUS menu (coming in phase 2)

Open with **Super + Alt + Space** or click the **◆** logo. It looks like the launcher: type to filter, Enter or click to choose, Escape to close. "‹ Back" goes up one level.

| Section | What's in it |
| --- | --- |
| Apps | Opens the app launcher |
| Style | Theme, wallpaper, font size, low-effects mode, animations on/off |
| Setup | Wi-Fi, Bluetooth, sound, display, idle and lock times, keyboard layout, time zone, Iris, (deck) modules and SD card |
| Install | Optional apps, one tap to install or remove (phase 4) |
| Update | Install updates, NEXUS version |
| Tools | Screenshot, colour picker, show shortcuts, restart the bar |
| Power | Lock, sleep, restart, shut down, log out |

**Wi-Fi:** pick a network (bars show signal strength), type the password, done. A notification says if it worked. "Forget" removes a saved network.

**Bluetooth:** Scan (10 seconds), pick a device to pair and connect. Controllers like the 8BitDo Zero 2: hold the pairing button on the controller first. Battery level shows for devices that report it.

## 12. Themes and wallpapers

**Now (phase 1):** Tokyo Night theme, three wallpapers. **Super + Ctrl + Space** switches to the next wallpaper.

**From phase 3:** six themes, switched in about a second with no logout:

| Theme | Feel |
| --- | --- |
| Tokyo Night (default) | Deep navy, soft blue and purple |
| Catppuccin Mocha | Warm dark, pastel accents |
| Gruvbox Dark | Retro brown and orange |
| Nord | Cool grey-blue |
| Everforest | Muted green |
| Rosé Pine | Dusky purple and rose |

Pick one with **Super + Shift + Ctrl + Space** or NEXUS menu › Style › Theme. Everything changes colour together: bar, borders, terminal, notifications, launcher, lock screen.

**Low-effects mode** (Style menu) turns off blur and shadows and shortens animations. Use it if things ever feel slow. It is on by itself on the deck.

Command-line version (works now): `nexus-theme list` shows themes, `nexus-theme set tokyo-night` switches.

## 13. Apps and the Install menu (coming in phase 4)

**Preinstalled:**

| For | App |
| --- | --- |
| Web | Chromium |
| Code | VS Code |
| Games you make | Godot 4 |
| Pico | Thonny, mpremote, picotool |
| Python | python3, pip, venv, pipx |
| Minecraft | Prism Launcher (Java 21) |
| Retro games | ES-DE + RetroArch |
| VPN to home | Tailscale |
| Remote shell | SSH (server off until you switch it on) |
| AI | Iris |
| Terminal tools | btop, fastfetch, lazygit, git, ripgrep, fd, bat, fzf |
| Everyday | Thunar (files), imv (pictures), mpv (video, music), Evince (PDF), Mousepad (notes), Calculator |

**Install menu** (NEXUS menu › Install): KiCad, Arduino IDE 2 (PC only), Bambu Studio (PC only), LibreOffice, FreeTube, Legcord (Discord), Remmina, Timeshift, a Samba share for your ROMs folder. One tap installs; tap again to remove. A terminal window shows the progress.

**Minecraft:** open Prism Launcher, sign in with your Microsoft account, make a Fabric instance with the same version as your server, then Add Server.

## 14. Iris (AI) (coming in phase 4 and 7)

Iris is your AI assistant. Full details: [AI.md](AI.md).

- **Phase 4:** the Iris app opens Open WebUI from your home PC in its own window. Set the PC's address once in NEXUS menu › Setup › Iris. Works at home, and away from home through Tailscale.
- **Phase 7 (deck):** when the home PC can't be reached, Iris uses a small model running on the deck itself, so it still works with no internet. The window title says which one is answering ("Iris · home PC" or "Iris · on this deck").
- **Super + I:** a one-line question box. The answer pops up as a notification with an "Open in Iris" button.

The offline model is downloaded from the menu onto the SD card. It is slower and less clever than the home PC; good for quick questions, code help and notes.

## 15. Deck features (coming in phase 6)

| Feature | How to use it |
| --- | --- |
| Touch | Tap = click, drag = scroll. Swipe in from the left or right edge = change workspace; from the bottom edge = launcher |
| On-screen keyboard | Bar keyboard button or Super + Shift + K |
| Controller as a mouse | Hold Select + Start for 2 s. Left stick moves, A clicks, B right-clicks. Turns itself off in games. Same again to stop |
| Lid | Close = sleep. Open = lock screen |
| Battery | In the bar. Warnings at 15 % and 5 % |
| SD card | NEXUS menu › Setup › Prepare SD card (once). Then put ROMs in `/mnt/sdcard/ROMs`, files in `/mnt/sdcard/Files` |
| Controller modules | Slide an 8BitDo tray into a slot; pair once in Bluetooth |
| Breadboard module | Snap it into both slots (see below) |

### Breadboard module

1. Snap the module into both slots. A notification says "Breadboard module connected" with three buttons: **Thonny**, **Terminal** (opens `mpremote`), **Flash .uf2**.
2. Set each power rail with its switch: **3.3V**, **5V**, or **ADJ** (then turn that rail's knob).
3. The `BB` chip in the bar shows each rail's voltage, top rail first (for example `5V · 1.8V`). Click it for current, a rails on/off switch and the Pico tools.
4. If a rail draws too much current (a short), its fuse cuts it and a red notification names the rail. Fix the circuit, then switch the rail back on from the `BB` chip.
5. To flash new firmware: hold BOOT, tap RESET, then **Flash .uf2** and pick the file.

## 16. Making it your own

Your own settings go in files that NEXUS never overwrites:

| To change | Edit this file | Example |
| --- | --- | --- |
| Shortcuts | `~/.config/hypr/hyprland.lua` (a separate `~/.config/hypr/bindings.lua` is planned for phase 2) | `hl.bind("SUPER + M", hl.dsp.exec_cmd("mpv ~/Music"))` |
| Anything in Hyprland | `~/.config/hypr/hyprland.lua` (add lines **after** the `dofile` line) | `hl.config({ general = { gaps_out = 20 } })` |
| Monitors | `~/.config/hypr/hyprland.lua` | `hl.monitor({ output = "HDMI-A-1", mode = "1920x1080@60", position = "0x0", scale = 1 })` |
| Things to start at login | `~/.config/hypr/hyprland.lua` | `hl.on("hyprland.start", function() hl.exec_cmd("thunar --daemon") end)` |

To open a file: `mousepad ~/.config/hypr/bindings.lua` in a terminal. Changes apply when you save (Hyprland reloads by itself). If you make a mistake, a red error bar appears at the top of the screen saying which line; fix it and save again.

`~` means your home folder, for example `/home/elijah`.

## 17. Where your files are

| What | Where |
| --- | --- |
| Your files | `/home/<you>/` (Documents, Downloads, Pictures, Music, Videos) |
| Screenshots | `~/Pictures/Screenshots/` |
| Your settings | `~/.config/` |
| Current theme files (made by NEXUS; don't edit, they are rebuilt) | `~/.config/nexus/current/` |
| Desktop log (for problems) | `~/.cache/nexus/hyprland.log` |
| SD card (deck) | `/mnt/sdcard/` |

## 18. When something goes wrong

**Something looks wrong or broken:** open a terminal and run these, then send Elijah's Claude the output (a photo of the screen is fine):

```
nexus-bench
hyprctl configerrors
tail -n 50 ~/.cache/nexus/hyprland.log
```

**The desktop doesn't start** and you see a message like "the desktop failed to start 3 times": you are at a text prompt, logged in.

- `cat ~/.cache/nexus/hyprland.log` shows why.
- `nexus-session` tries again.
- If your own `~/.config/hypr/` files are the problem: `mv ~/.config/hypr ~/.config/hypr.broken` then `nexus-session` starts with the defaults.

**Stop the desktop starting by itself** (to fix something from the text screen): `touch ~/.config/nexus/no-desktop`. Delete that file to turn it back on.

**Bar disappeared:** `nexus-bar` in a terminal (or NEXUS menu › Tools › Restart the bar, phase 2).

**Frozen screen:** press Ctrl + Alt + F2 for a text screen, log in, run `sudo reboot`.

**Turn off auto-login** (to share the computer): `sudo touch /etc/nexus/no-autologin`. A normal text login appears instead; after logging in, the desktop starts.

More help: [TESTING.md › Reporting a problem](TESTING.md#reporting-a-problem).
