#!/usr/bin/env python3
"""
Busan SMOKE case 2023capss_cb6: foreign anthropogenic emissions from HTAP_v3.2 (sector "htap").

What it does
  1. window   : crops the global 0.1 deg HTAP_v3.2 annual flux files (kg m-2 s-1) to 90-162E, 18-56N
                (covers the 27KM domain 91.5-160.5E, 19.8-54.0N with margin) -> 720 x 380 cells
  2. Korea    : sets to 0 every 0.1 deg cell touched by a CAPSS 2023 1km cell (area, mobile, sea, point),
                so that South Korea (land + sea) comes only from CAPSS 2023 (no double counting)
  3. names    : renames the HTAP_v3.2 sector variables to short names (<=16 chars) and writes
                SMOKE gridded-NetCDF list files (#LIST GRID), one per sector group + one with all groups
  4. masks    : crops the SMOKE example GRIDMASK_EDGAR.ncf (GEOCODE country codes, TZONES) to the same window
  5. profiles : copies the example HTAPv3 temporal/speciation profiles; adds GSREF/TREF rows for the
                detailed sectors the example lacks (each mapped to its parent sector, see PARENT)

Decisions (2026-11-10): HTAP_v3.2 2020 annual fluxes; CO NH3 NMVOC NOx SO2, and PM as in the EPA HTAP design:
BC -> PEC, OC -> POC (profile 0), PM2_5 and PM10 written WITHOUT BC+OC (PM2_5 'other' profiles have no PEC/POC;
PMC = PM10 - PM2_5 unchanged); where BC+OC > PM2.5, BC and OC are scaled down to PM2.5 so that
PEC + POC + PM2_5(other) = HTAP PM2.5 in every cell (carbon_adjust_t in the summary); South Korea removed by CAPSS 2023 coverage (GEOCODE alone cannot separate Korean coast/sea).

Usage
  python3 make_busan_htap_v32_inputs.py --htap <folder with edgar_HTAPv32_<year>_<pol>.zip> --year 2020 \
      --capss <CAPSS 2023 original folder> --example <smoke_example_case_v3> --out <package folder> \
      [--final <case EMIS folder, default /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/EMIS>]
  The package is then copied to the case:  cp -r <out>/EMIS/. <final>/
Output (under <out>/EMIS, same layout as the case EMIS folder)
  2023capss_cb6/inputs/htap/htap_v32_<year>_<POL>_busan.nc, arinv.HTAPv32.<GROUP>.lst, htap_summary_<TAG>.csv
  ge_dat/EDGAR/GRIDMASK_EDGAR_busan_window.ncf, geocode1-4_edgar.txt, HTAPv32_profiles/*
  ge_dat/invtable_busan_htap_<TAG>.txt (domestic INVTABLE + PEC/POC)
"""
import argparse, os, glob, io, zipfile, tempfile, shutil, time, collections
import numpy as np, pandas as pd, netCDF4 as nc
from pyproj import CRS, Transformer

ap = argparse.ArgumentParser()
for k in ('htap', 'capss', 'example', 'out'):
    ap.add_argument('--' + k, required=True)
ap.add_argument('--year', type=int, default=2020)
ap.add_argument('--invtable', default='/home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/EMIS/ge_dat/invtable_busan_2017capss_20261021.txt',
                help='domestic INVTABLE; PEC/POC lines from the example INVTABLE are added to a copy for HTAP')
ap.add_argument('--final', default='/home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/EMIS',
                help='case EMIS folder the package is installed to (paths written in the list files)')
a = ap.parse_args()
TAG, CASE = '20261110', '2023capss_cb6'
OUT = a.out.rstrip('/') + '/EMIS'
LON0, LON1, LAT0, LAT1, D = 90.0, 162.0, 18.0, 56.0, 0.1
NC_, NR_ = int(round((LON1 - LON0) / D)), int(round((LAT1 - LAT0) / D))      # 720, 380
T0 = time.time()
def log(*x): print(f'[{time.time()-T0:6.0f}s]', *x, flush=True)
def mk(p): os.makedirs(os.path.dirname(p), exist_ok=True); return p

