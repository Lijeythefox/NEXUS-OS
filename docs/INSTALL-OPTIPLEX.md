# Installing NEXUS OS on a Dell OptiPlex 3060 SFF

This build uses Armbian's `uefi-x86` target, so the image runs on a normal Intel PC.
On the OptiPlex the deck-only parts are switched off: the Pico lid/battery sensor and the battery HUD widget.

## 1. Build the image
1. On github.com, open the repo's **Actions** tab.
2. Click **Build NEXUS OS prototype**. If a run didn't start by itself, click **Run workflow**.
3. Wait for the green tick. It takes about 2-4 hours.
4. Open the finished run. Under **Artifacts**, download `NEXUS-OS-prototype_..._uefi-x86`.
5. Unzip it. Inside is `NEXUS-OS-prototype_..._uefi-x86.img.xz`. Leave it as `.img.xz`.

## 2. Put it on a USB stick (on Windows)
1. Install balenaEtcher (etcher.balena.io).
2. **Flash from file** → pick the `.img.xz` → **Select target** → your USB stick (16 GB or more) → **Flash**.
   This wipes the stick.

## 3. Set up the OptiPlex BIOS (one time only)
1. Turn the OptiPlex on and tap **F2** to open the BIOS setup.
2. **General → Boot Sequence**: set Boot List Option to **UEFI**.
3. **Secure Boot → Secure Boot Enable**: untick it. Linux kernels from Armbian aren't signed for Secure Boot.
4. **System Configuration → SATA Operation**: choose **AHCI**. Dell often ships these set to "RAID On", which hides the drive from Linux.
   If Windows is still on the drive and you want to keep it, back it up first: Windows may not boot after this change.
5. **Apply**, then **Exit**.

## 4. Boot from the USB stick
1. Plug the stick into a USB port on the back.
2. Turn the OptiPlex on and tap **F12**. Pick the USB stick under **UEFI BOOT**.
3. The first boot sets up a user and password, then restarts into the NEXUS login screen.
   You can use it straight off the stick to try it out.

## 5. Install it onto the internal drive
1. Open a terminal (Super + T) and run `sudo armbian-install`.
2. Choose the option that installs to the internal **SATA** or **NVMe** drive. **This erases that drive.**
3. When it finishes, shut down, unplug the USB stick and turn it back on.

## 6. Games and files
NEXUS keeps games, files and Minecraft worlds on a drive labelled **NEXUS-SD**, mounted at `/mnt/sdcard`.
Use a USB stick or a second drive: **Settings → System → Storage → Prepare storage drive**.

## Switching back to the deck later
Set `BOARD=rpi4b` in `config/board.conf` and `prototype/config/board.conf`. The build then uses the normal ARM `downloads.txt` automatically.
