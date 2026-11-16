"""Monitor every job the gating system submitted: Slurm state, simulated time reached, rate, ETA, warnings.
usage: python3 -m wrfgate.watch [FIRE] [--mine] [--active] [--write FILE]"""
import argparse
import datetime as _dt
import getpass
import glob
import os
import re
import subprocess
import time
from .common import ROOT, read_record, parse_time

TIMING = re.compile(r"Timing for main: time (\d{4}-\d\d-\d\d_\d\d:\d\d:\d\d) on domain\s+1:\s+([\d.]+) elapsed")
ACTIVE = {"PENDING", "RUNNING", "CONFIGURING", "COMPLETING", "REQUEUED", "SUSPENDED"}


def manifest(path):
    out = {}
    try:
        for line in open(path):
            if ":" in line and not line.startswith(" "):
                k, v = line.split(":", 1)
                out.setdefault(k.strip(), v.strip())
    except OSError:
        pass
    return out


def slurm(ids):
    """job id -> dict(state, elapsed, limit, nodes, reason) from squeue, then sacct for the rest."""
    info = {}
    if not ids:
        return info
    try:
        q = subprocess.run(["squeue", "-h", "-j", ",".join(ids), "-o", "%i|%T|%M|%l|%D|%r"], capture_output=True, text=True, timeout=60).stdout
        for line in q.splitlines():
            i, st, el, lim, n, why = (line.split("|") + [""] * 6)[:6]
            info[i] = dict(state=st, elapsed=el, limit=lim, nodes=n, reason=why)
    except Exception:
        pass
    rest = [i for i in ids if i not in info]
    if rest:
        try:
            a = subprocess.run(["sacct", "-n", "-P", "-X", "-j", ",".join(rest), "-o", "JobID,State,Elapsed,Timelimit,NNodes,ExitCode"],
                               capture_output=True, text=True, timeout=60).stdout
            for line in a.splitlines():
                i, st, el, lim, n, ex = (line.split("|") + [""] * 6)[:6]
                info[i] = dict(state=st.split()[0] if st else "?", elapsed=el, limit=lim, nodes=n, reason=f"exit {ex}")
        except Exception:
            pass
    return info


def secs(s):
    """Slurm duration (D-HH:MM:SS, HH:MM:SS, MM:SS) -> seconds, or None."""
    if not s or s in ("UNLIMITED", "INVALID", "NOT_SET"):
        return None
    d = 0
    if "-" in s:
        d, s = s.split("-", 1); d = int(d)
    p = [int(x) for x in s.split(":")]
    while len(p) < 3:
        p.insert(0, 0)
    return d * 86400 + p[0] * 3600 + p[1] * 60 + p[2]


def hms(x):
    if x is None:
        return "-"
    x = int(x)
    return f"{x // 3600}h{x % 3600 // 60:02d}" if x >= 3600 else f"{x // 60}m"


