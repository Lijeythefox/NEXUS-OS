import json
import time

from nexus.common import ETC_DIR, read_kv, runtime_dir

LI_ION_CURVE = [
    (4200, 100), (4150, 95), (4100, 90), (4000, 80), (3900, 65), (3800, 50),
    (3750, 40), (3700, 30), (3650, 20), (3600, 12), (3500, 5), (3300, 0),
]
STALE_SECONDS = 15


def state_file():
    return runtime_dir() / "battery.json"


def cells():
    try:
        return max(1, int(read_kv(ETC_DIR / "battery.conf").get("CELLS", "1")))
    except ValueError:
        return 1


def percent_from_mv(millivolts):
    per_cell = millivolts / cells()
    if per_cell >= LI_ION_CURVE[0][0]:
        return 100
    if per_cell <= LI_ION_CURVE[-1][0]:
        return 0
    for (high_mv, high_pct), (low_mv, low_pct) in zip(LI_ION_CURVE, LI_ION_CURVE[1:]):
        if low_mv <= per_cell <= high_mv:
            share = (per_cell - low_mv) / (high_mv - low_mv)
            return round(low_pct + share * (high_pct - low_pct))
    return 0


def write_state(data):
    data["time"] = time.time()
    path = state_file()
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data), encoding="utf-8")
    tmp.replace(path)


def read():
    try:
        data = json.loads(state_file().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"present": False}
    if time.time() - data.get("time", 0) > STALE_SECONDS:
        data["present"] = False
    return data


def summary():
    data = read()
    if not data.get("present"):
        return "NO SENSOR"
    text = f"{data.get('percent', 0)}%"
    if data.get("charging"):
        text += " CHG"
    return text
