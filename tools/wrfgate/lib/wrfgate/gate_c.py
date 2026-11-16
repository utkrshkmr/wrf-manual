"""Gate C: real.exe output and the namelists, before any wrf.exe time is spent.
usage: python3 -m wrfgate.gate_c RUN_DIR --inputs INPUT_DIR --record fire.yaml"""
import argparse
import glob
import os
import re
import numpy as np
from netCDF4 import Dataset
from .common import Gate, read_record, parse_time, get_namelist
from .metem import scan, attrs, fire_domain


def times(path):
    with Dataset(path) as d:
        return [b"".join(t).decode() for t in d["Times"][:]]


def col(nl, name, i, default=None):
    v = get_namelist(nl, name)
    if v is None:
        return default
    return v[i] if i < len(v) else v[-1]


def run(run_dir, input_dir, record, out=None):
    g = Gate("C", run_dir)
    rec = read_record(record)
    nl = open(os.path.join(run_dir, "namelist.input")).read()
    rsl = os.path.join(run_dir, "rsl.error.0000")
    log = open(rsl, errors="replace").read() if os.path.exists(rsl) else ""
    if not g.ok("C01_real_success", "SUCCESS COMPLETE REAL_EM INIT" in log, "real.exe finished: SUCCESS COMPLETE REAL_EM INIT",
                "real.exe did not report success; see rsl.error.0000"):
        return g.write(out or run_dir)
    warn = len(re.findall(r"warning", log, re.I))
    g.check("C02_real_warnings", "INFO", f"{warn} warning lines in rsl.error.0000")
    files = scan(input_dir)
    nd = len(files)
    max_dom = int(col(nl, "max_dom", 0, "1"))
    g.ok("C03_max_dom", max_dom == nd, f"max_dom = {max_dom}, as in the inputs", f"max_dom = {max_dom} but the inputs have {nd} domains")
    missing = [f"wrfinput_d{d:02d}" for d in range(1, max_dom + 1) if not os.path.exists(os.path.join(run_dir, f"wrfinput_d{d:02d}"))]
    g.ok("C04_outputs", not missing and os.path.exists(os.path.join(run_dir, "wrfbdy_d01")), "wrfinput for every domain and wrfbdy_d01 written",
         f"missing: {missing or ['wrfbdy_d01']}")
    if missing:
        return g.write(out or run_dir)
    # geometry against the inputs
    bad = []
    for d in range(1, nd + 1):
        a = attrs(files[d][0][1])
        for nm, key in [("e_we", "WEST-EAST_GRID_DIMENSION"), ("e_sn", "SOUTH-NORTH_GRID_DIMENSION"), ("sr_x", "sr_x"), ("sr_y", "sr_y")]:
            v = col(nl, nm, d - 1)
            if v is not None and int(float(v)) != int(a.get(key, 0)) and not (nm.startswith("sr") and int(a.get(key, 1)) <= 1 and int(float(v)) <= 1):
                bad.append(f"d{d:02d} {nm}={v} vs inputs {a.get(key)}")
        v = col(nl, "dx", d - 1)
        if v is not None and abs(float(v) - float(a["DX"])) > 0.01:
            bad.append(f"d{d:02d} dx={v} vs inputs {a['DX']}")
    a1 = attrs(files[1][0][1])
    nml = col(nl, "num_metgrid_levels", 0)
    if nml and int(nml) != int(a1.get("NUM_METGRID_LEVELS", -1)):
        bad.append(f"num_metgrid_levels={nml} vs inputs {a1.get('NUM_METGRID_LEVELS')}")
    g.ok("C05_geometry_matches", not bad, "domains, dx, fire ratio and level count match the inputs", f"mismatches: {bad}")
    # time window
    start, end = parse_time(rec["start"]), parse_time(rec["end"])
    t0 = parse_time(times(os.path.join(run_dir, "wrfinput_d01"))[0])
    g.ok("C06_start_time", t0 == start, f"initial time {t0} is the recorded start", f"initial time {t0} but the record starts at {start}")
    bt = times(os.path.join(run_dir, "wrfbdy_d01"))
    interval = int(col(nl, "interval_seconds", 0, "3600"))
    import datetime as _dt
    bend = parse_time(bt[-1]) + _dt.timedelta(seconds=interval)
    g.ok("C07_boundaries", bend >= end, f"boundaries cover to {bend} (record ends {end})", f"boundaries end at {bend}, before the recorded end {end}")
    # fire settings on the fire domain
    fd, sr = fire_domain(files)
    i = fd - 1
    g.facts.update(fire_domain=fd)
    g.ok("C08_ifire", col(nl, "ifire", i, "0") == "2", f"ifire = 2 on d{fd:02d}", f"ifire is {col(nl, 'ifire', i, '0')} on the fire domain d{fd:02d}")
    g.ok("C09_fuel_read", col(nl, "fire_fuel_read", i, "-1") == "-1", "fire_fuel_read = -1: fuel map from the inputs",
         f"fire_fuel_read = {col(nl, 'fire_fuel_read', i)}: the input fuel map is ignored", warn_only=True)
    zflag = int(attrs(files[fd][0][1]).get("FLAG_ZSF", 0))
    topo = col(nl, "fire_topo_from_atm", i, "1")
    g.ok("C10_fire_terrain", not (zflag == 1 and topo == "1"), f"fire_topo_from_atm = {topo} with ZSF {'present' if zflag else 'absent'}",
         "ZSF is in the inputs but fire_topo_from_atm = 1 overwrites it with smoothed atmosphere terrain", warn_only=True)
    # ignition
    ign = parse_time(rec["ignition_time"])
    want = (ign - start).total_seconds()
    have = col(nl, "fire_ignition_start_time1", i)
    g.ok("C11_ignition_time", have is not None and abs(float(have) - want) <= 1,
         f"fire_ignition_start_time1 = {have} s = {ign} UTC", f"fire_ignition_start_time1 = {have} s but the record's ignition at {ign} is {want:.0f} s after the start")
    lat_n, lon_n = col(nl, "fire_ignition_start_lat1", i), col(nl, "fire_ignition_start_lon1", i)
    if rec.get("ignition_lat"):
        okp = lat_n is not None and abs(float(lat_n) - float(rec["ignition_lat"])) < 1e-4 and abs(float(lon_n) - float(rec["ignition_lon"])) < 1e-4
        g.ok("C12_ignition_place", okp, f"ignition at {lat_n}, {lon_n}, as recorded",
             f"namelist ignition {lat_n}, {lon_n} differs from the record {rec['ignition_lat']}, {rec['ignition_lon']}")
    # fuel and moisture in wrfinput
    with Dataset(os.path.join(run_dir, f"wrfinput_d{fd:02d}")) as d:
        f = np.asarray(d["NFUEL_CAT"][0])
        fm = np.asarray(d["FMC_G"][0]) if "FMC_G" in d.variables else None
    nfile = os.path.join(run_dir, "namelist.fire")
    nfc = None
    if os.path.exists(nfile):
        v = get_namelist(open(nfile).read(), "nfuelcats")
        nfc = int(v[0]) if v else None
    if (f == 204).any():
        g.ok("C13_code_204", nfc is not None and nfc >= 54, f"code 204 present and namelist.fire sets nfuelcats = {nfc}",
             "code 204 (SB4) is in the fuel map but namelist.fire does not set nfuelcats = 54: wrf.exe will stop with 'fuel category out of bounds'")
    else:
        g.check("C13_code_204", "PASS", "no code 204 in the fuel map")
    fmc_read = col(nl, "fire_fmc_read", i, "1")
    if fmc_read == "0":
        frac = float((fm[: f.shape[0], : f.shape[1]] > 0).mean()) * 100 if fm is not None else 0
        g.ok("C14_fuel_moisture", frac > 99, f"fire_fmc_read = 0 and FMC_G is set in {frac:.1f}% of cells ({np.nanmin(fm):.3f} to {np.nanmax(fm):.3f})",
             f"fire_fmc_read = 0 but FMC_G is zero in {100 - frac:.1f}% of cells: those cells would burn as bone-dry fuel")
    else:
        g.check("C14_fuel_moisture", "INFO", f"fire_fmc_read = {fmc_read}: one moisture value from namelist.fire")
    cap = min(((int(attrs(files[d][0][1])["WEST-EAST_GRID_DIMENSION"]) - 1) // 10) * ((int(attrs(files[d][0][1])["SOUTH-NORTH_GRID_DIMENSION"]) - 1) // 10) for d in files)
    g.facts["rank_cap"] = cap
    g.check("C15_rank_cap", "INFO", f"wrf.exe can use at most {cap} MPI ranks")
    return g.write(out or run_dir)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir"); ap.add_argument("--inputs", required=True); ap.add_argument("--record", required=True); ap.add_argument("--out")
    a = ap.parse_args()
    raise SystemExit({"PASS": 0, "WARN": 0, "FAIL": 1}[run(a.run_dir, a.inputs, a.record, a.out)])
