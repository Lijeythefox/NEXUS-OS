# Trying NEXUS OS in a virtual machine (no USB stick needed)

After every successful image build, GitHub also makes a ready-to-run virtual machine
for **VMware Workstation Pro** (free for personal use). Workflow: **Make NEXUS OS virtual machine**.

## One-time setup

1. Install **VMware Workstation Pro** from Broadcom's website (free, needs a free Broadcom account).
   VMware is used instead of VirtualBox because the desktop needs good 3D graphics in the VM.

## Each new build

1. Open <https://github.com/Lijeythefox/NEXUS-OS/actions> and click **Make NEXUS OS virtual machine**.
2. Open the newest run with the green tick. Under **Artifacts**, download `NEXUS-OS-VM_...` (about 2.4 GB).
3. Unzip it into `Documents\Virtual Machines\` (it makes a `NEXUS-OS` folder; needs about 40 GB free over time).
4. In VMware: **File > Open...** and pick `Documents\Virtual Machines\NEXUS-OS\NEXUS-OS.vmx`.
   If it asks "Did you move it or copy it?", click **I Copied It**.
5. Click **Power on this virtual machine**. Do Armbian's first-run setup (root password, bash, your user), then unlock.

Tips:
- Click inside the window to use it. **Ctrl + Alt** gives the mouse back to Windows.
- Use **View > Full Screen** (Ctrl + Alt + Enter) so the Windows key reaches NEXUS instead of opening the Start menu.
- Black screen? **VM > Settings > Display**, tick **Accelerate 3D graphics**.
- To start fresh with a new build, delete the old `NEXUS-OS` folder first.

A virtual machine shows how NEXUS looks and behaves, but speed and hardware (Wi-Fi, sound, sleep)
can differ from the real OptiPlex or deck.
