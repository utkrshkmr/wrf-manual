---
title: The fuel-map mismatch
kicker: Our work · open investigation · November 2026
lead: Rebuilding Canyon's fuel map from the public LANDFIRE download first matched NCAR's in only 97.3% of fire cells. The pixels turned out to be identical; what differed was the reference point in the layer's index file. This page sets out the evidence, the hypothesis, the study that will settle it, and the questions for our collaborators.
---

## Why it matters

Every WRF-Fire run reads its fuel from `NFUEL_CAT`, one Scott and Burgan code per 25 m fire cell. If two ways of building "the same" input give different fuel in a few percent of cells, simulations built on CCR and at NCAR are not comparable, and any fire-behaviour difference we attribute to physics or hardware could be an input difference instead. Before the lab builds inputs on CCR, we need to know exactly what produces NCAR's fuel map.

## What we found, step by step

| Step | What we did | Result |
| --- | --- | --- |
| 1 | Rebuilt Canyon with CCR's WPS and Nisha's own layers and tables (Test A) | 96 of 97 fields identical; `NFUEL_CAT` differs in 3 of 753,424 cells |
| 2 | Downloaded LANDFIRE FBFM40 (CONUS) for LF2016, 2022, 2023, 2024 and 2025; cut California at LANDFIRE's native 30 m grid; converted to WPS tiles | All five aligned exactly to the source grid; no resampling |
| 3 | Ran geogrid for Canyon with each release in place of NCAR's fuel layer | LF2024 closest at **97.29%**; others 57–94% |
| 4 | Compared raw pixels of our LF2024 with NCAR's layer around Canyon, no geogrid in between | **100.00% identical**; any 1-pixel shift drops to 69–75% |
| 5 | Gave our layer the same reference pixel as NCAR's `index` (tiles unchanged) | **100.00%**: 7 of 753,424 cells differ |

{{fig:releases|**Step 3.** Each release changes a different share of Canyon's fuel. LF2024 is clearly the one NCAR used; the remaining 2.7% came from step 5's cause, not from the data.}}

### The mismatch pattern

The 2.7% were not random. The largest differences came in mirrored pairs: `122→145` in 3,505 cells and `145→122` in 3,466; `102→122` in 1,379 and `122→102` in 1,315. Swaps in both directions along the same fuel pairs mean the two maps hold the same fuel patches, placed a few metres apart: cells near a boundary between two fuels fall on one side or the other.

### The only difference: the anchor

A WPS layer's `index` file names one reference pixel and its latitude and longitude. NCAR's layer names a pixel at the north-west corner of California; our first conversion named the south-west corner. Both are exactly on LANDFIRE's 30 m grid, about 1 mm apart from the true pixel centres when checked with GDAL's projection library.

{{fig:anchor|**The working hypothesis.** geogrid positions pixels outward from the reference point with its own Albers formulas. A small difference from the exact projection grows with distance, so the same pixels anchored about 1,020 km away (NCAR's) and about 590 km away (ours) land slightly apart at Canyon.}}

### The 7 remaining cells

- **2 cells** are ties: a fire-cell centre almost exactly on a pixel edge, like the 3 cells in Test A.
- **5 cells** read as no data in our layer. They probably sit on seams between our 1000-pixel tiles, which have no halo (`tile_bdr = 0`); NCAR's tiles carry a 3-pixel halo. The anchor study measures this directly.

## What is not yet known

1. **Is the anchor the cause in general, or only at Canyon?** One fire shows the effect exists. It doesn't show how large it is elsewhere, or that NCAR used the same anchor and release for every fire.
2. **Which anchor is more accurate?** Matching NCAR shows we copied NCAR, not that the fuel is in the right place. If geogrid's Albers formulas drift with distance, a reference point near the fire would place the fuel more accurately than either corner.
3. **How large is geogrid's error,** in metres, as a function of distance from the reference point, and does it also affect latitude–longitude layers such as the fine terrain?

## The anchor study

Two experiments in one job, `tools/experiments/anchor_study.sbatch`, writing everything to `wrf/tests/anchor_study/` with a single `REPORT.txt`.

**Experiment 1: every NCAR fire.** For each fire with NCAR inputs on CCR (Canyon, Cranston, Long, Airport, Bradford Branch, Carmel), rebuild its domains from its `met_em` attributes and run geogrid once per fuel layer: our five releases with the south-west anchor, the same five with NCAR's anchor, and NCAR's own three layers as controls. Output: the share of identical fire cells for every fire × layer, the fire's distance to each anchor, and the top mismatches.

- If NCAR's anchor reproduces every fire at about 100%, NCAR used one layer set and one anchor throughout, and we can reproduce all of it.
- If the south-west anchor's match falls with the fire's distance from its anchor, the projection hypothesis holds.
- The best release per fire tells us which LANDFIRE year each fire was built from.

**Experiment 2: measuring geogrid directly.** Two "coded" layers on LANDFIRE's exact grid hold each pixel's own column and row number. Small 100 m test domains at about 150 sites on a 0.75° lattice across California are run through geogrid with the reference pixel at the south-west corner, at NCAR's north-west pixel, at the centre of California, and next to each site. Because the value geogrid picks *is* the pixel number, comparing it with the exact pixel from GDAL gives geogrid's positioning error in metres at every site, for every anchor. The same is done with a tile halo of 3 versus 0 (for the seam cells) and with a latitude–longitude coded layer (the kind of grid the fine terrain uses).

- If the error grows with distance from the anchor and is near zero for the local anchor, the hypothesis holds, and the rule becomes: anchor near the fire, or within a measured distance of it.
- If the error is near zero everywhere, the anchor is not the mechanism, and we look again.

## Questions for our collaborators

1. **Which LANDFIRE product and edition** was converted into `LF_2024/fbfm40`, and from which download: the CONUS GeoTIFF, a LANDFIRE Product Service clip, or another source?
2. **How was the WPS layer made:** which tool or script, and how was the `index` reference pixel (`known_x = 1`, `known_y = 43366`, 42.0618221 N, 125.1993245 W) chosen?
3. **Were the same fuel layer and `GEOGRID.TBL` used for every fire** (Canyon, Cranston, Long, Airport, Bradford Branch, Carmel), and did every fire use the `lf2024` resolution key?
4. **Where does `topo_CA_1s_nisha` come from:** USGS 3DEP 1 arc-second tiles, or another elevation product, and how was it mosaicked?
5. In the shared `GEOGRID.TBL`, the `lf2016`, `lf2022` and `lf2023` keys point at folders that don't exist (`LF2016_CA_WPS`, …), and the fuel entry has `halt_on_missing=no`. **Was any fire built with one of those keys?** It would have had fuel code 0 everywhere.
6. **Is there a reason to prefer a corner anchor** over one near each fire?

## What is settled already

- HRRR weather: our 31 downloads are byte-identical to NCAR's files.
- CCR's WPS module reproduces NCAR's processing (Test A).
- Our LANDFIRE conversion copies pixels exactly (step 4).
- With the same reference point, our LF2024 layer reproduces NCAR's Canyon fuel map (step 5).
