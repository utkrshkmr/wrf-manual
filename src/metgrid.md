---
title: Merge
kicker: Phase 4 · metgrid.exe
lead: metgrid interpolates each intermediate file onto each domain and adds the static fields from geo_em. The result, one met_em file per domain per time, is everything real.exe needs.
---

## Running it

```bash
metgrid.exe
tail -1 metgrid.log
ls met_em.d0* | wc -l
```

Canyon gets 31 times × 2 domains = 62 files. **Run it on one core.** A single-core build took 47 minutes for Canyon (about 90 s per hour of weather, both domains). With 8 MPI ranks on CCR, every rank reads each 3.4 GB HRRR file in full, and the same job was on course for about 4.7 hours before it hit its time limit.

{{fig:metem|**Inside a met_em file.** Weather on pressure levels, surface and soil fields, the static fields from geogrid, and the fire fields on the finer fire mesh. The fire fields are copied through unchanged.}}

## What a met_em file holds

| Group | Fields | Grid |
| --- | --- | --- |
| Static, from `geo_em` | `HGT_M`, `LU_INDEX`, `LANDUSEF`, `SOILCTOP`, `GREENFRAC`, `ALBEDO12M`, `LAI12M`, map factors, latitudes and longitudes, any custom geogrid field | Atmosphere |
| Fire, from `geo_em` | `NFUEL_CAT`, `ZSF`, `DZDXF`, `DZDYF`, any `subgrid=yes` field | Fire mesh |
| 3-D weather | `TT`, `RH` or `SPECHUMD`, `UU`, `VV`, `GHT`, `PRES`; for HRRR also `QC`, `QR`, `QI`, `QS`, `QG` | Atmosphere, pressure levels |
| Surface weather | `PSFC`, `PMSL`, `SKINTEMP`, `SNOW`, `SNOWH`, `SEAICE`, `LANDSEA`, `SOILHGT` | Atmosphere |
| Soil | `SOILT000` … `SOILT300`, `SOILM000` … `SOILM300` (HRRR: 9 depths, in cm) | Atmosphere |

The global attributes record how the file was made: `sr_x`, `sr_y`, `FLAG_NFUEL_CAT`, `FLAG_ZSF` (1 when the field was filled), `num_metgrid_levels`, `TITLE` (the WPS version) and the whole domain geometry. A `namelist.wps` can be rebuilt from them, which is how we confirmed NCAR's Canyon set-up:

```bash
ncdump -h met_em.d02.2025-08-07_18:00:00.nc | grep -E ':sr_x|:FLAG_|NUM_METGRID|TITLE|:DX'
```

## METGRID.TBL

`METGRID.TBL` controls how each weather field is interpolated horizontally (`interp_option`), whether it is masked to land or water (`interp_mask`), and what to do when a field is missing (`fill_missing`, `fill_lev`). A field with no entry is interpolated with the default method and a note in the log. The default table works for HRRR; edit it only for a field of your own that needs different handling, for example nearest-neighbour for a categorical field.

## Comparing two sets of met_em files

When you rebuild a fire's inputs (on another machine, with another data release or another WPS build), compare the outputs field by field before trusting them. Our script prints variables found in only one set, shape mismatches, and the largest absolute difference for each field:

```bash
python3 /projects/academic/negarkhodoe/utkarshk/pipeline/compare_met_em.py <new_dir> <reference_dir>
```

What to expect: static and fire fields identical (`NFUEL_CAT` matching in at least 99.9% of cells), and weather fields equal or within rounding when the GRIB files are the same.
