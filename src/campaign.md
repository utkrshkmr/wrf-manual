---
title: The scaling campaign
kicker: Our work · October 18–25, 2026
lead: To size runs from data instead of by hand, we ran four fires on all three of CCR's node types at several rank counts, with every run instrumented. 48 runs were planned; 25 were usable when we stopped ahead of CCR's October 27–28 downtime.
---

## The question

Every WRF-Fire run needs a node type, a node count, a rank count and a walltime. Choosing them by hand had cost us failed jobs, idle cores and long queues. The campaign measured what each choice actually buys, so the choice can be made by a rule.

## The sweep

| Fire | Window | Column updates per step | Rank cap | Rank ladder (each on all three node types) | Simulated |
| --- | --- | --- | --- | --- | --- |
| Canyon 2025 | Aug 7 18:00 → Aug 9 00:00 | 422,713 | 25 | 25 · 16 · 12 · 6 | full 30 h; 5 h at 12 and 6 |
| Cranston 2018 | Jul 25 16:00 → Jul 26 12:00 | 1,020,636 | 36 | 36 · 25 · 18 · 9 | full 20 h; 5 h at 18 and 9 |
| Long 2024 | Jul 15 20:00 → Jul 17 00:00 | 725,368 | 36 | 36 · 25 · 18 · 9 | full 28 h; 5 h at 18 and 9 |
| Eaton 2025 | Jan 8 00:00 → 17:00 | 6,106,501 | 2,025 | 24 · 12 · 6 · 3 whole nodes | first 5 h only |

**Column updates per step** is our unit of work: every grid cell of every domain, times the sub-steps the fine domain takes per coarse step. It is what WRF does per parent time step, independent of the fire. Eaton does about 14 times Canyon's work per step.

| Node type | CPU | Cores | Memory | Nodes |
| --- | --- | --- | --- | --- |
| Cascade Lake | Xeon Gold 6230 | 40 | 187 GB | 125 |
| Ice Lake | Xeon Gold 6330 | 56 | 512 GB | 56 |
| Sapphire Rapids | Xeon Gold 6448Y | 64 | 512 GB | 83 |

Rules of the sweep:

- **Whole nodes, one run per node set.** No other job shared a node, so timings were not disturbed by other users.
- **Full and short windows never mixed.** The 5-hour windows are mostly before ignition and cheaper per step, so they were compared only with each other.
- **One reference run per fire kept its output.** The others kept timings and logs only, so 48 runs fit in the project quota.
- **16 active at a time**, to stay inside the group's limits.

## Instrumentation

{{fig:probes|**What was measured.** None of the probes slows the run: WRF prints its timing lines anyway, and the sampler starts after WRF has claimed its cores.}}

## What came out

<div class="cards" markdown="0">
<a class="card" href="scaling.html"><span class="k">Results</span><h3>Scaling and the elbow</h3><p>Eaton's elbow on Cascade Lake at about 1,060 ranks; small fires hit WRF's cap first.</p></a>
<a class="card" href="costmodel.html"><span class="k">Results</span><h3>Cost model and node formula</h3><p>One equation for all three machines, typical error 11%; a sizing rule within 1% for Cranston.</p></a>
<a class="card" href="queue.html"><span class="k">Results</span><h3>Queue waits and cost</h3><p>Sapphire Rapids is fastest and cheapest, but stopped starting for us after day two.</p></a>
<a class="card" href="lessons.html"><span class="k">Lessons</span><h3>What went wrong</h3><p>Duplicate jobs, leftover continuations, a fire leaving its domain.</p></a>
</div>
