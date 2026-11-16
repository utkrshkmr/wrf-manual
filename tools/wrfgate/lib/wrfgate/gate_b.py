"""Gate B: an input version against independent reference maps (LANDFIRE fuel, fine elevation).
Every fire-mesh cell centre is located with exact NAD83 Albers maths and looked up in the reference
layer, so the check measures where the fuel really is, independent of how the input was made.
usage: python3 -m wrfgate.gate_b INPUT_DIR --fuel LAYER [--scan DIR] [--dem LAYER] [--record fire.yaml] [--out DIR]"""
import argparse
import glob
import os
import numpy as np
from .common import Gate, read_record
from .metem import scan, fire_domain, fire_mesh_latlon, fire_field
from .geo import WPSLayer

NONBURN = set(range(91, 100))


def compare(fuel, ref):
    ok = np.isfinite(ref)
    a, b = fuel[ok].astype(int), ref[ok].astype(int)
    same = 100 * np.mean(a == b) if a.size else 0.0
    d = a != b
    top = []
    if d.any():
        p, c = np.unique(np.stack([a[d], b[d]]), axis=1, return_counts=True)
        for i in np.argsort(c)[::-1][:6]:
            top.append(f"{p[0, i]}->{p[1, i]} ({c[i]})")
    mirrored = 0
    if d.any():
        pairs = {}
        for x, y in zip(a[d], b[d]):
            pairs[(x, y)] = pairs.get((x, y), 0) + 1
        mirrored = sum(min(n, pairs.get((y, x), 0)) for (x, y), n in pairs.items() if x < y) * 2 / d.sum() * 100
    return same, top, float(np.mean(~ok) * 100), mirrored


def run(input_dir, fuel_layer, scan_dir=None, dem=None, record=None, out=None, pass_pct=98.0, fail_pct=90.0):
    g = Gate("B", input_dir)
    rec = read_record(record) if record else {}
    files = scan(input_dir)
    fd, sr = fire_domain(files)
    if not g.ok("B01_fire_domain", fd is not None, f"fire domain d{fd or 0:02d}, ratio {sr}", "no fire mesh found"):
        return g.write(out or input_dir)
    p0 = files[fd][0][1]
    lat, lon, shape = fire_mesh_latlon(p0, sr)
    fuel = fire_field(p0, "NFUEL_CAT", shape)
    g.facts.update(fire_cells=int(fuel.size), fuel_layer=fuel_layer)
    layer = WPSLayer(fuel_layer)
    ref = layer.sample(lat, lon)
    same, top, nodata, mirrored = compare(fuel, ref)
    g.facts.update(fuel_agreement_pct=round(same, 4), reference_nodata_pct=round(nodata, 3), mirrored_pct=round(mirrored, 1))
    status = "PASS" if same >= pass_pct else ("WARN" if same >= fail_pct else "FAIL")
    g.check("B02_fuel_agreement", status, f"{same:.3f}% of fire cells match {os.path.basename(os.path.dirname(fuel_layer.rstrip('/')))}/"
            f"{os.path.basename(fuel_layer.rstrip('/'))} (pass >= {pass_pct}%, fail < {fail_pct}%)")
    if top:
        g.check("B03_top_mismatches", "INFO", f"input -> reference: {', '.join(top)}")
        g.check("B04_mirrored_share", "INFO", f"{mirrored:.0f}% of mismatches come in mirrored pairs (a->b and b->a): "
                f"high values point to a small positional shift, low values to different data")
    g.ok("B05_reference_cover", nodata < 1, f"reference covers {100 - nodata:.2f}% of fire cells",
         f"reference has no data under {nodata:.1f}% of fire cells", warn_only=True)
    burn_in = np.isin(fuel.astype(int), list(NONBURN), invert=True).mean() * 100
    rv = ref[np.isfinite(ref)].astype(int)
    burn_ref = np.isin(rv, list(NONBURN), invert=True).mean() * 100 if rv.size else 0
    g.ok("B06_burnable_share", abs(burn_in - burn_ref) < 2, f"burnable share {burn_in:.1f}% vs reference {burn_ref:.1f}%",
         f"burnable share {burn_in:.1f}% vs reference {burn_ref:.1f}%", warn_only=True)
    if scan_dir:
        res = []
        lays = [(l, l.split(os.sep)[-2]) for l in sorted(glob.glob(os.path.join(scan_dir, "LF20*", "FBFM40")))]
        lays += [(l, "NCAR " + l.split(os.sep)[-2]) for l in sorted(glob.glob(os.path.join(os.path.dirname(scan_dir.rstrip("/")), "landfire_ncar", "LF20*", "FBFM40")))]
        for lay, label in lays:
            s, _, _, _ = compare(fuel, WPSLayer(lay).sample(lat, lon))
            res.append((s, label))
        res.sort(reverse=True)
        g.facts["release_scan"] = {r: round(s, 3) for s, r in res}
        g.check("B07_release_scan", "INFO", "best matching releases: " + ", ".join(f"{r} {s:.2f}%" for s, r in res))
    if rec.get("ignition_lat"):
        il, io = float(rec["ignition_lat"]), float(rec["ignition_lon"])
        c = layer.sample(np.array([il]), np.array([io]))[0]
        g.ok("B08_ignition_reference", np.isfinite(c) and int(c) not in NONBURN, f"reference fuel at the ignition point is {c:.0f} (burnable)",
             f"reference fuel at the ignition point is {c} (not burnable): check the ignition location")
    if dem:
        zsf = fire_field(p0, "ZSF", shape)
        if zsf is None:
            g.check("B09_terrain", "WARN", "no ZSF in the input to compare with the reference elevation")
        else:
            z = WPSLayer(dem).sample(lat, lon)
            ok = np.isfinite(z)
            diff = zsf[ok] - z[ok]
            rmse, bias = float(np.sqrt(np.mean(diff ** 2))), float(np.mean(diff))
            g.facts.update(terrain_rmse_m=round(rmse, 2), terrain_bias_m=round(bias, 2))
            g.ok("B09_terrain", rmse < 15, f"ZSF vs reference elevation: RMSE {rmse:.1f} m, bias {bias:+.1f} m",
                 f"ZSF vs reference elevation: RMSE {rmse:.1f} m, bias {bias:+.1f} m", warn_only=True)
    return g.write(out or input_dir)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("input_dir"); ap.add_argument("--fuel", required=True); ap.add_argument("--scan")
    ap.add_argument("--dem"); ap.add_argument("--record"); ap.add_argument("--out")
    ap.add_argument("--pass-pct", type=float, default=98.0); ap.add_argument("--fail-pct", type=float, default=90.0)
    a = ap.parse_args()
    raise SystemExit({"PASS": 0, "WARN": 0, "FAIL": 1}[run(a.input_dir, a.fuel, a.scan, a.dem, a.record, a.out, a.pass_pct, a.fail_pct)])
