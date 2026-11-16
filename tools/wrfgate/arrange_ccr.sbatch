#!/bin/bash
#SBATCH -J wg_arrange
#SBATCH -p general-compute
#SBATCH --qos=general-compute
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --mem=64G
#SBATCH -t 24:00:00
#SBATCH -o /projects/academic/negarkhodoe/wrf/ledger/arrange_%j.out
# Copies every fire we have run, or have inputs for, into the gated layout:
#   fires/<FIRE>/fire.yaml, inputs/<version>/ (+ gate A and B results), specs/campaign/
# Copies only. Nothing is moved, edited or deleted, and nothing is submitted. Safe next to running jobs.
# Override any source with environment variables when submitting, e.g.
#   sbatch --export=ALL,MET_LONG_2024=/path/to/met_em_folder,NL_LONG_2024=/path/to/namelist.input arrange_ccr.sbatch
P=${ARRANGE_P:-/projects/academic/negarkhodoe}
W=${WRF_ROOT:-$P/wrf}
source $W/pipeline/current/setup.sh
source $W/pipeline/current/lib/wrfgate.sh
wg_person || { echo "no profile for $USER: run wrf-me --name ... --email ... first"; exit 1; }
wg_log event=arrange_start job=$SLURM_JOB_ID
FIRES="EATON_2025 CANYON_2025 CRANSTON_2018 LONG_2024 AIRPORT BRADFORD_BRANCH CARMEL"
declare -A SHORT=([EATON_2025]=EATON [CANYON_2025]=CANYON [CRANSTON_2018]=CRANSTON [LONG_2024]=LONG [AIRPORT]=AIRPORT [BRADFORD_BRANCH]=BRADFORD_BRANCH [CARMEL]=CARMEL)
declare -A METROOTS=(
  [EATON_2025]="$P/utkarshk/fires/EATON"
  [CANYON_2025]="$P/Thursday_deadline_fires/CANYON $P/utkarshk/fires/CANYON $P/WRF_NCAR_Fires/CANYON"
  [CRANSTON_2018]="$P/Thursday_deadline_fires/CRANSTON $P/utkarshk/fires/CRANSTON"
  [LONG_2024]="$P/Thursday_deadline_fires/LONG $P/utkarshk/fires/LONG"
  [AIRPORT]="$P/WRF_NCAR_Fires/AIRPORT"
  [BRADFORD_BRANCH]="$P/WRF_NCAR_Fires/BRADFORD_BRANCH"
  [CARMEL]="$P/WRF_NCAR_Fires/CARMEL")
# Release each fire's met_em matches best (anchor study, Nov 16): Canyon LF2024, Cranston LF2016, Long LF2023.
declare -A FUELREL=([CANYON_2025]=LF2024 [CRANSTON_2018]=LF2016 [LONG_2024]=LF2023)
fuel_for_year() { case $1 in 201[0-9]|2020|2021) echo LF2016;; 2022) echo LF2022;; 2023) echo LF2023;; *) echo LF2024;; esac; }
best_met() { # the folder under the given roots with the most met_em.d01 files
  for r in "$@"; do [[ -d $r ]] && find -L "$r" -maxdepth 4 -name 'met_em.d01.*' -printf '%h\n' 2>/dev/null; done | sort | uniq -c | sort -k1,1nr | head -1 | awk '{print $2}'; }
best_nl() { # newest namelist.input with an ignition, under the roots and the campaign folders
  for r in "$@"; do [[ -d $r ]] && find -L "$r" -maxdepth 6 -name namelist.input -printf '%T@ %p\n' 2>/dev/null; done | sort -k1,1nr | awk '{print $2}' |
    while read -r f; do grep -qi 'fire_ignition_start_lat1' "$f" && grep -qi 'start_year' "$f" && { echo "$f"; break; }; done; }
