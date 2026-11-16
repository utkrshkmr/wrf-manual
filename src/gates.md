---
title: The gating system
kicker: Running it safely
lead: Eight small commands carry a fire from its record to a checked run. Each one does one step, runs the checks for it, and writes what it did to a shared ledger. Nothing reaches the queue until the cheap checks have passed, and nothing is ever deleted.
---

## Why gates

A WRF-Fire run can wait a day in the queue and then fail in its first minute: a namelist typo, a fuel map from the wrong place, an ignition outside the fire domain. Each of those can be caught in seconds or minutes, before the expensive job is submitted. The gating system puts a check after every step of the [chain](index.html), and makes each command refuse to start until the check before it has passed.

{{fig:gateflow|**The six steps of one run.** The record and the input version are made once per fire; gates C and D are run once per set of namelists; `wrf-submit` refuses unless gate D passed for exactly those namelists on exactly that input version.}}

It also answers, for every file in the shared folder, who made it, when, from what, and whether it was checked. That is what the manifests and the ledger are for.

## Setting it up

Once, by whoever installs a release (from a clone of this site's repository):

```bash
git clone https://github.com/utkrshkmr/wrf-manual.git /projects/academic/negarkhodoe/utkarshk/wrf-manual
bash /projects/academic/negarkhodoe/utkarshk/wrf-manual/tools/wrfgate/install.sh
```

`install.sh` copies the code to `wrf/pipeline/releases/<version>/`, makes it read-only, and points `wrf/pipeline/current` at it. A newer release is installed the same way; the old one stays, so jobs already in the queue keep the code they were submitted with.

Once per person:

```bash
echo 'source /projects/academic/negarkhodoe/wrf/pipeline/current/setup.sh' >> ~/.bashrc
source /projects/academic/negarkhodoe/wrf/pipeline/current/setup.sh
wrf-me --name "Utkarsh Kumar" --email ukumar@buffalo.edu --mail END,FAIL
```

`setup.sh` puts the commands on your `PATH` and adds a shell hook that logs your commands that touch the shared folder. `wrf-me` writes your profile.

## Your profile

Every runner has a folder `wrf/people/<username>/` with a `profile.conf` in it:

```text
# wrfgate profile for ukumar. Edit with wrf-me, not by hand.
NAME=Utkarsh Kumar
EMAIL=ukumar@buffalo.edu
MAIL_TYPE=END,FAIL
UPDATED=2026-11-16T10:02:11-05:00
```

- **Every record, input version and run is signed with it.** Manifests carry a `by:` line (`Utkarsh Kumar <ukumar@buffalo.edu> (ukumar)`), the ledger carries your name on every line, and `wrf-status` shows who started each run.
- **Slurm emails you.** Every job the commands submit gets `--mail-user` and `--mail-type` from your profile. `MAIL_TYPE` takes Slurm's own types joined by commas (`BEGIN`, `END`, `FAIL`, `TIME_LIMIT_80`, `ALL`), or `NONE` to switch emails off.
- **No profile, no work.** Every command that creates something refuses until you have run `wrf-me`. Reading (`wrf-status`, `wrf-me` with no options) works without one.
- **Changing it** is `wrf-me` again with the new values; the old file is kept beside it with a timestamp.
- **`people/<username>/work/`** is yours for drafts: namelists you are still editing, notes, test scripts. Nothing in the gating system reads it until you point a command at it.

## The folders

```text
/projects/academic/negarkhodoe/wrf/
  pipeline/
    current -> releases/2026.11.16-a1b2c3d     the code everyone runs
    releases/<version>/                        read-only: bin/, lib/, setup.sh, MANIFEST.txt
  people/<username>/                           profile.conf, work/
  static/                                      LANDFIRE, elevation, geography; read-only
  tables/                                      GEOGRID.TBL, METGRID.TBL, Vtables
  fires/<FIRE>/
    fire.yaml                                  the record; read-only
    inputs/<YYYYmmdd>_<hash8>/                 one locked folder per input upload
    inputs/<YYYYmmdd>_<hash8>.gates/           gate A and B results for it
    inputs/current -> <version>                the version runs use by default
    specs/<name>/                              namelist.input, namelist.fire
    runs/<stamp>_gateC_<spec>/                 real.exe and gate C
    runs/<stamp>_gateD_<spec>/                 the smoke run and gate D
    runs/<stamp>_<spec>/                       production runs and gate E
  setaside/<YYYY-MM>/                          anything moved out of the way, with a NOTE.txt
  ledger/
    commands.jsonl                             hash-chained command and event log
    shell/<username>.log                       shell history from setup.sh's hook
```

{{fig:gatelayout|**One fire's folder.** Input versions are locked and named by the hash of their files. Gate D and production runs link to the `wrfinput` and `wrfbdy` files gate C checked, so what runs is exactly what was checked.}}

Rules the commands keep:

- **Group-owned, group-writable folders** (set-group-ID on `fires/`, `people/`, `ledger/`, `setaside/`), so a second person can add a run to a fire the first one created.
- **Locked means locked.** Records, input versions, specs copied by the arrange job and releases are read-only. Changing one means making a new one: `wrf-new-fire --replace`, a new `wrf-add-inputs`, a new spec folder, a new release.
- **Nothing is deleted.** `wrf-setaside PATH "reason"` moves a run, an input version or a spec into `setaside/<month>/` with a `NOTE.txt` saying where it came from, who moved it, why, and the command that moves it back. It refuses anything still in use: the current input version, an input version a run used, a gate C folder that a later run links to, and runs whose job is still queued or running. The pipeline, the ledger and `setaside/` itself are never moved.

## The commands

| Command | What it does | Refuses when |
| --- | --- | --- |
| `wrf-me [--name --email --mail]` | Shows or writes your profile | the email is not an address |
| `wrf-new-fire FIRE --from-namelist NL` | Writes `fires/FIRE/fire.yaml` from a namelist that was used for the fire (or from `--start --end --ignition --lat --lon`) | a record exists (use `--replace`, which keeps the old one) |
| `wrf-add-inputs FIRE DIR [--note]` | Copies `met_em*` (and `namelist.wps`, `geo_em*`, logs) into a new version folder, writes `MANIFEST.txt` with a SHA-256 per file, runs gates A and B, locks it; moves `current` only if neither gate failed | no record; identical files already registered |
| `wrf-gate A\|B FIRE [VERSION]` | Reruns gate A or B on a version | — |
| `wrf-gate C FIRE SPEC_DIR [--inputs V]` | New run folder, links the inputs and WRF's tables, submits real.exe on one node, then gate C | gate A failed on that version |
| `wrf-gate D FIRE GATE_C_DIR [--minutes 2] [--ranks N]` | Two simulated minutes of wrf.exe on one node, no output, then gate D | gate C did not pass |
| `wrf-submit FIRE SPEC_DIR --nodes --ranks --time [--constraint] [--name]` | The production run: links gate C's files, submits wrf.exe, runs gate E when the job ends | no passed gate D for the same namelists and inputs; ranks over the cap; walltime over 72 h; the same namelists already queued |
| `wrf-gate E FIRE RUN_DIR` | Reruns gate E, for a run that was killed before its own gate E | — |
| `wrf-status [FIRE]` | All fires, or one fire's record, versions, gates and runs with who started them and the job state | — |
| `wrf-setaside PATH "reason"` | Moves something into `setaside/` instead of deleting it | it is in use (see above) |
| `wrf-ledger-verify` | Checks that no ledger line was edited or removed | — |

**Same namelists** means the same SHA-256 of `namelist.input` plus `namelist.fire` (`spec_hash` in each manifest). Edit one character and gates C and D have to be run again; that is the point.

## What each gate checks

Each check ends `PASS`, `WARN`, `FAIL` or `INFO`. A gate's result is its worst check. `FAIL` blocks the next command; `WARN` is printed, logged and lets you go on. Every gate writes `gate_X.json` (with the facts it measured) and appends to a readable `GATES.txt` beside it.

### Gate A: the inputs make sense on their own

| Check | Fails when |
| --- | --- |
| A01–A05 files, domains, times | missing domains, uneven intervals, domains with different times, or a window that does not cover the record's start to end |
| A06–A09 geometry | grid changes between files, required fields missing, any NaN or Inf, a nest that breaks the parent-ratio rule |
| A10 rank cap | (info) `⌊nx/10⌋ × ⌊ny/10⌋` on the tightest domain; later steps refuse more ranks |
| A11–A13 fire fields | no domain with a fire mesh, `NFUEL_CAT` not filled; `ZSF` not filled is a warning |
| A14–A16 fuel codes | any code that is not Anderson 1–13 or one of the 40 Scott & Burgan codes plus 91–99; under 5% burnable warns; code 204 warns (it needs `nfuelcats = 54`) |
| A17–A18 terrain | `ZSF` outside −100 to 4,500 m; averaged to the atmosphere grid, more than 50 m from `HGT_M` on average warns |
| A19–A21 ignition | ignition outside the fire domain, closer than `min_edge_km` (default 2 km) to its edge, or on an unburnable cell |

### Gate B: the inputs match the reference maps

Gate B finds the LANDFIRE pixel under every fire-mesh cell by exact NAD83 Albers geometry (no geogrid involved) and compares codes.

| Check | Result |
| --- | --- |
| B02 fuel agreement | `PASS` ≥ 98% of cells, `WARN` 90–98%, `FAIL` < 90% |
| B03–B04 | the commonest mismatches, and how many come in mirrored pairs (a→b and b→a): many mirrored pairs mean a small shift, few mean different data |
| B05–B06 | reference coverage, burnable share against the reference |
| B07 release scan | agreement with every release in `static/landfire/`: which LANDFIRE year the inputs were made from |
| B08 | reference fuel at the ignition point is burnable |
| B09 terrain | `ZSF` against the elevation layer; RMSE over 15 m warns |

The record's `fuel_layer` picks the reference (default `static/landfire/LF2024/FBFM40`). The thresholds are options (`--pass-pct`, `--fail-pct`) and every value goes into the JSON, so they can be tightened later without losing what was measured.

### Gate C: real.exe and the namelists

real.exe must print `SUCCESS`; `max_dom`, grid sizes, `dx`, the fire ratio and the vertical levels must match the inputs; the initial time must be the record's start and the boundaries must reach its end; the fire domain must have `ifire = 2`, `fire_fuel_read = -1` and a terrain source; the ignition time and place must be the record's; code 204 needs `nfuelcats ≥ 54`; `fire_fmc_read = 0` needs a non-zero `FMC_G`.

### Gate D: wrf.exe starts cleanly

wrf.exe must print `SUCCESS COMPLETE WRF` after two simulated minutes, and no rank's `rsl.error` may mention CFL, NaN, a segmentation fault or a fatal error. It also measures seconds per coarse step. The fire usually has not ignited in two minutes, so this rate is a floor; `--minutes` can run it past ignition.

### Gate E: how the run ended

The ending is classed as **finished**, **domain edge** (the fire reached the fire domain's boundary, which WRF reports as a stop), **crash** or **killed / still running**. Then: history files for every domain, finite values, the first ignited cell within 10 minutes and 1 km of the record, the burnt area at the last output, whether the burnt area reaches within 8 cells of the edge, and whether the output reaches the record's end.

## The ledger

Every command writes one JSON line when it starts and one when it ends (exit code, seconds), and gates and jobs add their own events: `inputs_added`, `gate_C`, `submitted`, `run_start`, `run_end`. Each line holds the user, the profile name, host, Slurm job ID, release, time, and the SHA-256 of the line before it, so editing or removing any line breaks the chain and `wrf-ledger-verify` reports where.

```text
{"t": "2026-11-17T12:02:00-05:00", "user": "ukumar", "person": "Utkarsh Kumar", "event": "submitted",
 "fire": "CANYON_2025", "job": "26901234", "spec_hash": "e387ec79aa12", "inputs": "20261117_7f3e19a2",
 "nodes": "1", "ranks": "25", "time": "48:00:00", "release": "2026.11.16-a1b2c3d", "prev": "…", "hash": "…"}
```

The honest limit: anyone can still call `sbatch` by hand. Such a run has no manifest, so `wrf-status` does not list it and `wrf-submit` will not build on it; the shell hook still records the command.

## Files

| File | Role |
| --- | --- |
| `install.sh` | installs a read-only release and points `current` at it |
| `setup.sh` | `PATH`, `WRF_ROOT`, the shell-history hook |
| `arrange_ccr.sbatch` | one-off job that copies every fire we have into this layout (see the [worked example](example.html)) |
| `bin/wrf-*` | the commands above |
| `lib/wrfgate.sh` | shared shell functions: modules, profile, ledger, Slurm mail lines |
| `lib/wrfgate/common.py` | records, namelist reading and editing, the ledger, the gate result format |
| `lib/wrfgate/geo.py` | exact Albers projection and reading WPS tiles |
| `lib/wrfgate/metem.py` | reading `met_em` files and building the fire mesh's coordinates |
| `lib/wrfgate/gate_a.py` … `gate_e.py` | the five gates; each also runs on its own with `python3 -m wrfgate.gate_X --help` |
| `lib/wrfgate/record.py`, `ledger.py` | the record and the ledger from the command line |

All of it is in the site's repository under [`tools/wrfgate/`](https://github.com/utkrshkmr/wrf-manual/tree/main/tools/wrfgate).
