#!/bin/bash
# Runs inside a debian:trixie container on GitHub (see .github/workflows/check.yml).
#   1. installs the real package lists (fails the check if anything is missing)
#   2. copies overlay/ into place and verifies the Hyprland config (fails the check on errors)
#   3. checks the terminal and launcher configs and that every command the desktop calls exists
# Everything it learns is written to ci-out/.
set -uo pipefail
cd "$(dirname "$0")/.."
OUT="$PWD/ci-out"
mkdir -p "$OUT"
export DEBIAN_FRONTEND=noninteractive
result() { echo "$1" | tee -a "$OUT/result.txt"; }
: >"$OUT/result.txt"

echo "::group::Install packages"
if bash tools/install-packages.sh config/packages.txt config/packages-backports.txt >"$OUT/packages.log" 2>&1; then
	result "PACKAGES=ok"
else
	tail -n 60 "$OUT/packages.log"
	result "PACKAGES=FAILED"
	exit 1
fi
tail -n 5 "$OUT/packages.log"
dpkg-query -W -f='${Package} ${Version}\n' hyprland hyprlock hypridle hyprpolkitagent xdg-desktop-portal-hyprland \
	waybar fuzzel mako-notifier swayosd foot libgl1-mesa-dri >"$OUT/versions.txt" 2>&1
cat "$OUT/versions.txt"
apt-get install -y --no-install-recommends jq librsvg2-bin >>"$OUT/packages.log" 2>&1
echo "::endgroup::"

echo "::group::Install overlay"
cp -a overlay/. /
chmod 0755 /usr/local/bin/nexus-* /usr/local/sbin/nexus-*
python3 tools/make-wallpapers.py /usr/share/nexus/themes/tokyo-night/theme.conf /usr/share/nexus/themes/tokyo-night/wallpapers
useradd -m -s /bin/bash tester
echo "::endgroup::"

echo "::group::Verify the Hyprland config"
install -d -m 0700 -o tester -g tester /tmp/xdg-tester
su tester -c 'nexus-theme ensure && ls ~/.config/nexus/current' >"$OUT/verify.log" 2>&1
# The packaged Hyprland binary carries an extra file permission (for smoother scheduling)
# that an ordinary container may not run. A plain copy has none and checks the config the same way.
cp /usr/bin/Hyprland /tmp/Hyprland-check
chmod 0755 /tmp/Hyprland-check
su tester -c 'XDG_RUNTIME_DIR=/tmp/xdg-tester NEXUS_STRICT=1 /tmp/Hyprland-check --verify-config' >>"$OUT/verify.log" 2>&1
verify_rc=$?
cat "$OUT/verify.log"
if ((verify_rc == 0)) && grep -q 'config ok' "$OUT/verify.log"; then
	result "VERIFY=ok"
else
	result "VERIFY=FAILED (exit $verify_rc)"
	exit 1
fi
# Prove the check can fail: a config with a made-up setting must NOT pass.
printf 'hl.config({ general = { this_setting_does_not_exist = 1 } })\n' >/tmp/bad-config.lua
chmod 0644 /tmp/bad-config.lua
if su tester -c 'XDG_RUNTIME_DIR=/tmp/xdg-tester /tmp/Hyprland-check --verify-config -c /tmp/bad-config.lua' 2>&1 | tee "$OUT/verify-selftest.log" | grep -q 'config ok'; then
	result "VERIFY_SELFTEST=FAILED (a broken config passed the check)"
	exit 1
fi
result "VERIFY_SELFTEST=ok"
echo "::endgroup::"

echo "::group::Check the launcher and terminal configs"
cur=/home/tester/.config/nexus/current
other=ok
if ! su tester -c "foot --check-config -c $cur/foot.ini" >"$OUT/foot.log" 2>&1; then other=FAILED; fi
cat "$OUT/foot.log"
if ! su tester -c "fuzzel --check-config --config $cur/fuzzel.ini" >"$OUT/fuzzel.log" 2>&1; then other=FAILED; fi
cat "$OUT/fuzzel.log"
jq empty /usr/share/nexus/default/waybar/config.json || other=FAILED
for command in waybar mako swayosd-server swayosd-client swaybg hyprlock hypridle grim slurp wl-copy notify-send \
	brightnessctl playerctl thunar start-hyprland hyprctl Xwayland wpctl nmcli jq pkill; do
	command -v "$command" >/dev/null || { echo "missing command: $command"; other=FAILED; }
done
result "OTHER_CONFIGS=$other"
[[ "$other" == ok ]] || exit 1
echo "::endgroup::"

echo "::group::Check the app installer list"
apps=ok
nexus-apps check || apps=FAILED
# Every Debian package the installer can install must exist in Debian 13 (a dry run, nothing is installed).
pkgs="$(nexus-apps --arch amd64 apt-packages)"
echo "$pkgs"
if ! apt-get install -s --no-install-recommends $pkgs >"$OUT/apps-apt.log" 2>&1; then
	grep -E '^E:|Unable|has no installation candidate' "$OUT/apps-apt.log" | head -20
	# Show what Debian does have with a similar name, to make fixing apps.conf quick.
	for missing in $(grep -oP "Unable to locate package \K\S+" "$OUT/apps-apt.log"); do
		echo "Similar to $missing:"
		apt-cache search --names-only "^$(echo "$missing" | cut -d- -f1)" | head -40 | sed 's/^/   /'
	done
	apps=FAILED
fi
result "APPS_LIST=$apps"
[[ "$apps" == ok ]] || exit 1
fuzzel --help 2>&1 | grep -q -- '--select-index' && result "FUZZEL_SELECT_INDEX=yes" || result "FUZZEL_SELECT_INDEX=no"
echo "::endgroup::"

echo "::group::Try real installs (a Debian app, a zip download, an AppImage download)"
# Downloads depend on GitHub, so a failure here is reported but doesn't fail the check.
if nexus-apps --arch amd64 apply --install terminal-tools,godot,prism --user tester >"$OUT/apps-install.log" 2>&1 &&
	command -v btop >/dev/null && [[ -x /usr/local/bin/godot && -x /usr/local/bin/prismlauncher ]] &&
	ls /usr/share/applications/nexus-godot.desktop /usr/share/applications/nexus-prism.desktop >/dev/null; then
	result "APPS_INSTALL=ok"
else
	result "APPS_INSTALL=FAILED (see apps-install.log; not blocking)"
fi
tail -n 25 "$OUT/apps-install.log"
echo "::endgroup::"

chmod -R a+rX "$OUT"
cat "$OUT/result.txt"
exit 0
