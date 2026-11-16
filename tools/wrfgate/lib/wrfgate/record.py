"""Create a fire record (fire.yaml) from explicit values or from a namelist.input that was used for the fire.
usage: python3 -m wrfgate.record OUT.yaml FIRE [--from-namelist NL] [--start T] [--end T] [--ignition T] [--lat X] [--lon Y] [--note TEXT]"""
import argparse
import datetime as _dt
from .common import get_namelist, write_record, parse_time, now


def from_namelist(path):
    nl = open(path).read()
    g = lambda n, i=0, d=None: (get_namelist(nl, n) or [d])[min(i, len(get_namelist(nl, n) or [d]) - 1)]
    start = _dt.datetime(int(g("start_year")), int(g("start_month")), int(g("start_day")), int(g("start_hour", 0, 0)),
                         int(g("start_minute", 0, 0)), int(g("start_second", 0, 0)))
    if get_namelist(nl, "end_year"):
        end = _dt.datetime(int(g("end_year")), int(g("end_month")), int(g("end_day")), int(g("end_hour", 0, 0)),
                           int(g("end_minute", 0, 0)), int(g("end_second", 0, 0)))
    else:
        end = start + _dt.timedelta(days=int(g("run_days", 0, 0)), hours=int(g("run_hours", 0, 0)), minutes=int(g("run_minutes", 0, 0)))
    md = int(g("max_dom", 0, 1))
    srs = get_namelist(nl, "sr_x") or ["0"]
    fd = max(range(md), key=lambda i: int(float(srs[min(i, len(srs) - 1)])))
    t = float(g("fire_ignition_start_time1", fd, 0))
    rec = {"start": f"{start:%Y-%m-%d %H:%M:%S}", "end": f"{end:%Y-%m-%d %H:%M:%S}",
           "ignition_time": f"{start + _dt.timedelta(seconds=t):%Y-%m-%d %H:%M:%S}",
           "ignition_lat": g("fire_ignition_start_lat1", fd), "ignition_lon": g("fire_ignition_start_lon1", fd),
           "ignition_radius_m": g("fire_ignition_radius1", fd, ""), "fire_domain": f"d{fd + 1:02d}"}
    return rec


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("out"); ap.add_argument("fire"); ap.add_argument("--from-namelist")
    for k in ["start", "end", "ignition", "lat", "lon", "note", "fuel_layer", "terrain_layer", "min_edge_km", "source"]:
        ap.add_argument("--" + k.replace("_", "-"))
    a = ap.parse_args()
    rec = {"fire": a.fire}
    if a.from_namelist:
        rec.update(from_namelist(a.from_namelist)); rec["record_source"] = a.from_namelist
    for k, key in [("start", "start"), ("end", "end"), ("ignition", "ignition_time"), ("lat", "ignition_lat"), ("lon", "ignition_lon")]:
        v = getattr(a, k)
        if v:
            rec[key] = v
    for k in ["start", "end", "ignition_time"]:
        if k not in rec:
            raise SystemExit(f"missing {k}: give --{k.split('_')[0]} or --from-namelist")
        rec[k] = f"{parse_time(rec[k]):%Y-%m-%d %H:%M:%S}"
    for k in ["fuel_layer", "terrain_layer", "min_edge_km", "note", "source"]:
        if getattr(a, k):
            rec[k] = getattr(a, k)
    rec["created"] = now()
    write_record(a.out, rec, "Fire record: the fixed facts every run of this fire must agree with. Times are UTC.\nDo not edit by hand; replace it with wrf-new-fire --replace, which keeps the old one.")
    print(open(a.out).read())
