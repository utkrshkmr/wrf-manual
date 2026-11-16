#!/bin/bash
#SBATCH -p general-compute
#SBATCH --qos=general-compute
#SBATCH -N 1
#SBATCH -n 8
#SBATCH --mem=64G
#SBATCH -t 12:00:00
#SBATCH -o /projects/academic/negarkhodoe/wrf/tests/anchor_study/job_%j.out
# Fuel-map anchor study. Experiment 1: every NCAR fire x every fuel layer x anchor -> NFUEL_CAT match.
# Experiment 2: coded layers -> geogrid's positioning error in metres across California, per anchor.
# Writes everything to $W; the file to read first is $W/REPORT.txt. Nothing outside $W is modified.
set -u
X=${EXPDIR:-/projects/academic/negarkhodoe/utkarshk/pipeline/experiments}
[[ -f $X/exp_namelist.py ]] || { echo "helpers not found in $X"; exit 1; }
W=/projects/academic/negarkhodoe/wrf/tests/anchor_study
S=/projects/academic/negarkhodoe/wrf/static/landfire
NG=/projects/academic/negarkhodoe/Nisha/WPS_files/WPS_GEOG
NT=/projects/academic/negarkhodoe/Nisha/WPS_files/CANYON_2025/WPS-4.6.0/geogrid/GEOGRID.TBL
X0=-2314140; Y0=1195410; DX=30; NC=21329; NR=42586
NWX=-1608; NWY=42942; NWLAT=42.0618221; NWLON=-125.1993245
mkdir -p $W/exp1/layers $W/exp1/runs $W/exp2/layers $W/exp2/runs
cd $W
gdal_env() { module purge >/dev/null 2>&1; module load gcc/11.2.0 openmpi/4.1.1 gdal/3.3.2; }
wps_env()  { module purge >/dev/null 2>&1; module load gcc/11.2.0 openmpi/4.1.1 wps/4.6.0-dmpar; }
to_ll()  { gdaltransform -s_srs EPSG:5070 -t_srs EPSG:4269 | awk '{printf "%.8f %.8f\n", $2, $1}'; }
to_xy()  { gdaltransform -s_srs EPSG:4269 -t_srs EPSG:5070 | awk '{printf "%.3f %.3f\n", $1, $2}'; }
log() { echo "[$(date +%T)] $*"; }

# ---------------------------------------------------------------- Experiment 1
log "exp1: layers"
gdal_env
for R in LF2016 LF2022 LF2023 LF2024 LF2025; do
  src=$S/$R/FBFM40; [[ -f $src/index ]] || { log "missing $src"; continue; }
  base=$src/index; [[ -f $src/index.anchor_sw ]] && base=$src/index.anchor_sw
  for A in SW NW; do
    d=$W/exp1/layers/${R}_$A; mkdir -p $d; ln -sf $src/[0-9]* $d/ 2>/dev/null
    if [[ $A == SW ]]; then cp $base $d/index
    else sed -e "s/^known_x *=.*/known_x = $NWX.0/" -e "s/^known_y *=.*/known_y = $NWY.0/" -e "s/^known_lat *=.*/known_lat = $NWLAT/" -e "s/^known_lon *=.*/known_lon = $NWLON/" $base > $d/index; fi
  done
done
SWLAT=$(grep -E '^ *known_lat' $W/exp1/layers/LF2024_SW/index | sed 's/.*= *//'); SWLON=$(grep -E '^ *known_lon' $W/exp1/layers/LF2024_SW/index | sed 's/.*= *//')
for n in LF_2016 LF_2023 LF_2024; do [[ -d $NG/$n/fbfm40 ]] && ln -sfn $NG/$n/fbfm40 $W/exp1/layers/NCAR_${n/_/}; done
log "exp1: fires"
wps_env
> $W/exp1/fires.txt
for m in /projects/academic/negarkhodoe/Nisha/WPS_files/CANYON_2025/WPS-4.6.0 \
         /projects/academic/negarkhodoe/Thursday_deadline_fires/{CANYON,CRANSTON,CRANSTON/met_files,CRANSTON/met_files1,LONG} \
         /projects/academic/negarkhodoe/WRF_NCAR_Fires/{AIRPORT,BRADFORD_BRANCH,CARMEL}; do
  f=$(ls $m/met_em.d02.* 2>/dev/null | head -1); [[ -n $f ]] || continue
  ncdump -h $f | grep -q 'NFUEL_CAT(' && echo "$(echo $m | sed 's#/projects/academic/negarkhodoe/##; s#/#_#g') $m" >> $W/exp1/fires.txt
