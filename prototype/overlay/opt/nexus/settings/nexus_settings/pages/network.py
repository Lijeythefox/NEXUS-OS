from pathlib import Path

from nexus import system
from nexus.common import Settings, out, spawn
from nexus_settings.ui import Page, ask_text, confirm, label


class WifiPage(Page):
    networks = None

    def build(self):
        enabled = system.wifi_enabled()
        self.switch("Wi-Fi", None, enabled, self.set_enabled)
        if not enabled:
            return
        ssid, signal = system.active_wifi()
        self.info("Connected to", f"{ssid}  ({signal}%)" if ssid else "Nothing")
        actions = [("Scan", self.scan)]
        if ssid:
            actions.append(("Disconnect", self.disconnect))
        self.buttons("Networks", "Tap a network to connect", actions)
        self.section("Available")
        if self.networks is None:
            self.networks = system.wifi_scan(rescan=False)
        if not self.networks:
            self.note("No networks found. Press Scan.")
        for network in self.networks:
            secure = network["security"] not in ("", "--")
            subtitle = f"{network['signal']}%  ·  {'Secured' if secure else 'Open'}"
            if network["active"]:
                subtitle += "  ·  Connected"
            self.button(network["ssid"], subtitle, "Connect",
                        lambda item=network, needs=secure: self.connect(item["ssid"], needs))
        self.section("Saved networks")
        for item in system.wifi_saved():
            self.button(item["name"], "Connects automatically" if item["autoconnect"] else "Manual", "Forget",
                        lambda uuid=item["uuid"], name=item["name"]: self.forget(uuid, name))

    def set_enabled(self, value):
        self.networks = None
        self.task(lambda: system.set_wifi(value), lambda r, e: self.rebuild())

    def scan(self):
        def done(result, error):
            self.networks = result or []
            self.rebuild()

        self.task(lambda: system.wifi_scan(rescan=True), done, busy="Scanning...")

    def disconnect(self):
        self.task(system.wifi_disconnect, lambda r, e: self.rebuild())

    def connect(self, ssid, secure):
        saved = any(item["name"] == ssid for item in system.wifi_saved())
        password = None
        if secure and not saved:
            password = ask_text(self.window, "Wi-Fi password", f"Password for {ssid}", password=True)
            if password is None:
                return

        def done(result, error):
            if result is not None and result.code == 0:
                self.window.toast(f"Connected to {ssid}")
            else:
                text = (result.err or result.out).strip() if result is not None else str(error)
                self.window.toast(text or "Couldn't connect")
            self.networks = None
            self.rebuild()

        self.task(lambda: system.wifi_connect(ssid, password), done, busy=f"Connecting to {ssid}...")

    def forget(self, uuid, name):
        if confirm(self.window, f"Forget {name}? You'll need the password to reconnect.", "Forget", danger=True):
            system.wifi_forget(uuid)
            self.rebuild()


class HotspotPage(Page):
    def build(self):
        settings = Settings()
        self.note("Pick your phone's hotspot from your saved Wi-Fi networks. The deck connects to it "
                  "automatically when home Wi-Fi isn't around, and the Hotspot tile in Quick Settings uses it.")
        saved = system.wifi_saved()
        if not saved:
            self.note("Connect to your phone's hotspot once on the Wi-Fi page first.")
            return
        current = settings.get("HOTSPOT_SSID")
        options = [("", "None")] + [(item["name"], item["name"]) for item in saved]
        self.combo("Phone hotspot", options, current, self.choose)
        if current:
            self.switch("Connected to hotspot", None, system.hotspot_active(), self.toggle)

    def choose(self, name):
        Settings().set("HOTSPOT_SSID", name)
        if name:
            system.set_hotspot_preference(name)
        self.rebuild()

    def toggle(self, value):
        self.task(lambda: system.hotspot_toggle(value), lambda r, e: self.rebuild(), busy="Switching...")


