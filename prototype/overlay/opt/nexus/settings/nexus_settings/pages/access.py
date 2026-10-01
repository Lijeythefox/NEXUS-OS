from nexus import theme
from nexus.common import Settings, run, spawn
from nexus.presets import active_key
from nexus_settings.pages.personal import FontsPage, apply_preset
from nexus_settings.ui import Page


class ContrastPage(Page):
    def build(self):
        self.switch("High contrast", "White on black with yellow highlights", active_key() == "contrast", self.toggle)

    def toggle(self, value):
        settings = Settings()
        if value:
            current = active_key()
            if current != "contrast":
                settings.set("PREVIOUS_PRESET", current)
            apply_preset(self.window, "contrast")
        else:
            apply_preset(self.window, settings.get("PREVIOUS_PRESET", "amber") or "amber")


def gsettings_get(schema, key):
    return run(["gsettings", "get", schema, key]).out.strip()


class KeyboardAccessPage(Page):
    def build(self):
        auto = gsettings_get("org.onboard.auto-show", "enabled") == "true"
        self.switch("Show the keyboard automatically", "Pops up when you tap a text box", auto, self.set_auto)
        self.button("On-screen keyboard", "Super + K, or the keyboard button on the taskbar", "Show",
                    lambda: spawn(["nexus-osk", "show"]))

    def set_auto(self, value):
        run(["gsettings", "set", "org.gnome.desktop.interface", "toolkit-accessibility", "true" if value else "false"])
        run(["gsettings", "set", "org.onboard.auto-show", "enabled", "true" if value else "false"])
        self.window.toast("Saved. Log out and back in for every app to notice.")


class MotionPage(Page):
    def build(self):
        self.switch("Reduce animations", "Fewer moving effects in menus and windows",
                    Settings().get_bool("REDUCE_MOTION"), self.toggle)

    def toggle(self, value):
        Settings().set("REDUCE_MOTION", value)
        theme.apply_motion(Settings())


PAGES = [
    ("textsize", "Text size", "Make everything easier to read", "text size font bigger zoom", FontsPage),
    ("contrast", "High contrast", "Maximum contrast preset", "contrast accessibility vision", ContrastPage),
    ("osk", "On-screen keyboard", "Always available, auto pop-up", "onboard keyboard touch typing", KeyboardAccessPage),
    ("motion", "Reduce animations", "Fewer moving effects", "animation motion effects", MotionPage),
]
