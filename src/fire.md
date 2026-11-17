---
title: The fire model
kicker: WRF mechanics · Phase 6 · wrf.exe with WRF-Fire
lead: wrf.exe runs the atmosphere and the fire together. Fire options live in the &fire section of namelist.input; fuel properties and the moisture model live in a second file, namelist.fire. Every variable below was checked against WRF 4.6.0's Registry/registry.fire.
---

## Running it

```bash
srun -n <ranks> wrf.exe
grep -iE 'SUCCESS|error|cfl|boundary' rsl.error.0000 | tail
```

Every `&fire` variable takes one value per domain unless noted. Set it on the fire domain and leave the others at 0. The rank count is limited by [the decomposition cap](run.html#how-many-ranks).

{{fig:coupling|**The coupled loop.** WRF-Fire tracks the fire front with a level-set function on the fire mesh. The spread rate comes from Rothermel's model: wind, fuel properties, fuel moisture and slope. The heat released goes back into the atmosphere, which changes the wind.}}

## Switching it on, and where fuel and terrain come from

| Variable | Default | Meaning |
| --- | --- | --- |
| `ifire` | 0 | 2 = run the fire model on this domain |
| `fire_fuel_read` | −1 | −1 = fuel map from WPS (`NFUEL_CAT` in `wrfinput`); 0 = one category everywhere; 1 = by altitude (idealized cases) |
| `fire_fuel_cat` | 1 | The category used when `fire_fuel_read = 0` |
| `fire_topo_from_atm` | 1 | Read but **not used in WRF 4.6**: the code that filled fire terrain from the atmosphere is commented out in `phys/module_fr_fire_driver.F`. The fire always uses `ZSF`, `DZDXF` and `DZDYF` from the inputs, so supply `ZSF` from WPS or the fire sees flat ground |
| `fire_fmc_read` | 1 | Where dead fuel moisture comes from: see [Fuel moisture](moisture.html) |
| `fire_boundary_guard` | 8 | Stop when the fire comes this many cells from the domain edge |
| `fire_print_msg`, `fire_print_file` | 0, 0 | Fire diagnostics in the `rsl` logs; debug files |

## Ignition

Up to five ignitions, numbered 1 to 5 in the variable names. Each one is a line drawn from a start to an end point during a time window. A start equal to the end gives a point.

{{fig:ignition|**One ignition.** Everything within `radius1` of the line burns as the line is drawn. Times count from the run start, so the offset is computed from the clock time, never typed by guesswork.}}

| Variable | Units | Meaning |
| --- | --- | --- |
| `fire_num_ignitions` | — | How many of the five are used |
| `fire_ignition_start_lat1`, `fire_ignition_start_lon1`, `fire_ignition_end_lat1`, `fire_ignition_end_lon1` | degrees | End points, for real cases |
| `fire_ignition_start_x1` … `fire_ignition_end_y1` | m from the lower-left corner | End points, for idealized cases |
| `fire_ignition_start_time1`, `fire_ignition_end_time1` | s from run start | The time window |
| `fire_ignition_radius1` | m | Everything within this distance of the line ignites; at least one fire cell |
| `fire_ignition_ros1` | m/s | How fast the line is drawn |
| `fire_is_real_perim` | logical | Start from an observed perimeter instead: see [Ignitions and perimeters](ignitions.html#start-from-an-observed-perimeter) |

## Spread, heat release and coupling

| Variable | Default | Meaning |
| --- | --- | --- |
| `fire_sprd_mdl` | 1 | 1 = Rothermel (BEHAVE); 0 = McArthur |
| `fire_wind_height` | 6.096 m | Height of the wind used in the spread rate (20 ft) |
| `fire_lsm_zcoupling`, `fire_lsm_zcoupling_ref` | `.false.`, 50 m | Take the wind at a reference height and bring it down with a log profile |
| `fire_slope_factor` | 1.0 | Multiplier on the slope effect |
| `fire_atm_feedback` | 1.0 | Multiplier on heat sent to the atmosphere; 0 = one-way coupling |
| `fire_ext_grnd`, `fire_ext_crwn`, `fire_crwn_hgt` | 50 m, 50 m, 15 m | Depth over which surface and crown heat is spread vertically; crown release height |
| `fire_sfc_flx`, `fire_heat_peak`, `fire_tg_ub` | 0, 0, 1000 m | 0 = exponential heat profile; 1 = truncated Gaussian with this peak and upper bound |
| `fire_smk_scheme`, `fire_smk_peak`, `fire_smk_ext`, `fire_tracer_smoke` | 0, 0, 50 m, 0.02 | Smoke tracer release (with `tracer_opt = 3`) |
| `fire_const_time`, `fire_const_grnhfx`, `fire_const_grnqfx` | −1, 0, 0 | Freeze the fire at a time and hold a constant heat flux (experiments) |

## Numerics

Change these only with a reason; the defaults are the tested ones.

| Variable | Default | Meaning |
| --- | --- | --- |
| `fire_upwinding` | 9 | Level-set advection scheme; 9 = hybrid WENO5/ENO1 |
| `fire_viscosity`, `fire_viscosity_bg`, `fire_viscosity_band`, `fire_viscosity_ngp` | 0.4, 0.4, 0.5, 2 | Artificial viscosity away from and near the front |
| `fire_lsm_reinit`, `fire_lsm_reinit_iter`, `fire_upwinding_reinit`, `fire_lsm_band_ngp` | `.true.`, 1, 4, 4 | Level-set reinitialization |
| `fire_grows_only` | 1 | The burnt area can only grow |
| `fire_advection` | 1 | Spread uses the fire-line particle speed projected on the normal |
| `fire_fuel_left_method`, `fire_fuel_left_irl`, `fire_fuel_left_jrl` | 1, 2, 2 | How remaining fuel is integrated within a cell |

## Spotting

Firebrand spotting is off by default (`fs_firebrand_gen_lim = 0`). A value above 0 generates firebrands. The other `fs_*` variables set how often and how many are made, how high (`fs_firebrand_gen_maxhgt`, 50 m), their size, density and temperature, and how long they live.

## namelist.fire

`namelist.fire` sits in the run folder. Without it, built-in defaults are used; either way, WRF writes the values it used to `namelist.fire.output`, the first thing to check. It has three groups.

**`&fuel_scalars`**, one value each:

| Variable | Default | Meaning |
| --- | --- | --- |
| `cmbcnst` | 17.433e6 J/kg | Heat of combustion of dry fuel |
| `hfgl` | 17e4 W/m² | Surface heat flux that ignites the canopy |
| `fuelmc_g` | 0.08 | Dead surface fuel moisture, as a fraction (0.08 = 8%) |
| `fuelmc_g_lh` | 1.20 | Live herbaceous moisture: ≥ 1.20 uncured, ≤ 0.30 fully cured, in between a share of the live load counts as dead |
| `fuelmc_c` | 1.00 | Canopy fuel moisture |
| `nfuelcats` | 53 | Number of categories defined. **Must be 54 for Scott and Burgan SB4 (code 204)** |
| `no_fuel_cat` | 14 | The "no fuel" category |

**`&fuel_categories`**, one value per category, as comma-separated lists:

| Variable | Meaning |
| --- | --- |
| `fuel_name` | Label |
| `fgi`, `fgi_lh` | Dead fuel load and live herbaceous load, kg/m² |
| `fueldepthm` | Fuel bed depth, m |
| `savr` | Surface-area-to-volume ratio, 1/ft |
| `fuelmce` | Moisture of extinction: moisture at which this fuel stops burning |
| `fueldens` | Particle density, lb/ft³ |
| `st`, `se` | Total and effective mineral content |
| `windrf` | Wind reduction factor from the wind height to mid-flame |
| `weight` | Burn-out time constant: about 7 for grass, 900 for timber litter |
| `ichap` | 1 = treat as chaparral |
| `fci_d`, `fct` | Canopy load and canopy burn time |
| `fgi_1h`, `fgi_10h`, `fgi_100h`, `fgi_1000h`, `fgi_live` | Load per moisture class, used as weights by the moisture model |

Editing a column changes that fuel type everywhere it occurs. The third group, `&fuel_moisture`, is covered on the [fuel-moisture page](moisture.html#route-d-the-moisture-model).

## How fuel codes become categories

{{fig:fuelmap|**The code map in `set_fire_params`.** Anderson codes keep their numbers. Scott and Burgan codes become categories 15–54 in order. Every other code up to 204, including the non-burnable 91–99, becomes 14, no fuel.}}

Two consequences:

- **Code 204 crashes a default run.** It maps to category 54, but the built-in table stops at 53, so WRF stops with `fuel category out of bounds`. This is the code-204 crash we hit. The fix is a `namelist.fire` with `nfuelcats = 54` and 54 columns, such as `test/em_fire/namelist.fire.sb40` in the WRF source.
- **The lookup ends at 204.** A code of 0, or above 204 (LANDFIRE's missing value is 205), is outside the table. Check `NFUEL_CAT` for stray values before running.

## Outputs to look at

| Field | Meaning |
| --- | --- |
| `FIRE_AREA` | Burnt fraction of each fire cell |
| `TIGN_G` | Ignition time of each fire cell, seconds from run start |
| `ROS` | Rate of spread, m/s |
| `FGRNHFX`, `FGRNQFX` | Ground heat and moisture flux, W/m² |
| `FLAME_LENGTH`, `ROS_FRONT` | At the front |
| `FMC_G` | Fuel moisture used |
| `UF`, `VF` | Wind at the fire |
| `LFN` | The level-set function; the front is where it is 0 |

Not all of these are in `wrfout` by default; add them with `iofields_filename`.
