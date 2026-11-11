# Installing NEXUS OS 2 on a Dell OptiPlex 3060 SFF

NEXUS OS is built by GitHub, never on your PC. You download the finished image, put it on a USB stick and boot the OptiPlex from it.

## 1. Get the image

1. Open <https://github.com/Lijeythefox/NEXUS-OS/actions>.
2. Click **Build NEXUS OS image** on the left.
3. Wait for the newest run to show a **green tick**. A build takes about 2 hours.
   A **red cross** means it failed: tell Claude, who can read the build log.
4. Click the run with the green tick. Scroll down to **Artifacts**.
5. Download the one starting with `NEXUS-OS_2.0-dev-`. It arrives as a `.zip`.
6. Unzip it. Inside is `NEXUS-OS_2.0-dev-..._uefi-x86.img.xz`. Leave it as `.img.xz`.

## 2. Put it on a USB stick (on Windows)

1. Install balenaEtcher from <https://etcher.balena.io>.
2. **Flash from file** → pick the `.img.xz` → **Select target** → your USB stick (8 GB or more) → **Flash!**
   This wipes the stick.
3. If Windows says "You need to format the disk", click **Cancel**. Windows can't read Linux drives.

## 3. Set up the OptiPlex BIOS (one time only)

1. Turn the OptiPlex on and tap **F2** to open the BIOS setup.
2. **General → Boot Sequence**: set Boot List Option to **UEFI**.
3. **Secure Boot → Secure Boot Enable**: untick it.
4. **System Configuration → SATA Operation**: choose **AHCI**.
   If Windows is still on the drive and you want to keep it, back it up first: Windows may not boot after this change.
5. **Apply**, then **Exit**.

## 4. First boot

1. Plug the stick into a USB port on the back. Plug in a network cable if you can.
2. Turn the OptiPlex on and tap **F12**. Pick the USB stick under **UEFI BOOT**.
3. Text scrolls past, then Armbian's setup asks you to:
   - set a **root password** (the admin password),
   - pick a shell (choose **bash**),
   - create your **user** (name and password: this is what unlocks the desktop),
   - confirm language and time zone.
4. It then says "Starting the NEXUS desktop..." and the **lock screen** appears. Type your user password and press Enter.

You can keep using it straight off the stick to try it out.

## 5. Install it onto the internal drive (optional)

1. Open a terminal: **Super + Return** (Super is the Windows key).
2. Run `sudo armbian-install` and type your password.
3. Choose the option that installs to the internal **SATA** or **NVMe** drive. **This erases that drive.**
4. When it finishes, shut down (**Super + Escape** → Shut down), unplug the USB stick and turn it back on.

## Finding your way around

| Keys | What happens |
| --- | --- |
| Super + Space | App launcher |
| Super + Alt + Space | NEXUS menu |
| Super + K | List of all shortcuts |
| Super + Return | Terminal |
| Super + W | Close window |
| Super + 1..5 | Switch workspace |
| Super + Escape | Lock, sleep, restart, shut down |

## If something goes wrong

- **Black screen after the setup, or the desktop never appears:** press **Ctrl + Alt + F2**, log in with your user name and password, run `tail -n 40 ~/.cache/nexus/hyprland.log` and send Claude a photo.
- **The OptiPlex starts Windows or says "No boot device":** check step 3, then use **F12** again.
- **To report how fast it is:** open a terminal, run `nexus-bench` and send Claude the output.
