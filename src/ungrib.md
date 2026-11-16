---
title: Weather
kicker: WRF mechanics · Phase 3 · ungrib.exe
lead: ungrib turns one weather model's GRIB files into WPS intermediate files, one per time. The weather product you choose sets the initial state, the boundaries, and even which land-surface model WRF can run.
---

## Running it

```bash
ln -sf /projects/academic/negarkhodoe/wrf/tables/fire/Vtable.HRRR.prs Vtable
i=0; for f in /path/to/grib/hrrr.*.wrfprsf00.grib2; do
  L=ABCDEFGHIJKLMNOPQRSTUVWXYZ
  ln -sf $f GRIBFILE.${L:i/676%26:1}${L:i/26%26:1}${L:i%26:1}; i=$((i+1))
done
ungrib.exe
tail -1 ungrib.log
```

The loop does what WPS's `link_grib.csh` does: `GRIBFILE.AAA`, `GRIBFILE.AAB` and so on, in time order. ungrib is serial. For HRRR it takes about 45 s per hour of weather (22.5 minutes for Canyon's 31 files) and writes `FILE:2025-08-07_18` and so on. `ungrib.log` has an `Inventory` table showing which fields it found at each time.

{{fig:vtable|**What ungrib does with each GRIB record.** It looks the record up in the Vtable by its GRIB codes and level, and stores it under the WPS name. Fields the Vtable doesn't list never reach WRF.}}

## Choosing a weather product

| Product | Grid | Interval | Source | Vtable | Notes |
| --- | --- | --- | --- | --- | --- |
| HRRR `wrfprsf00` | 3 km, CONUS | hourly | NOAA archive on AWS (`noaa-hrrr-bdp-pds/hrrr.YYYYMMDD/conus/`) | `Vtable.HRRR.prs` or `Vtable.raphrrr` | 9 soil levels; cloud and rain fields (`QC`, `QR`, `QI`, `QS`, `QG`). Canyon uses hourly analyses (`f00`) |
| RAP | 13 km, North America | hourly | NOAA archives | `Vtable.raphrrr` | Same soil levels as HRRR |
| NAM | 12 km | 3-hourly analyses | NCEI, NCAR RDA | `Vtable.NAM` | 4 soil levels |
| GFS | 0.25° | 3-hourly | NCEI, NCAR RDA, AWS | `Vtable.GFS` | Global; coarse for a fire |
| ERA5 | 0.25° | hourly | Copernicus CDS, NCAR RDA | `Vtable.ECMWF` | Reanalysis; consistent over decades |

Downloading Canyon's 31 HRRR hours on CCR:

```bash
mkdir -p /projects/academic/negarkhodoe/wrf/inputs/weather/hrrr && cd /projects/academic/negarkhodoe/wrf/inputs/weather/hrrr
for h in $(seq 0 30); do
  t=$(date -u -d "2025-08-07 18:00 + $h hour" +%Y%m%d/%H)
  wget -nc -q -O hrrr.${t%/*}.t${t#*/}z.wrfprsf00.grib2 \
    https://noaa-hrrr-bdp-pds.s3.amazonaws.com/hrrr.${t%/*}/conus/hrrr.t${t#*/}z.wrfprsf00.grib2
done
```

**What the choice controls downstream.**

- **Soil layers.** HRRR and RAP give 9 soil levels, the others 4. In `namelist.input` this sets `num_metgrid_soil_levels`, and it pairs with the land-surface model: RUC (`sf_surface_physics = 3`, `num_soil_layers = 9`) for HRRR, Noah (`= 2`, 4 layers) for the others.
- **Vertical levels.** `num_metgrid_levels` in `namelist.input` must equal the level count in `met_em`; read it with `ncdump -h met_em.d01.* | grep -i num_metgrid_levels`.
- **Analysis or forecast.** Hourly `f00` analyses (Canyon) restart from observations every hour. One forecast cycle (`f01`, `f02` …) is smoother in time but drifts. Choose one and state it.

## Adding your own gridded field

A field that isn't in any GRIB file, such as a gridded fuel-moisture analysis, observed winds or a smoke field, can be written straight into WPS intermediate format. Then list it in `fg_name` if it changes in time, or `constants_name` if it doesn't:

```fortran
&metgrid
 fg_name = 'FILE', 'MYFIELD',
 constants_name = 'FMC_STATIC:2025-08-07_18',
/
```

The format is a short sequence of Fortran unformatted records per field: version, header, projection, a description, then the 2-D array. The Python package `pywinter` writes it from NumPy arrays; `rd_intermediate.exe` lists what a file holds. metgrid then interpolates the field onto every domain like any other weather field. It reaches the atmosphere grid of `met_em`, not the fire mesh; for fire-mesh fields use a geogrid layer instead ([Phase 2](geogrid.html#writing-your-own-layer)).
