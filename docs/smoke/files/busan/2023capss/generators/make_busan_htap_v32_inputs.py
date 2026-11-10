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
for s in range(0, len(cx), 200_000):
    X = ((cx[s:s + 200_000, None] + ox[None, :]) * 1000.0).ravel()
    Y = ((cy[s:s + 200_000, None] + oy[None, :]) * 1000.0).ravel()
    lo, la = T_LL.transform(X, Y)
    c = np.floor((lo - LON0) / D).astype(np.int64); r = np.floor((la - LAT0) / D).astype(np.int64)
    ok = (c >= 0) & (c < NC_) & (r >= 0) & (r < NR_)
    KMASK[r[ok], c[ok]] = True
log(f'South Korea mask: {KMASK.sum()} of {NC_*NR_} 0.1 deg cells (GEOCODE 197000 cells: {(GEO == 197000).sum()}, '
    f'of them outside mask: {((GEO == 197000) & ~KMASK).sum()})')

# =====================================================================================
# 3. HTAP files: window, Korea removal, rename
# =====================================================================================
R = 6371.0e3
lat_e = LAT0 + D * np.arange(NR_ + 1)
AREA = (R ** 2 * np.deg2rad(D) * np.diff(np.sin(np.deg2rad(lat_e))))[:, None] * np.ones((1, NC_))   # m2
SEC = 365.0 * 86400.0
SUMMARY, LST = [], collections.defaultdict(list)
codes = sorted(set(np.unique(GEO[KMASK]).tolist()))
odir = f'{OUT}/{CASE}/inputs/htap'
os.makedirs(a.out, exist_ok=True)
tmp = tempfile.mkdtemp(prefix='htap_', dir=a.out)

def read_window(hp):
    """window of one HTAP pollutant file: {short: (scc, htap_variable, kg m-2 s-1 array, attrs)}, + source text"""
    z = os.path.join(a.htap, f'edgar_HTAPv32_{a.year}_{hp}.zip')
    if not os.path.isfile(z): raise SystemExit(f'ERROR: HTAP file not found: {z}')
    with zipfile.ZipFile(z) as zz:
        ncm = [n for n in zz.namelist() if n.endswith('.nc')][0]
        zz.extract(ncm, tmp)
    fin = os.path.join(tmp, ncm)
    ds = nc.Dataset(fin)
    lat = np.asarray(ds['lat'][:]); lon = np.asarray(ds['lon'][:]) % 360.0
    ii = np.where((lat > LAT0) & (lat < LAT1))[0]; jj = np.where((lon > LON0) & (lon < LON1))[0]
    if len(ii) != NR_ or len(jj) != NC_: raise SystemExit(f'ERROR: window size {len(jj)}x{len(ii)} in {ncm}')
    i0, i1, j0, j1 = ii.min(), ii.max() + 1, jj.min(), jj.max() + 1
    if i1 - i0 != NR_ or j1 - j0 != NC_: raise SystemExit(f'ERROR: window not contiguous in {ncm}')
    oi, oj = np.argsort(lat[i0:i1]), np.argsort(lon[j0:j1])
    if not (np.allclose(lat[i0:i1][oi], LAT0 + D * (np.arange(NR_) + 0.5)) and
            np.allclose(lon[j0:j1][oj], LON0 + D * (np.arange(NC_) + 0.5))):
        raise SystemExit(f'ERROR: unexpected cell centres in {ncm}')
    out, unknown = {}, []
    for vn, var in ds.variables.items():
        if vn in ('lat', 'lon'): continue
        m = lookup(vn)
        if m is None: unknown.append(vn); continue
        x = np.ma.filled(var[i0:i1, j0:j1].astype(np.float64), 0.0)[oi][:, oj]
        x[~np.isfinite(x)] = 0.0; x[x > 1e30] = 0.0
        out[m[1]] = (m[0], vn, x, {'long_name': getattr(var, 'long_name', m[1]),
                                    'description': getattr(var, 'description', m[1])})
    src = os.path.basename(z) + ':' + ncm + ' / original description: ' + str(getattr(ds, 'description', ''))
    ds.close(); os.remove(fin)
    if unknown: raise SystemExit(f'ERROR: unmapped variables in {ncm}: {unknown} (add them to VARS)')
    return out, src

