---
title: Eaton 2025
kicker: Examples · EATON_2025
lead: The largest fire we run: an 81 km fire domain at 100 m, 2,025-rank cap, and a full run that needs 24 whole nodes. Ignited in the evening of January 7 local time, in Santa Ana winds.
---

## The fire card

Everything that defines this fire, from the NCAR reference case `eaton_100_25_LF2024_WRF` and our campaign namelist. The exact card, with every value read from the shared folder, is one command away:

```bash
wrf-card EATON_2025
```

```text
name:                EATON_2025
start:               2025-01-08 00:00
end:                 2025-01-08 17:00
ignition_time:       2025-01-08 02:18
ignition_lat:        34.186040
ignition_lon:        -118.093250
ignition_radius_m:   100
outer_cells:         450
outer_dx_m:          900
fire_cells:          811
fire_ratio:          9
fire_start_i:        180
fire_start_j:        180
fire_mesh_ratio:     4
weather_interval_s:  10800
fuel_layer:          /projects/academic/negarkhodoe/wrf/static/landfire/LF2024/FBFM40
fuel_moisture:       0.08
fire_feedback:       1
time_step_s:         3
base_spec:           EATON_2025/campaign
```

Other settings in its spec that the card carries over through `base_spec`: `fire_lsm_zcoupling = .true.` with `fire_lsm_zcoupling_ref = 60`, `fire_ignition_ros1 = 0.10`, ignition over 800 s (`fire_ignition_end_time1 = 9080`), `fire_upwinding = 9`, `fire_lsm_reinit = .true.`; physics `mp_physics = 6`, `ra_lw_physics = 4`, `ra_sw_physics = 1`, `sf_sfclay_physics = 1`, `sf_surface_physics = 2`, `bl_pbl_physics = 1, 0`, no cumulus; 60 vertical levels, weather with 41 levels and 9 soil levels every 3 hours.

Rank cap: **2,025**.

## Run it from an AI chat

Copy the [skill](skill.html) into a new chat, then paste underneath:

```text
Run this fire. Here is its card:
<paste the output of: wrf-card EATON_2025>
```

The assistant checks the card with you, then walks you through the commands below one at a time.

## Run it with the commands

**1. Check the fire and its inputs.**

```bash
wrf-status EATON_2025
wrf-card EATON_2025
```

Read the card: times, ignition, domains, and under *Measured* the gate A and B results and `fire_fuel_read` (must be `-1`).

**2. Gate C: real.exe on the campaign spec.**

```bash
wrf-gate C EATON_2025 /projects/academic/negarkhodoe/wrf/fires/EATON_2025/specs/campaign
```

It prints the run folder; Slurm emails you when it ends. Then `cat /projects/academic/negarkhodoe/wrf/fires/EATON_2025/runs/<stamp>_gateC_campaign/GATES.txt`.

**3. Gate D: two minutes of wrf.exe.** Gate D on one Sapphire Rapids node: add `--ranks 64 --constraint SAPPHIRE-RAPIDS-IB`, so the measured rate is for the node type the run will use.

```bash
wrf-gate D EATON_2025 /projects/academic/negarkhodoe/wrf/fires/EATON_2025/runs/<stamp>_gateC_campaign --ranks 64 --constraint SAPPHIRE-RAPIDS-IB
```

**4. Submit.** In the campaign, 1,530 ranks on 24 Sapphire Rapids nodes ran at 1.16 s per step, and the first 5 simulated hours took 3.7 h. The fire makes later hours slower, so 24 h for all 17 leaves room under the 72-hour limit. That is 24 × 64 × 24 ≈ 36,900 core-hours charged.

```bash
wrf-submit EATON_2025 /projects/academic/negarkhodoe/wrf/fires/EATON_2025/specs/campaign --nodes 24 --ranks 1530 --time 24:00:00 --constraint SAPPHIRE-RAPIDS-IB --name rerun
```

**5. Watch it, and read how it ended.**

```bash
wrf-watch EATON_2025
cat /projects/academic/negarkhodoe/wrf/fires/EATON_2025/runs/<stamp>_rerun/GATES.txt
```

Gate E runs inside the job when it ends: *finished*, *domain edge*, *crash* or *killed*, plus whether the first burning cell matches the card's ignition time and place.

## Make a variant

Copy the card, change what you are testing (and the `note:` line), and make it. Times and domains unchanged means the existing inputs are reused, so no WPS:

```bash
wrf-card EATON_2025 > /projects/academic/negarkhodoe/wrf/people/$USER/work/eaton_variant.card
wrf-card --make /projects/academic/negarkhodoe/wrf/people/$USER/work/eaton_variant.card
```

Then gates C and D and `wrf-submit` on the spec folder it prints, with a `--name` that says what changed. Ideas: [fuel moisture](moisture.html), [one-way coupling](coupling.html), [slope sensitivity](terrain.html#the-slope-effect), [another ignition](ignitions.html).

## Good to know

- Rank 0 used 168 GB in the campaign: whole 512 GB nodes (Sapphire Rapids or Ice Lake), never Cascade Lake.
- An earlier CCR namelist for Eaton had `fire_fuel_read = 0` (one fuel everywhere) instead of `-1` (the fuel map). The card prints `fire_fuel_read` under *Measured*; gate C fails if it is not `-1`.

