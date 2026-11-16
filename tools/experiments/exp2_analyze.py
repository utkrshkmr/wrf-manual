"""Measure geogrid's positioning error from coded-layer runs.
usage: exp2_analyze.py RUNS_CSV TRUTH_TXT OUT_CSV SUMMARY_TXT
RUNS_CSV columns: run,variant,proj,site_lat,site_lon,anchor_lat,anchor_lon,gx0,gy0,gd,npz
  proj = albers: gx0 gy0 = EPSG:5070 x y of pixel (1,1) centre, gd = 30
  proj = ll:     gx0 gy0 = lon lat of pixel (1,1) centre, gd = degrees
TRUTH_TXT: 'x y' in EPSG:5070 for every cell of every albers run, in RUNS_CSV order."""
import sys, math
import numpy as np
runs, truth, out, summ = sys.argv[1:5]
rows = [l.rstrip("\n").split(",") for l in open(runs) if l.strip() and not l.startswith("run,")]
xy = np.loadtxt(truth, usecols=(0, 1)) if any(r[2] == "albers" for r in rows) else np.zeros((0, 2))
k, res = 0, []
for run, var, proj, slat, slon, alat, alon, gx0, gy0, gd, npz in rows:
    z = np.load(npz)
    lat, lon = z["lat"].ravel(), z["lon"].ravel()
    pc, pr = z["col"].ravel().astype(float), z["row"].ravel().astype(float)
    gx0, gy0, gd = float(gx0), float(gy0), float(gd)
    if proj == "albers":
        tx, ty = xy[k:k + lat.size, 0], xy[k:k + lat.size, 1]; k += lat.size
        tc, tr = 1 + (tx - gx0) / gd, 1 + (ty - gy0) / gd
        mx, my = gd, gd
    else:
        tc, tr = 1 + (lon - gx0) / gd, 1 + (lat - gy0) / gd
        my = gd * 111195.0; mx = my * math.cos(math.radians(float(slat)))
    ok = (pc > 0) & (pr > 0)
    if ok.sum() == 0:
        res.append([run, var, proj, slat, slon, "", "", "", "", "", "", "", str(lat.size)]); continue
    ex, ey = (pc[ok] - tc[ok]) * mx, (pr[ok] - tr[ok]) * my
    wrong = 100 * np.mean((pc[ok] != np.round(tc[ok])) | (pr[ok] != np.round(tr[ok])))
    km = ""
    if alat:
        p1, p2 = math.radians(float(slat)), math.radians(float(alat))
        km = f"{6371.0 * math.acos(min(1, math.sin(p1)*math.sin(p2) + math.cos(p1)*math.cos(p2)*math.cos(math.radians(float(slon)-float(alon))))):.0f}"
    res.append([run, var, proj, slat, slon, km, f"{ex.mean():.2f}", f"{ey.mean():.2f}", f"{math.hypot(ex.mean(), ey.mean()):.2f}",
                f"{np.abs(ex).max():.1f}", f"{np.abs(ey).max():.1f}", f"{wrong:.2f}", str(int((~ok).sum()))])
with open(out, "w") as f:
    f.write("run,variant,proj,site_lat,site_lon,km_to_anchor,shift_east_m,shift_north_m,shift_m,max_abs_err_east_m,max_abs_err_north_m,pct_wrong_pixel,missing_cells\n")
    for r in res: f.write(",".join(r) + "\n")
with open(summ, "w") as f:
    f.write(f"{'variant':16s} {'sites':>5s} {'med shift m':>11s} {'p90 shift m':>11s} {'max shift m':>11s} {'mean %wrong':>11s} {'missing':>8s} {'m per 100 km':>12s}\n")
    vs = []
    for r in res:
        if r[1] not in vs: vs.append(r[1])
    for v in vs:
        rs = [r for r in res if r[1] == v and r[8]]
        if not rs: continue
        s = np.array([float(r[8]) for r in rs]); w = np.array([float(r[11]) for r in rs]); miss = sum(int(r[12]) for r in rs)
        kms = np.array([float(r[5]) for r in rs]) if all(r[5] for r in rs) else None
        slope = np.polyfit(kms, s, 1)[0] * 100 if kms is not None and kms.std() > 0 else float("nan")
        f.write(f"{v:16s} {len(rs):5d} {np.median(s):11.2f} {np.percentile(s, 90):11.2f} {s.max():11.2f} {w.mean():11.2f} {miss:8d} {slope:12.2f}\n")
print(open(summ).read())
