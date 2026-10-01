import time

from nexus import weather
from nexus.common import Settings, out, run, spawn, xfconf_set
from nexus_settings.ui import Page, ask_text, choose

DATE_FORMATS = [
    ("%d %b %Y", "02 Oct 2026"),
    ("%d/%m/%Y", "02/10/2026"),
    ("%m/%d/%Y", "10/02/2026"),
    ("%Y-%m-%d", "2026-10-02"),
    ("%A %d %B", "Friday 02 October"),
]


def update_clocks():
    settings = Settings()
    time_format = "%H:%M" if settings.get_bool("CLOCK_24H") else "%I:%M %p"
    xfconf_set("xfce4-panel", "/plugins/plugin-7/digital-time-format", time_format)
    xfconf_set("xfce4-panel", "/plugins/plugin-7/digital-date-format", settings.get("DATE_FORMAT", "%d %b %Y"))
    spawn(["nexus-hud", "restart"])


def timedate():
    values = {}
    for line in out(["timedatectl", "show"]).splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            values[key] = value
    return values


class TimePage(Page):
    def build(self):
        settings = Settings()
        info = timedate()
        self.info("Time now", time.strftime("%H:%M  %d %b %Y"))
        self.button("Time zone", info.get("Timezone", "?"), "Change", self.change_zone)
        self.switch("Set time automatically", "Uses internet time servers", info.get("NTP") == "yes",
                    lambda value: run(["timedatectl", "set-ntp", "true" if value else "false"]))
        self.switch("24-hour clock", None, settings.get_bool("CLOCK_24H"), self.set_24h)
        self.combo("Date format", DATE_FORMATS, settings.get("DATE_FORMAT", "%d %b %Y"), self.set_date)

    def change_zone(self):
        zones = out(["timedatectl", "list-timezones"]).splitlines()
        zone = choose(self.window, "Time zone", [(item, item.replace("_", " ")) for item in zones], searchable=True)
        if zone:
            result = run(["timedatectl", "set-timezone", zone], timeout=120)
            self.window.toast(f"Time zone set to {zone}" if result.code == 0 else (result.err.strip() or "Cancelled"))
            update_clocks()
            self.rebuild()

    def set_24h(self, value):
        Settings().set("CLOCK_24H", value)
        update_clocks()

    def set_date(self, value):
        Settings().set("DATE_FORMAT", value)
        update_clocks()


class WeatherPage(Page):
    def build(self):
        settings = Settings()
        self.switch("Show weather", "On the clock widget, from Open-Meteo (free, no account)",
                    settings.get_bool("WEATHER_ENABLED"), self.set_enabled)
        place = settings.get("WEATHER_PLACE") or "Not set"
        self.button("Location", place, "Change", self.change)
        self.button("Refresh now", None, "Refresh", self.refresh)

    def set_enabled(self, value):
        Settings().set("WEATHER_ENABLED", value)
        spawn(["nexus-hud", "restart"])

    def change(self):
        name = ask_text(self.window, "Weather location", "Town or city")
        if not name:
            return

        def done(places, error):
            if error or not places:
                self.window.toast("No places found. Check the spelling and the internet connection.")
                return
            index = choose(self.window, "Pick the right place",
                           [(str(i), place["label"]) for i, place in enumerate(places)])
            if index is None:
                return
            place = places[int(index)]
            settings = Settings()
            settings.set("WEATHER_PLACE", place["name"])
            settings.set("WEATHER_LAT", place["lat"])
            settings.set("WEATHER_LON", place["lon"])
            self.refresh()
            self.rebuild()

        self.task(lambda: weather.search(name), done, busy="Searching...")

    def refresh(self):
        self.task(lambda: weather.current(force=True), lambda text, e: (self.window.toast(text or "Weather off"),
                                                                       spawn(["nexus-hud", "restart"])))


PAGES = [
    ("time", "Date & time", "Time zone, 24-hour clock, date format", "time zone clock date 24 hour", TimePage),
    ("weather", "Weather", "Location for the clock widget", "weather location forecast", WeatherPage),
]
