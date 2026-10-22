import configparser
from pathlib import Path

from gi.repository import Gio, Gtk

from nexus import appcenter, webapps
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


def desktop_app(app_id):
    try:
        return Gio.DesktopAppInfo.new(app_id)
    except TypeError:
        return None


def set_default_app(app_id, mimes):
    app = desktop_app(app_id)
    if not app:
        return None
    for mime in mimes:
        try:
            app.set_as_default_for_type(mime)
        except Exception:
            continue
    return app.get_display_name()


def default_browser_id():
    app = Gio.AppInfo.get_default_for_type(DEFAULT_TYPES[0][1][0], False)
    return app.get_id() if app else ""


def launch_desktop(app_id):
    app = desktop_app(app_id)
    return bool(app) and app.launch([], None)


class AppCenterPage(Page):
    def build(self):
        self.note("Extra browsers, games and game systems you can add or remove at any time. Installing needs internet. "
                  "Your files and saved games are never touched.")
        entries = appcenter.load()
        if not entries:
            self.note("The App Center list is empty.")
            return
        browser = default_browser_id()
        states = appcenter.installed_map(entries)
        for category in appcenter.categories(entries):
            self.section(category)
            for entry in (item for item in entries if item.category == category):
                self.entry_row(entry, states[entry.key], browser)

    def entry_row(self, entry, installed, browser):
        actions = []
        status = ""
        if installed:
            launch = appcenter.launch_id(entry)
            if launch:
                actions.append(("Open", lambda app_id=launch: launch_desktop(app_id)))
            if entry.browser:
                if entry.launch == browser:
                    status = "Default browser"
                else:
                    actions.append(("Make default", lambda item=entry: self.make_default(item)))
            if entry.kind != "builtin":
                actions.append(("Remove", lambda item=entry: self.remove(item)))
            status = status or ("Built in" if entry.kind == "builtin" else "Installed")
        else:
            actions.append(("Install", lambda item=entry: self.install(item)))
        subtitle = entry.description + (f"  ·  {status}" if status else "")
        self.buttons(entry.name, subtitle, actions)

    def install(self, entry):
        self.root_task(lambda: root("app-install", entry.key), f"{entry.name} installed",
                       busy=f"Installing {entry.name}...")

    def remove(self, entry):
        extra = " Your games stay on the card." if entry.kind == "core" else ""
        if confirm(self.window, f"Remove {entry.name}?{extra}", "Remove", danger=True):
            self.root_task(lambda: root("app-remove", entry.key), f"{entry.name} removed",
                           busy=f"Removing {entry.name}...")

    def make_default(self, entry):
        name = set_default_app(entry.launch, DEFAULT_TYPES[0][1])
        self.window.toast(f"{name} is now the default browser" if name else "That browser isn't installed")
        self.rebuild()


class WebAppsPage(Page):
    def build(self):
        self.note("Turn any website into an app with its own start menu entry and window. "
                  "It opens in your default browser (as an app window in Chromium, a new window in Firefox).")
        self.button("Add a web app", "Any web address", "Add", self.add_webapp)
        mine = webapps.listing()
        self.section("Your web apps")
        if not mine:
            self.note("None yet. Add one above or pick a suggestion below.")
        for app in mine:
            self.buttons(app["name"], app["url"], [
                ("Open", lambda slug=app["slug"]: spawn(["nexus-webapp", slug])),
                ("Remove", lambda item=app: self.remove(item)),
            ])
        taken = {app["url"] for app in mine}
        self.section("Suggestions")
        for name, url in webapps.SUGGESTIONS:
            if url not in taken:
                self.button(name, url, "Add", lambda n=name, u=url: self.create(n, u))
        self.note("Netflix, Disney+ and Spotify need copy protection (DRM) that browsers on ARM boards don't have, "
                  "so they usually won't play.")

    def add_webapp(self):
        url = ask_text(self.window, "Add a web app", "Web address, for example music.youtube.com")
        if not url:
            return
        try:
            url = webapps.clean_url(url)
        except ValueError as error:
            self.window.toast(str(error))
            return
        suggestion = url.split("://", 1)[1].split("/")[0].removeprefix("www.").split(".")[0].title()
        name = ask_text(self.window, "Add a web app", "Name in the start menu", suggestion)
        if name:
            self.create(name, url)

    def create(self, name, url):
        def done(result, error):
            self.window.toast(str(error) if error else f"{name} added to the start menu")
            self.rebuild()

        self.task(lambda: webapps.add(name, url), done, busy="Fetching the site's icon...")

    def remove(self, app):
        if confirm(self.window, f"Remove the {app['name']} web app?", "Remove", danger=True):
            webapps.remove(app["slug"])
            self.rebuild()


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
        name = set_default_app(app_id, mimes)
        if name:
            self.window.toast(f"{name} is now the default")


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
    ("appcenter", "App Center", "Add browsers, games and game systems",
     "install store browser firefox emulator games solitaire chess add apps",
     AppCenterPage),
    ("webapps", "Web apps", "Turn websites into apps", "web app website pwa youtube discord shortcut", WebAppsPage),
    ("installed", "Installed apps", "Open or uninstall", "apps programs uninstall remove", InstalledPage),
    ("defaults", "Default apps", "Browser, video player, text editor", "default open with browser", DefaultsPage),
    ("startup", "Startup apps", "Turn login apps on or off", "autostart startup login", StartupPage),
    ("ai", "AI Assistant", "Open WebUI address on the home PC", "ai ollama openwebui llm", AiPage),
]
