#!/usr/bin/env python3
"""
Busan SMOKE case 2023capss_cb6: all domestic (CAPSS 2023) inputs in one run.

Sectors
  kor_point  : CAPSS 2023 point (stack records)           -> FF10_POINT
  kor_area   : CAPSS 2023 area      (national a-file)     -> FF10_NONPOINT + surrogates
  kor_mobile : CAPSS 2023 mobile    (national m-file)     -> FF10_NONPOINT + surrogates  (road 07, non-road 08, road dust 12)
  kor_sea    : CAPSS 2023 sea       (sea m-file, 90100)   -> FF10_NONPOINT + surrogates

Decisions: docs/smoke/SMOKE_Emission_Improvement_Plan.md (2026-10-22)
  * units kg/yr -> short ton/yr (/907.18474); FF10 control efficiency written as 0
  * SCC10 = SCC 8 + legacy 2-digit fuel number (2017 fuel list position without 'xx00' rows; 20500->44, 999xx->99);
    fuels absent in 2017 list: 23101 G1, 50101 G2, 50102 G3, 50103 G4, 50201 G5, 50202 G6 (borrow 82),
    80201 S1, 80202 S2 (borrow 07), 41300 C1 (CNG, borrow 82)
  * reference fill: 1 exact -> 2 borrowed fuel -> 3 same SCC8 & same fuel class (first 3 digits of 5-digit fuel,
    nearest number) -> 4 same SCC8 other fuel (82, 99, 80, 33) -> 5 same SCC6 -> 6 SMOKE default
    point uses legacy point references, area/mobile/sea use legacy area references
  * stack fill: 0 same stack -> 1 SCC+fuel median -> 2 SCC median -> 3 all median
  * region code = ADMIN_CD first 5 digits; SMOKE internal '1' + 5 digits; COSTCY time zone GMT
  * surrogates: per (region, SCC10) share of the 1 km CAPSS cells, weight = SCC10's dominant pollutant (national mass);
    each 1 km cell split into 10x10 points for overlap with model cells; fractions relative to the region total
    (emissions of the region outside a domain are dropped). Default surrogate per sector = all-pollutant mass.

Usage
  python3 make_busan_2023_domestic_inputs.py --capss <dir with point/area/mobile/sea files> --code2017 <xlsx> \
      --code2023 <xlsx> --legacy <dir with legacy 4_*/5_*/9_* reference files> --out <dir>
  file names expected in --capss (change with options): point.txt, area.txt, mobile.txt, sea.txt
"""
import argparse, os, collections, time
import numpy as np, pandas as pd
from pyproj import CRS, Transformer

ap = argparse.ArgumentParser()
for k in ('capss', 'code2017', 'code2023', 'legacy', 'out'):
    ap.add_argument('--' + k, required=True)
ap.add_argument('--point', default='point.txt'); ap.add_argument('--area', default='area.txt')
ap.add_argument('--mobile', default='mobile.txt'); ap.add_argument('--sea', default='sea.txt')
ap.add_argument('--sub', type=int, default=10, help='sub-points per km for surrogate overlap')
a = ap.parse_args()
TAG, CASE = '20261022', '2023capss_cb6'
OUT = a.out.rstrip('/') + '/EMIS'
T0 = time.time()
def log(*x): print(f'[{time.time()-T0:6.0f}s]', *x, flush=True)
def mk(p): os.makedirs(os.path.dirname(p), exist_ok=True); return p

POL = {'CO': 'CO', 'NOx': 'NOX', 'SOx': 'SO2', 'PM10r': 'PM10', 'PM25r': 'PM2_5', 'VOC': 'VOC', 'NH3': 'NH3'}
PCOL = list(POL)
def fixcols(cols): return [c.strip().replace('NOX', 'NOx').replace('SOX', 'SOx').replace('PM-10', 'PM10r')
                           .replace('PM-2.5', 'PM25r') for c in cols]

