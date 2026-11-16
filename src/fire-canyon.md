---
title: Canyon 2025
kicker: Fires we have run · CANYON_2025
lead: Ventura and Los Angeles counties, August 2025. A small, quick fire: one node is enough, and it is the example used throughout this site.
---

| | |
| --- | --- |
| Simulated | 30 hours, Aug 7 18:00 to Aug 9 00:00 UTC |
| Ignition | Aug 7 20:25 UTC at 34.439636, −118.735548 |
| Grids | outer 54 × 54, fire 217 × 217 |
| Fuel map | LANDFIRE 2024 |
| Size of the run | 1 node, 25 processes |

Its files are already in the shared folder, checked and ready. You only need to have [set up](start.html) once.

## Run it

**1. Start it.**

```bash
wrf-next CANYON_2025
```

It checks everything and submits the first job. You get an email when it ends.

**2. After each email, run the same command again.**

```bash
wrf-next CANYON_2025
```

Each time, it reports how the last step went and starts the next one. There are four steps: the weather and map files (already done for this fire), the start files, a 2-minute test run, and the simulation itself.

**3. Before the simulation, it asks you.** It shows the size it suggests (nodes, processes, time limit and the most it can cost) and waits for *y*.

**4. While it runs**, `wrf-next CANYON_2025` shows how far it has got and the time left.

**5. When it is done**, `wrf-next CANYON_2025` says how it ended and where the results are: the `wrfout_*` files in the run folder it prints.

If a step fails, `wrf-next` prints what is wrong in plain words. If it is not clear what to do, paste the output into the [AI chat helper](skill.html).

## Its settings

These are the settings that define the fire. `wrf-card CANYON_2025` prints all of them, including everything not shown here.

```text
name:                CANYON_2025
start:               2025-08-07 18:00
end:                 2025-08-09 00:00
ignition_time:       2025-08-07 20:25
ignition_lat:        34.439636
ignition_lon:        -118.735548
outer_cells:         54
outer_dx_m:          900
fire_cells:          217
fire_ratio:          9
fire_mesh_ratio:     4
weather_interval_s:  3600
fuel_layer:          /projects/academic/negarkhodoe/wrf/static/landfire/LF2024/FBFM40
base_spec:           CANYON_2025/campaign
```

## Try a variation

Change one setting, for example drier fuel, and run it as your own copy:

```bash
wrf-card CANYON_2025 > /projects/academic/negarkhodoe/wrf/people/$USER/work/canyon_dry.card
nano /projects/academic/negarkhodoe/wrf/people/$USER/work/canyon_dry.card
wrf-card --make /projects/academic/negarkhodoe/wrf/people/$USER/work/canyon_dry.card
wrf-next CANYON_2025
```

In the editor, change the line you want (for example `fuel_moisture: 0.05`) and the `note:` line, then save (Ctrl-O, Enter) and exit (Ctrl-X). `wrf-next` always uses your newest copy. Settings you can change are listed on [Your own fire](newfire.html#5-changing-settings).
