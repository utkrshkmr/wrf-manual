---
title: Canyon 2025
kicker: Examples · CANYON_2025
lead: Our worked example throughout the manual: a 21.6 km fire domain at 100 m on a 54 × 54 outer grid, HRRR weather every hour, LANDFIRE 2024 fuels. One node is enough.
---

## The fire card

Everything that defines this fire, from Nisha's `namelist.wps` (shown on [Domain design](domain.html)) and the campaign. The exact card, with every value read from the shared folder, is one command away:

```bash
wrf-card CANYON_2025
```

```text
name:                CANYON_2025
start:               2025-08-07 18:00
end:                 2025-08-09 00:00
ignition_time:       2025-08-07 20:25
ignition_lat:        (printed by wrf-card)
ignition_lon:        (printed by wrf-card)
center_lat:          34.46681
center_lon:          -118.70165
outer_cells:         54
outer_dx_m:          900
fire_cells:          217
fire_ratio:          9
fire_start_i:        15
fire_start_j:        15
fire_mesh_ratio:     4
weather:             HRRR
weather_interval_s:  3600
vtable:              Vtable.HRRR.prs
fuel_layer:          /projects/academic/negarkhodoe/wrf/static/landfire/LF2024/FBFM40
fuel_key:            lf2024
terrain_layer:       /projects/academic/negarkhodoe/wrf/static/CA_1s
terrain_key:         ca_1s
base_spec:           CANYON_2025/campaign
```

<div class="note" markdown="1">
Values shown as *(printed by wrf-card)* (`ignition_lat`, `ignition_lon`) are in the fire's record in the shared folder but not yet on this page.
</div>

Rank cap: **25**.

## Run it from an AI chat

Copy the [skill](skill.html) into a new chat, then paste underneath:

```text
Run this fire. Here is its card:
<paste the output of: wrf-card CANYON_2025>
```

The assistant checks the card with you, then walks you through the commands below one at a time.

## Run it with the commands

**1. Check the fire and its inputs.**

```bash
wrf-status CANYON_2025
wrf-card CANYON_2025
```

Read the card: times, ignition, domains, and under *Measured* the gate A and B results and `fire_fuel_read` (must be `-1`).

**2. Gate C: real.exe on the campaign spec.**

```bash
wrf-gate C CANYON_2025 /projects/academic/negarkhodoe/wrf/fires/CANYON_2025/specs/campaign
```

It prints the run folder; Slurm emails you when it ends. Then `cat /projects/academic/negarkhodoe/wrf/fires/CANYON_2025/runs/<stamp>_gateC_campaign/GATES.txt`.

**3. Gate D: two minutes of wrf.exe.** Gate D on one node with the default ranks.

```bash
wrf-gate D CANYON_2025 /projects/academic/negarkhodoe/wrf/fires/CANYON_2025/runs/<stamp>_gateC_campaign
```

**4. Submit.** 25 ranks is WRF's cap for this grid (the 54 × 54 outer domain allows ⌊54/10⌋² = 25), so one whole node of any type. The campaign simulated the full 30 hours; use gate D's rate to check 48 h before submitting.

```bash
wrf-submit CANYON_2025 /projects/academic/negarkhodoe/wrf/fires/CANYON_2025/specs/campaign --nodes 1 --ranks 25 --time 48:00:00 --name rerun
```

**5. Watch it, and read how it ended.**

```bash
wrf-watch CANYON_2025
cat /projects/academic/negarkhodoe/wrf/fires/CANYON_2025/runs/<stamp>_rerun/GATES.txt
```

Gate E runs inside the job when it ends: *finished*, *domain edge*, *crash* or *killed*, plus whether the first burning cell matches the card's ignition time and place.

## Make a variant

Copy the card, change what you are testing (and the `note:` line), and make it. Times and domains unchanged means the existing inputs are reused, so no WPS:

```bash
wrf-card CANYON_2025 > /projects/academic/negarkhodoe/wrf/people/$USER/work/canyon_variant.card
wrf-card --make /projects/academic/negarkhodoe/wrf/people/$USER/work/canyon_variant.card
```

Then gates C and D and `wrf-submit` on the spec folder it prints, with a `--name` that says what changed. Ideas: [fuel moisture](moisture.html), [one-way coupling](coupling.html), [slope sensitivity](terrain.html#the-slope-effect), [another ignition](ignitions.html).

## Good to know

- The fuel map in the NCAR/Nisha inputs matches our LANDFIRE 2024 copy at 97.3% cell by cell, because of how geogrid places the layer; gate B reports the number. The anchor study will settle which placement is right.

