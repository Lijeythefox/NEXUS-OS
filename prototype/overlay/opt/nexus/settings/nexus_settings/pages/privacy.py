from nexus import system
from nexus.common import Settings, out, read_kv, root
from nexus_settings.ui import Page, ask_password_twice


class SshPage(Page):
    def build(self):
        enabled = out(["systemctl", "is-enabled", "ssh"]) == "enabled"
        self.switch("SSH access", "Lets you log in to the deck from another computer", enabled, self.toggle)
        address = system.ip_address()
        if enabled and address:
            self.info("Connect with", f"ssh {out(['whoami'])}@{address}")
        self.note("Only devices on your home network or Tailscale can reach it while the firewall is on.")

    def toggle(self, value):
        self.root_task(lambda: root("ssh", "on" if value else "off"), "SSH turned " + ("on" if value else "off"))


class FirewallPage(Page):
    def build(self):
        enabled = read_kv("/etc/ufw/ufw.conf").get("ENABLED", "no") == "yes"
        self.switch("Firewall", "Blocks incoming connections except SSH and file sharing from your own network",
                    enabled, self.toggle)

    def toggle(self, value):
        self.root_task(lambda: root("firewall", "on" if value else "off"),
                       "Firewall turned " + ("on" if value else "off"))


class SharePage(Page):
    def build(self):
        active = out(["systemctl", "is-active", "smbd"]) == "active"
        self.switch("Share the games folder", "Drop games in from Windows at \\\\nexus.local\\ROMs", active, self.toggle)
        self.button("Share password", "Windows asks for your deck username and this password", "Set",
                    self.set_password)

    def toggle(self, value):
        self.root_task(lambda: root("share", "on" if value else "off"),
                       "File sharing turned " + ("on" if value else "off"))

    def set_password(self):
        secret = ask_password_twice(self.window, "Share password")
        if secret:
            self.root_task(lambda: root("share-password", input_text=secret + "\n"), "Share password set", refresh=False)


class LocationPage(Page):
    def build(self):
        self.switch("Use location for weather", "Only the town you choose is sent to Open-Meteo",
                    Settings().get_bool("WEATHER_ENABLED"), lambda value: Settings().set("WEATHER_ENABLED", value))


PAGES = [
    ("ssh", "SSH access", "Log in to the deck remotely", "ssh remote terminal login", SshPage),
    ("firewall", "Firewall", "Block incoming connections", "firewall ufw security ports", FirewallPage),
    ("share", "File sharing", "The ROMs folder on your network", "samba smb share windows roms", SharePage),
    ("location", "Location", "Weather location on or off", "location privacy weather", LocationPage),
]
