#!/bin/bash
# Install this copy of wrfgate as a read-only release and point 'current' at it.
#   bash install.sh [VERSION]      VERSION defaults to YYYY.MM.DD-<git hash or time>
# Never overwrites a release; old releases stay, so running jobs keep the code they started with.
set -eu
WRF_ROOT=${WRF_ROOT:-/projects/academic/negarkhodoe/wrf}
SRC=$(cd "$(dirname "$(readlink -f "$0")")" && pwd)
H=$(git -C "$SRC" rev-parse --short HEAD 2>/dev/null || date +%H%M%S)
VER=${1:-$(date +%Y.%m.%d)-$H}
P=$WRF_ROOT/pipeline; R=$P/releases/$VER
[[ -e $R ]] && { echo "release $VER already exists at $R; pass another version name" >&2; exit 1; }
mkdir -p "$P/releases" "$WRF_ROOT"/{fires,ledger/shell,people,setaside}
mkdir "$R"
cp -r "$SRC"/bin "$SRC"/lib "$SRC"/setup.sh "$SRC"/install.sh "$SRC"/arrange_ccr.sbatch "$R"/
find "$R" -name __pycache__ -prune -exec rm -rf {} +
echo "$VER" > "$R/VERSION"
{ echo "release: $VER"; echo "installed: $(date -Is) by $USER on $(hostname)"; echo "from: $SRC"; echo "files:"; (cd "$R" && find . -type f ! -name MANIFEST.txt -print0 | sort -z | xargs -0 sha256sum | sed 's/^/  /'); } > "$R/MANIFEST.txt"
chmod -R a-w,a+rX "$R"; chmod a+x "$R"/bin/*
ln -sfn "releases/$VER" "$P/current"
chgrp -R "$(stat -c %G "$WRF_ROOT")" "$WRF_ROOT/fires" "$WRF_ROOT/ledger" "$WRF_ROOT/people" "$WRF_ROOT/setaside" 2>/dev/null || true
chmod g+rwxs "$WRF_ROOT/fires" "$WRF_ROOT/ledger" "$WRF_ROOT/ledger/shell" "$WRF_ROOT/people" "$WRF_ROOT/setaside"
touch "$WRF_ROOT/ledger/commands.jsonl"; chmod g+rw "$WRF_ROOT/ledger/commands.jsonl"
source "$R/lib/wrfgate.sh"; python3 -m wrfgate.ledger log event=release_installed release="$VER" by="$USER" >/dev/null
echo "installed $R"
echo "current -> releases/$VER"
echo "add to ~/.bashrc:  source $P/current/setup.sh"
echo "then, once per person:  wrf-me --name 'Your Name' --email you@buffalo.edu"
