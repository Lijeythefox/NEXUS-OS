# Installing NEXUS OS

Start to finish: send the recipe to GitHub, let GitHub build the image, put it on a micro SD card, and boot the deck from it.

The Radxa Zero 3W in the deck has no built-in storage (no eMMC), so **the micro SD card is the deck's system drive**. NEXUS runs from it all the time. Your games and files live on a separate USB flash drive called **NEXUS-SD** (step 6).

You need:

- **GitHub Desktop** on your PC (already installed).
- **[balenaEtcher](https://etcher.balena.io/)** on your PC.
- A **micro SD card for the system**, 64 GB or bigger and **A2-rated** (it says "A2" on the card). A2 cards open apps much faster, which matters because NEXUS runs straight from the card. It gets wiped every time you flash.
- A **USB flash drive** for your games and files (any size you like). It plugs into the deck's internal USB hub.
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

## 4. Write it to the system micro SD card

1. Put the system micro SD card in your PC.
2. Open balenaEtcher.
3. **Flash from file**: pick the `.img.xz`.
4. **Select target**: pick the micro SD card. Check the size to make sure it's the card and not another drive (and not your NEXUS-SD USB drive, if it's plugged in).
5. Click **Flash!** and wait until it has also finished verifying (5 to 15 minutes).
6. If Windows pops up "You need to format the disk", click **Cancel**. That's normal: Windows can't read Linux drives.
7. Take the card out.

## 5. First boot

1. With the deck switched off, put the micro SD card in the deck's card slot.
2. Plug in your keyboard and switch on.
3. Wait. The first boot takes 2 to 5 minutes. The screen may stay black or show text for a while.
4. Armbian's setup screen appears (NEXUS OS is built on Armbian, so some setup screens say "Armbian"). It asks you to:
   - set a **root password** (the admin password, keep it safe),
   - pick your shell (choose **bash**),
   - create your **user account** (name and password; this is what you log in with),
   - confirm language and time zone.
5. The desktop starts. That's it: the deck always starts from this card from now on.

## 6. Set up your NEXUS-SD storage drive (prototype)

Games, documents, Minecraft worlds and snapshots live on a USB flash drive named **NEXUS-SD**, so reflashing the system card never touches them. You only do this once per drive.

1. Plug the USB flash drive into the deck's internal USB hub.
2. Open **Settings > System > Storage**.
3. Click **Prepare storage drive**. Only USB drives are listed; the system micro SD card never is.
4. Pick your drive from the list, check the name and size, type `ERASE` and enter your password. This wipes the drive, formats it the Linux way, names it `NEXUS-SD` and creates the `ROMs`, `Files`, `Minecraft` and `Snapshots` folders.
5. Log out and back in so Documents, Downloads, Pictures and so on point at the drive.

Then, in **Settings**:

- **Network & internet > Wi-Fi**: connect to Wi-Fi.
- **Bluetooth & devices > Bluetooth**: pair the controller and keyboard.
- **Accounts > Callsign**: set your callsign.
- **Privacy & security > File sharing > Share password**: lets you copy games in from Windows at `\\nexus.local\ROMs`.
- **Network & internet > VPN**: sign in to Tailscale.

## Updating to a newer build later

Repeat steps 1 to 5 with the same system card. Reflashing **wipes the system micro SD card** (apps, settings and your account on it are replaced, so you'll go through the setup screen again), but it **never touches the NEXUS-SD drive**: your games, files, Minecraft worlds and snapshots stay put. To be extra safe, unplug the NEXUS-SD drive from your PC while Etcher runs, so it can't be picked by mistake.

After the setup screen, log in and the deck finds the NEXUS-SD drive by itself. If the folders in your home don't point at it yet, log out and back in.

## Troubleshooting

- **Black screen for more than 5 minutes.** Try another HDMI cable, and check the screen has power and is set to HDMI input. Then try reflashing the card, or a different card.
- **Etcher says the image is invalid.** The download was probably cut short. Download the artifact again.
- **Keyboard does nothing at the setup screen.** It's probably Bluetooth. Use a USB keyboard or one with a wireless dongle for first boot.
- **Settings > Storage says "No USB drive found".** Check the drive is plugged into the deck's USB hub (not a charger port), wait 5 seconds, then open the Storage page again.
- **Games or files are missing after plugging the drive in late.** Open **Settings > System > Storage** and press **Mount**, or restart the deck with the drive plugged in.
