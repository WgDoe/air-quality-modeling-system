#!/usr/bin/env python3
"""
Busan SMOKE case (2017capss_cb6) common inputs generator.
Reproduces the step-3 files of docs/smoke/SMOKE_Busan_Case_Run_Guide.md.

Inputs (legacy SMOKE 2.7, 2020 version / MCIP / SMOKE example):
  --mcip    : MCIP folder containing 27KM/09KM/03KM/01KM/GRIDDESC_<grid>
  --legacy  : folder with 9_Area_TimeZone.txt, 9_Asia_TimeZone.txt, 9_Bio_TimeZone.txt, holidays_korea.txt
  --invtab  : example invtable_2022platform_integrate_15sep2025_nf_v3.txt
  --out     : output folder (EMIS layout is created under it)
"""
import argparse, datetime as dt, os, re

p = argparse.ArgumentParser()
p.add_argument('--mcip', required=True)
p.add_argument('--legacy', required=True)
p.add_argument('--invtab', required=True)
p.add_argument('--out', required=True)
a = p.parse_args()
TAG = '20261021'
GRIDS = ['27KM', '09KM', '03KM', '01KM']

def mk(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path

# 1) GRIDDESC: merge MCIP GRIDDESC_<grid> (values unchanged)
coord, grids = None, []
for g in GRIDS:
    lines = [l.rstrip('\n') for l in open(os.path.join(a.mcip, g, f'GRIDDESC_{g}'))]
    q = [l for l in lines if l.strip() != "' '"]
    if coord is None:
        coord = q[0:2]
    grids += q[2:4]
gd = ["' '"] + coord + ["' '"] + grids + ["' '"]
open(mk(f'{a.out}/EMIS/ge_dat/gridding/griddesc_busan_4domains.txt'), 'w').write('\n'.join(gd) + '\n')

# 2) COSTCY: legacy 9_*_TimeZone merged, SMOKE 5.3 rdstcy.f columns, GMT kept
rows = []
for fn in ['9_Asia_TimeZone.txt', '9_Bio_TimeZone.txt', '9_Area_TimeZone.txt']:
    for l in open(os.path.join(a.legacy, fn)):
        l = l.rstrip('\n')
        if not l.startswith('    '):
            continue
        name, code = l[4:24].strip(), l[25:31]
        s = f"    {name:<20} {code:>6}{'':8}GMTx"
        assert s[25:31] == code and s[39:42] == 'GMT'
        rows.append((code, s))
rows.sort()
assert len({c for c, _ in rows}) == len(rows)
hdr = ["# COSTCY for Busan SMOKE case (2017capss_cb6)",
       "# Source: legacy SMOKE2.7 9_Area_TimeZone.txt + 9_Asia_TimeZone.txt + 9_Bio_TimeZone.txt (2020 version)",
       "# Time zone GMT kept as legacy: legacy temporal hourly profiles are already shifted to UTC.",
       "# County cols: name 5-24, country 26, state 27-28, county 29-31, time zone 40-42 (SMOKE rdstcy.f)",
       "/COUNTRY/", "1 ASIA", "/STATE/", "111   KOREA_EASTASIA", "/COUNTY/"]
open(mk(f'{a.out}/EMIS/ge_dat/costcy_busan_2017capss_{TAG}.txt'), 'w').write('\n'.join(hdr + [r for _, r in rows]) + '\n')

# 3) Holidays: legacy up to 2020 (2021+ lines have month errors) + newly written 2026
leg = [l.rstrip('\n') for l in open(os.path.join(a.legacy, 'holidays_korea.txt'))
       if l.strip() and re.match(r'^\d{6}\s+\d\d\s+\d\d\s+(\d{4})', l) and int(l.split()[3]) <= 2020]
h26 = [(1,1,"New Year's Day"),(2,16,"Seollal Holiday"),(2,17,"Seollal"),(2,18,"Seollal Holiday"),
       (3,1,"Independence Movement Day"),(3,2,"Substitute Holiday (Independence Movement Day)"),
       (5,5,"Children's Day"),(5,24,"Buddha's Birthday"),(5,25,"Substitute Holiday (Buddha's Birthday)"),
       (6,3,"Local Election Day"),(6,6,"Memorial Day"),(8,15,"Liberation Day"),(8,17,"Substitute Holiday (Liberation Day)"),
       (9,24,"Chuseok Holiday"),(9,25,"Chuseok"),(9,26,"Chuseok Holiday"),(10,3,"National Foundation Day"),
       (10,5,"Substitute Holiday (National Foundation Day)"),(10,9,"Hangeul Proclamation Day"),(12,25,"Christmas Day")]
hl = ["# Korea holidays for SMOKE (all treated as Sunday)",
      "# 2012-2020: copied from legacy holidays_korea.txt (2020 version; its 2021-2030 lines had month errors and were dropped)",
      "# 2026: newly written 2026-10-21 - verify against official calendar before production use",
      "# 2021-2025: not included (not needed for TEST_20260901)"] + leg + \
     [f"000000 {m:02d} {d:02d} 2026 Sunday !{n}" for m, d, n in h26]
open(mk(f'{a.out}/EMIS/ge_dat/temporal/holidays_korea_2012_2026_{TAG}.txt'), 'w').write('\n'.join(hl) + '\n')
H = {dt.date(2026, m, d) for m, d, _ in h26}

# 4) Merge dates 2026 (example 2022 format; representative week = first full Mon-Sun week without holidays)
f8 = lambda x: x.strftime('%Y%m%d')
for mon in range(1, 13):
    d0 = dt.date(2026, mon, 1)
    days = [d0 + dt.timedelta(i) for i in range(31) if (d0 + dt.timedelta(i)).month == mon]
    rep = next(d for d in days if d.weekday() == 0 and (d + dt.timedelta(6)).month == mon
               and not any(d + dt.timedelta(k) in H for k in range(7)))
    R = {w: rep + dt.timedelta(w) for w in range(7)}
    out = ["    Date, aveday_N, aveday_Y,  mwdss_N,  mwdss_Y,   week_N,   week_Y,      all"]
    for d in days:
        w, hol = d.weekday(), d in H
        av = R[1]; mw = R[0] if w == 0 else R[5] if w == 5 else R[6] if w == 6 else R[1]; wk = R[w]
        Y = (lambda x: d) if hol else (lambda x: x)
        out.append(', '.join(f8(x) for x in [d, av, Y(av), mw, Y(mw), wk, Y(wk), d]))
    open(mk(f'{a.out}/EMIS/smoke5.2/scripts/smk_dates/2026/smk_merge_dates_2026{mon:02d}.txt'), 'w').write('\n'.join(out) + '\n')

# 5) INVTABLE: 8 lines copied unchanged from example
want = ['CO', 'NOX', 'VOC', 'NH3', 'SO2', 'PM10', 'PM2_5', 'PMC']
src = {}
for l in open(a.invtab):
    l = l.rstrip('\n')
    t = l.split()
    if len(t) > 2 and t[0] in want and t[1] == t[0] and t[0] not in src:
        src[t[0]] = l
ih = ["# INVTABLE for Busan SMOKE case 2017capss_cb6 (CAPSS 2017 / East Asia inventories)",
      "# Lines copied unchanged from example ge_dat/invtable_2022platform_integrate_15sep2025_nf_v3.txt",
      "# (file lines 533 CO, 657 NOX, 702 VOC, 653 NH3, 687 SO2, 663 PM10, 665 PM2_5, 667 PMC)",
      "# Busan inventories have no HAPs: NONHAPVOC/NONHAPTOG, VOC_INV, mode-specific (EXH/EVP...) lines removed",
      "# PMC is computed in Smkinven (SMKINVEN_FORMULA PMC=PM10-PM2_5); VOC -> TOG via GSCNV in speciation"]
open(mk(f'{a.out}/EMIS/ge_dat/invtable_busan_2017capss_{TAG}.txt'), 'w').write('\n'.join(ih + [src[w] for w in want]) + '\n')
print('done:', a.out)
