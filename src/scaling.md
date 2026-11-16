---
title: Scaling and the elbow
kicker: Results
lead: More ranks make each step faster only up to a point. Our runs show where that point is for each machine, and that for our small fires WRF's own decomposition rule stops us long before we reach it.
---

## Two kinds of scaling

{{fig:strongweak|**Two questions.** Strong scaling answers how many ranks a given fire is worth. Weak scaling answers what a patch of a given size costs on a given machine. The [cost model](costmodel.html) uses the weak view.}}

## The elbow

Time per step behaves like Amdahl's law written in seconds: a serial part `s` that no extra rank shrinks, plus a parallel part `p` shared among `n` ranks.

<p class="formula">T(n) = s + p ⁄ n<span>elbow: n* = p ⁄ s</span><span>there T(n*) = 2s</span></p>

{{fig:amdahl|**Where to stop adding ranks.** At the elbow `n*`, the divisible work has shrunk to the size of the floor. Beyond it, each doubling of ranks doubles the charged core-hours for a small gain in time.}}

## Eaton, measured

Eaton is the only fire large enough to reach an elbow. We ran it on 6, 12 and 24 whole nodes of each type, on its 5-hour window.

{{fig:eaton|**Eaton's strong scaling.** Cascade Lake's doubling efficiency drops from 90% (6 → 12 nodes) to 69% (12 → 24): that is its elbow. Ice Lake and Sapphire Rapids are still at 87% at 24 nodes; their fitted elbows lie beyond WRF's cap of 2,025 ranks, so for them the cap is the limit.}}

| Node type | Seconds per step at 6 / 12 / 24 nodes | Doubling efficiency | `s` | `p` | Elbow `p/s` |
| --- | --- | --- | --- | --- | --- |
| Cascade Lake | 9.28 / 5.17 / 3.75 | 90% · 69% | 1.70 | 1,799 | ≈ 1,060 ranks |
| Ice Lake | 5.88 / 3.28 / 1.88 | 90% · 87% | 0.58 | 1,786 | ≈ 3,100 (beyond the cap) |
| Sapphire Rapids | 3.69 / 2.01 / 1.16 | 92% · 87% | 0.32 | 1,296 | ≈ 4,100 (beyond the cap) |

The 6-node Ice Lake run was still going when the campaign stopped; its value is from the steps it completed.

## Small fires never reach their elbow

WRF refuses a decomposition that gives any rank fewer than 10 grid points in either direction, on any domain. The small fires' outer domains are 54–60 points a side, which caps them at 25 or 36 ranks ([the rule](run.html#how-many-ranks)).

Seconds per step on one node, full windows:

| Fire, ranks | Cascade Lake | Ice Lake | Sapphire Rapids | Efficiency of the last step to the cap |
| --- | --- | --- | --- | --- |
| Canyon, 16 | 8.25 | 6.06 | 3.93 | |
| Canyon, 25 (cap) | 5.75 | 5.08 | 3.24 | 92% · 76% · 78% |
| Cranston, 25 | 12.60 | 11.28 | 7.27 | |
| Cranston, 36 (cap) | 9.96 | 8.62 | 5.99 | 88% · 91% · 84% |
| Long, 36 (cap) | 7.45 | 6.97 | 4.91 | |

Efficiency is speed-up ÷ rank ratio. Every value is above 75%, so the cap sits on the steep part of the curve. The 6-, 9- and 12-rank runs used the short window and are not comparable with these.

<div class="key" markdown="1">
<span class="callout-title">What we took from it</span>

- **Small fires: run at the cap on one whole node.** Fewer ranks cost more core-hours, because CCR charges the whole node for longer.
- **Sapphire Rapids runs each rank 1.5–2.1× faster than Cascade Lake.** Ice Lake sits between.
- **Large fires: the lower of the elbow and the cap,** and at most about 1,000 ranks on Cascade Lake.
- **To use more cores on a small fire, enlarge or refine its outer domain.** That is a science decision for whoever designs the run, not a sizing decision.
</div>
