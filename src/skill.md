---
title: Skill file for chat assistants
kicker: Running it safely
lead: One block of text you paste at the start of a chat with any AI assistant. It tells the assistant how our setup works, so it can walk you through running any fire, one command at a time, and read what CCR prints back.
---

## How to use it

1. **Copy the skill.** Press **Copy the skill** below (or select the whole block and copy it).
2. **Start a new chat** with your assistant (Claude, ChatGPT, Gemini, or any other) and paste it as your first message.
3. **Underneath, paste the fire's card and one line saying what you want.** A card is the fire's settings: name, window, ignition time and place, domains and a few model settings ([what a card is](quickstart.html#2-describe-the-fire-as-a-card)). For example:
   - a filled card from `wrf-card --template`, and *"Run this fire."*
   - the output of `wrf-card LONG_2024` with `time_step_s` changed, and *"Run this as a variant."*
   - the output of `wrf-card CANYON_2025`, plus its gate C `GATES.txt`, and *"Gate C failed; what is wrong?"*

   No card yet? Give it what you know (name, dates, ignition point) and it builds the card with you first.
4. **Follow it step by step.** The assistant gives you commands to paste into your CCR terminal. Paste them, then paste what CCR prints back into the chat. It reads the output and tells you the next step.

## Good to know

- **It works one step at a time.** Run only the block it just gave you, and paste back all of the output, including errors.
- **It asks before spending.** Before the real run it states nodes, ranks, walltime and core-hours, and waits for your yes.
- **It never deletes.** Anything you want out of the way goes through `wrf-setaside`, which keeps it in `wrf/setaside/` with a note.
- **It asks you for facts.** Ignition time and place, the window and the location of your files come from you; it will not guess them.
- **One chat per fire works best.** For a new fire, start a new chat and paste the skill again.
- **If it goes off track** ("just delete the folder", a hand-written `sbatch` for wrf.exe, an edit to `fire.yaml`), say "follow the skill's rules" or start a new chat.
- **The first time** it will ask for your name and email, to set up your profile; Slurm then emails you when your jobs end.

## The skill

<div class="copybar" markdown="0"><button type="button" onclick="(function(b){var t=document.querySelector('#skill-src code').textContent;function ok(){b.textContent='Copied';setTimeout(function(){b.textContent='Copy the skill'},2000)}if(navigator.clipboard){navigator.clipboard.writeText(t).then(ok,function(){fb()})}else fb();function fb(){var a=document.createElement('textarea');a.value=t;document.body.appendChild(a);a.select();try{document.execCommand('copy');ok()}catch(e){}document.body.removeChild(a)}})(this)">Copy the skill</button></div>

<div id="skill-src" markdown="1">

{{include:tools/wrfgate/SKILL.md}}

</div>