# ---------------- pollutants and sectors
POLS = {'CO': 'CO', 'NH3': 'NH3', 'NMVOC': 'VOC', 'NOx': 'NOX', 'PM10': 'PM10', 'PM2.5': 'PM2_5', 'SO2': 'SO2'}
# HTAP_v3.2 variable -> (SCC used in SMOKE, short NetCDF variable name)
VARS = {
    'HTAPv3_1_International_Shipping':        ('INTSHIP',      'IntShipping'),
    'HTAPv3_2_1_1_Domestic_Aviation_LTO':     ('DOMAVIA_LTO',  'DomAviaLTO'),
    'HTAPv3_2_1_2_Domestic_Aviation_CDS':     ('DOMAVIA_CDS',  'DomAviaCDS'),
    'HTAPv3_2_1_3_Domestic_Aviation_CRS':     ('DOMAVIA_CRS',  'DomAviaCRS'),
    'HTAPv3_2_2_1_International_Aviation_LTO': ('INTAVIA_LTO', 'IntAviaLTO'),
    'HTAPv3_2_2_2_International_Aviation_CDS': ('INTAVIA_CDS', 'IntAviaCDS'),
    'HTAPv3_2_2_3_International_Aviation_CRS': ('INTAVIA_CRS', 'IntAviaCRS'),
    'HTAPv3_3_Energy':                        ('ENERGY',       'Energy'),
    'HTAPv3_4_1_Industry':                    ('INDUSTRY',     'Industry'),
    'HTAPv3_4_2_Fugitive':                    ('FUGITIVE',     'Fugitive'),
    'HTAPv3_4_3_Solvents':                    ('SOLVENTS',     'Solvents'),
    'HTAPv3_5_1_Road_Transport':              ('TRANSPORT',    'Transport'),
    'HTAPv3_5_2_Brake_and_Tyre_wear':         ('BWTW',         'BrakeTyreWear'),
    'HTAPv3_5_3_Domestic_shipping':           ('DOMSHIP',      'DomShipping'),
    'HTAPv3_5_4_Other_ground_transport':      ('OTHTRANSPORT', 'OtherTransport'),
    'HTAPv3_6_Residential':                   ('RESIDENT',     'Residential'),
    'HTAPv3_7_Waste':                         ('WASTE',        'Waste'),
    'HTAPv3_8_1_Agricultural_waste_burning':  ('AGRIBURN',     'AgriBurn'),
    'HTAPv3_8_2_Agriculture_livestock':       ('LIVESTOCK',    'Livestock'),
    'HTAPv3_8_3_Agriculture_crops':           ('CROPS',        'Crops'),
}
def lookup(v):
    """exact name, or brake/tyre wear variants (name not yet seen in v3.2 files)"""
    if v in VARS: return VARS[v]
    if 'brake' in v.lower() or 'tyre' in v.lower() or 'tire' in v.lower(): return VARS['HTAPv3_5_2_Brake_and_Tyre_wear']
    return None
GROUPS = {'INTSHIP': ['INTSHIP'],
          'AVIATION': ['DOMAVIA_LTO', 'DOMAVIA_CDS', 'DOMAVIA_CRS', 'INTAVIA_LTO', 'INTAVIA_CDS', 'INTAVIA_CRS'],
          'ENERGY': ['ENERGY'], 'INDUSTRY': ['INDUSTRY', 'FUGITIVE', 'SOLVENTS'],
          'TRANSPORT': ['TRANSPORT', 'BWTW', 'DOMSHIP', 'OTHTRANSPORT'], 'RESIDENT': ['RESIDENT'], 'WASTE': ['WASTE'],
          'AGRICULTURE': ['AGRIBURN', 'LIVESTOCK', 'CROPS']}
