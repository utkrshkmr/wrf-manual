---
title: Environment and data
kicker: Phase 0
lead: One module line gives you WPS and WRF built together. Before running anything, you need four datasets on disk, three tables, and one working folder per simulation.
---

## Software

On CCR, one module line loads WPS 4.6 and its matching WRF 4.6. Both are built with gcc 11.2.0, Open MPI 4.1.1 and netCDF 4.8.1:

```bash
module load gcc/11.2.0 openmpi/4.1.1 wps/4.6.0-dmpar
```

That puts `geogrid.exe`, `ungrib.exe`, `metgrid.exe`, `real.exe` and `wrf.exe` on your `PATH`. The tables WPS reads live in the module's install folder:

| What | Where, under `$EBROOTWPS/WPS-4.6.0/` | Notes |
| --- | --- | --- |
| `GEOGRID.TBL` variants | `geogrid/` | `GEOGRID.TBL` is the default. `GEOGRID.TBL.FIRE` has the `NFUEL_CAT` fire entry, but no `ZSF` |
| `METGRID.TBL` | `metgrid/` | The default works for HRRR |
| Vtables | `ungrib/Variable_Tables/` | Has `Vtable.raphrrr`, `GFS`, `NAM`, `ECMWF`, `ERA-interim.pl`. No `Vtable.HRRR.prs`: copy that one from a WPS source tree |
| Utilities | on `PATH` | `g1print.exe`, `g2print.exe` (list a GRIB file's contents), `rd_intermediate.exe` (list an intermediate file), `avg_tsfc.exe`, `mod_levs.exe`, `calc_ecmwf_p.exe` |

<div class="warn" markdown="1">
<span class="callout-title">Two CCR-specific limits</span>

- **Run WPS on one core.** The module is an MPI ("dmpar") build. With 8 ranks, every rank reads each 3.4 GB HRRR intermediate file in full, so Canyon's metgrid was on course for about 4.7 hours. On one core it takes 47 minutes.
- **Keep paths short.** geogrid crashes with `Fortran runtime error: End of record` when it composes an error message about a path longer than roughly 100 characters. A short `geog_data_path` (under 60 characters) avoids it.
</div>

## Data

{{fig:datasets|**Where every input comes from.** All four sources are public. The fuel and fine-terrain layers must be in WPS's own binary tile format; see [Phase 2](geogrid.html#writing-your-own-layer).}}

| Dataset | Used by | Size | Notes |
| --- | --- | --- | --- |
| WPS static geography | geogrid, every domain | 2.6 GB download, 29 GB unpacked | UCAR's `geog_high_res_mandatory.tar.gz`. Already on CCR at `/projects/academic/negarkhodoe/wrf/static/WPS_GEOG` |
| LANDFIRE FBFM40 | geogrid → `NFUEL_CAT` | 2.8 GB per release for California | Scott & Burgan 40 fuel models. Releases on CCR: LF2016, LF2023, LF2024 |
| Fine terrain, 1 arc-second | geogrid → `ZSF` | 5.4 GB for California | Optional but recommended: without it, fire terrain is smoothed atmosphere terrain |
| Weather GRIB2 | ungrib | HRRR about 0.4 GB per hour | Pick the product first: it decides the soil layers and the land-surface model |
| Observed perimeters (optional) | validation, or perimeter initialization | small | NIFC or CAL FIRE FRAP |

## A working folder

A manual run is easiest in one folder per simulation, with everything linked in:

```text
canyon_run/
  namelist.wps          you write it (Phase 1)
  GEOGRID.TBL -> ...    or point opt_geogrid_tbl_path at its folder
  Vtable -> ...Vtable.HRRR.prs
  GRIBFILE.AAA -> ...hrrr.20250807.t18z.wrfprsf00.grib2   (one link per hour)
  geo_em.d01.nc  geo_em.d02.nc          from geogrid
  FILE:2025-08-07_18 ...                from ungrib
  met_em.d01.2025-08-07_18:00:00.nc ... from metgrid
  namelist.input        you write it (Phases 5 and 6)
  namelist.fire         fuel table and moisture model (Phase 6)
  wrfinput_d01 wrfinput_d02 wrfbdy_d01  from real.exe
  wrfout_d0N_* wrfrst_d0N_* rsl.*       from wrf.exe
```

WRF also needs its run-time data tables in the run folder (`RRTMG_LW_DATA`, `GENPARM.TBL`, `LANDUSE.TBL`, `SOILPARM.TBL`, `VEGPARM.TBL`, `CAMtr_volume_mixing_ratio` and others). Link everything from the WRF module's `run/` folder:

```bash
ln -sf $EBROOTWRF/WRF-4.6.0/run/* /path/to/canyon_run/
```

The exact install path can differ; `module show wrf/4.6.0-dmpar` prints it. Then replace the linked `namelist.input` with your own.