SUMMARY=$W/ledger/arrange_${SLURM_JOB_ID:-manual}.summary
: > "$SUMMARY"
for F in $FIRES; do
  S=${SHORT[$F]}
  echo; echo "########## $F  $(date '+%F %T')"
  mv_=MET_$F; nl_=NL_$F
  MET=${!mv_:-$(best_met ${METROOTS[$F]})}
  NL=${!nl_:-$(best_nl $P/utkarshk/fires/$S $P/utkarshk/campaign $P/utkarshk/runs ${METROOTS[$F]})}
  echo "met_em folder: ${MET:-NOT FOUND}  ($( [[ -n $MET ]] && ls "$MET"/met_em.d0* | wc -l) files, $( [[ -n $MET ]] && du -shL "$MET" 2>/dev/null | cut -f1))"
  echo "namelist.input: ${NL:-NOT FOUND}"
  echo "other namelist.input candidates (newest first; override with NL_$F=...):"
  for r in $P/utkarshk/fires/$S $P/utkarshk/campaign $P/utkarshk/runs ${METROOTS[$F]}; do [[ -d $r ]] && find -L "$r" -maxdepth 6 -name namelist.input -printf '%TY-%Tm-%Td %TH:%TM  %p\n' 2>/dev/null; done | sort -r | head -8 | sed 's/^/    /'
  if [[ -z $MET ]]; then echo "$F  SKIPPED: no met_em folder found (set MET_$F)" >> "$SUMMARY"; continue; fi
  if [[ ! -f $W/fires/$F/fire.yaml ]]; then
    if [[ -n $NL ]]; then
      Y=$(python3 -c "import sys;from wrfgate.common import get_namelist;print(get_namelist(open(sys.argv[1]).read(),'start_year')[0])" "$NL")
      REL=${FUELREL[$F]:-$(fuel_for_year "$Y")}
      wrf-new-fire "$F" --from-namelist "$NL" --fuel-layer "$W/static/landfire/$REL/FBFM40" --source "campaign namelist $NL" ||
        { echo "$F  SKIPPED: record could not be made from $NL" >> "$SUMMARY"; continue; }
    else
      echo "$F  SKIPPED: no namelist.input with an ignition found (set NL_$F, or run wrf-new-fire by hand)" >> "$SUMMARY"; continue
    fi
  else echo "record exists, kept: $W/fires/$F/fire.yaml"; fi
  if [[ -n $NL && ! -d $W/fires/$F/specs/campaign ]]; then
    D=$W/fires/$F/specs/campaign; mkdir -p "$D"; N=$(dirname "$NL")
    cp "$NL" "$D"/; for f in namelist.fire iofields*.txt namelist.wps; do ls "$N"/$f >/dev/null 2>&1 && cp "$N"/$f "$D"/; done
    { echo "spec: campaign"; echo "copied_from: $N"; echo "copied: $(date -Is) by $USER"; } > "$D/SOURCE.txt"
    chmod -R a-w "$D"
  fi
  wrf-add-inputs "$F" "$MET" --note "arranged from $MET"
  wrf-card "$F" > "$W/fires/$F/CARD.txt" 2>/dev/null && echo "card: $W/fires/$F/CARD.txt"
  V=$(readlink "$W/fires/$F/inputs/current" 2>/dev/null)
  last=$(ls -d "$W"/fires/$F/inputs/*/ 2>/dev/null | grep -v -e '\.gates/$' -e '/current/$' | tail -1); last=$(basename "${last:-none}")
  printf "%-16s inputs %-20s gate A %-5s gate B %-5s current %s\n" "$F" "$last" \
    "$(wg_gate_status "$W/fires/$F/inputs/$last.gates/gate_A.json")" "$(wg_gate_status "$W/fires/$F/inputs/$last.gates/gate_B.json")" "${V:-none}" >> "$SUMMARY"
done
echo; echo "########## summary"; cat "$SUMMARY"
echo; wrf-status
wg_log event=arrange_end job=$SLURM_JOB_ID
