---
title: Running it on Slurm
kicker: WRF mechanics · Operations
lead: The whole chain as batch jobs on CCR, how many ranks a fire can use, how long to ask for, how to survive the 72-hour limit, and what to check after each phase.
---

## The whole chain as two jobs

WPS is serial and short, so it runs as one single-core job. real.exe and wrf.exe run as an MPI job that depends on it.

```bash
cat > wps.sbatch <<'EOF'
#!/bin/bash
#SBATCH -p general-compute --qos=general-compute
#SBATCH -N 1 -n 1 --mem=16G -t 03:00:00
#SBATCH -o wps_%j.out
module load gcc/11.2.0 openmpi/4.1.1 wps/4.6.0-dmpar
cd /path/to/canyon_run
srun -n 1 geogrid.exe && tail -1 geogrid.log
ungrib.exe && tail -1 ungrib.log
srun -n 1 metgrid.exe && tail -1 metgrid.log
EOF

cat > wrf.sbatch <<'EOF'
#!/bin/bash
#SBATCH -p general-compute --qos=general-compute
#SBATCH -N 1 --ntasks=25 --exclusive -t 40:00:00
#SBATCH --constraint=SAPPHIRE-RAPIDS-IB
#SBATCH -o wrf_%j.out
module load gcc/11.2.0 openmpi/4.1.1 wps/4.6.0-dmpar
cd /path/to/canyon_run
srun real.exe && grep -q "SUCCESS COMPLETE REAL_EM" rsl.error.0000 || exit 1
srun wrf.exe
EOF

j=$(sbatch --parsable wps.sbatch); sbatch --dependency=afterok:$j wrf.sbatch
```

Launch MPI programs with `srun` inside a batch job. Starting the MPI-built WPS programs bare inside an `srun` step on CCR loses the step's connection (`Connection refused`).

## How many ranks

{{fig:decomp|**The decomposition cap.** WRF splits every domain over the same set of ranks and refuses a split that leaves any rank fewer than 10 points in either direction. Small fires are capped by their small outer domain.}}

From our campaign ([results](scaling.html)):

- **Small fires: run at the cap, on one whole node.** Every step up to the cap was still 76–94% efficient, and CCR charges the whole node, so fewer ranks cost more core-hours, not fewer.
- **Large fires: up to the elbow or the cap, whichever comes first.** For Eaton, Cascade Lake's elbow is about 1,060 ranks; on Ice Lake and Sapphire Rapids the 2,025-rank cap comes first.
- To raise a small fire's cap, enlarge or refine the outer domain. That is a science decision, so make it deliberately.

## How long to ask for

Measure, don't guess. A two-minute test run gives the seconds per step; `rsl.error.0000` prints one timing line per step:

```bash
grep 'Timing for main' rsl.error.0000 | tail -20 | awk '{s+=$(NF-2)} END {print s/NR, "s per step"}'
```

Then walltime = seconds per step × steps × 1.15 + 1 hour, where steps = simulated seconds ÷ `time_step`. Steps get slower after ignition, as the fire model's work grows; measure after ignition if you can. For a fire never run before, use × 1.3. [The node formula](costmodel.html#the-node-formula) does this from the grid alone.

## The 72-hour limit and restarts

CCR's `general-compute` jobs end at 72 hours. A longer run is a chain of jobs, each resuming from the last restart file:

1. Set `restart_interval` (minutes) so a restart file is written well before the limit, for example every 6 simulated hours.
2. For the next job, set `restart = .true.` and `start_*` to the restart file's time, and keep everything else the same.
3. Queue it with `--dependency=afterany:<job>`, and **cancel it if the first job finished the run**. Leftover continuations were one of our campaign's incidents ([what went wrong](lessons.html)).

Each continuation waited 12–24 hours in the queue during our campaign, so a set-up that fits one job is worth a lot.

## What to check after each phase

| After | Check | Command |
| --- | --- | --- |
| geogrid | success; fire fields present; the folders each field read | `tail -1 geogrid.log; grep -i 'NFUEL\|ZSF' geogrid.log` |
| ungrib | success; every hour in the inventory | `grep -c Inventory ungrib.log` |
| metgrid | success; files = hours × domains; fire flags | `ls met_em.d0* \| wc -l; ncdump -h met_em.d02.* \| grep FLAG_` |
| real.exe | success; fuel codes in range; terrain; `FMC_G` | the [field check](real.html#checking-the-fire-fields) |
| first minutes of wrf.exe | ignition at the right time; no CFL warnings; seconds per step | `grep -iE 'ignit\|cfl' rsl.error.0000` |
| the end | `SUCCESS COMPLETE WRF` in rank 0's log; or which ending it was | see [failure modes](reference.html#failure-modes) |

## Ending classes

A WRF-Fire job ends in one of four ways, and each needs a different response:

| Ending | How to recognize it | Response |
| --- | --- | --- |
| Finished | `SUCCESS COMPLETE WRF` in `rsl.error.0000` | Cancel any queued continuation |
| Fire reached the domain edge | `reached domain boundary` in any rank's log; Slurm exit 137 (MPI_Abort) | Not a crash: the run is over. Enlarge or move the fire domain, or end the window earlier |
| WRF crash | `cfl`, `NaN` or a segfault in any rank's log | Look at the time and place; often a smaller `time_step` or `w_damping = 1` |
| Killed with clean logs | Slurm `TIMEOUT`, `OUT_OF_MEMORY`, or a node failure | Resume from the newest restart; more memory or more time |

Always read **all** ranks' logs (`grep -l <pattern> rsl.error.*`). The rank that hits a problem is often not rank 0.
