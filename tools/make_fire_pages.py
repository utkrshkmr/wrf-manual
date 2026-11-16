"""Write one page per fire we have run (src/fire-<slug>.md). Plain-language, setup-and-run only."""
import pathlib
SRC = pathlib.Path(__file__).resolve().parent.parent / "src"
W = "/projects/academic/negarkhodoe/wrf"

FIRES = [
 dict(slug="eaton", name="EATON_2025", title="Eaton 2025",
      about="Los Angeles County, January 2025. Ignited in the evening of January 7 local time, driven by Santa Ana winds. The largest fire we run: it needs many nodes.",
      card=[("start", "2025-01-08 00:00"), ("end", "2025-01-08 17:00"), ("ignition_time", "2025-01-08 02:18"),
            ("ignition_lat", "34.186040"), ("ignition_lon", "-118.093250"), ("ignition_radius_m", "100"),
            ("outer_cells", "450"), ("outer_dx_m", "900"), ("fire_cells", "811"), ("fire_ratio", "9"), ("fire_mesh_ratio", "4"),
            ("weather_interval_s", "10800"), ("fuel_layer", f"{W}/static/landfire/LF2024/FBFM40"), ("fuel_moisture", "0.08"),
            ("time_step_s", "3"), ("base_spec", "EATON_2025/campaign")],
      facts=[("Simulated", "17 hours, Jan 8 00:00 to 17:00 UTC"), ("Ignition", "Jan 8 02:18 UTC (Jan 7, 6:18 pm local) at 34.18604, −118.09325"),
             ("Fire area", "81 km square at 100 m"), ("Fuel map", "LANDFIRE 2024"), ("Size of the run", "24 whole nodes, about 1,530 processes; about 13–24 hours")],
      notes=["`wrf-next` will suggest 24 Sapphire Rapids nodes. That is a large request (tens of thousands of core-hours): check with the lab before you answer *y*.",
             "Its first process needs a lot of memory, so it only runs on the 512 GB nodes; `wrf-next` asks for those automatically."]),
 dict(slug="canyon", name="CANYON_2025", title="Canyon 2025",
      about="Ventura and Los Angeles counties, August 2025. A small, quick fire: one node is enough, and it is the example used throughout this site.",
      card=[("start", "2025-08-07 18:00"), ("end", "2025-08-09 00:00"), ("ignition_time", "2025-08-07 20:25"),
            ("ignition_lat", "34.439636"), ("ignition_lon", "-118.735548"),
            ("outer_cells", "54"), ("outer_dx_m", "900"), ("fire_cells", "217"), ("fire_ratio", "9"), ("fire_mesh_ratio", "4"),
            ("weather_interval_s", "3600"), ("fuel_layer", f"{W}/static/landfire/LF2024/FBFM40"), ("base_spec", "CANYON_2025/campaign")],
      facts=[("Simulated", "30 hours, Aug 7 18:00 to Aug 9 00:00 UTC"), ("Ignition", "Aug 7 20:25 UTC at 34.439636, −118.735548"),
             ("Grids", "outer 54 × 54, fire 217 × 217"), ("Fuel map", "LANDFIRE 2024"), ("Size of the run", "1 node, 25 processes")],
      notes=[]),
 dict(slug="cranston", name="CRANSTON_2018", title="Cranston 2018",
      about="Riverside County, July 2018. A mid-sized fire on one node, with a long run time.",
      card=[("start", "2018-07-25 16:00"), ("end", "2018-07-26 12:00"), ("ignition_time", "2018-07-25 18:41"),
            ("ignition_lat", "33.711295"), ("ignition_lon", "-116.769312"),
            ("outer_cells", "71x64"), ("fire_cells", "370x307"),
            ("fuel_layer", f"{W}/static/landfire/LF2016/FBFM40"), ("base_spec", "CRANSTON_2018/campaign")],
      facts=[("Simulated", "20 hours, Jul 25 16:00 to Jul 26 12:00 UTC"), ("Ignition", "Jul 25 18:41 UTC at 33.711295, −116.769312"),
             ("Grids", "outer 71 × 64, fire 370 × 307"), ("Fuel map", "LANDFIRE 2016"), ("Size of the run", "1 node, 36 processes; about 30–42 hours")],
      notes=["It takes more than a day and a half on the slower nodes; `wrf-next` sizes the time limit from its test run."]),
 dict(slug="long", name="LONG_2024", title="Long 2024",
      about="Kern County, July 2024. One node; in our earlier run the fire reached the edge of its simulated area before the end.",
      card=[("start", "2024-07-15 20:00"), ("end", "2024-07-17 00:00"), ("ignition_time", "2024-07-15 21:30"),
            ("ignition_lat", "35.830005"), ("ignition_lon", "-118.175345"),
            ("outer_cells", "60x63"), ("fire_cells", "271x298"),
            ("fuel_layer", f"{W}/static/landfire/LF2023/FBFM40"), ("base_spec", "LONG_2024/campaign")],
      facts=[("Simulated", "28 hours, Jul 15 20:00 to Jul 17 00:00 UTC"), ("Ignition", "Jul 15 21:30 UTC at 35.830005, −118.175345"),
             ("Grids", "outer 60 × 63, fire 271 × 298"), ("Fuel map", "LANDFIRE 2023"), ("Size of the run", "1 node, 36 processes")],
      notes=["**It stops early, and that is expected.** In our earlier run the fire reached the edge of the fire area at Jul 16 22:24 UTC and the model stopped. `wrf-next` reports this as *domain edge*, not as a failure. To go further, make a variation with a larger fire area (`fire_cells`) and run it with `--wps`."]),
]


