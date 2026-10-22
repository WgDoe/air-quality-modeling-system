#!/usr/bin/env python3
"""
Busan SMOKE case (2017capss_cb6) step-4 inputs generator.
  (a) FF10_NONPOINT inventories from legacy IDA area files
  (b) SMOKE 5.x temporal profiles (monthly/weekly/hourly CSV) and TREF CSV from legacy SMOKE 2.7 files

Inputs (legacy SMOKE 2.7, 2020 version) in --legacy:
  1_Area_Inventory_File.txt, 1_Area_Inventory_File_sea.txt, 1_New_Asia_Area_Inventory_File.txt,
  7_Area_Temporal_Profile.txt,
  4_Area_Temporal_Reference_Profile.txt, 4_Point_Temporal_Reference_Profile.txt,
  4_New_ASIA_Area_Temporal_Reference_Profile.txt,
  2_Surrogate_Description_<27KM|09KM|03KM|01KM>_2017_2020update.txt.div,
  2_ASIA_Surrogate_Description_<27KM|09KM>_meicreas.txt.div.div,
  4_Area_Gridding_Surrogate_file.txt, 4_New_ASIA_Area_Gridding_Surrogate_file.txt,
  5_Area/5_Point/5_Asia_Area_Speciation_Reference_Profile.txt,
  10_Area/10_Point/10_New_ASIA_Area_SCC_Description.txt
  (file names with '.' or '_' before txt/div are both accepted)
Output: EMIS layout under --out
  (c) gridding: srgdesc_kor_<grid>, srgdesc_asia_<grid>, agref_kor_area, agref_asia (legacy, unchanged + header)
  (d) speciation: gsref_kor_area / gsref_kor_point / gsref_asia (legacy refs, CSV; TOG->VOC; defaults incl. PMC 99999)
  (e) smkreport: sccdesc_busan
"""
import argparse, os, glob, collections

p = argparse.ArgumentParser()
p.add_argument('--legacy', required=True)
p.add_argument('--out', required=True)
a = p.parse_args()
TAG = '20261021'
POL_IDA = ['SO2', 'NOX', 'CO', 'PM10', 'VOC', 'NH3', 'PM2_5']   # #POLID order of 2020 area files
DESC = ('"country_cd","region_cd","tribal_code","census_tract_cd","shape_id","scc","emis_type","poll",'
        '"ann_value","ann_pct_red","control_ids","control_measures","current_cost","cumulative_cost",'
        '"projection_factor","reg_codes","calc_method","calc_year","date_updated","data_set_id",'
        '"jan_value","feb_value","mar_value","apr_value","may_value","jun_value","jul_value","aug_value",'
        '"sep_value","oct_value","nov_value","dec_value","jan_pctred","feb_pctred","mar_pctred","apr_pctred",'
        '"may_pctred","jun_pctred","jul_pctred","aug_pctred","sep_pctred","oct_pctred","nov_pctred","dec_pctred",'
        '"comment","comments"')

