---
title: Reference and failures
kicker: WRF mechanics · Look-up
lead: Every file in the chain, the handful of settings that must agree, and every failure we have met so far with its cause and fix.
---

## Files

| File | Written by | Read by | Holds |
| --- | --- | --- | --- |
| `namelist.wps` | you | geogrid, ungrib, metgrid | domains, dates, data and table paths |
| `GEOGRID.TBL` | you (from WPS) | geogrid | which dataset feeds which field |
| `index` + tiles | you or a converter | geogrid | one static layer |
| `Vtable` | WPS | ungrib | GRIB code → field name |
| `geo_em.d0N.nc` | geogrid | metgrid | static fields, incl. `NFUEL_CAT`, `ZSF` |
| `FILE:YYYY-MM-DD_HH` | ungrib | metgrid | weather, one time |
| `METGRID.TBL` | WPS | metgrid | interpolation per field |
| `met_em.d0N.<time>.nc` | metgrid | real.exe | everything for one domain and time |
| `namelist.input` | you | real.exe, wrf.exe | run, domains, physics, `&fire` |
| `namelist.fire` | you (from WRF's `test/em_fire`) | wrf.exe | fuel table, scalar moistures, moisture model |
| `wrfinput_d0N` | real.exe (you may edit) | wrf.exe | initial state, fire fields |
| `wrfbdy_d01` | real.exe | wrf.exe | lateral boundaries |
| `wrfout_d0N_<time>` | wrf.exe | you | history output |
| `wrfrst_d0N_<time>` | wrf.exe | wrf.exe (restart) | full state for resuming |
| `rsl.out.*`, `rsl.error.*` | real.exe, wrf.exe | you | one log per MPI rank |
| `namelist.fire.output` | wrf.exe | you | fuel values actually used |

## Settings that must agree

| Setting | In `namelist.wps` | In `namelist.input` |
| --- | --- | --- |
| Domain count and sizes | `max_dom`, `e_we`, `e_sn` | the same |
| Nesting | `parent_id`, `parent_grid_ratio`, `i_parent_start`, `j_parent_start` | the same |
| Grid spacing | `dx`, `dy` for d01 | `dx`, `dy` for every domain |
| Fire-mesh ratio | `subgrid_ratio_x`, `subgrid_ratio_y` (in `&share`) | `sr_x`, `sr_y` |
| Weather spacing | `interval_seconds` | `interval_seconds` |
| Levels | (from the data) | `num_metgrid_levels`, `num_metgrid_soil_levels` |
| Soil and land surface | (HRRR: 9 soil levels) | `num_soil_layers`, `sf_surface_physics` |

## Failure modes

Every one of these happened to us, except where noted.

| Symptom | Cause | Fix |
| --- | --- | --- |
| `Fortran runtime error: End of record` in `source_data_module.f90`, geogrid | A data path over about 100 characters, met while composing an error message | Short `geog_data_path` (under 60 characters) |
| `Bad data for namelist object e_sn`, geogrid | `subgrid_ratio_x` put in `&geogrid` | It belongs in `&share` |
| geogrid succeeds but no `NFUEL_CAT` | Default `GEOGRID.TBL` has no fire entries, or `subgrid_ratio` is 0 | Use a fire table; set the ratio in `&share` |
| `Could not open …/landfire_data/index` | `GEOGRID.TBL.FIRE` expects a fuel folder that isn't there | Point `rel_path`/`abs_path` at your fuel layer |
| `NFUEL_CAT` all 0, no spread (risk, not yet hit) | Wrong fuel path with `halt_on_missing=no`, `fill_missing=0` | `halt_on_missing=yes`; read the paths in `geogrid.log` |
| `fuel category out of bounds`, wrf.exe | Code 204 (SB4) with the built-in 53 categories | `namelist.fire` with `nfuelcats = 54` |
| `Connection refused` from `srun` | MPI-built WPS program started bare in an `srun` step | Run it with `srun -n 1` inside a batch job, or on a login node |
| metgrid hits a 2-hour limit | 8 MPI ranks each reading every 3.4 GB HRRR file | One core: 47 minutes for Canyon |
| Job ends with exit 137 mid-run | `reached domain boundary`: WRF-Fire called MPI_Abort | Not a crash. Enlarge or move the fire domain |
| Two jobs writing the same run folder | A hand submission next to a scripted one | One lock file per run folder |
| Continuation jobs start after the run finished | Continuations queued ahead, never cancelled | Cancel on every ending; a sweeper that checks |
| `Timing for main` shows steps getting slower | The fire front grows, so the fire model does more work | Expected; size walltime from post-ignition steps |

## WRF source files worth reading

| File | What it tells you |
| --- | --- |
| `Registry/registry.fire` | every `&fire` variable, default and description; fire fields and their I/O streams |
| `phys/module_fr_fire_phys.F` | `namelist.fire` groups, the fuel code map, how moisture enters the spread rate |
| `phys/module_fr_fire_driver.F` | the moisture model switches and their rules |
| `phys/module_fr_fire_model.F` | ignitions and perimeter initialization |
| `test/em_fire/namelist.fire.sb40`, `namelist.fire_fmc.sb40` | complete 54-category fuel tables, with and without the moisture group |

Source: [WRF v4.6.0 on GitHub](https://github.com/wrf-model/WRF/tree/v4.6.0).
