---
title: Eaton 2025
kicker: Fires we have run · EATON_2025
lead: Los Angeles County, January 2025. Ignited in the evening of January 7 local time, driven by Santa Ana winds. The largest fire we run: it needs many nodes.
---

| | |
| --- | --- |
| Simulated | 17 hours, Jan 8 00:00 to 17:00 UTC |
| Ignition | Jan 8 02:18 UTC (Jan 7, 6:18 pm local) at 34.18604, −118.09325 |
| Fire area | 81 km square at 100 m |
| Fuel map | LANDFIRE 2024 |
| Size of the run | 24 whole nodes, about 1,530 processes; about 13–24 hours |

Its files are already in the shared folder, checked and ready. You only need to have [set up](start.html) once.

## Run it

**1. Start it.**

```bash
wrf-next EATON_2025
```

It checks everything and submits the first job. You get an email when it ends.

**2. After each email, run the same command again.**

```bash
wrf-next EATON_2025
```

Each time, it reports how the last step went and starts the next one. There are four steps: the weather and map files (already done for this fire), the start files, a 2-minute test run, and the simulation itself.

**3. Before the simulation, it asks you.** It shows the size it suggests (nodes, processes, time limit and the most it can cost) and waits for *y*.

**4. While it runs**, `wrf-next EATON_2025` shows how far it has got and the time left.

**5. When it is done**, `wrf-next EATON_2025` says how it ended and where the results are: the `wrfout_*` files in the run folder it prints.

If a step fails, `wrf-next` prints what is wrong in plain words. If it is not clear what to do, paste the output into the [AI chat helper](skill.html).

## Its settings

These are the settings that define the fire. `wrf-card EATON_2025` prints all of them, including everything not shown here.

```text
name:                EATON_2025
start:               2025-01-08 00:00
end:                 2025-01-08 17:00
ignition_time:       2025-01-08 02:18
ignition_lat:        34.186040
ignition_lon:        -118.093250
ignition_radius_m:   100
outer_cells:         450
outer_dx_m:          900
fire_cells:          811
fire_ratio:          9
fire_mesh_ratio:     4
weather_interval_s:  10800
fuel_layer:          /projects/academic/negarkhodoe/wrf/static/landfire/LF2024/FBFM40
fuel_moisture:       0.08
time_step_s:         3
base_spec:           EATON_2025/campaign
```

## Try a variation

Change one setting, for example drier fuel, and run it as your own copy:

```bash
wrf-card EATON_2025 > /projects/academic/negarkhodoe/wrf/people/$USER/work/eaton_dry.card
nano /projects/academic/negarkhodoe/wrf/people/$USER/work/eaton_dry.card
wrf-card --make /projects/academic/negarkhodoe/wrf/people/$USER/work/eaton_dry.card
wrf-next EATON_2025
```

In the editor, change the line you want (for example `fuel_moisture: 0.05`) and the `note:` line, then save (Ctrl-O, Enter) and exit (Ctrl-X). `wrf-next` always uses your newest copy. Settings you can change are listed on [Your own fire](newfire.html#5-changing-settings).

## Good to know

- `wrf-next` will suggest 24 Sapphire Rapids nodes. That is a large request (tens of thousands of core-hours): check with the lab before you answer *y*.
- Its first process needs a lot of memory, so it only runs on the 512 GB nodes; `wrf-next` asks for those automatically.
