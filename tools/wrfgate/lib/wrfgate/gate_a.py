"""Gate A: structure of an input version (a folder of met_em files), before anything is run.
usage: python3 -m wrfgate.gate_a INPUT_DIR [--record fire.yaml] [--out DIR]"""
import argparse
import datetime as _dt
import os
import numpy as np
from netCDF4 import Dataset
from .common import Gate, read_record, parse_time
from .metem import scan, attrs, fire_domain, fire_mesh_latlon, fire_field
from .geo import haversine_km

REQUIRED = ["TT", "UU", "VV", "GHT", "PRES", "PSFC", "PMSL", "SKINTEMP", "HGT_M", "LANDUSEF", "LU_INDEX",
            "XLAT_M", "XLONG_M", "LANDMASK", "SOILHGT"]
VALID_FUEL = set(range(1, 14)) | set(range(91, 100)) | set(range(101, 110)) | set(range(121, 125)) | \
    set(range(141, 150)) | set(range(161, 166)) | set(range(181, 190)) | set(range(201, 205))
NONBURN = set(range(91, 100))


def run(input_dir, record=None, out=None):
    g = Gate("A", input_dir)
    rec = read_record(record) if record else {}
    files = scan(input_dir)
    if not g.ok("A01_files", bool(files), f"{sum(len(v) for v in files.values())} met_em files, domains {list(files)}",
                "no met_em files found"):
        return g.write(out or input_dir)
    doms = list(files)
    g.ok("A02_domains", doms == list(range(1, len(doms) + 1)), f"domains d01..d{len(doms):02d}",
         f"domain numbers are not contiguous: {doms}")
    t1 = [t for t, _ in files[1]]
    steps = sorted({(b - a).total_seconds() for a, b in zip(t1, t1[1:])})
    g.facts.update(start=str(t1[0]), end=str(t1[-1]), times=len(t1), interval_s=steps)
    g.ok("A03_interval", len(steps) <= 1, f"{len(t1)} times every {int(steps[0]) if steps else 0} s",
         f"uneven or missing times: intervals {steps} s")
    same = all([t for t, _ in files[d]] == t1 for d in doms)
    g.ok("A04_times_all_domains", same, "every domain has the same times", "domains have different time lists")
    if rec.get("start") and rec.get("end"):
        s, e = parse_time(rec["start"]), parse_time(rec["end"])
        g.ok("A05_window", t1[0] <= s and t1[-1] >= e, f"covers the recorded window {s} to {e}",
             f"files run {t1[0]} to {t1[-1]} but the record asks for {s} to {e}")
    # geometry consistency and required fields
    geo_keys = ["DX", "DY", "WEST-EAST_GRID_DIMENSION", "SOUTH-NORTH_GRID_DIMENSION", "CEN_LAT", "CEN_LON",
                "MAP_PROJ", "TRUELAT1", "TRUELAT2", "STAND_LON", "sr_x", "sr_y", "parent_grid_ratio",
                "i_parent_start", "j_parent_start", "NUM_METGRID_LEVELS"]
    bad_geo, missing, bad_vals = [], {}, []
    for d in doms:
        ref = attrs(files[d][0][1])
        for t, p in files[d]:
            a = attrs(p)
            diff = [k for k in geo_keys if k in ref and str(a.get(k)) != str(ref.get(k))]
            if diff:
                bad_geo.append(f"d{d:02d} {t}: {diff}")
            with Dataset(p) as nc:
                miss = [v for v in REQUIRED if v not in nc.variables and not (v == "RH" and "SPECHUMD" in nc.variables)]
                if "RH" not in nc.variables and "SPECHUMD" not in nc.variables:
                    miss.append("RH/SPECHUMD")
                if miss:
                    missing[f"d{d:02d}"] = sorted(set(missing.get(f"d{d:02d}", [])) | set(miss))
                for v in nc.variables:
                    x = nc[v]
                    if x.dtype.kind == "f" and x.ndim >= 2:
                        arr = np.asarray(x[:])
                        if not np.isfinite(arr).all():
                            bad_vals.append(f"{os.path.basename(p)}:{v}")
    g.ok("A06_geometry_constant", not bad_geo, "domain geometry identical in every file", f"geometry changes: {bad_geo[:5]}")
    g.ok("A07_required_fields", not missing, f"{len(REQUIRED)} required fields present in every file",
         f"missing fields: {missing}")
    g.ok("A08_finite", not bad_vals, "no NaN or Inf in any field of any file", f"non-finite values in {bad_vals[:8]}")
    # nesting rule and decomposition cap
    caps, nest_bad = [], []
    for d in doms:
        a = attrs(files[d][0][1])
        nx, ny = int(a["WEST-EAST_GRID_DIMENSION"]) - 1, int(a["SOUTH-NORTH_GRID_DIMENSION"]) - 1
        caps.append((nx // 10) * (ny // 10))
        if d > 1 and (nx % int(a["parent_grid_ratio"]) or ny % int(a["parent_grid_ratio"])):
            nest_bad.append(f"d{d:02d}")
    g.facts["rank_cap"] = min(caps)
    g.ok("A09_nest_rule", not nest_bad, "every nest's (e_we-1, e_sn-1) divides by its parent ratio",
         f"nest size not a multiple of the ratio: {nest_bad}")
    g.check("A10_rank_cap", "INFO", f"WRF allows at most {min(caps)} MPI ranks (10 points per rank on the tightest domain)")
    # fire fields
    fd, sr = fire_domain(files)
    if not g.ok("A11_fire_domain", fd is not None, f"fire domain d{fd or 0:02d}, fire mesh ratio {sr}",
                "no domain has sr_x > 1: there is no fire mesh"):
        return g.write(out or input_dir)
    g.facts.update(fire_domain=fd, sr=sr)
    p0 = files[fd][0][1]
    a0 = attrs(p0)
    g.ok("A12_fuel_flag", int(a0.get("FLAG_NFUEL_CAT", 0)) == 1, "NFUEL_CAT filled (FLAG_NFUEL_CAT = 1)",
         "FLAG_NFUEL_CAT is not 1: no fuel map")
    g.ok("A13_terrain_flag", int(a0.get("FLAG_ZSF", 0)) == 1, "fine fire terrain ZSF filled (FLAG_ZSF = 1)",
         "no ZSF: the fire would see flat ground (WRF 4.6 does not fill fire terrain from the atmosphere); add the terrain layer in geogrid")
    lat, lon, shape = fire_mesh_latlon(p0, sr)
    fuel = fire_field(p0, "NFUEL_CAT", shape)
    codes, counts = np.unique(fuel.astype(int), return_counts=True)
    g.facts["fuel_codes"] = {int(c): int(n) for c, n in zip(codes, counts)}
    invalid = {int(c): int(n) for c, n in zip(codes, counts) if int(c) not in VALID_FUEL}
    g.ok("A14_fuel_codes", not invalid, f"{len(codes)} fuel codes, all valid Anderson or Scott-Burgan codes",
         f"invalid fuel codes (count): {invalid} (0 = no data; >204 is outside WRF's table)")
    burn = 100 * np.isin(fuel.astype(int), list(VALID_FUEL - NONBURN)).mean()
    g.facts["burnable_pct"] = round(float(burn), 2)
    g.ok("A15_burnable", burn > 5, f"{burn:.1f}% of fire cells burnable", f"only {burn:.1f}% of fire cells burnable", warn_only=True)
    if 204 in g.facts["fuel_codes"]:
        g.check("A16_code_204", "WARN", f"code 204 (SB4) in {g.facts['fuel_codes'][204]} cells: namelist.fire must set nfuelcats = 54 (gate C checks it)")
    zsf = fire_field(p0, "ZSF", shape)
    if zsf is not None and int(a0.get("FLAG_ZSF", 0)) == 1:
        with Dataset(p0) as nc:
            hgt = np.asarray(nc["HGT_M"][0], float)
        z_ok = np.isfinite(zsf).all() and zsf.min() > -100 and zsf.max() < 4500
        g.ok("A17_terrain_range", z_ok, f"ZSF {zsf.min():.0f} to {zsf.max():.0f} m (atmosphere terrain {hgt.min():.0f} to {hgt.max():.0f} m)",
             f"ZSF out of range: {np.nanmin(zsf):.0f} to {np.nanmax(zsf):.0f} m")
        zm = zsf.reshape(hgt.shape[0], sr, hgt.shape[1], sr).mean(axis=(1, 3))
        mad = float(np.abs(zm - hgt).mean())
        g.facts["zsf_vs_hgt_mean_abs_m"] = round(mad, 1)
        g.ok("A18_terrain_vs_atm", mad < 50, f"fire terrain agrees with atmosphere terrain (mean |diff| {mad:.1f} m per cell)",
             f"fire terrain differs from atmosphere terrain by {mad:.1f} m on average: misplaced or wrong terrain layer", warn_only=True)
    # ignition from the record
    if rec.get("ignition_lat") and rec.get("ignition_lon"):
        il, io = float(rec["ignition_lat"]), float(rec["ignition_lon"])
        d2 = (lat - il) ** 2 + ((lon - io) * np.cos(np.radians(il))) ** 2
        j, i = np.unravel_index(np.argmin(d2), d2.shape)
        inside = 0 < j < shape[0] - 1 and 0 < i < shape[1] - 1 and np.sqrt(d2[j, i]) * 111.2 < 0.1
        edge_km = min(haversine_km(il, io, lat[0, i], lon[0, i]), haversine_km(il, io, lat[-1, i], lon[-1, i]),
                      haversine_km(il, io, lat[j, 0], lon[j, 0]), haversine_km(il, io, lat[j, -1], lon[j, -1]))
        g.facts.update(ignition_cell=[int(j), int(i)], ignition_edge_km=round(float(edge_km), 2))
        if g.ok("A19_ignition_inside", inside, f"ignition inside the fire domain, {edge_km:.1f} km from the nearest edge",
                "ignition point is outside the fire domain"):
            need = float(rec.get("min_edge_km", 2))
            g.ok("A20_ignition_margin", edge_km >= need, f"at least {need} km of room to every edge",
                 f"only {edge_km:.1f} km to the nearest edge (record asks for {need} km)", warn_only=True)
            code = int(fuel[j, i])
            g.ok("A21_ignition_fuel", code not in NONBURN and code in VALID_FUEL, f"ignition cell fuel code {code} is burnable",
                 f"ignition cell fuel code {code} is not burnable")
    return g.write(out or input_dir)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("input_dir"); ap.add_argument("--record"); ap.add_argument("--out")
    a = ap.parse_args()
    raise SystemExit({"PASS": 0, "WARN": 0, "FAIL": 1}[run(a.input_dir, a.record, a.out)])
