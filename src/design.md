---
title: The workflow we designed
kicker: Design · draft for the lab
lead: A lab-wide workflow that lives in one shared folder, with no app to install. Five shell scripts over Slurm do the bookkeeping, the checks and the sizing. People keep every decision about WRF, the system takes every decision about the machine, and everything is recorded.
---

## The division of labour

| A collaborator decides | The system decides |
| --- | --- |
| Which fire, with its ignition time and place | Node type, by racing the three types |
| Every WRF setting: physics, domains, fire options, output | Rank and node counts, from the measured scaling |
| Variants for experiments, by WRF's own variable names | Walltime, continuations and retries |
| Research extensions, such as a fuel-moisture grid | Where files live, what is kept, what is pruned |
| When to run, and from which input version | What gets checked, and what counts as a failure |

## One shared folder

```text
/projects/academic/negarkhodoe/wrf/
  setup.sh                   source once: path, modules, shell log
  pipeline/
    releases/2026.11.0/      code, read-only; current -> one release
      bin/                   the five scripts
      schema/ capabilities/ defaults/
  static/ reference/         geography, LANDFIRE, elevation; read-only
  tables/fire/               GEOGRID.TBL, METGRID.TBL, Vtables
  fires/LONG_2024/
    fire.yaml                the record: ignition, window, source
    inputs/20261018_7f3e/    one folder per upload, locked
    specs/default.yaml       WRF configuration, grouped; variants beside it
    runs/20261102_1402_default_7f3e/
  ledger/                    commands.jsonl, events/, shell/
  calibration/               weekly lookup tables
  results/ reports/
```

- **Group-owned and group-writable.** Every file anyone creates belongs to the lab group; deleting someone else's file still needs them.
- **Code is released, not edited.** A release is a read-only folder; `current` points at one. Running jobs keep the release they started with.
- **One line in `.bashrc`** (`source …/wrf/setup.sh`) is all a person adds to their own account.

## Five scripts

