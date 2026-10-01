import configparser
from pathlib import Path

from gi.repository import Gio, Gtk

from nexus.common import Settings, out, root, spawn
from nexus_settings.ui import Page, ask_text, confirm

DEFAULT_TYPES = [
    ("Web browser", ["x-scheme-handler/http", "x-scheme-handler/https", "text/html"]),
    ("Video player", ["video/mp4", "video/x-matroska", "video/webm"]),
    ("Music player", ["audio/mpeg", "audio/flac", "audio/ogg"]),
    ("Text editor", ["text/plain"]),
    ("Photo viewer", ["image/png", "image/jpeg"]),
    ("PDF viewer", ["application/pdf"]),
]


class InstalledPage(Page):
    filter_text = ""

    def build(self):
        search = Gtk.SearchEntry(placeholder_text="Search apps", text=self.filter_text)
        search.connect("activate", lambda entry: self.search(entry.get_text()))
        search.connect("search-changed", lambda entry: self.search(entry.get_text()) if not entry.get_text() else None)
        self.put(search)
        apps = sorted((app for app in Gio.AppInfo.get_all() if app.should_show()),
                      key=lambda app: app.get_display_name().lower())
        needle = self.filter_text.lower()
        for app in apps:
            name = app.get_display_name()
            if needle and needle not in name.lower():
                continue
            self.buttons(name, app.get_description() or "", [
                ("Open", lambda item=app: item.launch([], None)),
                ("Uninstall", lambda item=app: self.uninstall(item)),
            ])

    def search(self, text):
        self.filter_text = text
        self.rebuild()

    def uninstall(self, app):
        path = app.get_filename() if hasattr(app, "get_filename") else None
        owner = out(["dpkg-query", "-S", path]) if path else ""
        if not owner:
            self.window.toast("This app is part of NEXUS and can't be removed here.")
            return
        package = owner.split(":")[0]
        if confirm(self.window, f"Uninstall {app.get_display_name()} ({package})?", "Uninstall", danger=True):
            self.root_task(lambda: root("uninstall", package), f"{app.get_display_name()} removed")


class DefaultsPage(Page):
    def build(self):
        for title, types in DEFAULT_TYPES:
            options = [(app.get_id(), app.get_display_name()) for app in Gio.AppInfo.get_all_for_type(types[0])]
            if not options:
                continue
            current = Gio.AppInfo.get_default_for_type(types[0], False)
            self.combo(title, options, current.get_id() if current else options[0][0],
                       lambda app_id, mimes=types: self.set_default(app_id, mimes))

    def set_default(self, app_id, mimes):
        app = Gio.DesktopAppInfo.new(app_id)
        if not app:
            return
        for mime in mimes:
            try:
                app.set_as_default_for_type(mime)
            except Exception:
                continue
        self.window.toast(f"{app.get_display_name()} is now the default")


def autostart_entries():
    entries = {}
    for folder in (Path("/etc/xdg/autostart"), Path.home() / ".config/autostart"):
        for path in sorted(folder.glob("*.desktop")):
            parser = configparser.ConfigParser(interpolation=None, strict=False)
            try:
                parser.read(path, encoding="utf-8")
            except configparser.Error:
                continue
            if not parser.has_section("Desktop Entry"):
                continue
            section = parser["Desktop Entry"]
            only = section.get("OnlyShowIn", "")
            if only and "XFCE" not in only:
                entries.pop(path.name, None)
                continue
            if "XFCE" in section.get("NotShowIn", ""):
                continue
            enabled = section.get("Hidden", "false").lower() != "true" and \
                section.get("X-GNOME-Autostart-enabled", "true").lower() != "false"
            entries[path.name] = {"name": section.get("Name", path.stem), "path": path, "enabled": enabled,
                                  "comment": section.get("Comment", "")}
    return entries


class StartupPage(Page):
    def build(self):
        self.note("Apps and helpers that start when you log in.")
        for filename, entry in sorted(autostart_entries().items(), key=lambda item: item[1]["name"].lower()):
            self.switch(entry["name"], entry["comment"], entry["enabled"],
                        lambda value, name=filename, source=entry["path"]: self.set_enabled(name, source, value))

    def set_enabled(self, filename, source, value):
        target = Path.home() / ".config/autostart" / filename
        target.parent.mkdir(parents=True, exist_ok=True)
        lines = Path(source).read_text(encoding="utf-8").splitlines()
        lines = [line for line in lines if not line.startswith(("Hidden=", "X-GNOME-Autostart-enabled="))]
        lines.append(f"Hidden={'false' if value else 'true'}")
        target.write_text("\n".join(lines) + "\n", encoding="utf-8")


class AiPage(Page):
    def build(self):
        url = Settings().get("OPENWEBUI_URL")
        self.info("Open WebUI address", url)
        self.note("Use your home PC's Tailscale name or address so it works away from home too, "
                  "for example http://home-pc:3000")
        self.buttons("AI Assistant", None, [("Change address", self.change), ("Open", lambda: spawn(["nexus-ai"]))])

    def change(self):
        url = ask_text(self.window, "AI Assistant", "Open WebUI address", Settings().get("OPENWEBUI_URL"))
        if url:
            if not url.startswith(("http://", "https://")):
                url = "http://" + url
            Settings().set("OPENWEBUI_URL", url.strip())
            self.rebuild()


PAGES = [
    ("installed", "Installed apps", "Open or uninstall", "apps programs uninstall remove", InstalledPage),
    ("defaults", "Default apps", "Browser, video player, text editor", "default open with browser", DefaultsPage),
    ("startup", "Startup apps", "Turn login apps on or off", "autostart startup login", StartupPage),
    ("ai", "AI Assistant", "Open WebUI address on the home PC", "ai ollama openwebui llm", AiPage),
]