# detailed sectors without own entries in the example GSREF/TREF -> parent key that has them
PARENT = {'INTSHIP': 'SHIPS', 'DOMSHIP': 'SHIPS',
          'DOMAVIA_LTO': 'AIR_LTO', 'DOMAVIA_CDS': 'AIR_CDS', 'DOMAVIA_CRS': 'AIR_CRS',
          'INTAVIA_LTO': 'AIR_LTO', 'INTAVIA_CDS': 'AIR_CDS', 'INTAVIA_CRS': 'AIR_CRS',
          'FUGITIVE': 'INDUSTRY', 'SOLVENTS': 'INDUSTRY', 'OTHTRANSPORT': 'TRANSPORT', 'BWTW': 'TRANS_BWTW',
          'AGRIBURN': 'AG_BURNING', 'LIVESTOCK': 'AG', 'CROPS': 'AG'}

# ---------------- example files
EXG = os.path.join(a.example, 'ge_dat', 'EDGAR')
EXP = os.path.join(EXG, 'HTAPv3_profiles')
for f in [os.path.join(EXG, 'GRIDMASK_EDGAR.ncf')] + [os.path.join(EXG, f'geocode{i}_edgar.txt') for i in range(1, 5)]:
    if not os.path.isfile(f): raise SystemExit(f'ERROR: example file not found: {f}')
PROF = {k: (glob.glob(os.path.join(EXP, p)) or [None])[0] for k, p in
        [('gsref', 'gsref_HTAP_*'), ('gspro', 'gspro_HTAP_CB06_*'), ('gscnv', 'gscnv_edgar_HTAPv3_*'),
         ('tref', 'HTAP_2011_BaseA_tref_*'), ('hourly', 'HTAP_2011_BaseA_tpro_hourly_*'),
         ('weekly', 'HTAP_2011_BaseA_tpro_weekly_*'), ('monthly', 'HTAP_2011_BaseA_tpro_monthly_*')]}
for k, v in PROF.items():
    if v is None: raise SystemExit(f'ERROR: example HTAPv3 profile ({k}) not found in {EXP}')

# =====================================================================================
# 1. GRIDMASK window (GEOCODE, TZONES)
# =====================================================================================
src = nc.Dataset(os.path.join(EXG, 'GRIDMASK_EDGAR.ncf'))
xo, yo, dx = float(src.XORIG), float(src.YORIG), float(src.XCELL)
gc0 = int(round(((LON0 - xo) % 360.0) / dx)); gr0 = int(round((LAT0 - yo) / dx))
GEO = np.asarray(src['GEOCODE'][0, 0, gr0:gr0 + NR_, gc0:gc0 + NC_])
gmp = mk(f'{OUT}/ge_dat/EDGAR/GRIDMASK_EDGAR_busan_window.ncf')
with nc.Dataset(gmp, 'w', format=src.file_format) as dst:
    for k in src.ncattrs():
        v = src.getncattr(k)
        v = {'NCOLS': NC_, 'NROWS': NR_, 'XORIG': xo + gc0 * dx, 'YORIG': yo + gr0 * dx}.get(k, v)
        dst.setncattr(k, v)
    for n, dm in src.dimensions.items():
        dst.createDimension(n, {'COL': NC_, 'ROW': NR_}.get(n, None if dm.isunlimited() else len(dm)))
    for n, v in src.variables.items():
        o = dst.createVariable(n, v.datatype, v.dimensions)
        for k in v.ncattrs(): o.setncattr(k, v.getncattr(k))
        o[:] = v[:] if n == 'TFLAG' else v[:, :, gr0:gr0 + NR_, gc0:gc0 + NC_]
src.close()
log(f'GRIDMASK window: COL {gc0}-{gc0+NC_-1}, ROW {gr0}-{gr0+NR_-1} -> {gmp}')
for i in range(1, 5):
    shutil.copy(os.path.join(EXG, f'geocode{i}_edgar.txt'), mk(f'{OUT}/ge_dat/EDGAR/geocode{i}_edgar.txt'))

