---
title: Static data
kicker: WRF mechanics · Phase 2 · geogrid.exe
lead: geogrid puts every static map onto every domain. GEOGRID.TBL decides which dataset feeds which field and how it is interpolated, so any GIS layer can enter the simulation as a new entry plus a folder of tiles.
---

## Running it

```bash
geogrid.exe
tail -1 geogrid.log
ncdump -h geo_em.d02.nc | grep -E 'NFUEL_CAT|ZSF|sr_x'
```

It takes seconds to a minute. Success ends with `Successful completion of program geogrid.exe`. The log also lists, for each field, the folder it actually read: the first place to look when a field is wrong.

## Resolution keys

`geog_data_res` in `namelist.wps` lists keys such as `'ca_1s+lf2024+default'`. Each `GEOGRID.TBL` entry gives a path for some of those keys. For each field, geogrid walks the list left to right and uses the first key the entry has.

{{fig:reskeys|**Key fallback for Canyon's d02.** `NFUEL_CAT` has five keys and picks `lf2024`. `ZSF` and land use only have `default`, so they take that. Changing the fuel release for one domain is a one-word change in `geog_data_res`.}}

## The fire fields

Two `GEOGRID.TBL` entries produce the fields WRF-Fire reads. Both are marked `subgrid=yes`, so geogrid writes them on the fire mesh, `subgrid_ratio` times finer than the atmosphere grid.

```text
name=NFUEL_CAT
    priority=1
    dest_type=categorical
    dominant_only=NFUEL_CAT
    z_dim_name=fuel_cat
    halt_on_missing=no
    fill_missing=0
    interp_option = lf2024:nearest_neighbor
    interp_option = default:nearest_neighbor
    rel_path = lf2024:LF_2024/fbfm40/
    rel_path = default:LF2016_CA_WPS/fbfm40/
    subgrid=yes
===============================
name=ZSF
    priority = 1
    dest_type = continuous
    df_dx=DZDXF
    df_dy=DZDYF
    smooth_option = smth-desmth_special; smooth_passes=1
    halt_on_missing=yes
    interp_option = default:average_gcell(4.0)+four_pt+average_4pt
    rel_path= default:topography/topo_CA_1s_nisha/
    subgrid=yes
===============================
```

- **`NFUEL_CAT`** is the fuel code in each fire cell: the dominant LANDFIRE code there, picked by nearest neighbour.
- **`ZSF`** is fire-mesh terrain height. `df_dx` and `df_dy` make geogrid also write its slopes, `DZDXF` and `DZDYF`, which drive the slope term in the spread rate.
- **Without `ZSF`** the fire sees flat ground: WRF 4.6 no longer fills fire terrain from the atmosphere grid (the `fire_topo_from_atm` code is commented out), and the slopes `DZDXF`/`DZDYF` come only from geogrid. CCR's own `GEOGRID.TBL.FIRE` has no `ZSF` entry, so add one; the lab's `tables/fire/GEOGRID.TBL` has it.

<div class="warn" markdown="1">
<span class="callout-title">A silent failure</span>

With `halt_on_missing=no` and `fill_missing=0`, a wrong fuel path does not stop geogrid. It writes fuel code 0 in every cell, and the fire cannot spread. In Canyon's table, three of the four fuel keys (`lf2016`, `lf2022`, `lf2023`) point at folders that do not exist; only `lf2024` is correct. Set `halt_on_missing=yes` on `NFUEL_CAT`, and check the folder each field read in `geogrid.log`.
</div>

## GEOGRID.TBL keys

| Key | Meaning | Values |
| --- | --- | --- |
| `name` | Output field name | Becomes the netCDF variable in `geo_em` |
| `priority` | Order when several entries share a name | 1 first; a later priority fills only cells still missing |
| `dest_type` | Kind of data | `continuous` (heights, fractions) or `categorical` (classes) |
| `interp_option` | Interpolation, per key | `nearest_neighbor`, `four_pt`, `sixteen_pt`, `average_4pt`, `average_16pt`, `average_gcell(r)`, `search`; `+` joins fallbacks |
| `rel_path`, `abs_path` | Data folder, per key: `key:path/` | `rel_path` is under `geog_data_path`; `abs_path` is a full path |
| `subgrid` | Write on the fire mesh | `yes` for fire fields |
| `fill_missing` | Value where no data covers a cell | A number |
| `halt_on_missing` | Stop if the data is missing | `yes` or `no` |
| `dominant_only`, `dominant` | Categorical data: write only the dominant class, or the fractions plus the dominant class | Output name |
| `z_dim_name` | Name of the category dimension | e.g. `fuel_cat` |
| `df_dx`, `df_dy` | Also write the x and y derivatives under these names | `DZDXF`, `DZDYF` |
| `smooth_option`, `smooth_passes` | Smoothing after interpolation | `1-2-1`, `smth-desmth`, `smth-desmth_special` |
| `masked`, `fill_lev` | Fill only over land or water; fill extra levels | Used by soil and albedo fields |

## Writing your own layer

WPS reads raw binary tiles plus a text file called `index`. Each tile is a plain array of integers, named by the column and row range it covers. Values are stored as integers and multiplied by `scale_factor` when read, which is how fractions and decimals are stored.

{{fig:tiles|**Anatomy of a layer.** Tiles hold integers; `index` says how to place and scale them. This is Canyon's LANDFIRE 2024 fuel layer.}}

| `index` key | Meaning | Fuel (`LF_2024/fbfm40`) | Terrain (`topo_CA_1s_nisha`) |
| --- | --- | --- | --- |
| `type` | `categorical` or `continuous` | `categorical` | `continuous` |
| `category_min`, `category_max` | Range of class codes | 1, 205 | — |
| `projection` | Grid of the data | `albers_nad83` | `regular_ll` |
| `truelat1`, `truelat2`, `stdlon` | Projection parameters | 29.5, 45.5, −96 | — |
| `dx`, `dy` | Cell size: metres if projected, degrees for `regular_ll` | 30, 30 | 1/3600° |
| `known_x`, `known_y`, `known_lat`, `known_lon` | One cell whose position is given | (1, 43366) at 42.0618 N, 125.1993 W | (1, 34200) at 42.0 N, 124.5 W |
| `wordsize`, `signed`, `endian` | Integer format | 2, yes, little | 4, yes, little |
| `scale_factor` | Multiply stored integers by this | 1 | 0.001 (stored in mm) |
| `missing_value` | Stored value meaning no data | 205 | 0 |
| `tile_x`, `tile_y`, `tile_z`, `tile_bdr` | Tile size and halo | 100, 100, 1, 3 | 3600, 3600, 1, 0 |
| `row_order` | First row is south or north | `bottom_top` | `bottom_top` |
| `units`, `description` | Free text | `fuel category` | `meters MSL` |

This Python function writes any 2-D array on a regular latitude–longitude grid as a WPS layer. It was tested by writing and reading back a random field:

```python
import os
import numpy as np

def write_wps_layer(field, out, lat_south, lon_west, dlat, dlon, scale=0.001,
                    kind="continuous", units="fraction", description="custom layer",
                    tile=1000, missing=-9999):
    """field: 2-D array, rows south -> north, columns west -> east, regular lat-lon.
    lat_south, lon_west: centre of the south-west cell."""
    os.makedirs(out, exist_ok=True)
    ny, nx = field.shape
    data = np.where(np.isfinite(field), np.round(field / scale), missing).astype(">i4")
    for j0 in range(0, ny, tile):
        for i0 in range(0, nx, tile):
            t = np.full((tile, tile), missing, dtype=">i4")
            blk = data[j0:j0 + tile, i0:i0 + tile]
            t[:blk.shape[0], :blk.shape[1]] = blk
            t.tofile(f"{out}/{i0+1:05d}-{i0+tile:05d}.{j0+1:05d}-{j0+tile:05d}")
    with open(f"{out}/index", "w") as f:
        f.write(f"type = {kind}\nprojection = regular_ll\n"
                f"dx = {dlon}\ndy = {dlat}\nknown_x = 1.0\nknown_y = 1.0\n"
                f"known_lat = {lat_south}\nknown_lon = {lon_west}\n"
                f"wordsize = 4\nsigned = yes\nendian = big\nrow_order = bottom_top\n"
                f"tile_x = {tile}\ntile_y = {tile}\ntile_z = 1\n"
                f"scale_factor = {scale}\nmissing_value = {missing}\n"
                f'units = "{units}"\ndescription = "{description}"\n')
```

Then add an entry such as:

```text
name = MY_FIELD
    priority = 1
    dest_type = continuous
    interp_option = default:average_gcell(4.0)+four_pt
    abs_path = default:/projects/academic/negarkhodoe/wrf/static/my_field/
    fill_missing = -9999
    subgrid = yes
===============================
```

The field appears in `geo_em` and is carried through to `met_em`. Whether `real.exe` then copies it into `wrfinput` depends on its name: only fields WRF's Registry declares as input are read. A fire-grid field named `FMC_G` or `LFN_HIST` is one WRF knows; see [Fuel moisture](moisture.html) and [Ignitions and perimeters](ignitions.html#start-from-an-observed-perimeter).

## Fuel data for a different area or year

LANDFIRE publishes FBFM40 as GeoTIFFs in its CONUS Albers projection. WPS reads that projection directly (`albers_nad83`), so no resampling is needed: keep the 30 m pixels, write them as tiles, and copy the projection parameters into `index`. For a fire outside an existing layer, either clip a new layer from LANDFIRE's download service or extend the California one. Keep the release in the folder name (`LF2024/`) so every run's manifest shows which fuel map it used.
