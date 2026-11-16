---
title: Your own fire
kicker: Step 2
lead: Answer six questions about the fire, then run the same command after each email until it is done. Nothing else to edit by hand.
---

## 1. Describe the fire

```bash
wrf-card --new /projects/academic/negarkhodoe/wrf/people/$USER/work/bridge.card
```

It asks six questions. Have these ready:

| Question | Example answer |
| --- | --- |
| A short name, capitals with the year | `BRIDGE_2024` |
| When it ignited, local California time | `2024-09-08 14:30` |
| Where it ignited, latitude and longitude (right-click the spot in Google Maps to copy them) | `34.2997` and `-117.7756` |
| Hours of weather before ignition | press Enter for 2 |
| Hours to simulate after ignition | `30` |
| How far the fire spread from the ignition point, in km | `12` |

It then shows a summary, picks the fuel map for that year and a fire area big enough for the spread you gave, and saves your answers as the fire's **card**, a short text file. A finished session looks like this:

```text
Summary
  fire          BRIDGE_2024
  ignition      2024-09-08 21:30 UTC at 34.299700, -117.775600
  simulated     2024-09-08 19:00 to 2024-09-10 04:00 UTC (33 h)
  fire area     30.6 km square at 100 m, inside a 58 km area at 900 m
  fuel map      LANDFIRE 2023
  weather       HRRR, hourly

Saved the card: /projects/academic/negarkhodoe/wrf/people/ukumar/work/bridge.card
```

## 2. Get its weather

```bash
wrf-card --weather /projects/academic/negarkhodoe/wrf/people/$USER/work/bridge.card
```

It downloads the hourly weather (HRRR) for the simulated period into the lab's shared weather folder, skipping hours already there. It takes a few minutes per hour of weather, so leave it running. If some files fail, run it again.

## 3. Make the fire

```bash
wrf-card --make /projects/academic/negarkhodoe/wrf/people/$USER/work/bridge.card --wps
```

It checks the card (for example that the ignition sits well inside the fire area), registers the fire, writes all the model settings, and starts the job that builds the weather and map files. You get an email when that job ends.

## 4. Run it

After each email, run:

```bash
wrf-next BRIDGE_2024
```

Each time it says how the last step went and starts the next:

| Step | What happens | Usual time |
| --- | --- | --- |
| 1. Weather and map files | started by step 3 above | 1–3 hours |
| 2. Start files | prepares the model's first state | under 1 hour |
| 3. Test run | 2 minutes of simulated time, to catch problems early | under 1 hour |
| 4. The simulation | asks you first, showing its size and cost | hours to days |

Queue waits come on top of these times. While the simulation runs, `wrf-next BRIDGE_2024` shows how far it has got and the time left. When it ends, it says how it ended and where the results are.

If a step fails, `wrf-next` prints what is wrong. The usual fix is to correct one line of the card (step 5) and make it again. If it is not clear, paste the output into the [AI chat helper](skill.html).

## 5. Changing settings

Open the card in an editor, change a line, save, and make it again:

```bash
nano /projects/academic/negarkhodoe/wrf/people/$USER/work/bridge.card
wrf-card --make /projects/academic/negarkhodoe/wrf/people/$USER/work/bridge.card
wrf-next BRIDGE_2024
```

In `nano`: change the value, then Ctrl-O, Enter to save and Ctrl-X to exit. Add `--wps` to the `--make` line only when you changed a line marked *new weather and map files* below.

| Line | What it means | Example |
| --- | --- | --- |
| `note` | a few words about this run, saved with it | `drier fuel test` |
| `fuel_moisture` | how wet the dead fuel is, as a fraction | `0.05` (5%, drier) |
| `fire_feedback` | 1 = the fire changes the wind, 0 = it does not | `0` |
| `slope_factor` | how strongly slope speeds the fire, 1 = normal | `1.5` |
| `ignition_radius_m` | size of the first burning circle, in metres | `100` |
| `ignition_lat`, `ignition_lon` | where it starts (must stay inside the fire area) | |
| `ignition_time` | when it starts, UTC (must stay inside the simulated period) | |
| `start`, `end` | the simulated period, UTC | *new weather and map files* |
| `fire_cells` | size of the fire area, in 100 m cells per side | *new weather and map files* |
| `outer_cells` | size of the surrounding area, in 900 m cells per side | *new weather and map files* |

Each `--make` keeps the earlier versions; `wrf-next` uses your newest.

## Where things are

| What | Where |
| --- | --- |
| your cards and settings | `/projects/academic/negarkhodoe/wrf/people/$USER/work/` |
| the fire's runs and results | `/projects/academic/negarkhodoe/wrf/fires/BRIDGE_2024/runs/` |
| all your jobs | `wrf-watch --mine` |
