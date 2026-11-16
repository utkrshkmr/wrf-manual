"""The shared static data: one place for every fuel and terrain layer, and a GEOGRID.TBL that can select each by name.

  python3 -m wrfgate.static inventory          every WPS layer under static/ (any folder with an 'index')
  python3 -m wrfgate.static plan               what 'wire' would do, changing nothing
  python3 -m wrfgate.static wire               put layers in their standard places, write the table and LAYERS.txt
  python3 -m wrfgate.static check-job          write a Slurm job that runs geogrid once per layer name and checks the result

Standard places (WRF_ROOT/static/):
  landfire/<LFyyyy>/<FBFM40|FBFM13>/   our conversions of the LANDFIRE downloads, every release and product
  landfire_ncar/<LFyyyy>/FBFM40/        the NCAR/Nisha copies, to reproduce inputs made with them
  elevation/<name>/                     terrain layers, e.g. CA_1s (1 arc-second California)
  WPS_GEOG/                             UCAR's standard geography
Nothing is deleted. A layer that is moved leaves a link at its old path, so anything that used the old path still works."""
import datetime as _dt
import glob
import os
import re
import shutil
import sys
from .common import ROOT

S = os.path.join(ROOT, "static")
T = os.path.join(ROOT, "tables", "fire")


def read_index(d):
    out = {}
    for line in open(os.path.join(d, "index")):
        line = line.split("#")[0]
        if "=" in line:
            k, v = line.split("=", 1)
            out[k.strip().lower()] = v.strip().strip("'\"")
    return out


def inventory():
    rows = []
    idxs = []
    for top in sorted(os.listdir(S)):
        if top == "WPS_GEOG" or not os.path.isdir(os.path.join(S, top)):
            continue
        idxs += glob.glob(os.path.join(S, top, "**", "index"), recursive=True)
    for idx in sorted(idxs):
        d = os.path.dirname(idx)
        try:
            ix = read_index(d)
        except Exception as e:
            rows.append((d, "unreadable index", str(e))); continue
        tiles = len([f for f in os.listdir(d) if re.match(r"^\d{5}-\d{5}\.\d{5}-\d{5}$", f)])
        rows.append((d, ix.get("type", "?"), f"proj={ix.get('projection', '?')} dx={ix.get('dx', '?')} "
                     f"cat={ix.get('category_min', '')}-{ix.get('category_max', '')} tiles={tiles} "
                     f"known=({ix.get('known_x', '')},{ix.get('known_y', '')}) {ix.get('known_lat', '')},{ix.get('known_lon', '')}"))
    return rows


def classify(d):
    """Decide where a layer folder belongs. Returns (standard_path, key, kind) or None if it is not a fuel or terrain layer we manage."""
    rel = d[len(S) + 1:]
    if rel.startswith("WPS_GEOG"):
        return None
    m = re.match(r"landfire/(LF20\d\d)/(FBFM40|FBFM13)$", rel)
    if m:
        key = m.group(1).lower() + ("" if m.group(2) == "FBFM40" else "_fbfm13")
        return d, key, "fuel"
    m = re.match(r"landfire_ncar/(LF20\d\d)/FBFM40$", rel)
    if m:
        return d, "ncar_" + m.group(1).lower(), "fuel"
    m = re.match(r"elevation/([A-Za-z0-9_]+)$", rel)
    if m:
        return d, m.group(1).lower(), "terrain"
    # the earlier snapshots of Nisha's layers: static/LF2016, static/LF2023, static/LF2024 (index at any depth)
    m = re.match(r"(LF20\d\d)(/.*)?$", rel)
    if m:
        ix = read_index(d)
        if ix.get("type") == "categorical":
            return os.path.join(S, "landfire_ncar", m.group(1), "FBFM40"), "ncar_" + m.group(1).lower(), "fuel"
    m = re.match(r"(CA_1s)(/.*)?$", rel)
    if m:
        return os.path.join(S, "elevation", "CA_1s"), "ca_1s", "terrain"
    return None