# ---------------- fuel numbers and reference rules
f17 = pd.read_excel(a.code2017, sheet_name='fuel_cd', dtype=str)
seq = [c for c in f17['연료코드'] if not c.endswith('00')]
POS = {c: i + 1 for i, c in enumerate(seq)}
INV = {f'{i+1:02d}': c for i, c in enumerate(seq) if i + 1 < 99}; INV['44'] = '20500'; INV['99'] = '99999'
NEW = {'23101': ('G1', '82'), '50101': ('G2', '82'), '50102': ('G3', '82'), '50103': ('G4', '82'),
       '50201': ('G5', '82'), '50202': ('G6', '82'), '80201': ('S1', '07'), '80202': ('S2', '07'), '41300': ('C1', '82')}
def fuel2(c):
    if c in NEW: return NEW[c][0]
    if c.startswith('999'): return '99'
    if c == '20500': return '44'
    p = POS.get(c)
    if p and p < 99: return f'{p:02d}'
    raise ValueError(f'no 2-digit fuel number for {c}')
def borrow(c): return NEW[c][1] if c in NEW else fuel2(c)
def fclass(c2): c = INV.get(c2); return c[:3] if c else None

def read_ref(fn):
    r = collections.defaultdict(list)
    for l in open(os.path.join(a.legacy, fn), encoding='latin-1'):
        if ';' in l and not l.startswith('/'):
            f = l.strip().split(';'); r[f[0]].append(f)
    return r

def source(scc8, fuel, R, by8):
    s10 = scc8 + fuel2(fuel)
    if s10 in R: return '1 exact', s10
    b = scc8 + borrow(fuel)
    if b in R: return '2 borrow fuel', b
    c8 = sorted(by8.get(scc8, []))
    if c8:
        cls = (INV[NEW[fuel][1]] if fuel in NEW else fuel)[:3]
        same = [x for x in c8 if fclass(x[8:]) == cls]
        if same:
            tgt = int(borrow(fuel)) if borrow(fuel).isdigit() else 0
            same.sort(key=lambda x: (abs(int(x[8:]) - tgt) if x[8:].isdigit() else 99, x))
            return '3 same fuel class', same[0]
        for p in ('82', '99', '80', '33'):
            if scc8 + p in R: return '4 same SCC8', scc8 + p
        return '4 same SCC8', c8[0]
    c6 = sorted(x for x in R if x[:6] == scc8[:6])
    if c6:
        for p in (borrow(fuel), '82', '99'):
            hit = [x for x in c6 if x[8:] == p]
            if hit: return '5 same SCC6', hit[0]
        return '5 same SCC6', c6[0]
    return '6 default', ''

TR = {'point': read_ref('4_Point_Temporal_Reference_Profile.txt'), 'area': read_ref('4_Area_Temporal_Reference_Profile.txt')}
SR = {'point': read_ref('5_Point_Speciation_Reference_Profile.txt'), 'area': read_ref('5_Area_Speciation_Reference_Profile.txt')}
BY8 = {}
for k in ('point', 'area'):
    for kind, R in (('T', TR[k]), ('S', SR[k])):
        d = collections.defaultdict(list)
        for x in R: d[x[:8]].append(x)
        BY8[(k, kind)] = d

