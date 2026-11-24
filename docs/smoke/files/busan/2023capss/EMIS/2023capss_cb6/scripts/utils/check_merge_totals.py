#!/usr/bin/env python3
"""Check SMOKE Mrggrid outputs of the Busan case against the premerged sector files.

For every merged file emis_mole_all_<YYYYMMDD>_<GRID>_nobeis_norwc_<CASE>.ncf:
  - the premerged files of all sectors with mergesector=Y in the sector list exist,
  - grid name, time steps, layers and start date match the premerged files,
  - every species equals the sum of the premerged sectors (relative tolerance),
  - no negative or non-finite values.
Run from EMIS/<CASE>:  python3 scripts/utils/check_merge_totals.py 27KM 09KM 03KM 01KM
Exit code 0 = all files OK.
"""
import csv, glob, os, sys
import numpy as np
from netCDF4 import Dataset

CASE = "2023capss_cb6"
SPC = "cmaq_cb6ae7"
TOL = 1.0e-5
SHOW = ["NO", "SO2", "CO", "PEC", "PMOTHR"]


def merged_sectors(grid):
    name = f"scripts/sectorlist_{CASE}_01KM" if grid == "01KM" else f"scripts/sectorlist_{CASE}"
    with open(name) as f:
        return name, [r["sector"] for r in csv.DictReader(f) if r["mergesector"] == "Y"]


def check(grid):
    slist, sectors = merged_sectors(grid)
    mdir = f"smoke_out/{CASE}/{grid}/{SPC}/merged_nobeis_norwc"
    files = sorted(glob.glob(f"{mdir}/emis_mole_all_*_{grid}_nobeis_norwc_{CASE}.ncf"))
    print(f"== {grid}: {len(files)} merged files, {len(sectors)} sectors from {slist}")
    if not files:
        print("   FAIL: no merged files"); return False
    ok_all = True
    for mf in files:
        date = os.path.basename(mf).split("_")[3]   # emis_mole_all_<YYYYMMDD>_...
        pfiles = [f"premerged/{s}/emis_mole_{s}_{date}_{grid}_{SPC}_{CASE}.ncf" for s in sectors]
        miss = [p for p in pfiles if not os.path.exists(p)]
        if miss:
            print(f"   {date} FAIL: missing premerged {miss}"); ok_all = False; continue
        M = Dataset(mf)
        P = [Dataset(p) for p in pfiles]
        msg = []
        if M.GDNAM.strip() != P[0].GDNAM.strip(): msg.append(f"GDNAM {M.GDNAM.strip()}")
        if M.dimensions["TSTEP"].size != P[0].dimensions["TSTEP"].size: msg.append("TSTEP")
        if M.dimensions["LAY"].size != 1: msg.append(f"LAY {M.dimensions['LAY'].size}")
        if M.SDATE != P[0].SDATE or M.STIME != P[0].STIME: msg.append(f"SDATE {M.SDATE} {M.STIME}")
        mvars = [v for v in M.variables if v != "TFLAG"]
        pvars = set(v for d in P for v in d.variables if v != "TFLAG")
        if set(mvars) != pvars: msg.append(f"species differ {sorted(set(mvars) ^ pvars)}")
        worst, wv, bad = 0.0, "", 0
        for v in mvars:
            x = np.asarray(M[v][:], dtype="f8")
            if not np.isfinite(x).all() or (x < 0).any(): bad += 1
            y = sum(np.asarray(d[v][:], dtype="f8") for d in P if v in d.variables)
            s = np.abs(y).sum()
            r = np.abs(x - y).sum() / s if s > 0 else np.abs(x).sum()
            if r > worst: worst, wv = r, v
        if bad: msg.append(f"{bad} species with negative/non-finite values")
        if worst > TOL: msg.append(f"sum mismatch {worst:.2e} ({wv})")
        tot = "  ".join(f"{v}={float(np.asarray(M[v][:], dtype='f8').sum()):.4g}" for v in SHOW if v in M.variables)
        status = "OK" if not msg else "FAIL: " + "; ".join(msg)
        print(f"   {date} nvar={len(mvars)} tstep={M.dimensions['TSTEP'].size} sdate={M.SDATE} "
              f"maxreldiff={worst:.1e} ({wv}) {status}")
        print(f"            25h sums [mol/s or g/s]: {tot}")
        ok_all = ok_all and not msg
        M.close(); [d.close() for d in P]
    return ok_all


if __name__ == "__main__":
    grids = sys.argv[1:] or ["27KM", "09KM", "03KM", "01KM"]
    results = [check(g) for g in grids]
    print("RESULT:", "ALL OK" if all(results) else "FAIL")
    sys.exit(0 if all(results) else 1)
