---
title: Run WRF-Fire on CCR
kicker: WRF 4.6 · WPS 4.6 · UB CCR
lead: Everything the lab needs to run wildfire simulations on UB's cluster: a quick start, a set of commands that check every step before it costs queue time, an AI-chat helper, and a full manual of how WRF-Fire works.
toc: no
---

## Start here

<div class="cards" markdown="0">
<a class="card" href="quickstart.html"><span class="k">10 minutes</span><h3>Quick start</h3><p>Install, set yourself up, and start your first run.</p></a>
<a class="card" href="skill.html"><span class="k">Easiest</span><h3>Use it from an AI chat</h3><p>Copy one block of text into any chat assistant; it walks you through the rest.</p></a>
<a class="card" href="example.html"><span class="k">Example</span><h3>Every fire we have run</h3><p>Eaton, Canyon, Cranston, Long and the NCAR fires, command by command.</p></a>
</div>

## Running fires

Every run goes through a few `wrf-*` commands. Each does one step, checks it (the "gates"), and refuses to go on if something is wrong, so a typo or a misplaced map is caught in minutes instead of after a day in the queue. Jobs are signed with your name, Slurm emails you, `wrf-watch` shows how every job is doing, and nothing is ever deleted.

<div class="cards" markdown="0">
<a class="card" href="gates.html"><span class="k">Reference</span><h3>The gating system</h3><p>The commands, what each gate checks, the folders, monitoring and the log.</p></a>
<a class="card" href="run.html"><span class="k">Sizing</span><h3>Ranks and walltime</h3><p>How many cores to ask for, how long, and what to do past 72 hours.</p></a>
<a class="card" href="reference.html"><span class="k">Help</span><h3>Failures and fixes</h3><p>Common errors from WPS, real.exe and wrf.exe, and what they mean.</p></a>
</div>

## Advanced: research inputs

Changing what the fire sees, one theme per page, each with the variables, ready-to-run scripts and the checks that confirm the change took effect.

<div class="cards" markdown="0">
<a class="card" href="moisture.html"><span class="k">Moisture</span><h3>Fuel moisture</h3><p>From one number to a per-cell map and a moisture model driven by the weather.</p></a>
<a class="card" href="fuelmap.html"><span class="k">Map</span><h3>The fuel map</h3><p>Other LANDFIRE releases, fuel breaks, treated areas.</p></a>
<a class="card" href="fuelprops.html"><span class="k">Table</span><h3>How a fuel type burns</h3><p>Load, depth, extinction moisture and the other <code>namelist.fire</code> columns.</p></a>
<a class="card" href="ignitions.html"><span class="k">Start</span><h3>Ignitions and perimeters</h3><p>Points, lines, staggered ignitions, or an observed perimeter.</p></a>
<a class="card" href="terrain.html"><span class="k">Ground</span><h3>Terrain and slope</h3><p>Fine 30 m terrain for the fire, and slope sensitivity tests.</p></a>
<a class="card" href="coupling.html"><span class="k">Air</span><h3>Fire and atmosphere</h3><p>One-way coupling, heat release height, spread wind, prescribed heat.</p></a>
</div>

## WRF mechanics

How the six programs turn maps and weather into a burning fire: every file, every namelist variable, with Canyon 2025 as the example. Read this when you build a new fire's inputs from scratch, or want to know why a setting matters.

{{fig:pipeline|**The whole chain.** Grey boxes are programs, dashed boxes are files. The orange numbers mark the four places a research input can enter.}}

<div class="cards" markdown="0">
<a class="card" href="env.html"><span class="k">Phase 0</span><h3>Environment and data</h3><p>Modules, folders, the static datasets and tables.</p></a>
<a class="card" href="domain.html"><span class="k">Phase 1</span><h3>Domain design</h3><p><code>namelist.wps</code>: nests, projection, the fire-grid ratio.</p></a>
<a class="card" href="geogrid.html"><span class="k">Phase 2</span><h3>Static data</h3><p><code>GEOGRID.TBL</code>, fuel and terrain layers, your own maps.</p></a>
<a class="card" href="ungrib.html"><span class="k">Phase 3</span><h3>Weather</h3><p>GRIB products, Vtables, intermediate files.</p></a>
<a class="card" href="metgrid.html"><span class="k">Phase 4</span><h3>Merge</h3><p>What a <code>met_em</code> file holds.</p></a>
<a class="card" href="real.html"><span class="k">Phase 5</span><h3>real.exe</h3><p><code>namelist.input</code>: time, domains, physics, boundaries.</p></a>
<a class="card" href="fire.html"><span class="k">Phase 6</span><h3>The fire model</h3><p>Every <code>&amp;fire</code> option and <code>namelist.fire</code>.</p></a>
</div>

## About this site

- Variable names are WRF's and WPS's own, in `code`; defaults are from WRF 4.6.0's source. Paths are CCR's; the lab's shared folder is `/projects/academic/negarkhodoe/wrf/`.
- The site and the gating code live in [github.com/utkrshkmr/wrf-manual](https://github.com/utkrshkmr/wrf-manual). To rebuild the site after editing a page in `src/`, run `python3 tools/build.py`.