def build_refs(combos, refset, label):
    """combos: DataFrame SCC_CD, FUEL_CD, (NOx, VOC ...) ; returns map rows, tref lines, gsref lines"""
    rows, tref, gsref = [], [], []
    for r in combos.itertuples(index=False):
        s10 = r.SCC_CD + fuel2(r.FUEL_CD)
        rt, st = source(r.SCC_CD, r.FUEL_CD, TR[refset], BY8[(refset, 'T')])
        rs, ss = source(r.SCC_CD, r.FUEL_CD, SR[refset], BY8[(refset, 'S')])
        rows.append(dict(sector=label, SCC10=s10, SCC=r.SCC_CD, FUEL=r.FUEL_CD, rule_temporal=rt, src_temporal=st,
                         rule_speciation=rs, src_speciation=ss, NOx_t=round(r.NOx / 1000, 2), VOC_t=round(r.VOC / 1000, 2),
                         PM25_t=round(r.PM25r / 1000, 2)))
        for f in TR[refset].get(st, []):
            tref += [f'"{s10}",,,,,,,"MONTHLY","{f[1]}",""', f'"{s10}",,,,,,,"WEEKLY","{f[2]}",""', f'"{s10}",,,,,,,"ALLDAY","{f[3]}",""']
        for f in SR[refset].get(ss, []):
            pol = 'VOC' if f[2] in ('VOC', 'TOG', 'NONHAPTOG') else f[2]
            gsref.append(f'"{s10}","{f[1]}","{pol}",,,,,,,,,,,')
    return rows, tref, gsref

GSDEF = [f'"0000000000","{p}","{q}",,,,,,,,,,,' for p, q in
         [('0000', 'CO'), ('0000', 'NH3'), ('0000', 'SO2'), ('99999', 'PMC'), ('HONO', 'NOX'), ('0000', 'VOC'), ('91117', 'PM2_5')]]

# ---------------- coordinates
TMCRS = CRS.from_proj4('+proj=tmerc +lat_0=38 +lon_0=127.002890277778 +k=1 +x_0=200000 +y_0=500000 +ellps=bessel '
                       '+towgs84=-115.80,474.99,674.11,1.16,-2.31,-1.63,6.43 +units=m +no_defs')
T_LL = Transformer.from_crs(TMCRS, CRS.from_epsg(4326), always_xy=True)
LCC = CRS.from_proj4('+proj=lcc +lat_1=30 +lat_2=60 +lat_0=38 +lon_0=126 +a=6370000 +b=6370000 +units=m +no_defs')
T_LCC = Transformer.from_crs(CRS.from_proj4('+proj=longlat +a=6370000 +b=6370000 +no_defs'), LCC, always_xy=True)
GRIDS = {'27KM': (-2349000., -1728000., 27000., 174, 128), '09KM': (-180000., -585000., 9000., 67, 82),
         '03KM': (105000., -408000., 3000., 83, 83), '01KM': (231000., -332000., 1000., 78, 70)}

# =====================================================================================
# 1. POINT
# =====================================================================================
log('point: reading')
d = pd.read_csv(os.path.join(a.capss, a.point), dtype={'ADMIN_CD': str, 'POINT_ID': str, 'SCC_CD': str, 'FUEL_CD': str})
d.columns = fixcols(d.columns)
nraw = len(d)
key = ['ADMIN_CD', 'POINT_ID', 'SCC_CD', 'FUEL_CD']
stk = ['TM_X', 'TM_Y', 'ALTITUDE', 'STACK_HEIGHT', 'STACK_DIAMETER', 'GAS_TEMPER', 'GAS_SPEED']
agg = {p: 'sum' for p in PCOL}; agg.update({s: 'first' for s in stk})
d = d.groupby(key, as_index=False, sort=False).agg(agg)
log(f'point: {nraw} rows -> {len(d)} after merging duplicates')
fill_log = []
S = ['STACK_HEIGHT', 'STACK_DIAMETER', 'GAS_TEMPER', 'GAS_SPEED']
for c in S: d.loc[d[c] <= 0, c] = np.nan
for c in S:
    steps = [('0 same stack', d.groupby(['ADMIN_CD', 'POINT_ID'])[c].transform('first')),
             ('1 SCC+fuel median', d.groupby(['SCC_CD', 'FUEL_CD'])[c].transform('median')),
             ('2 SCC median', d.groupby(['SCC_CD'])[c].transform('median')),
             ('3 all median', pd.Series(d[c].median(), index=d.index))]
    for name, val in steps:
        m = d[c].isna() & val.notna()
        for i in d.index[m]:
            fill_log.append(dict(ADMIN_CD=d.at[i, 'ADMIN_CD'], POINT_ID=d.at[i, 'POINT_ID'], SCC_CD=d.at[i, 'SCC_CD'],
                                 FUEL_CD=d.at[i, 'FUEL_CD'], item=c, rule=name, value=round(float(val[i]), 4)))
        d.loc[m, c] = val[m]
