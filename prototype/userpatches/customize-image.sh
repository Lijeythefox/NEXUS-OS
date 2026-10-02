#!/bin/bash
set -euo pipefail

RELEASE="$1"
LINUXFAMILY="$2"
BOARD="$3"
BUILD_DESKTOP="$4"
ARCH="$5"

OVERLAY=/tmp/overlay
STAGING="$OVERLAY/.nexus-build"
DOWNLOADS="$STAGING/downloads"
NEXUS_HOSTNAME=nexus
DEFAULT_PRESET=amber
LIBRETRO_DIR="/usr/lib/aarch64-linux-gnu/libretro"
export DEBIAN_FRONTEND=noninteractive

log() {
	echo "[nexus] $*"
}

prepare_apt() {
	log "Telling apt to keep existing config files instead of asking"
	cat >/etc/apt/apt.conf.d/90nexus-noninteractive <<'EOF'
Dpkg::Options {
   "--force-confdef";
   "--force-confold";
};
EOF
}

repair_dpkg() {
	dpkg --configure -a || true
	apt-get install -y -f || true
}

add_repositories() {
	install -d /usr/share/keyrings /etc/apt/sources.list.d
	if [[ -f "$DOWNLOADS/keys/microsoft.gpg" ]]; then
		log "Adding the Visual Studio Code repository"
		install -m 0644 "$DOWNLOADS/keys/microsoft.gpg" /usr/share/keyrings/microsoft.gpg
		cat >/etc/apt/sources.list.d/vscode.sources <<EOF
Types: deb
URIs: https://packages.microsoft.com/repos/code
Suites: stable
Components: main
Architectures: $ARCH
Signed-By: /usr/share/keyrings/microsoft.gpg
EOF
		echo "code code/add-microsoft-repo boolean false" | debconf-set-selections
	fi
	if [[ -f "$DOWNLOADS/keys/tailscale-archive-keyring.gpg" ]]; then
		log "Adding the Tailscale repository"
		install -m 0644 "$DOWNLOADS/keys/tailscale-archive-keyring.gpg" /usr/share/keyrings/tailscale-archive-keyring.gpg
		echo "deb [signed-by=/usr/share/keyrings/tailscale-archive-keyring.gpg] https://pkgs.tailscale.com/stable/debian $RELEASE main" \
			>/etc/apt/sources.list.d/tailscale.list
	fi
}

install_packages() {
	local list="$STAGING/packages.txt"
	local -a packages=()
	local missing=()
	mapfile -t packages < <(sed -e 's/\r$//' -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' "$list" | grep -v -e '^$' -e '^#' || true)
	((${#packages[@]})) || return 0
	log "Installing ${#packages[@]} packages"
	apt-get update
	if ! apt-get install -y "${packages[@]}"; then
		log "Bulk install failed, repairing and trying again"
		repair_dpkg
		if ! apt-get install -y "${packages[@]}"; then
			log "Still failing, installing one at a time"
			for package in "${packages[@]}"; do
				apt-get install -y "$package" || {
					missing+=("$package")
					repair_dpkg
				}
			done
		fi
	fi
	mkdir -p /var/lib/nexus
	printf '%s\n' "${missing[@]:-}" >/var/lib/nexus/missing-packages.txt
	if ((${#missing[@]})); then
		log "Packages that could not be installed: ${missing[*]}"
	fi
}

install_downloads() {
	if compgen -G "$DOWNLOADS/debs/*.deb" >/dev/null; then
		log "Installing downloaded apps"
		for deb in "$DOWNLOADS"/debs/*.deb; do
			apt-get install -y "$deb" || {
				log "Could not install $(basename "$deb")"
				repair_dpkg
			}
		done
	fi
	if [[ -d "$DOWNLOADS/apps" ]]; then
		install -d /opt/nexus/apps
		cp -a "$DOWNLOADS/apps/." /opt/nexus/apps/
		chown -R root:root /opt/nexus/apps
	fi
	if compgen -G "$DOWNLOADS/cores/*.so" >/dev/null; then
		log "Installing emulator cores"
		install -d "$LIBRETRO_DIR"
		install -m 0644 "$DOWNLOADS"/cores/*.so "$LIBRETRO_DIR/"
	fi
	if compgen -G "$DOWNLOADS/fonts/*" >/dev/null; then
		install -d /usr/share/fonts/truetype/nexus
		install -m 0644 "$DOWNLOADS"/fonts/* /usr/share/fonts/truetype/nexus/
		fc-cache -f >/dev/null 2>&1 || true
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
	chmod 0644 /etc/systemd/system/nexus-firstboot.service
}

hide_autostart() {
	local file="/etc/xdg/autostart/$1"
	[[ -f "$file" ]] || return 0
	sed -i '/^Hidden=/d' "$file"
	echo "Hidden=true" >>"$file"
}

configure_desktop() {
	log "Configuring the desktop"
	hide_autostart xfce4-screensaver.desktop
	hide_autostart onboard-autostart.desktop
	hide_autostart nm-applet.desktop
	install -d /etc/xdg/xfce4/panel
	cp /etc/skel/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-panel.xml /etc/xdg/xfce4/panel/default.xml
	glib-compile-schemas /usr/share/glib-2.0/schemas || log "glib-compile-schemas reported a problem"
	for theme in /usr/share/icons/NEXUS-*; do
		[[ -d "$theme" ]] && gtk-update-icon-cache -f -q "$theme" || true
	done
	PYTHONPATH=/opt/nexus/lib /usr/local/sbin/nexus-root-quick preset "$DEFAULT_PRESET" || log "Preset setup reported a problem"
	if [[ -f /boot/armbianEnv.txt ]]; then
		if grep -q '^bootlogo=' /boot/armbianEnv.txt; then
			sed -i 's/^bootlogo=.*/bootlogo=true/' /boot/armbianEnv.txt
		else
			echo 'bootlogo=true' >>/boot/armbianEnv.txt
		fi
	fi
}

configure_system() {
	log "Configuring system services"
	install -d /mnt/sdcard /var/lib/nexus
	if ! grep -q 'LABEL=NEXUS-SD' /etc/fstab; then
		echo 'LABEL=NEXUS-SD /mnt/sdcard ext4 defaults,noatime,nofail,x-systemd.device-timeout=5s 0 2' >>/etc/fstab
	fi
	systemctl enable nexus-firstboot.service
	systemctl disable nmbd.service 2>/dev/null || true
	systemctl enable smbd.service 2>/dev/null || true
	systemctl enable ssh.service 2>/dev/null || true
	systemctl enable tailscaled.service 2>/dev/null || true
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
	log "NEXUS OS prototype version $version"
	mkdir -p /etc/nexus
	cat >/etc/nexus/version <<EOF
NEXUS_VERSION=$version
NEXUS_BUILD=prototype
NEXUS_BOARD=$BOARD
NEXUS_KERNEL_FAMILY=$LINUXFAMILY
NEXUS_DEBIAN=$RELEASE
NEXUS_ARCH=$ARCH
NEXUS_DESKTOP=$BUILD_DESKTOP
EOF
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
	log "Customising prototype image for $BOARD ($RELEASE, $ARCH, desktop=$BUILD_DESKTOP)"
	prepare_apt
	add_repositories
	install_packages
	install_downloads
	copy_overlay
	configure_desktop
	configure_system
	set_hostname
	write_version
	clean_up
	log "Done"
}

main
