---
title: Set up (once)
kicker: Step 1
lead: Three lines in your CCR terminal, once. After that every fire is run with the same few commands.
toc: no
---

## What you need

- A CCR account in the lab's group (`grp-negarkhodoe`). If you can open `/projects/academic/negarkhodoe`, you have it.
- A terminal on CCR: log in with `ssh` as you normally do, or open a shell from CCR's OnDemand web portal.

## Set up

Copy these three lines into the terminal, with your own name and email in the last one, and press Enter:

```bash
echo 'source /projects/academic/negarkhodoe/wrf/pipeline/current/setup.sh' >> ~/.bashrc
source /projects/academic/negarkhodoe/wrf/pipeline/current/setup.sh
wrf-me --name "Your Name" --email you@buffalo.edu
```

- The first line makes the commands available every time you log in. The second makes them available now.
- The third saves your name and email. Every run you start is labelled with your name, and the cluster emails you when each of your jobs ends or fails.

## Check it worked

```bash
wrf-status
```

You should see a list of fires, including `EATON_2025`, `CANYON_2025`, `CRANSTON_2018` and `LONG_2024`.

| If you see | Do this |
| --- | --- |
| `command not found` | Run the second line again, or log out and back in |
| `no profile for …` | Run the `wrf-me` line again |
| `Permission denied` | Your account is not in the lab's group yet: ask the lab |

## Emails

By default you get an email when a job ends or fails. To change that:

```bash
wrf-me --mail ALL
wrf-me --mail NONE
wrf-me --mail END,FAIL
```

## Next

- Run a fire we have already set up: [Eaton](fire-eaton.html), [Canyon](fire-canyon.html), [Cranston](fire-cranston.html) or [Long](fire-long.html).
- Set up a new fire: [Your own fire](newfire.html).
- Prefer to be guided? The [AI chat helper](skill.html) walks you through either, one command at a time.