pd.DataFrame(fill_log).to_csv(mk(f'{OUT}/{CASE}/inputs/kor_point/stack_fill_log_{TAG}.csv'), index=False)
d['SCC10'] = d.SCC_CD + d.FUEL_CD.map(fuel2)
pc = d.groupby(['SCC_CD', 'FUEL_CD'], as_index=False)[PCOL].sum()
prow, ptref, pgsref = build_refs(pc, 'point', 'kor_point')
lon, lat = T_LL.transform(d.TM_X.values * 1000, d.TM_Y.values * 1000)
d['LON'], d['LAT'] = lon, lat
M2FT = 3.280839895
def g_(x, n=6): return f'{x:.{n}g}'
lines = ['#FORMAT=FF10_POINT', '#COUNTRY=ASIA', '#YEAR=2023', '#INVENTORY_LABEL=CAPSS2023_point', '#VALUE_UNITS=TON',
         f'#SOURCE=CAPSS 2023 1km point (kg/yr /907.18474), {TAG} make_busan_2023_domestic_inputs.py',
         '#DESC country_cd,region_cd,tribal_code,facility_id,unit_id,rel_point_id,process_id,agy_facility_id,agy_unit_id,'
         'agy_rel_point_id,agy_process_id,scc,poll,ann_value,ann_pct_red,facility_name,erptype,stkhgt,stkdiam,stktemp,stkflow,'
         'stkvel,naics,longitude,latitude,...']
ptot = collections.Counter()
for r in d.itertuples(index=False):
    plant, _, stack = r.POINT_ID.partition('_')
    hft, dft, tf, vft = r.STACK_HEIGHT * M2FT, r.STACK_DIAMETER * M2FT, r.GAS_TEMPER * 9 / 5 + 32, r.GAS_SPEED * M2FT
    flow = vft * np.pi * (dft / 2) ** 2
    for col, pol in POL.items():
        v = getattr(r, col)
        if not v > 0: continue
        t = v / 907.18474; ptot[pol] += t
        f = [''] * 78
        f[0], f[1], f[3], f[4], f[5], f[6] = '"ASIA"', f'"{r.ADMIN_CD[:5]}"', f'"{plant}"', f'"{r.POINT_ID}"', f'"{stack or 1}"', f'"{r.FUEL_CD}"'
        f[11], f[12], f[13], f[14], f[16] = f'"{r.SCC10}"', f'"{pol}"', g_(t, 8), '0', '2'
        f[17], f[18], f[19], f[20], f[21] = g_(hft), g_(dft), g_(tf), g_(flow), g_(vft)
        f[23], f[24] = f'{r.LON:.6f}', f'{r.LAT:.6f}'
        lines.append(','.join(f))
open(mk(f'{OUT}/{CASE}/inputs/kor_point/kor_point_CAPSS2023_ff10_{TAG}.csv'), 'w').write('\n'.join(lines) + '\n')
log('point FF10 lines', len(lines) - 7, {k: round(v) for k, v in ptot.items()})
SUMMARY = [('kor_point', 'FF10 lines', len(lines) - 7)] + [('kor_point', f'{k} short ton', round(v)) for k, v in ptot.items()]

