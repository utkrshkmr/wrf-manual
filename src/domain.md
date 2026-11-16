---
title: Domain design
kicker: Phase 1 · namelist.wps
lead: namelist.wps fixes the geometry for everything that follows. The domains, dates and fire-grid ratio written here are repeated exactly in namelist.input, so decide them once and copy them.
---

## Canyon's namelist.wps

```fortran
&share
 wrf_core = 'ARW', max_dom = 2,
 start_date = '2025-08-07_18:00:00','2025-08-07_18:00:00',
 end_date   = '2025-08-09_00:00:00','2025-08-09_00:00:00',
 interval_seconds = 3600, io_form_geogrid = 2,
 subgrid_ratio_x = 0, 4, subgrid_ratio_y = 0, 4,
/
&geogrid
 parent_id = 1, 1,  parent_grid_ratio = 1, 9,
 i_parent_start = 1, 15,  j_parent_start = 1, 15,
 e_we = 54, 217,  e_sn = 54, 217,
 geog_data_res = 'lf2024+default', 'ca_1s+lf2024+default',
 dx = 900, dy = 900, map_proj = 'lambert',
 ref_lat = 34.46681, ref_lon = -118.70165,
 truelat1 = 34.46681, truelat2 = 34.46681, stand_lon = -118.70165,
 geog_data_path = '/projects/academic/negarkhodoe/wrf/static/WPS_GEOG/',
 opt_geogrid_tbl_path = '/projects/academic/negarkhodoe/wrf/tables/fire/'
/
&ungrib
 out_format = 'WPS', prefix = 'FILE',
/
&metgrid
 fg_name = 'FILE', io_form_metgrid = 2,
/
```

Values with one entry per domain are comma-separated lists, d01 first.

{{fig:nesting|**What those numbers mean on the ground.** d02 sits 14 parent cells in from d01's lower-left corner and covers 24 parent cells, each split 9 × 9. Each 100 m d02 cell is split again 4 × 4 for the fire, so a fire cell (25 m) is about the size of one LANDFIRE pixel (30 m).}}

## &share

| Variable | Meaning | Values and rules |
| --- | --- | --- |
| `wrf_core` | Dynamical core | `'ARW'` |
| `max_dom` | Number of domains | The fire runs on the innermost |
| `start_date`, `end_date` | First and last weather time, per domain | `'YYYY-MM-DD_HH:MM:SS'`. Nests may start later than d01 |
| `interval_seconds` | Spacing of weather times | Must match the GRIB files: 3600 for hourly HRRR, 10800 for 3-hourly NAM or GFS |
| `io_form_geogrid` | geogrid output format | 2 = netCDF |
| `subgrid_ratio_x`, `subgrid_ratio_y` | Fire-mesh refinement per domain | 0 or 1 = no fire mesh. 4 = each atmosphere cell split 4 × 4. Must equal `sr_x`, `sr_y` in `namelist.input`. These go in `&share`, not `&geogrid`: in `&geogrid` they cause `Bad data for namelist object e_sn` |
| `opt_output_from_geogrid_path` | Where `geo_em` files go | Default `./` |
| `active_grid` | Process this domain or not | `.true.` per domain |
| `debug_level` | Log detail | 0 |

## &geogrid

| Variable | Meaning | Values and rules |
| --- | --- | --- |
| `parent_id` | Which domain each nest sits in | d01's own entry is 1 |
| `parent_grid_ratio` | Nest cell size = parent's ÷ this | Odd ratios (3, 5, 9) keep nest and parent cell centres aligned. Canyon: 9 |
| `i_parent_start`, `j_parent_start` | Nest's lower-left corner, in parent cell indices | Counted from 1 |
| `e_we`, `e_sn` | Domain size in grid points (staggered, so cells + 1) | For a nest, `e_we − 1` must divide by `parent_grid_ratio`: 216 ÷ 9 = 24 |
| `dx`, `dy` | d01 cell size | Metres for Lambert, Mercator and polar; nests get `dx ÷ ratio` automatically |
| `map_proj` | Projection | `'lambert'` for mid-latitudes, `'mercator'` near the equator, `'polar'`, `'lat-lon'` |
| `ref_lat`, `ref_lon` | Domain centre | Degrees. `ref_x`, `ref_y` can move the reference point off-centre |
| `truelat1`, `truelat2`, `stand_lon` | Lambert parameters | For a small domain, setting both true latitudes to the centre minimises distortion |
| `geog_data_res` | Which resolution keys to try in `GEOGRID.TBL` | Keys joined by `+`, tried left to right: see [Phase 2](geogrid.html#resolution-keys) |
| `geog_data_path` | Root folder for every `rel_path` in the table | Ends in `/`. Keep it short |
| `opt_geogrid_tbl_path` | Folder containing `GEOGRID.TBL` | Default `./geogrid/` |

## &ungrib and &metgrid

| Variable | Meaning | Values and rules |
| --- | --- | --- |
| `out_format` | Intermediate file format | `'WPS'` |
| `prefix` | Intermediate file name | `'FILE'` gives `FILE:2025-08-07_18` |
| `fg_name` | Which intermediate sets metgrid reads | A list: `'FILE', 'SST'` merges two sources; later entries win for the same field |
| `constants_name` | Intermediate files with fields that never change in time | Read once and applied to every time: a route for your own static field |
| `io_form_metgrid` | metgrid output format | 2 = netCDF |
| `opt_metgrid_tbl_path` | Folder containing `METGRID.TBL` | Default `./metgrid/` |
| `process_only_bdy` | Only process boundary rows after the first time | Saves time on big outer domains |

## Designing a fire domain

1. **Start from the fire.** Centre d01 on the fire's centroid and set the true latitudes to it.
2. **Size the fire domain for the whole run.** When the fire comes within `fire_boundary_guard` cells (default 8) of the fire domain's edge, WRF stops with a fatal error. The Long fire ended that way at 22:24 on July 16, on every node type.
3. **Match the fire mesh to the fuel data.** LANDFIRE is 30 m, so a 25–30 m fire cell sees about one fuel pixel. Canyon: 100 m ÷ 4 = 25 m.
4. **Mind the decomposition cap.** WRF needs at least 10 grid points per MPI rank in each direction on every domain. Canyon's 54-point d01 allows only 5 × 5 = 25 ranks, whatever the size of d02. A larger d01 raises the cap; see [Running it](run.html#how-many-ranks).
5. **Check the nest rule.** `(e_we − 1)` and `(e_sn − 1)` must be multiples of `parent_grid_ratio`.
