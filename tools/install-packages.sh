#!/bin/bash
# Installs the NEXUS package lists. Used both by the image build and by the
# GitHub check, so the check tests exactly what the image will get.
#   install-packages.sh PACKAGES.TXT PACKAGES-BACKPORTS.TXT
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
stable_list="$1"
backports_list="$2"

read_list() {
	sed -e 's/\r$//' -e 's/#.*//' -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' "$1" | grep -v '^$' || true
}

# shellcheck disable=SC1091
codename="$(. /etc/os-release && echo "${VERSION_CODENAME:-trixie}")"

if ! grep -rqs "${codename}-backports" /etc/apt/sources.list /etc/apt/sources.list.d 2>/dev/null; then
	echo "[nexus] Adding Debian ${codename}-backports (only the Hyprland family is installed from it)"
	cat >/etc/apt/sources.list.d/nexus-backports.sources <<SRC
Types: deb
URIs: http://deb.debian.org/debian
Suites: ${codename}-backports
Components: main
Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg
SRC
fi

apt-get update

mapfile -t stable < <(read_list "$stable_list")
mapfile -t backports < <(read_list "$backports_list")

echo "[nexus] Installing ${#stable[@]} packages from Debian ${codename}"
apt-get install -y --no-install-recommends "${stable[@]}"

echo "[nexus] Installing ${#backports[@]} packages from ${codename}-backports"
apt-get install -y --no-install-recommends -t "${codename}-backports" "${backports[@]}"

missing=()
for package in "${stable[@]}" "${backports[@]}"; do
	if ! dpkg-query -W -f='${Status}' "$package" 2>/dev/null | grep -q 'install ok installed'; then
		missing+=("$package")
	fi
done
if ((${#missing[@]})); then
	echo "[nexus] ERROR: not installed: ${missing[*]}" >&2
	exit 1
fi
echo "[nexus] All ${#stable[@]} + ${#backports[@]} packages are installed"
