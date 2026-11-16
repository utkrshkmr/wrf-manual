---
title: Cranston 2018
kicker: Examples · CRANSTON_2018
lead: A mid-sized fire: 1.0 million column updates per step, a rank cap of 36, and a 20-hour window. One node; its measured run time is the anchor of our walltime rule.
---

## The fire card

Everything that defines this fire, from the campaign. The exact card, with every value read from the shared folder, is one command away:

```bash
wrf-card CRANSTON_2018
```

```text
name:                CRANSTON_2018
start:               2018-07-25 16:00
end:                 2018-07-26 12:00
ignition_time:       (printed by wrf-card)
ignition_lat:        (printed by wrf-card)
ignition_lon:        (printed by wrf-card)
fuel_layer:          /projects/academic/negarkhodoe/wrf/static/landfire/LF2016/FBFM40
base_spec:           CRANSTON_2018/campaign
```

<div class="note" markdown="1">
Values shown as *(printed by wrf-card)* (`ignition_time`, `ignition_lat`, `ignition_lon`) are in the fire's record in the shared folder but not yet on this page.
</div>

Rank cap: **36**.

## Run it from an AI chat

Copy the [skill](skill.html) into a new chat, then paste underneath:

```text
Run this fire. Here is its card:
<paste the output of: wrf-card CRANSTON_2018>
```

The assistant checks the card with you, then walks you through the commands below one at a time.

## Run it with the commands

**1. Check the fire and its inputs.**

```bash
wrf-status CRANSTON_2018
wrf-card CRANSTON_2018
```

Read the card: times, ignition, domains, and under *Measured* the gate A and B results and `fire_fuel_read` (must be `-1`).

**2. Gate C: real.exe on the campaign spec.**

```bash
wrf-gate C CRANSTON_2018 /projects/academic/negarkhodoe/wrf/fires/CRANSTON_2018/specs/campaign
```

It prints the run folder; Slurm emails you when it ends. Then `cat /projects/academic/negarkhodoe/wrf/fires/CRANSTON_2018/runs/<stamp>_gateC_campaign/GATES.txt`.

**3. Gate D: two minutes of wrf.exe.** Gate D on one node with the default ranks.

```bash
wrf-gate D CRANSTON_2018 /projects/academic/negarkhodoe/wrf/fires/CRANSTON_2018/runs/<stamp>_gateC_campaign
```

**4. Submit.** 36 ranks on one node. The full 20-hour run took 41.6 h in the campaign; on Sapphire Rapids it ran at 6.19 s per step, on Cascade Lake at 9.95 s. Ask for 48 h (Cascade Lake) or about 30 h on Sapphire Rapids (`--constraint SAPPHIRE-RAPIDS-IB`) after checking gate D's rate.

```bash
wrf-submit CRANSTON_2018 /projects/academic/negarkhodoe/wrf/fires/CRANSTON_2018/specs/campaign --nodes 1 --ranks 36 --time 48:00:00 --name rerun
```

**5. Watch it, and read how it ended.**

```bash
wrf-watch CRANSTON_2018
cat /projects/academic/negarkhodoe/wrf/fires/CRANSTON_2018/runs/<stamp>_rerun/GATES.txt
```

Gate E runs inside the job when it ends: *finished*, *domain edge*, *crash* or *killed*, plus whether the first burning cell matches the card's ignition time and place.

## Make a variant

Copy the card, change what you are testing (and the `note:` line), and make it. Times and domains unchanged means the existing inputs are reused, so no WPS:

```bash
wrf-card CRANSTON_2018 > /projects/academic/negarkhodoe/wrf/people/$USER/work/cranston_variant.card
wrf-card --make /projects/academic/negarkhodoe/wrf/people/$USER/work/cranston_variant.card
```

Then gates C and D and `wrf-submit` on the spec folder it prints, with a `--name` that says what changed. Ideas: [fuel moisture](moisture.html), [one-way coupling](coupling.html), [slope sensitivity](terrain.html#the-slope-effect), [another ignition](ignitions.html).

## Good to know

- Its fuel map is LANDFIRE **2016**: 98.4% of fire cells match LF2016, under 35% match any later release.
- The fire's `met_em` folders exist in three versions (`CRANSTON`, `CRANSTON/met_files`, `CRANSTON/met_files1`); the registered input version names the one used. Check `wrf-status CRANSTON_2018`.

