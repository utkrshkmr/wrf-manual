"""Write one example page per fire (src/fire-<slug>.md) from the facts below.
Values marked None are not known to this site yet: the page says so and shows the command that prints them."""
import pathlib
SRC = pathlib.Path(__file__).resolve().parent.parent / "src"
W = "/projects/academic/negarkhodoe/wrf"

FIRES = [
 dict(slug="eaton", name="EATON_2025", title="Eaton 2025",
      lead="The largest fire we run: an 81 km fire domain at 100 m, 2,025-rank cap, and a full run that needs 24 whole nodes. Ignited in the evening of January 7 local time, in Santa Ana winds.",
      card=dict(start="2025-01-08 00:00", end="2025-01-08 17:00", ignition_time="2025-01-08 02:18", ignition_lat="34.186040", ignition_lon="-118.093250",
                ignition_radius_m="100", outer_cells="450", outer_dx_m="900", fire_cells="811", fire_ratio="9", fire_start_i="180", fire_start_j="180",
                fire_mesh_ratio="4", weather_interval_s="10800", fuel_layer=f"{W}/static/landfire/LF2024/FBFM40", fuel_moisture="0.08",
                fire_feedback="1", time_step_s="3", base_spec="EATON_2025/campaign"),
      other="`fire_lsm_zcoupling = .true.` with `fire_lsm_zcoupling_ref = 60`, `fire_ignition_ros1 = 0.10`, ignition over 800 s (`fire_ignition_end_time1 = 9080`), `fire_upwinding = 9`, `fire_lsm_reinit = .true.`; physics `mp_physics = 6`, `ra_lw_physics = 4`, `ra_sw_physics = 1`, `sf_sfclay_physics = 1`, `sf_surface_physics = 2`, `bl_pbl_physics = 1, 0`, no cumulus; 60 vertical levels, weather with 41 levels and 9 soil levels every 3 hours.",
      source="the NCAR reference case `eaton_100_25_LF2024_WRF` and our campaign namelist",
      cap="2,025", run=dict(nodes="24", ranks="1530", time="24:00:00", constraint="SAPPHIRE-RAPIDS-IB"),
      sizing="In the campaign, 1,530 ranks on 24 Sapphire Rapids nodes ran at 1.16 s per step, and the first 5 simulated hours took 3.7 h. The fire makes later hours slower, so 24 h for all 17 leaves room under the 72-hour limit. That is 24 × 64 × 24 ≈ 36,900 core-hours charged.",
      gated="Gate D on one Sapphire Rapids node: add `--ranks 64 --constraint SAPPHIRE-RAPIDS-IB`, so the measured rate is for the node type the run will use.",
      notes=["Rank 0 used 168 GB in the campaign: whole 512 GB nodes (Sapphire Rapids or Ice Lake), never Cascade Lake.",
             "An earlier CCR namelist for Eaton had `fire_fuel_read = 0` (one fuel everywhere) instead of `-1` (the fuel map). The card prints `fire_fuel_read` under *Measured*; gate C fails if it is not `-1`."]),
 dict(slug="canyon", name="CANYON_2025", title="Canyon 2025",
      lead="Our worked example throughout the manual: a 21.6 km fire domain at 100 m on a 54 × 54 outer grid, HRRR weather every hour, LANDFIRE 2024 fuels. One node is enough.",
      card=dict(start="2025-08-07 18:00", end="2025-08-09 00:00", ignition_time="2025-08-07 20:25", ignition_lat=None, ignition_lon=None,
                center_lat="34.46681", center_lon="-118.70165", outer_cells="54", outer_dx_m="900", fire_cells="217", fire_ratio="9",
                fire_start_i="15", fire_start_j="15", fire_mesh_ratio="4", weather="HRRR", weather_interval_s="3600", vtable="Vtable.HRRR.prs",
                fuel_layer=f"{W}/static/landfire/LF2024/FBFM40", fuel_key="lf2024", terrain_layer=f"{W}/static/CA_1s", terrain_key="ca_1s",
                base_spec="CANYON_2025/campaign"),
      other=None, source="Nisha's `namelist.wps` (shown on [Domain design](domain.html)) and the campaign",
      cap="25", run=dict(nodes="1", ranks="25", time="48:00:00", constraint=""),
      sizing="25 ranks is WRF's cap for this grid (the 54 × 54 outer domain allows ⌊54/10⌋² = 25), so one whole node of any type. The campaign simulated the full 30 hours; use gate D's rate to check 48 h before submitting.",
      gated="Gate D on one node with the default ranks.",
      notes=["The fuel map in the NCAR/Nisha inputs matches our LANDFIRE 2024 copy at 97.3% cell by cell, because of how geogrid places the layer; gate B reports the number. The anchor study will settle which placement is right."]),
 dict(slug="cranston", name="CRANSTON_2018", title="Cranston 2018",
      lead="A mid-sized fire: 1.0 million column updates per step, a rank cap of 36, and a 20-hour window. One node; its measured run time is the anchor of our walltime rule.",
      card=dict(start="2018-07-25 16:00", end="2018-07-26 12:00", ignition_time=None, ignition_lat=None, ignition_lon=None, base_spec="CRANSTON_2018/campaign"),
      other=None, source="the campaign",
      cap="36", run=dict(nodes="1", ranks="36", time="48:00:00", constraint=""),
      sizing="36 ranks on one node. The full 20-hour run took 41.6 h in the campaign; on Sapphire Rapids it ran at 6.19 s per step, on Cascade Lake at 9.95 s. Ask for 48 h (Cascade Lake) or about 30 h on Sapphire Rapids (`--constraint SAPPHIRE-RAPIDS-IB`) after checking gate D's rate.",
      gated="Gate D on one node with the default ranks.",
      notes=["The fire's `met_em` folders exist in three versions (`CRANSTON`, `CRANSTON/met_files`, `CRANSTON/met_files1`); the registered input version names the one used. Check `wrf-status CRANSTON_2018`."]),
 dict(slug="long", name="LONG_2024", title="Long 2024",
      lead="A 28-hour window with a rank cap of 36. In the campaign the fire reached the edge of its fire domain before the end, which WRF treats as a stop.",
      card=dict(start="2024-07-15 20:00", end="2024-07-17 00:00", ignition_time=None, ignition_lat=None, ignition_lon=None, base_spec="LONG_2024/campaign"),
      other=None, source="the campaign",
      cap="36", run=dict(nodes="1", ranks="36", time="56:00:00", constraint="SAPPHIRE-RAPIDS-IB"),
      sizing="36 ranks on one Sapphire Rapids node; 56 h leaves room for the full window. Check against gate D's rate first.",
      gated="Gate D on one Sapphire Rapids node: `--constraint SAPPHIRE-RAPIDS-IB`.",
      notes=["**It reaches the domain edge.** In the campaign the fire hit the fire domain's boundary at Jul 16 22:24 and WRF stopped. Gate E classes that ending as *domain edge*, not a crash. To run past it, make a variant card with a larger `fire_cells` (and `outer_cells` if needed), which means new `met_em` files: `wrf-card --make … --wps`."]),
 dict(slug="airport", name="AIRPORT", title="Airport",
      lead="One of the three fires we have as NCAR `met_em` files only. It has not been run on CCR yet, so its card starts from the inputs and a base spec.",
      card=dict(start=None, end=None, ignition_time=None, ignition_lat=None, ignition_lon=None, base_spec="CANYON_2025/campaign"),
      other=None, source="the NCAR `met_em` files", cap=None, run=None, sizing=None, gated="Gate D on one node with the default ranks.", notes=[]),
 dict(slug="bradford", name="BRADFORD_BRANCH", title="Bradford Branch",
      lead="NCAR `met_em` files only; not yet run on CCR. Its card starts from the inputs and a base spec.",
      card=dict(start=None, end=None, ignition_time=None, ignition_lat=None, ignition_lon=None, base_spec="CANYON_2025/campaign"),
      other=None, source="the NCAR `met_em` files", cap=None, run=None, sizing=None, gated="Gate D on one node with the default ranks.", notes=[]),
 dict(slug="carmel", name="CARMEL", title="Carmel",
      lead="NCAR `met_em` files only; not yet run on CCR. Its card starts from the inputs and a base spec.",
      card=dict(start=None, end=None, ignition_time=None, ignition_lat=None, ignition_lon=None, base_spec="CANYON_2025/campaign"),
      other=None, source="the NCAR `met_em` files", cap=None, run=None, sizing=None, gated="Gate D on one node with the default ranks.", notes=[]),
]