# =====================================================================================
# 2. NONPOINT sectors: inventory + cell table
# =====================================================================================
FF10_DESC = ('#DESC "country_cd","region_cd","tribal_code","census_tract_cd","shape_id","scc","emis_type","poll","ann_value",'
             '"ann_pct_red","control_ids","control_measures","current_cost","cumulative_cost","projection_factor","reg_codes",'
             '"calc_method","calc_year","date_updated","data_set_id","jan_value","feb_value","mar_value","apr_value","may_value",'
             '"jun_value","jul_value","aug_value","sep_value","oct_value","nov_value","dec_value","jan_pctred","feb_pctred",'
             '"mar_pctred","apr_pctred","may_pctred","jun_pctred","jul_pctred","aug_pctred","sep_pctred","oct_pctred","nov_pctred",'
             '"dec_pctred","comment","comments"')
SECT = {'kor_area': a.area, 'kor_mobile': a.mobile, 'kor_sea': a.sea}
CODEBASE = {'kor_area': 1000, 'kor_mobile': 3000, 'kor_sea': 5000}
DEFCODE = {'kor_area': 900, 'kor_mobile': 901, 'kor_sea': 902}
allrows, nptref, npgsref, srgdesc_lines, agref_lines = [], [], [], {g: [] for g in GRIDS}, []
cellmaps = {}
for sec, fn in SECT.items():
    log(f'{sec}: reading {fn}')
    parts, cparts = [], []
    for ch in pd.read_csv(os.path.join(a.capss, fn), dtype=str, chunksize=1_500_000):
        ch.columns = fixcols(ch.columns)
        ch = ch[ch.INVEST_YEAR == '2023']
        for p in PCOL: ch[p] = pd.to_numeric(ch[p]).astype('float32')
        ch['X'] = pd.to_numeric(ch.TM_X).astype('int32'); ch['Y'] = pd.to_numeric(ch.TM_Y).astype('int32')
        ch['REG'] = ch.ADMIN_CD.str[:5]
        f2 = {f: fuel2(f) for f in ch.FUEL_CD.unique()}
        ch['SCC10'] = ch.SCC_CD + ch.FUEL_CD.map(f2)
        cparts.append(ch.groupby(['SCC_CD', 'FUEL_CD'], as_index=False)[PCOL].sum())
        ch = ch[['REG', 'SCC10', 'X', 'Y'] + PCOL]
        ch['REG'] = ch.REG.astype('category'); ch['SCC10'] = ch.SCC10.astype('category')
        parts.append(ch)
    c = pd.concat(parts, ignore_index=True); del parts
    for k in ('REG', 'SCC10'): c[k] = c[k].astype(str).astype('category')
    c = c.groupby(['REG', 'SCC10', 'X', 'Y'], as_index=False, observed=True)[PCOL].sum()
    for k in ('REG', 'SCC10'): c[k] = c[k].astype(str)
    combos = pd.concat(cparts).groupby(['SCC_CD', 'FUEL_CD'], as_index=False)[PCOL].sum()
    log(f'{sec}: {len(c)} region-SCC10-cell rows')
    # inventory (region x SCC10)
    inv = c.groupby(['REG', 'SCC10'], as_index=False)[PCOL].sum()
    lines = ['#FORMAT=FF10_NONPOINT', '#COUNTRY=ASIA', '#YEAR=2023', f'#INVENTORY_LABEL=CAPSS2023_{sec}', '#VALUE_UNITS=TON',
             f'#SOURCE=CAPSS 2023 1km {sec} (kg/yr /907.18474), {TAG} make_busan_2023_domestic_inputs.py', FF10_DESC]
    tot = collections.Counter()
    for r in inv.itertuples(index=False):
        for col, pol in POL.items():
            v = getattr(r, col)
            if not v > 0: continue
            t = v / 907.18474; tot[pol] += t
            lines.append(f'"ASIA","{r.REG}",,,,"{r.SCC10}",,"{pol}",{t:.8g},0' + ',' * 36)
    open(mk(f'{OUT}/{CASE}/inputs/{sec}/{sec}_CAPSS2023_ff10_{TAG}.csv'), 'w').write('\n'.join(lines) + '\n')
    log(f'{sec}: FF10 lines {len(lines)-7}', {k: round(v) for k, v in tot.items()})
    SUMMARY += [(sec, 'FF10 lines', len(lines) - 7)] + [(sec, f'{k} short ton', round(v)) for k, v in tot.items()]
    # references
    rows, tr, gs = build_refs(combos, 'area', sec)
    allrows += rows; nptref += tr; npgsref += gs
    # surrogate weights: dominant pollutant per SCC10
    nat = c.groupby('SCC10')[PCOL].sum()
    dom = nat.idxmax(axis=1)
    W = np.zeros(len(c), dtype='float32')
    for col in PCOL:
        m = c.SCC10.map(dom).values == col
        W[m] = c[col].values[m]
    c['W'] = W
    c['WALL'] = c[PCOL].sum(axis=1).astype('float32')
    codes = {s10: CODEBASE[sec] + i + 1 for i, s10 in enumerate(sorted(nat.index))}
    agref_lines += [f'000000 {s10} {codes[s10]}' for s10 in sorted(codes)]
    for g in GRIDS:
        srgdesc_lines[g] += [f'KOREA,{DEFCODE[sec]},{sec} all sources,srg_{sec}_2023capss_{g}.txt'] + \
                            [f'KOREA,{codes[s10]},{s10},srg_{sec}_2023capss_{g}.txt' for s10 in sorted(codes)]
    cellmaps[sec] = (c[['REG', 'SCC10', 'X', 'Y', 'W', 'WALL']].copy(), codes, dom)
    del c

