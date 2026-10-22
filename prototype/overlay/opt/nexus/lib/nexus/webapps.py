import configparser
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

from nexus.common import spawn

APPS_DIR = Path.home() / ".local/share/applications"
ICON_DIR = Path.home() / ".local/share/nexus/webapp-icons"
PREFIX = "nexus-web-"
URL_KEY = "X-Nexus-WebApp-URL"
CHROMIUM_LIKE = ("chromium", "brave", "vivaldi", "google-chrome", "microsoft-edge")
SUGGESTIONS = [
    ("YouTube Music", "https://music.youtube.com"),
    ("Discord", "https://discord.com/app"),
    ("Twitch", "https://www.twitch.tv"),
    ("Google Drive", "https://drive.google.com"),
    ("GitHub", "https://github.com"),
]


def clean_url(text):
    text = text.strip()
    if not re.match(r"^[a-z][a-z0-9+.-]*://", text, re.IGNORECASE):
        text = "https://" + text
    parts = urllib.parse.urlsplit(text)
    if parts.scheme not in ("http", "https") or not parts.netloc or any(char.isspace() for char in text):
        raise ValueError("That doesn't look like a web address. Try something like music.youtube.com")
    return text


def clean_name(text):
    name = re.sub(r"[\r\n\t]", " ", text).strip()[:40]
    if not name:
        raise ValueError("Give the web app a name")
    return name


def slug_for(name):
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "app"
    slug, number = base, 2
    while (APPS_DIR / f"{PREFIX}{slug}.desktop").exists():
        slug, number = f"{base}-{number}", number + 1
    return slug


def fetch_icon(url, slug):
    try:
        import gi

        gi.require_version("GdkPixbuf", "2.0")
        from gi.repository import GdkPixbuf
    except (ImportError, ValueError):
        return None
    parts = urllib.parse.urlsplit(url)
    request = urllib.request.Request(f"{parts.scheme}://{parts.netloc}/favicon.ico",
                                     headers={"User-Agent": "Mozilla/5.0 NEXUS-OS"})
    try:
        with urllib.request.urlopen(request, timeout=6) as response:
            data = response.read(512 * 1024)
        loader = GdkPixbuf.PixbufLoader()
        loader.write(data)
        loader.close()
        pixbuf = loader.get_pixbuf().scale_simple(64, 64, GdkPixbuf.InterpType.BILINEAR)
        ICON_DIR.mkdir(parents=True, exist_ok=True)
        target = ICON_DIR / f"{slug}.png"
        pixbuf.savev(str(target), "png", [], [])
        return str(target)
    except Exception:
        return None


def add(name, url):
    name = clean_name(name)
    url = clean_url(url)
    slug = slug_for(name)
    icon = fetch_icon(url, slug) or "web-browser"
    host = urllib.parse.urlsplit(url).netloc
    APPS_DIR.mkdir(parents=True, exist_ok=True)
    (APPS_DIR / f"{PREFIX}{slug}.desktop").write_text(
        "\n".join([
            "[Desktop Entry]",
            "Type=Application",
            f"Name={name}",
            f"Comment=Web app: {host}",
            f"Exec=nexus-webapp {slug}",
            f"Icon={icon}",
            "Terminal=false",
            "Categories=Network;",
            f"{URL_KEY}={url}",
            "",
        ]),
        encoding="utf-8",
    )
    return slug


def read(path):
    parser = configparser.ConfigParser(interpolation=None, strict=False)
    try:
        parser.read(path, encoding="utf-8")
        section = parser["Desktop Entry"]
    except (configparser.Error, KeyError):
        return None
    return {"slug": path.stem[len(PREFIX):], "name": section.get("Name", path.stem),
            "url": section.get(URL_KEY, ""), "icon": section.get("Icon", "")}


def listing():
    found = [read(path) for path in sorted(APPS_DIR.glob(f"{PREFIX}*.desktop"))]
    return [app for app in found if app and app["url"]]


def remove(slug):
    for app in listing():
        if app["slug"] == slug:
            (APPS_DIR / f"{PREFIX}{slug}.desktop").unlink(missing_ok=True)
            if app["icon"].startswith(str(ICON_DIR)):
                Path(app["icon"]).unlink(missing_ok=True)
            return True
    return False


def browser_command():
    try:
        import gi

        gi.require_version("Gio", "2.0")
        from gi.repository import Gio

        app = Gio.AppInfo.get_default_for_uri_scheme("https")
        executable = app.get_executable() if app else ""
    except (ImportError, ValueError):
        executable = ""
    return executable or "chromium"


def open_url(url):
    browser = browser_command()
    name = os.path.basename(browser)
    if any(name.startswith(prefix) for prefix in CHROMIUM_LIKE):
        return spawn([browser, f"--app={url}"])
    if name.startswith("firefox"):
        return spawn([browser, "--new-window", url])
    return spawn(["xdg-open", url])


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print("usage: nexus-webapp NAME", file=sys.stderr)
        return 2
    for app in listing():
        if app["slug"] == argv[0]:
            return 0 if open_url(app["url"]) else 1
    print(f"No web app called {argv[0]}", file=sys.stderr)
    return 1