class VpnPage(Page):
    def build(self):
        status = system.tailscale_status()
        if not status["installed"]:
            self.note("Tailscale isn't installed.")
            return
        running = status["state"] == "Running"
        self.switch("Tailscale", "Reach your home PC and Minecraft server from anywhere", running, self.set_running)
        self.info("Status", status["state"])
        if status["ips"]:
            self.info("This deck's Tailscale address", status["ips"][0])
        if status["state"] in ("NeedsLogin", "NoState", "Stopped") or status.get("auth_url"):
            self.button("Sign in", "Opens the Tailscale sign-in page", "Sign in", self.sign_in)
        if status["peers"]:
            self.section("Devices")
            for peer in status["peers"]:
                self.info(f"{peer['name']} ({peer['os']})", f"{peer['ip']}  {'online' if peer['online'] else 'offline'}")

    def set_running(self, value):
        def done(result, error):
            if isinstance(result, str) and result:
                self.window.toast(result)
            self.rebuild()

        self.task(system.tailscale_up if value else system.tailscale_down, done, busy="Switching Tailscale...")

    def sign_in(self):
        self.task(system.tailscale_up, lambda r, e: self.window.toast(r or "Signed in"))


def bookmarks_file():
    return Path.home() / ".config/gtk-3.0/bookmarks"


def read_bookmarks():
    try:
        return [line for line in bookmarks_file().read_text(encoding="utf-8").splitlines() if line.strip()]
    except OSError:
        return []


def write_bookmarks(lines):
    path = bookmarks_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


class SharesPage(Page):
    def build(self):
        self.section("Windows shared folders")
        self.button("Add a shared folder", "From a Windows PC on your network or Tailscale", "Add", self.add_share)
        shares = [line for line in read_bookmarks() if line.startswith("smb://")]
        if not shares:
            self.note("No shared folders saved yet. They also appear in the Files sidebar.")
        for line in shares:
            uri, _, name = line.partition(" ")
            self.buttons(name or uri, uri, [
                ("Open", lambda target=uri: spawn(["thunar", target])),
                ("Remove", lambda entry=line: self.remove(entry)),
            ])
        self.section("This deck's games folder")
        active = out(["systemctl", "is-active", "smbd"]) == "active"
        host = out(["hostname"]) or "nexus"
        self.info("Share", f"\\\\{host}.local\\ROMs" if active else "Off")
        self.button("Share settings", "Turn it on or off and set its password", "Privacy & security",
                    lambda: self.window.open_page("share"))

    def add_share(self):
        pc = ask_text(self.window, "Add shared folder", "PC name or IP address (for example DESKTOP-1234)")
        if not pc:
            return
        share = ask_text(self.window, "Add shared folder", "Folder name on that PC (for example Games)")
        if not share:
            return
        lines = read_bookmarks()
        lines.append(f"smb://{pc.strip()}/{share.strip()} {share.strip()} on {pc.strip()}")
        write_bookmarks(lines)
        self.rebuild()

    def remove(self, entry):
        write_bookmarks([line for line in read_bookmarks() if line != entry])
        self.rebuild()


class AirplanePage(Page):
    def build(self):
        self.switch("Airplane mode", "Turns off Wi-Fi and Bluetooth", system.airplane_get(), self.toggle)

    def toggle(self, value):
        self.task(lambda: system.airplane_set(value), lambda r, e: self.rebuild())


PAGES = [
    ("wifi", "Wi-Fi", "Scan, connect, saved networks", "wifi wireless network internet password", WifiPage),
    ("hotspot", "Hotspot", "Your phone's hotspot, auto-connect", "phone tether hotspot mobile", HotspotPage),
    ("vpn", "VPN", "Tailscale on/off, sign in, devices", "tailscale vpn remote home", VpnPage),
    ("shares", "Network shares", "Saved Windows shared folders", "smb samba windows share folder network", SharesPage),
    ("airplane", "Airplane mode", "All wireless off", "flight airplane offline radio", AirplanePage),
]