pd.DataFrame(allrows + prow).to_csv(mk(f'{OUT}/{CASE}/inputs/scc10_reference_map_{TAG}.csv'), index=False)
hdr = ['# rules: 1 exact / 2 borrowed fuel / 3 same SCC8 same fuel class / 4 same SCC8 / 5 same SCC6 / 6 default; see inputs/scc10_reference_map',
       '# hourly profiles are UTC-shifted legacy profiles (COSTCY time zone GMT)']
open(mk(f'{OUT}/ge_dat/temporal/tref_kor_point_2023capss_{TAG}.csv'), 'w').write('\n'.join(['# TREF kor_point 2023 (legacy point references)'] + hdr + sorted(set(ptref))) + '\n')
open(mk(f'{OUT}/ge_dat/temporal/tref_kor_nonpoint_2023capss_{TAG}.csv'), 'w').write('\n'.join(['# TREF kor_area/kor_mobile/kor_sea 2023 (legacy area references)'] + hdr + sorted(set(nptref))) + '\n')
gh = ['# VOC: SPECIATE numbers with gspro_CB6R3_AE7_criteria + gscnv_SPECIATE_5_3; PM2_5: gspro_PM2_5_AE6; defaults below']
open(mk(f'{OUT}/ge_dat/speciation/gsref_kor_point_2023capss_{TAG}.csv'), 'w').write('\n'.join(['# GSREF kor_point 2023'] + hdr[:1] + gh + GSDEF + sorted(set(pgsref))) + '\n')
open(mk(f'{OUT}/ge_dat/speciation/gsref_kor_nonpoint_2023capss_{TAG}.csv'), 'w').write('\n'.join(['# GSREF kor_area/kor_mobile/kor_sea 2023'] + hdr[:1] + gh + GSDEF + sorted(set(npgsref))) + '\n')
open(mk(f'{OUT}/ge_dat/gridding/agref_kor_nonpoint_2023capss_{TAG}.txt'), 'w').write(
    '# AGREF kor_area/kor_mobile/kor_sea 2023: SCC10 -> surrogate code (area 1001-, mobile 3001-, sea 5001-; defaults 900/901/902)\n'
    + '\n'.join(agref_lines) + '\n')
for g, (x0, y0, dx, nc, nr) in GRIDS.items():
    open(mk(f'{OUT}/ge_dat/gridding/srgdesc_kor_2023capss_{g}_{TAG}.txt'), 'w').write(
        f'# SRGDESC kor_area/kor_mobile/kor_sea 2023 {g}: surrogates from CAPSS 2023 1km cells (files in ge_dat/gridding/surrogates/kor_2023capss_{g}/)\n'
        + '\n'.join(srgdesc_lines[g]) + '\n')
