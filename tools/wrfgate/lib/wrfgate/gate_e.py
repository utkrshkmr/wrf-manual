"""Gate E: a finished (or stopped) run - how it ended, whether the output is complete, whether the fire
started where and when the record says.
usage: python3 -m wrfgate.gate_e RUN_DIR --record fire.yaml"""
import argparse
import datetime as _dt
import glob
import os
import re
import numpy as np
from netCDF4 import Dataset
from .common import Gate, read_record, parse_time, get_namelist
from .gate_d import scan_rsl
from .geo import haversine_km


def ending(run_dir):
    txt = {p: open(p, errors="replace").read() for p in glob.glob(os.path.join(run_dir, "rsl.error.*"))}
    if any("SUCCESS COMPLETE WRF" in t for t in txt.values()):
        return "finished"
    if any(re.search(r"reached domain boundary", t, re.I) for t in txt.values()):
        return "domain_edge"
    if any(re.search(r"cfl|\bnan\b|segmentation fault|sigsegv|forrtl|fatal", t, re.I) for t in txt.values()):
        return "crash"
    return "killed_or_running"


def run(run_dir, record, out=None):
    g = Gate("E", run_dir)
    rec = read_record(record)
    end_class = ending(run_dir)
    g.facts["ending"] = end_class
    st = {"finished": "PASS", "domain_edge": "WARN", "crash": "FAIL", "killed_or_running": "WARN"}[end_class]
    g.check("E01_ending", st, {"finished": "finished: SUCCESS COMPLETE WRF",
                               "domain_edge": "stopped when the fire reached the fire domain's edge (not a crash; the domain is too small for this fire)",
                               "crash": "crashed: CFL, NaN, segfault or fatal message in a rank log",
                               "killed_or_running": "no ending in the logs: still running, or killed by Slurm (time limit, memory, node)"}[end_class])
    nl = open(os.path.join(run_dir, "namelist.input")).read()
    md = int(get_namelist(nl, "max_dom")[0])
    outs = {d: sorted(glob.glob(os.path.join(run_dir, f"wrfout_d{d:02d}_*"))) for d in range(1, md + 1)}
    g.ok("E02_outputs", all(outs.values()), "history output for every domain: " + ", ".join(f"d{d:02d} {len(v)} files" for d, v in outs.items()),
         "missing history output for " + ", ".join(f"d{d:02d}" for d, v in outs.items() if not v))
    if not all(outs.values()):
        return g.write(out or run_dir)
    start = parse_time(rec["start"])
    srs = get_namelist(nl, "sr_x") or ["0"]
    srs = [int(float(srs[min(k, len(srs) - 1)])) for k in range(md)]
    fd = 1 + int(np.argmax(srs))
    sr = max(1, srs[fd - 1])
    last = outs[fd][-1]
    bad = []
    with Dataset(last) as d:
        tl = b"".join(d["Times"][-1]).decode()
        for v in ["U", "V", "T", "PSFC", "FIRE_AREA", "FGRNHFX"]:
            if v in d.variables and not np.isfinite(np.asarray(d[v][-1])).all():
                bad.append(v)
        g.facts["last_output"] = tl
        g.ok("E03_finite", not bad, f"no NaN or Inf in the last output ({tl})", f"non-finite values in {bad} at {tl}")
        if "TIGN_G" in d.variables and "FXLAT" in d.variables:
            tign = np.asarray(d["TIGN_G"][-1]); fl, fo = np.asarray(d["FXLAT"][-1]), np.asarray(d["FXLONG"][-1])
            area = np.asarray(d["FIRE_AREA"][-1]) if "FIRE_AREA" in d.variables else None
            t_out = (parse_time(tl) - start).total_seconds()
            burned = tign <= t_out
            if g.ok("E04_burned", burned.any(), f"{int(burned.sum())} fire cells ignited by {tl}", "no fire cell has ignited"):
                t_first = float(tign[burned].min())
                ign = parse_time(rec["ignition_time"]); want = (ign - start).total_seconds()
                g.ok("E05_ignition_time", abs(t_first - want) <= 600, f"first cell ignited {t_first:.0f} s after start (record: {want:.0f} s)",
                     f"first cell ignited {t_first:.0f} s after start, but the record says {want:.0f} s")
                j, i = np.unravel_index(np.argmin(np.where(burned, tign, np.inf)), tign.shape)
                if rec.get("ignition_lat") and (fl != 0).any():
                    km = float(haversine_km(float(rec["ignition_lat"]), float(rec["ignition_lon"]), fl[j, i], fo[j, i]))
                    g.ok("E06_ignition_place", km <= 1.0, f"first ignited cell {km*1000:.0f} m from the recorded ignition point",
                         f"first ignited cell is {km:.2f} km from the recorded ignition point")
                guard = 8
                edge = burned[:guard].any() or burned[-guard:].any() or burned[:, :guard].any() or burned[:, -guard:].any()
                g.ok("E07_inside_domain", not edge, "burnt area stays clear of the fire domain's edge",
                     "burnt area reaches within 8 cells of the fire domain's edge", warn_only=True)
                if area is not None:
                    dx = float(d.getncattr("DX")) / sr
                    g.facts["burnt_area_ha"] = round(float(area.sum()) * dx * dx / 1e4, 1)
                    g.check("E08_burnt_area", "INFO", f"burnt area at {tl}: {g.facts['burnt_area_ha']} ha")
        else:
            g.check("E04_burned", "WARN", "TIGN_G/FXLAT not in the history output: add them with iofields_filename to check the ignition")
    if rec.get("end"):
        reached = parse_time(tl)
        g.ok("E09_reached_end", reached >= parse_time(rec["end"]), f"output reaches the recorded end {rec['end']}",
             f"output stops at {reached}, before the recorded end {rec['end']}", warn_only=True)
    return g.write(out or run_dir)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("run_dir"); ap.add_argument("--record", required=True); ap.add_argument("--out")
    a = ap.parse_args()
    raise SystemExit({"PASS": 0, "WARN": 0, "FAIL": 1}[run(a.run_dir, a.record, a.out)])
