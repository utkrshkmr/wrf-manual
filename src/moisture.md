---
title: Fuel moisture in depth
kicker: Deep dive
lead: The spread rate reads one field, FMC_G, the dead fuel moisture in each fire cell. By default it is a single number for the whole fire. This page shows every way to make it richer, from a per-cell map to a moisture model driven by the weather, with the exact variables, formats and commands.
---

## What fuel moisture does in the model

Rothermel's spread rate falls steeply as fuel gets wetter, and reaches zero at the fuel's **moisture of extinction** (`fuelmce` in `namelist.fire`: 0.12–0.40 depending on the fuel). In WRF-Fire, the dead fuel moisture of each fire cell, `FMC_G`, enters in three places:

- the **moisture damping** of the reaction intensity, through the ratio `FMC_G / fuelmce`;
- the **heat needed to ignite** the fuel ahead of the front, `250 + 1116 × FMC_G` BTU/lb;
- the **dry fuel load**, `fgi × (1 − FMC_G / (1 + FMC_G))`.

Three more moisture values are scalars only, set in `&fuel_scalars` of `namelist.fire`:

| Variable | Default | What it changes |
| --- | --- | --- |
| `fuelmc_g` | 0.08 | Dead fuel moisture for route A below (fraction: 0.08 = 8%) |
| `fuelmc_g_lh` | 1.20 | Live herbaceous moisture. Between 0.30 and 1.20, part of the live herb load (`fgi_lh`) is treated as dead fuel, as in Scott and Burgan's dynamic fuel models; at 0.30 or below, all of it |
| `fuelmc_c` | 1.00 | Canopy fuel moisture, used by the crown heat release |

## Four routes

{{fig:fmcroutes|**The four routes.** A is the default. B gives a fixed map, cell by cell. C gives moisture per fuel size class on the atmosphere grid, and WRF blends it for each fuel. D computes it from the weather as the run goes.}}

| Route | `&fire` settings | Input | Varies in | Notes |
| --- | --- | --- | --- | --- |
| A. One number | `fire_fmc_read = 1` (default) | `fuelmc_g` in `namelist.fire` | nothing | Overwrites `FMC_G` in every cell at start |
| B. Per-cell map | `fire_fmc_read = 0`, `fmoist_run = .false.`, `fmoist_interp = .false.` | `FMC_G` in `wrfinput_d02`, fire mesh | space | The route for a measured or modelled moisture map |
| C. By size class | `fire_fmc_read = 0`, `fmoist_interp = .true.`, `fmoist_run = .false.` | `FMC_GC` in `wrfinput_d02`: 5 classes on the atmosphere grid | space, by class | Interpolated to fuels once, at the first step |
| D. Moisture model | `fire_fmc_read = 0`, `fmoist_run = .true.`, `fmoist_interp = .true.` | the weather, plus `&fuel_moisture` in `namelist.fire` | space and time | WRF stops if `fmoist_run` is set with `fire_fmc_read ≠ 0` |

`fire_fmc_read = 2` exists but only reads a file in idealized cases.

<div class="warn" markdown="1">
<span class="callout-title">Check routes C and D with LANDFIRE fuels</span>

Reading WRF 4.6's `module_fr_fire_phys.F`: when the class moistures are blended into `FMC_G`, the weight for each cell is looked up as `fmc_gw(n, k)` with `n` = the raw code in `NFUEL_CAT`. That table has 60 rows. Anderson codes (1–13) fit, but LANDFIRE's Scott and Burgan codes (101–204) fall outside it, so the weights read for those cells are undefined. We have not run routes C or D yet. Before relying on them with LANDFIRE fuels, run a short test and compare the `FMC_G` written to `wrfout` with what you expect. Route B avoids the issue entirely.
</div>

## Route B: a per-cell moisture map

This is the route for the research question "what changes when the fire sees a fine-grained moisture field instead of one value". The map is fixed for the whole run; for moisture that changes in time, see route D or split the run at restarts.

**Format.** `FMC_G` is a 2-D float on the fire mesh of the fire domain, as a fraction (0.08 = 8%). Its dimensions in `wrfinput_d02` are `(Time, south_north_subgrid, west_east_subgrid)`: for Canyon, 868 × 868 cells of 25 m.

