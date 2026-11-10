#!/bin/bash
# Runs inside the image while GitHub builds it. Installs the NEXUS packages,
# copies overlay/ into place and switches off services the desktop does not need.
set -euo pipefail

RELEASE="$1"
LINUXFAMILY="$2"
BOARD="$3"
BUILD_DESKTOP="$4"
ARCH="$5"

OVERLAY=/tmp/overlay
STAGING="$OVERLAY/.nexus-build"
NEXUS_HOSTNAME=nexus
export DEBIAN_FRONTEND=noninteractive

log() {
	echo "[nexus] $*"
}

prepare_apt() {
	log "Telling apt to keep existing config files instead of asking"
	cat >/etc/apt/apt.conf.d/90nexus-noninteractive <<'CONF'
Dpkg::Options {
   "--force-confdef";
   "--force-confold";
};
CONF
}

repair_dpkg() {
	dpkg --configure -a || true
	apt-get install -y -f || true
}

install_packages() {
	log "Installing the NEXUS package lists"
	if ! bash "$STAGING/install-packages.sh" "$STAGING/packages.txt" "$STAGING/packages-backports.txt"; then
		log "Package install failed, repairing and trying once more"
		repair_dpkg
		bash "$STAGING/install-packages.sh" "$STAGING/packages.txt" "$STAGING/packages-backports.txt"
	fi
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
	chmod 0755 /usr/local/bin/nexus-* /usr/local/sbin/nexus-*
	chmod 0644 /etc/profile.d/zz-nexus-session.sh "/etc/systemd/system/getty@tty1.service.d/zz-nexus.conf"
}

trim_services() {
	log "Switching off services the desktop does not need"
	local unit
	for unit in cups.service cups.socket cups-browsed.service avahi-daemon.service avahi-daemon.socket \
		ModemManager.service ssh.service ssh.socket; do
		systemctl disable "$unit" 2>/dev/null || true
	done
	# Keep automatic updates from slowing down the first 10 minutes after boot.
	for unit in apt-daily.timer apt-daily-upgrade.timer; do
		install -d "/etc/systemd/system/$unit.d"
		cat >"/etc/systemd/system/$unit.d/nexus.conf" <<'CONF'
[Timer]
Persistent=false
OnBootSec=10min
CONF
	done
	systemctl enable NetworkManager.service 2>/dev/null || true
	systemctl enable swayosd-libinput-backend.service 2>/dev/null || true
}

freeze_kernel() {
	mapfile -t frozen < <(dpkg-query -W -f='${Package}\n' | grep -E '^(linux-(image|dtb|u-boot)-|armbian-firmware)' || true)
	if ((${#frozen[@]})); then
		log "Freezing kernel and firmware: ${frozen[*]}"
		apt-mark hold "${frozen[@]}"
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
	mkdir -p /etc/nexus /var/lib/nexus
	cat >/etc/nexus/version <<VERSION
NEXUS_VERSION=$version
NEXUS_BOARD=$BOARD
NEXUS_KERNEL_FAMILY=$LINUXFAMILY
NEXUS_DEBIAN=$RELEASE
NEXUS_ARCH=$ARCH
VERSION
}

clean_up() {
	repair_dpkg
	if dpkg --audit | grep -q .; then
		log "Some packages are still not fully set up:"
		dpkg --audit
		exit 1
	fi
	if ! mountpoint -q /var/cache/apt; then
		apt-get clean
	fi
}

main() {
	log "Customising image for $BOARD ($RELEASE, $ARCH, armbian desktop=$BUILD_DESKTOP)"
	prepare_apt
	install_packages
	copy_overlay
	trim_services
	freeze_kernel
	set_hostname
	write_version
	clean_up
	log "Done"
}

main
