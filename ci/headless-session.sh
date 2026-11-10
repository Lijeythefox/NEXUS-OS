#!/bin/bash
# Started by ci/desktop-check.sh as a normal user. Runs Hyprland with no screen,
# pokes at it and saves screenshots into the folder given as $1.
shots="$1"
export HYPRLAND_HEADLESS_ONLY=1 NEXUS_STRICT=1 NEXUS_NO_LOCK=1
cd "$HOME" || exit 1
problems=0
say() { echo "[headless] $*"; }
h() { hyprctl -i 0 "$@"; }

Hyprland >"$HOME/hyprland-headless.log" 2>&1 &
hypr_pid=$!

for _ in $(seq 1 40); do
	h version >/dev/null 2>&1 && break
	kill -0 "$hypr_pid" 2>/dev/null || break
	sleep 1
done
if ! h version >/dev/null 2>&1; then
	say "Hyprland did not come up. Last log lines:"
	tail -n 40 "$HOME/hyprland-headless.log"
	exit 1
fi
h version | head -n 2

sig="$(basename "$(find "$XDG_RUNTIME_DIR/hypr" -mindepth 1 -maxdepth 1 -type d | head -n 1)")"
export HYPRLAND_INSTANCE_SIGNATURE="$sig"
wl="$(find "$XDG_RUNTIME_DIR" -maxdepth 1 -name 'wayland-*' ! -name '*.lock' -printf '%f\n' | head -n 1)"
export WAYLAND_DISPLAY="$wl"
say "instance $sig on $wl"

if [[ "$(h -j monitors | jq 'length')" == 0 ]]; then
	say "no monitor yet, creating a headless one"
	h output create headless
	sleep 1
fi
h monitors | head -n 4

say "config errors (should be empty):"
errors="$(h configerrors)"
echo "$errors"
if [[ -n "$(echo "$errors" | tr -d '[:space:]')" ]]; then problems=$((problems + 1)); fi

sleep 6
say "layers:"
h layers | grep -E 'namespace|Layer level' | head -n 20
for proc in waybar mako swayosd-server hypridle swaybg; do
	if pidof "$proc" >/dev/null; then say "running: $proc"; else say "NOT running: $proc"; problems=$((problems + 1)); fi
done

h dispatch 'hl.dsp.exec_cmd("foot")'
sleep 2
h dispatch 'hl.dsp.exec_cmd("foot -e sh -c \"nexus-bench; sleep 60\"")'
sleep 4
say "windows open: $(h -j clients | jq 'length')"
grim "$shots/shot-1-desktop.png" && say "saved shot-1-desktop.png"

nexus-launcher &
sleep 2
grim "$shots/shot-2-launcher.png" && say "saved shot-2-launcher.png"
pkill -x fuzzel

nexus-menu &
sleep 2
grim "$shots/shot-3-menu.png" && say "saved shot-3-menu.png"
pkill -x fuzzel

say "old-style dispatch (what Waybar's workspace click uses):"
h dispatch workspace 2
say "new-style dispatch:"
h dispatch 'hl.dsp.focus({ workspace = 2 })'
sleep 1
say "active workspace: $(h -j activeworkspace | jq '.id')"
grim "$shots/shot-4-workspace2.png" && say "saved shot-4-workspace2.png"
h dispatch 'hl.dsp.focus({ workspace = 1 })'
sleep 1

notify-send "NEXUS OS" "Notification test from the build check"
nexus-osd volume up
sleep 1
grim "$shots/shot-5-notification.png" && say "saved shot-5-notification.png"

nexus-lock >"$HOME/hyprlock.log" 2>&1 &
sleep 4
if pidof hyprlock >/dev/null; then say "lock screen is running"; else say "lock screen did NOT stay running"; tail -n 15 "$HOME/hyprlock.log"; problems=$((problems + 1)); fi
grim "$shots/shot-6-lock.png" 2>/dev/null && say "saved shot-6-lock.png"
pkill -USR1 hyprlock
sleep 1

say "waybar messages:"
grep -iE 'error|warn' "$HOME/hyprland-headless.log" | grep -i waybar | head -n 10
say "problems found: $problems"
h dispatch 'hl.dsp.exit()'
sleep 2
kill "$hypr_pid" 2>/dev/null
exit "$problems"