def plan():
    moves, layers = [], []
    for d, kind, _ in inventory():
        c = classify(d)
        if not c:
            continue
        std, key, k = c
        if os.path.realpath(d) != os.path.realpath(std) and not os.path.islink(d):
            top = d
            # move the whole top-level snapshot folder (e.g. static/LF2024) only when the index sits in it directly
            moves.append((d, std))
        layers.append((key, k, std))
    seen, uniq = set(), []
    for key, k, std in layers:
        if key not in seen:
            seen.add(key); uniq.append((key, k, std))
    return moves, sorted(uniq)


def _block(text, name):
    m = re.search(rf"^\s*name\s*=\s*{name}\s*$.*?^=+\s*$", text, re.M | re.S)
    return m


FUEL_TEMPLATE = """name=NFUEL_CAT
    priority=1
    dest_type=categorical
    dominant_only=NFUEL_CAT
    z_dim_name=fuel_cat
    halt_on_missing=no
    fill_missing=0
{interp}
{paths}
    subgrid=yes
==============================="""

TERRAIN_TEMPLATE = """name=ZSF
    priority=1
    dest_type=continuous
    df_dx=DZDXF
    df_dy=DZDYF
    smooth_option=smth-desmth_special; smooth_passes=1
    halt_on_missing=yes
{interp}
{paths}
    subgrid=yes
==============================="""


def blocks(text):
    """Split a GEOGRID.TBL into its entries: list of (name, entry_text)."""
    out, cur = [], []
    for line in text.splitlines():
        if re.match(r"^\s*=+\s*$", line):
            if any(l.strip() for l in cur):
                body = "\n".join(cur)
                m = re.search(r"^\s*name\s*=\s*(\S+)", body, re.M)
                out.append((m.group(1) if m else "?", body))
            cur = []
        else:
            cur.append(line)
    if any(l.strip() and not l.strip().startswith("#") for l in cur):
        body = "\n".join(cur)
        m = re.search(r"^\s*name\s*=\s*(\S+)", body, re.M)
        out.append((m.group(1) if m else "?", body))
    return out


def validate(text):
    """Problems geogrid would refuse: halt_on_missing=yes together with fill_missing, an entry without a name,
    the same field twice at the same priority."""
    bad, seen = [], {}
    for name, body in blocks(text):
        if name == "?":
            bad.append("an entry has no name"); continue
        halt = re.search(r"^\s*halt_on_missing\s*=\s*yes", body, re.M | re.I)
        fill = re.search(r"^\s*fill_missing\s*=", body, re.M | re.I)
        if halt and fill:
            bad.append(f"{name}: halt_on_missing=yes and fill_missing together")
        pr = (re.search(r"^\s*priority\s*=\s*(\d+)", body, re.M) or [None, "1"])[1]
        if (name, pr) in seen:
            bad.append(f"{name}: two entries with priority {pr}")
        seen[(name, pr)] = 1
    return bad


def table(layers, default_fuel="lf2024", default_terrain="ca_1s"):
    """The current GEOGRID.TBL with every NFUEL_CAT and ZSF entry removed and one clean entry of each added,
    listing every layer by name."""
    src = open(os.path.join(T, "GEOGRID.TBL")).read()
    kept = [body for name, body in blocks(src) if name not in ("NFUEL_CAT", "ZSF")]
    kept = [re.sub(r"^\s*#.*\n?", "", b, flags=re.M) for b in kept]
    kept = [b for b in kept if b.strip()]
    parts = []
    for kind, tmpl, dflt, style in (("fuel", FUEL_TEMPLATE, default_fuel, "nearest_neighbor"),
                                    ("terrain", TERRAIN_TEMPLATE, default_terrain, "average_gcell(4.0)+four_pt+average_4pt")):
        sel = [(k, p) for k, kk, p in layers if kk == kind]
        interp = [f"    interp_option={k}:{style}" for k, _ in sel] + [f"    interp_option=default:{style}"]
        paths = [f"    abs_path={k}:{p}/" for k, p in sel]
        if dict(sel).get(dflt):
            paths.append(f"    abs_path=default:{dict(sel)[dflt]}/")
        parts.append(tmpl.format(interp="\n".join(interp), paths="\n".join(paths)))
    sep = "==============================="
    out = sep + "\n" + ("\n" + sep + "\n").join(b.strip("\n") for b in kept) + "\n" + sep + "\n" + "\n".join(parts) + "\n"
    bad = validate(out)
    if bad:
        raise SystemExit("the new table would not work: " + "; ".join(bad) + "; nothing was written")
    return out


