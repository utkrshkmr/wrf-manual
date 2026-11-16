"""Fire cards: every fire described by the same short list of settings.

  python3 -m wrfgate.card show FIRE [--spec NAME]     the card of a registered fire, from its files
  python3 -m wrfgate.card template                      a blank card with the lab defaults
  python3 -m wrfgate.card make CARD OUTDIR              namelist.wps, wps.sbatch and a spec from a filled card

A card is 'key: value' lines with # comments. A card printed by 'show' is a valid input for 'make':
copy it, change the name and what differs, and make a new fire from it."""
import datetime as _dt
import glob
import json
import math
import os
import sys
from .common import ROOT, read_record, parse_time, get_namelist, set_namelist, split_assignments

FIELDS = [
    ("Fire", [
        ("name", "", "UPPER_CASE with the year, e.g. CANYON_2025"),
        ("note", "", "one line: what this run is"),
    ]),
    ("When (UTC)", [
        ("start", "", "first weather time, YYYY-MM-DD HH:MM"),
        ("end", "", "last weather time"),
        ("ignition_time", "", "when the fire starts"),
    ]),
    ("Where", [
        ("ignition_lat", "", "degrees north"),
        ("ignition_lon", "", "degrees east (negative in the US)"),
        ("ignition_radius_m", "50", "initial burning circle"),
        ("center_lat", "", "domain centre; blank = the ignition point"),
        ("center_lon", "", ""),
    ]),
    ("Domains", [
        ("outer_cells", "54", "outer domain cells per side (or NXxNY)"),
        ("outer_dx_m", "900", "outer cell size"),
        ("fire_cells", "217", "fire domain cells per side (or NXxNY); (cells-1) must divide by fire_ratio"),
        ("fire_ratio", "9", "outer dx / fire-domain dx"),
        ("fire_start_i", "", "fire domain's lower-left corner in outer cells; blank = centred"),
        ("fire_start_j", "", ""),
        ("fire_mesh_ratio", "4", "fire mesh cells per fire-domain cell, each way"),
    ]),
    ("Data", [
        ("weather", "HRRR", "weather product"),
        ("weather_dir", f"{ROOT}/inputs/weather/hrrr", "folder with the GRIB files (searched below it)"),
        ("weather_files", "wrfprsf00", "text every weather file name contains"),
        ("weather_interval_s", "3600", "time between weather files: 3600 HRRR, 10800 for 3-hourly products"),
        ("vtable", "Vtable.HRRR.prs", "Vtable in tables/fire/ for this product"),
        ("fuel_layer", f"{ROOT}/static/landfire/LF2024/FBFM40", "LANDFIRE reference for gate B; pick the release before the fire"),
        ("fuel_key", "lf2024", "GEOGRID.TBL resolution key for the fuel"),
        ("terrain_layer", f"{ROOT}/static/CA_1s", "elevation reference for gate B"),
        ("terrain_key", "ca_1s", "GEOGRID.TBL resolution key for the fire terrain"),
    ]),
    ("Fire model", [
        ("fuel_moisture", "0.08", "dead fuel moisture, fraction (fuelmc_g); 0.08 = 8%"),
        ("fire_feedback", "1.0", "fire_atm_feedback: 1 = full coupling, 0 = one-way"),
        ("slope_factor", "1.0", "fire_slope_factor"),
        ("wind_height_m", "6.096", "fire_wind_height"),
    ]),
    ("Run", [
        ("time_step_s", "", "outer time step; blank = the base spec's"),
        ("history_minutes", "", "output interval on the fire domain; blank = the base spec's"),
        ("base_spec", "CANYON_2025/campaign", "spec whose physics and other settings are reused"),
    ]),
]
KEYS = [k for _, items in FIELDS for k, _, _ in items]


def render(values, measured=None, title=None):
    out = []
    if title:
        out.append(f"# {title}")
    for group, items in FIELDS:
        out.append(f"\n# --- {group}")
        for k, d, help_ in items:
            v = values.get(k, d)
            out.append(f"{k + ':':<20} {v}" + (f"   # {help_}" if help_ and not values.get('_nohelp') else ""))
    if measured:
        out.append("\n# --- Measured from the fire's files (read-only, ignored when making a fire)")
        for k, v in measured.items():
            out.append(f"# {k + ':':<26} {v}")
    return "\n".join(out) + "\n"


def size(s):
    s = str(s).lower().replace(" ", "")
    if "x" in s:
        a, b = s.split("x"); return int(a), int(b)
    return int(s), int(s)


