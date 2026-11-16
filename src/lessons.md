---
title: What went wrong, what we learnt
kicker: Lessons
lead: Every incident of the October campaign and the November WPS work, what actually caused it, and the rule it turned into. None of them were science decisions; nearly all were machine decisions made by hand.
---

## Incidents and the rules they produced

| What happened | What it really was | Rule it produced |
| --- | --- | --- |
| Long ended with Slurm exit 137 on every node type | First read as a node kill, then as a time limit. It was WRF-Fire stopping by MPI_Abort: "Fire has reached domain boundary" at 22:24:11 on July 16 | Classify every ending from **all** ranks' logs, not the exit code. "Domain edge" is its own ending, not a crash |
| A second, hand-submitted job started in the same run folder | Nothing stopped two jobs writing the same files | One lock file per run folder; a second job exits in its first second |
| Continuation jobs started after their run had finished | Continuations queued ahead and never cancelled | Every ending cancels or releases its continuation; a sweeper catches jobs that die silently |
| Ignition at the wrong time in some early runs | People edited dates and ignition offsets in the namelist by hand | Dates and ignition are locked, derived from the fire record; the offset in seconds is computed, never typed |
| WRF stopped with `fuel category out of bounds` | Fuel code 204 needs 54 categories; the built-in table has 53 | `namelist.fire` with `nfuelcats = 54`; a smoke run catches it in ten minutes instead of a day |
| Sapphire Rapids jobs never started after day two | Group fairshare: heavy use moved us to the back of the queue | Race the node types; the first to start runs |
| Smaller Eaton jobs waited longer than bigger ones | The wait was set by priority, not size | Being "greedy" was insisting on the best node type, not asking for many nodes |
| A cleanup re-run would have overwritten an archive | A fixed output name | Every derived file gets a time-stamped name; dry run first |
| geogrid `End of record` | A path-length bug in an error message | Data paths under 60 characters |
| metgrid hit its time limit | Eight ranks each reading every 3.4 GB HRRR file | WPS on one core; walltime from the number of weather hours |
| A fire table with three dead fuel paths | `halt_on_missing=no` with `fill_missing=0` hides it | `halt_on_missing=yes`; a gate checks every path in the table exists |

## Things that worked

- **Instrumenting everything from the start.** WRF's own timing lines plus a light node sampler were enough for every result on this site; nothing needed hardware counters.
- **Measuring per unit of work.** Dividing by column updates turned four very different fires into one model.
- **Keeping inputs when cleaning up.** After the campaign we deleted every WRF output and restart (group usage fell to about 3.7 TB) but kept every input. That is what let us check NCAR's Canyon files against our own WPS later.
- **Reading the outputs instead of asking.** `met_em` attributes and logs tell you exactly how an input was made.

## What we believe now

<div class="key" markdown="1">
<span class="callout-title">Principles</span>

1. **People own the science; the system owns the machine.** Fire choice, WRF settings and research variants are human decisions. Node type, ranks, walltime, continuations and checks are rules.
2. **Failures are data.** Every ending is classified and logged; a crash, a timeout and a fire leaving its domain are different facts.
3. **Nothing is overwritten.** A new folder for every upload and every run, each with a manifest.
4. **Check cheaply before running expensively.** Ten minutes of smoke run beats a day in the queue and a crash.
5. **Stay on Slurm and bash.** No app, no new vocabulary; a few scripts that do the bookkeeping and then call `sbatch`.
</div>

These principles shaped [the workflow we designed](design.html).
