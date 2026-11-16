"""Reading a folder of met_em files: domains, times, the fire domain and its fire-mesh coordinates."""
import datetime as _dt
import glob
import os
import re
import numpy as np
from netCDF4 import Dataset


def scan(folder):
    """{domain: [(time, path), ...]} sorted by time."""
    out = {}
    for p in glob.glob(os.path.join(folder, "met_em.d0*")):
        m = re.search(r"met_em\.d(\d\d)\.(\d{4}-\d\d-\d\d_\d\d:\d\d:\d\d)\.nc$", os.path.basename(p))
        if m:
            out.setdefault(int(m.group(1)), []).append((_dt.datetime.strptime(m.group(2), "%Y-%m-%d_%H:%M:%S"), p))
    return {d: sorted(v) for d, v in sorted(out.items())}


def attrs(path):
    with Dataset(path) as d:
        return {k: d.getncattr(k) for k in d.ncattrs()}


def fire_domain(files):
    """Domain number with the largest sr_x, and that ratio."""
    best = (None, 1)
    for d, lst in files.items():
        sr = int(attrs(lst[0][1]).get("sr_x", 1))
        if sr > best[1]:
            best = (d, sr)
    return best


def fire_mesh_latlon(path, sr):
    """Latitude and longitude of every fire-mesh cell centre inside the domain, from XLAT_M/XLONG_M.
    Returns (lat, lon, (ny_fire, nx_fire)); cells beyond the last atmosphere cell are left out."""
    with Dataset(path) as d:
        la, lo = np.asarray(d["XLAT_M"][0], float), np.asarray(d["XLONG_M"][0], float)
    ny, nx = la.shape
    fy = (np.arange(ny * sr) + 0.5) / sr - 0.5
    fx = (np.arange(nx * sr) + 0.5) / sr - 0.5

    def interp(a, fy, fx):
        y0 = np.clip(np.floor(fy).astype(int), 0, ny - 2); x0 = np.clip(np.floor(fx).astype(int), 0, nx - 2)
        wy = (fy - y0)[:, None]; wx = (fx - x0)[None, :]
        a00 = a[np.ix_(y0, x0)]; a01 = a[np.ix_(y0, x0 + 1)]; a10 = a[np.ix_(y0 + 1, x0)]; a11 = a[np.ix_(y0 + 1, x0 + 1)]
        return a00 * (1 - wy) * (1 - wx) + a01 * (1 - wy) * wx + a10 * wy * (1 - wx) + a11 * wy * wx

    return interp(la, fy, fx), interp(lo, fy, fx), (ny * sr, nx * sr)


def fire_field(path, name, shape):
    with Dataset(path) as d:
        if name not in d.variables:
            return None
        a = np.asarray(d[name][0], float)
    return a[: shape[0], : shape[1]]
