import json
import os
import time

from nexus.common import read_text, root, spawn
from nexus_settings.ui import Page, confirm

GUIDE_URL = "https://github.com/Lijeythefox/NEXUS-OS/blob/main/docs/FLASHING.md"


def last_check():
    try:
        stamp = os.path.getmtime("/var/lib/apt/periodic/update-success-stamp")
    except OSError:
        return "Never"
    return time.strftime("%d %b %Y %H:%M", time.localtime(stamp))


class UpdatesPage(Page):
    status = None

    def build(self):
        auto = 'Unattended-Upgrade "1"' in read_text("/etc/apt/apt.conf.d/20auto-upgrades")
        self.info("Security updates", "Installed automatically" if auto else "Off")
        self.info("Last checked", last_check())
        self.note("Only stable security updates install by themselves. The kernel and board firmware stay frozen "
                  "until you flash a new NEXUS image.")
        if self.status:
            self.info("Updates available", str(self.status.get("count", 0)))
        self.buttons("Updates", "A snapshot is taken before installing", [
            ("Check now", self.check),
            ("Install", self.install),
        ])

    def check(self):
        def done(result, error):
            if error or result.code != 0:
                self.window.toast((result.err.strip() if result else str(error)) or "Check failed")
                return
            try:
                self.status = json.loads(result.out.strip().splitlines()[-1])
            except (ValueError, IndexError):
                self.status = {"count": 0}
            self.rebuild()

        self.task(lambda: root("update-check"), done, busy="Checking for updates...")

    def install(self):
        if confirm(self.window, "Install all available updates? This can take a while.", "Install"):
            self.root_task(lambda: root("update-install", timeout=7200), "Updates installed")


class SnapshotsPage(Page):
    snapshots = None

    def build(self):
        self.note("Full system snapshots are saved on the micro SD card every day (the last 5 are kept) and before "
                  "updates.")
        self.buttons("Snapshots", None, [
            ("Take one now", self.create),
            ("Show list", self.load),
            ("Restore...", lambda: spawn(["timeshift-launcher"])),
        ])
        if self.snapshots is not None:
            self.section("Saved snapshots")
            if not self.snapshots:
                self.note("No snapshots yet.")
            for item in self.snapshots:
                self.info(item["name"], item["comment"] or item["tags"])

    def create(self):
        self.root_task(lambda: root("snapshot-create", "Manual snapshot", timeout=7200), "Snapshot saved")

    def load(self):
        def done(result, error):
            try:
                self.snapshots = json.loads(result.out) if result and result.code == 0 else []
            except ValueError:
                self.snapshots = []
            self.rebuild()

        self.task(lambda: root("snapshot-list"), done, busy="Reading snapshots...")


class GuidePage(Page):
    def build(self):
        self.note("To upgrade the board or start fresh, download a new NEXUS image from GitHub and flash it. "
                  "Your games and files on the micro SD card are not touched.")
        self.button("Rebuild and flash guide", None, "Open", lambda: spawn(["xdg-open", GUIDE_URL]))


PAGES = [
    ("updates", "Updates", "Security updates and checking for new ones", "update upgrade security apt", UpdatesPage),
    ("snapshots", "Snapshots", "Take, list and restore", "backup timeshift snapshot restore", SnapshotsPage),
    ("guide", "Rebuild & flash guide", "How to reflash or upgrade the board", "flash reinstall image guide", GuidePage),
]
