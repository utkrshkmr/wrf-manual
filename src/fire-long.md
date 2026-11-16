---
title: Long 2024
kicker: Fires we have run · LONG_2024
lead: Kern County, July 2024. One node; in our earlier run the fire reached the edge of its simulated area before the end.
---

| | |
| --- | --- |
| Simulated | 28 hours, Jul 15 20:00 to Jul 17 00:00 UTC |
| Ignition | Jul 15 21:30 UTC at 35.830005, −118.175345 |
| Grids | outer 60 × 63, fire 271 × 298 |
| Fuel map | LANDFIRE 2023 |
| Size of the run | 1 node, 36 processes |

Its files are already in the shared folder, checked and ready. You only need to have [set up](start.html) once.

## Run it

**1. Start it.**

```bash
wrf-next LONG_2024
```

It checks everything and submits the first job. You get an email when it ends.

**2. After each email, run the same command again.**

```bash
wrf-next LONG_2024
```

Each time, it reports how the last step went and starts the next one. There are four steps: the weather and map files (already done for this fire), the start files, a 2-minute test run, and the simulation itself.

**3. Before the simulation, it asks you.** It shows the size it suggests (nodes, processes, time limit and the most it can cost) and waits for *y*.

**4. While it runs**, `wrf-next LONG_2024` shows how far it has got and the time left.

**5. When it is done**, `wrf-next LONG_2024` says how it ended and where the results are: the `wrfout_*` files in the run folder it prints.

If a step fails, `wrf-next` prints what is wrong in plain words. If it is not clear what to do, paste the output into the [AI chat helper](skill.html).

## Its settings

These are the settings that define the fire. `wrf-card LONG_2024` prints all of them, including everything not shown here.

```text
name:                LONG_2024
start:               2024-07-15 20:00
end:                 2024-07-17 00:00
ignition_time:       2024-07-15 21:30
ignition_lat:        35.830005
ignition_lon:        -118.175345
outer_cells:         60x63
fire_cells:          271x298
fuel_layer:          /projects/academic/negarkhodoe/wrf/static/landfire/LF2023/FBFM40
base_spec:           LONG_2024/campaign
```

## Try a variation

Change one setting, for example drier fuel, and run it as your own copy:

```bash
wrf-card LONG_2024 > /projects/academic/negarkhodoe/wrf/people/$USER/work/long_dry.card
nano /projects/academic/negarkhodoe/wrf/people/$USER/work/long_dry.card
wrf-card --make /projects/academic/negarkhodoe/wrf/people/$USER/work/long_dry.card
wrf-next LONG_2024
```

In the editor, change the line you want (for example `fuel_moisture: 0.05`) and the `note:` line, then save (Ctrl-O, Enter) and exit (Ctrl-X). `wrf-next` always uses your newest copy. Settings you can change are listed on [Your own fire](newfire.html#5-changing-settings).

## Good to know

- **It stops early, and that is expected.** In our earlier run the fire reached the edge of the fire area at Jul 16 22:24 UTC and the model stopped. `wrf-next` reports this as *domain edge*, not as a failure. To go further, make a variation with a larger fire area (`fire_cells`) and run it with `--wps`.