def mk(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path

def ida_area_to_ff10(src, dst, year, label, keep=None):
    """IDA area: FIPS(1-5) SCC(6-15) then 7 x 47-char blocks; first 10 chars = annual ton/yr."""
    hdr = ['#FORMAT=FF10_NONPOINT', '#COUNTRY=ASIA', f'#YEAR={year}',
           f'#INVENTORY_LABEL={label}', '#VALUE_UNITS=TON',
           f'#SOURCE_FILE={os.path.basename(src)} (legacy SMOKE 2.7 IDA, 2020 version)',
           f'#CREATED={TAG} by make_busan_step4_inputs.py', '#DESC ' + DESC]
    rows, tot = [], {p: 0.0 for p in POL_IDA}
    for l in open(src):
        if l.startswith('#') or not l.strip():
            continue
        l = l.rstrip('\n')
        fips, scc = l[0:5], l[5:15]
        if keep and not keep(fips):
            continue
        for i, pol in enumerate(POL_IDA):
            s = l[15 + 47 * i: 25 + 47 * i].strip()
            v = float(s) if s else 0.0
            if v <= 0:
                continue
            tot[pol] += v
            rows.append(f'"ASIA","{fips}",,,,"{scc}",,"{pol}",{v:.6g}' + ',' * 37)
    open(mk(dst), 'w').write('\n'.join(hdr + rows) + '\n')
    return len(rows), tot

base = f'{a.out}/EMIS/2017capss_cb6/inputs'
n, t = ida_area_to_ff10(f'{a.legacy}/1_Area_Inventory_File.txt',
                        f'{base}/kor_area/kor_area_CAPSS2017_ff10_{TAG}.csv', 2017, 'CAPSS2017_area_2020version')
print('kor_area rows', n, {k: round(v) for k, v in t.items()})
# Sea (coastal shipping, region 11352): same area sector as legacy arinv.stationary.lst
n, t = ida_area_to_ff10(f'{a.legacy}/1_Area_Inventory_File_sea.txt',
                        f'{base}/kor_area/kor_sea_CAPSS2017_ff10_{TAG}.csv', 2017, 'CAPSS2017_sea_2020version')
print('kor_sea rows', n, {k: round(v) for k, v in t.items()})
# Asia: exclude separate North Korea file; Asia file already contains North Korea (11002)
n, t = ida_area_to_ff10(f'{a.legacy}/1_New_Asia_Area_Inventory_File.txt',
                        f'{base}/asia/asia_2010_ff10_{TAG}.csv', 2010, 'EastAsia2010_2016update')
print('asia rows', n, {k: round(v) for k, v in t.items()})

# ---- temporal profiles
sec, prof = None, {}
for l in open(f'{a.legacy}/7_Area_Temporal_Profile.txt'):
    s = l.strip()
    if s.startswith('/'):
        sec = s.strip('/').strip()
        if sec != 'END':
            prof.setdefault(sec, {})
        continue
    t_ = s.split()
    if t_ and sec and sec != 'END':
        prof[sec][t_[0]] = [float(x) for x in t_[1:]]
wd, we = prof['DIURANAL WEEKDAY'], prof['DIURANAL WEEKEND']
assert all(wd[k] == we[k] for k in wd), 'weekday/weekend diurnal differ: ALLDAY cannot be used'

def write_pro(name, d, n, header=None):
    out = [] if header is None else [header]
    for k in sorted(d, key=int):
        v = d[k][:n]
        s = sum(v)
        fr = [x / s if s > 0 else 0.0 for x in v]
        out.append(f'"{k}",' + ','.join(f'{x:.6g}' for x in fr) + ',""')
    open(mk(f'{a.out}/EMIS/ge_dat/temporal/{name}'), 'w').write('\n'.join(out) + '\n')

write_pro(f'tpro_monthly_busan_2020ver_{TAG}.csv', prof['MONTHLY'], 12)
write_pro(f'tpro_weekly_busan_2020ver_{TAG}.csv', prof['WEEKLY'], 7)
write_pro(f'tpro_hourly_busan_2020ver_UTC_{TAG}.csv', wd, 24,
          'profile_id,' + ','.join(f'hour{i}' for i in range(1, 25)) + ',comment')

def write_tref(src, dst):
    out = ['# TREF converted from legacy ' + os.path.basename(src) + ' (SCC;monthly;weekly;diurnal;0;FIPS)',
           '# diurnal: weekday and weekend profiles are identical in legacy -> ALLDAY',
           '# hourly profiles are UTC-shifted (legacy); keep COSTCY time zone GMT']
    n = 0
    for l in open(src):
        l = l.strip()
        if not l or l.startswith('/') or l.startswith('#'):
            continue
        f = l.split(';')
        scc, mon, wk, diu = f[0], f[1], f[2], f[3]
        for typ, pid in (('MONTHLY', mon), ('WEEKLY', wk), ('ALLDAY', diu)):
            out.append(f'"{scc}",,,,,,,"{typ}","{pid}",""')
        n += 1
    open(mk(f'{a.out}/EMIS/ge_dat/temporal/{dst}'), 'w').write('\n'.join(out) + '\n')
    return n

print('tref area', write_tref(f'{a.legacy}/4_Area_Temporal_Reference_Profile.txt', f'tref_kor_area_2020ver_{TAG}.csv'))
print('tref point', write_tref(f'{a.legacy}/4_Point_Temporal_Reference_Profile.txt', f'tref_kor_point_2020ver_{TAG}.csv'))
print('tref asia', write_tref(f'{a.legacy}/4_New_ASIA_Area_Temporal_Reference_Profile.txt', f'tref_asia_2020ver_{TAG}.csv'))


# ---- helpers for legacy names written as x.txt.div or x_txt.div
def lg(name):
    cands = [name, name.replace('.txt.div.div', '_txt_div.div').replace('.txt.div', '_txt.div')]
    for c in cands:
        f = os.path.join(a.legacy, c)
        if os.path.exists(f):
            return f
    raise FileNotFoundError(name)

def rd(f):
    return open(f, encoding='latin-1').read().replace('\r', '')

G = f'{a.out}/EMIS/ge_dat/gridding'
# (c) gridding
for g in ['27KM', '09KM', '03KM', '01KM']:
    src = lg(f'2_Surrogate_Description_{g}_2017_2020update.txt.div')
    h = [f'# SRGDESC Busan domestic {g}: legacy 2_Surrogate_Description_{g}_2017_2020update.txt.div (2020 version), copied unchanged',
         f'# Surrogate files: ge_dat/gridding/surrogates/2017_CAPSS_{g}_2020/']
    if g in ('03KM', '01KM'):
        h.append('# NOTE: sea codes 606-612 point to pieces .06-.12 that have no sea (111352) values; to be replaced by *_sea_from09KM.txt (pending)')
    open(mk(f'{G}/srgdesc_kor_{g}_2017_2020update.txt'), 'w').write('\n'.join(h) + '\n' + rd(src))
for g in ['27KM', '09KM']:
    src = lg(f'2_ASIA_Surrogate_Description_{g}_meicreas.txt.div.div')
    h = [f'# SRGDESC East Asia {g}: legacy 2_ASIA_Surrogate_Description_{g}_meicreas.txt.div.div, copied unchanged',
         f'# Surrogate files: ge_dat/gridding/surrogates/2010_ASIA_{g}_2016/']
    open(mk(f'{G}/srgdesc_asia_{g}_2016update.txt'), 'w').write('\n'.join(h) + '\n' + rd(src))
open(mk(f'{G}/agref_kor_area_2017capss_2020ver.txt'), 'w').write(
    '# AGREF Busan domestic area+sea: legacy 4_Area_Gridding_Surrogate_file.txt (2020 version), copied unchanged (region SCC surrogate)\n'
    + rd(lg('4_Area_Gridding_Surrogate_file.txt')))
open(mk(f'{G}/agref_asia_2016.txt'), 'w').write(
    '# AGREF East Asia: legacy 4_New_ASIA_Area_Gridding_Surrogate_file.txt, copied unchanged\n'
    + rd(lg('4_New_ASIA_Area_Gridding_Surrogate_file.txt')))

# (d) speciation cross-references
def refs(fn):
    r = []
    for l in open(lg(fn)):
        if ';' in l:
            sc, pr, pol = l.strip().split(';')
            if pol in ('TOG', 'NONHAPTOG'):
                pol = 'VOC'
            r.append((sc, pr, pol))
    return r

def write_gsref(name, rr, src, pmdef='91117'):
    hdr = [f'# GSREF Busan 2017capss_cb6: converted from legacy {src} (2020 version)',
           '# Format as example gsref_*_2022platform: "SCC","profile","pollutant",...',
           '# VOC profiles: SPECIATE numbers used with example gspro_CB6R3_AE7_criteria + gscnv_SPECIATE_5_3 (by profile)',
           '# PM2_5 profiles: example gspro_PM2_5_AE6; NOX -> HONO profile (NO 0.9 / NO2 0.092 / HONO 0.008, same split as legacy)',
           '# Defaults (SCC 0000000000): CO, NH3, SO2 -> 0000; PMC -> 99999 (example gspro_static: 99999;"PMC";"PMC"); NOX -> HONO; VOC -> 0000; PM2_5 -> ' + pmdef]
    d = [f'"0000000000","{pr}","{pol}",,,,,,,,,,,' for pr, pol in
         [('0000', 'CO'), ('0000', 'NH3'), ('0000', 'SO2'), ('99999', 'PMC'), ('HONO', 'NOX'), ('0000', 'VOC'), (pmdef, 'PM2_5')]]
    body = [f'"{sc}","{pr}","{pol}",,,,,,,,,,,' for sc, pr, pol in rr]
    open(mk(f'{a.out}/EMIS/ge_dat/speciation/{name}'), 'w').write('\n'.join(hdr + d + body) + '\n')
    print(name, dict(collections.Counter(p for _, _, p in rr)))

write_gsref('gsref_kor_area_2017capss_2020ver.csv', refs('5_Area_Speciation_Reference_Profile.txt'), '5_Area_Speciation_Reference_Profile.txt')
write_gsref('gsref_kor_point_2017capss_2020ver.csv', refs('5_Point_Speciation_Reference_Profile.txt'), '5_Point_Speciation_Reference_Profile.txt')
write_gsref('gsref_asia_2016.csv', refs('5_Asia_Area_Speciation_Reference_Profile.txt'), '5_Asia_Area_Speciation_Reference_Profile.txt (TOG renamed to VOC)')

# (e) SCC description (codes only)
S = set()
for fn in ['10_Area_SCC_Description.txt', '10_Point_SCC_Description.txt', '10_New_ASIA_Area_SCC_Description.txt']:
    for l in open(lg(fn)):
        l = l.strip()
        if l and not l.startswith('#'):
            S.add(l)
for l in open(lg('1_Area_Inventory_File_sea.txt')):
    if l[0] != '#':
        S.add(l[5:15])
open(mk(f'{a.out}/EMIS/ge_dat/smkreport/sccdesc_busan_2017capss_{TAG}.txt'), 'w').write(
    '# SCC list from legacy 10_*_SCC_Description.txt (codes only; legacy had no names) + sea SCCs\n'
    + '\n'.join(f'"{x}","{x}"' for x in sorted(S)) + '\n')
print('sccdesc', len(S))
