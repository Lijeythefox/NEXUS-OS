import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

from nexus.common import Settings

CACHE_SECONDS = 1800
CODES = {
    0: "CLEAR", 1: "MOSTLY CLEAR", 2: "PART CLOUDY", 3: "OVERCAST", 45: "FOG", 48: "FOG",
    51: "DRIZZLE", 53: "DRIZZLE", 55: "DRIZZLE", 56: "ICY DRIZZLE", 57: "ICY DRIZZLE",
    61: "RAIN", 63: "RAIN", 65: "HEAVY RAIN", 66: "ICY RAIN", 67: "ICY RAIN",
    71: "SNOW", 73: "SNOW", 75: "HEAVY SNOW", 77: "SNOW GRAINS", 80: "SHOWERS", 81: "SHOWERS",
    82: "HEAVY SHOWERS", 85: "SNOW SHOWERS", 86: "SNOW SHOWERS", 95: "STORM", 96: "STORM", 99: "STORM",
}


def cache_file():
    path = Path.home() / ".cache" / "nexus"
    path.mkdir(parents=True, exist_ok=True)
    return path / "weather.json"


def fetch_json(url, timeout=8):
    request = urllib.request.Request(url, headers={"User-Agent": "NEXUS-OS"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def search(name):
    query = urllib.parse.urlencode({"name": name, "count": 6, "language": "en", "format": "json"})
    data = fetch_json(f"https://geocoding-api.open-meteo.com/v1/search?{query}")
    places = []
    for item in data.get("results") or []:
        label = ", ".join(part for part in (item.get("name"), item.get("admin1"), item.get("country")) if part)
        places.append({"label": label, "name": item.get("name", ""), "lat": item["latitude"], "lon": item["longitude"]})
    return places


def current(force=False):
    settings = Settings()
    if not settings.get_bool("WEATHER_ENABLED"):
        return ""
    lat, lon = settings.get("WEATHER_LAT"), settings.get("WEATHER_LON")
    if not lat or not lon:
        return "SET LOCATION IN SETTINGS"
    path = cache_file()
    try:
        cached = json.loads(path.read_text(encoding="utf-8"))
        if not force and time.time() - cached["time"] < CACHE_SECONDS and cached.get("key") == f"{lat},{lon}":
            return cached["text"]
    except (OSError, ValueError, KeyError):
        cached = None
    query = urllib.parse.urlencode({
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,weather_code,wind_speed_10m",
        "timezone": "auto",
    })
    try:
        data = fetch_json(f"https://api.open-meteo.com/v1/forecast?{query}")
        now = data["current"]
        place = settings.get("WEATHER_PLACE", "").upper()
        text = f"{place}  {round(now['temperature_2m'])}°C  {CODES.get(now['weather_code'], 'UNKNOWN')}".strip()
    except Exception:
        return cached["text"] + " (OLD)" if cached else "WEATHER OFFLINE"
    path.write_text(json.dumps({"time": time.time(), "key": f"{lat},{lon}", "text": text}), encoding="utf-8")
    return text


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    print(current(force="--refresh" in argv))
    return 0
