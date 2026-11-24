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

echo "nexus-ws-state"
mkhypr() { # active workspace id, workspaces JSON
	mkdir -p "$T/hy"
	cat >"$T/hy/hyprctl" <<FAKE
#!/bin/bash
case "\$*" in
*activeworkspace*) echo '{"id": $1, "windows": 0}' ;;
*workspaces*) echo '$2' ;;
esac
FAKE
	chmod +x "$T/hy/hyprctl"
}
ws() { PATH="$T/hy:$PATH" bash "$BIN/nexus-ws-state" "$1"; }
ws_active() { mkhypr 2 '[{"id":1,"windows":1},{"id":2,"windows":0}]'; ws 2 | jq -e '.class == ["ws","active"] and .tooltip == false' >/dev/null; }
ws_occupied() { mkhypr 2 '[{"id":1,"windows":3},{"id":2,"windows":0}]'; ws 1 | jq -e '.class == ["ws","occupied"]' >/dev/null; }
ws_empty() { mkhypr 2 '[{"id":1,"windows":3},{"id":2,"windows":0}]'; ws 4 | jq -e '.class == ["ws","empty"]' >/dev/null; }
ws_no_hyprland() { mkdir -p "$T/hy"; printf '#!/bin/bash\nexit 1\n' >"$T/hy/hyprctl"; chmod +x "$T/hy/hyprctl"; ws 1 | jq -e '.class == ["ws","empty"]' >/dev/null; }
check "the workspace you are on is marked active" ws_active
check "a workspace with windows is marked occupied" ws_occupied
check "a workspace with no windows is marked empty" ws_empty
check "still prints valid output when Hyprland does not answer" ws_no_hyprland

echo "nexus-apps"
apps() { python3 "$BIN/nexus-apps" --conf "${CONF:-$SHARE/apps.conf}" --state "$T/state" "$@"; }
mkconf() { CONF="$T/apps-test.conf"; printf '%s\n' "$@" >"$CONF"; }
fakerel() { # owner/repo, JSON for its releases list
	mkdir -p "$T/api/repos/$1"
	printf '%s' "$2" >"$T/api/repos/$1/releases"
}
apps_conf_is_valid() { CONF="" apps check; }
apps_check_rejects_unknown_key() {
	mkconf '[x]' 'name = X' 'about = x' 'default = no' 'apt = x' 'colour = red'
	if apps check >"$T/o" 2>&1; then echo "exit 0"; return 1; fi
	grep -q colour "$T/o"
}
apps_check_rejects_app_with_nothing_to_install() {
	mkconf '[x]' 'name = X' 'about = x' 'default = no'
	if apps check >"$T/o" 2>&1; then echo "exit 0"; return 1; fi
	grep -q '\[x\]' "$T/o"
}
apps_pc_only_hidden_on_arm() {
	CONF="" apps --arch arm64 list >"$T/o" || return 1
	! grep -q '^arduino-ide' "$T/o" && CONF="" apps --arch amd64 list | grep -q '^arduino-ide'
}
apps_defaults_are_elijahs_list() {
	got="$(CONF="" apps --arch amd64 list | awk -F'\t' '$2=="yes"{print $1}' | sort | tr '\n' ' ')"
	[[ "$got" == "chromium everyday pico-tools python-tools ssh-server tailscale terminal-tools vscode " ]] || { echo "got: $got"; return 1; }
}
apps_shows_installed() {
	mkdir -p "$T/state"; touch "$T/state/thonny"
	CONF="" apps --arch amd64 list | awk -F'\t' '$1=="thonny"{print $3}' | grep -qx installed
}
apps_one_apt_call_without_recommends() {
	CONF="" apps --arch amd64 plan --install chromium,everyday >"$T/o" || return 1
	[[ "$(grep -c 'apt-get install' "$T/o")" == 1 ]] || { cat "$T/o"; return 1; }
	grep 'apt-get install' "$T/o" | grep -- '--no-install-recommends' | grep -q chromium && grep 'apt-get install' "$T/o" | grep -q mpv
}
apps_repo_added_before_install() {
	CONF="" apps --arch amd64 plan --install vscode >"$T/o" || return 1
	key=$(grep -n 'microsoft.asc' "$T/o" | head -1 | cut -d: -f1); inst=$(grep -n 'apt-get install' "$T/o" | cut -d: -f1)
	[[ -n "$key" && -n "$inst" && "$key" -lt "$inst" ]] || { cat "$T/o"; return 1; }
}
apps_ssh_switched_off() { CONF="" apps --arch amd64 plan --install ssh-server | grep -q 'systemctl disable --now ssh.service ssh.socket'; }
apps_pipx_runs_as_user() { CONF="" apps --arch amd64 plan --install pico-tools --user sam | grep -q 'as sam: pipx install mpremote'; }
apps_unknown_app_named() {
	if CONF="" apps plan --install nope >"$T/o" 2>&1; then echo "exit 0"; return 1; fi
	grep -q nope "$T/o"
}
apps_pc_only_refused_on_arm() {
	if CONF="" apps --arch arm64 plan --install arduino-ide >"$T/o" 2>&1; then echo "exit 0"; return 1; fi
	grep -qi 'PC only' "$T/o"
}
GODOT_REL='[{"tag_name":"4.5-stable","prerelease":false,"draft":false,"assets":[
 {"name":"Godot_v4.5-stable_mono_linux_x86_64.zip","browser_download_url":"https://x/mono.zip","digest":"sha256:aa"},
 {"name":"Godot_v4.5-stable_linux.x86_64.zip","browser_download_url":"https://x/amd.zip","digest":"sha256:bb"},
 {"name":"Godot_v4.5-stable_linux.arm64.zip","browser_download_url":"https://x/arm.zip","digest":"sha256:cc"}]}]'
