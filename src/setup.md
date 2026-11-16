---
title: WPS on CCR, setup so far
kicker: Our work · November 2026
lead: CCR now provides WPS 4.6 as a module. Until now our inputs were built by our collaborator on NCAR's Derecho. This page records how we verified the module, staged the data, worked out exactly how NCAR built Canyon, and where the end-to-end rebuild stands.
---

## Where it stands

<div class="stats" markdown="0">
<div class="stat"><b>0</b><span>failures in the module check, on login and compute nodes</span></div>
<div class="stat"><b>29 GB</b><span>static geography staged, read-only, in 40 s of download</span></div>
<div class="stat"><b>10 GB</b><span>of fuel and terrain snapshots copied from the Canyon set-up</span></div>
<div class="stat"><b>2 of 3</b><span>WPS programs rerun on Canyon with CCR's module</span></div>
</div>

{{fig:testab|**The validation plan.** Test A swaps only the software; test B swaps only the data. Running both tells us which one to blame if anything differs.}}

## What we did, step by step

| Date | Step | Result |
| --- | --- | --- |
| Nov 10 | Ran `check_wps.sh` on a login node | 0 failures: module loads, all three programs and utilities present, GRIB2 support, Vtables for HRRR, GFS, NAM, ECMWF |
| Nov 10 | Same check on a compute node | Programs start, but the bare-`srun` launch dropped the step (`Connection refused`) |
| Nov 10 | Ran the programs under `srun` in a batch job | ungrib and metgrid stopped at the expected missing-input errors; geogrid hit `End of record` |
| Nov 10 | Short versus long data path | 7-character path: clean error. 85-character path: `End of record`. A path-length bug, now a gate rule |
| Nov 10 | Downloaded UCAR's static geography | 2.6 GB in 40 s, 29 GB unpacked, made read-only |
| Nov 10 | geogrid on real data, 4 ranks | `geo_em.d01.nc` written; terrain values right for the Piru hills (790–860 m) |
| Nov 10 | geogrid with a fire mesh | Default table has no fire entries; `GEOGRID.TBL.FIRE` wants a `landfire_data/` folder; `subgrid_ratio` must be in `&share` |
| Nov 10 | Read NCAR's Canyon `met_em` | Fire ratio 4, `FLAG_ZSF = 1` (fine terrain), HRRR soil levels: the full recipe can be read off the files |
| Nov 10 | Found the Canyon WPS folder on CCR | Exact namelist, combined `GEOGRID.TBL`, `Vtable.HRRR.prs`, 31 GRIB links, logs |
| Nov 10 | Snapshot of fuel and terrain into `wrf/static/` | LF2016, LF2023, LF2024 (2.8 GB each), 1″ terrain (5.4 GB); about 130,000 small tiles per release, so copying ran at 1 MB/s |
| Nov 10 | Test A: geogrid and ungrib | Both `rc 0`. geogrid 12 s. ungrib 55 min (her build: 22.5), slowed by our own copy running at the same time |
| Nov 10 | Test A: metgrid on 8 ranks | Killed at the 2-hour limit while on hour 7 of 31: about 9 minutes per hour of weather |
| Nov 15 | Compared with her single-core metgrid | 47 minutes for all 31 hours: one core is about 6× faster than eight here |
| next | Test A: metgrid on one core, then compare | Pending |

## What we learnt about WPS on CCR

**The module is sound.** It ships with the same compiler, MPI and netCDF as the WRF module our runs use, which is the best case for consistency.

**Run WPS on one core.** Each HRRR intermediate file is 3.4 GB, and with MPI every rank reads all of it. For two small domains there is nothing to gain from splitting the work. From her timings: about 45 s per hour of weather for ungrib and 90 s for metgrid, so about 2.5 minutes per weather hour on one core. Our walltime rule for the WPS job is 4 minutes per weather hour plus 15 minutes.

**Short paths.** geogrid's `End of record` crash comes from a fixed-length text buffer, met while composing an error message about a long path. Our data lives at `/projects/academic/negarkhodoe/wrf/static/` (39 characters).

**The tables need work for fire.** CCR's default `GEOGRID.TBL` has no fire entries, and its `GEOGRID.TBL.FIRE` has `NFUEL_CAT` but no `ZSF`. The Canyon set-up uses its own combined table, which we now keep, with paths pointed at our read-only copies and `halt_on_missing=yes` on the fuel entry.

**A latent trap in the Canyon table.** Three of its four fuel releases (`lf2016`, `lf2022`, `lf2023`) point at folders that don't exist, and the fuel entry fills missing data with 0 silently. Canyon used `lf2024`, the one correct path, so its inputs are fine; another fire using a different release would have had no fuel and no spread.

**Everything can be recovered from the outputs.** `met_em` attributes give the domain geometry, the fire ratio and which fire fields were filled; the soil-level names identify the weather model. With the folder found, we no longer depend on asking anyone how an input was made.

## The data now on CCR

| Folder, under `/projects/academic/negarkhodoe/wrf/` | Contents | Size |
| --- | --- | --- |
| `static/WPS_GEOG/` | UCAR mandatory high-resolution geography | 29 GB |
| `static/LF2016/`, `LF2023/`, `LF2024/` | LANDFIRE FBFM40, California, WPS tiles | 2.8 GB each |
| `static/CA_1s/` | 1-arc-second California elevation, WPS tiles | 5.4 GB |
| `static/MANIFEST_nisha_snapshot.txt` | source, date and file list of the copies | — |
| `tables/fire/` | combined `GEOGRID.TBL`, `METGRID.TBL`, `Vtable.HRRR.prs`, `MANIFEST.sha256` | small |
| `tests/` | geogrid tests 1–3, `canyon_A` | — |

## Scripts written along the way

| Script, in `utkarshk/pipeline/` | Does |
| --- | --- |
| `check_wps.sh` | Loads the module and checks programs, libraries, tables, GRIB2, and that each program runs |
| `compare_met_em.py` | Compares two `met_em` folders field by field |
| `compare_static.py` | Compares one `geo_em` with another, or with a `met_em`, field by field |
| `reverse_wps.py` | Rebuilds a `namelist.wps` and a report from a folder of `met_em` files |
| `landfire_to_wps.py` | Converts a LANDFIRE GeoTIFF (fuel or elevation) into WPS tiles without resampling |
| `snapshot_nisha.sh` | Copies the fuel and terrain layers and tables into the shared folder, read-only, with a manifest |
