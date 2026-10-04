import json
import sys
import time

from machine import ADC, Pin

HALL_PIN = 15
CHARGE_PIN = 14
BATTERY_ADC_PIN = 26
BUTTON_PINS = (
    ("up", 2), ("down", 3), ("left", 4), ("right", 5),
    ("a", 6), ("b", 7), ("x", 8), ("y", 9),
)
DIVIDER_RATIO = 2.0
REFERENCE_MV = 3300
REPORT_EVERY_MS = 2000
DEBOUNCE_MS = 40
BUTTON_DEBOUNCE_MS = 10
LOOP_MS = 2
SAMPLES = 16


class Debounced:
    def __init__(self, pin, settle_ms):
        self.pin = pin
        self.settle_ms = settle_ms
        self.raw = self.low()
        self.state = self.raw
        self.since = time.ticks_ms()

    def low(self):
        return self.pin.value() == 0

    def update(self, now):
        raw = self.low()
        if raw != self.raw:
            self.raw = raw
            self.since = now
        elif raw != self.state and time.ticks_diff(now, self.since) >= self.settle_ms:
            self.state = raw
            return True
        return False


charge = Pin(CHARGE_PIN, Pin.IN, Pin.PULL_UP)
battery = ADC(BATTERY_ADC_PIN)
led = Pin("LED", Pin.OUT)
lid = Debounced(Pin(HALL_PIN, Pin.IN, Pin.PULL_UP), DEBOUNCE_MS)
buttons = [(name, Debounced(Pin(pin, Pin.IN, Pin.PULL_UP), BUTTON_DEBOUNCE_MS)) for name, pin in BUTTON_PINS]


def battery_mv():
    total = 0
    for _ in range(SAMPLES):
        total += battery.read_u16()
        time.sleep_ms(1)
    return int(total / SAMPLES * REFERENCE_MV / 65535 * DIVIDER_RATIO)


def lid_state():
    return "closed" if lid.state else "open"


def button_state():
    return {name: button.state for name, button in buttons}


def send(event, **extra):
    message = {
        "nexus": "lid-sensor",
        "event": event,
        "lid": lid_state(),
        "buttons": button_state(),
    }
    message.update(extra)
    sys.stdout.write(json.dumps(message) + "\n")
    led.toggle()


def report(event):
    send(event, mv=battery_mv(), charging=charge.value() == 0)


last_report = time.ticks_ms()
report("boot")

while True:
    now = time.ticks_ms()
    for name, button in buttons:
        if button.update(now):
            send("button", button=name, pressed=button.state)
    if lid.update(now):
        report("lid")
        last_report = time.ticks_ms()
    if time.ticks_diff(now, last_report) >= REPORT_EVERY_MS:
        report("status")
        last_report = time.ticks_ms()
    time.sleep_ms(LOOP_MS)