def _rename(src, dst):
    """Move a folder by renaming it (instant, same file system) and leave a link at the old path. Never copies: if a rename is not possible, stop.
    Read-only parent folders (the snapshots were locked) are opened for the rename and locked again after."""
    import stat
    par = os.path.dirname(src)
    mode = os.stat(par).st_mode
    try:
        if not os.access(par, os.W_OK):
            os.chmod(par, mode | stat.S_IWUSR)
        os.rename(src, dst)
        os.symlink(dst, src)
    except OSError as e:
        raise SystemExit(f"could not move {src} to {dst} by renaming ({e.strerror}); nothing was copied. Ask the lab to check the folder's owner and permissions.")
    finally:
        os.chmod(par, mode)


def wire(dry=False):
    moves, layers = plan()
    stamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    for src, dst in moves:
        print(f"move  {src}\n   -> {dst}   (a link is left at the old path)")
        if dry:
            continue
        if os.path.exists(dst):
            print(f"   skipped: {dst} already exists"); continue
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        _rename(src, dst)
    for key, kind, p in layers:
        print(f"layer {key:<16} {kind:<8} {p}")
    if dry:
        return
    os.makedirs(T + "_previous", exist_ok=True)
    keep = os.path.join(T + "_previous", f"GEOGRID.TBL.{stamp}")
    shutil.copy2(os.path.join(T, "GEOGRID.TBL"), keep)
    new = table(layers)
    import stat
    dmode = os.stat(T).st_mode
    fmode = os.stat(os.path.join(T, "GEOGRID.TBL")).st_mode
    tmp = os.path.join(T, ".GEOGRID.TBL.new")
    try:
        os.chmod(T, dmode | stat.S_IWUSR)
        open(tmp, "w").write(new)
        os.chmod(tmp, stat.S_IMODE(fmode))
        os.replace(tmp, os.path.join(T, "GEOGRID.TBL"))
    except OSError as e:
        raise SystemExit(f"could not write {T}/GEOGRID.TBL ({e.strerror}); the old table is unchanged")
    finally:
        os.chmod(T, dmode)
    print(f"wrote {T}/GEOGRID.TBL (previous kept as {keep})")
    with open(os.path.join(S, "LAYERS.txt"), "w") as f:
        f.write(f"# Written with {T}/GEOGRID.TBL by wrfgate.static.\n# Fuel and terrain layers for WPS, {_dt.datetime.now():%Y-%m-%d}. Select one in namelist.wps geog_data_res, e.g.\n"
                f"#   geog_data_res = 'lf2024+default', 'ca_1s+lf2024+default'\n"
                f"# Fire cards set this from fuel_layer automatically. 'default' = lf2024 for fuel, ca_1s for terrain.\n\n")
        for key, kind, p in layers:
            ix = read_index(p)
            f.write(f"{key:<16} {kind:<8} {p}   ({ix.get('projection', '?')}, dx {ix.get('dx', '?')})\n")
    print(f"wrote {S}/LAYERS.txt")