# =====================================================================================
# 2. South Korea mask from CAPSS 2023 1km cells (same file detection as the domestic generator)
# =====================================================================================
def _members():
    out = []
    for f in sorted(glob.glob(os.path.join(a.capss, '*'))):
        if f.lower().endswith('.zip'):
            z = zipfile.ZipFile(f)
            for i in z.infolist():
                if i.is_dir(): continue
                out.append((os.path.basename(f) + ':' + i.filename, i.file_size,
                            (lambda z=z, i=i: io.TextIOWrapper(z.open(i), encoding='cp949', errors='replace'))))
        elif os.path.isfile(f):
            out.append((os.path.basename(f), os.path.getsize(f), (lambda f=f: open(f, encoding='cp949', errors='replace'))))
    return out
MEMBERS = _members()
def _pick(cond, what):
    m = [x for x in MEMBERS if cond(x[0])]
    if not m: raise SystemExit(f'ERROR: no CAPSS {what} file found in {a.capss}')
    m.sort(key=lambda x: -x[1])
    if len(m) > 1 and abs(m[0][1] - sum(x[1] for x in m[1:])) <= 0.01 * m[0][1]:
        m = m[:1]
    log(f'CAPSS {what}: ' + ', '.join(f'{x[0]} ({x[1]:,} B)' for x in m))
    return m
def _base(n): return n.split(':')[-1]
SRC = {'point': _pick(lambda n: '점오염원' in n and not n.lower().endswith('.zip'), 'point'),
       'sea': _pick(lambda n: '바다' in n, 'sea'),
       'area': _pick(lambda n: '바다' not in n and (n.split(':')[0].startswith('면오염원') or _base(n).endswith('a(2023).txt')) and n.endswith('.txt'), 'area'),
       'mobile': _pick(lambda n: '바다' not in n and (n.split(':')[0].startswith('이동오염원') or _base(n).endswith('m(2023).txt')) and n.endswith('.txt'), 'mobile')}
cells = set()
for sec, mems in SRC.items():
    n0 = len(cells)
    for label, size, op in mems:
        with op() as fh:
            for ch in pd.read_csv(fh, dtype=str, chunksize=2_000_000,
                                  usecols=lambda c: c.strip() in ('TM_X', 'TM_Y', 'INVEST_YEAR')):
                ch.columns = [c.strip() for c in ch.columns]
                if 'INVEST_YEAR' in ch.columns and sec != 'point': ch = ch[ch.INVEST_YEAR == '2023']
                x = np.floor(pd.to_numeric(ch.TM_X, errors='coerce')).dropna().astype(np.int32)
                y = np.floor(pd.to_numeric(ch.TM_Y, errors='coerce')).dropna().astype(np.int32)
                cells.update(zip(x.values.tolist(), y.values.tolist()))
    log(f'CAPSS {sec}: unique 1km cells so far {len(cells)} (+{len(cells)-n0})')
cx = np.array([c[0] for c in cells], dtype=np.float64); cy = np.array([c[1] for c in cells], dtype=np.float64)
TMCRS = CRS.from_proj4('+proj=tmerc +lat_0=38 +lon_0=127.002890277778 +k=1 +x_0=200000 +y_0=500000 +ellps=bessel '
                       '+towgs84=-115.80,474.99,674.11,1.16,-2.31,-1.63,6.43 +units=m +no_defs')
T_LL = Transformer.from_crs(TMCRS, CRS.from_epsg(4326), always_xy=True)
off = np.array([1 / 6, 0.5, 5 / 6])                       # 3 x 3 sub-points per 1km cell
ox, oy = [g.ravel() for g in np.meshgrid(off, off)]
KMASK = np.zeros((NR_, NC_), dtype=bool)
