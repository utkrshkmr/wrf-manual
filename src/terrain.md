---
title: Terrain and slope
kicker: Advanced · research inputs
lead: Slope can change the spread rate several-fold. How this setup defines terrain for the atmosphere and for the fire, how to check it, and how to test the slope effect.
---

## How the terrain is defined

The model uses two terrains, both made by geogrid:

| | Atmosphere terrain | Fire terrain |
| --- | --- | --- |
| Field | `HGT_M` on each domain (100 m on the fire domain, 900 m outside) | `ZSF` on the fire mesh (25 m), plus its slopes `DZDXF`, `DZDYF` |
| Source | WPS's standard terrain in `static/WPS_GEOG`, through the table's `default` entry | `static/elevation/CA_1s`: 1 arc-second (about 30 m) California elevation, name `ca_1s` |
| How geogrid samples it | the standard averaging of the `HGT_M` entry | `average_gcell(4.0)+four_pt+average_4pt`, then one smoothing pass (`smth-desmth_special`); slopes from the smoothed heights |
| Used for | winds, pressure, everything in the atmosphere | the slope term in the fire's spread rate (`DZDXF`, `DZDYF`); `ZSF` for fuel by altitude |

`namelist.wps` selects the fire terrain for the fire domain with `geog_data_res = '…', 'ca_1s+lf2024+default'`; a fire card sets this from its `terrain_layer` line. real.exe copies `ZSF`, `DZDXF` and `DZDYF` into `wrfinput_d02` unchanged.

**WRF 4.6 does not fill fire terrain from the atmosphere.** The `fire_topo_from_atm` option is still read, but the code that used it is commented out (`phys/module_fr_fire_driver.F`). So the fire always uses `ZSF` and its slopes from the inputs, and inputs without `ZSF` give a fire on flat ground. At start-up wrf.exe prints `max gradient … max error against zsf …` in `rsl.error.0000`: the steepest slope it sees.

The layer `CA_1s` is the 1 arc-second elevation used for the NCAR and campaign inputs (`topo_CA_1s_nisha` in their table): integer tiles in millimetres (`scale_factor = 0.001`, `wordsize = 4`) on a regular latitude–longitude grid.

## Checking it

- Gate A: **A13** (`ZSF` filled; fails without it), **A17** (heights plausible), **A18** (fine terrain agrees, on average, with the atmosphere's).
- Gate B: **B09** compares `ZSF` with the elevation layer itself: a large RMSE means a misplaced or wrong layer.
- Gate C: **C10** (the inputs have `ZSF`) and **C16** (`wrfinput_d02` has real heights and non-zero slopes).
- Gate D: **D04** reads the `max gradient` line wrf.exe printed: zero means flat.
- `wrf-static --check` runs geogrid with each terrain name and compares `ZSF` with the atmosphere terrain over the same area.

## The slope effect

`fire_slope_factor` multiplies the slope term in the spread rate (default 1). A sensitivity test is three variant specs with 0.5, 1 and 1.5, identical otherwise, each through gates C and D. To see how much the fine terrain itself matters, `fire_slope_factor = 0` removes the slope effect entirely (in WRF 4.6, `fire_topo_from_atm` no longer switches the terrain source).