# BC and OC first: PM2_5 and PM10 are written without carbon (EPA HTAP design: PM2_5_OTH profiles + PEC/POC
# directly from the BC/OC inventories), so that PEC + POC + PM2_5(other) = original PM2.5 in every cell
CARBON = {}
for hp in ('BC', 'OC'):
    CARBON[hp], _ = read_window(hp)
PM25, PM25SRC = read_window('PM2.5')
CLOSS = collections.defaultdict(float)          # carbon removed by the scaling, t/yr, per (pollutant, short)
for short, (scc, vn, x, at) in PM25.items():
    c = sum(CARBON[k][short][2] for k in ('BC', 'OC') if short in CARBON[k])
    if np.isscalar(c): continue
    f = np.where(c > x, x / np.maximum(c, 1e-30), 1.0)    # BC+OC > PM2.5: scale BC and OC down to PM2.5
    for k in ('BC', 'OC'):
        if short in CARBON[k]:
            arr = CARBON[k][short][2]
            CLOSS[(k, short)] = float(((1.0 - f) * arr * AREA * SEC / 1000.0).sum())
            arr *= f
log(f'BC/OC read; scaled down where BC+OC > PM2.5: BC {sum(v for (k, _), v in CLOSS.items() if k == "BC"):,.0f} t/yr, '
    f'OC {sum(v for (k, _), v in CLOSS.items() if k == "OC"):,.0f} t/yr')

def write_pol(ip, data, src, note):
    fout = mk(f'{odir}/htap_v32_{a.year}_{ip}_busan.nc')
    with nc.Dataset(fout, 'w', format='NETCDF4_CLASSIC') as o:
        o.createDimension('lon', NC_); o.createDimension('lat', NR_)
        for n, val, ax in (('lon', LON0 + D * (np.arange(NC_) + 0.5), 'X'), ('lat', LAT0 + D * (np.arange(NR_) + 0.5), 'Y')):
            v = o.createVariable(n, 'f8', (n,)); v[:] = val
            v.standard_name = v.long_name = {'lon': 'longitude', 'lat': 'latitude'}[n]
            v.units = {'lon': 'degrees_east', 'lat': 'degrees_north'}[n]; v.axis = ax
        for short, (scc, vn, x, at, extra) in data.items():
            tot = x * AREA * SEC / 1000.0                               # t/yr (365 d)
            rem = np.where(KMASK, tot, 0.0)
            y = x.copy(); y[KMASK] = 0.0
            v = o.createVariable(short, 'f4', ('lat', 'lon')); v[:] = y.astype(np.float32)
            v.long_name = at['long_name']; v.description = at['description']
            v.units = 'kg m-2 s-1'; v.htap_variable = vn
            LST[scc].append(f'{scc},{ip},{short},0,{a.final.rstrip("/")}/{CASE}/inputs/htap/{os.path.basename(fout)}')
            row = {'pollutant': ip, 'scc': scc, 'variable': vn, 'window_t': tot.sum(), 'removed_t': rem.sum(),
                   'kept_t': tot.sum() - rem.sum(),
                   'kept_in_GEOCODE_197000_t': np.where((GEO == 197000) & ~KMASK, tot, 0).sum(),
                   'carbon_adjust_t': extra}
            for cd in codes: row[f'removed_GEOCODE_{cd}_t'] = np.where(GEO == cd, rem, 0.0).sum()
            SUMMARY.append(row)
        o.description = (f'HTAP_v3.2 {a.year} annual flux, window {LON0}-{LON1}E {LAT0}-{LAT1}N, '
                         f'South Korea (CAPSS 2023 coverage) set to 0{note}')
        o.source = src
        o.history = f'{TAG} make_busan_htap_v32_inputs.py'
    s = [r for r in SUMMARY if r['pollutant'] == ip]
    log(f'{ip}: {len(s)} sectors, window {sum(r["window_t"] for r in s):,.0f} t/yr, removed (Korea) '
        f'{sum(r["removed_t"] for r in s):,.0f} t/yr -> {fout}')

