---
title: Queue waits and cost
kicker: Results
lead: The fastest node type was also the cheapest, but after two days it stopped starting our jobs. Waiting in the queue, not running, set our finish times, and that changed the design.
---

## Queue waits

Wait = start time − the time the job became eligible, so a continuation's wait does not include the job it depends on.

| Jobs eligible | Size | Cascade Lake | Ice Lake | Sapphire Rapids |
| --- | --- | --- | --- | --- |
| Oct 18–19 | 1 node | 0–0.1 h, 5 of 5 started | 0–33 h, median 7 h, 5 of 5 | 0–1.1 h, 5 of 5 |
| Oct 20–25 | 1 node | 4–41 h, median 23 h, 9 of 9 | 45 h, 1 of 6; the rest still waiting after 25–101 h | none of 5 started; still waiting after 14–101 h |
| Oct 18 | 24 nodes | 0 h | 43 h | 9 h |
| Oct 20–23 | 6 and 12 nodes | 21 h and 53 h | 47 h and 3 h | 47 h and 68 h |

45 jobs; 5 leftover continuations cancelled by hand are left out. From Oct 24, jobs of up to 3 days could not start before the Oct 27–28 downtime anyway.

**Why.** CCR ranks waiting jobs partly by the group's recent usage ("fairshare"). Our first jobs started at once; by day three we had used a lot, and the scarcest nodes went to other groups first.

**Asking for less did not help.** 6- and 12-node Eaton jobs waited 21–68 h, longer than the 24-node jobs had at the start. Time limits of 4–14 h did not get jobs in sooner. Continuations each waited 12–24 h.

{{fig:race|**The rule that follows.** Submit one copy per node type and keep whichever starts first. Sapphire Rapids is worth waiting for only while it can still finish first.}}

One week of data, under our own heavy load: trust the pattern, not the exact hours. Every production job logs its wait, so the rule keeps being retuned.

## Cost

{{fig:cost|**Charged core-hours per run.** CCR charges whole nodes, so speed and cost agree on the node type.}}

| Run (core-hours, run time) | Cascade Lake | Ice Lake | Sapphire Rapids |
| --- | --- | --- | --- |
| Canyon, 25 ranks, full window | 2,360 (59.0 h) | 2,912 (52.0 h) | 2,125 (33.2 h) |
| Canyon, 16 ranks, full window | 3,372 (84.3 h) | 3,478 (62.1 h) | 2,586 (40.4 h) |
| Cranston, 36 ranks, full window | 2,732 (68.3 h) | 3,304 (59.0 h) | 2,662 (41.6 h) |
| Long, 36 ranks, to the domain edge | 2,692 (67.3 h) | 3,517 (62.8 h) | 2,835 (44.3 h) |
| Eaton, 5 h window, 24 nodes | 7,392 (7.7 h) | 5,914 (4.4 h) | 5,683 (3.7 h) |
| Eaton, 5 h window, 12 nodes | 4,848 (10.1 h) | 4,502 (6.7 h) | 3,686 (4.8 h) |
| Eaton, 5 h window, 6 nodes | 4,128 (17.2 h) | not finished | 2,918 (7.6 h) |

- **Sapphire Rapids is cheapest for every fire,** even with 44–61% of its 64 cores idle on a small fire, because it finishes so much sooner.
- **Fewer ranks on one node costs more.** Canyon at 16 ranks charged 22–43% more than at 25: the node is charged whole for longer.
- **For Eaton, halving the nodes halves the cost and doubles the time.** 6 Sapphire Rapids nodes: 2,918 core-hours in 7.6 h; 24 nodes: 5,683 in 3.7 h. The queue data tips that choice toward 24, since fewer nodes did not start any sooner.
