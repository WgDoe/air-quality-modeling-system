#!/usr/bin/env python3
"""GFv7 관목 피복(SC30s7.nc) 변수 이름 수정본 만들기.

배포 파일 SC30s7.nc 안의 관목 변수 이름이 작물과 같은 'CCpercent'로 들어 있다.
값과 좌표는 그대로 두고 변수 이름만 'SCpercent'로 바꾼 복사본을 만든다.
사용법: python3 megan_fix_sc30s7.py GFv7nc/SC30s7.nc GFv7nc/SC30s7_SCpercent.nc
"""
import shutil, sys
from pathlib import Path
from netCDF4 import Dataset

src, dst = map(Path, sys.argv[1:3])
if dst.exists():
    with Dataset(dst) as d:
        if "SCpercent" in d.variables:
            print(f"{dst} 있음 - 건너뜀")
            sys.exit(0)
tmp = dst.with_suffix(".nc.part")
shutil.copyfile(src, tmp)
with Dataset(tmp, "a") as d:
    assert "CCpercent" in d.variables and "SCpercent" not in d.variables
    d.renameVariable("CCpercent", "SCpercent")
tmp.rename(dst)
print(f"{dst} 생성 (CCpercent → SCpercent)")