def _first(nl, name, i=0, default=""):
    v = get_namelist(nl, name)
    if not v:
        return default
    return v[min(i, len(v) - 1)]


def show(fire, spec="campaign"):
    F = os.path.join(ROOT, "fires", fire)
    rec = read_record(os.path.join(F, "fire.yaml"))
    v = {"name": fire, "note": rec.get("note", ""), "start": rec["start"][:16], "end": rec["end"][:16],
         "ignition_time": rec["ignition_time"][:16], "ignition_lat": rec.get("ignition_lat", ""),
         "ignition_lon": rec.get("ignition_lon", ""), "ignition_radius_m": rec.get("ignition_radius_m", ""),
         "fuel_layer": rec.get("fuel_layer", ""), "terrain_layer": rec.get("terrain_layer", ""), "base_spec": f"{fire}/{spec}"}
    for k in ["weather", "weather_dir", "weather_files", "vtable", "fuel_key", "terrain_key", "center_lat", "center_lon"]:
        v[k] = "(not recorded)"
    v["fuel_layer"] = v["fuel_layer"] or "(not recorded)"
    v["terrain_layer"] = v["terrain_layer"] or "(not recorded)"
    meas = {}
    sd = os.path.join(F, "specs", spec)
    nl = open(os.path.join(sd, "namelist.input")).read() if os.path.exists(os.path.join(sd, "namelist.input")) else ""
    nf = open(os.path.join(sd, "namelist.fire")).read() if os.path.exists(os.path.join(sd, "namelist.fire")) else ""
    if nl:
        md = int(_first(nl, "max_dom", 0, "1"))
        srs = get_namelist(nl, "sr_x") or ["0"]
        fd = max(range(md), key=lambda i: int(float(srs[min(i, len(srs) - 1)])))
        ex = lambda n, i: _first(nl, n, i)
        v["outer_cells"] = ex("e_we", 0) if ex("e_we", 0) == ex("e_sn", 0) else f"{ex('e_we', 0)}x{ex('e_sn', 0)}"
        v["outer_dx_m"] = ex("dx", 0)
        v["fire_cells"] = ex("e_we", fd) if ex("e_we", fd) == ex("e_sn", fd) else f"{ex('e_we', fd)}x{ex('e_sn', fd)}"
        v["fire_ratio"] = str(int(float(ex("dx", 0)) / float(ex("dx", fd)) + 0.5)) if ex("dx", fd) else ex("parent_grid_ratio", fd)
        v["fire_start_i"], v["fire_start_j"] = ex("i_parent_start", fd), ex("j_parent_start", fd)
        v["fire_mesh_ratio"] = ex("sr_x", fd)
        v["fire_feedback"] = ex("fire_atm_feedback", fd) or "1.0 (default)"
        v["slope_factor"] = ex("fire_slope_factor", fd) or "1.0 (default)"
        v["wind_height_m"] = ex("fire_wind_height", fd) or "6.096 (default)"
        v["time_step_s"] = ex("time_step", 0)
        v["weather_interval_s"] = ex("interval_seconds", 0)
        v["history_minutes"] = ex("history_interval", fd)
        if md > 2:
            meas["domains"] = f"{md} (cards describe the outer and the fire domain only)"
        phys = [f"{n}={ex(n, 0)}" for n in ["mp_physics", "bl_pbl_physics", "sf_sfclay_physics", "sf_surface_physics",
                                              "ra_lw_physics", "ra_sw_physics", "cu_physics"] if ex(n, 0)]
        if phys:
            meas["physics (from the spec)"] = ", ".join(phys)
        meas["fire_fuel_read"] = (ex("fire_fuel_read", fd) or "-1 (default)") + ("   <- not -1: the fuel map in the inputs is NOT used" if ex("fire_fuel_read", fd) not in ("", "-1") else "")
        meas["fire_fmc_read"] = ex("fire_fmc_read", fd) or "1 (default)"
        import re as _re
        fire_grp = _re.search(r"&fire(.*?)^\s*/", split_assignments(nl), _re.S | _re.M | _re.I)
        covered = {"ifire", "fire_fuel_read", "fire_num_ignitions", "fire_ignition_start_lat1", "fire_ignition_start_lon1",
                   "fire_ignition_end_lat1", "fire_ignition_end_lon1", "fire_ignition_start_time1", "fire_ignition_radius1",
                   "fire_atm_feedback", "fire_slope_factor", "fire_wind_height", "fire_fmc_read"}
        if fire_grp:
            other = []
            for m_ in _re.finditer(r"^\s*([A-Za-z_0-9]+)\s*=", fire_grp.group(1), _re.M):
                n_ = m_.group(1).lower()
                if n_ not in covered:
                    other.append(f"{n_}={ex(n_, fd)}")
            if other:
                meas["other &fire settings (fire domain)"] = ", ".join(other)
        meas["num_metgrid_levels"] = ex("num_metgrid_levels", 0)
    if nf:
        v["fuel_moisture"] = _first(nf, "fuelmc_g") or "0.08 (default)"
    else:
        v["fuel_moisture"] = "0.08 (default: no namelist.fire in the spec)"
        if _first(nf, "nfuelcats"):
            meas["nfuelcats"] = _first(nf, "nfuelcats")
    cur = os.path.join(F, "inputs", "current")
    if os.path.exists(cur):
        ver = os.path.basename(os.path.realpath(cur))
        meas["inputs"] = ver
        wps = os.path.join(cur, "namelist.wps")
        if os.path.exists(wps):
            w = open(wps).read()
            v["center_lat"], v["center_lon"] = _first(w, "ref_lat"), _first(w, "ref_lon")
            res = get_namelist(w, "geog_data_res") or []
            if len(res) > 1:
                keys = res[-1].split("+")
                v["fuel_key"] = next((k for k in keys if k.startswith("lf")), v["fuel_key"])
                v["terrain_key"] = next((k for k in keys if not k.startswith("lf") and k != "default"), v["terrain_key"])
            res = get_namelist(w, "geog_data_res") or []
            if res:
                meas["geog_data_res"] = ", ".join(res)
        if v.get("center_lat") in ("", "(not recorded)"):
            try:
                from .metem import attrs
                d1 = sorted(glob.glob(os.path.join(cur, "met_em.d01.*")))[0]
                at = attrs(d1)
                v["center_lat"], v["center_lon"] = f"{float(at['CEN_LAT']):.5f}", f"{float(at['CEN_LON']):.5f}"
            except Exception:
                pass
        for g in "AB":
            p = os.path.realpath(cur) + f".gates/gate_{g}.json"
            if os.path.exists(p):
                j = json.load(open(p))
                meas[f"gate {g}"] = j["status"]
                fa = j.get("facts", {})
                if g == "A":
                    for k in ["rank_cap", "burnable_pct", "ignition_edge_km", "interval_s"]:
                        if k in fa:
                            meas[k] = fa[k]
                if g == "B":
                    for k in ["fuel_agreement_pct", "terrain_rmse_m"]:
                        if k in fa:
                            meas[k] = fa[k]
                    if fa.get("release_scan"):
                        best = max(fa["release_scan"].items(), key=lambda x: x[1])
                        meas["best LANDFIRE release"] = f"{best[0]} ({best[1]}%)"
        src = [l.split(":", 1)[1].strip() for l in open(os.path.join(cur, "MANIFEST.txt")) if l.startswith("source:")]
        if src:
            meas["met_em copied from"] = src[0]
    runs = sorted(glob.glob(os.path.join(F, "runs", "*", "MANIFEST.txt")))
    for r in reversed(runs):
        m = read_record(r)
        if m.get("kind") == "production":
            meas["last run"] = f"{os.path.basename(os.path.dirname(r))}: {m.get('nodes')} nodes, {m.get('ranks')} ranks, {m.get('time')} {m.get('constraint', '')}".strip()
            break
    v["_nohelp"] = True
    return render(v, meas, title=f"Fire card for {fire} (spec {spec}), printed {_dt.datetime.now():%Y-%m-%d %H:%M}")


