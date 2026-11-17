"""Gate D: a short smoke run of wrf.exe (a few simulated minutes on one node).
usage: python3 -m wrfgate.gate_d SMOKE_DIR"""
import argparse
import glob
import os
import re
import numpy as np
from .common import Gate

BAD = [(r"cfl", "CFL violation"), (r"\bnan\b", "NaN"), (r"segmentation fault|sigsegv", "segfault"),
       (r"fuel category out of bounds", "fuel category out of bounds"), (r"forrtl|fatal", "fatal error")]


def scan_rsl(run_dir):
    hits, success, timing = {}, False, {}
    for p in sorted(glob.glob(os.path.join(run_dir, "rsl.error.*"))):
        txt = open(p, errors="replace").read()
        if "SUCCESS COMPLETE WRF" in txt:
            success = True
        for pat, name in BAD:
            if re.search(pat, txt, re.I):
                hits.setdefault(name, []).append(os.path.basename(p))
        if p.endswith(".0000"):
            for m in re.finditer(r"Timing for main: time \S+ on domain\s+(\d+):\s+([\d.]+) elapsed", txt):
                timing.setdefault(int(m.group(1)), []).append(float(m.group(2)))
    return success, hits, timing


def run(run_dir, out=None):
    g = Gate("D", run_dir)
    success, hits, timing = scan_rsl(run_dir)
    g.ok("D01_success", success, "wrf.exe finished the smoke run: SUCCESS COMPLETE WRF", "no SUCCESS line in any rsl.error file")
    for name, files in hits.items():
        if name == "CFL violation":
            g.check("D02_" + name.replace(" ", "_"), "WARN", f"'{name}' in {len(files)} rank logs, e.g. {files[0]}")
        else:
            g.check("D02_" + name.replace(" ", "_"), "FAIL", f"'{name}' in {len(files)} rank logs, e.g. {files[0]}")
    if not hits:
        g.check("D02_logs_clean", "PASS", "no CFL, NaN, segfault or fatal messages in any rank log")
    if timing:
        d1 = timing.get(1, [])
        steady = d1[len(d1) // 3:] if len(d1) > 3 else d1
        sps = float(np.mean(steady)) if steady else float("nan")
        g.facts.update(seconds_per_step_d01=round(sps, 3), steps_timed=len(d1))
        g.check("D03_rate", "INFO", f"{sps:.3f} s per d01 step over {len(steady)} steady steps (before ignition: expect slower once the fire grows)")
    else:
        g.check("D03_rate", "WARN", "no 'Timing for main' lines found in rsl.error.0000")
    import re as _re
    r0 = os.path.join(run_dir, "rsl.error.0000")
    grads = _re.findall(r"max gradient\s+([-\d.Ee+]+)", open(r0, errors="replace").read()) if os.path.exists(r0) else []
    if grads:
        mg = float(grads[0])
        g.facts["max_terrain_gradient"] = mg
        g.ok("D04_fire_terrain", mg > 0, f"the fire model sees terrain: steepest slope {mg:.2f}", "the fire model reports a max gradient of 0: flat terrain")
    return g.write(out or run_dir)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("run_dir"); ap.add_argument("--out")
    a = ap.parse_args()
    raise SystemExit({"PASS": 0, "WARN": 0, "FAIL": 1}[run(a.run_dir, a.out)])
