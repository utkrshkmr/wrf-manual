---
title: Terrain and slope
kicker: Advanced · research inputs
lead: Slope can change the spread rate several-fold, and a 100 m atmosphere grid flattens ridges and canyons. Give the fire model its own fine terrain, and test how much the result depends on slope.
---

## Fine terrain

Fire spread depends strongly on slope, and a 100 m atmosphere grid smooths ridges. Supply `ZSF` from a 30 m elevation layer ([Phase 2](geogrid.html#the-fire-fields)) and set `fire_topo_from_atm = 0`, or WRF overwrites it with smoothed atmosphere terrain. `fire_slope_factor` scales the slope effect, for sensitivity tests.

In the shared folder, the 1-arc-second (about 30 m) California elevation layer is `/projects/academic/negarkhodoe/wrf/static/CA_1s/`. [Phase 2](geogrid.html#the-fire-fields) shows the `ZSF` entry of `GEOGRID.TBL` that reads it.

## Checking it

- Gate A: **A13** (`ZSF` filled), **A17** (heights plausible), **A18** (fine terrain agrees, on average, with the atmosphere's).
- Gate B: **B09** compares `ZSF` with the elevation layer itself: a large RMSE means a misplaced or wrong layer.
- Gate C: **C10** checks `fire_topo_from_atm = 0` when `ZSF` is present, so the fine terrain is not silently replaced.

## The slope effect

`fire_slope_factor` multiplies the slope term in the spread rate (default 1). A sensitivity test is three variant specs with 0.5, 1 and 1.5, identical otherwise, each through gates C and D. With `fire_topo_from_atm = 1` instead, the fire runs on the smoothed atmosphere terrain: a quick way to see how much the fine terrain itself matters.
