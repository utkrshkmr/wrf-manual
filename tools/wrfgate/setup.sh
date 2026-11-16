# Source this from ~/.bashrc:  source /projects/academic/negarkhodoe/wrf/pipeline/current/setup.sh
# Puts the wrf-* scripts on PATH and logs your shell commands that touch the shared folder.
export WRF_ROOT=${WRF_ROOT:-/projects/academic/negarkhodoe/wrf}
_wg_home=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
case ":$PATH:" in *":$_wg_home/bin:"*) ;; *) export PATH=$_wg_home/bin:$PATH ;; esac
if [[ $- == *i* && -d $WRF_ROOT/ledger/shell && -w $WRF_ROOT/ledger/shell ]]; then
  _wg_shlog() {
    local c; c=$(HISTTIMEFORMAT= history 1 | sed 's/^ *[0-9]* *//')
    [[ -z $c || $c == "$_wg_last" ]] && return; _wg_last=$c
    if [[ $PWD == "$WRF_ROOT"* || $c == *wrf* || $c == sbatch* || $c == scancel* || $c == *negarkhodoe* ]]; then
      printf '%s\t%s\t%s\t%s\n' "$(date -Is)" "$(hostname -s)" "$PWD" "$c" >> "$WRF_ROOT/ledger/shell/$USER.log" 2>/dev/null
    fi; }
  case "$PROMPT_COMMAND" in *_wg_shlog*) ;; *) PROMPT_COMMAND="_wg_shlog${PROMPT_COMMAND:+; $PROMPT_COMMAND}" ;; esac
fi
unset _wg_home
