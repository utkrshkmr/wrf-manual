---
title: Other research inputs
kicker: Deep dive
lead: Beyond fuel moisture, most research changes are one of a few kinds of edit: a different fuel map, different fuel properties, a different starting fire, different terrain, or a change to how the fire talks to the atmosphere. Each has a single, checkable place to make it.
---

## The menu

| You want to change | Edit | Where | Kind of change |
| --- | --- | --- | --- |
| The fuel map (another release, a fuel break, a treated area) | `NFUEL_CAT` | geogrid layer, or `wrfinput_d02` after `real.exe` | Map |
| How a fuel type burns | a column in `&fuel_categories` | `namelist.fire` | Table |
| Fuel moisture | `FMC_G`, `FMC_GC`, `fuelmc_*`, the moisture model | [Fuel moisture](moisture.html) | Map, table or model |
| Where and when the fire starts | `fire_ignition_*` (up to 5 lines) | `&fire` | Namelist |
| Start from an observed perimeter | `LFN_HIST`, `fire_is_real_perim` | `wrfinput_d02` + `&fire` | Map |
| Fine terrain under the fire | `ZSF` and `fire_topo_from_atm = 0` | geogrid layer + `&fire` | Map |
| Strength of the slope effect | `fire_slope_factor` | `&fire` | Namelist |
| Which wind drives the spread | `fire_wind_height`, `fire_lsm_zcoupling` | `&fire` | Namelist |
| Fire–atmosphere feedback | `fire_atm_feedback`, `fire_ext_grnd`, `fire_sfc_flx` | `&fire` | Namelist |
| A prescribed heat source | `fire_const_time`, `fire_const_grnhfx`, `fire_const_grnqfx` | `&fire` | Namelist |
| Spotting | `fs_*` | `&fire` | Namelist |
| Weather (another product, a perturbed field) | GRIB or intermediate files | [Phase 3](ungrib.html) | Data |
| Extra output fields | `iofields_filename` | `&time_control` | Output |

## Edit the fuel map

Two ways, depending on whether the change is for one run or for every run of a fire.

