---
title: Skill file for coding agents
kicker: Running it safely
lead: One file, SKILL.md, that teaches a coding agent how to run any fire through the gating system - from building met_em files to reading gate E - and the rules it must keep: never delete, never hand-submit, ask before spending core-hours.
---

## What it is

`SKILL.md` is a plain Markdown file with a short header (a name and a one-line description of when to use it) followed by step-by-step instructions. Agents that support skills, such as Claude Code, read the header to know when the skill applies and load the rest when you ask for something it covers: "set up a run for the Bridge fire", "why did gate C fail on Canyon", "rerun Long with a bigger time step".

It ships with every release, at `/projects/academic/negarkhodoe/wrf/pipeline/current/SKILL.md`, so it always matches the commands installed. It is also in the repository: [`tools/wrfgate/SKILL.md`](https://github.com/utkrshkmr/wrf-manual/blob/main/tools/wrfgate/SKILL.md) ([raw](https://raw.githubusercontent.com/utkrshkmr/wrf-manual/main/tools/wrfgate/SKILL.md)).

## Installing it for your agent

**Claude Code on CCR** (personal skills folder; the link follows the release, so a new release updates the skill):

```bash
mkdir -p ~/.claude/skills/wrf-fire-gated-runs
ln -sfn /projects/academic/negarkhodoe/wrf/pipeline/current/SKILL.md ~/.claude/skills/wrf-fire-gated-runs/SKILL.md
```

**Claude Code for one project folder only:** the same link under `<folder>/.claude/skills/wrf-fire-gated-runs/SKILL.md`.

**Agents that read `AGENTS.md`** (Codex and others): put a line in your project's `AGENTS.md` telling the agent to read the file before any WRF-Fire work:

```bash
echo 'Before any WRF-Fire work, read and follow /projects/academic/negarkhodoe/wrf/pipeline/current/SKILL.md' >> /path/to/project/AGENTS.md
```

**Any other agent or chat assistant:** attach or paste the file at the start of the session.

The agent still needs `setup.sh` sourced in the shell it uses and a profile from `wrf-me`; the skill's step 0 checks both and asks you for your name and email if the profile is missing.

## What it tells the agent

| Part | Covers |
| --- | --- |
| Rules | never delete (use `wrf-setaside`), never `sbatch` WRF by hand, never edit locked files, ask before `wrf-submit`, `--replace`, `scancel` or setting aside, leave other people's jobs alone, never loosen a gate |
| Step 0–1 | environment and profile; what already exists for the fire, and where to start |
| Step W | building `met_em` with WPS on CCR when nothing exists: what to ask the human, domain rules, the one-core job, short paths |
| Steps 2–3 | the record and the inputs; a table of gate A and B failures with their fixes |
| Steps 4–5 | writing a spec that matches the inputs; gates C and D with their common failures |
| Steps 6–7 | sizing (rank cap, node types, walltime rule, the 72-hour limit), submitting, and reading gate E's four endings |
| Pitfalls | the CCR lessons: module set, one-core WPS, path length, `&share`, `srun` and stdin, spool copies of batch scripts, LANDFIRE anchors |

## The file

{{include:tools/wrfgate/SKILL.md}}
