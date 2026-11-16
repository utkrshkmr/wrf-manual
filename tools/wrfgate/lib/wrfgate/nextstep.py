"""wrf-next: look at where a fire is and do (or say) the next step.
usage: python3 -m wrfgate.nextstep FIRE [--spec DIR] [--yes] [--retry]"""
import argparse
import getpass
import glob
import hashlib
import json
import math
import os
import subprocess
import sys
from .common import ROOT, read_record, parse_time, get_namelist

BIN = os.environ.get("WG_BIN", "")
ACTIVE = {"PENDING", "RUNNING", "CONFIGURING", "COMPLETING", "REQUEUED", "SUSPENDED"}


def say(*a):
    print(*a, flush=True)


def job_state(jid):
    if not jid:
        return None
    try:
        q = subprocess.run(["squeue", "-h", "-j", jid, "-o", "%T"], capture_output=True, text=True, timeout=60).stdout.strip()
        if q:
            return q.split()[0]
        a = subprocess.run(["sacct", "-n", "-P", "-X", "-j", jid, "-o", "State"], capture_output=True, text=True, timeout=60).stdout.strip()
        return a.split()[0] if a else "UNKNOWN"
    except Exception:
        return "UNKNOWN"


def manifest(path):
    out = {}
    if os.path.exists(path):
        for line in open(path):
            if ":" in line and not line.startswith(" "):
                k, v = line.split(":", 1)
                out.setdefault(k.strip(), v.strip())
    return out


def gate(path):
    if not os.path.exists(path):
        return None, {}
    j = json.load(open(path))
    return j["status"], j


def fails(j):
    return [f"    {c['id']}: {c['text']}" for c in j.get("checks", []) if c["status"] == "FAIL"]


def run(cmd):
    say("  $ " + " ".join(cmd))
    r = subprocess.run([os.path.join(BIN, cmd[0])] + cmd[1:])
    if r.returncode:
        raise SystemExit(r.returncode)


def spec_hash(spec):
    h = hashlib.sha256()
    for n in ("namelist.input", "namelist.fire"):
        p = os.path.join(spec, n)
        if os.path.exists(p):
            h.update(open(p, "rb").read())
    return h.hexdigest()[:12]


def find_spec(fire):
    me = getpass.getuser()
    mine = sorted(glob.glob(os.path.join(ROOT, "people", me, "work", f"{fire}_[0-9]*_[0-9]*", "spec")), key=os.path.getmtime)
    if mine:
        return mine[-1]
    camp = os.path.join(ROOT, "fires", fire, "specs", "campaign")
    return camp if os.path.isdir(camp) else None


def latest(fire, pattern, **want):
    for d in sorted(glob.glob(os.path.join(ROOT, "fires", fire, "runs", pattern)), reverse=True):
        m = manifest(os.path.join(d, "MANIFEST.txt"))
        if all(m.get(k) == v for k, v in want.items()):
            return d, m
    return None, None


