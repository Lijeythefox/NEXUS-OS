#!/bin/bash
# Unit tests for the NEXUS commands. Run from the repo root: bash ci/tests.sh
set -uo pipefail
cd "$(dirname "$0")/.."
ROOT="$PWD"
BIN="$ROOT/overlay/usr/local/bin"
SBIN="$ROOT/overlay/usr/local/sbin"
SHARE="$ROOT/overlay/usr/share/nexus"
pass=0; failed=0
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT

ok() { pass=$((pass + 1)); echo "  ok   $1"; }
bad() { failed=$((failed + 1)); echo "  FAIL $1: $2"; }
check() { # name, command...
	local name="$1"; shift
	if "$@" >"$T/out" 2>&1; then ok "$name"; else bad "$name" "$(tail -3 "$T/out" | tr '\n' ' ')"; fi
}

echo "nexus-theme"
theme_fills_everything() {
	rm -rf "$T/r" && python3 "$BIN/nexus-theme" --share "$SHARE" render tokyo-night "$T/r" || return 1
	[[ -n "$(ls "$T/r")" ]] || { echo "nothing rendered"; return 1; }
	! grep -rn '{{' "$T/r"
}
theme_rejects_unknown_key() {
	mkdir -p "$T/s/themes/x" "$T/s/templates"
	cp "$SHARE/themes/tokyo-night/theme.conf" "$T/s/themes/x/"
	echo 'colour={{nope}}' >"$T/s/templates/bad.conf"
	if python3 "$BIN/nexus-theme" --share "$T/s" render x "$T/r2" 2>"$T/err"; then echo "exit 0 on unknown key"; return 1; fi
	grep -q 'nope' "$T/err"
}
theme_three_forms() {
	mkdir -p "$T/f/themes/x" "$T/f/templates"
	printf 'bg=#1a1b26\n' >"$T/f/themes/x/theme.conf"
	printf '%s\n' '{{bg}} {{bg_hex}} {{bg_rgb}}' >"$T/f/templates/t.txt"
	python3 "$BIN/nexus-theme" --share "$T/f" render x "$T/r3" || return 1
	[[ "$(cat "$T/r3/t.txt")" == "#1a1b26 1a1b26 26,27,38" ]] || { cat "$T/r3/t.txt"; return 1; }
}
theme_rejects_bad_colour() {
	mkdir -p "$T/b/themes/x" "$T/b/templates"
	printf 'bg=blue\n' >"$T/b/themes/x/theme.conf"
	echo '{{bg}}' >"$T/b/templates/t.txt"
	if python3 "$BIN/nexus-theme" --share "$T/b" render x "$T/r4" 2>"$T/err4"; then echo "exit 0 on bad colour"; return 1; fi
	grep -q 'bg' "$T/err4" && grep -qi 'colour' "$T/err4"
}
theme_ensure_creates_current() {
	HOME="$T/home1" python3 "$BIN/nexus-theme" --share "$SHARE" ensure || return 1
	[[ -s "$T/home1/.config/nexus/current/waybar.css" ]] || { echo "no waybar.css"; return 1; }
	[[ "$(cat "$T/home1/.config/nexus/theme")" == "tokyo-night" ]]
}
theme_ensure_keeps_user_choice() {
	mkdir -p "$T/home2/.config/nexus"; echo "tokyo-night" >"$T/home2/.config/nexus/theme"
	HOME="$T/home2" python3 "$BIN/nexus-theme" --share "$SHARE" ensure || return 1
	HOME="$T/home2" python3 "$BIN/nexus-theme" --share "$SHARE" current | grep -qx tokyo-night
}
check "render fills every placeholder" theme_fills_everything
check "render fails on an unknown placeholder and names it" theme_rejects_unknown_key
check "placeholders come as #hex, hex and r,g,b" theme_three_forms
check "render fails on a colour that is not #rrggbb" theme_rejects_bad_colour
check "ensure renders the default theme on first run" theme_ensure_creates_current
check "ensure keeps the saved theme" theme_ensure_keeps_user_choice

