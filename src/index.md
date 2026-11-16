---
title: WRF-Fire, from raw data to a burning fire
kicker: WRF 4.6 · WPS 4.6 · UB CCR
lead: A hands-on manual for building and running a WRF-Fire simulation entirely by hand, every input explained, plus a record of what our lab has set up, measured and learnt on UB's CCR cluster.
toc: no
---

A WRF-Fire run is six programs in a row. Each one reads a namelist and a few files, and writes the files the next one reads. Once you know what each file holds and which variable controls it, every research change becomes one of a few kinds of edit: a new map, a new field in an input file, or a new value in a namelist. The manual half of this site walks the chain from start to finish, with Canyon 2025 as the worked example. The second half records our own work on CCR: the setup, a week-long scaling campaign, and the workflow we designed from it.

{{fig:pipeline|**The whole chain.** Grey boxes are programs, dashed boxes are files. The orange numbers mark the four places a research input can enter; each has its own section in the manual.}}

## The manual

<div class="cards" markdown="0">
<a class="card" href="env.html"><span class="k">Phase 0</span><h3>Environment and data</h3><p>Modules, folders, the static datasets and the tables WPS needs.</p></a>
<a class="card" href="domain.html"><span class="k">Phase 1</span><h3>Domain design</h3><p>Every <code>namelist.wps</code> variable: nests, projection, the fire-grid ratio.</p></a>
<a class="card" href="geogrid.html"><span class="k">Phase 2</span><h3>Static data</h3><p><code>GEOGRID.TBL</code>, the fuel and terrain layers, and how to add your own map.</p></a>
<a class="card" href="ungrib.html"><span class="k">Phase 3</span><h3>Weather</h3><p>GRIB products, Vtables, intermediate files, hand-made fields.</p></a>
<a class="card" href="metgrid.html"><span class="k">Phase 4</span><h3>Merge</h3><p>What a <code>met_em</code> file holds and how fields are interpolated.</p></a>
<a class="card" href="real.html"><span class="k">Phase 5</span><h3>real.exe</h3><p><code>namelist.input</code>: time, domains, physics, boundaries.</p></a>
<a class="card" href="fire.html"><span class="k">Phase 6</span><h3>The fire model</h3><p>Every <code>&amp;fire</code> option, ignition, coupling, <code>namelist.fire</code> fuels.</p></a>
<a class="card" href="moisture.html"><span class="k">Deep dive</span><h3>Fuel moisture</h3><p>Four ways to set it, from one number to a per-cell map and a live moisture model.</p></a>
<a class="card" href="extend.html"><span class="k">Deep dive</span><h3>Other research inputs</h3><p>Fuel edits, custom fuel types, observed perimeters, terrain, heat-flux experiments.</p></a>
</div>

## Our work on CCR

<div class="cards" markdown="0">
<a class="card" href="setup.html"><span class="k">November 2026</span><h3>WPS on CCR</h3><p>Verifying CCR's WPS module, staging data, and rebuilding Canyon's inputs ourselves.</p></a>
<a class="card" href="campaign.html"><span class="k">October 2026</span><h3>The scaling campaign</h3><p>Four fires × three node types, instrumented end to end.</p></a>
<a class="card" href="scaling.html"><span class="k">Results</span><h3>Scaling and the elbow</h3><p>Strong and weak scaling, Amdahl's elbow, why small fires never reach it.</p></a>
<a class="card" href="costmodel.html"><span class="k">Results</span><h3>Cost model and node formula</h3><p>One equation for every machine, and a nine-step sizing rule.</p></a>
<a class="card" href="queue.html"><span class="k">Results</span><h3>Queue waits and cost</h3><p>Why the fastest node stopped starting for us, and what a run really costs.</p></a>
<a class="card" href="lessons.html"><span class="k">Lessons</span><h3>What went wrong</h3><p>Every incident of the campaign and the rule it produced.</p></a>
<a class="card" href="design.html"><span class="k">Design</span><h3>The workflow</h3><p>A shared folder, five scripts, gates, a ledger and a weekly lookup table.</p></a>
</div>

## Key numbers so far

<div class="stats" markdown="0">
<div class="stat"><b>25</b><span>usable instrumented runs from 48 planned, Oct 18–25</span></div>
<div class="stat"><b>1.5–2.1×</b><span>Sapphire Rapids speed per rank over Cascade Lake</span></div>
<div class="stat"><b>41.8 h</b><span>node formula's walltime for Cranston, against 41.6 h measured</span></div>
<div class="stat"><b>96 / 97</b><span>fields identical when CCR's WPS rebuilt NCAR's Canyon inputs</span></div>
<div class="stat"><b>23 h</b><span>median queue wait on Cascade Lake after day two</span></div>
</div>

## How to read this site

- Variable names are WRF's and WPS's own, in `code`. Defaults come from WRF 4.6.0's `Registry/registry.fire` and the `test/em_fire` examples.
- Paths are CCR's. The lab's shared folder is `/projects/academic/negarkhodoe/wrf/`.
- Numbers in the second half are measurements from our runs, with the conditions stated beside them. Where a run did not finish, it is said so.
- To rebuild the site after editing a page in `src/`, run `python3 tools/build.py`.
