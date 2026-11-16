---
title: WRF-Fire, from raw data to a burning fire
kicker: WRF 4.6 · WPS 4.6 · UB CCR
lead: A hands-on manual for building, checking and running a WRF-Fire simulation on UB's CCR cluster, with every input explained and a gating system that checks each step before it costs queue time.
toc: no
---

A WRF-Fire run is six programs in a row. Each one reads a namelist and a few files, and writes the files the next one reads. Once you know what each file holds and which variable controls it, every research change becomes one of a few kinds of edit: a new map, a new field in an input file, or a new value in a namelist. The manual walks the chain from start to finish, with Canyon 2025 as the worked example, and the gating pages show how each input and run is checked before and after it uses the cluster.

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

## Running it safely

<div class="cards" markdown="0">
<a class="card" href="gates.html"><span class="k">Gates</span><h3>The gating system</h3><p>Eight commands, five gates, your profile, the folders and the ledger.</p></a>
<a class="card" href="example.html"><span class="k">Example</span><h3>Every fire we have run</h3><p>Eaton first, then Canyon, Cranston, Long and the NCAR fires, command by command.</p></a>
<a class="card" href="skill.html"><span class="k">For agents</span><h3>Skill file</h3><p>SKILL.md: lets a coding agent run any fire through the gates, safely.</p></a>
</div>

## How to read this site

- Variable names are WRF's and WPS's own, in `code`. Defaults come from WRF 4.6.0's `Registry/registry.fire` and the `test/em_fire` examples.
- Paths are CCR's. The lab's shared folder is `/projects/academic/negarkhodoe/wrf/`.
- To rebuild the site after editing a page in `src/`, run `python3 tools/build.py`.
