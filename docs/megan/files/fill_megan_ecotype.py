#!/usr/bin/env python3
"""MEGAN3.2 grid_ecotype.csv 결측(EcotypeID=65535) 채우기.

규칙
 1) 셀 안에 유효 생태유형이 일부 있으면: 결측 비율을 그 셀의 유효 생태유형에 비율대로 재배분
 2) 셀 전체가 결측이면: 격자 거리(행·열)로 가장 가까운 '유효 생태유형이 있는 셀'의 구성을 복사
    (같은 거리면 gridID가 작은 셀)
기록: 셀마다 처리 방법·참조 셀·거리·MCIP 육지/수면(LWMASK)·식생 비율을 함께 저장

사용법:
 python3 fill_megan_ecotype.py ECO_IN GROWTH_IN GRIDCRO2D NCOLS NROWS ECO_OUT RECORD_OUT
"""
import sys
import numpy as np
import pandas as pd
from netCDF4 import Dataset

eco_in, gf_in, gcro, ncols, nrows, eco_out, rec_out = sys.argv[1:8]
ncols, nrows = int(ncols), int(nrows)
MISSING = 65535

eco = pd.read_csv(eco_in)
gf = pd.read_csv(gf_in)
n = ncols * nrows
assert sorted(eco.gridID.unique()) == list(range(1, n + 1)), "gridID 범위 불일치"
assert sorted(gf.gridID) == list(range(1, n + 1))

with Dataset(gcro) as d:
    lw = np.asarray(d["LWMASK"][0, 0])          # (ROW, COL), 1=육지 0=수면
assert lw.shape == (nrows, ncols), lw.shape
gid = np.arange(1, n + 1)
col = (gid - 1) % ncols                          # CT3.csv와 같은 순서(열이 안쪽 반복)
row = (gid - 1) // ncols

valid = eco[eco.EcotypeID != MISSING]
miss = eco[eco.EcotypeID == MISSING].groupby("gridID").EcotypeFrac.sum()
has_valid = set(valid.gridID)
donors = np.array(sorted(has_valid))
dr, dc = row[donors - 1], col[donors - 1]

out_rows, records = [], []
vegfrac = gf.set_index("gridID")[["TreeFrac", "CropFrac", "ShrubFrac", "HerbFrac"]].sum(axis=1)
for g in gid:
    mf = float(miss.get(g, 0.0))
    method, src, dist = "unchanged", g, 0.0
    if mf == 0.0:
        part = valid[valid.gridID == g][["EcotypeID", "EcotypeFrac"]].copy()
        # 원자료 CSV 소수 4자리 반올림 때문에 합이 0.9999~1.0001인 셀이 있어 합 1로 정규화
        part["EcotypeFrac"] = part.EcotypeFrac / part.EcotypeFrac.sum()
    elif g in has_valid:
        part = valid[valid.gridID == g][["EcotypeID", "EcotypeFrac"]].copy()
        part["EcotypeFrac"] = part.EcotypeFrac / part.EcotypeFrac.sum()
        method = "renormalize"
    else:
        dd = np.hypot(dr - row[g - 1], dc - col[g - 1])
        k = int(np.argmin(dd))                     # 같은 거리면 gridID 작은 셀(정렬되어 있음)
        src, dist = int(donors[k]), float(dd[k])
        part = valid[valid.gridID == src][["EcotypeID", "EcotypeFrac"]].copy()
        part["EcotypeFrac"] = part.EcotypeFrac / part.EcotypeFrac.sum()
        method = "nearest"
    part.insert(0, "gridID", g)
    out_rows.append(part)
    records.append(dict(gridID=g, ICELL=col[g - 1] + 1, JCELL=row[g - 1] + 1,
                        MCIP_LWMASK=int(lw[row[g - 1], col[g - 1]]),
                        vegetation_frac=round(float(vegfrac[g]), 4),
                        missing_frac=round(mf, 4), method=method,
                        source_gridID=src, distance_cells=round(dist, 3)))

out = pd.concat(out_rows, ignore_index=True)
assert np.allclose(out.groupby("gridID").EcotypeFrac.sum(), 1.0, atol=1e-6)
assert (out.EcotypeID != MISSING).all()
out.to_csv(eco_out, index=False, float_format="%.4f")
rec = pd.DataFrame(records)
rec.to_csv(rec_out, index=False)

veg = rec.vegetation_frac > 0
print("cells", n, "| ecotypes", sorted(out.EcotypeID.unique()))
print(rec.groupby("method").size().to_string())
print("vegetated & changed:", int((veg & (rec.method != "unchanged")).sum()),
      "(MCIP land", int((veg & (rec.method != "unchanged") & (rec.MCIP_LWMASK == 1)).sum()),
      ", water", int((veg & (rec.method != "unchanged") & (rec.MCIP_LWMASK == 0)).sum()), ")")
nn = rec[rec.method == "nearest"]
if len(nn):
    print("nearest distance (cells): max", nn.distance_cells.max(), "mean", round(nn.distance_cells.mean(), 2))
