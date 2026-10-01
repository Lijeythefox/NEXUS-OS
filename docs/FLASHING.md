# Flashing NEXUS OS

The Radxa Zero 3W's eMMC is soldered to the board, so Windows can't write to it directly. Instead you put the image on a **spare micro SD card**, boot the deck from it, and copy the system onto the eMMC from there.

You need:

- A spare micro SD card, 16 GB or bigger. Not your personal-files card: it gets wiped.
- [balenaEtcher](https://etcher.balena.io/) on your Windows PC.
- A keyboard that works without Bluetooth (USB, or a 2.4 GHz wireless dongle). Bluetooth isn't set up until after first boot.

## 1. Download the image

1. Open the repo on GitHub: <https://github.com/Lijeythefox/NEXUS-OS>
2. Click **Actions**, then **Build NEXUS OS image**.
3. Click the newest run with a green tick.
4. Scroll to **Artifacts** and click the one named `NEXUS-OS_...`. It downloads as a `.zip`.
5. Unzip it. Inside is `NEXUS-OS_<version>_radxa-zero3.img.xz`. Don't unpack the `.img.xz` itself; Etcher reads it as is.

Tagged versions (for example `v0.1`) are also on the **Releases** page.

## 2. Write it to the spare SD card

1. Put the spare SD card in your PC.
2. Open balenaEtcher.
3. **Flash from file**: pick the `.img.xz`.
4. **Select target**: pick the SD card. Double-check it's the right drive.
5. **Flash!** and wait for it to finish verifying.
6. If Windows offers to "format the disk", click **Cancel**. That's normal: Windows can't read Linux drives.

## 3. Boot the deck from the SD card

1. With the deck powered off, put the SD card in.
2. Plug in your keyboard and power on.
3. The first boot takes a few minutes. Armbian's setup screen appears (NEXUS OS is built on Armbian, so some setup screens say "Armbian"). It asks you to:
   - set a **root password** (the admin password, keep it safe),
   - pick your shell (choose **bash**),
   - create your **user account** (name and password),
   - confirm language and timezone.
4. The XFCE desktop starts.

For testing during development you can keep running from the SD card and skip step 4.

## 4. Copy the system onto the eMMC

1. Open a terminal (Applications menu > Terminal Emulator).
2. Run `sudo armbian-install` and type your password.
3. Choose **Boot from eMMC - system on eMMC**.
4. Confirm. It erases the eMMC and copies the system across (around 5 to 10 minutes).
5. When it says it's done, choose **Power off**.
6. Take the SD card out and power on. The deck now boots from the eMMC.

If `armbian-install` isn't found, run `sudo armbian-config` and look under **System** for the install option.

## Troubleshooting

- **The deck boots the old system instead of the SD card.** The board may be preferring a bootloader already on the eMMC. Tell Claude what you see on screen; the fix depends on what's on the eMMC.
- **Black screen.** Wait 3 minutes on first boot. If it's still black, try another HDMI cable and check the screen has power.
