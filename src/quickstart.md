---
title: Quick start
kicker: Start here
lead: Every fire is described by one short card: its name, ignition time and place, the window, the domains and a few model settings. Set yourself up once, write or copy a card, and the commands (or an AI chat) take it from there.
toc: no
---

## 1. Set yourself up (once)

```bash
echo 'source /projects/academic/negarkhodoe/wrf/pipeline/current/setup.sh' >> ~/.bashrc
source /projects/academic/negarkhodoe/wrf/pipeline/current/setup.sh
wrf-me --name "Your Name" --email you@buffalo.edu --mail END,FAIL
```

Your name goes on everything you create, and Slurm emails you when your jobs end or fail. `wrf-status` should now list the lab's fires.

## 2. Describe the fire as a card

A fire card is a short text file. Start from a blank one, or from a fire we have already run:

```bash
wrf-card --template > /projects/academic/negarkhodoe/wrf/people/$USER/work/bridge.card
wrf-card EATON_2025 > /projects/academic/negarkhodoe/wrf/people/$USER/work/eaton_variant.card
```

A filled card looks like this (the full list, with defaults and help, is in the template):

```text
name:                BRIDGE_2024
note:                first look, campaign physics
start:               2024-09-08 12:00
end:                 2024-09-10 00:00
ignition_time:       2024-09-08 21:00
ignition_lat:        34.30
ignition_lon:        -117.78
ignition_radius_m:   50
outer_cells:         54
outer_dx_m:          900
fire_cells:          217
fire_ratio:          9
fire_mesh_ratio:     4
weather:             HRRR
weather_interval_s:  3600
fuel_layer:          /projects/academic/negarkhodoe/wrf/static/landfire/LF2024/FBFM40
fuel_moisture:       0.08
fire_feedback:       1.0
base_spec:           CANYON_2025/campaign
```

`base_spec` is the fire whose physics and other settings are reused; the card overrides the times, domains, ignition and fire settings. Blank fields take the lab defaults.

## 3a. Let an AI chat guide you (easiest)

1. Open the [skill page](skill.html) and press **Copy the skill**.
2. Paste it into a new chat with Claude, ChatGPT or any assistant, and paste your card underneath with one line saying what you want, for example *"Run this fire."* or *"Run this fire with fire_feedback 0 as a one-way coupling test."*
3. Paste the commands it gives you into your CCR terminal, and paste the output back. Repeat.

It checks the card with you, asks before anything that spends core-hours, never deletes anything, and looks up errors in this manual.

## 3b. Or type the commands

```bash
wrf-card --make /projects/academic/negarkhodoe/wrf/people/$USER/work/bridge.card --wps
```

This checks the card (ignition inside the fire domain, domain sizes, times), records the fire, writes `namelist.wps` and a spec into `people/$USER/work/BRIDGE_2024_<time>/`, and submits WPS. When WPS ends, its `met_em` files are registered and checked (gates A and B) automatically. For a fire that already has `met_em` files, leave out `--wps`: it prints the next command instead.

Then, using the folder names each command prints:

```bash
wrf-gate C BRIDGE_2024 /projects/academic/negarkhodoe/wrf/people/$USER/work/BRIDGE_2024_<time>/spec
wrf-gate D BRIDGE_2024 /projects/academic/negarkhodoe/wrf/fires/BRIDGE_2024/runs/<stamp>_gateC_spec
wrf-submit BRIDGE_2024 /projects/academic/negarkhodoe/wrf/people/$USER/work/BRIDGE_2024_<time>/spec --nodes 1 --ranks 25 --time 48:00:00
```

Each refuses, with a reason, if the step before it did not pass. To read a step's result, `cat` the `GATES.txt` in the folder it printed.

## 4. Keep an eye on your jobs

```bash
wrf-watch --mine
wrf-watch --active --every 120
```

One line per job: queued or running, how far the simulation has got, seconds per step, time left, and warnings such as **won't finish in its time limit** or **log idle** (possibly stuck).

## Cheat sheet

| I want to | Command |
| --- | --- |
| see all fires, or one | `wrf-status`, `wrf-status FIRE` |
| see a fire's full settings | `wrf-card FIRE` |
| start a new fire or a variant | `wrf-card --template` or `wrf-card FIRE`, edit, then `wrf-card --make CARD [--wps]` |
| watch my jobs | `wrf-watch --mine` (add `--every 120` to refresh) |
| check real.exe, then a 2-minute run | `wrf-gate C FIRE SPEC_FOLDER`, then `wrf-gate D FIRE GATE_C_FOLDER` |
| start the real run | `wrf-submit FIRE SPEC_FOLDER --nodes N --ranks R --time HH:MM:SS` |
| change my email settings | `wrf-me --mail END,FAIL` (or `ALL`, or `NONE`) |
| get rid of something | `wrf-setaside PATH "why"` (moved, never deleted) |

## Where next

<div class="cards" markdown="0">
<a class="card" href="example.html"><span class="k">Example</span><h3>The fires we have run</h3><p>Each one as its card, and how to run it again.</p></a>
<a class="card" href="gates.html"><span class="k">Reference</span><h3>The gating system</h3><p>What each gate checks, the folders, profiles, monitoring and the log.</p></a>
<a class="card" href="extend.html"><span class="k">Advanced</span><h3>Research inputs</h3><p>Fuel moisture, fuel maps, ignitions, terrain, coupling.</p></a>
</div>