log('references written')

# =====================================================================================
# 3. SURROGATES (cell overlap with 10x10 sub-points)
# =====================================================================================
allcells = pd.concat([cm[0][['X', 'Y']] for cm in cellmaps.values()]).drop_duplicates().reset_index(drop=True)
allcells['CID'] = np.arange(len(allcells))
log('unique 1km cells', len(allcells))
NSUB = {'27KM': 2, '09KM': 3, '03KM': 5, '01KM': a.sub}
for sec in cellmaps:
    c, codes, dom = cellmaps[sec]
    c = c.merge(allcells, on=['X', 'Y']).drop(columns=['X', 'Y'])
    cellmaps[sec] = (c, codes, dom)
hdrline = {}
for g, (x0, y0, dx, nc, nr) in GRIDS.items():
    hdrline[g] = (f'#GRID {g} {x0:.8E} {y0:.8E} {dx:.8E} {dx:.8E} {nc} {nr} 1 LAMBERT METERS '
                  f'3.00000000E+01 6.00000000E+01 1.26000000E+02 1.26000000E+02 3.80000000E+01')
    n = NSUB[g]
    off = (np.arange(n) + 0.5) / n
    ox, oy = np.meshgrid(off, off); ox, oy = ox.ravel(), oy.ravel()
    # cell centres -> pre-select cells near the domain
    lo, la = T_LL.transform((allcells.X.values + 0.5) * 1000.0, (allcells.Y.values + 0.5) * 1000.0)
    cx, cy = T_LCC.transform(lo, la)
    near = (cx > x0 - 2000) & (cx < x0 + nc * dx + 2000) & (cy > y0 - 2000) & (cy < y0 + nr * dx + 2000)
    cells = allcells[near]
    X = ((cells.X.values[:, None] + ox[None, :]) * 1000.0).ravel()
    Y = ((cells.Y.values[:, None] + oy[None, :]) * 1000.0).ravel()
    lo, la = T_LL.transform(X, Y); px, py = T_LCC.transform(lo, la); del X, Y, lo, la
    cid = np.repeat(cells.CID.values, n * n)
    col = np.floor((px - x0) / dx).astype(np.int64) + 1
    row = np.floor((py - y0) / dx).astype(np.int64) + 1
    inside = (col >= 1) & (col <= nc) & (row >= 1) & (row <= nr)
    mp = pd.DataFrame({'CID': cid[inside], 'C': col[inside].astype('int16'), 'R': row[inside].astype('int16')})
    mp = mp.groupby(['CID', 'C', 'R']).size().rename('k').reset_index()
    mp['f'] = (mp.k / (n * n)).astype('float32')
    del px, py, cid, col, row, inside
    log(f'{g}: {mp.CID.nunique()} cells touch the domain, {len(mp)} cell-grid overlaps (sub-points {n}x{n})')
    for sec, (c, codes, dom) in cellmaps.items():
        regtot = c.groupby(['REG', 'SCC10']).W.sum().rename('WT')
        regall = c.groupby('REG').WALL.sum().rename('WAT')
        jn = c[c.CID.isin(mp.CID.values)].merge(mp[['CID', 'C', 'R', 'f']], on='CID')
        out = []
        if len(jn):
            jn['w'] = jn.W * jn.f; jn['wa'] = jn.WALL * jn.f
            sg_ = jn.groupby(['REG', 'SCC10', 'C', 'R']).w.sum().reset_index().join(regtot, on=['REG', 'SCC10'])
            sg_ = sg_[(sg_.w > 0) & (sg_.WT > 0)]
            sg_['frac'] = sg_.w / sg_.WT
            sg_['code'] = sg_.SCC10.map(codes)
            dflt = jn.groupby(['REG', 'C', 'R']).wa.sum().reset_index().join(regall, on='REG')
            dflt = dflt[(dflt.wa > 0) & (dflt.WAT > 0)]
            dflt['frac'] = dflt.wa / dflt.WAT
            out = [f'{DEFCODE[sec]:>5d} 1{r.REG} {r.C:>4d} {r.R:>4d} {r.frac:.8f}' for r in dflt.itertuples(index=False)]
            out += [f'{r.code:>5d} 1{r.REG} {r.C:>4d} {r.R:>4d} {r.frac:.8f}'
                    for r in sg_.sort_values(['code', 'REG', 'C', 'R']).itertuples(index=False)]
            del jn, sg_, dflt
        p = mk(f'{OUT}/ge_dat/gridding/surrogates/kor_2023capss_{g}/srg_{sec}_2023capss_{g}.txt')
        open(p, 'w').write(hdrline[g] + '\n' + '\n'.join(out) + ('\n' if out else ''))
        SUMMARY.append((sec, f'surrogate lines {g}', len(out)))
        log(f'{g} {sec}: surrogate lines {len(out)}')