def page(f):
    F, s = f["name"], f["slug"]
    card = "\n".join(f"{k + ':':<20} {v}" for k, v in [("name", F)] + f["card"])
    facts = "\n".join(f"| {a} | {b} |" for a, b in f["facts"])
    out = f"""---
title: {f['title']}
kicker: Fires we have run · {F}
lead: {f['about']}
---

| | |
| --- | --- |
{facts}

Its files are already in the shared folder, checked and ready. You only need to have [set up](start.html) once.

## Run it

**1. Start it.**

```bash
wrf-next {F}
```

It checks everything and submits the first job. You get an email when it ends.

**2. After each email, run the same command again.**

```bash
wrf-next {F}
```

Each time, it reports how the last step went and starts the next one. There are four steps: the weather and map files (already done for this fire), the start files, a 2-minute test run, and the simulation itself.

**3. Before the simulation, it asks you.** It shows the size it suggests (nodes, processes, time limit and the most it can cost) and waits for *y*.

**4. While it runs**, `wrf-next {F}` shows how far it has got and the time left.

**5. When it is done**, `wrf-next {F}` says how it ended and where the results are: the `wrfout_*` files in the run folder it prints.

If a step fails, `wrf-next` prints what is wrong in plain words. If it is not clear what to do, paste the output into the [AI chat helper](skill.html).

## Its settings

These are the settings that define the fire. `wrf-card {F}` prints all of them, including everything not shown here.

```text
{card}
```

## Try a variation

Change one setting, for example drier fuel, and run it as your own copy:

```bash
wrf-card {F} > {W}/people/$USER/work/{s}_dry.card
nano {W}/people/$USER/work/{s}_dry.card
wrf-card --make {W}/people/$USER/work/{s}_dry.card
wrf-next {F}
```

In the editor, change the line you want (for example `fuel_moisture: 0.05`) and the `note:` line, then save (Ctrl-O, Enter) and exit (Ctrl-X). `wrf-next` always uses your newest copy. Settings you can change are listed on [Your own fire](newfire.html#5-changing-settings).
"""
    if f["notes"]:
        out += "\n## Good to know\n\n" + "\n".join(f"- {n}" for n in f["notes"]) + "\n"
    (SRC / f"fire-{s}.md").write_text(out)


if __name__ == "__main__":
    for f in FIRES:
        page(f)
    print("wrote", len(FIRES), "fire pages")
