---
title: Fire and atmosphere
kicker: Advanced · research inputs
lead: The fire heats the air, the air changes the wind, and the wind drives the fire. Turn the feedback off, scale it, release the heat higher or lower, choose which wind drives the spread, or replace the fire with a prescribed heat source.
---

## The coupling experiments

| Experiment | Settings |
| --- | --- |
| One-way coupling (the fire doesn't change the weather) | `fire_atm_feedback = 0` |
| Stronger or weaker coupling | `fire_atm_feedback` between 0 and 1, or above |
| Heat released lower or higher | `fire_ext_grnd` (default 50 m), or `fire_sfc_flx = 1` with `fire_heat_peak` |
| A prescribed, constant heat source | `fire_const_time` (when to freeze), `fire_const_grnhfx`, `fire_const_grnqfx` |
| Wind for the spread taken higher up | `fire_lsm_zcoupling = .true.`, `fire_lsm_zcoupling_ref = 50` |

All of these are `&fire` settings on the fire domain; the defaults are on the [fire model page](fire.html#spread-heat-release-and-coupling).

## Which wind drives the spread

By default the spread rate uses the wind at `fire_wind_height` (6.1 m, the 20 ft of fire-behaviour practice), interpolated from the model's lowest levels. With `fire_lsm_zcoupling = .true.` the wind is taken at `fire_lsm_zcoupling_ref` (50 m) and brought down with a log profile, which is less sensitive to how the lowest model levels are placed. Each fuel's `windrf` then reduces it to mid-flame height.

## A prescribed heat source

`fire_const_time` freezes the fire at that many seconds after the start; from then on each burning cell releases the constant fluxes `fire_const_grnhfx` (sensible, W/m²) and `fire_const_grnqfx` (latent). It separates the atmosphere's response to a known heat source from the fire's own spread.

## Running the variants

Each experiment is a copy of the fire's spec with one `&fire` change, through gates C and D, then `wrf-submit` with a `--name` that says what changed (`--name oneway`, `--name feedback05`). One-way coupling (`fire_atm_feedback = 0`) is the usual first comparison: the difference between it and the baseline is the fire's own effect on its weather.