ORDER = ["name", "start", "end", "ignition_time", "ignition_lat", "ignition_lon", "ignition_radius_m", "center_lat", "center_lon",
         "outer_cells", "outer_dx_m", "fire_cells", "fire_ratio", "fire_start_i", "fire_start_j", "fire_mesh_ratio",
         "weather", "weather_interval_s", "vtable", "fuel_layer", "fuel_key", "terrain_layer", "terrain_key",
         "fuel_moisture", "fire_feedback", "time_step_s", "base_spec"]


def card_text(f):
    c = dict(f["card"]); c["name"] = f["name"]
    lines = []
    for k in ORDER:
        if k in c:
            v = c[k] if c[k] is not None else "(printed by wrf-card)"
            lines.append(f"{k + ':':<20} {v}")
    return "\n".join(lines)


def page(f):
    F, D = f["name"], f"{W}/fires/{f['name']}"
    missing = [k for k, v in f["card"].items() if v is None]
    run = f["run"]
    sub = (f"wrf-submit {F} {D}/specs/campaign --nodes {run['nodes']} --ranks {run['ranks']} --time {run['time']}"
           + (f" --constraint {run['constraint']}" if run and run["constraint"] else "") + " --name rerun") if run else None
    dflag = " --ranks 64 --constraint SAPPHIRE-RAPIDS-IB" if f["slug"] == "eaton" else (" --constraint SAPPHIRE-RAPIDS-IB" if f["slug"] == "long" else "")
    out = [f"---\ntitle: {f['title']}\nkicker: Examples · {F}\nlead: {f['lead']}\n---\n"]
    out.append("## The fire card\n")
    out.append(f"Everything that defines this fire, from {f['source']}. The exact card, with every value read from the shared folder, is one command away:\n")
    out.append(f"```bash\nwrf-card {F}\n```\n")
    out.append(f"```text\n{card_text(f)}\n```\n")
    if missing:
        out.append(f"<div class=\"note\" markdown=\"1\">\nValues shown as *(printed by wrf-card)* ({', '.join('`' + m + '`' for m in missing)}) are in the fire's record in the shared folder but not yet on this page.\n</div>\n")
    if f["other"]:
        out.append(f"Other settings in its spec that the card carries over through `base_spec`: {f['other']}\n")
    if f["cap"]:
        out.append(f"Rank cap: **{f['cap']}**.\n")
    out.append("## Run it from an AI chat\n")
    out.append(f"Copy the [skill](skill.html) into a new chat, then paste underneath:\n")
    out.append(f"```text\nRun this fire. Here is its card:\n<paste the output of: wrf-card {F}>\n```\n")
    out.append("The assistant checks the card with you, then walks you through the commands below one at a time.\n")
    out.append("## Run it with the commands\n")
    out.append("**1. Check the fire and its inputs.**\n")
    out.append(f"```bash\nwrf-status {F}\nwrf-card {F}\n```\n")
    out.append("Read the card: times, ignition, domains, and under *Measured* the gate A and B results and `fire_fuel_read` (must be `-1`).\n")
    if f["slug"] in ("airport", "bradford", "carmel"):
        out.append(f"""**2. Make its spec from a card.** These fires have inputs but no spec of their own yet. Print the card, fill in what is missing from the record and the inputs, keep `base_spec: CANYON_2025/campaign` for the lab's physics, and make the spec without rerunning WPS:

```bash
wrf-card {F} > {W}/people/$USER/work/{f['slug']}.card
wrf-card --make {W}/people/$USER/work/{f['slug']}.card
```

It prints the spec folder (`people/$USER/work/{F}_<time>/spec`). Its domain sizes and grid spacing must match the `met_em` files; gate C checks them.

**3. Gate C (real.exe), then gate D (2-minute smoke run).**

```bash
wrf-gate C {F} {W}/people/$USER/work/{F}_<time>/spec
wrf-gate D {F} {D}/runs/<stamp>_gateC_spec
```

**4. Size and submit.** The rank cap is in gate C's `GATES.txt` (`C15`). Use one whole node at the cap if it is under 64, and set the walltime from gate D's seconds per step ([how](run.html)):

```bash
wrf-submit {F} {W}/people/$USER/work/{F}_<time>/spec --nodes 1 --ranks <cap> --time <HH:MM:SS>
```
""")
    else:
        out.append(f"""**2. Gate C: real.exe on the campaign spec.**

```bash
wrf-gate C {F} {D}/specs/campaign
```

It prints the run folder; Slurm emails you when it ends. Then `cat {D}/runs/<stamp>_gateC_campaign/GATES.txt`.

**3. Gate D: two minutes of wrf.exe.** {f['gated']}

```bash
wrf-gate D {F} {D}/runs/<stamp>_gateC_campaign{dflag}
```

**4. Submit.** {f['sizing']}

```bash
{sub}
```
""")
    out.append("**5. Watch it, and read how it ended.**\n")
    out.append(f"```bash\nwrf-watch {F}\ncat {D}/runs/<stamp>_rerun/GATES.txt\n```\n")
    out.append("Gate E runs inside the job when it ends: *finished*, *domain edge*, *crash* or *killed*, plus whether the first burning cell matches the card's ignition time and place.\n")
    out.append("## Make a variant\n")
    out.append(f"""Copy the card, change what you are testing (and the `note:` line), and make it. Times and domains unchanged means the existing inputs are reused, so no WPS:

```bash
wrf-card {F} > {W}/people/$USER/work/{f['slug']}_variant.card
wrf-card --make {W}/people/$USER/work/{f['slug']}_variant.card
```

Then gates C and D and `wrf-submit` on the spec folder it prints, with a `--name` that says what changed. Ideas: [fuel moisture](moisture.html), [one-way coupling](coupling.html), [slope sensitivity](terrain.html#the-slope-effect), [another ignition](ignitions.html).
""")
    if f["notes"]:
        out.append("## Good to know\n")
        out += [f"- {n}" for n in f["notes"]]
        out.append("")
    (SRC / f"fire-{f['slug']}.md").write_text("\n".join(out) + "\n")


if __name__ == "__main__":
    for f in FIRES:
        page(f)
    print("wrote", len(FIRES), "fire pages")
