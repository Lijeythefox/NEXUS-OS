#!/bin/bash
set -euo pipefail

RELEASE="$1"
LINUXFAMILY="$2"
BOARD="$3"
BUILD_DESKTOP="$4"
ARCH="$5"

OVERLAY=/tmp/overlay
STAGING="$OVERLAY/.nexus-build"
NEXUS_HOSTNAME=nexus

log() {
	echo "[nexus] $*"
}

copy_overlay() {
	log "Copying overlay into the image"
	tar -C "$OVERLAY" \
		--exclude=./.nexus-build \
		--exclude=.keep \
		--owner=0 --group=0 \
		-cf - . |
		tar -C / -xf - \
			--no-same-owner \
			--no-overwrite-dir \
			--keep-directory-symlink

	if [[ -d "$OVERLAY/usr/local/bin" ]]; then
		find "$OVERLAY/usr/local/bin" -type f ! -name .keep -printf '%P\n' |
			while read -r tool; do
				chmod 0755 "/usr/local/bin/$tool"
			done
	fi
}

install_packages() {
	local list="$STAGING/packages.txt"
	local -a packages=()

	if [[ -f "$list" ]]; then
		mapfile -t packages < <(sed -e 's/\r$//' -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' "$list" | grep -v -e '^$' -e '^#' || true)
	fi

	if ((${#packages[@]} == 0)); then
		log "packages.txt is empty, nothing extra to install"
		return
	fi

	log "Installing ${#packages[@]} packages from packages.txt"
	apt-get update
	DEBIAN_FRONTEND=noninteractive apt-get install -y "${packages[@]}"

	if ! mountpoint -q /var/cache/apt; then
		apt-get clean
	fi
}

set_hostname() {
	log "Setting hostname to $NEXUS_HOSTNAME"
	echo "$NEXUS_HOSTNAME" >/etc/hostname
	if grep -q '^127\.0\.1\.1' /etc/hosts; then
		sed -i "s/^127\.0\.1\.1.*/127.0.1.1\t$NEXUS_HOSTNAME/" /etc/hosts
	else
		printf '127.0.1.1\t%s\n' "$NEXUS_HOSTNAME" >>/etc/hosts
	fi
}

write_version() {
	local version="unknown"
	if [[ -f "$STAGING/version" ]]; then
		version="$(tr -d '\r\n' <"$STAGING/version")"
	fi
	log "NEXUS OS version $version"
	mkdir -p /etc/nexus
	cat >/etc/nexus/version <<EOF
NEXUS_VERSION=$version
NEXUS_BOARD=$BOARD
NEXUS_KERNEL_FAMILY=$LINUXFAMILY
NEXUS_DEBIAN=$RELEASE
NEXUS_ARCH=$ARCH
NEXUS_DESKTOP=$BUILD_DESKTOP
EOF
}

main() {
	log "Customising image for $BOARD ($RELEASE, $ARCH, desktop=$BUILD_DESKTOP)"
	copy_overlay
	install_packages
	set_hostname
	write_version
	log "Done"
}

main
