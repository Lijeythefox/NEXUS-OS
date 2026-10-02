# Installing NEXUS OS

Start to finish: send the recipe to GitHub, let GitHub build the image, put it on a micro SD card, boot the deck from it, then copy it onto the deck's built-in storage (eMMC).

The Radxa Zero 3W's eMMC is soldered to the board, so Windows can't write to it directly. That's why the image goes onto a **spare micro SD card** first.

You need:

- **GitHub Desktop** on your PC (already installed).
- **[balenaEtcher](https://etcher.balena.io/)** on your PC.
- A **spare micro SD card**, 16 GB or bigger. Not your personal-files card: it gets wiped.
- A **keyboard that works without Bluetooth** (USB, or a 2.4 GHz wireless dongle). Bluetooth isn't set up until after first boot.

## 1. Send the latest changes to GitHub

1. Open **GitHub Desktop** and pick the **NEXUS-OS** repository (top left).
2. Click **Publish branch** (the first time) or **Push origin** (after that), top right.
3. This starts the builds on GitHub automatically.

## 2. Wait for the build

1. Open <https://github.com/Lijeythefox/NEXUS-OS/actions>.
2. There are two builds:
   - **Build NEXUS OS image**: the main, phase-by-phase build. Right now it's the bare Phase 1 desktop.
   - **Build NEXUS OS prototype**: the everything-at-once prototype (all apps, themes, Settings app). Less tested.
3. A yellow dot means it's still running. The main build takes about 1 to 2 hours, the prototype 2 to 4 hours.
4. When it shows a **green tick**, it's ready. A **red cross** means it failed: open the run, download the **build-logs** artifact at the bottom, and send it to Claude.

## 3. Download the image

1. Click the run with the green tick.
2. Scroll to **Artifacts** at the bottom of the page.
3. Click the one starting with `NEXUS-OS_` (main) or `NEXUS-OS-prototype_` (prototype). It downloads as a `.zip` (about 1 to 3 GB).
4. Unzip it. Inside is a file ending in `.img.xz`. Don't unpack the `.img.xz` itself; Etcher reads it as is.

Tagged versions of the main build (for example `v0.1`) are also on the **Releases** page.

## 4. Write it to the spare SD card

1. Put the spare SD card in your PC.
2. Open balenaEtcher.
3. **Flash from file**: pick the `.img.xz`.
4. **Select target**: pick the SD card. Check the size to make sure it's the card and not another drive.
5. Click **Flash!** and wait until it has also finished verifying (5 to 15 minutes).
6. If Windows pops up "You need to format the disk", click **Cancel**. That's normal: Windows can't read Linux drives.
7. Take the card out.

## 5. First boot from the SD card

1. With the deck switched off, put the SD card in.
2. Plug in your keyboard and switch on.
3. Wait. The first boot takes 2 to 5 minutes. The screen may stay black or show text for a while.
4. Armbian's setup screen appears (NEXUS OS is built on Armbian, so some setup screens say "Armbian"). It asks you to:
   - set a **root password** (the admin password, keep it safe),
   - pick your shell (choose **bash**),
   - create your **user account** (name and password; this is what you log in with),
   - confirm language and time zone.
5. The desktop starts.

For testing new builds you can keep running from the SD card and skip step 6.

## 6. Copy the system onto the eMMC

Do this once you're happy with a build. It replaces whatever is on the eMMC.

1. Open a terminal: start menu > **Terminal** (or Super + T on the prototype).
2. Type `sudo armbian-install`, press Enter, and type your password.
3. Choose **Boot from eMMC - system on eMMC**.
4. Confirm. It erases the eMMC and copies the system across (around 5 to 10 minutes).
5. When it's done, choose **Power off**.
6. Take the SD card out and switch on. The deck now starts from the eMMC.

If `armbian-install` isn't found, run `sudo armbian-config` and look under **System** for the install option.

## 7. Set up your personal micro SD card (prototype)

Games, documents, Minecraft worlds and snapshots live on the micro SD card, so reflashing never touches them.

1. Put your personal micro SD card in the deck.
2. Open **Settings > System > Storage**.
3. Click **Prepare card**, type `ERASE` and enter your password. This formats the card the Linux way and creates the `ROMs`, `Files`, `Minecraft` and `Snapshots` folders.
4. Log out and back in so Documents, Downloads, Pictures and so on point at the card.

Then, in **Settings**:

- **Network & internet > Wi-Fi**: connect to Wi-Fi.
- **Bluetooth & devices > Bluetooth**: pair the controller and keyboard.
- **Accounts > Callsign**: set your callsign.
- **Privacy & security > File sharing > Share password**: lets you copy games in from Windows at `\\nexus.local\ROMs`.
- **Network & internet > VPN**: sign in to Tailscale.

## Updating to a newer build later

Repeat steps 1 to 6. Your micro SD card (games, files, snapshots) isn't touched. Your settings on the eMMC are replaced, so you'll go through the setup screen again.

## Troubleshooting

- **The deck starts the old system instead of the SD card.** The board may prefer a bootloader that's already on the eMMC. Tell Claude what's on screen; the fix depends on what's on the eMMC.
- **Black screen for more than 5 minutes.** Try another HDMI cable, and check the screen has power and is set to HDMI input.
- **Etcher says the image is invalid.** The download was probably cut short. Download the artifact again.
- **Keyboard does nothing at the setup screen.** It's probably Bluetooth. Use a USB keyboard or one with a wireless dongle for first boot.
