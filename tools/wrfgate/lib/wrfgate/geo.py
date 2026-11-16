"""Exact geometry for the gates: NAD83 Albers (EPSG:5070 form) and a reader for WPS geogrid layers.

albers_forward follows Snyder (1987), Map Projections - A Working Manual, eqs 14-3 to 14-12, on the
GRS80 ellipsoid. It is checked against PROJ in tests. The reader looks up the pixel that contains a point
using the layer's own index file, in exact projected coordinates (no WPS code involved)."""
import math
import os
import numpy as np

A = 6378137.0
F = 1 / 298.257222101
E2 = F * (2 - F)
E = math.sqrt(E2)


def _q(phi):
    s = np.sin(phi)
    return (1 - E2) * (s / (1 - E2 * s * s) - (1 / (2 * E)) * np.log((1 - E * s) / (1 + E * s)))


def _m(phi):
    s = np.sin(phi)
    return np.cos(phi) / np.sqrt(1 - E2 * s * s)


def albers_forward(lat, lon, lat1=29.5, lat2=45.5, lat0=23.0, lon0=-96.0):
    """lat/lon (degrees, NAD83) -> x, y in metres. Defaults are LANDFIRE/USGS CONUS Albers (EPSG:5070)."""
    p1, p2, p0 = map(math.radians, (lat1, lat2, lat0))
    m1, m2 = _m(p1), _m(p2)
    q1, q2, q0 = _q(p1), _q(p2), _q(p0)
    n = (m1 * m1 - m2 * m2) / (q2 - q1)
    C = m1 * m1 + n * q1
    rho0 = A * math.sqrt(C - n * q0) / n
    phi = np.radians(np.asarray(lat, float))
    lam = np.radians(np.asarray(lon, float) - lon0)
    rho = A * np.sqrt(C - n * _q(phi)) / n
    th = n * lam
    return rho * np.sin(th), rho0 - rho * np.cos(th)


class WPSLayer:
    """Nearest-pixel sampler for a WPS geogrid layer (albers_nad83 or regular_ll), values as stored x scale."""

    def __init__(self, folder):
        self.dir = folder
        m = {}
        for line in open(os.path.join(folder, "index")):
            if "=" in line:
                k, v = line.split("=", 1)
                m[k.strip().lower()] = v.split("#")[0].strip().strip('"')
        self.m = m
        self.proj = m["projection"]
        self.tx, self.ty = int(m["tile_x"]), int(m["tile_y"])
        self.bdr = int(m.get("tile_bdr", 0))
        ws = int(m["wordsize"])
        signed = m.get("signed", "no").lower() == "yes"
        end = "<" if m.get("endian", "big").lower() == "little" else ">"
        self.dtype = np.dtype(end + {1: "i1", 2: "i2", 4: "i4"}[ws] if signed else end + {1: "u1", 2: "u2", 4: "u4"}[ws])
        self.scale = float(m.get("scale_factor", 1.0))
        self.missing = float(m["missing_value"]) if "missing_value" in m else None
        self.kx, self.ky = float(m["known_x"]), float(m["known_y"])
        self.dx, self.dy = float(m["dx"]), float(m["dy"])
        self.klat, self.klon = float(m["known_lat"]), float(m["known_lon"])
        if self.proj == "albers_nad83":
            self.p = dict(lat1=float(m["truelat1"]), lat2=float(m["truelat2"]), lon0=float(m["stdlon"]))
            self.kxm, self.kym = albers_forward(self.klat, self.klon, **self.p)
        elif self.proj != "regular_ll":
            raise ValueError(f"projection {self.proj} not supported by the gate reader")
        self.cache = {}

    def pixel(self, lat, lon):
        """1-based (column, row) of the pixel containing each point; rows count from the south."""
        if self.proj == "albers_nad83":
            x, y = albers_forward(lat, lon, **self.p)
            c = self.kx + (x - self.kxm) / self.dx
            r = self.ky + (y - self.kym) / self.dy
        else:
            c = self.kx + (np.asarray(lon) - self.klon) / self.dx
            r = self.ky + (np.asarray(lat) - self.klat) / self.dy
        return np.floor(c + 0.5).astype(np.int64), np.floor(r + 0.5).astype(np.int64)

    def _tile(self, i0, j0):
        key = (i0, j0)
        if key not in self.cache:
            name = f"{i0:05d}-{i0 + self.tx - 1:05d}.{j0:05d}-{j0 + self.ty - 1:05d}"
            p = os.path.join(self.dir, name)
            if os.path.exists(p):
                b = self.bdr
                a = np.fromfile(p, dtype=self.dtype).reshape(self.ty + 2 * b, self.tx + 2 * b)
                self.cache[key] = a[b:b + self.ty, b:b + self.tx]
            else:
                self.cache[key] = None
        return self.cache[key]

    def sample(self, lat, lon):
        """Values at the points (NaN where no tile or missing value)."""
        lat, lon = np.asarray(lat, float), np.asarray(lon, float)
        c, r = self.pixel(lat.ravel(), lon.ravel())
        out = np.full(c.shape, np.nan)
        i0 = (c - 1) // self.tx * self.tx + 1
        j0 = (r - 1) // self.ty * self.ty + 1
        for key in set(zip(i0.tolist(), j0.tolist())):
            sel = (i0 == key[0]) & (j0 == key[1])
            t = self._tile(*key) if key[0] > 0 and key[1] > 0 else None
            if t is None:
                continue
            v = t[r[sel] - key[1], c[sel] - key[0]].astype(float) * self.scale
            out[sel] = v
        if self.missing is not None:
            out[out == self.missing * self.scale] = np.nan
        return out.reshape(lat.shape)


def haversine_km(lat1, lon1, lat2, lon2):
    p1, p2 = np.radians(lat1), np.radians(lat2)
    d = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(np.radians(np.asarray(lon2) - lon1) / 2) ** 2
    return 2 * 6371.0 * np.arcsin(np.sqrt(d))
