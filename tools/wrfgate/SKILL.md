---
name: wrf-fire-gated-runs
description: Run any WRF-Fire simulation on UB CCR through the lab's gating system (wrfgate) - from a fire's record and met_em inputs through real.exe, a smoke run and the production run, with every step checked and logged. Use whenever the user asks to set up, check, run, rerun, size, debug or clean up a WRF-Fire run, add a new fire, or build met_em files with WPS for one.
---

# Running WRF-Fire on CCR with the gating system

You are helping a member of the lab run WRF-Fire 4.6 on UB's CCR cluster. Every run goes through the gating system (`wrfgate`): eight commands that each do one step, check it, and log it. Your job is to drive those commands, read their results, fix what they report, and ask the human before anything expensive or irreversible.

Full manual: https://utkrshkmr.github.io/wrf-manual/docs/gates.html
Worked example: https://utkrshkmr.github.io/wrf-manual/docs/example.html
Every WPS and WRF variable: https://utkrshkmr.github.io/wrf-manual/docs/index.html

## Rules (never break these)

1. **Never delete anything** under `/projects/academic/negarkhodoe/`. No `rm`, no overwriting. To get something out of the way use `wrf-setaside PATH "reason"`. Outside the shared `wrf/` folder, move things into a `_setaside/` folder beside them and tell the user.
2. **Never call `sbatch` for real.exe or wrf.exe yourself.** Use `wrf-gate C`, `wrf-gate D` and `wrf-submit`. Hand-submitted runs have no manifest and are invisible to the system.
3. **Never edit locked files**: `fire.yaml`, anything in `inputs/<version>/`, `specs/campaign/`, anything in `pipeline/releases/`, the ledger. Make a new one instead (`wrf-new-fire --replace`, a new `wrf-add-inputs`, a new spec folder).
4. **Ask the human before** `wrf-submit` (it spends core-hours: say nodes, ranks, walltime and the estimate), before `wrf-new-fire --replace`, before `scancel`, and before `wrf-setaside`. Gates C and D are cheap (one node, under 1.5 h); you may submit them once the user has asked for a run.
5. **Do not touch jobs you did not start.** Check `squeue -u $USER` before acting on a folder.
6. **Do not change thresholds to make a gate pass.** A `FAIL` means fix the input or the namelist, or report to the human.
7. **Use absolute paths and no `cd`** in commands you give or run, so they work from anywhere and in batch jobs.
8. **Report results from files, not memory**: quote the lines from `GATES.txt`, `wrf-status` or the logs you read.

## Where things are

```text
/projects/academic/negarkhodoe/wrf/
  pipeline/current/          the installed release: bin/, lib/, setup.sh, SKILL.md
  people/<user>/             profile.conf (name, email, Slurm mail), work/ for drafts
  static/                    WPS_GEOG, landfire/<LFyyyy>/<FBFM40|FBFM13>/, CA_1s (elevation); read-only
  tables/fire/               GEOGRID.TBL, METGRID.TBL, Vtable.HRRR.prs
  inputs/weather/hrrr/       HRRR GRIB2 already downloaded
  fires/<FIRE>/              fire.yaml, inputs/, specs/, runs/
  setaside/                  things moved out of the way
  ledger/                    commands.jsonl (hash-chained), shell/<user>.log
```

## Step 0: make sure the environment is ready

```bash
source /projects/academic/negarkhodoe/wrf/pipeline/current/setup.sh
wrf-me
```

- If `setup.sh` does not exist, the system is not installed: tell the user and point them to the manual's "Setting it up".
- If `wrf-me` says there is no profile, ask the user for their full name and email and which Slurm emails they want (default `END,FAIL`), then run `wrf-me --name "..." --email ... --mail END,FAIL`. Do not invent an email.

## Step 1: what does the user already have?

```bash
wrf-status
wrf-status FIRE
```

Decide from what exists:

| Situation | Go to |
| --- | --- |
| Fire is listed, inputs `current` set, a spec exists | Step 4 |
| Fire is listed but has no `current` | read the gate results (Step 3) |
| Fire not listed, but `met_em` files exist somewhere | Step 2 |
| Nothing exists for this fire | Step W (build `met_em` with WPS), then Step 2 |

Fire names are UPPER_CASE with digits and underscores, with the year: `CANYON_2025`.

## Step W: build met_em files with WPS (only if none exist)

Work in `/projects/academic/negarkhodoe/wrf/work/<FIRE>/` or the user's `people/<user>/work/<FIRE>/`. Keep every path in a namelist **under about 60 characters** (geogrid crashes with `End of record` on long paths); symlink long folders to short names if needed.

1. Ask the human for: fire name, ignition time (UTC) and point, the window (start and end, UTC), and how big the fire grew. Do not guess an ignition.
2. Domain design (manual: `domain.html`): Lambert conformal; outer domain about 900 m; fire domain about 100 m with `parent_grid_ratio = 9` (or 3/3); fire mesh ratio `subgrid_ratio_x = subgrid_ratio_y = 4` **in `&share`**; ignition at least several km from every fire-domain edge, more for a big fire; `(e_we-1)` and `(e_sn-1)` of each nest divisible by its parent ratio.
3. `namelist.wps`: `geog_data_path = '/projects/academic/negarkhodoe/wrf/static/WPS_GEOG'`, `opt_geogrid_tbl_path` and `opt_metgrid_tbl_path` pointing at `/projects/academic/negarkhodoe/wrf/tables/fire`; `geog_data_res` for the fire domain selecting the LANDFIRE fuel and 1-arc-second elevation entries that `GEOGRID.TBL` defines (read the table to get their names). Pick the LANDFIRE release closest to the fire's year.
4. Weather: HRRR `wrfprsf00` analyses, hourly, `Vtable.HRRR.prs`, `interval_seconds = 3600`. Use files from `inputs/weather/hrrr/` or download the missing hours from NOAA's HRRR archive into a new folder there.
5. Run all three programs in **one sbatch job on one core**:

```bash
#!/bin/bash
#SBATCH -p general-compute
#SBATCH --qos=general-compute
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --mem=64G
#SBATCH -t 06:00:00
module purge
module load gcc/11.2.0 openmpi/4.1.1 wps/4.6.0-dmpar
srun -n 1 geogrid.exe < /dev/null
/path/to/link_grib.csh /path/to/hrrr/*wrfprsf00*
ln -sf /projects/academic/negarkhodoe/wrf/tables/fire/Vtable.HRRR.prs Vtable
srun -n 1 ungrib.exe < /dev/null
srun -n 1 metgrid.exe < /dev/null
```

   Do not run more ranks: every rank reads the whole HRRR intermediate file, and 8 ranks run out of time. Do not run the programs bare (without `srun`) inside the job.
6. Check: `geogrid.log`, `ungrib.log`, `metgrid.log` each end with `Successful completion`. Then go to Step 2; gate A and B do the real checking.

## Step 2: record the fire and register its inputs

Record from a namelist that was used for this fire:

```bash
wrf-new-fire FIRE --from-namelist /path/namelist.input --fuel-layer /projects/academic/negarkhodoe/wrf/static/landfire/LF2024/FBFM40
```

or from explicit values (all UTC):

```bash
wrf-new-fire FIRE --start "2025-08-07 18:00" --end "2025-08-09 00:00" --ignition "2025-08-07 20:25" --lat 35.0 --lon -118.0 --fuel-layer /projects/academic/negarkhodoe/wrf/static/landfire/LF2024/FBFM40
```

Show the printed record to the user and confirm the window and ignition before going on. Then:

```bash
wrf-add-inputs FIRE /path/to/met_em_folder --note "what these are and how they were made"
```

This copies the files into a locked version folder, runs gates A and B, and sets `current` if neither failed. "identical inputs are already registered" means nothing to do.

