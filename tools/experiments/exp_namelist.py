"""Write a geogrid namelist.wps that rebuilds the domains of an NCAR met_em folder.
usage: exp_namelist.py MET_EM_DIR OUT_NAMELIST TBL_DIR GEOG_PATH
Prints: fire domain number, its centre lat lon."""
import sys, glob, os, re
from netCDF4 import Dataset
src, out, tbl, geog = sys.argv[1:5]
doms = sorted({re.search(r"met_em\.d(\d\d)", f).group(1) for f in glob.glob(f"{src}/met_em.d0*")})
D = {d: Dataset(sorted(glob.glob(f"{src}/met_em.d{d}.*"))[0]) for d in doms}
at = lambda d, k: D[d].getncattr(k)
L = lambda k: ", ".join(str(int(at(d, k))) for d in doms)
t0 = os.path.basename(sorted(glob.glob(f"{src}/met_em.d01.*"))[0]).split(".")[2]
proj = {1: "lambert", 2: "polar", 3: "mercator", 6: "lat-lon"}[int(at("01", "MAP_PROJ"))]
res = ", ".join("'lf2024+default'" if d == "01" else "'ca_1s+lf2024+default'" for d in doms)
srs = [int(at(d, "sr_x")) for d in doms]
fire = doms[srs.index(max(srs))]
open(out, "w").write(f"""&share
 wrf_core='ARW', max_dom={len(doms)},
 start_date={", ".join(f"'{t0}'" for _ in doms)}, end_date={", ".join(f"'{t0}'" for _ in doms)},
 interval_seconds=3600, io_form_geogrid=2,
 subgrid_ratio_x={L('sr_x')}, subgrid_ratio_y={L('sr_y')},
/
&geogrid
 parent_id={L('parent_id')}, parent_grid_ratio={L('parent_grid_ratio')},
 i_parent_start={L('i_parent_start')}, j_parent_start={L('j_parent_start')},
 e_we={L('WEST-EAST_GRID_DIMENSION')}, e_sn={L('SOUTH-NORTH_GRID_DIMENSION')},
 geog_data_res={res},
 dx={at('01','DX')}, dy={at('01','DY')}, map_proj='{proj}',
 ref_lat={at('01','CEN_LAT')}, ref_lon={at('01','CEN_LON')},
 truelat1={at('01','TRUELAT1')}, truelat2={at('01','TRUELAT2')}, stand_lon={at('01','STAND_LON')},
 geog_data_path='{geog}',
 opt_geogrid_tbl_path='{tbl}'
/
""")
print(fire, at(fire, "CEN_LAT"), at(fire, "CEN_LON"), max(srs))