**Steps.**

1. Run WPS and `real.exe` as usual.
2. Put your moisture map on a regular latitude–longitude grid and save it as `fmc.npz` with three arrays: `fmc` (2-D, rows south to north), `lat` and `lon` (1-D, ascending).
3. Write it into `wrfinput_d02` with the script below. It finds the latitude and longitude of every fire cell from the atmosphere grid, picks the nearest value from your map, checks coverage and range, and writes `FMC_G`.
4. In `namelist.input`, set `fire_fmc_read = 0` on the fire domain, and keep `fmoist_run` and `fmoist_interp` false.
5. Add `FMC_G` to the history output (`iofields_filename`, `+:h:0:FMC_G`) and check the first output time shows your map.

```python
"""Write a per-cell dead fuel moisture map into wrfinput_d02 (FMC_G, fire mesh).
usage: python3 set_fmc_g.py wrfinput_d02 fmc.npz
fmc.npz: fmc (2-D fraction, rows south->north), lat (1-D ascending), lon (1-D ascending)"""
import sys
import numpy as np
from netCDF4 import Dataset
from scipy.interpolate import RegularGridInterpolator

wrfinput, src = sys.argv[1], sys.argv[2]
s = np.load(src)
fmc, lat, lon = s["fmc"], s["lat"], s["lon"]

d = Dataset(wrfinput, "r+")
xlat, xlon = d["XLAT"][0], d["XLONG"][0]
ny, nx = xlat.shape
fny, fnx = d["FMC_G"].shape[-2:]
sr = round(fnx / (nx + 1))
fx = (np.arange(fnx) + 0.5) / sr - 0.5
fy = (np.arange(fny) + 0.5) / sr - 0.5
FY, FX = np.meshgrid(np.clip(fy, 0, ny - 1), np.clip(fx, 0, nx - 1), indexing="ij")
pts = np.stack([FY.ravel(), FX.ravel()], axis=1)
ix = (np.arange(ny), np.arange(nx))
flat = RegularGridInterpolator(ix, xlat)(pts).reshape(fny, fnx)
flon = RegularGridInterpolator(ix, xlon)(pts).reshape(fny, fnx)

pick = RegularGridInterpolator((lat, lon), fmc, method="nearest", bounds_error=False, fill_value=np.nan)
out = pick(np.stack([flat.ravel(), flon.ravel()], axis=1)).reshape(fny, fnx)
if np.isnan(out).any():
    sys.exit(f"{np.isnan(out).sum()} fire cells fall outside the moisture map; extend it")
if out.min() < 0 or out.max() > 2.5:
    sys.exit(f"values {out.min():.3f}..{out.max():.3f} look wrong: FMC_G is a fraction (0.08 = 8%)")
d["FMC_G"][0] = out.astype("f4")
d.close()
print(f"FMC_G set on {fny} x {fnx} fire cells (sr = {sr}): {out.min():.3f} to {out.max():.3f}")
```

We tested the script on a synthetic `wrfinput_d02` with Canyon's dimensions (216 × 216 atmosphere cells, ratio 4) and a north–south moisture gradient; it wrote 868 × 868 values and kept the gradient.

**Through WPS instead.** WRF's Registry lists `FMC_G` as an input field that `real.exe` reads from `met_em` (I/O flags `i102`). So a geogrid layer named `FMC_G` with `subgrid = yes` ([how to write one](geogrid.html#writing-your-own-layer)) should reach `wrfinput_d02` without the post-processing step. We have not tested this route; if you use it, check `FMC_G` in `wrfinput_d02` after `real.exe` with the script on the [real.exe page](real.html#checking-the-fire-fields).

**Good practice for experiments.** Keep everything else identical between the uniform-moisture baseline and the map run: same inputs, same namelists, same node type. Set the baseline's `fuelmc_g` to the map's mean, so the comparison isolates the spatial pattern from the overall wetness.

## Route C: moisture by size class

Fuel is made of particles of different sizes, which dry at different speeds. WRF-Fire tracks five classes, set by `nfmc` (default 5) and `moisture_classes` in `namelist.fire`:

| Class | Name | Drying time lag |
| --- | --- | --- |
| 1 | 1-h | 1 h |
| 2 | 10-h | 10 h |
| 3 | 100-h | 100 h |
| 4 | 1000-h | 1000 h |
| 5 | Live | effectively never (1e9 h) |

`FMC_GC` holds one moisture per class on the **atmosphere** grid: `(Time, south_north, fuel_moisture_classes, west_east)` in `wrfinput_d02`. With `fmoist_interp = .true.`, WRF interpolates each class to the fire mesh at the first step and blends them for each cell's fuel, weighted by that fuel's load in each class (`fgi_1h` … `fgi_live` in `&fuel_categories`). A grass fuel then follows the 1-h moisture almost entirely; a timber litter fuel is dominated by its 10-h and 100-h loads. Write `FMC_GC` into `wrfinput_d02` after `real.exe`, the same way as route B, one 2-D slice per class.

## Route D: the moisture model

With `fmoist_run = .true.`, WRF runs a fuel moisture model on the atmosphere grid. At each moisture step it computes an equilibrium moisture from the 2 m temperature, humidity and surface pressure, or a wetting target when it rains. Each class then moves toward that target with its own time lag.

{{fig:fmclag|**The model's behaviour.** After a sudden drying, 1-h fuels reach the new equilibrium within hours; 100-h fuels have barely moved after two days. The blend for each fuel follows its class loads.}}

**`&fire` switches** (in `namelist.input`):

| Variable | Default | Meaning |
| --- | --- | --- |
| `fmoist_run` | `.false.` | Run the moisture model; needs `fire_fmc_read = 0` |
| `fmoist_interp` | `.false.` | Blend class moistures into `FMC_G` on the fire mesh |
| `fmoist_only` | `.false.` | Run only the moisture model, no fire |
| `fmoist_freq` | 0 | Run the model every this many time steps; 0 = use `fmoist_dt` |
| `fmoist_dt` | 600 s | Moisture model time step |
| `nfmc` | 5 | Number of moisture classes allocated |
| `fmep_decay_tlag` | 999999 | Time constant for decay of assimilated adjustments (`FMEP`) |

**`&fuel_moisture`** (in `namelist.fire`), one value per class; omit the group to use the defaults shown:

| Variable | Default (1-h, 10-h, 100-h, 1000-h, live) | Meaning |
| --- | --- | --- |
| `moisture_classes` | 5 | Classes in use |
| `drying_lag` | 1, 10, 100, 1000, 1e9 h | Time lag toward the drying equilibrium |
| `wetting_lag` | 1.4, 14, 140, 1400, 1e9 h | Time lag toward saturation in rain |
| `saturation_moisture` | 2.5 each | Moisture the class approaches in heavy rain |
| `saturation_rain` | 8 mm/h each | Rain rate above which more rain changes little |
| `rain_threshold` | 0.05 mm/h each | Rain below this counts as none |
| `drying_model`, `wetting_model` | 1 each | Only model 1 (Van Wagner and Pickett) is implemented |
| `fmc_gc_initialization` | 2, 2, 2, 2, 3 | Starting value: 0 = `FMC_GC` from `wrfinput`; 1 = `fuelmc_g`; 2 = the equilibrium; 3 = `fmc_1h` … `fmc_live` |
| `fmc_1h`, `fmc_10h`, `fmc_100h`, `fmc_1000h`, `fmc_live` | 0.08, 0.08, 0.08, 0.08, 0.30 | Starting values when initialization is 3 |

A useful combination: initialize the classes from your own analysis (`fmc_gc_initialization = 0` with `FMC_GC` written into `wrfinput_d02`), then let the model evolve them with the simulated weather. Diagnostic outputs: `FMC_GC` (class moistures), `FMC_EQUI` (equilibrium), `FMC_TEND` (tendency), `FMC_G` (blended, on the fire mesh).

## Which route for which question

| Question | Route |
| --- | --- |
| How sensitive is spread to overall dryness? | A, varying `fuelmc_g` across runs |
| Does a spatial moisture pattern change the fire's path? | B, with A at the map's mean as the baseline |
| Do size-class differences matter for a mixed fuel bed? | C, after the weight check above |
| Does diurnal drying change the spread during the run? | D, after the weight check above |
| Does live herb curing matter? | A or B, varying `fuelmc_g_lh` |