def check_job(out_dir):
    """A Slurm job: geogrid on a small Canyon-area domain, once per layer name; then the fuel layers are compared cell by cell
    with the same layer read directly (exact projection), which shows the name reaches the right files."""
    _, layers = plan()
    os.makedirs(out_dir, exist_ok=True)
    runs = []
    for key, kind, p in layers:
        res = f"'{key}+default', '{key}+default'" if kind == "fuel" else f"'{key}+default', '{key}+lf2024+default'"
        runs.append((key, kind, p, res))
    lines = [f"""#!/bin/bash
#SBATCH -J wg_static_check
#SBATCH -p general-compute
#SBATCH --qos=general-compute
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --mem=32G
#SBATCH -t 03:00:00
#SBATCH -o {out_dir}/check_%j.out
source {ROOT}/pipeline/current/lib/wrfgate.sh
wg_modules
"""]
    for key, kind, p, res in runs:
        d = os.path.join(out_dir, key)
        lines.append(f"""mkdir -p {d}; cd {d}
cat > namelist.wps <<'NL'
&share
 wrf_core = 'ARW', max_dom = 2, start_date = '2025-08-07_18:00:00','2025-08-07_18:00:00', end_date = '2025-08-07_18:00:00','2025-08-07_18:00:00',
 interval_seconds = 3600, io_form_geogrid = 2, subgrid_ratio_x = 0, 4, subgrid_ratio_y = 0, 4,
/
&geogrid
 parent_id = 1, 1, parent_grid_ratio = 1, 9, i_parent_start = 1, 6, j_parent_start = 1, 6,
 e_we = 16, 37, e_sn = 16, 37, geog_data_res = {res},
 dx = 900, dy = 900, map_proj = 'lambert', ref_lat = 34.44, ref_lon = -118.73, truelat1 = 34.44, truelat2 = 34.44, stand_lon = -118.73,
 geog_data_path = '{S}/WPS_GEOG/', opt_geogrid_tbl_path = '{T}/'
/
NL
srun -n 1 geogrid.exe > geogrid.out 2>&1 < /dev/null
python3 -m wrfgate.static verify {d} {key} {kind} {p} >> {out_dir}/RESULTS.txt 2>&1
""")
    lines.append(f"echo; cat {out_dir}/RESULTS.txt\n")
    path = os.path.join(out_dir, "check_static.sbatch")
    open(path, "w").write("".join(lines))
    open(os.path.join(out_dir, "RESULTS.txt"), "w").write(f"layer            kind     result\n")
    return path


def verify(d, key, kind, layer):
    import numpy as np
    from netCDF4 import Dataset
    g = os.path.join(d, "geo_em.d02.nc")
    ok = os.path.exists(g) and "Successful completion" in open(os.path.join(d, "geogrid.log")).read() if os.path.exists(os.path.join(d, "geogrid.log")) else False
    if not ok:
        err = [l.strip() for l in open(os.path.join(d, "geogrid.log"))][-1] if os.path.exists(os.path.join(d, "geogrid.log")) else "no geogrid.log"
        print(f"{key:<16} {kind:<8} FAIL geogrid: {err}"); return
    nc = Dataset(g)
    if kind == "fuel":
        from .geo import WPSLayer
        from .metem import fire_mesh_latlon, fire_field
        lat, lon, shape = fire_mesh_latlon(g, 4)
        v = fire_field(g, "NFUEL_CAT", shape)
        ref = WPSLayer(layer).sample(lat, lon)
        good = np.isfinite(ref)
        same = float((v[good] == ref[good]).mean() * 100) if good.any() else 0.0
        zero = float((v == 0).mean() * 100)
        status = "PASS" if same >= 95 and zero < 5 else "FAIL"
        print(f"{key:<16} {kind:<8} {status} {same:.2f}% of fire cells equal the layer read directly; {zero:.1f}% empty; codes {sorted(set(np.unique(v).astype(int)))[:12]}")
    else:
        z = np.asarray(nc["ZSF"][0]); h = np.asarray(nc["HGT_M"][0])
        status = "PASS" if np.isfinite(z).all() and z.max() > 0 and abs(float(z.mean()) - float(h.mean())) < 100 else "FAIL"
        print(f"{key:<16} {kind:<8} {status} ZSF {z.min():.0f} to {z.max():.0f} m, mean {z.mean():.0f} m (atmosphere terrain mean {h.mean():.0f} m)")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        print(__doc__); raise SystemExit(1)
    if a[0] == "inventory":
        for r in inventory():
            print(f"{r[0]}\n    {r[1]}  {r[2]}")
    elif a[0] == "plan":
        wire(dry=True)
    elif a[0] == "wire":
        wire()
    elif a[0] == "check-job":
        print(check_job(a[1] if len(a) > 1 else os.path.join(ROOT, "tests", "static_check")))
    elif a[0] == "check-table":
        txt = open(os.path.join(T, "GEOGRID.TBL")).read()
        names = [n for n, _ in blocks(txt)]
        print(f"{len(names)} entries: " + ", ".join(names))
        for n in ("NFUEL_CAT", "ZSF"):
            print(f"{n}: {names.count(n)} entr{'y' if names.count(n) == 1 else 'ies'}")
        bad = validate(txt)
        print("problems: " + ("; ".join(bad) if bad else "none"))
    elif a[0] == "verify":
        verify(*a[1:5])
    else:
        print(__doc__); raise SystemExit(1)