# =====================================================================================
# 4. COSTCY, SCCDESC, summary
# =====================================================================================
sg = pd.read_excel(a.code2023, sheet_name='sigungu_cd', dtype=str).drop_duplicates('행정구역코드')
states = sorted(set(sg['행정구역코드'].str[:2]))
cty = [(c[:5], f"    {'KR'+c[:5]:<20} 1{c[:5]:>5}{'':8}GMTx") for c in sg['행정구역코드']]
for fn in ('9_Asia_TimeZone.txt', '9_Bio_TimeZone.txt'):
    for l in open(os.path.join(a.legacy, fn), encoding='latin-1'):
        if l.startswith('    '):
            nm, code = l[4:24].strip(), l[25:31]
            cty.append((code[1:], f"    {nm:<20} {code:>6}{'':8}GMTx"))
assert len({k for k, _ in cty}) == len(cty)
open(mk(f'{OUT}/ge_dat/costcy_busan_2023capss_{TAG}.txt'), 'w').write('\n'.join(
    ['# COSTCY 2023capss_cb6: CAPSS 2023 sigungu (ADMIN_CD first 5 digits, sea 90100) + legacy East Asia/biogenic codes; GMT',
     '# County cols: name 5-24, country 26, state 27-28, county 29-31, time zone 40-42 (SMOKE rdstcy.f)',
     '/COUNTRY/', '1 ASIA', '/STATE/'] + [f'1{s}   SIDO{s}' for s in states] + ['/COUNTY/'] + [s for _, s in sorted(cty)]) + '\n')
sc = pd.read_excel(a.code2023, sheet_name='scc_cd', dtype=str).fillna('')
nm = {r.SCC_CD: ' / '.join(x for x in [r.SCC_NAME1, r.SCC_NAME2, r.SCC_NAME3, r.SCC_NAME4] if x) for r in sc.itertuples()}
f23 = pd.read_excel(a.code2023, sheet_name='fuel_cd', dtype=str); fnm = dict(zip(f23['연료코드'], f23['연료명']))
desc = {f'"{r["SCC10"]}","{nm.get(r["SCC"], r["SCC"])} | {fnm.get(r["FUEL"], r["FUEL"])}"' for r in allrows + prow}
open(mk(f'{OUT}/ge_dat/smkreport/sccdesc_busan_2023capss_{TAG}.txt'), 'w', encoding='utf-8').write(
    '#DELIMITED\n# SCC description 2023capss_cb6 (CAPSS 2023 SCC name | fuel name); #DELIMITED header required by SMOKE rdsccdsc.f\n' + '\n'.join(sorted(desc)) + '\n')
pd.DataFrame(SUMMARY, columns=['sector', 'item', 'value']).to_csv(mk(f'{OUT}/{CASE}/inputs/generation_summary_{TAG}.csv'), index=False)
log('done')
