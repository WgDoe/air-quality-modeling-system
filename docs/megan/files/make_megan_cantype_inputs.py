#!/usr/bin/env python3
"""MEGAN 3.2 캐노피 유형(CT3) 입력 6종을 동아시아 범위로 잘라 만든다.

  사용법: python3 make_megan_cantype_inputs.py <RAW>     (RAW = $MODEL/DATA/EMIS/MEGAN)
  출력  : <RAW>/cantype_EA/{TC,SC,GC,CC}30s7.nc, NTfrac_EA.nc, tropfrac_EA.nc

- 생육형 4종(TC/SC/GC/CC, %): GFv7 30초 자료를 값 변경 없이 자르기만 한다.
- NTfrac  : NCAR d312006 veg_GrowthFormFracions.nc의 nl_tree(나무 중 침엽수 %) / 100
- tropfrac: 같은 파일의 trop_tree(나무 중 열대수 %) / 100
  NCAR 자료는 위도 오름차순(-57~83), GFv7은 내림차순(80~-60)이라 위도값으로 행을 맞춘다.
- 범위: 위도 18~56°, 경도 90~162° (부산 사례 27KM 도메인 + 여유 1° 이상).
  전처리기가 입력 변수를 실수 두 벌로 읽으므로 전지구 그대로 쓰면 약 5.8GB가 필요하다.
"""
import os, sys
import numpy as np
from netCDF4 import Dataset

RAW = sys.argv[1]
GF = f"{RAW}/GFv7nc"
NCAR = f"{RAW}/NCAR_d312006/veg_GrowthFormFracions.nc"
OUT = f"{RAW}/cantype_EA"
LAT_MIN, LAT_MAX, LON_MIN, LON_MAX = 18.0, 56.0, 90.0, 162.0
os.makedirs(OUT, exist_ok=True)

# 기준 격자: SC30s7_SCpercent.nc 좌표(정확히 1/120°)
with Dataset(f"{GF}/SC30s7_SCpercent.nc") as ref:
    lat = ref["lat"][:].astype("f8")
    lon = ref["lon"][:].astype("f8")
iy = np.where((lat >= LAT_MIN) & (lat <= LAT_MAX))[0]
ix = np.where((lon >= LON_MIN) & (lon <= LON_MAX))[0]
y0, y1, x0, x1 = iy[0], iy[-1] + 1, ix[0], ix[-1] + 1
clat, clon = lat[y0:y1], lon[x0:x1]
print("crop rows", y0, y1, "cols", x0, x1, "->", clat.size, "x", clon.size)


def write_nc(fname, vname, data, dtype, fill, units, note):
    path = f"{OUT}/{fname}"
    with Dataset(path, "w", format="NETCDF4") as d:
        d.createDimension("lat", clat.size)
        d.createDimension("lon", clon.size)
        v = d.createVariable("lat", "f8", ("lat",)); v[:] = clat
        v.units = "degrees_north"; v.long_name = "latitude coordinate"
        v = d.createVariable("lon", "f8", ("lon",)); v[:] = clon
        v.units = "degrees_east"; v.long_name = "longitude coordinate"
        v = d.createVariable(vname, dtype, ("lat", "lon"), zlib=True, complevel=4)
        v.units = units
        v.missing_value = np.array(fill, dtype=dtype)
        v.coordinates = "lon lat"
        v[:] = data
        d.note = note
    print("wrote", path, vname, float(np.nanmin(data)), float(np.nanmax(data)))


# 1) 생육형 4종: 원본 값을 그대로 자르기
for fname, vname in [("TC30s7.nc", "TCpercent"), ("SC30s7_SCpercent.nc", "SCpercent"),
                     ("GC30s7.nc", "GCpercent"), ("CC30s7.nc", "CCpercent")]:
    with Dataset(f"{GF}/{fname}") as d:
        v = d[vname]
        v.set_auto_maskandscale(False)
        assert v.shape == (lat.size, lon.size), (fname, v.shape)
        data = v[y0:y1, x0:x1]
    out = fname.replace("_SCpercent", "")
    write_nc(out, vname, data, "u1", 127, "percent", f"cropped from GFv7nc/{fname} (values unchanged)")

# 2) NTfrac / tropfrac: NCAR 자료를 위도·경도값으로 GFv7 격자에 대응
with Dataset(NCAR) as d:
    nlat = d["lat"][:].astype("f8")
    nlon = d["lon"][:].astype("f8")
    ky = np.rint((clat - nlat[0]) * 120.0).astype(int)
    kx = np.rint((clon - nlon[0]) * 120.0).astype(int)
    assert ky.min() >= 0 and ky.max() < nlat.size and kx.min() >= 0 and kx.max() < nlon.size
    dy = np.abs(nlat[ky] - clat).max(); dx = np.abs(nlon[kx] - clon).max()
    print("max coord mismatch (deg): lat", dy, "lon", dx)
    assert dy < 0.5 / 120 and dx < 0.5 / 120
    for nvar, fname, oname in [("nl_tree", "NTfrac_EA.nc", "NTfrac"),
                               ("trop_tree", "tropfrac_EA.nc", "tropfrac")]:
        v = d[nvar]
        v.set_auto_maskandscale(False)
        blk = v[ky.min():ky.max() + 1, kx.min():kx.max() + 1].astype("i2")
        blk = blk[ky - ky.min()][:, kx - kx.min()]
        bad = (blk < 0) | (blk > 100)
        print(nvar, "missing/out-of-range cells set to 0:", int(bad.sum()))
        frac = np.where(bad, 0, blk).astype("f8") / 100.0
        write_nc(fname, oname, frac, "f8", -1.0, "fraction of tree cover (0-1)",
                 f"{nvar}/100 from NCAR GDEX d312006 veg_GrowthFormFracions.nc, "
                 f"matched by coordinate to GFv7 30s grid")
print("done")
