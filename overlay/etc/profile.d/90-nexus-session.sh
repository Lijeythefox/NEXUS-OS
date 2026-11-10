# NEXUS OS: start the desktop when the desktop user logs in on the first screen.
# It does nothing for root, over SSH, on other screens, or inside the desktop.
if [ -z "${NEXUS_NO_DESKTOP:-}" ] && [ -z "${WAYLAND_DISPLAY:-}" ] && [ -z "${DISPLAY:-}" ] \
	&& [ "$(id -u)" -ge 1000 ] && [ "$(tty 2>/dev/null)" = "/dev/tty1" ] \
	&& [ ! -e "$HOME/.config/nexus/no-desktop" ] && [ -x /usr/local/bin/nexus-session ]; then
	/usr/local/bin/nexus-session
	nexus_rc=$?
	if [ "$nexus_rc" -ne 3 ]; then
		# Desktop closed (or failed fewer than 3 times): log out, which starts it again.
		exit
	fi
	# Exit code 3: the desktop failed 3 times in a row. Stay in this shell so it can be fixed.
	export NEXUS_NO_DESKTOP=1
	unset nexus_rc
fi
