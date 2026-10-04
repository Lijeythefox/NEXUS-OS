# Pico lid, battery and deck button sensor

A Raspberry Pi Pico (or Pico W) plugged into one of the deck's USB ports. It tells NEXUS OS when the screen arm folds shut, how full the battery is, and when the deck's 8 built-in buttons are pressed. The Radxa Zero 3W has no GPIO pins, so the Pico does that job instead.

## Wiring

| Pico pin | Connects to |
| --- | --- |
| GP15 (pin 20) | Hall sensor output (for example A3144 or DRV5032). The magnet in the hinge pulls it to GND when the lid is closed. |
| 3V3 (pin 36) | Hall sensor power |
| GND (pin 38) | Hall sensor GND and battery minus |
| GP26 / ADC0 (pin 31) | Middle of a voltage divider from battery plus: 100 kΩ from battery plus to GP26, 100 kΩ from GP26 to GND |
| GP14 (pin 19) | Optional: the charger board's CHRG pin (it goes low while charging). Leave it unconnected if your charger doesn't have one. |

The two 100 kΩ resistors halve the battery voltage so it's safe for the Pico (it must stay under 3.3 V at GP26). That's what `DIVIDER_RATIO = 2.0` in `main.py` means. If you use different resistors, set `DIVIDER_RATIO` to (top + bottom) ÷ bottom.

For a battery pack with more than one cell in series (for example 2S = 7.4 V), use a bigger divider and set `CELLS=2` in `/etc/nexus/battery.conf` on the deck.

## Deck buttons

The D-pad on the left and the A, B, X, Y diamond on the right, next to the controller cradles. Each button has two legs: one goes to its Pico pin, the other to any GND pin (pins 3, 8, 13, 18, 23, 28 or 38). No resistors needed: the Pico's built-in pull-ups are switched on in `main.py`.

| Button | Pico pin | Shows up in games as |
| --- | --- | --- |
| D-pad up | GP2 (pin 4) | D-pad up |
| D-pad down | GP3 (pin 5) | D-pad down |
| D-pad left | GP4 (pin 6) | D-pad left |
| D-pad right | GP5 (pin 7) | D-pad right |
| A (bottom of the diamond) | GP6 (pin 9) | South button |
| B (right of the diamond) | GP7 (pin 10) | East button |
| X (left of the diamond) | GP8 (pin 11) | West button |
| Y (top of the diamond) | GP9 (pin 12) | North button |

Games go by position, not by the letter printed on the button. If your diamond is labelled the Nintendo way round (X on top, Y on the left), wire by **position**, so the top button goes to GP9 and the left one to GP8.

NEXUS turns these buttons into a controller called **NEXUS Deck Buttons**, which RetroArch and ES-DE pick up automatically. To check each button, open **Settings > Bluetooth & devices > Controller > Deck button test**.

## Flashing the Pico

1. Hold BOOTSEL on the Pico and plug it into the deck. It shows up as a USB drive.
2. Copy the MicroPython `.uf2` file for your Pico onto it. Get it from micropython.org.
3. Open **Thonny** on the deck. Choose the interpreter "MicroPython (Raspberry Pi Pico)".
4. Open `main.py` from this folder and save it to the Pico as `main.py`.
5. Unplug the Pico and plug it back in. Its LED blinks every 2 seconds while it's reporting, and flickers when you press a deck button.

## Programming other Picos

NEXUS only listens to a Pico that sends `"nexus": "lid-sensor"` messages, so your other Pico projects are left alone. To reprogram the sensor Pico itself, open **Settings > System > Power & battery > Pico sensor > Pause** first, then press **Resume** when you're done. While it's paused, the lid sensor, battery level and deck buttons all stop working.