for hp, ip in POLS.items():
    data, src = (PM25, PM25SRC) if hp == 'PM2.5' else read_window(hp)
    note = ''
    if hp in ('PM2.5', 'PM10'):
        note = '; BC and OC subtracted (carbon enters as PEC/POC)'
        for short, (scc, vn, x, at) in list(data.items()):
            c = np.zeros_like(x)
            for k in ('BC', 'OC'):
                if short in CARBON[k]: c += CARBON[k][short][2]
            y = x - c
            clip = np.where(y < 0, -y, 0.0) * AREA * SEC / 1000.0
            data[short] = (scc, vn, np.maximum(y, 0.0), at, clip.sum())
    else:
        data = {k: v + (0.0,) for k, v in data.items()}
    write_pol(ip, data, src, note)
for hp, ip in (('BC', 'PEC'), ('OC', 'POC')):
    write_pol(ip, {k: v + (CLOSS[(hp, k)],) for k, v in CARBON[hp].items()}, f'edgar_HTAPv32_{a.year}_{hp}.zip',
              f'; HTAP {hp} as {ip} (scaled down where BC+OC > PM2.5)')
shutil.rmtree(tmp, ignore_errors=True)

# list files
hdr = ['#LIST GRID', '#SCC,InvPollName,HTAP_VarName,Month,FileName']
for g, sccs in GROUPS.items():
    lines = [l for s_ in sccs for l in LST.get(s_, [])]
    if lines: open(mk(f'{odir}/arinv.HTAPv32.{g}.lst'), 'w').write('\n'.join(hdr + lines) + '\n')
open(mk(f'{odir}/arinv.HTAPv32.ALL.lst'), 'w').write(
    '\n'.join(hdr + [l for g in GROUPS for s_ in GROUPS[g] for l in LST.get(s_, [])]) + '\n')
log('list files:', ', '.join(f'{g}={sum(len(LST.get(s_, [])) for s_ in GROUPS[g])}' for g in GROUPS))

# =====================================================================================
# 4. Profiles (example copies + rows for detailed sectors)
# =====================================================================================
pdir = f'{OUT}/ge_dat/EDGAR/HTAPv32_profiles'
for k in ('gspro', 'gscnv', 'hourly', 'weekly', 'monthly'):
    shutil.copy(PROF[k], mk(f'{pdir}/{os.path.basename(PROF[k])}'))
used = sorted(LST)
def extend(path, key_of, make, outname, label, more=()):
    lines = open(path, encoding='latin-1').read().splitlines()
    have = {key_of(l) for l in lines if l and not l.startswith('#')}
    add = []
    for s_ in used:
        if s_ in have: continue
        p = PARENT.get(s_)
        par = [l for l in lines if l and not l.startswith('#') and key_of(l) == p]
        if not par: raise SystemExit(f'ERROR: no {label} rows for {s_} (parent {p})')
        add += [make(l, s_) for l in par]
    out = lines + [f'# {TAG} Busan HTAP_v3.2: detailed sectors mapped to parent entries ({label})'] + add
    more = [m for m in more if m not in lines]
    if more: out += [f'# {TAG} Busan HTAP_v3.2: PEC/POC from the HTAP BC/OC inventories -> profile 0 (PEC->PEC, POC->POC)'] + more
    open(mk(f'{pdir}/{outname}'), 'w').write('\n'.join(out) + '\n')
    log(f'{label}: {len(add)} rows added -> {outname}')
