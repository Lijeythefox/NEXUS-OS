#!/bin/bash
set -uo pipefail

list="$1"
out="$2"
work="$(mktemp -d)"
failed=0
mkdir -p "$out"/{debs,apps,cores,fonts,keys}

appimage_offset() {
	python3 - "$1" <<'PY'
import struct
import sys

with open(sys.argv[1], "rb") as handle:
    header = handle.read(64)
section_offset = struct.unpack_from("<Q", header, 0x28)[0]
entry_size = struct.unpack_from("<H", header, 0x3A)[0]
entry_count = struct.unpack_from("<H", header, 0x3C)[0]
print(section_offset + entry_size * entry_count)
PY
}

fetch() {
	curl -fsSL --retry 4 --retry-delay 5 -o "$2" "$1"
}

while read -r kind name url; do
	[[ -z "${kind:-}" || "$kind" == \#* ]] && continue
	echo "[fetch] $kind $name"
	case "$kind" in
	deb)
		fetch "$url" "$out/debs/$name.deb" || { echo "::warning::Could not download $name"; failed=1; }
		;;
	appimage)
		if fetch "$url" "$work/$name.AppImage"; then
			offset="$(appimage_offset "$work/$name.AppImage")"
			unsquashfs -q -f -o "$offset" -d "$out/apps/$name" "$work/$name.AppImage" >/dev/null ||
				{ echo "::warning::Could not unpack $name"; failed=1; }
			chmod 0755 "$out/apps/$name" 2>/dev/null
		else
			echo "::warning::Could not download $name"
			failed=1
		fi
		;;
	core)
		if fetch "$url" "$work/$name.zip"; then
			unzip -qo "$work/$name.zip" -d "$out/cores" || { echo "::warning::Could not unzip $name"; failed=1; }
		else
			echo "::warning::Could not download core $name"
			failed=1
		fi
		;;
	font)
		fetch "$url" "$out/fonts/$name" || { echo "::error::Could not download font $name"; exit 1; }
		;;
	key)
		if [[ "$name" == *.asc ]]; then
			fetch "$url" "$work/$name" && gpg --dearmor <"$work/$name" >"$out/keys/${name%.asc}.gpg" ||
				{ echo "::error::Could not get key $name"; exit 1; }
		else
			fetch "$url" "$out/keys/$name" || { echo "::error::Could not get key $name"; exit 1; }
		fi
		;;
	*)
		echo "::warning::Unknown download type $kind"
		;;
	esac
done < <(sed 's/\r$//' "$list")

rm -rf "$work"
du -sh "$out"/* || true
if ((failed)); then
	echo "::warning::Some optional downloads failed. The image still builds without them."
fi
exit 0