echo "nexus-session"
mkfake() { # dir, seconds to stay alive
	mkdir -p "$1"; printf '#!/bin/bash\necho fake-hyprland started\nsleep %s\n' "$2" >"$1/start-hyprland"; chmod +x "$1/start-hyprland"
	printf '#!/bin/bash\nexit 0\n' >"$1/nexus-theme"; chmod +x "$1/nexus-theme"
}
session() { # fake dir, fast-fail limit in seconds; prints output, returns the exit code
	env -i HOME="$T/sh" PATH="$1:/usr/bin:/bin" NEXUS_FAST_FAIL_SECS="$2" bash "$BIN/nexus-session"
}
fresh_home() { rm -rf "$T/sh"; mkdir -p "$T/sh"; }
session_gives_up_after_three_fast_failures() {
	fresh_home; mkfake "$T/fake0" 0
	session "$T/fake0" 5 >"$T/s1" 2>&1; local c1=$?
	session "$T/fake0" 5 >"$T/s2" 2>&1; local c2=$?
	session "$T/fake0" 5 >"$T/s3" 2>&1; local c3=$?
	[[ $c1 -eq 1 && $c2 -eq 1 ]] || { echo "runs 1 and 2 should exit 1, got $c1 $c2"; return 1; }
	[[ $c3 -eq 3 ]] || { echo "run 3 should exit 3 (stay in the shell), got $c3"; return 1; }
	grep -q "hyprland.log" "$T/s3" || { echo "log path not shown"; return 1; }
}
session_long_run_resets_counter() {
	fresh_home; mkfake "$T/fake0" 0; mkfake "$T/fake2" 2
	session "$T/fake0" 1 >/dev/null 2>&1; session "$T/fake0" 1 >/dev/null 2>&1
	session "$T/fake2" 1 >/dev/null 2>&1; local long=$?
	[[ $long -eq 0 ]] || { echo "a long run should exit 0, got $long"; return 1; }
	session "$T/fake0" 1 >/dev/null 2>&1; local c=$?
	[[ $c -eq 1 ]] || { echo "should not give up after a long run in between, got $c"; return 1; }
	[[ "$(cat "$T/sh/.cache/nexus/session-fails")" == "1" ]] || { echo "counter is not 1"; return 1; }
}
session_writes_log() {
	fresh_home; mkfake "$T/fake0" 0
	session "$T/fake0" 5 >/dev/null 2>&1
	grep -q "fake-hyprland started" "$T/sh/.cache/nexus/hyprland.log"
}
session_without_hyprland_says_so() {
	fresh_home; mkdir -p "$T/empty"; printf '#!/bin/bash\nexit 0\n' >"$T/empty/nexus-theme"; chmod +x "$T/empty/nexus-theme"
	session "$T/empty" 5 >"$T/s5" 2>&1
	grep -qi "not installed" "$T/sh/.cache/nexus/hyprland.log"
}
check "gives up after three fast failures and shows the log path" session_gives_up_after_three_fast_failures
check "a run longer than the limit resets the failure count" session_long_run_resets_counter
check "Hyprland output goes to ~/.cache/nexus/hyprland.log" session_writes_log
check "says so in the log when Hyprland is not installed" session_without_hyprland_says_so

echo "nexus-getty"
getty() { env NEXUS_FIRSTLOGIN_MARKER="$T/marker" NEXUS_AUTOLOGIN_FILE="$T/autologin-user" NEXUS_NO_AUTOLOGIN_FILE="$T/no-autologin" AGETTY=echo bash "$SBIN/nexus-getty" linux; }
getty_root_during_setup() { rm -f "$T/no-autologin"; touch "$T/marker"; echo sam >"$T/autologin-user"; getty | grep -q -- '--autologin root'; }
getty_user_after_setup() { rm -f "$T/marker" "$T/no-autologin"; echo sam >"$T/autologin-user"; getty | grep -q -- '--autologin sam'; }
getty_prompt_when_switched_off() { rm -f "$T/marker"; echo sam >"$T/autologin-user"; touch "$T/no-autologin"; getty >"$T/g" || return 1; grep -q -- '--noclear' "$T/g" && ! grep -q -- '--autologin' "$T/g"; }
getty_never_autologins_root_after_setup() { rm -f "$T/marker" "$T/no-autologin"; echo root >"$T/autologin-user"; getty >"$T/g" || return 1; grep -q -- '--noclear' "$T/g" && ! grep -q -- '--autologin' "$T/g"; }
check "auto-logs in root while Armbian's first-run setup is pending" getty_root_during_setup
check "auto-logs in the desktop user after setup" getty_user_after_setup
check "plain login prompt when auto-login is switched off" getty_prompt_when_switched_off
check "never auto-logs in root once setup is done" getty_never_autologins_root_after_setup

echo
echo "$pass passed, $failed failed"
((failed == 0))
