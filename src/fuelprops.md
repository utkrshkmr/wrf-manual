---
title: How a fuel type burns
kicker: Advanced · research inputs
lead: Every fuel category has a column of properties in namelist.fire: load, depth, surface-to-volume ratio, moisture of extinction and more. Changing one column changes how that fuel type burns everywhere it occurs, without touching the map.
---

## The parameters

The full list of `&fuel_scalars` and `&fuel_categories` is on the [fire model page](fire.html#namelist-fire). The ones most often changed in experiments:

| Variable | What raising it does |
| --- | --- |
| `fgi` | more dead fuel load: more heat, usually faster spread |
| `fueldepthm` | deeper fuel bed: faster spread, taller flames |
| `savr` | finer fuel particles: dry out and ignite faster |
| `fuelmce` | higher moisture of extinction: keeps burning in wetter conditions |
| `windrf` | more of the reference wind reaches the flames |
| `weight` | longer burn-out time: heat released over longer |

## Change how a fuel type burns

Each column of `&fuel_categories` in `namelist.fire` is one fuel category. To test a different load or depth for, say, Scott and Burgan GR2 (code 102, category 16), change the 16th value of `fgi` or `fueldepthm`. Copy `test/em_fire/namelist.fire.sb40` from the WRF source as the starting point: it already has `nfuelcats = 54` and all 54 columns.

<div class="note" markdown="1">
<span class="callout-title">New fuel types</span>

The code map is fixed in the WRF source: only Anderson codes 1–13 and the 40 Scott and Burgan codes reach a category. A brand-new category (55–60) would never be reached from `NFUEL_CAT` without changing the code. For a custom fuel, repurpose a category you are not using, for example one of the Anderson 1–13 in a LANDFIRE-based run, and write your custom code number for it into the fuel map.
</div>

## As a variant run

1. Copy the fire's spec: `cp -r /projects/academic/negarkhodoe/wrf/fires/FIRE/specs/campaign /projects/academic/negarkhodoe/wrf/people/$USER/work/FIRE_gr2load` (copies are writable; the original stays locked).
2. Edit the copy's `namelist.fire`: change only the columns you mean to, and note them in a `README` beside it.
3. `wrf-gate C FIRE <copy>` then `wrf-gate D FIRE <gate C folder>`; gate C's **C13** checks that `nfuelcats` covers code 204 if the map has it.
4. After the run, compare `namelist.fire.output` in the run folder with the baseline's: it is what WRF actually used.
