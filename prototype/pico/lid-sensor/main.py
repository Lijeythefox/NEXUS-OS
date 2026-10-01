import json
import sys
import time

from machine import ADC, Pin

HALL_PIN = 15
CHARGE_PIN = 14
BATTERY_ADC_PIN = 26
DIVIDER_RATIO = 2.0
REFERENCE_MV = 3300
REPORT_EVERY_MS = 2000
DEBOUNCE_MS = 40
SAMPLES = 16

hall = Pin(HALL_PIN, Pin.IN, Pin.PULL_UP)
charge = Pin(CHARGE_PIN, Pin.IN, Pin.PULL_UP)
battery = ADC(BATTERY_ADC_PIN)
led = Pin("LED", Pin.OUT)


def battery_mv():
    total = 0
    for _ in range(SAMPLES):
        total += battery.read_u16()
        time.sleep_ms(1)
    return int(total / SAMPLES * REFERENCE_MV / 65535 * DIVIDER_RATIO)


def lid_state():
    return "closed" if hall.value() == 0 else "open"


def report(event, lid):
    message = {
        "nexus": "lid-sensor",
        "event": event,
        "lid": lid,
        "mv": battery_mv(),
        "charging": charge.value() == 0,
    }
    sys.stdout.write(json.dumps(message) + "\n")
    led.toggle()


last_lid = lid_state()
last_report = time.ticks_ms()
report("boot", last_lid)

while True:
    current = lid_state()
    if current != last_lid:
        time.sleep_ms(DEBOUNCE_MS)
        if lid_state() == current:
            last_lid = current
            report("lid", last_lid)
            last_report = time.ticks_ms()
    if time.ticks_diff(time.ticks_ms(), last_report) >= REPORT_EVERY_MS:
        report("status", last_lid)
        last_report = time.ticks_ms()
    time.sleep_ms(20)