def progress(run_dir):
    """Last simulated time on d01, mean s/step over the last 20 steps, coarse step (s), seconds since the log changed."""
    f = os.path.join(run_dir, "rsl.error.0000")
    if not os.path.exists(f):
        return None
    with open(f, "rb") as fh:
        fh.seek(0, 2); size = fh.tell(); fh.seek(max(0, size - 400_000))
        tail = fh.read().decode("utf-8", "replace")
    hits = TIMING.findall(tail)
    if not hits:
        return dict(sim=None, sps=None, dt=None, idle=time.time() - os.path.getmtime(f))
    t = [_dt.datetime.strptime(a, "%Y-%m-%d_%H:%M:%S") for a, _ in hits[-21:]]
    e = [float(b) for _, b in hits[-20:]]
    dts = [(b - a).total_seconds() for a, b in zip(t, t[1:]) if (b - a).total_seconds() > 0]
    return dict(sim=t[-1], sps=sum(e) / len(e), dt=(sorted(dts)[len(dts) // 2] if dts else None),
                idle=time.time() - os.path.getmtime(f))


def rows(fire=None, mine=False, active=False):
    me = getpass.getuser()
    runs = []
    for d in sorted(glob.glob(os.path.join(ROOT, "fires", fire or "*", "runs", "*", ""))):
        j = os.path.join(d, "JOBID")
        if not os.path.exists(j):
            continue
        m = manifest(os.path.join(d, "MANIFEST.txt"))
        by = m.get("by", "")
        if mine and f"({me})" not in by:
            continue
        runs.append((d.rstrip("/"), open(j).read().strip(), m))
    info = slurm([r[1] for r in runs])
    out = []
    for d, jid, m in runs:
        s = info.get(jid, dict(state="UNKNOWN", elapsed="", limit="", nodes="", reason="not in squeue or sacct"))
        if active and s["state"] not in ACTIVE:
            continue
        f = d.split(os.sep)[-3]
        try:
            rec = read_record(os.path.join(ROOT, "fires", f, "fire.yaml"))
            start, end = parse_time(rec["start"]), parse_time(rec["end"])
        except Exception:
            start = end = None
        kind = m.get("kind", "?").split(" (")[0]
        if kind.startswith("gate D") and start:
            end = start + _dt.timedelta(minutes=float(m.get("minutes", 2)))
        p = progress(d) if s["state"] in ACTIVE or s["state"] in ("COMPLETED", "FAILED", "TIMEOUT", "CANCELLED", "NODE_FAIL", "OUT_OF_MEMORY") else None
        pct = eta = None
        flags = []
        if p and p["sim"] and start and end and end > start:
            pct = 100 * (p["sim"] - start).total_seconds() / (end - start).total_seconds()
            if p["sps"] and p["dt"]:
                eta = max(0.0, (end - p["sim"]).total_seconds()) / p["dt"] * p["sps"]
        if s["state"] == "RUNNING":
            if p and p["idle"] > 1800:
                flags.append(f"log idle {hms(p['idle'])}")
            el, lim = secs(s["elapsed"]), secs(s["limit"])
            if eta is not None and el is not None and lim is not None and el + eta > lim:
                flags.append(f"won't finish: needs ~{hms(el + eta)} of {hms(lim)}")
        if s["state"] == "PENDING" and s["reason"]:
            flags.append(s["reason"])
        if s["state"] not in ACTIVE and s["state"] != "COMPLETED":
            flags.append(s["state"].lower() + (" " + s["reason"] if s["reason"] else ""))
        for g in "CDE":
            gf = os.path.join(d, f"gate_{g}.json")
            if os.path.exists(gf):
                import json
                flags.append(f"gate {g} {json.load(open(gf))['status']}")
        out.append(dict(fire=f, run=os.path.basename(d), kind=kind, by=re.sub(r" <.*", "", m.get("by", "-")), job=jid,
                        state=s["state"], elapsed=s["elapsed"] or "-", limit=s["limit"] or "-", nodes=s["nodes"] or "-",
                        sim=p["sim"].strftime("%m-%d %H:%M") if p and p["sim"] else "-", pct=pct,
                        sps=p["sps"] if p else None, eta=eta, flags="; ".join(flags)))
    return out


def table(r):
    head = f"{'FIRE':<15} {'RUN':<34} {'KIND':<10} {'BY':<16} {'JOB':<10} {'STATE':<10} {'ELAPSED':>10} {'LIMIT':>10} {'SIM TIME':>11} {'DONE':>5} {'S/STEP':>7} {'ETA':>6}  NOTES"
    lines = [f"wrfgate jobs  {_dt.datetime.now():%Y-%m-%d %H:%M:%S}", head]
    for x in r:
        lines.append(f"{x['fire'][:15]:<15} {x['run'][:34]:<34} {x['kind'][:10]:<10} {x['by'][:16]:<16} {x['job']:<10} {x['state'][:10]:<10} "
                     f"{x['elapsed']:>10} {x['limit']:>10} {x['sim']:>11} {('%.0f%%' % x['pct']) if x['pct'] is not None else '-':>5} "
                     f"{('%.2f' % x['sps']) if x['sps'] else '-':>7} {hms(x['eta']):>6}  {x['flags']}")
    if not r:
        lines.append("(no jobs)")
    return "\n".join(lines)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("fire", nargs="?"); ap.add_argument("--mine", action="store_true"); ap.add_argument("--active", action="store_true")
    ap.add_argument("--write")
    a = ap.parse_args()
    txt = table(rows(a.fire, a.mine, a.active))
    if a.write:
        tmp = a.write + ".tmp"
        open(tmp, "w").write(txt + "\n"); os.replace(tmp, a.write)
    print(txt)
