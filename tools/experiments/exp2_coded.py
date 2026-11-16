"""Write 'coded' WPS layers whose values are their own column / row numbers, to measure where geogrid looks.
usage: exp2_coded.py OUT KIND NCOLS NROWS BDR [TILE]
KIND: col or row. uint16 values = 1-based pixel index (columns west->east, rows south->north),
halo cells carry the index they would have (clamped to 0..65535). The index file is written without
a known point; add projection and anchor lines afterwards."""
import sys, os, math
import numpy as np
out, kind, nc, nr, b = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
T = int(sys.argv[6]) if len(sys.argv) > 6 else 1000
os.makedirs(out, exist_ok=True)
NX, NY = math.ceil(nc / T), math.ceil(nr / T)
for j in range(NY):
    for i in range(NX):
        cols = np.arange(i * T + 1 - b, (i + 1) * T + 1 + b)
        rows = np.arange(j * T + 1 - b, (j + 1) * T + 1 + b)
        v = np.broadcast_to(cols[None, :], (rows.size, cols.size)) if kind == "col" else np.broadcast_to(rows[:, None], (rows.size, cols.size))
        np.clip(v, 0, 65535).astype(">u2").tofile(f"{out}/{i*T+1:05d}-{(i+1)*T:05d}.{j*T+1:05d}-{(j+1)*T:05d}")
with open(f"{out}/index.base", "w") as f:
    f.write(f"type = continuous\nwordsize = 2\nsigned = no\nendian = big\nrow_order = bottom_top\n"
            f"tile_x = {T}\ntile_y = {T}\ntile_z = 1\ntile_bdr = {b}\nscale_factor = 1.0\nmissing_value = 0\n"
            f'units = "index"\ndescription = "coded {kind} index"\n')
print(f"{out}: {kind}, {nc} x {nr}, {NX * NY} tiles, halo {b}")
