---
title: Cranston 2018
kicker: Fires we have run · CRANSTON_2018
lead: Riverside County, July 2018. A mid-sized fire on one node, with a long run time.
---

| | |
| --- | --- |
| Simulated | 20 hours, Jul 25 16:00 to Jul 26 12:00 UTC |
| Ignition | Jul 25 18:41 UTC at 33.711295, −116.769312 |
| Grids | outer 71 × 64, fire 370 × 307 |
| Fuel map | LANDFIRE 2016 |
| Size of the run | 1 node, 36 processes; about 30–42 hours |

Its files are already in the shared folder, checked and ready. You only need to have [set up](start.html) once.

## Run it

**1. Start it.**

```bash
wrf-next CRANSTON_2018
```

It checks everything and submits the first job. You get an email when it ends.

**2. After each email, run the same command again.**

```bash
wrf-next CRANSTON_2018
```

Each time, it reports how the last step went and starts the next one. There are four steps: the weather and map files (already done for this fire), the start files, a 2-minute test run, and the simulation itself.

**3. Before the simulation, it asks you.** It shows the size it suggests (nodes, processes, time limit and the most it can cost) and waits for *y*.

**4. While it runs**, `wrf-next CRANSTON_2018` shows how far it has got and the time left.

**5. When it is done**, `wrf-next CRANSTON_2018` says how it ended and where the results are: the `wrfout_*` files in the run folder it prints.

If a step fails, `wrf-next` prints what is wrong in plain words. If it is not clear what to do, paste the output into the [AI chat helper](skill.html).

## Its settings

These are the settings that define the fire. `wrf-card CRANSTON_2018` prints all of them, including everything not shown here.

```text
name:                CRANSTON_2018
start:               2018-07-25 16:00
end:                 2018-07-26 12:00
ignition_time:       2018-07-25 18:41
ignition_lat:        33.711295
ignition_lon:        -116.769312
outer_cells:         71x64
fire_cells:          370x307
fuel_layer:          /projects/academic/negarkhodoe/wrf/static/landfire/LF2016/FBFM40
base_spec:           CRANSTON_2018/campaign
```

## Try a variation

Change one setting, for example drier fuel, and run it as your own copy:

```bash
wrf-card CRANSTON_2018 > /projects/academic/negarkhodoe/wrf/people/$USER/work/cranston_dry.card
nano /projects/academic/negarkhodoe/wrf/people/$USER/work/cranston_dry.card
wrf-card --make /projects/academic/negarkhodoe/wrf/people/$USER/work/cranston_dry.card
wrf-next CRANSTON_2018
```

In the editor, change the line you want (for example `fuel_moisture: 0.05`) and the `note:` line, then save (Ctrl-O, Enter) and exit (Ctrl-X). `wrf-next` always uses your newest copy. Settings you can change are listed on [Your own fire](newfire.html#5-changing-settings).

## Good to know

- It takes more than a day and a half on the slower nodes; `wrf-next` sizes the time limit from its test run.