extend(PROF['gsref'], lambda l: l.split(';')[0].strip('"'), lambda l, s_: s_ + l[l.index(';'):],
       f'gsref_HTAPv32_busan_{TAG}.txt', 'GSREF',
       more=['0000000000;"0";"PEC";;;;;;;', '0000000000;"0";"POC";;;;;;;'])
gsp = open(PROF['gspro'], encoding='latin-1').read()
for sp in ('PEC', 'POC'):
    if f'0;"{sp}";"{sp}";' not in gsp: raise SystemExit(f'ERROR: profile 0 {sp}->{sp} not in {PROF["gspro"]}')

# INVTABLE for HTAP: domestic INVTABLE + PEC/POC lines copied unchanged from the example INVTABLE
exinv = sorted(glob.glob(os.path.join(a.example, 'ge_dat', 'invtable_*.txt')))
if not os.path.isfile(a.invtable): raise SystemExit(f'ERROR: domestic INVTABLE not found: {a.invtable}')
if not exinv: raise SystemExit('ERROR: example INVTABLE (ge_dat/invtable_*.txt) not found')
inv = open(a.invtable, encoding='latin-1').read().splitlines()
add = []
for sp in ('PEC', 'POC'):
    if any(l.split()[:1] == [sp] for l in inv if l and not l.startswith('#')): continue
    hit = [(f, i + 1, l) for f in exinv for i, l in enumerate(open(f, encoding='latin-1').read().splitlines())
           if l.split()[:2] == [sp, sp]]                  # plain line only (not mode-specific 'PEC EXH EXH__PEC')
    if not hit: raise SystemExit(f'ERROR: no plain "{sp} {sp}" line in example INVTABLE {exinv}')
    f, n, l = hit[0]
    if l.split()[2] != 'Y': raise SystemExit(f'ERROR: example INVTABLE {sp} line keep flag is not Y: {l}')
    log(f'INVTABLE {sp}: {os.path.basename(f)} line {n}: {l.rstrip()[:60]}')
    add.append((f, n, l))
hdr2 = [f'# {TAG} Busan HTAP_v3.2: copy of {os.path.basename(a.invtable)}'] + \
       [f'#   + {sp} line copied unchanged from {os.path.basename(f)} line {n}' for (f, n, l), sp in zip(add, ('PEC', 'POC'))]
ip_ = mk(f'{OUT}/ge_dat/invtable_busan_htap_{TAG}.txt')
cm = [l for l in inv if l.startswith('#')]; body = [l for l in inv if not l.startswith('#')]
open(ip_, 'w').write('\n'.join(cm + hdr2 + body + [l for _, _, l in add]) + '\n')
log(f'INVTABLE for HTAP: {len(add)} lines added -> {ip_}')
extend(PROF['tref'], lambda l: l.split(',')[0].strip('"'), lambda l, s_: f'"{s_}"' + l[l.index(','):],
       f'tref_HTAPv32_busan_{TAG}.txt', 'TREF')

# summary
df = pd.DataFrame(SUMMARY)
df.to_csv(mk(f'{odir}/htap_summary_{TAG}.csv'), index=False, float_format='%.3f')
t = df.groupby('pollutant')[['window_t', 'removed_t', 'kept_in_GEOCODE_197000_t', 'carbon_adjust_t']].sum()
rc = df.groupby('pollutant')[[c for c in df.columns if c.startswith('removed_GEOCODE_')]].sum()
print('\n=== pollutant totals in window (t/yr, 365 d) ===')
print(t.round(0).to_string())
print('\n=== removed by GEOCODE (share of removed, %) ===')
print((rc.div(rc.sum(axis=1), axis=0) * 100).round(1).rename(columns=lambda c: c.replace('removed_GEOCODE_', '').replace('_t', '')).to_string())
log('done')
