# Shared shell functions for the wrfgate scripts. Sourced, never run.
WRF_ROOT=${WRF_ROOT:-/projects/academic/negarkhodoe/wrf}
WG_HOME=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
export WRF_ROOT PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH=$WG_HOME/lib${PYTHONPATH:+:$PYTHONPATH}
export WRFGATE_RELEASE=$(cat "$WG_HOME/VERSION" 2>/dev/null || echo dev)
WG_MODULES=${WG_MODULES:-"gcc/11.2.0 openmpi/4.1.1 wps/4.6.0-dmpar"}
WG_PARTITION=${WG_PARTITION:-general-compute}
WG_QOS=${WG_QOS:-general-compute}

wg_modules() { module purge >/dev/null 2>&1; module load $WG_MODULES >/dev/null 2>&1 || { echo "error: could not load $WG_MODULES" >&2; return 1; }; }
wg_die() { echo "error: $*" >&2; exit 1; }
wg_log() { python3 -m wrfgate.ledger log "$@" >/dev/null 2>&1 || echo "warning: could not write the ledger" >&2; }
wg_start() { WG_CMD="$(basename "$0") $*"; WG_T0=$(date +%s); wg_person >/dev/null 2>&1; wg_log phase=start cmd="$WG_CMD" cwd="$PWD" person="${WG_NAME:-unregistered}"; trap 'wg_log phase=end cmd="$WG_CMD" exit=$? secs=$(( $(date +%s) - WG_T0 ))' EXIT; }
wg_record() { local f=$WRF_ROOT/fires/$1/fire.yaml; [[ -f $f ]] || wg_die "no fire record $f (create it with wrf-new-fire)"; echo "$f"; }
wg_rec() { grep -E "^$2:" "$WRF_ROOT/fires/$1/fire.yaml" | head -1 | sed 's/^[^:]*: *//'; }
wg_version_dir() { # FIRE [VERSION] -> absolute input version folder
  local v=${2:-current} d=$WRF_ROOT/fires/$1/inputs
  [[ -e $d/$v ]] || wg_die "no input version '$v' for $1 (see wrf-status $1)"
  readlink -f "$d/$v"; }
wg_gate_status() { python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['status'])" "$1" 2>/dev/null || echo NONE; }
wg_wrf_run_tables() { [[ -n ${WG_WRF_RUN:-} ]] && { echo "$WG_WRF_RUN"; return; }; local r; r=$(find "${EBROOTWRF:-/nonexistent}" -maxdepth 4 -name RRTMG_LW_DATA -print -quit 2>/dev/null); [[ -n $r ]] && dirname "$r"; }
wg_exe() { local p; p=$(command -v "$1") || p=$(find "${EBROOTWRF:-/nonexistent}" -maxdepth 4 -name "$1" -type f -print -quit 2>/dev/null); [[ -n $p ]] && echo "$p" || { echo "error: $1 not found; load the WRF module or set PATH" >&2; echo "$1"; }; }
# People: $WRF_ROOT/people/<user>/profile.conf holds NAME=, EMAIL=, MAIL_TYPE= (written by wrf-me).
wg_profile() { echo "$WRF_ROOT/people/$USER/profile.conf"; }
wg_person() { # load the profile into WG_NAME, WG_EMAIL, WG_MAIL_TYPE; read, never sourced
  local f; f=$(wg_profile); WG_NAME=""; WG_EMAIL=""; WG_MAIL_TYPE="END,FAIL"
  [[ -f $f ]] || return 1
  WG_NAME=$(grep -m1 '^NAME=' "$f" | cut -d= -f2-); WG_EMAIL=$(grep -m1 '^EMAIL=' "$f" | cut -d= -f2-)
  local m; m=$(grep -m1 '^MAIL_TYPE=' "$f" | cut -d= -f2-); [[ -n $m ]] && WG_MAIL_TYPE=$m
  [[ -n $WG_NAME && -n $WG_EMAIL ]]; }
wg_need_person() { wg_person || wg_die "no profile for $USER. Run once: wrf-me --name 'Your Name' --email you@buffalo.edu"; }
wg_by() { echo "$WG_NAME <$WG_EMAIL> ($USER)"; }
wg_mail_lines() { [[ $WG_MAIL_TYPE == NONE ]] && return; echo "#SBATCH --mail-user=$WG_EMAIL"; echo "#SBATCH --mail-type=$WG_MAIL_TYPE"; }
wg_stamp() { date +%Y%m%d_%H%M%S; }
wg_hash() { sha256sum "$@" | sha256sum | cut -c1-8; }