## Step 3: read gates A and B

```bash
cat /projects/academic/negarkhodoe/wrf/fires/FIRE/inputs/VERSION.gates/GATES.txt
```

| Check failed | Meaning | Fix |
| --- | --- | --- |
| A05_window | inputs do not cover the record's start or end | more weather hours in WPS, or a record with the right window |
| A08_finite | NaN or Inf in a field | rerun metgrid; check the GRIB files for those times |
| A09_nest_rule | a nest's size does not divide by its ratio | change `e_we`/`e_sn` in `namelist.wps`, rerun WPS |
| A11/A12 | no fire mesh or no fuel | `subgrid_ratio` missing from `&share`, or the fuel entry not selected in `geog_data_res` |
| A14 | invalid fuel codes | wrong fuel layer, or the layer's missing value leaking in |
| A16 (warn) | code 204 present | the spec's `namelist.fire` must set `nfuelcats = 54` |
| A19/A20 | ignition outside or too near the fire domain's edge | move or enlarge the fire domain in WPS |
| A21 | ignition on an unburnable cell | check the ignition point with the user |
| B02 FAIL (< 90%) | fuel map does not match LANDFIRE where it should be | see B07: maybe a different release; if every release is low, the layer is misplaced. Report to the human |
| B02 WARN (90–98%) | mostly matches | report the numbers; do not proceed silently |
| B09 (warn) | terrain differs from the elevation layer | report; check `geog_data_res` for the terrain entry |

If a gate failed and the user wants to continue anyway, they can pass `--inputs VERSION` explicitly to later steps; ask first.

## Step 4: the spec (namelists)

A spec is a folder with `namelist.input` and `namelist.fire` (and `iofields*.txt` if used). Start from an existing spec of a similar fire, copy it into `people/<user>/work/<FIRE>_<variant>/` (or a new `fires/FIRE/specs/<name>/`), and edit. Never edit `specs/campaign/`.

Must agree with the inputs (gate C checks): `max_dom`, `e_we`, `e_sn`, `e_vert`, `dx`, `dy`, `parent_grid_ratio`, `i_parent_start`, `j_parent_start`, `num_metgrid_levels`, `num_metgrid_soil_levels`, `sr_x`/`sr_y` (= the fire mesh ratio on the fire domain, 0 elsewhere), start time = record start, end time = record end. Get the numbers from `inputs/VERSION.gates/gate_A.json` (`facts`) and from `ncdump -h` of one `met_em` file.

On the fire domain: `ifire = 2`, `fire_fuel_read = -1`, `fire_ignition_start_lat1/lon1` = record, `fire_ignition_start_time1` = seconds from the run's start to the record's ignition, a radius (`fire_ignition_radius1`) and end time. Fuel moisture: `fire_fmc_read = 1` with the value in `namelist.fire` is the simple route (manual: `moisture.html`).

Time step: `time_step` about 6 × `dx` in km of the outer domain, lower if gate D reports CFL.

## Step 5: gate C (real.exe), then gate D (smoke run)

```bash
wrf-gate C FIRE /path/to/spec
```

Wait for the job (Slurm emails the user; or `squeue -u $USER`), then read `fires/FIRE/runs/<stamp>_gateC_<spec>/GATES.txt`. If real.exe failed, read that folder's `rsl.error.0000` from the bottom.

```bash
wrf-gate D FIRE /projects/academic/negarkhodoe/wrf/fires/FIRE/runs/<stamp>_gateC_<spec>
```

For a large fire, add `--ranks 64 --constraint SAPPHIRE-RAPIDS-IB` (or the node type the run will use) so the measured rate is meaningful. Read `GATES.txt` in the gate D folder: `D01` must pass; `D02` lists CFL/NaN/segfault lines with their rank log; `D03` is seconds per coarse step before ignition.

Common C/D failures:

| Message | Fix |
| --- | --- |
| C05 geometry mismatch | the spec's domain numbers differ from the inputs; copy them from gate A's facts |
| C07 boundaries short | `end_*` past the last `met_em` time |
| C11/C12 ignition | `fire_ignition_start_time1` or lat/lon differ from the record |
| C13 code 204 | add `nfuelcats = 54` to `namelist.fire` (and the 54th category's parameters) |
| D02 CFL | lower `time_step`; check `epssm`, `w_damping = 1` |
| D02 segfault at start | too many ranks for the grid (cap is gate A's `rank_cap`), or memory: fewer ranks per node |

Any change to the spec means gates C and D again: `wrf-submit` matches them by the namelists' hash.

## Step 6: size and submit

Sizing (manual: `run.html`):

- **Ranks**: at most gate C's `rank_cap` (`⌊nx/10⌋ × ⌊ny/10⌋` on the tightest domain). Small fire: the cap on one whole node. Large fire: up to 24 whole nodes. Use whole nodes; ranks a multiple of the cores per node, at most the cap.
- **Walltime**: `seconds per step × steps × 1.15 + 1 h`, with steps = simulated seconds ÷ `time_step`; × 1.3 for a fire never run before, and more because the rate after ignition is slower than gate D's. Must be ≤ 72 h; if not, more nodes, or tell the user it needs restarts.
- Node types: Cascade Lake 40 cores, Ice Lake 56, Sapphire Rapids 64 (fastest, about 1.8× Cascade Lake).

Tell the user: nodes, ranks, node type, walltime, and core-hours (`nodes × cores × walltime`). After they agree:

```bash
wrf-submit FIRE /path/to/spec --nodes N --ranks R --time HH:MM:SS --constraint SAPPHIRE-RAPIDS-IB --name short_label
```

## Step 7: when the run ends

Gate E runs inside the job. Read `fires/FIRE/runs/<stamp>_<label>/GATES.txt`:

- **finished**: check E05/E06 (ignition time and place match) and E09 (reached the end).
- **domain edge**: the fire reached the fire domain's boundary. Not a crash. Running further needs a larger fire domain: new WPS run, new input version.
- **crash**: read the run's `rsl.error.*` files; find the first rank that printed an error (`grep -l -i -E "error|cfl|nan" rsl.error.*`).
- **killed_or_running**: hit the walltime or was cancelled; `sacct -j JOBID` tells which. If killed, rerun gate E by hand after looking: `wrf-gate E FIRE RUN_DIR`.

## Other commands

```bash
wrf-status FIRE
wrf-gate A FIRE VERSION
wrf-gate B FIRE VERSION
wrf-gate E FIRE RUN_DIR
wrf-setaside /projects/academic/negarkhodoe/wrf/fires/FIRE/runs/RUN "reason"
wrf-ledger-verify
```

Every gate also runs standalone: `python3 -m wrfgate.gate_b --help` (after sourcing `setup.sh` and `pipeline/current/lib/wrfgate.sh`).

## Known pitfalls on CCR

- Modules: `module load gcc/11.2.0 openmpi/4.1.1 wps/4.6.0-dmpar` gives WPS and WRF 4.6 together.
- WPS on 1 core only; WRF on whole nodes with `--exclusive`.
- Keep namelist paths short (under about 60 characters).
- `subgrid_ratio_x/_y` in `&share` of `namelist.wps`, not `&geogrid`.
- In batch loops that call `srun`, redirect stdin (`< /dev/null`), or `srun` eats the loop's input.
- Slurm runs a copy of the batch script from a spool folder: do not locate helper files relative to `$0` inside sbatch scripts; use absolute paths.
- The fire moisture model's tables are indexed by raw fuel code; with LANDFIRE codes, moisture routes C and D need care (manual: `moisture.html`).
- The LANDFIRE layers in `static/landfire/` are anchored at the south-west corner; how geogrid places Albers layers depends on that anchor, which is under study. Do not change any layer's `index` file.
