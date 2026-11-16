"""Compare NFUEL_CAT of a geo_em with an NCAR met_em; append one CSV row.
usage: exp1_compare.py GEO_EM MET_EM CSV FIRE LAYER ANCHOR FIRE_LAT FIRE_LON ANCHOR_LAT ANCHOR_LON"""
import sys, os, math
import numpy as np
from netCDF4 import Dataset
geo, met, csv, fire, layer, anchor, flat, flon, alat, alon = sys.argv[1:11]
a = Dataset(geo)["NFUEL_CAT"][0].astype(int); b = Dataset(met)["NFUEL_CAT"][0].astype(int)
ga, gb = Dataset(geo), Dataset(met)
grid_ok = float(np.abs(ga["XLAT_M"][0] - gb["XLAT_M"][0]).max()) < 1e-4 and float(np.abs(ga["XLONG_M"][0] - gb["XLONG_M"][0]).max()) < 1e-4
if a.shape != b.shape:
    row = [fire, layer, anchor, "", "", "", "shape", str(a.shape), str(b.shape)]
else:
    d = a != b
    pct = 100 * (1 - d.mean())
    top = ""
    if d.any():
        p, c = np.unique(np.stack([a[d], b[d]]), axis=1, return_counts=True)
        o = np.argsort(c)[::-1][:4]
        top = " ".join(f"{p[0,i]}>{p[1,i]}:{c[i]}" for i in o)
    la, lo = float(alat), float(alon)
    R = 6371.0; p1, p2 = math.radians(float(flat)), math.radians(la); dl = math.radians(float(flon) - lo)
    km = R * math.acos(min(1, math.sin(p1) * math.sin(p2) + math.cos(p1) * math.cos(p2) * math.cos(dl)))
    row = [fire, layer, anchor, f"{pct:.4f}", str(int(d.sum())), str(d.size), "ok" if grid_ok else "GRID_DIFFERS", f"{km:.0f}", top]
new = not os.path.exists(csv)
with open(csv, "a") as f:
    if new: f.write("fire,layer,anchor,pct_identical,cells_differ,cells,grid,km_to_anchor,top_mismatches\n")
    f.write(",".join(row) + "\n")
print(" ".join(row))
