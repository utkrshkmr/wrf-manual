---
title: Quick start
kicker: Start here
lead: From nothing to a running fire in about ten minutes of typing. Install once for the lab, set yourself up once, then either let an AI chat guide you or type the five commands yourself.
toc: no
---

## 1. Install (once for the whole lab)

Skip this step if `/projects/academic/negarkhodoe/wrf/pipeline/current` already exists: someone has installed it.

```bash
git clone https://github.com/utkrshkmr/wrf-manual.git /projects/academic/negarkhodoe/utkarshk/wrf-manual
bash /projects/academic/negarkhodoe/utkarshk/wrf-manual/tools/wrfgate/install.sh
```

To update later: `git -C /projects/academic/negarkhodoe/utkarshk/wrf-manual pull`, then run `install.sh` again. Old versions are kept, so jobs already queued are not affected.

## 2. Set yourself up (once per person)

```bash
echo 'source /projects/academic/negarkhodoe/wrf/pipeline/current/setup.sh' >> ~/.bashrc
source /projects/academic/negarkhodoe/wrf/pipeline/current/setup.sh
wrf-me --name "Your Name" --email you@buffalo.edu --mail END,FAIL
```

Your name goes on everything you create, and Slurm emails you when your jobs end or fail.

Check it worked:

```bash
wrf-status
```

You should see a table of fires (it may be empty).

## 3a. The easy way: let an AI chat guide you

1. Open the [skill page](skill.html) and press **Copy the skill**.
2. Paste it into a new chat with Claude, ChatGPT or any assistant, and write underneath what you want, e.g. *"Run CANYON_2025 with the campaign settings"* or *"Set up the Bridge fire from 2024 from scratch"*.
3. Paste the commands it gives you into your CCR terminal, and paste the output back. Repeat.

It asks before anything that spends core-hours, never deletes anything, and looks up errors in this manual for you.

## 3b. Or type it yourself

For a fire that already has a record, inputs and a spec (all the fires we have run; see `wrf-status`):

```bash
wrf-gate C CANYON_2025 /projects/academic/negarkhodoe/wrf/fires/CANYON_2025/specs/campaign
```

When the email says it ended, use the folder name it printed:

```bash
wrf-gate D CANYON_2025 /projects/academic/negarkhodoe/wrf/fires/CANYON_2025/runs/<stamp>_gateC_campaign
```

When that one ends too, start the real run:

```bash
wrf-submit CANYON_2025 /projects/academic/negarkhodoe/wrf/fires/CANYON_2025/specs/campaign --nodes 1 --ranks 25 --time 48:00:00
```

Each command refuses, with a reason, if the step before it did not pass. To read a step's result, `cat` the `GATES.txt` in the folder it printed.

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
| watch my jobs | `wrf-watch --mine` (add `--every 120` to refresh) |
| add a new fire | `wrf-new-fire FIRE --start … --end … --ignition … --lat … --lon …` |
| add its `met_em` files | `wrf-add-inputs FIRE /path/to/met_em_folder` |
| check real.exe, then a 2-minute run | `wrf-gate C FIRE SPEC_FOLDER`, then `wrf-gate D FIRE GATE_C_FOLDER` |
| start the real run | `wrf-submit FIRE SPEC_FOLDER --nodes N --ranks R --time HH:MM:SS` |
| change my email settings | `wrf-me --mail END,FAIL` (or `ALL`, or `NONE`) |
| get rid of something | `wrf-setaside PATH "why"` (moved, never deleted) |

## Where next

<div class="cards" markdown="0">
<a class="card" href="example.html"><span class="k">Example</span><h3>Every fire we have run</h3><p>Eaton, Canyon, Cranston, Long and the NCAR fires, command by command.</p></a>
<a class="card" href="gates.html"><span class="k">Reference</span><h3>The gating system</h3><p>What each gate checks, the folders, profiles, monitoring and the ledger.</p></a>
<a class="card" href="env.html"><span class="k">Manual</span><h3>WPS to WRF-Fire</h3><p>Every input and variable, for making a new fire's files from scratch.</p></a>
</div>
