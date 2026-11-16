---
title: Ignitions and perimeters
kicker: Advanced · research inputs
lead: How the fire starts is often the largest single uncertainty in a hindcast. Start it from points, lines, several staggered ignitions, or from an observed perimeter at a known time.
---

## Ignitions

Up to five ignition lines, each with its own position, time window, radius and drawing speed ([Phase 6](fire.html#ignition)). Useful variants: several spot ignitions to mimic spotting, a long line for a firing operation, or a delayed second ignition.

The variables are on the [fire model page](fire.html#ignition). Two staggered point ignitions, for example:

```text
 fire_num_ignitions        = 2, 2,
 fire_ignition_start_lat1  = 0, 34.4710,   fire_ignition_end_lat1 = 0, 34.4710,
 fire_ignition_start_lon1  = 0, -118.7000, fire_ignition_end_lon1 = 0, -118.7000,
 fire_ignition_start_time1 = 0, 3600,      fire_ignition_end_time1 = 0, 3660,
 fire_ignition_radius1     = 0, 50,
 fire_ignition_start_lat2  = 0, 34.4800,   fire_ignition_end_lat2 = 0, 34.4800,
 fire_ignition_start_lon2  = 0, -118.6900, fire_ignition_end_lon2 = 0, -118.6900,
 fire_ignition_start_time2 = 0, 5400,      fire_ignition_end_time2 = 0, 5460,
 fire_ignition_radius2     = 0, 50,
```

Times are seconds from the run's start: work them out from the clock times (ignition − start), never by hand-guessing. The fire's record holds the first ignition; gate C checks **C11** (time) and **C12** (place) against it, and gate E checks that the first burning cell matches (**E05**, **E06**). A deliberately different ignition is a different experiment: make a new record for it with `wrf-new-fire FIRE_VARIANT …` rather than editing the original.

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
