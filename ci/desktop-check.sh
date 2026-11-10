#!/bin/bash
# Runs inside a debian:trixie container on GitHub (see .github/workflows/check.yml).
#   1. installs the real package lists (fails the check if anything is missing)
#   2. copies overlay/ into place and verifies the Hyprland config (fails the check on errors)
#   3. starts the whole desktop without a screen and takes screenshots (information only)
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
apt-get install -y --no-install-recommends procps psmisc jq librsvg2-bin >>"$OUT/packages.log" 2>&1
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
su tester -c 'XDG_RUNTIME_DIR=/tmp/xdg-tester NEXUS_STRICT=1 Hyprland --verify-config' >>"$OUT/verify.log" 2>&1
verify_rc=$?
cat "$OUT/verify.log"
if ((verify_rc == 0)) && ! grep -qiE 'config error|error in|errors found' "$OUT/verify.log"; then
	result "VERIFY=ok"
else
	result "VERIFY=FAILED (exit $verify_rc)"
	exit 1
fi
echo "::endgroup::"

echo "::group::Run the desktop without a screen"
ls -l /dev/dri 2>&1 | tee "$OUT/dri.txt"
chmod -R a+rw /dev/dri 2>/dev/null
cp ci/headless-session.sh /tmp/headless-session.sh
chmod 0755 /tmp/headless-session.sh
install -d -o tester -g tester /tmp/shots
timeout 240 su tester -c 'XDG_RUNTIME_DIR=/tmp/xdg-tester dbus-run-session -- /tmp/headless-session.sh /tmp/shots' >"$OUT/headless.log" 2>&1
headless_rc=$?
cat "$OUT/headless.log"
cp /tmp/shots/* "$OUT/" 2>/dev/null
cp /home/tester/hyprland-headless.log "$OUT/" 2>/dev/null
if ((headless_rc == 0)); then result "HEADLESS=ok"; else result "HEADLESS=FAILED (exit $headless_rc)"; fi
echo "::endgroup::"

chmod -R a+rX "$OUT"
cat "$OUT/result.txt"
exit 0