def parse(path):
    c = read_record(path)
    c = {k: ("" if v.startswith("(") else v) for k, v in c.items()}
    unknown = [k for k in c if k not in KEYS]
    if unknown:
        raise SystemExit(f"unknown keys in the card: {', '.join(unknown)}")
    for _, items in FIELDS:
        for k, d, _ in items:
            if not c.get(k):
                c[k] = d
    for k in ["name", "start", "end", "ignition_time", "ignition_lat", "ignition_lon"]:
        if not c.get(k):
            raise SystemExit(f"the card needs {k}")
    c["center_lat"] = c["center_lat"] or c["ignition_lat"]
    c["center_lon"] = c["center_lon"] or c["ignition_lon"]
    for k in ["fire_feedback", "slope_factor", "wind_height_m", "fuel_moisture", "time_step_s", "history_minutes"]:
        c[k] = c[k].split()[0] if c[k] else ""
    return c


def check(c):
    """Return (errors, notes) for a card's geometry and times."""
    err, note = [], []
    t0, t1, ti = parse_time(c["start"]), parse_time(c["end"]), parse_time(c["ignition_time"])
    if not t0 < ti < t1:
        err.append("ignition_time must be after start and before end")
    if (ti - t0).total_seconds() < 3600:
        note.append("less than an hour of weather before ignition: the winds have little time to settle")
    ox, oy = size(c["outer_cells"]); fx, fy = size(c["fire_cells"]); r = int(c["fire_ratio"])
    if (fx - 1) % r or (fy - 1) % r:
        err.append(f"fire_cells - 1 must divide by fire_ratio {r} (try {((fx - 1) // r) * r + 1})")
    px, py = (fx - 1) // r, (fy - 1) // r
    i = int(c["fire_start_i"]) if c["fire_start_i"] else (ox - px) // 2 + 1
    j = int(c["fire_start_j"]) if c["fire_start_j"] else (oy - py) // 2 + 1
    c["fire_start_i"], c["fire_start_j"] = str(i), str(j)
    if i < 6 or j < 6 or i + px > ox - 5 or j + py > oy - 5:
        err.append(f"the fire domain ({px}x{py} outer cells from ({i},{j})) needs at least 5 outer cells of margin inside {ox}x{oy}")
    dx = float(c["outer_dx_m"]); fdx = dx / r
    km_lat = 111.2; km_lon = 111.2 * math.cos(math.radians(float(c["center_lat"])))
    # fire domain centre relative to the outer centre (outer centre = centre point)
    cx = ((i - 1) + px / 2 - ox / 2) * dx / 1000; cy = ((j - 1) + py / 2 - oy / 2) * dx / 1000
    ex = (float(c["ignition_lon"]) - float(c["center_lon"])) * km_lon - cx
    ey = (float(c["ignition_lat"]) - float(c["center_lat"])) * km_lat - cy
    hx, hy = (fx - 1) * fdx / 2000, (fy - 1) * fdx / 2000
    margin = min(hx - abs(ex), hy - abs(ey))
    if margin < 0:
        err.append("the ignition is outside the fire domain")
    elif margin < 2:
        err.append(f"the ignition is only {margin:.1f} km from the fire domain's edge (need 2 km; more for a big fire)")
    else:
        note.append(f"ignition about {margin:.1f} km from the nearest fire-domain edge; fire domain {2 * hx:.1f} x {2 * hy:.1f} km at {fdx:.0f} m, fire mesh {fdx / int(c['fire_mesh_ratio']):.0f} m")
    cap = min((ox // 10) * (oy // 10), (fx // 10) * (fy // 10))
    note.append(f"rank cap {cap}")
    return err, note


def namelist_wps(c):
    t0, t1 = parse_time(c["start"]), parse_time(c["end"])
    ox, oy = size(c["outer_cells"]); fx, fy = size(c["fire_cells"])
    s, e, m = f"{t0:%Y-%m-%d_%H:%M:%S}", f"{t1:%Y-%m-%d_%H:%M:%S}", c["fire_mesh_ratio"]
    return f"""&share
 wrf_core = 'ARW', max_dom = 2,
 start_date = '{s}','{s}',
 end_date   = '{e}','{e}',
 interval_seconds = {c['weather_interval_s']}, io_form_geogrid = 2,
 subgrid_ratio_x = 0, {m}, subgrid_ratio_y = 0, {m},
/
&geogrid
 parent_id = 1, 1,  parent_grid_ratio = 1, {c['fire_ratio']},
 i_parent_start = 1, {c['fire_start_i']},  j_parent_start = 1, {c['fire_start_j']},
 e_we = {ox}, {fx},  e_sn = {oy}, {fy},
 geog_data_res = '{c['fuel_key']}+default', '{c['terrain_key']}+{c['fuel_key']}+default',
 dx = {c['outer_dx_m']}, dy = {c['outer_dx_m']}, map_proj = 'lambert',
 ref_lat = {c['center_lat']}, ref_lon = {c['center_lon']},
 truelat1 = {c['center_lat']}, truelat2 = {c['center_lat']}, stand_lon = {c['center_lon']},
 geog_data_path = '{ROOT}/static/WPS_GEOG/',
 opt_geogrid_tbl_path = '{ROOT}/tables/fire/'
/
&ungrib
 out_format = 'WPS', prefix = 'FILE',
/
&metgrid
 fg_name = 'FILE', io_form_metgrid = 2,
 opt_metgrid_tbl_path = '{ROOT}/tables/fire/'
/
"""


def put(text, name, value, group):
    try:
        return set_namelist(text, name, value)
    except KeyError:
        text = split_assignments(text)
        return text.replace(f"&{group}", f"&{group}\n {name} = {value},", 1)


def spec(c):
    bf, _, bs = c["base_spec"].partition("/")
    base = os.path.join(ROOT, "fires", bf, "specs", bs or "campaign")
    nl_p = os.path.join(base, "namelist.input")
    if not os.path.exists(nl_p):
        raise SystemExit(f"base spec not found: {nl_p} (base_spec is FIRE/SPEC, e.g. CANYON_2025/campaign)")
    nl = open(nl_p).read()
    nf = open(os.path.join(base, "namelist.fire")).read() if os.path.exists(os.path.join(base, "namelist.fire")) else ""
    t0, t1, ti = parse_time(c["start"]), parse_time(c["end"]), parse_time(c["ignition_time"])
    ox, oy = size(c["outer_cells"]); fx, fy = size(c["fire_cells"]); r = c["fire_ratio"]
    fdx = float(c["outer_dx_m"]) / int(r)
    two = lambda a, b: f"{a}, {b}"
    try:
        ign_len = max(1, int(float(_first(nl, "fire_ignition_end_time1", 1)) - float(_first(nl, "fire_ignition_start_time1", 1))))
    except ValueError:
        ign_len = 60
    sets = [("time_control", "run_days", "0"), ("time_control", "run_hours", "0"), ("time_control", "run_minutes", "0"),
            ("time_control", "run_seconds", "0")]
    for k, fmt in [("year", "%Y"), ("month", "%m"), ("day", "%d"), ("hour", "%H"), ("minute", "%M"), ("second", "%S")]:
        sets += [("time_control", f"start_{k}", two(t0.strftime(fmt), t0.strftime(fmt))),
                 ("time_control", f"end_{k}", two(t1.strftime(fmt), t1.strftime(fmt)))]
    sets += [("time_control", "interval_seconds", c["weather_interval_s"]),
             ("domains", "max_dom", "2"), ("domains", "e_we", two(ox, fx)), ("domains", "e_sn", two(oy, fy)),
             ("domains", "dx", two(c["outer_dx_m"], f"{fdx:g}")), ("domains", "dy", two(c["outer_dx_m"], f"{fdx:g}")),
             ("domains", "grid_id", "1, 2"), ("domains", "parent_id", "0, 1"),
             ("domains", "parent_grid_ratio", two(1, r)), ("domains", "parent_time_step_ratio", two(1, r)),
             ("domains", "i_parent_start", two(1, c["fire_start_i"])), ("domains", "j_parent_start", two(1, c["fire_start_j"])),
             ("domains", "sr_x", two(0, c["fire_mesh_ratio"])), ("domains", "sr_y", two(0, c["fire_mesh_ratio"])),
             ("fire", "ifire", "0, 2"), ("fire", "fire_fuel_read", "-1, -1"), ("fire", "fire_num_ignitions", "0, 1"),
             ("fire", "fire_ignition_start_lat1", two(0, c["ignition_lat"])), ("fire", "fire_ignition_end_lat1", two(0, c["ignition_lat"])),
             ("fire", "fire_ignition_start_lon1", two(0, c["ignition_lon"])), ("fire", "fire_ignition_end_lon1", two(0, c["ignition_lon"])),
             ("fire", "fire_ignition_start_time1", two(0, int((ti - t0).total_seconds()))),
             ("fire", "fire_ignition_end_time1", two(0, int((ti - t0).total_seconds()) + ign_len)),
             ("fire", "fire_ignition_radius1", two(0, c["ignition_radius_m"])),
             ("fire", "fire_atm_feedback", two(0, c["fire_feedback"])), ("fire", "fire_slope_factor", two(0, c["slope_factor"])),
             ("fire", "fire_wind_height", two(0, c["wind_height_m"]))]
    if c["time_step_s"]:
        sets.append(("domains", "time_step", c["time_step_s"]))
    if c["history_minutes"]:
        sets.append(("time_control", "history_interval", two(60, c["history_minutes"])))
    for g, k, val in sets:
        nl = put(nl, k, val, g)
    if nf:
        nf = put(nf, "fuelmc_g", c["fuel_moisture"], "fuel_scalars")
    return nl, nf


def wps_job(c, out):
    t0, t1 = parse_time(c["start"]), parse_time(c["end"])
    return f"""#!/bin/bash
#SBATCH -J wps_{c['name']}
#SBATCH -p general-compute
#SBATCH --qos=general-compute
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --mem=64G
#SBATCH -t 08:00:00
#SBATCH -o {out}/wps_%j.out
source {ROOT}/pipeline/current/lib/wrfgate.sh
wg_person >/dev/null 2>&1
module purge
module load gcc/11.2.0 openmpi/4.1.1 wps/4.6.0-dmpar
cd {out}
wg_log event=wps_start fire={c['name']} folder={out} job=$SLURM_JOB_ID
srun -n 1 geogrid.exe < /dev/null
grep -q "Successful completion" geogrid.log || {{ wg_log event=wps_end fire={c['name']} step=geogrid status=FAIL; exit 1; }}
python3 - <<'PY' > grib.list || {{ echo "weather files missing (see above)"; wg_log event=wps_end fire={c['name']} step=weather status=FAIL; exit 1; }}
import os, re, datetime as d
t0, t1 = d.datetime({t0.year}, {t0.month}, {t0.day}, {t0.hour}), d.datetime({t1.year}, {t1.month}, {t1.day}, {t1.hour})
want = {{}}
for root, _, files in os.walk("{c['weather_dir']}"):
    for f in files:
        p = os.path.join(root, f)
        if "{c['weather_files']}" not in f:
            continue
        m = re.search(r"(\\d{{8}})\\D*?t?(\\d\\d)z", p) or re.search(r"(\\d{{8}})(\\d\\d)", p)
        if m:
            t = d.datetime.strptime(m.group(1) + m.group(2), "%Y%m%d%H")
            if t0 <= t <= t1 and (t - t0).total_seconds() % {c['weather_interval_s']} == 0:
                want[t] = p
missing = int((t1 - t0).total_seconds() // {c['weather_interval_s']}) + 1 - len(want)
if missing:
    import sys; print(f"missing {{missing}} weather files between {{t0}} and {{t1}} under {c['weather_dir']}", file=sys.stderr); sys.exit(1)
for t in sorted(want):
    print(want[t])
PY
[[ -s grib.list ]] || {{ echo "no weather files found"; wg_log event=wps_end fire={c['name']} step=link status=FAIL; exit 1; }}
csh $EBROOTWPS/WPS-4.6.0/link_grib.csh $(cat grib.list)
ln -sf {ROOT}/tables/fire/{c['vtable']} Vtable
srun -n 1 ungrib.exe < /dev/null
grep -q "Successful completion" ungrib.log || {{ wg_log event=wps_end fire={c['name']} step=ungrib status=FAIL; exit 1; }}
srun -n 1 metgrid.exe < /dev/null
grep -q "Successful completion" metgrid.log || {{ wg_log event=wps_end fire={c['name']} step=metgrid status=FAIL; exit 1; }}
wg_log event=wps_end fire={c['name']} status=OK
{ROOT}/pipeline/current/bin/wrf-add-inputs {c['name']} {out} --note "WPS from fire card"
"""


def make(card_path, out):
    c = parse(card_path)
    err, notes = check(c)
    for n in notes:
        print("note:", n)
    if err:
        for e in err:
            print("error:", e)
        raise SystemExit(1)
    os.makedirs(os.path.join(out, "spec"), exist_ok=True)
    nl, nf = spec(c)
    open(os.path.join(out, "namelist.wps"), "w").write(namelist_wps(c))
    open(os.path.join(out, "spec", "namelist.input"), "w").write(nl)
    if nf:
        open(os.path.join(out, "spec", "namelist.fire"), "w").write(nf)
    open(os.path.join(out, "wps.sbatch"), "w").write(wps_job(c, out))
    c2 = dict(c); c2["_nohelp"] = True
    open(os.path.join(out, "fire.card"), "w").write(render(c2, title=f"Fire card for {c['name']}, as used to make this folder"))
    print(f"wrote {out}/namelist.wps, wps.sbatch, spec/namelist.input" + (", spec/namelist.fire" if nf else "") + ", fire.card")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] not in ("show", "template", "make"):
        print(__doc__); raise SystemExit(1)
    if a[0] == "template":
        print(render({}, title="New fire card: fill the blanks, keep or change the defaults. Times are UTC."), end="")
    elif a[0] == "show":
        sp = a[a.index("--spec") + 1] if "--spec" in a else "campaign"
        print(show(a[1], sp), end="")
    else:
        make(a[1], a[2])
