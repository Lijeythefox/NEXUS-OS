#!/bin/bash
# Fast checks that need no packages from the image: syntax of every script and
# config, then the unit tests. Run from the repo root: bash ci/check-static.sh
set -euo pipefail
cd "$(dirname "$0")/.."

fail=0
note() { echo "[check] $*"; }

mapfile -t bash_files < <(grep -rlI --exclude-dir=.git --exclude-dir=.superpowers -e '^#!/bin/bash' -e '^#!/usr/bin/env bash' . | sort)
for f in "${bash_files[@]}"; do
	bash -n "$f" || fail=1
done
if command -v shellcheck >/dev/null; then
	shellcheck -S error "${bash_files[@]}" || fail=1
fi
note "${#bash_files[@]} bash scripts"

mapfile -t py_files < <({ grep -rlI --exclude-dir=.git --exclude-dir=.superpowers '^#!/usr/bin/python3' . || true; find . -name '*.py' -not -path './.git/*'; } | sort -u)
for f in "${py_files[@]}"; do
	python3 -c "import ast,sys; ast.parse(open(sys.argv[1], encoding='utf-8').read(), sys.argv[1])" "$f" || fail=1
done
note "${#py_files[@]} python files"

mapfile -t lua_files < <(find overlay -name '*.lua' | sort)
luac_bin="$(command -v luac5.4 || command -v luac || true)"
for f in "${lua_files[@]}"; do
	if [[ -n "$luac_bin" ]]; then
		"$luac_bin" -p "$f" || fail=1
	fi
done
note "${#lua_files[@]} lua files (checked with ${luac_bin:-nothing, luac missing})"

mapfile -t json_files < <(find overlay config -name '*.json' | sort)
for f in "${json_files[@]}"; do
	jq empty "$f" || { echo "bad JSON: $f"; fail=1; }
done
note "${#json_files[@]} json files"

if grep -rIl $'\r' --exclude-dir=.git --exclude-dir=.superpowers overlay ci config userpatches tools 2>/dev/null | grep -q .; then
	echo "Windows line endings found in:"; grep -rIl $'\r' overlay ci config userpatches tools; fail=1
fi

bash ci/tests.sh || fail=1

if ((fail)); then
	echo "[check] FAILED"; exit 1
fi
echo "[check] all static checks passed"
