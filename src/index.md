---
title: Run wildfire simulations on CCR
kicker: WRF-Fire on UB CCR
lead: Set up once, then run any fire with one command that you repeat after each email. No programming needed.
toc: no
---

<div class="cards" markdown="0">
<a class="card" href="start.html"><span class="k">Step 1 · once</span><h3>Set up</h3><p>Three lines in your CCR terminal.</p></a>
<a class="card" href="newfire.html"><span class="k">Step 2</span><h3>Your own fire</h3><p>Answer seven questions about the fire, then run it.</p></a>
<a class="card" href="skill.html"><span class="k">Help</span><h3>AI chat helper</h3><p>Paste one block into any AI chat and it guides you, one command at a time.</p></a>
</div>

## Fires we have run

Ready to run again, or to use as a starting point.

<div class="cards" markdown="0">
<a class="card" href="fire-eaton.html"><span class="k">January 2025</span><h3>Eaton</h3><p>Los Angeles County. Large: 24 nodes.</p></a>
<a class="card" href="fire-canyon.html"><span class="k">August 2025</span><h3>Canyon</h3><p>Ventura and Los Angeles counties. Small: 1 node.</p></a>
<a class="card" href="fire-cranston.html"><span class="k">July 2018</span><h3>Cranston</h3><p>Riverside County. 1 node, long run.</p></a>
<a class="card" href="fire-long.html"><span class="k">July 2024</span><h3>Long</h3><p>Kern County. 1 node.</p></a>
</div>

## The commands, in one table

| To | Type |
| --- | --- |
| describe a new fire | `wrf-card --new FILE` |
| get its weather | `wrf-card --weather FILE` |
| make it | `wrf-card --make FILE --wps` |
| run it, step by step | `wrf-next FIRE` (again after each email) |
| see a fire's settings | `wrf-card FIRE` |
| see all fires | `wrf-status` |
| see all my jobs | `wrf-watch --mine` |
| put something out of the way (never deleted) | `wrf-setaside PATH "why"` |

## How it works

For those who want the details: [the checks behind each step](gates.html), the [research inputs](extend.html) you can change (fuel moisture, fuel maps, ignitions, terrain, coupling), and [how WRF-Fire works](env.html), program by program. The site and its code are at [github.com/utkrshkmr/wrf-manual](https://github.com/utkrshkmr/wrf-manual).