def step(fire, spec=None, yes=False, retry=False):
    F = os.path.join(ROOT, "fires", fire)
    if not os.path.exists(os.path.join(F, "fire.yaml")):
        say(f"There is no fire called {fire}. To start one:  wrf-card --new MY_FIRE.card")
        return
    rec = read_record(os.path.join(F, "fire.yaml"))
    spec = os.path.realpath(spec) if spec else find_spec(fire)
    say(f"Fire {fire}: {rec['start']} to {rec['end']} UTC, ignition {rec['ignition_time']} at {rec.get('ignition_lat')}, {rec.get('ignition_lon')}")

    # 1. inputs
    cur = os.path.join(F, "inputs", "current")
    if not os.path.exists(cur):
        work = sorted(glob.glob(os.path.join(ROOT, "people", "*", "work", f"{fire}_[0-9]*_[0-9]*")), key=os.path.getmtime)
        w = work[-1] if work else None
        jid = open(os.path.join(w, "WPS_JOBID")).read().strip() if w and os.path.exists(os.path.join(w, "WPS_JOBID")) else None
        st = job_state(jid)
        if st in ACTIVE:
            say(f"\nStep 1 of 4, making the weather and map files (WPS): job {jid} is {st.lower()}. Run wrf-next {fire} again when it has finished (you get an email).")
        elif jid:
            say(f"\nStep 1 of 4, WPS job {jid} ended ({st}) but no files were registered. The end of its log:")
            logs = sorted(glob.glob(os.path.join(w, "wps_*.out")))
            if logs:
                say("".join(open(logs[-1]).readlines()[-15:]))
            say(f"Fix the problem shown, then:  wrf-card --make {w}/fire.card --wps")
        else:
            vers = [v for v in glob.glob(os.path.join(F, "inputs", "*")) if not v.endswith(".gates") and os.path.isdir(v)]
            if vers:
                v = sorted(vers)[-1]
                say(f"\nStep 1 of 4: the input files {os.path.basename(v)} did not pass their checks:")
                for g in "AB":
                    s, j = gate(v + f".gates/gate_{g}.json")
                    if s == "FAIL":
                        say("\n".join(fails(j)))
                say("Fix the card (see the fire page on the website) and make it again with --wps.")
            else:
                say(f"\nStep 1 of 4: this fire has no weather and map files yet. Make them from its card:\n  wrf-card --make CARD_FILE --wps")
        return
    ver = os.path.basename(os.path.realpath(cur))
    if not spec:
        say(f"\nNo settings (spec) found for {fire}. Make the card into one:  wrf-card --make CARD_FILE")
        return
    sh = spec_hash(spec)
    say(f"Inputs {ver}; settings {spec}")

    # 2. gate C
    c_dir, c_m = latest(fire, "*_gateC_*", spec_hash=sh, inputs=ver)
    if not c_dir or retry and gate(os.path.join(c_dir, "gate_C.json"))[0] in (None, "FAIL"):
        say("\nStep 2 of 4: preparing the start files (real.exe) and checking them. Submitting:")
        run(["wrf-gate", "C", fire, spec])
        say(f"You get an email when it ends (usually within an hour of starting). Then run:  wrf-next {fire}")
        return
    st = job_state(open(os.path.join(c_dir, "JOBID")).read().strip()) if os.path.exists(os.path.join(c_dir, "JOBID")) else None
    s, j = gate(os.path.join(c_dir, "gate_C.json"))
    if s is None:
        if st in ACTIVE:
            say(f"\nStep 2 of 4: preparing the start files: job is {st.lower()}. Run wrf-next {fire} again after the email.")
        else:
            say(f"\nStep 2 of 4: the job ended ({st}) without a result. End of its log:")
            r = os.path.join(c_dir, "rsl.error.0000")
            if os.path.exists(r):
                say("".join(open(r).readlines()[-12:]))
            say(f"To try again:  wrf-next {fire} --retry")
        return
    if s == "FAIL":
        say(f"\nStep 2 of 4 failed. What is wrong:\n" + "\n".join(fails(j)))
        say(f"Fix the settings (the card, then wrf-card --make CARD) and run wrf-next {fire} again. Full report: {c_dir}/GATES.txt")
        return
    cap = int(j["facts"].get("rank_cap", 16))

    # 3. gate D
    d_dir, d_m = latest(fire, "*_gateD_*", from_gate_c=c_dir)
    if not d_dir or retry and gate(os.path.join(d_dir, "gate_D.json"))[0] in (None, "FAIL"):
        say("\nStep 3 of 4: a 2-minute test run of the model. Submitting:")
        extra = ["--ranks", "64", "--constraint", "SAPPHIRE-RAPIDS-IB"] if cap > 64 else []
        run(["wrf-gate", "D", fire, c_dir] + extra)
        say(f"You get an email when it ends. Then run:  wrf-next {fire}")
        return
    st = job_state(open(os.path.join(d_dir, "JOBID")).read().strip()) if os.path.exists(os.path.join(d_dir, "JOBID")) else None
    s, j = gate(os.path.join(d_dir, "gate_D.json"))
    if s is None:
        if st in ACTIVE:
            say(f"\nStep 3 of 4: the test run is {st.lower()}. Run wrf-next {fire} again after the email.")
        else:
            say(f"\nStep 3 of 4: the test run ended ({st}) without a result. To try again:  wrf-next {fire} --retry")
        return
    if s == "FAIL":
        say(f"\nStep 3 of 4 failed. What is wrong:\n" + "\n".join(fails(j)) + f"\nFull report: {d_dir}/GATES.txt")
        return
    sps_d = float(j["facts"].get("seconds_per_step_d01", 0) or 0)
    ranks_d = int(d_m.get("ranks", 32) or 32)

    # 4. the run
    p_dir, p_m = latest(fire, "*", kind="production", spec_hash=sh, inputs=ver)
    if p_dir and not retry:
        st = job_state(open(os.path.join(p_dir, "JOBID")).read().strip())
        if st in ACTIVE:
            say(f"\nStep 4 of 4: the simulation is {st.lower()}. Progress:")
            subprocess.run([os.path.join(BIN, "wrf-watch"), fire])
            return
        s, j = gate(os.path.join(p_dir, "gate_E.json"))
        say(f"\nStep 4 of 4: the simulation has ended ({st}).")
        if j:
            fa = j.get("facts", {})
            say(f"  ending: {fa.get('ending', '?')}; burnt area: {fa.get('burnt_area_ha', '?')} ha; result: {s}")
            say("\n".join(fails(j)))
        say(f"  output files: {p_dir}/wrfout_*\n  full report: {p_dir}/GATES.txt")
        say(f"To run it again anyway:  wrf-next {fire} --retry")
        return
    nl = open(os.path.join(spec, "namelist.input")).read()
    dt = float((get_namelist(nl, "time_step") or ["6"])[0])
    window = (parse_time(rec["end"]) - parse_time(rec["start"])).total_seconds()
    steps = window / dt
    if cap <= 64:
        nodes, ranks, con = 1, cap, ""
    else:
        nodes = min(24, math.ceil(cap / 64)); ranks = min(cap, nodes * 64); con = "SAPPHIRE-RAPIDS-IB"
    eff = 1.0 if ranks <= ranks_d else 0.8
    sps = sps_d * ranks_d / ranks / eff if sps_d else 0
    hours = math.ceil(sps * steps * 1.5 / 3600 + 1) if sps else 48
    hours = min(max(hours, 2), 72)
    cores = 64
    say(f"""
Step 4 of 4: the simulation. Suggested size (from the 2-minute test run, with a margin for the fire's growth):
  nodes        {nodes}{' (Sapphire Rapids)' if con else ''}
  processes    {ranks}
  time limit   {hours} h
  cost         at most {nodes * cores * hours:,} core-hours (whole nodes are charged for the time used)""")
    if sps and sps * steps * 1.5 / 3600 + 1 > 72:
        say("  NOTE: this may need more than 72 h, the cluster's limit. Ask the lab before submitting.")
    if not yes:
        try:
            a = input("Submit it? [y/N]: ").strip().lower()
        except EOFError:
            a = ""
        if a not in ("y", "yes"):
            say("Not submitted. To submit with these numbers later:  wrf-next " + fire + " --yes")
            return
    cmd = ["wrf-submit", fire, spec, "--nodes", str(nodes), "--ranks", str(ranks), "--time", f"{hours}:00:00", "--name", "run"]
    if con:
        cmd += ["--constraint", con]
    run(cmd)
    say(f"Submitted. You get an email when it ends. To see progress at any time:  wrf-next {fire}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("fire"); ap.add_argument("--spec"); ap.add_argument("--yes", action="store_true"); ap.add_argument("--retry", action="store_true")
    a = ap.parse_args()
    step(a.fire, a.spec, a.yes, a.retry)
