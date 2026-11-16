---
title: The fuel map
kicker: Advanced · research inputs
lead: The fuel map, NFUEL_CAT on the fire mesh, decides what burns where. Use a different LANDFIRE release, cut a fuel break, or mark a treated area, either for every run of a fire or for one run only.
---

## What it does in the model

Each fire cell holds one fuel code. WRF maps the code to a category ([the code map](fire.html#how-fuel-codes-become-categories)), and the category's column in `namelist.fire` gives the load, depth and other properties the spread rate uses. Changing the map changes which column each cell reads.

## Choosing a LANDFIRE release

The shared folder holds several releases, each as WPS tiles: `/projects/academic/negarkhodoe/wrf/static/landfire/<LF2016|LF2022|LF2023|LF2024|LF2025>/FBFM40/`. Match the release to the fire's date: the landscape a fire burned is the one mapped before it. A fire's record names its reference layer (`fuel_layer`), and gate B's **B07 release scan** shows which release an existing input actually matches, cell by cell.

To build inputs with another release, point the fuel entry of `GEOGRID.TBL` at that folder under its own resolution key ([how](geogrid.html#resolution-keys)) and select the key in `geog_data_res`.

## Edit the fuel map

Two ways, depending on whether the change is for one run or for every run of a fire.

- **For every run:** build a new geogrid layer ([how](geogrid.html#writing-your-own-layer)) with the change, give it its own resolution key such as `lf2024_break`, and select it in `geog_data_res`.
- **For one run:** change `NFUEL_CAT` in `wrfinput_d02` after `real.exe`. The script below turns everything inside a polygon into code 99 (non-burnable), a simple fuel break. It uses the same fire-mesh positions as the [perimeter script](ignitions.html#start-from-an-observed-perimeter).

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

## Checking it

- `wrf-add-inputs` runs gate A (**A14** valid codes, **A15** burnable share, **A21** ignition cell burnable) and gate B (**B02** agreement with LANDFIRE). An edited map is meant to disagree with LANDFIRE where you edited it: B02 tells you by how much, and B03 lists which codes changed into which.
- For a one-run edit in `wrfinput_d02`, compare `NFUEL_CAT` before and after with `ncdump` or the script's own output, and keep the edited file's script and polygon beside the spec.
