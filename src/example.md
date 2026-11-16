---
title: Worked example: every fire we have run
kicker: Running it safely
lead: The same six steps, fire by fire, starting with Eaton. The arrange job does the first two steps for all seven fires at once; after that each fire is three commands and a wait.
---

## Before the first fire

Install a release and make your profile, as on [the gating system](gates.html#setting-it-up) page:

```bash
git clone https://github.com/utkrshkmr/wrf-manual.git /projects/academic/negarkhodoe/utkarshk/wrf-manual
bash /projects/academic/negarkhodoe/utkarshk/wrf-manual/tools/wrfgate/install.sh
echo 'source /projects/academic/negarkhodoe/wrf/pipeline/current/setup.sh' >> ~/.bashrc
source /projects/academic/negarkhodoe/wrf/pipeline/current/setup.sh
wrf-me --name "Utkarsh Kumar" --email ukumar@buffalo.edu --mail END,FAIL
```

## Step 1 and 2 for all fires: the arrange job

The fires we have run, or have inputs for, live in several older folders. One job copies each into the gated layout: it writes the record from the namelist the fire was run with, copies that namelist (and `namelist.fire`) as the spec `campaign`, and registers the `met_em` files as an input version, which runs gates A and B.

```bash
sbatch /projects/academic/negarkhodoe/wrf/pipeline/current/arrange_ccr.sbatch
```

| Fire | Record name | `met_em` from | Run in the campaign |
| --- | --- | --- | --- |
| Eaton 2025 | `EATON_2025` | `utkarshk/fires/EATON` | yes, 24 nodes |
| Canyon 2025 | `CANYON_2025` | `Thursday_deadline_fires/CANYON` | yes, 25 ranks |
| Cranston 2018 | `CRANSTON_2018` | `Thursday_deadline_fires/CRANSTON` | yes, 36 ranks |
| Long 2024 | `LONG_2024` | `Thursday_deadline_fires/LONG` | yes, 36 ranks |
| Airport | `AIRPORT` | `WRF_NCAR_Fires/AIRPORT` | inputs only |
| Bradford Branch | `BRADFORD_BRANCH` | `WRF_NCAR_Fires/BRADFORD_BRANCH` | inputs only |
| Carmel | `CARMEL` | `WRF_NCAR_Fires/CARMEL` | inputs only |

What it does and does not do:

- **Copies only.** It reads the old folders and never moves, edits or deletes anything in them, and submits nothing. Jobs already running are not touched.
- **Finds the files itself.** For each fire it takes the folder with the most `met_em.d01` files, and the newest `namelist.input` that has an ignition, under `utkarshk/fires/<FIRE>`, `utkarshk/campaign`, `utkarshk/runs` and the `met_em` folder. The log lists every other candidate it saw.
- **Can be told.** Any choice can be overridden when submitting, e.g. `sbatch --export=ALL,NL_LONG_2024=/path/namelist.input,MET_LONG_2024=/path/met_em_folder …/arrange_ccr.sbatch`.
- **Picks the reference fuel layer by the fire's year** (2016 release for fires before 2022, otherwise the matching year, 2024 for 2024 and later); gate B's release scan then shows which release each input really matches.
- **Can be rerun.** Records that exist are kept, identical inputs are refused as already registered, and a fire it skipped can be fixed and picked up next time.

The log is `wrf/ledger/arrange_<job>.out`, ending in a one-line summary per fire, and `wrf-status` shows the result:

```text
$ wrf-status
FIRE               START                      CURRENT_INPUTS         RUNS
CANYON_2025        2025-08-07 18:00:00        20261116_7f3e19a2      0
EATON_2025         2025-01-08 00:00:00        20261116_c04a91e7      0
...
```

A fire whose gate B **failed** has its inputs registered but no `current`; read its `GATES.txt` before going on.

## Eaton 2025

The largest fire: 6.1 million column updates per coarse step, a rank cap of 2,025, and in the campaign 1.16 s per step on 24 Sapphire Rapids nodes.

**1. Look at the record and the gates.**

```bash
wrf-status EATON_2025
cat /projects/academic/negarkhodoe/wrf/fires/EATON_2025/inputs/$(readlink /projects/academic/negarkhodoe/wrf/fires/EATON_2025/inputs/current).gates/GATES.txt
```

Check that the record's window is Jan 8 00:00 → 17:00 UTC and that the ignition time and place are the ones you mean. If not, make it again from the right namelist, which keeps the old one: `wrf-new-fire EATON_2025 --from-namelist /path/namelist.input --replace`.

**2. Gate C: real.exe on the campaign namelists.**

```bash
wrf-gate C EATON_2025 /projects/academic/negarkhodoe/wrf/fires/EATON_2025/specs/campaign
```

It prints the job ID and the run folder `fires/EATON_2025/runs/<stamp>_gateC_campaign`. You get an email when it ends; then:

```bash
cat /projects/academic/negarkhodoe/wrf/fires/EATON_2025/runs/*_gateC_campaign/GATES.txt
```

**3. Gate D: two minutes of wrf.exe.** On one Sapphire Rapids node, so the measured rate is for the node type the run will use:

```bash
wrf-gate D EATON_2025 /projects/academic/negarkhodoe/wrf/fires/EATON_2025/runs/<stamp>_gateC_campaign --ranks 64 --constraint SAPPHIRE-RAPIDS-IB
```

**4. The run.** 24 whole nodes, 1,530 ranks as in the campaign:

```bash
wrf-submit EATON_2025 /projects/academic/negarkhodoe/wrf/fires/EATON_2025/specs/campaign --nodes 24 --ranks 1530 --time 24:00:00 --constraint SAPPHIRE-RAPIDS-IB --name full17h
```

The campaign's first 5 simulated hours took 3.7 h on 24 nodes; the fire makes later hours slower, so 24 h for all 17 leaves room under the 72-hour limit. `wrf-submit` refuses if the namelists changed since gate D, if 1,530 is over the cap, or if the same namelists are already queued.

**5. When it ends**, gate E has already run inside the job:

```bash
wrf-status EATON_2025
cat /projects/academic/negarkhodoe/wrf/fires/EATON_2025/runs/*_full17h/GATES.txt
```

## Canyon, Cranston and Long

The same three commands, one node each. Every fire's gate C folder name comes from step 2's output.

| Fire | Window (UTC) | Rank cap | `wrf-submit` options |
| --- | --- | --- | --- |
| `CANYON_2025` | Aug 7 18:00 → Aug 9 00:00 | 25 | `--nodes 1 --ranks 25 --time 48:00:00` |
| `CRANSTON_2018` | Jul 25 16:00 → Jul 26 12:00 | 36 | `--nodes 1 --ranks 36 --time 48:00:00` |
| `LONG_2024` | Jul 15 20:00 → Jul 17 00:00 | 36 | `--nodes 1 --ranks 36 --time 56:00:00 --constraint SAPPHIRE-RAPIDS-IB` |

```bash
F=CANYON_2025
S=/projects/academic/negarkhodoe/wrf/fires/$F/specs/campaign
wrf-gate C $F $S
wrf-gate D $F /projects/academic/negarkhodoe/wrf/fires/$F/runs/<stamp>_gateC_campaign
wrf-submit $F $S --nodes 1 --ranks 25 --time 48:00:00
```

Walltimes: Cranston took 41.6 h in the campaign; the others use the [walltime rule](run.html) with its margin. Gate D prints the seconds per step before ignition; multiply by the number of steps and by 1.15, and add an hour, to check the number before submitting.

<div class="note" markdown="1">
**Long reaches its domain edge.** In the campaign, Long's fire hit the edge of the fire domain at Jul 16 22:24 and WRF stopped. Gate E classes that ending as **domain edge**, not as a crash. Running past it needs a larger fire domain, which means new `met_em` files: a new input version, then gates C and D again.
</div>

## Airport, Bradford Branch and Carmel

These came from NCAR as `met_em` files only. The arrange job registers their inputs (gates A and B) if it finds a `namelist.input` with an ignition next to them, since the record comes from it. If it does not, give the record by hand, then register the inputs:

```bash
wrf-new-fire AIRPORT --start "YYYY-MM-DD HH:MM" --end "YYYY-MM-DD HH:MM" --ignition "YYYY-MM-DD HH:MM" --lat LAT --lon LON
wrf-add-inputs AIRPORT /projects/academic/negarkhodoe/WRF_NCAR_Fires/AIRPORT --note "NCAR met_em"
```

They have no spec yet. Write one in your `people/<username>/work/` folder: copy Canyon's `namelist.input` and `namelist.fire`, set the domain sizes, `dx`, the time step and the window from gate A's facts (`inputs/<version>.gates/gate_A.json`), and the ignition from the record; [Phase 5](real.html) and [Phase 6](fire.html) explain each variable. Then gates C and D will tell you what is still wrong, before any long job is queued.

## Changing something

| You want to | Do |
| --- | --- |
| try other namelists | copy `specs/campaign` to a new spec folder, edit it, then gates C, D and `wrf-submit` with it |
| use new `met_em` files | `wrf-add-inputs`; it becomes `current` if gates A and B pass; older versions stay, and `--inputs V` picks one |
| fix a wrong record | `wrf-new-fire FIRE … --replace` |
| get rid of a failed run | `wrf-setaside RUN_DIR "why"` |
| stop a run | `scancel JOB`; gate E does not run, so run `wrf-gate E FIRE RUN_DIR` after |