- **For every run:** build a new geogrid layer ([how](geogrid.html#writing-your-own-layer)) with the change, give it its own resolution key such as `lf2024_break`, and select it in `geog_data_res`.
- **For one run:** change `NFUEL_CAT` in `wrfinput_d02` after `real.exe`. The script below turns everything inside a polygon into code 99 (non-burnable), a simple fuel break. It uses the same fire-mesh positions as the perimeter script further down.

```python
"""Make a polygon non-burnable: usage python3 fuel_break.py wrfinput_d02 polygon.csv [code]"""
import sys
import numpy as np
from netCDF4 import Dataset
from matplotlib.path import Path
from scipy.interpolate import RegularGridInterpolator

wrfinput, csv = sys.argv[1], sys.argv[2]
code = int(sys.argv[3]) if len(sys.argv) > 3 else 99
d = Dataset(wrfinput, "r+")
xlat, xlon = d["XLAT"][0], d["XLONG"][0]
ny, nx = xlat.shape
fny, fnx = d["NFUEL_CAT"].shape[-2:]
sr = round(fnx / (nx + 1))
FY, FX = np.meshgrid(np.clip((np.arange(fny) + 0.5) / sr - 0.5, 0, ny - 1),
                     np.clip((np.arange(fnx) + 0.5) / sr - 0.5, 0, nx - 1), indexing="ij")
pts = np.stack([FY.ravel(), FX.ravel()], axis=1)
ix = (np.arange(ny), np.arange(nx))
lon = RegularGridInterpolator(ix, xlon)(pts)
lat = RegularGridInterpolator(ix, xlat)(pts)
inside = Path(np.loadtxt(csv, delimiter=",")).contains_points(np.stack([lon, lat], 1)).reshape(fny, fnx)
f = d["NFUEL_CAT"][0]
f[inside] = code
d["NFUEL_CAT"][0] = f
d.close()
print(f"{inside.sum()} fire cells set to code {code}")
```

Any code WRF maps to category 14 is "no fuel" ([the code map](fire.html#how-fuel-codes-become-categories)): the non-burnable LANDFIRE codes 91–99 all are.

## Change how a fuel type burns

Each column of `&fuel_categories` in `namelist.fire` is one fuel category. To test a different load or depth for, say, Scott and Burgan GR2 (code 102, category 16), change the 16th value of `fgi` or `fueldepthm`. Copy `test/em_fire/namelist.fire.sb40` from the WRF source as the starting point: it already has `nfuelcats = 54` and all 54 columns.

<div class="note" markdown="1">
<span class="callout-title">New fuel types</span>

The code map is fixed in the WRF source: only Anderson codes 1–13 and the 40 Scott and Burgan codes reach a category. A brand-new category (55–60) would never be reached from `NFUEL_CAT` without changing the code. For a custom fuel, repurpose a category you are not using, for example one of the Anderson 1–13 in a LANDFIRE-based run, and write your custom code number for it into the fuel map.
</div>

## Start from an observed perimeter

Instead of a point or line ignition, the fire can start from a mapped perimeter, for example a satellite or aircraft perimeter at a known time. WRF reads it as a level-set field, `LFN_HIST`, on the fire mesh.

{{fig:perimeter|**Perimeter initialization.** The perimeter becomes a signed distance field. At the first ignition's start time, WRF replaces its fire front with that field and spreads outward from it.}}

Steps:

1. Run WPS and `real.exe` as usual. Set `fire_num_ignitions = 1` and `fire_ignition_start_time1` to the perimeter's time, in seconds from the run start.
2. Write `LFN_HIST` with the script below, from a `lon,lat` vertex list.
3. Set `fire_is_real_perim = .true.` on the fire domain.

```python
"""Write an observed perimeter into wrfinput_d02 as LFN_HIST.
usage: python3 set_perimeter.py wrfinput_d02 perimeter.csv   (one 'lon,lat' per line)"""
import sys
import numpy as np
from netCDF4 import Dataset
from matplotlib.path import Path
from scipy.interpolate import RegularGridInterpolator
from scipy.ndimage import distance_transform_edt

wrfinput, csv = sys.argv[1], sys.argv[2]
poly = np.loadtxt(csv, delimiter=",")
d = Dataset(wrfinput, "r+")
xlat, xlon = d["XLAT"][0], d["XLONG"][0]
ny, nx = xlat.shape
fny, fnx = d["LFN_HIST"].shape[-2:]
sr = round(fnx / (nx + 1))
FY, FX = np.meshgrid(np.clip((np.arange(fny) + 0.5) / sr - 0.5, 0, ny - 1),
                     np.clip((np.arange(fnx) + 0.5) / sr - 0.5, 0, nx - 1), indexing="ij")
pts = np.stack([FY.ravel(), FX.ravel()], axis=1)
ix = (np.arange(ny), np.arange(nx))
flat = RegularGridInterpolator(ix, xlat)(pts)
flon = RegularGridInterpolator(ix, xlon)(pts)
inside = Path(poly).contains_points(np.stack([flon, flat], axis=1)).reshape(fny, fnx)
if not inside.any():
    sys.exit("no fire cell is inside the perimeter: check lon,lat order and the domain")
dx = float(d.getncattr("DX")) / sr if "DX" in d.ncattrs() else 25.0
lfn = (distance_transform_edt(~inside) - distance_transform_edt(inside)) * dx
d["LFN_HIST"][0] = lfn.astype("f4")
d.close()
print(f"perimeter covers {inside.sum()} fire cells ({inside.sum() * dx * dx / 1e4:.1f} ha)")
```

Tested on a synthetic `wrfinput_d02` with Canyon's dimensions: a 0.05° × 0.03° box gave 1,505 ha, as expected. Like `FMC_G`, `LFN_HIST` is an input field `real.exe` reads from `met_em`, so a geogrid layer of that name is an untested alternative.

## Fine terrain

Fire spread depends strongly on slope, and a 100 m atmosphere grid smooths ridges. Supply `ZSF` from a 30 m elevation layer ([Phase 2](geogrid.html#the-fire-fields)) and set `fire_topo_from_atm = 0`, or WRF overwrites it with smoothed atmosphere terrain. `fire_slope_factor` scales the slope effect, for sensitivity tests.

## Ignitions

Up to five ignition lines, each with its own position, time window, radius and drawing speed ([Phase 6](fire.html#ignition)). Useful variants: several spot ignitions to mimic spotting, a long line for a firing operation, or a delayed second ignition.

## The fire–atmosphere coupling

| Experiment | Settings |
| --- | --- |
| One-way coupling (the fire doesn't change the weather) | `fire_atm_feedback = 0` |
| Stronger or weaker coupling | `fire_atm_feedback` between 0 and 1, or above |
| Heat released lower or higher | `fire_ext_grnd` (default 50 m), or `fire_sfc_flx = 1` with `fire_heat_peak` |
| A prescribed, constant heat source | `fire_const_time` (when to freeze), `fire_const_grnhfx`, `fire_const_grnqfx` |
| Wind for the spread taken higher up | `fire_lsm_zcoupling = .true.`, `fire_lsm_zcoupling_ref = 50` |

## Output for analysis

`iofields_filename = 'fire_out.txt', 'fire_out.txt'` in `&time_control`, with a file such as:

```text
+:h:0:FIRE_AREA,TIGN_G,ROS,FGRNHFX,FGRNQFX,FMC_G,FLAME_LENGTH,ROS_FRONT,UF,VF,LFN
```

adds those fields to the history output of each domain. `-:h:0:` removes fields, which helps when the fire domain's output is large.
