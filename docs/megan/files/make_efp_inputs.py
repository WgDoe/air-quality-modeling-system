#!/usr/bin/env python3
"""도메인별 MEGAN EFP(배출계수 처리기) 입력 준비.

  사용법: python3 make_efp_inputs.py SCEN ECO_CSV GROWTH_CSV EFP_DIR EFP_PROGRAM_DIR EFP_UTF8_DIR

- 종 구성표 4종(Tree/Shrub/Herb/Crop)에서 도메인에 있는 생태유형만 남긴다.
  (전체 표를 쓰면 EFP가 배출계수 없는 수종을 묻는 입력 대기 상태로 멈춘다)
- 종 구성표의 VegID가 배출계수표에 없고 대소문자만 다르면 배출계수표 이름으로 맞춘다.
  그래도 없는 VegID는 목록으로 출력한다(EFP가 배출계수 0으로 처리).
- 생태유형·생육형 격자 CSV를 EFP 입력 폴더에 복사하고,
  배포본 MEGAN_EFP.py를 틀로 실행 파일 MEGAN_EFP_<SCEN>.py를 만든다.
"""
import re, shutil, sys
from pathlib import Path
import pandas as pd

scen, eco_csv, gf_csv, efp_dir, prog_dir, utf8_dir = sys.argv[1:7]
efp, prog, src = Path(efp_dir), Path(prog_dir), Path(utf8_dir)
inp = efp / "inputs" / "EFP"
inp.mkdir(parents=True, exist_ok=True)
EF = "EFv240120.csv"
TABLES = {"Crop": "SpeciationCrop230822", "Herb": "SpeciationHerb230822",
          "Shrub": "SpeciationShrub230822", "Tree": "SpeciationTree230921"}

shutil.copy(src / EF, inp / EF)
eco = pd.read_csv(eco_csv)
ids = set(eco.EcotypeID.unique())
efids = set(pd.read_csv(src / EF, usecols=["VegID"]).VegID)
lower = {v.lower(): v for v in efids}

names, report = {}, []
for gf, fname in TABLES.items():
    t = pd.read_csv(src / f"{fname}.csv", dtype={"VegID": str})
    t = t.loc[:, ~t.columns.str.startswith("Unnamed")]
    sub = t[t.EcoTypeID.isin(ids)].copy()
    lost = sorted(ids - set(sub.EcoTypeID))
    fixed, missing = {}, set()
    for v in sub.VegID.unique():
        if v not in efids:
            if v.lower() in lower:
                fixed[v] = lower[v.lower()]
            else:
                missing.add(v)
    sub["VegID"] = sub.VegID.replace(fixed)
    out = f"{fname}.{scen}.csv"
    sub.to_csv(inp / out, index=False)
    names[gf] = out
    report.append(f"{gf}: ecotypes {sub.EcoTypeID.nunique()}/{len(ids)}, rows {len(sub)}, "
                  f"no-speciation ecotypes {len(lost)}, case-fixed VegIDs {len(fixed)}, "
                  f"VegIDs without EF {len(missing)} {sorted(missing)[:20]}")

shutil.copy(eco_csv, inp / f"grid_ecotype.{scen}.csv")
shutil.copy(gf_csv, inp / f"grid_growth_form.{scen}.csv")

tpl = (prog / "MEGAN_EFP.py").read_text()
subs = {"scen_name": scen, "EF": EF, **{f"Ecotype_{g}": n for g, n in names.items()}}
for key, val in subs.items():
    tpl, k = re.subn(rf'^{key} = ".*"$', f'{key} = "{val}"', tpl, flags=re.M)
    assert k == 1, key
(efp / f"MEGAN_EFP_{scen}.py").write_text(tpl)
print(f"[{scen}] ecotypes in domain: {len(ids)}")
print("\n".join(report))