{{fig:workflow|**The interface.** Each script does the bookkeeping and checks, then calls `sbatch`. Watching and stopping stay with Slurm's own `squeue`, `scancel` and `sacct`.}}

| Script | What it adds over plain `sbatch` |
| --- | --- |
| `add_inputs.sh FIRE /path` | Copies an upload into a new hashed version folder, runs gates A–C, locks it, writes the manifest |
| `check.sh FIRE [spec]` | Compiles the spec into WRF's namelists, checks every name against WRF's Registry, refuses edits to locked keys, shows the diff against the lab default |
| `smoke.sh FIRE [spec]` | Two simulated minutes of wrf.exe on one node: catches crashes in ten minutes instead of after a day in the queue |
| `run.sh FIRE [spec] [--inputs V]` | New run folder, sizing, the node-type race, the continuation chain, the Slurm script and the manifest, then submits |
| `status.sh [FIRE]` | Every registered run: simulated time reached, rate, estimated finish, how it ended |

The Slurm script each run leaves in its folder explains every decision in comments:

```bash
#SBATCH --job-name=wf_LONG_2024_default
#SBATCH --constraint=SAPPHIRE-RAPIDS-IB
#SBATCH --nodes=1 --ntasks=36 --exclusive
#SBATCH --time=56:00:00
# 36 ranks = WRF cap for a 60x60 coarse grid
# 56 h = 4.9 s/step x 33,600 steps x 1.15 + 1 h
# inputs 7f3e  spec default 3c1a  release 2026.11.0
srun ./wrf.exe
```

## The spec: one grouped file

WRF's `namelist.input` is about 300 flat variables. The spec groups them the way people think about a simulation, and a compiler writes the flat form:

```yaml
fire: LONG_2024
time:                      # locked, from fire.yaml
  start: 2024-07-15 20:00
  ignition: 2024-07-15 21:30
domains:
  d01: {dx: 900 m, size: 60 x 60, step: 3 s}
  d02: {dx: 100 m, ratio: 9, fire_subgrid: 4}
physics:
  microphysics: thompson
  boundary_layer: ysu
fire:
  ignition: {radius: 100 m, duration: 800 s}
  fuel: {source: input_file}            # locked
  fuel_moisture: {mode: constant, value: 0.08}
output:
  history: {d01: 60 min, d02: 15 min}
raw:                       # anything WRF allows, by WRF's own name
  fire_wind_height: {d02: 2.0}
reason: wind-height sensitivity
```

- **Locked keys** (dates, ignition, fuel source, restart settings) come from the fire record. Every ignition-time error we had came from editing exactly these.
- **The `raw:` block** sets anything WRF allows by its own name, checked against WRF's Registry, so a typo or a wrong-length list is caught before submission.

## Versions and manifests

- **Uploads never overwrite.** A corrected set of files is a new version; `current` moves to it only after its gates pass. Old runs keep pointing at what they used.
- **Every run is a new folder,** with inputs linked in read-only, so no run can change what the next one sees.
- **The manifest is the receipt:** input hash, spec hash, release, user, time, sizing decisions and job IDs. Any run can be rebuilt exactly.
- **A folder without a manifest is unregistered:** scripts refuse it, status ignores it, nothing publishes it.
- **One active job per folder,** held by a lock file.

## A run's life

{{fig:lifecycle|**Steps and endings.** Each of the campaign's incidents, from the duplicate job to the leftover continuations and the domain-edge runs counted as crashes, has a step here that closes it.}}

## The weekly lookup table

{{fig:lookup|**The group's experience, accumulated.** One row per fire × node type × rank count, with the measured rate after ignition, peak memory and median queue wait, plus the refitted device constants. Each table is dated and kept; a run's manifest names the table it was sized from.}}

| Fire | Node type | Ranks | Runs | s/step after ignition | Peak memory | Median wait | Last run |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CRANSTON | Sapphire Rapids | 36 | 1 | 6.19 s | 18 GB | 0.0 h | Oct 20 |
| CRANSTON | Cascade Lake | 36 | 1 | 9.95 s | 17 GB | 0.0 h | Oct 21 |
| EATON | Sapphire Rapids | 1,530 | 1 | 1.16 s | 168 GB on rank 0 | 9.4 h | Oct 19 |
| any | device constants | | 24 | a = 207 · 169 · 114 µs | k = 110 | 23 · 45 · — h by type | refit Oct 25 |

Rows from the October campaign.

## Research extensions as modules

Anything WRF can do that needs more than a namelist line is a capability module: one folder that declares the spec keys it reads, the namelist variables it sets, the input fields it writes, the checks it runs, and the WRF version it needs. The worked example is a fuel-moisture grid:

```yaml
fire:
  fuel_moisture:
    mode: grid
    file: fmc_2024-07-15.nc
    variable: fmc
    units: fraction
```

The module regrids the file onto the fire mesh, writes it into `wrfinput_d02` as `FMC_G` as a new input version, sets `fire_fmc_read = 0`, checks the values (0–0.4, full coverage, a date within the window), and records it all in the manifest; this is [route B](moisture.html#route-b-a-per-cell-moisture-map). Any run with a module or a `raw:` setting is labelled a variant, so it is never mistaken for the fire's baseline.

## Bookkeeping

- **The ledger.** The scripts write one JSON line before and after every call: who, when, where, the full command, release, exit code, duration, and what it touched. Each line carries the hash of the line before it, so editing or deleting any line breaks the chain, and a nightly check reports it.
- **Jobs log their own events:** started, rate measured, continuation queued, ended with its class.
- **Shell commands:** `setup.sh` adds a bash hook that appends each command to a per-user log. Everyone sources it to get the scripts, so in practice everyone is covered.
- **The honest limit:** whatever produces a registered input or run is always logged; anything else is marked unregistered.

## Trying it

| Stage | What | Pass when |
| --- | --- | --- |
| 0 | Create the folder, install a release, stage the reference data | A second user sees the scripts and can write a fire folder |
| 1 | Canyon end to end | Finishes, gate E passes, continuation cancelled, walltime within 15% of the estimate |
| 2 | Break it on purpose: a bad fuel map, a locked key edited, a hand `sbatch`, an edited ledger line, a second job on a folder | Every one refused or flagged, with the reason in the ledger |
| 3 | Long with a fixed domain, as a second input version | Both versions listed; the run finishes or ends as "domain edge", never "crash" |
| 4 | A variant by a second person | Labelled a variant, their commands in the ledger, baseline untouched |
| 5 | Eaton, full 17 hours, 24 nodes | Finishes in one job, rank 0 under 512 GB |

Budget: about 25,000 core-hours, most of it the full Eaton. Nothing existing is touched; the lab switches only after stage 5 passes.
