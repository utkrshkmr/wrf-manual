"""Shared pieces of the WRF-Fire gating system: paths, records, ledger, gate results."""
import datetime as _dt
import fcntl
import getpass
import hashlib
import json
import os
import re
import socket

ROOT = os.environ.get("WRF_ROOT", "/projects/academic/negarkhodoe/wrf")
RELEASE = os.environ.get("WRFGATE_RELEASE", "dev")


def now():
    return _dt.datetime.now().astimezone().isoformat(timespec="seconds")


def fire_dir(fire):
    return os.path.join(ROOT, "fires", fire)


def read_record(path):
    """Read a flat 'key: value' YAML file (comments with #). Values stay strings."""
    rec = {}
    for line in open(path):
        line = line.split("#", 1)[0].rstrip()
        if not line.strip() or ":" not in line:
            continue
        k, v = line.split(":", 1)
        rec[k.strip()] = v.strip().strip('"').strip("'")
    return rec


def write_record(path, rec, header=""):
    with open(path, "w") as f:
        if header:
            f.write("".join(f"# {h}\n" for h in header.splitlines()))
        for k, v in rec.items():
            f.write(f"{k}: {v}\n")


def parse_time(s):
    s = s.strip().replace("_", " ").replace("T", " ").rstrip("Z")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return _dt.datetime.strptime(s, fmt)
        except ValueError:
            pass
    raise ValueError(f"cannot read time '{s}' (use YYYY-MM-DD HH:MM[:SS], UTC)")


def ledger_append(event):
    """Append one JSON line to ledger/commands.jsonl, chained to the previous line's hash."""
    path = os.path.join(ROOT, "ledger", "commands.jsonl")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    event = {"t": now(), "user": getpass.getuser(), "host": socket.gethostname(),
             "release": RELEASE, "job": os.environ.get("SLURM_JOB_ID", ""), **event}
    with open(path, "a+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        f.seek(0)
        prev = "0" * 64
        for line in f:
            if line.strip():
                try:
                    prev = json.loads(line)["hash"]
                except (ValueError, KeyError):
                    prev = "corrupt"
        event["prev"] = prev
        body = json.dumps(event, sort_keys=True)
        event["hash"] = hashlib.sha256((prev + body).encode()).hexdigest()
        f.seek(0, 2)
        f.write(json.dumps(event, sort_keys=True) + "\n")
        fcntl.flock(f, fcntl.LOCK_UN)
    return event["hash"]


def ledger_verify(path=None):
    path = path or os.path.join(ROOT, "ledger", "commands.jsonl")
    prev, n = "0" * 64, 0
    for i, line in enumerate(open(path), 1):
        if not line.strip():
            continue
        e = json.loads(line)
        h = e.pop("hash")
        if e.get("prev") != prev:
            return False, f"line {i}: chain broken (prev does not match line {i-1})"
        if hashlib.sha256((prev + json.dumps(e, sort_keys=True)).encode()).hexdigest() != h:
            return False, f"line {i}: content changed after it was written"
        prev, n = h, n + 1
    return True, f"{n} lines, chain intact"


def sha256_file(path, block=1 << 22):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(block), b""):
            h.update(b)
    return h.hexdigest()


class Gate:
    """Collects checks for one gate and writes them as text and JSON."""
    ORDER = {"PASS": 0, "INFO": 0, "WARN": 1, "FAIL": 2}

    def __init__(self, name, target):
        self.name, self.target, self.checks, self.facts = name, target, [], {}

    def check(self, cid, status, text):
        assert status in self.ORDER, status
        self.checks.append((cid, status, text))
        print(f"  {status:4s}  {cid:22s} {text}", flush=True)

    def ok(self, cid, cond, good, bad, warn_only=False):
        self.check(cid, "PASS" if cond else ("WARN" if warn_only else "FAIL"), good if cond else bad)
        return cond

    @property
    def status(self):
        worst = max((self.ORDER[s] for _, s, _ in self.checks), default=0)
        return ["PASS", "WARN", "FAIL"][worst]

    def write(self, folder):
        os.makedirs(folder, exist_ok=True)
        rec = {"gate": self.name, "target": self.target, "status": self.status, "time": now(),
               "user": getpass.getuser(), "release": RELEASE, "facts": self.facts,
               "checks": [{"id": c, "status": s, "text": t} for c, s, t in self.checks]}
        with open(os.path.join(folder, f"gate_{self.name}.json"), "w") as f:
            json.dump(rec, f, indent=1, default=str)
        with open(os.path.join(folder, "GATES.txt"), "a") as f:
            f.write(f"\n== gate {self.name}  {self.status}  {rec['time']}  {rec['user']}  release {RELEASE}\n")
            f.write(f"   target {self.target}\n")
            for c, s, t in self.checks:
                f.write(f"   {s:4s}  {c:22s} {t}\n")
        print(f"== gate {self.name}: {self.status}  ({sum(s == 'FAIL' for _, s, _ in self.checks)} fail, "
              f"{sum(s == 'WARN' for _, s, _ in self.checks)} warn)", flush=True)
        return self.status


def split_assignments(text):
    """Put every 'name = values' on its own line, so 'a = 1, b = 2,' on one line reads as two variables."""
    return re.sub(r",[ \t]*([A-Za-z_][A-Za-z0-9_]*[ \t]*=)", r",\n \1", text)


def set_namelist(text, name, values):
    """Set a namelist variable that is already present; values is a string as it should appear."""
    text = split_assignments(text)
    pat = re.compile(rf"^(\s*){re.escape(name)}\s*=.*?(?=^\s*[A-Za-z_][A-Za-z0-9_]*\s*=|^\s*/)", re.M | re.S | re.I)
    if pat.search(text):
        return pat.sub(lambda m: f"{m.group(1)}{name} = {values},\n", text, count=1)
    raise KeyError(f"{name} not found in namelist; add it by hand to the right group")


def get_namelist(text, name):
    """Return the value list of a namelist variable as strings, or None."""
    text = split_assignments(text)
    m = re.search(rf"^\s*{re.escape(name)}\s*=(.*?)(?=^\s*[A-Za-z_][A-Za-z0-9_]*\s*=|^\s*/)", text, re.M | re.S | re.I)
    if not m:
        return None
    raw = re.sub(r"!.*", "", m.group(1))
    return [v.strip().strip("'\"") for v in raw.replace("\n", " ").split(",") if v.strip()]
