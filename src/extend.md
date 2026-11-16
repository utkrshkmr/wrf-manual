---
title: Research inputs: where each change goes
kicker: Advanced · research inputs
lead: Most research questions come down to one of a few kinds of change: the fuel map, how a fuel burns, its moisture, how the fire starts, the terrain under it, or how it talks to the atmosphere. Each has its own page; this one is the map.
---

## The menu

| You want to change | Edit | Where | Kind of change |
| --- | --- | --- | --- |
| [The fuel map (another release, a fuel break, a treated area)](fuelmap.html) | `NFUEL_CAT` | geogrid layer, or `wrfinput_d02` after `real.exe` | Map |
| [How a fuel type burns](fuelprops.html) | a column in `&fuel_categories` | `namelist.fire` | Table |
| [Fuel moisture](moisture.html) | `FMC_G`, `FMC_GC`, `fuelmc_*`, the moisture model | [Fuel moisture](moisture.html) | Map, table or model |
| [Where and when the fire starts](ignitions.html) | `fire_ignition_*` (up to 5 lines) | `&fire` | Namelist |
| [Start from an observed perimeter](ignitions.html#start-from-an-observed-perimeter) | `LFN_HIST`, `fire_is_real_perim` | `wrfinput_d02` + `&fire` | Map |
| [Fine terrain under the fire](terrain.html) | `ZSF` and `fire_topo_from_atm = 0` | geogrid layer + `&fire` | Map |
| [Strength of the slope effect](terrain.html#the-slope-effect) | `fire_slope_factor` | `&fire` | Namelist |
| [Which wind drives the spread](coupling.html#which-wind-drives-the-spread) | `fire_wind_height`, `fire_lsm_zcoupling` | `&fire` | Namelist |
| [Fire–atmosphere feedback](coupling.html) | `fire_atm_feedback`, `fire_ext_grnd`, `fire_sfc_flx` | `&fire` | Namelist |
| [A prescribed heat source](coupling.html#a-prescribed-heat-source) | `fire_const_time`, `fire_const_grnhfx`, `fire_const_grnqfx` | `&fire` | Namelist |
| Spotting | `fs_*` | `&fire` | Namelist |
| Weather (another product, a perturbed field) | GRIB or intermediate files | [Phase 3](ungrib.html) | Data |
| Extra output fields | `iofields_filename` | `&time_control` | Output |

## How a change becomes a run

Every change ends up in one of two places, and that decides what you do next with the [gating system](gates.html):

- **A change to the inputs** (a new fuel map, terrain, a moisture map, a perimeter written into a file): register it as a new input version with `wrf-add-inputs`, so gates A and B check it and the old version stays untouched.
- **A change to the namelists** (`&fire` options, `namelist.fire` columns): copy the fire's spec to a new folder, edit the copy, and run gates C and D on it before `wrf-submit`.

Either way the run's manifest records exactly which inputs and which namelists it used, so a variant can never be mistaken for the baseline.

## Output for analysis

`iofields_filename = 'fire_out.txt', 'fire_out.txt'` in `&time_control`, with a file such as:

```text
+:h:0:FIRE_AREA,TIGN_G,ROS,FGRNHFX,FGRNQFX,FMC_G,FLAME_LENGTH,ROS_FRONT,UF,VF,LFN
```

adds those fields to the history output of each domain. `-:h:0:` removes fields, which helps when the fire domain's output is large.
