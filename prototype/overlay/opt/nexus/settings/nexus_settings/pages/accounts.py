from nexus.common import callsign, root, root_quick, spawn, xfconf_get, xfconf_set
from nexus_settings.ui import Page, ask_password_twice, ask_text, label

LOCK_TIMES = [("1", "1 minute"), ("2", "2 minutes"), ("5", "5 minutes"), ("10", "10 minutes"),
              ("15", "15 minutes"), ("30", "30 minutes"), ("0", "Never")]


class PasswordPage(Page):
    def build(self):
        self.button("Password", "Used to log in, unlock and change system settings", "Change", self.change)

    def change(self):
        secret = ask_password_twice(self.window, "Change password")
        if secret:
            self.root_task(lambda: root("set-password", input_text=secret + "\n"), "Password changed", refresh=False)


class CallsignPage(Page):
    def build(self):
        self.put(label(callsign(), "nexus-heading"))
        self.note("Shown on the boot animation, login screen and HUD. Letters, numbers, spaces and dashes, "
                  "up to 16 characters.")
        self.button("Callsign", None, "Change", self.change)

    def change(self):
        text = ask_text(self.window, "Callsign", "New callsign", callsign())
        if text:
            def work():
                result = root_quick("callsign", text)
                spawn(["nexus-hud", "restart"])
                return result

            self.root_task(work, "Callsign saved. The boot animation shows it from the next restart.")


class AutoLockPage(Page):
    def build(self):
        current = str(xfconf_get("xfce4-power-manager", "/xfce4-power-manager/blank-on-ac") or "5")
        self.combo("Lock after", LOCK_TIMES, current, self.set_time,
                   subtitle="The screen locks when it goes idle for this long")
        self.button("Lock now", "Super + L", "Lock", lambda: spawn(["nexus-lock"]))

    def set_time(self, minutes):
        for key in ("blank-on-ac", "blank-on-battery"):
            xfconf_set("xfce4-power-manager", f"/xfce4-power-manager/{key}", int(minutes), "int")


PAGES = [
    ("password", "Password", "Change your password", "password login security", PasswordPage),
    ("callsign", "Callsign", "The name shown on boot, login and HUD", "callsign name hostname", CallsignPage),
    ("autolock", "Auto-lock", "Lock after being idle", "lock timeout idle screen", AutoLockPage),
]
