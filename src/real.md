---
title: real.exe and namelist.input
kicker: Phase 5
lead: real.exe builds the model's vertical grid from the met_em files and writes the initial state (wrfinput) and the boundary conditions (wrfbdy). It reads the same namelist.input that wrf.exe will read, so this page covers that file's core sections.
---

## Running it

Link the `met_em` files and WRF's run-time tables into the run folder, then:

```bash
srun -n 8 real.exe
tail -1 rsl.error.0000
ls -la wrfinput_d0* wrfbdy_d01
```

Success ends with `SUCCESS COMPLETE REAL_EM INIT`. real.exe takes minutes. It writes `wrfinput_d01`, `wrfinput_d02` (initial state; the fire fields are in `wrfinput_d02`) and `wrfbdy_d01` (lateral boundaries for d01, one update every `interval_seconds`). Nests get their boundaries from their parent while WRF runs.

{{fig:agree|**The values that must agree.** Domain geometry, the fire-mesh ratio, dates and level counts appear in all three places. A mismatch stops real.exe with an error in `rsl.error.0000`.}}

## &time_control

| Variable | Meaning | Rule |
| --- | --- | --- |
| `run_days`, `run_hours`, `run_minutes` | Run length | `end_*` takes precedence when both are set |
| `start_year` … `start_second`, `end_year` … `end_second` | Start and end, per domain | Inside the `met_em` period |
| `interval_seconds` | Boundary update interval | Same as `namelist.wps` |
| `input_from_file` | Each domain reads its own `wrfinput` | `.true.` on the fire domain, so it gets fine fuel and terrain |
| `history_interval` | Minutes between `wrfout` times, per domain | e.g. 60 for d01, 10–15 for the fire domain |
| `frames_per_outfile` | Output times per `wrfout` file | 1 = one file per time |
| `restart`, `restart_interval` | Start from a restart file; minutes between restart files | `restart_interval` sets how much is lost if a job dies |
| `io_form_history`, `io_form_restart`, `io_form_input`, `io_form_boundary` | File formats | 2 = netCDF |
| `iofields_filename` | Text file adding or removing output fields, per domain | e.g. `+:h:0:FMC_G,ROS,FGRNHFX` adds fire fields to the history output |
| `debug_level` | Log detail | 0; higher values make huge `rsl` files |

## &domains

| Variable | Meaning | Rule |
| --- | --- | --- |
| `max_dom`, `e_we`, `e_sn`, `parent_id`, `parent_grid_ratio`, `i_parent_start`, `j_parent_start` | Domain geometry | Exactly as in `namelist.wps` |
| `dx`, `dy` | Cell size, listed for every domain | Canyon: 900, 100 |
| `e_vert` | Vertical levels | Same on all domains |
| `p_top_requested` | Model top, Pa | Must lie inside the `met_em` data; 5000 is common |
| `num_metgrid_levels`, `num_metgrid_soil_levels` | Level counts in `met_em` | Read them from a `met_em` file |
| `time_step` | d01 time step, s | At most about 6 × `dx` in km: 5 s or less for 900 m. the campaign's Cranston runs used 3 s |
| `parent_time_step_ratio` | Nest step = parent's ÷ this | Usually equal to `parent_grid_ratio` |
| `feedback` | Nest results fed back to the parent | 0 or 1 |
| `sr_x`, `sr_y` | Fire-mesh ratio per domain | Same as WPS `subgrid_ratio_x/_y`; Canyon 4 on d02 |
| `nproc_x`, `nproc_y` | Force the MPI tiling | Optional; see [the decomposition cap](run.html#how-many-ranks) |

## &physics, &dynamics and &bdy_control

These decide how the atmosphere behaves. The fire couples to it through heat and moisture fluxes, so at fire scale the boundary layer and turbulence choices matter most.

| Variable | Selects | Fire-scale notes |
| --- | --- | --- |
| `mp_physics` | Cloud microphysics | Thompson (8) pairs well with HRRR input |
| `ra_lw_physics`, `ra_sw_physics`, `radt` | Radiation and how often it runs | RRTMG (4) |
| `sf_sfclay_physics` | Surface layer | Must pair with the boundary-layer scheme |
| `sf_surface_physics`, `num_soil_layers` | Land-surface model | RUC (3) with 9 layers for HRRR input; Noah (2) with 4 for NAM, GFS, ERA5 |
| `bl_pbl_physics` | Boundary-layer scheme | Either a PBL scheme on both domains, or on a 100 m fire domain an LES set-up: `bl_pbl_physics = 0`, `km_opt = 2`, `diff_opt = 2` |
| `cu_physics` | Cumulus | 0 on both domains below about 4 km |
| `diff_opt`, `km_opt`, `w_damping`, `damp_opt`, `epssm` | Turbulence, damping, sound-wave filtering (`&dynamics`) | `w_damping = 1` guards against fire-driven updrafts breaking the time step |
| `specified`, `nested`, `spec_bdy_width`, `relax_zone` | Boundary treatment (`&bdy_control`) | `specified = .true.` on d01, `nested = .true.` on the nest |

## Checking the fire fields

real.exe writes these into `wrfinput_d02`, on the fire mesh: `NFUEL_CAT`, `ZSF`, `DZDXF`, `DZDYF`, and `FMC_G` (present, but only filled if you supply it). Check them before submitting a long job:

```bash
python3 - <<'EOF'
import numpy as np
from netCDF4 import Dataset
d = Dataset("wrfinput_d02")
f = d["NFUEL_CAT"][0].astype(int)
codes, n = np.unique(f, return_counts=True)
print("fire mesh", f.shape, "codes", dict(zip(codes.tolist(), n.tolist())))
print("ZSF", float(d["ZSF"][0].min()), "to", float(d["ZSF"][0].max()), "m")
print("FMC_G", float(d["FMC_G"][0].min()), "to", float(d["FMC_G"][0].max()))
EOF
```

Look for: no code 0 or codes above 204 (see [the fuel code map](fire.html#how-fuel-codes-become-categories)), terrain in a plausible range, and `FMC_G` all zero unless you meant to set it.
