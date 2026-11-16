---
title: Examples: the fires we have run
kicker: Examples
lead: Each fire has its own page that can be followed on its own: its card with every setting, how to run it from an AI chat or with the commands, how to size it, and how to make a variant.
toc: no
---

## The fires

| Fire | Window (UTC) | Ignition | Domains | Rank cap | Page |
| --- | --- | --- | --- | --- | --- |
| `EATON_2025` | Jan 8 00:00 → 17:00, 2025 | 02:18 at 34.18604, −118.09325 | 450² at 900 m, fire 811² at 100 m | 2,025 | [Eaton 2025](fire-eaton.html) |
| `CANYON_2025` | Aug 7 18:00 → Aug 9 00:00, 2025 | 20:25 | 54² at 900 m, fire 217² at 100 m | 25 | [Canyon 2025](fire-canyon.html) |
| `CRANSTON_2018` | Jul 25 16:00 → Jul 26 12:00, 2018 | in its card | in its card | 36 | [Cranston 2018](fire-cranston.html) |
| `LONG_2024` | Jul 15 20:00 → Jul 17 00:00, 2024 | in its card | in its card | 36 | [Long 2024](fire-long.html) |
| `AIRPORT` | in its card | in its card | in its card | — | [Airport](fire-airport.html) |
| `BRADFORD_BRANCH` | in its card | in its card | in its card | — | [Bradford Branch](fire-bradford.html) |
| `CARMEL` | in its card | in its card | in its card | — | [Carmel](fire-carmel.html) |

Fuel maps (from comparing each fire's `met_em` with every LANDFIRE release): Eaton, Canyon LF2024 · Cranston LF2016 · Long LF2023 · Airport has no fuel map in its inputs · Bradford Branch and Carmel match none of our releases. Details on each page.

Every fire is already in the shared folder with its record, its checked `met_em` files and (for the four we ran) the spec it ran with. `wrf-card FIRE` prints its full card from those files.

## A new fire

Start from the closest of these: `wrf-card CANYON_2025 > my.card` for a small fire, `wrf-card EATON_2025 > my.card` for a large one. Change the name, times, ignition and domains, keep `base_spec` for the lab's physics, and follow the [quick start](quickstart.html#3b-or-type-the-commands).