done
cat $W/exp1/fires.txt
CSV1=$W/exp1/results.csv; rm -f $CSV1
while read name m; do
  for L in $W/exp1/layers/*; do
    lay=$(basename $L); A=${lay##*_}; [[ $lay == NCAR_* ]] && A=NCAR
    case $A in SW) al="$SWLAT $SWLON";; *) al="$NWLAT $NWLON";; esac
    r=$W/exp1/runs/${name}__$lay; mkdir -p $r; cd $r
    sed -E "s#rel_path *= *lf2024:[^ ]*#abs_path = lf2024:$L/#" $NT > GEOGRID.TBL
    read fd flat flon sr < <(python3 $X/exp_namelist.py $m namelist.wps $r/ $NG/ < /dev/null)
    [[ -n $fd ]] || { log "namelist failed $name $lay"; continue; }
    srun -n 8 geogrid.exe > geogrid.out 2>&1 < /dev/null || { log "geogrid failed $name $lay"; continue; }
    met=$(ls $m/met_em.d$fd.* | head -1)
    python3 $X/exp1_compare.py geo_em.d$fd.nc $met $CSV1 $name $lay $A $flat $flon $al < /dev/null
    rm -f geo_em.d0[1-9].nc.tmp
  done
done < $W/exp1/fires.txt

# ---------------------------------------------------------------- Experiment 2
log "exp2: coded layers"
gdal_env
for B in 3 0; do for K in col row; do
  [[ -f $W/exp2/layers/alb_b${B}_$K/index.base ]] || python3 $X/exp2_coded.py $W/exp2/layers/alb_b${B}_$K $K $NC $NR $B
done; done
LLD=0.000833333333333333; LLNC=12720; LLNR=11640; LLX0=-124.59958333333333; LLY0=32.40041666666667
for K in col row; do
  d=$W/exp2/layers/ll_$K; [[ -f $d/index ]] || { python3 $X/exp2_coded.py $d $K $LLNC $LLNR 3
  { cat $d/index.base; echo "projection = regular_ll"; echo "dx = $LLD"; echo "dy = $LLD"; echo "known_x = 1.0"; echo "known_y = 1.0"; echo "known_lat = $LLY0"; echo "known_lon = $LLX0"; } > $d/index; }
done
read CLAT CLON < <(echo "$((X0 + 10664 * DX)) $((Y0 + 21292 * DX))" | to_ll)
read SWLAT2 SWLON2 < <(echo "$X0 $Y0" | to_ll)
anchor_index() {  # dir kx ky lat lon -> writes index from index.base
  { cat $1/index.base; echo "projection = albers_nad83"; echo "truelat1 = 29.5"; echo "truelat2 = 45.5"; echo "stdlon = -96"
    echo "dx = $DX"; echo "dy = $DX"; echo "known_x = $2"; echo "known_y = $3"; echo "known_lat = $4"; echo "known_lon = $5"; } > $1/index; }
for K in col row; do
  anchor_index $W/exp2/layers/alb_b3_$K 1.0 1.0 $SWLAT2 $SWLON2
  anchor_index $W/exp2/layers/alb_b0_$K 1.0 1.0 $SWLAT2 $SWLON2
  for A in NW CENTER; do
    d=$W/exp2/layers/alb_b3_${K}_$A; mkdir -p $d; ln -sf $W/exp2/layers/alb_b3_$K/[0-9]* $d/; cp $W/exp2/layers/alb_b3_$K/index.base $d/
    if [[ $A == NW ]]; then anchor_index $d $NWX.0 $NWY.0 $NWLAT $NWLON; else anchor_index $d 10665.0 21293.0 $CLAT $CLON; fi
  done
done
log "exp2: sites"
> $W/exp2/sites.txt
for la in $(seq 32.75 0.75 41.75); do for lo in $(seq -124.25 0.75 -114.5); do echo "$la $lo" >> $W/exp2/sites.txt; done; done
awk '{print $1, $2}' $W/exp2/sites.txt | while read la lo; do echo "$lo $la"; done | gdaltransform -s_srs EPSG:4269 -t_srs EPSG:5070 > $W/exp2/sites_xy.txt
paste -d' ' $W/exp2/sites.txt $W/exp2/sites_xy.txt | awk -v x0=$X0 -v y0=$Y0 -v dx=$DX -v nc=$NC -v nr=$NR '{c=int(($3-x0)/dx+1.5); r=int(($4-y0)/dx+1.5); if (c>30 && c<nc-30 && r>30 && r<nr-30) print $1, $2, c, r, x0+(c-1)*dx, y0+(r-1)*dx}' > $W/exp2/sites_in.txt
awk '{print $5, $6}' $W/exp2/sites_in.txt | to_ll > $W/exp2/sites_local_ll.txt
log "exp2: $(wc -l < $W/exp2/sites_in.txt) sites inside the layer"
mklocal() { # site index c r lat lon; links only the tiles within one tile of the site (a 22 x 22 cell domain needs at most four)
  local ti=$(( ($2 - 1) / 1000 )) tj=$(( ($3 - 1) / 1000 ))
  for K in col row; do d=$W/exp2/layers/local/$1_$K; mkdir -p $d
    for a in $((ti-1)) $ti $((ti+1)); do for b in $((tj-1)) $tj $((tj+1)); do
      [[ $a -ge 0 && $b -ge 0 ]] || continue
      f=$(printf "%05d-%05d.%05d-%05d" $((a*1000+1)) $(((a+1)*1000)) $((b*1000+1)) $(((b+1)*1000)))
      [[ -f $W/exp2/layers/alb_b3_$K/$f ]] && ln -sf $W/exp2/layers/alb_b3_$K/$f $d/$f
    done; done
    cp $W/exp2/layers/alb_b3_$K/index.base $d/; anchor_index $d $2.0 $3.0 $4 $5; done; }
i=0; paste -d' ' $W/exp2/sites_in.txt $W/exp2/sites_local_ll.txt | while read la lo c r x y llat llon; do i=$((i+1)); mklocal $i $c $r $llat $llon; done
wps_env
RUNS=$W/exp2/runs.csv; echo "run,variant,proj,site_lat,site_lon,anchor_lat,anchor_lon,gx0,gy0,gd,npz" > $RUNS
run_site() { # id variant proj lat lon anchor_lat anchor_lon coldir rowdir gx0 gy0 gd
  local r=$W/exp2/runs/$1; mkdir -p $r; cd $r
  printf "name = COLIDX\n  priority = 1\n  dest_type = continuous\n  interp_option = default:nearest_neighbor\n  abs_path = default:%s/\n  fill_missing = 0\n  halt_on_missing = yes\n===============================\nname = ROWIDX\n  priority = 1\n  dest_type = continuous\n  interp_option = default:nearest_neighbor\n  abs_path = default:%s/\n  fill_missing = 0\n  halt_on_missing = yes\n===============================\n" $8 $9 > GEOGRID.TBL
  [[ -f $W/exp2/full_table ]] && { cat $NT GEOGRID.TBL > G2 && mv G2 GEOGRID.TBL; }
  cat > namelist.wps <<NL
&share
 wrf_core='ARW', max_dom=1, start_date='2025-08-07_18:00:00', end_date='2025-08-07_18:00:00', interval_seconds=3600, io_form_geogrid=2,
/
&geogrid
 parent_id=1, parent_grid_ratio=1, i_parent_start=1, j_parent_start=1, e_we=22, e_sn=22,
 geog_data_res='default', dx=100, dy=100, map_proj='lambert', ref_lat=$4, ref_lon=$5,
 truelat1=$4, truelat2=$4, stand_lon=$5, geog_data_path='$NG/', opt_geogrid_tbl_path='$r/'
/
NL
  srun -n 1 --exclusive geogrid.exe > geogrid.out 2>&1 < /dev/null
  python3 -c "
import numpy as np; from netCDF4 import Dataset
d=Dataset('geo_em.d01.nc'); np.savez('cells.npz', lat=d['XLAT_M'][0], lon=d['XLONG_M'][0], col=d['COLIDX'][0], row=d['ROWIDX'][0])" 2>/dev/null < /dev/null && echo "$1,$2,$3,$4,$5,$6,$7,${10},${11},${12},$r/cells.npz" >> $RUNS.$2
}
first=$(head -1 $W/exp2/sites_in.txt)
run_site probe SW_halo3 albers ${first% * * * *} "" "" $W/exp2/layers/alb_b3_col $W/exp2/layers/alb_b3_row $X0 $Y0 $DX
if [[ ! -f $W/exp2/runs/probe/cells.npz ]]; then log "minimal table failed; using the full table"; touch $W/exp2/full_table; fi
rm -f $RUNS.SW_halo3
i=0
while read la lo c r x y llat llon; do
  i=$((i+1))
  run_site s${i}_SW SW_halo3 albers $la $lo $SWLAT2 $SWLON2 $W/exp2/layers/alb_b3_col $W/exp2/layers/alb_b3_row $X0 $Y0 $DX &
  run_site s${i}_SW0 SW_halo0 albers $la $lo $SWLAT2 $SWLON2 $W/exp2/layers/alb_b0_col $W/exp2/layers/alb_b0_row $X0 $Y0 $DX &
  run_site s${i}_NW NW_halo3 albers $la $lo $NWLAT $NWLON $W/exp2/layers/alb_b3_col_NW $W/exp2/layers/alb_b3_row_NW $X0 $Y0 $DX &
  run_site s${i}_CE CENTER_halo3 albers $la $lo $CLAT $CLON $W/exp2/layers/alb_b3_col_CENTER $W/exp2/layers/alb_b3_row_CENTER $X0 $Y0 $DX &
  run_site s${i}_LO LOCAL_halo3 albers $la $lo $llat $llon $W/exp2/layers/local/${i}_col $W/exp2/layers/local/${i}_row $X0 $Y0 $DX &
  run_site s${i}_LL LATLON regular $la $lo "" "" $W/exp2/layers/ll_col $W/exp2/layers/ll_row $LLX0 $LLY0 $LLD &
  wait
done < <(paste -d' ' $W/exp2/sites_in.txt $W/exp2/sites_local_ll.txt)
for v in SW_halo3 SW_halo0 NW_halo3 CENTER_halo3 LOCAL_halo3 LATLON; do cat $RUNS.$v 2>/dev/null; done | sed 's/,regular,/,ll,/' >> $RUNS
log "exp2: $(($(wc -l < $RUNS) - 1)) runs collected; transforming cell centres"
python3 -c "
import numpy as np
for l in open('$RUNS').read().splitlines()[1:]:
    p=l.split(',')
    if p[2]=='albers':
        z=np.load(p[10])
        for la,lo in zip(z['lat'].ravel(), z['lon'].ravel()): print(f'{lo:.8f} {la:.8f}')
" > $W/exp2/cells_ll.txt
gdal_env
gdaltransform -s_srs EPSG:4269 -t_srs EPSG:5070 < $W/exp2/cells_ll.txt > $W/exp2/cells_xy.txt
wps_env
python3 $X/exp2_analyze.py $RUNS $W/exp2/cells_xy.txt $W/exp2/results.csv $W/exp2/summary.txt > /dev/null

# ---------------------------------------------------------------- Report
{
echo "ANCHOR STUDY  $(date -Is)  job $SLURM_JOB_ID  host $(hostname)"
echo; echo "== Experiment 1: NFUEL_CAT match with NCAR, per fire x layer"; echo "fires:"; cat $W/exp1/fires.txt
echo; column -s, -t < $CSV1
echo; echo "best layer per fire:"
python3 -c "
import csv
rows=[r for r in csv.DictReader(open('$CSV1')) if r['pct_identical']]
for f in sorted({r['fire'] for r in rows}):
    rs=sorted([r for r in rows if r['fire']==f], key=lambda r:-float(r['pct_identical']))
    print(f'{f:45s}', ' | '.join(f\"{r['layer']} {float(r['pct_identical']):.3f}%\" for r in rs[:3]))"
echo; echo "== Experiment 2: geogrid positioning error (coded layers), by variant"; cat $W/exp2/summary.txt
echo; echo "worst 15 site-variant rows by shift:"; (head -1 $W/exp2/results.csv; tail -n +2 $W/exp2/results.csv | sort -t, -k9 -gr | head -15) | column -s, -t
echo; echo "== environment"; module list 2>&1 | tail -n +2 | head -20
} > $W/REPORT.txt
log "done; read $W/REPORT.txt"
