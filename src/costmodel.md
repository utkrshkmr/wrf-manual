---
title: Cost model and node formula
kicker: Results
lead: Expressed per unit of work, all our runs collapse onto one curve per machine with a single shared shape. That gives three device constants and a nine-step rule that sizes a run from its grid alone, within 1% for Cranston.
---

## The cost model

Seconds per step depend on the fire's size and the rank count. Dividing them out leaves what the machine charges for one column update, as a function of how big each rank's patch is:

<p class="formula">cost per update = seconds per step × ranks ÷ column updates per step<span>patch side = √(column updates ÷ ranks)</span></p>

{{fig:costmodel|**The weak-scaling view.** Each machine's points rise to the left, toward small patches, by the same shape. Perfect weak scaling would be three flat lines.}}

The fit, over the 24 full-window runs (plus Eaton's short-window runs):

<p class="formula">cost = a(type) × (1 + k ÷ side)<span>a = 207 · 169 · 114 µs</span><span>k = 110 points</span></p>

| Node type | `a`, µs per column update | Relative to Sapphire Rapids |
| --- | --- | --- |
| Cascade Lake | 207 | 1.82× |
| Ice Lake | 169 | 1.48× |
| Sapphire Rapids | 114 | 1 |

**How to read it.** The `1 + k ÷ side` factor is the cost of exchanging patch edges with neighbouring ranks. At a 60-point patch it adds about 180% to the cost; at 200 points, about 55%. One `k` serves all three machines, so the machines differ only by a constant factor.

**What it misses.** Typical error 11%, worst 28%. Long and Cranston sit above their curves and Canyon below: a fire with a larger active front does more fire-model work per column, which a count of grid cells cannot see. The first 15 minutes of a real run measure it per fire, and the [lookup table](design.html#the-weekly-lookup-table) keeps those measurements.

## The node formula

{{fig:formula|**The sizing rule, worked.** Steps 1–3 need only the fire's grid, 4–5 the calibration, 6–7 the simulated window. For Cranston it predicts 41.8 h against 41.6 h measured.}}

1. **Rank cap.** `⌊nx/10⌋ × ⌊ny/10⌋` on the tightest domain.
2. **Ranks.** Small fire: the cap, on one whole node. Large fire: `min(cap, 24 nodes × cores)`, and at most about 1,000 on Cascade Lake (its elbow).
3. **Patch side.** `√(column updates per step ÷ ranks)`.
4. **Cost per update.** `a(type) × (1 + 110 ÷ side)`.
5. **Seconds per step.** `column updates × cost × 10⁻⁶ ÷ ranks`.
6. **Steps.** Simulated seconds ÷ coarse time step.
7. **Walltime.** `seconds per step × steps × 1.15 + 1 h`; × 1.3 for a fire never run before.
8. **Over 72 hours?** Split into a chain of jobs resuming from restart files. Each link waited 12–24 h in the queue, so fitting in one job is worth a lot.
9. **Charged core-hours.** `nodes × cores per node × walltime`, whether the cores are used or not.

Cranston lands within 1% partly because it is in the calibration set. A new fire gets the 1.3 margin until its own first measured rate replaces step 5.
