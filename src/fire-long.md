---
title: Long 2024
kicker: Examples · LONG_2024
lead: A 28-hour window with a rank cap of 36. In the campaign the fire reached the edge of its fire domain before the end, which WRF treats as a stop.
---

## The fire card

Everything that defines this fire, from the campaign. The exact card, with every value read from the shared folder, is one command away:

```bash
wrf-card LONG_2024
```

```text
name:                LONG_2024
start:               2024-07-15 20:00
end:                 2024-07-17 00:00
ignition_time:       (printed by wrf-card)
ignition_lat:        (printed by wrf-card)
ignition_lon:        (printed by wrf-card)
base_spec:           LONG_2024/campaign
```

<div class="note" markdown="1">
Values shown as *(printed by wrf-card)* (`ignition_time`, `ignition_lat`, `ignition_lon`) are in the fire's record in the shared folder but not yet on this page.
</div>

Rank cap: **36**.

## Run it from an AI chat

Copy the [skill](skill.html) into a new chat, then paste underneath:

```text
Run this fire. Here is its card:
<paste the output of: wrf-card LONG_2024>
```

The assistant checks the card with you, then walks you through the commands below one at a time.

## Run it with the commands

**1. Check the fire and its inputs.**

```bash
wrf-status LONG_2024
wrf-card LONG_2024
```

Read the card: times, ignition, domains, and under *Measured* the gate A and B results and `fire_fuel_read` (must be `-1`).

**2. Gate C: real.exe on the campaign spec.**

```bash
wrf-gate C LONG_2024 /projects/academic/negarkhodoe/wrf/fires/LONG_2024/specs/campaign
```

It prints the run folder; Slurm emails you when it ends. Then `cat /projects/academic/negarkhodoe/wrf/fires/LONG_2024/runs/<stamp>_gateC_campaign/GATES.txt`.

**3. Gate D: two minutes of wrf.exe.** Gate D on one Sapphire Rapids node: `--constraint SAPPHIRE-RAPIDS-IB`.

```bash
wrf-gate D LONG_2024 /projects/academic/negarkhodoe/wrf/fires/LONG_2024/runs/<stamp>_gateC_campaign --constraint SAPPHIRE-RAPIDS-IB
```

**4. Submit.** 36 ranks on one Sapphire Rapids node; 56 h leaves room for the full window. Check against gate D's rate first.

```bash
wrf-submit LONG_2024 /projects/academic/negarkhodoe/wrf/fires/LONG_2024/specs/campaign --nodes 1 --ranks 36 --time 56:00:00 --constraint SAPPHIRE-RAPIDS-IB --name rerun
```

**5. Watch it, and read how it ended.**

```bash
wrf-watch LONG_2024
cat /projects/academic/negarkhodoe/wrf/fires/LONG_2024/runs/<stamp>_rerun/GATES.txt
```

Gate E runs inside the job when it ends: *finished*, *domain edge*, *crash* or *killed*, plus whether the first burning cell matches the card's ignition time and place.

## Make a variant

Copy the card, change what you are testing (and the `note:` line), and make it. Times and domains unchanged means the existing inputs are reused, so no WPS:

```bash
wrf-card LONG_2024 > /projects/academic/negarkhodoe/wrf/people/$USER/work/long_variant.card
wrf-card --make /projects/academic/negarkhodoe/wrf/people/$USER/work/long_variant.card
```

Then gates C and D and `wrf-submit` on the spec folder it prints, with a `--name` that says what changed. Ideas: [fuel moisture](moisture.html), [one-way coupling](coupling.html), [slope sensitivity](terrain.html#the-slope-effect), [another ignition](ignitions.html).

## Good to know

- **It reaches the domain edge.** In the campaign the fire hit the fire domain's boundary at Jul 16 22:24 and WRF stopped. Gate E classes that ending as *domain edge*, not a crash. To run past it, make a variant card with a larger `fire_cells` (and `outer_cells` if needed), which means new `met_em` files: `wrf-card --make … --wps`.

