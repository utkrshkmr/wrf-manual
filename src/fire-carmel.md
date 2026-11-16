---
title: Carmel
kicker: Examples · CARMEL
lead: NCAR `met_em` files only; not yet run on CCR. Its card starts from the inputs and a base spec.
---

## The fire card

Everything that defines this fire, from the NCAR `met_em` files. The exact card, with every value read from the shared folder, is one command away:

```bash
wrf-card CARMEL
```

```text
name:                CARMEL
start:               (printed by wrf-card)
end:                 (printed by wrf-card)
ignition_time:       (printed by wrf-card)
ignition_lat:        (printed by wrf-card)
ignition_lon:        (printed by wrf-card)
base_spec:           CANYON_2025/campaign
```

<div class="note" markdown="1">
Values shown as *(printed by wrf-card)* (`start`, `end`, `ignition_time`, `ignition_lat`, `ignition_lon`) are in the fire's record in the shared folder but not yet on this page.
</div>

## Run it from an AI chat

Copy the [skill](skill.html) into a new chat, then paste underneath:

```text
Run this fire. Here is its card:
<paste the output of: wrf-card CARMEL>
```

The assistant checks the card with you, then walks you through the commands below one at a time.

## Run it with the commands

**1. Check the fire and its inputs.**

```bash
wrf-status CARMEL
wrf-card CARMEL
```

Read the card: times, ignition, domains, and under *Measured* the gate A and B results and `fire_fuel_read` (must be `-1`).

**2. Make its spec from a card.** These fires have inputs but no spec of their own yet. Print the card, fill in what is missing from the record and the inputs, keep `base_spec: CANYON_2025/campaign` for the lab's physics, and make the spec without rerunning WPS:

```bash
wrf-card CARMEL > /projects/academic/negarkhodoe/wrf/people/$USER/work/carmel.card
wrf-card --make /projects/academic/negarkhodoe/wrf/people/$USER/work/carmel.card
```

It prints the spec folder (`people/$USER/work/CARMEL_<time>/spec`). Its domain sizes and grid spacing must match the `met_em` files; gate C checks them.

**3. Gate C (real.exe), then gate D (2-minute smoke run).**

```bash
wrf-gate C CARMEL /projects/academic/negarkhodoe/wrf/people/$USER/work/CARMEL_<time>/spec
wrf-gate D CARMEL /projects/academic/negarkhodoe/wrf/fires/CARMEL/runs/<stamp>_gateC_spec
```

**4. Size and submit.** The rank cap is in gate C's `GATES.txt` (`C15`). Use one whole node at the cap if it is under 64, and set the walltime from gate D's seconds per step ([how](run.html)):

```bash
wrf-submit CARMEL /projects/academic/negarkhodoe/wrf/people/$USER/work/CARMEL_<time>/spec --nodes 1 --ranks <cap> --time <HH:MM:SS>
```

**5. Watch it, and read how it ended.**

```bash
wrf-watch CARMEL
cat /projects/academic/negarkhodoe/wrf/fires/CARMEL/runs/<stamp>_rerun/GATES.txt
```

Gate E runs inside the job when it ends: *finished*, *domain edge*, *crash* or *killed*, plus whether the first burning cell matches the card's ignition time and place.

## Make a variant

Copy the card, change what you are testing (and the `note:` line), and make it. Times and domains unchanged means the existing inputs are reused, so no WPS:

```bash
wrf-card CARMEL > /projects/academic/negarkhodoe/wrf/people/$USER/work/carmel_variant.card
wrf-card --make /projects/academic/negarkhodoe/wrf/people/$USER/work/carmel_variant.card
```

Then gates C and D and `wrf-submit` on the spec folder it prints, with a `--name` that says what changed. Ideas: [fuel moisture](moisture.html), [one-way coupling](coupling.html), [slope sensitivity](terrain.html#the-slope-effect), [another ignition](ignitions.html).

## Good to know

- **Its fuel map matches none of our LANDFIRE releases** (best: LF2016 at 66%). The release between 2016 and 2022 that we do not have (LF 2019 or 2020) is the likely source; gate B fails until that layer is added or the inputs are remade from a card.

