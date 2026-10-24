#!/usr/bin/env python3
"""Print the SMOKE run period from an MCIP METCRO2D file:  RUN_SDATE RUN_EDATE BASE_YEAR MONTHS...
RUN_SDATE/RUN_EDATE are YYYYDDD of the first and last emission day (00-24 UTC day files).
The last day is the day containing the last MCIP hour minus one second
(e.g. 2026-08-31 01 UTC .. 2026-09-02 00 UTC -> 2026243 2026244, months 8 9).
Usage: python3 mcip_period.py <MCIP folder of one domain>"""
import sys, glob, re, subprocess, datetime as dt
f = sorted(glob.glob(sys.argv[1].rstrip('/') + '/METCRO2D*'))[0]
h = subprocess.run(['ncdump', '-h', f], capture_output=True, text=True, check=True).stdout
sd = int(re.search(r':SDATE = (\d+)', h).group(1)); st = int(re.search(r':STIME = (\d+)', h).group(1))
ts = int(re.search(r':TSTEP = (\d+)', h).group(1)); n = int(re.search(r'TSTEP = UNLIMITED ; // \((\d+) currently', h).group(1))
t0 = dt.datetime(sd // 1000, 1, 1) + dt.timedelta(days=sd % 1000 - 1, hours=st // 10000, minutes=st // 100 % 100)
step = dt.timedelta(hours=ts // 10000, minutes=ts // 100 % 100)
t1 = t0 + step * (n - 1)
d0, d1 = t0.date(), (t1 - dt.timedelta(seconds=1)).date()
j = lambda d: d.year * 1000 + d.timetuple().tm_yday
months = sorted({(d0 + dt.timedelta(days=k)).month for k in range((d1 - d0).days + 1)})
print(j(d0), j(d1), d0.year, *months)