apps_picks_file_for_machine() {
	fakerel godotengine/godot "$GODOT_REL"
	NEXUS_APPS_API="file://$T/api" CONF="" apps --arch amd64 resolve godot | grep -q 'https://x/amd.zip' &&
		NEXUS_APPS_API="file://$T/api" CONF="" apps --arch arm64 resolve godot | grep -q 'https://x/arm.zip'
}
apps_skips_test_releases() {
	fakerel Legcord/Legcord '[{"tag_name":"v2-beta","prerelease":true,"draft":false,"assets":[{"name":"Legcord-2-linux-amd64.deb","browser_download_url":"https://x/beta.deb"}]},
	 {"tag_name":"v1","prerelease":false,"draft":false,"assets":[{"name":"Legcord-1-linux-amd64.deb","browser_download_url":"https://x/stable.deb"}]}]'
	fakerel FreeTubeApp/FreeTube '[{"tag_name":"v2-beta","prerelease":true,"draft":false,"assets":[{"name":"freetube_2_amd64.deb","browser_download_url":"https://x/ft.deb"}]}]'
	NEXUS_APPS_API="file://$T/api" CONF="" apps --arch amd64 resolve legcord | grep -q stable.deb &&
		NEXUS_APPS_API="file://$T/api" CONF="" apps --arch amd64 resolve freetube | grep -q ft.deb
}
apps_no_file_names_the_app() {
	fakerel Lijeythefox/IRIS '[{"tag_name":"v1.0.2","prerelease":false,"draft":false,"assets":[{"name":"Iris_1.0.2_x64-setup.exe","browser_download_url":"https://x/iris.exe"}]}]'
	if NEXUS_APPS_API="file://$T/api" CONF="" apps --arch amd64 resolve iris >"$T/o" 2>&1; then echo "exit 0"; return 1; fi
	grep -q Iris "$T/o"
}
apps_download_checks_fingerprint() {
	echo hello >"$T/hello.deb"
	good="sha256:$(sha256sum "$T/hello.deb" | cut -d' ' -f1)"
	mkconf '[t]' 'name = T' 'about = t' 'default = no' 'arch = amd64' 'github = a/b' 'amd64_file = \.deb$' 'kind = deb'
	fakerel a/b "[{\"tag_name\":\"1\",\"prerelease\":false,\"draft\":false,\"assets\":[{\"name\":\"t.deb\",\"browser_download_url\":\"file://$T/hello.deb\",\"digest\":\"sha256:0000\"}]}]"
	if NEXUS_APPS_API="file://$T/api" apps --arch amd64 fetch t "$T/dl1" >"$T/o" 2>&1; then echo "accepted a bad fingerprint"; return 1; fi
	[[ ! -e "$T/dl1/t.deb" ]] || { echo "bad file kept"; return 1; }
	fakerel a/b "[{\"tag_name\":\"1\",\"prerelease\":false,\"draft\":false,\"assets\":[{\"name\":\"t.deb\",\"browser_download_url\":\"file://$T/hello.deb\",\"digest\":\"$good\"}]}]"
	NEXUS_APPS_API="file://$T/api" apps --arch amd64 fetch t "$T/dl2" && [[ -s "$T/dl2/t.deb" ]]
}
check "the app list has no mistakes" apps_conf_is_valid
check "the list check refuses an unknown setting and names it" apps_check_rejects_unknown_key
check "the list check refuses an app with nothing to install" apps_check_rejects_app_with_nothing_to_install
check "PC-only apps are hidden on ARM boards" apps_pc_only_hidden_on_arm
check "ticked by default: Elijah's list" apps_defaults_are_elijahs_list
check "installed apps are marked installed" apps_shows_installed
check "Debian packages go in one apt call without recommended extras" apps_one_apt_call_without_recommends
check "an app's extra repository is added before installing" apps_repo_added_before_install
check "the SSH server is switched off after installing" apps_ssh_switched_off
check "pipx tools are installed as the user, not root" apps_pipx_runs_as_user
check "an unknown app is refused by name" apps_unknown_app_named
check "a PC-only app is refused on an ARM board" apps_pc_only_refused_on_arm
check "the release file for this machine is picked" apps_picks_file_for_machine
check "test releases are skipped unless the app allows them" apps_skips_test_releases
check "no matching release file: the error names the app" apps_no_file_names_the_app
check "downloads with the wrong fingerprint are refused and deleted" apps_download_checks_fingerprint

echo
echo "$pass passed, $failed failed"
((failed == 0))
