# CMAQ 모델링 시스템 SMOKE 부산 사례 부문 병합(Mrggrid) 가이드

> **문서 순서:** 01 설치 → 02 기존 체계 분석 → 03 배출량 개선 계획 → 04 국내 실행 → 05 국외 실행 → **06 부문 병합**. [SMOKE 문서 목차](00_README_First.md)를 확인하세요.

## 1. 목적

부산 사례(`CASES/BUSAN/TEST_20260901`)에서 04·05 문서로 만든 부문별 지면 배출 파일(`premerged`)을 SMOKE 5.3 공식 병합 체계(`smk_sectormerge_emf.csh` → `mrggrid`)로 날짜·도메인마다 하나의 CMAQ 입력 파일로 합치는 절차를 다른 컴퓨터에서 그대로 재현할 수 있도록 기록한다. 예제 배포판 스크립트에서 **바꾼 부분은 4장에 따로 모았다.** 재실행할 때는 4장의 변경값만 확인하면 된다.

실행 순서:

```text
3장  필요한 파일 (04 §3.1 내려받기에 포함, 2026-11-25부터)
  ↓
5장  설치 확인 — 04 §7 설치 스크립트가 병합 파일 설치와 날짜 패치까지 자동으로 함
     5.1 병합 입력 확인 → 5.2 날짜 패치 확인 → 5.3 병합 설정 파일 확인
     (04 §7을 다시 돌리지 않는 기존 CASE만 5.2·5.3의 수동 명령)
  ↓
6장  실행
     6.1 09KM 시험 → 6.2 27·03·01KM
  ↓
7장  확인 (부문 합계 = 병합 파일, 로그, README)
  ↓
9장  CMAQ로 넘기는 파일 (병합 파일 + 점오염원 inline 파일)
```

병합 구성 (03 §9.3 이중계상 기준과 같다):

| 구분 | 부문 | 처리 |
|---|---|---|
| 병합 (지면층) | `kor_area`, `kor_mobile`, `kor_sea` | 4개 도메인 |
| 병합 (지면층) | `htap_energy`, `htap_industry`, `htap_transport`, `htap_resident`, `htap_waste`, `htap_agriculture`, `htap_aviation`, `htap_intship` | 27·09·03KM만. 01KM은 05 §8.4에 따라 제외 |
| 병합하지 않음 | `kor_point` | CMAQ inline 굴뚝 처리 (`stack_groups` + `inln_mole` 파일을 CMAQ에 직접 입력) |
| 병합하지 않음 | 생물성 | CMAQ 5.5 인라인 MEGAN 3.2 (03 §9) |

현재 상태(2026-11-25): **4개 도메인 × 2일(8월 31일·9월 1일) 병합 완료, 부문 합계 일치(7장). 국내 `SOAALK` 반영 후 재병합. CCTM 메커니즘 `cb6r5_ae7_aq` 확정([03 §7.3](03_SMOKE_Emission_Improvement_Plan.md#busan-mechanism)).** 2026-11-25 서버 기록에서 당시 5.1~7.2 절차로 같은 결과를 확인했다. 현재 문서의 종료 상태 확인은 이후 반영했다. CMAQ CCTM 연결은 미검증.

## 2. 구축 환경과 선행 조건

**설치·컴파일과의 구분:** 이 문서에는 컴파일 단계가 없다. `mrggrid`는 [01 SMOKE 설치](01_SMOKE_Installation_Guide.md)에서 이미 빌드됐다. 5장의 날짜 패치와 설정 파일은 CASE 폴더에 들어가는 **CASE 설치 단계**이고, 04 §7 설치 스크립트가 자동으로 한다. 6~7장이 CASE마다 반복하는 **실행 단계**다([운영 목차](../operations/README.md)).

- 환경은 [04 §2](04_SMOKE_Busan_Case_Run_Guide.md)와 같다 (Rocky Linux 9.8, 사용자 `woogon`, bash·csh, Python 3.9).
- 파이썬 모듈 `netCDF4`·`numpy`: 병합 스크립트의 영역 합계 점검(`emisqa.py`)과 7장 확인에 쓴다. 없으면 `python3 -m pip install --user netCDF4` ([01 설치 가이드](01_SMOKE_Installation_Guide.md) 예제 병합 단계와 같음).
- 선행 작업 (이 문서는 아래가 끝났다고 가정한다):
  - [04 국내 실행](04_SMOKE_Busan_Case_Run_Guide.md) 5~8장: `kor_point`, `kor_area`, `kor_mobile`, `kor_sea` × 4개 도메인
  - [05 국외 실행](05_HTAP_v32_Reproduction_Checklist.md) 6~7장: HTAP 8개 묶음 × 27·09·03KM
  - 04에서 설치한 `directory_definitions.csh`, `utils/mcip_period.py`, `smoke5.2/`(예제 실행 체계), `smoke5.2/scripts/smk_dates/2026/`

## 3. 필요한 파일

### 3.1 저장소에서 받는 파일 (5개)

**새 CASE는 따로 받을 필요가 없다.** 2026-11-25부터 아래 5개가 04 §3.1의 내려받기 목록(`file_list.txt`, 48개)에 들어 있고, 04 §6.4 패키지 → §7 설치 스크립트가 CASE에 설치하고 날짜 패치까지 적용한다.

04 §7을 다시 돌리지 않고 이미 설치된 CASE에 병합만 추가할 때는 아래 명령으로 5개만 받는다. 04 §3.1과 같은 `~/busan_smoke_files`에 저장소와 같은 폴더 구조로 받는다. 목록은 `docs/smoke/files/busan/2023capss/merge_file_list.txt`에 있다.

```bash
(
set -euo pipefail
F=$HOME/busan_smoke_files
REF=main # 최초 취득용. 검증 후 실제 커밋 SHA로 고정해 같은 입력을 다시 받는다.
RAW=https://raw.githubusercontent.com/WgDoe/air-quality-modeling-system/$REF/docs/smoke/files/busan
mkdir -p "$F/2023capss"
curl -fsSL -o "$F/2023capss/merge_file_list.txt.part" "$RAW/2023capss/merge_file_list.txt"
mv -- "$F/2023capss/merge_file_list.txt.part" "$F/2023capss/merge_file_list.txt"
count=0
while IFS= read -r p || [ -n "$p" ]; do
  case "$p" in ''|/*|*..*) echo "ERROR: invalid path: $p"; exit 1 ;; esac
  mkdir -p "$F/$(dirname "$p")"
  curl -fsSL -o "$F/$p.part" "$RAW/$p" || { echo "FAIL $p"; exit 1; }
  mv -- "$F/$p.part" "$F/$p"
  count=$((count + 1))
done < "$F/2023capss/merge_file_list.txt"
[ "$count" -eq 5 ] || { echo "ERROR: expected 5 files, got $count"; exit 1; }
echo "Downloaded $count files (+ merge_file_list.txt)"
)
```

정상 기준: `Downloaded 5 files (+ merge_file_list.txt)`.

| 파일 (`~/busan_smoke_files/2023capss/` 기준) | 용도 |
|---|---|
| `EMIS/2023capss_cb6/scripts/sectorlist_2023capss_cb6` | 27·09·03KM 부문 목록 (병합 11개) |
| `EMIS/2023capss_cb6/scripts/sectorlist_2023capss_cb6_01KM` | 01KM 부문 목록 (병합 3개, HTAP 제외) |
| `EMIS/2023capss_cb6/scripts/merge/Sector_merge_2023capss_cb6.csh` | 병합 실행기 |
| `EMIS/2023capss_cb6/scripts/utils/check_merge_totals.py` | 병합 결과 확인 (7장) |
| `EMIS/smoke5.2/scripts/emf/smk_sectormerge_emf_busan.patch` | 예제 공통 병합 스크립트 날짜 패치 (5.2) |

### 3.2 이미 설치된 파일 (04·05에서 설치)

| 파일 | 역할 |
|---|---|
| `EMIS/smoke5.2/scripts/emf/smk_sectormerge_emf.csh` | 예제 공통 병합 스크립트 (5.2에서 패치) |
| `EMIS/smoke5.2/scripts/smk_dates/2026/smk_merge_dates_2026MM.txt` | 날짜 대응표. 부산 사례는 `all` 열(실제 날짜)만 사용 |
| `EMIS/2023capss_cb6/scripts/directory_definitions.csh`, `utils/mcip_period.py` | 경로, MCIP 기간(`RUN_SDATE`·`RUN_EDATE`·`RUN_MONTHS`) |
| `SMOKEv5.3/subsys/smoke/Linux2_x86_64gfort10/mrggrid` | 병합 프로그램 ([01 설치](01_SMOKE_Installation_Guide.md)) |

<a id="merge-changes"></a>
## 4. 예제 대비 수정 사항 (재실행 시 확인할 부분)

예제(`smoke_example_case_v3/2022he_cb6_22m/scripts/merge/Sector_merge_12US1_2022he_cb6_22m_withbeis_withrwc.csh`, `sectorlist_2022he_cb6_22m_withbeis_withrwc`)를 틀로 썼다.

| 파일 | 예제 원본 | 부산 수정 내용 | 이유 | 적용 시점 |
|---|---|---|---|---|
| `smoke5.2/scripts/emf/smk_sectormerge_emf.csh` | 달의 1일~말일을 모두 병합 | `setenv G_STDATE $juldate` 다음에 5줄 추가: `RUN_SDATE`~`RUN_EDATE` 밖 날짜는 `continue` (패치 파일 `smk_sectormerge_emf_busan.patch`) | MCIP 기간(2일)만 부문 파일이 있어 원본대로는 8월 1일 파일을 찾다가 `does not exist`로 멈춤. 04의 `set_days_v5.csh` 패치와 같은 규칙 | **자동** — 04 §7 설치 스크립트 단계 4b (CASE 안 `smoke5.2` 사본에 적용, 재설치 시 건너뜀) |
| `scripts/merge/Sector_merge_2023capss_cb6.csh` | `RUN_MONTHS "1"`, `BASE_YEAR "2022"`, `MRGDATE_FILES` 2022, `SECTORLIST` 예제 | 기간·연도는 `directory_definitions.csh`(MCIP)에서 받음, 날짜 파일은 `${BASE_YEAR}` 폴더, `GRID=01KM`이면 01KM 부문 목록 선택, 패치·목록 존재를 먼저 검사, `OCL2ROOT` 삭제(병합에서 사용하지 않음) | 도메인·기간을 스크립트에 고정하지 않기 위함 | **자동** — 04 §7 설치 스크립트 단계 3 |
| `scripts/sectorlist_2023capss_cb6` | 예제 미국 부문 15개, `projectroot` `/home/cmas/training` | 부산 12개 부문, `sectbaseyr` `2026`, `mrgapproach` `all`, `kor_point`는 `mergesector` `N`, `projectroot` 빈칸 | 빈칸이면 `directory_definitions.csh`의 `PROJECT_ROOT`를 써서 경로 수정이 필요 없음 | **자동** — 04 §7 설치 스크립트 단계 3 |
| `scripts/sectorlist_2023capss_cb6_01KM` | (없음) | 위와 같고 HTAP 8개 `mergesector` `N` | 05 §8.4 01KM 국외 제외 | **자동** — 04 §7 설치 스크립트 단계 3 |

<a id="merge-case-settings"></a>
### 4.1 새 CASE에서 바꾸는 값

- **CASE 경로:** 5장·6장 명령의 `B=`·`C=`와 `directory_definitions.csh`의 `INSTALL_DIR` (04 §5와 같음).
- **기상 연도가 2026이 아닐 때:** 부문 목록 두 파일의 3번째 칸 `sectbaseyr`(`"2026"`)를 기상 연도로 바꾸고 `smk_dates/<연도>/` 날짜 파일을 준비한다. 병합 스크립트는 이 값으로 날짜 파일 줄을 찾는다. **다른 연도는 아직 검증하지 않았다.**
- **기간:** 바꿀 필요 없음. MCIP 파일에서 자동으로 읽는다.
- **01KM 국외:** 새 도메인·기간에서 05 §8.4 검사로 01KM 국외가 0이 아니면 `sectorlist_2023capss_cb6_01KM`을 쓰지 않도록 실행기의 01KM 분기를 지우고 HTAP 01KM을 처리한다.

<a id="merge-install"></a>
## 5. 설치 확인

04 §7 설치 스크립트(2026-11-25 이후 판)가 5.2·5.3을 자동으로 한다. 설치 화면에 4b `patched …` 또는 `already patched`와 병합 파일 `ok` 5줄이 보였으면 5.1과 아래 각 절의 **공통 확인** 블록만 실행한다. 이전에 설치한 CASE는 **수동 적용** 후 공통 확인을 진행한다.

### 5.1 병합 입력 확인

```bash
C=/home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/EMIS/2023capss_cb6
cd "$C" || exit 1
for G in 27KM 09KM 03KM 01KM; do
  printf '%s ' "$G"
  for s in kor_area kor_mobile kor_sea htap_energy htap_industry htap_transport htap_resident htap_waste htap_agriculture htap_aviation htap_intship; do
    n=$(ls premerged/$s/emis_mole_${s}_*_${G}_cmaq_cb6ae7_2023capss_cb6.ncf 2>/dev/null | wc -l)
    printf '%s=%s ' "$s" "$n"
  done
  P=smoke_out/2023capss_cb6/$G/cmaq_cb6ae7/kor_point
  echo "| stack_groups=$(ls $P/stack_groups_kor_point_${G}_2023capss_cb6.ncf 2>/dev/null | wc -l) inln=$(ls $P/inln_mole_kor_point_*_${G}_*.ncf 2>/dev/null | wc -l)"
done
```

정상 기준: 27·09·03KM은 11개 부문 모두 `=2`(MCIP 기간 2일), 01KM은 국내 3개 부문 `=2`(HTAP 칸은 0이어도 됨), 모든 도메인 `stack_groups=1 inln=2`.

### 5.2 병합 스크립트 날짜 패치

**수동 적용 — 기존 CASE에서 패치를 추가할 때만**

```bash
B=/home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/EMIS
F=$HOME/busan_smoke_files/2023capss
cd "$B/smoke5.2/scripts/emf" || exit 1
if grep -q 'Busan patch (2026-11-24)' smk_sectormerge_emf.csh; then
  echo "already patched"
else
  cp -p smk_sectormerge_emf.csh smk_sectormerge_emf.csh.orig
  patch -p1 --dry-run < "$F/EMIS/smoke5.2/scripts/emf/smk_sectormerge_emf_busan.patch" && \
  patch -p1 < "$F/EMIS/smoke5.2/scripts/emf/smk_sectormerge_emf_busan.patch"
fi
```

**공통 확인**

```bash
B=/home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/EMIS
cd "$B/smoke5.2/scripts/emf" || exit 1
grep -c 'Busan patch (2026-11-24)' smk_sectormerge_emf.csh
diff smk_sectormerge_emf.csh.orig smk_sectormerge_emf.csh
```

정상 기준: 처음 적용할 때 `checking file …`, `patching file smk_sectormerge_emf.csh`가 나온다(`fuzz`·`FAILED` 문구 없음). 이어서 `grep`이 `1`, `diff`에 `631a632,636`과 추가된 5줄만 보인다. 이미 패치된 CASE에서 다시 실행하면 `already patched`가 나오고, 뒤 두 줄 결과는 같다.

> 참고: 원본은 예제 배포판과 같은 파일이다(MD5 `00477c9a24787fd47848080738be1b57`). 다른 버전에서 `patch`가 실패하면 `set juldate = …` 다음 줄 `setenv G_STDATE $juldate` 바로 아래에 패치 파일의 `+` 5줄을 직접 넣는다.

### 5.3 병합 설정 파일 설치

**수동 적용 — 기존 CASE에서 병합 파일을 추가할 때만**

```bash
B=/home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/EMIS
F=$HOME/busan_smoke_files/2023capss
S=$B/2023capss_cb6/scripts
mkdir -p "$S/merge" "$S/utils" "$S/logs"
cp "$F"/EMIS/2023capss_cb6/scripts/sectorlist_2023capss_cb6 "$F"/EMIS/2023capss_cb6/scripts/sectorlist_2023capss_cb6_01KM "$S"/
cp "$F"/EMIS/2023capss_cb6/scripts/merge/Sector_merge_2023capss_cb6.csh "$S"/merge/
cp "$F"/EMIS/2023capss_cb6/scripts/utils/check_merge_totals.py "$S"/utils/
chmod +x "$S"/merge/Sector_merge_2023capss_cb6.csh
```

**공통 확인**

```bash
B=/home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/EMIS
S=$B/2023capss_cb6/scripts
grep -c '"Y"' "$S"/sectorlist_2023capss_cb6 "$S"/sectorlist_2023capss_cb6_01KM
ls -l "$S"/merge "$S"/utils/check_merge_totals.py
```

정상 기준: `sectorlist_2023capss_cb6:11`, `sectorlist_2023capss_cb6_01KM:3`.

<a id="merge-run"></a>
## 6. 실행

### 6.0 이전 결과 지우기 (다시 실행할 때만)

**기존 병합 결과를 다시 생성할 때만 이 블록을 실행한다.** 병합 결과·중간 파일·보고서만 지운다. 부문별 결과(`premerged`, `kor_point`)와 설정 파일은 남긴다. 병합 결과는 6장으로 다시 만들 수 있다.

```bash
C=/home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/EMIS/2023capss_cb6
cd "$C" || exit 1
rm -rf -- smoke_out/2023capss_cb6/{27KM,09KM,03KM,01KM}/cmaq_cb6ae7/merged_nobeis_norwc \
          intermed/{27KM,09KM,03KM,01KM}/{merge,mrggrid} reports/mrggrid
rm -f -- scripts/logs/mrggrid_*.log smoke_out/2023capss_cb6/*/cmaq_cb6ae7/tmp_{readme,filelist}_*
ls smoke_out/2023capss_cb6/*/cmaq_cb6ae7/
```

정상 기준: 마지막 `ls`에 `kor_point`만 보인다. `tmp_readme_<번호>`·`tmp_filelist_<번호>`는 병합이 중간에 멈춘 실행이 남긴 임시 파일이다.

### 6.1 09KM 시험

```bash
source ~/.bashrc
C=/home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/EMIS/2023capss_cb6
cd "$C/scripts/merge" || exit 1
if ! GRID=09KM LC_ALL=C ./Sector_merge_2023capss_cb6.csh > ../logs/mrggrid_09KM.log 2>&1; then
  echo 'STOP: merge failed in 09KM (see ../logs/mrggrid_09KM.log)' >&2
  exit 1
fi
grep -E 'Run period|Sector merge|Months|Running merge script|Completed sector merge' ../logs/mrggrid_09KM.log
cd "$C"
grep -E 'ERROR|does not exist|Segmentation fault' scripts/logs/mrggrid_09KM.log | grep -vc 'No warning or error'
ls smoke_out/2023capss_cb6/09KM/cmaq_cb6ae7/merged_nobeis_norwc/
python3 scripts/utils/check_merge_totals.py 09KM
```

정상 기준:

```text
Run period from MCIP: 2026243 - 2026244 (months: 8 9)
Sector merge, grid 09KM, sector list .../scripts/sectorlist_2023capss_cb6
Months 8 9, dates 2026243 - 2026244
## Running merge script for 08/31/2026, using data files:
Completed sector merge for 08/2026
## Running merge script for 09/01/2026, using data files:
Completed sector merge for 09/2026
0
README_2023capss_cb6_09KM_nobeis_norwc_premerged_sectors.txt
emis_mole_all_20260831_09KM_nobeis_norwc_2023capss_cb6.ncf
emis_mole_all_20260901_09KM_nobeis_norwc_2023capss_cb6.ncf
...
RESULT: ALL OK
```

로그의 `No warning or error messages. Exiting`은 로그 분석기의 정상 문구라 위 오류 수(`0`)에서 뺐다. 실행 시간은 4개 도메인을 모두 합쳐 1분 이내다(2026-11-24, 6.0~7.2 전체 48초).

### 6.2 27·03·01KM

```bash
source ~/.bashrc
C=/home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/EMIS/2023capss_cb6
cd "$C/scripts/merge" || exit 1
for G in 27KM 03KM 01KM; do
  log=../logs/mrggrid_$G.log
  if ! GRID=$G LC_ALL=C ./Sector_merge_2023capss_cb6.csh > "$log" 2>&1; then
    echo "STOP: merge failed in $G (see $log)" >&2
    exit 1
  fi
  grep -E 'Sector merge|Running merge script' "$log"
  if grep -E 'ERROR|does not exist|Segmentation fault' ../logs/mrggrid_$G.log | grep -vq 'No warning or error'; then
    echo "STOP: error in $G (see $log)" >&2
    exit 1
  fi
done
```

병합 완료는 실행기 정상 종료와 7장의 파일 수·부문 합계 검증을 모두 확인한 뒤 기록한다.

정상 기준: 도메인마다 `Running merge script for 08/31/2026`, `09/01/2026` 두 줄. 01KM은 `sector list .../sectorlist_2023capss_cb6_01KM`. `STOP` 문구 없음.

<a id="merge-verify"></a>
## 7. 확인

### 7.1 파일 수와 부문 합계

```bash
C=/home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/EMIS/2023capss_cb6
cd "$C"
ls smoke_out/2023capss_cb6/*/cmaq_cb6ae7/merged_nobeis_norwc/emis_mole_all_*.ncf | wc -l
python3 scripts/utils/check_merge_totals.py 27KM 09KM 03KM 01KM
```

`check_merge_totals.py`는 병합 파일마다 다음을 검사한다: 부문 목록의 병합 대상(`Y`) 부문 파일이 모두 있는지, 격자 이름·시간 수·층수(1)·시작일이 부문 파일과 같은지, 모든 화학종이 부문 파일의 합과 같은지(상대차 1×10⁻⁵ 이하), 음수·비정상값이 없는지. 점오염원(`kor_point`)이 병합에 들어갔다면 합계가 맞지 않아 실패한다.

정상 기준: 파일 수 `8`, 마지막 줄 `RESULT: ALL OK`. 2026-11-25 결과:

| 도메인 | 부문 | 화학종 | 최대 상대차 | NO 25시간 합 (8/31, mol/s) | SO2 | PEC (g/s) | SOAALK (mol/s) |
|---|---:|---:|---:|---:|---:|---:|---:|
| 27KM | 11 | 63 | 4.9×10⁻⁸ | 4.106×10⁵ | 1.221×10⁵ | 7.423×10⁵ | 5.867×10⁴ |
| 09KM | 11 | 63 | 4.3×10⁻⁸ | 1.416×10⁴ | 2015 | 1.54×10⁴ | 1023 |
| 03KM | 11 | 63 | 3.3×10⁻⁸ | 3423 | 171 | 2292 | 229.6 |
| 01KM | 3 | 60 | 2.9×10⁻⁸ | 1199 | 48.39 | 588.9 | 81.2 |

모든 파일 25시간(0시~다음날 0시), 1층, 음수 0. 01KM의 화학종이 3개 적은 이유는 부록 B. 값은 2026-11-25 국내 `SOAALK` 반영(04 부록 A) 후 재병합 결과이며, `SOAALK` 외 값은 반영 전과 같다.

### 7.2 README와 로그

```bash
C=/home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/EMIS/2023capss_cb6
cat $C/smoke_out/2023capss_cb6/01KM/cmaq_cb6ae7/merged_nobeis_norwc/README_*.txt
ls $C/intermed/09KM/mrggrid/logs $C/reports/mrggrid/09KM/cmaq_cb6ae7
```

정상 기준: README에 병합된 부문 폴더가 나열된다(27·09·03KM 11개, 01KM 3개). `reports/mrggrid/<GRID>/cmaq_cb6ae7/`에 날짜별 `domain_totals_*.rpt`(영역 합계)와 `mrggrid_dates_*.rpt`가 있다.

## 8. 입력 파일과 생성 파일

| 역할 | 위치·파일명 (`EMIS/` 기준) | 내용 | 쓰는 프로그램 | 구분 |
|---|---|---|---|---|
| 배출량 (입력) | `2023capss_cb6/premerged/<부문>/emis_mole_<부문>_<날짜>_<GRID>_cmaq_cb6ae7_2023capss_cb6.ncf` | 부문별 시간·격자 지면 배출 | mrggrid | 04·05 결과 |
| 병합 설정 | `2023capss_cb6/scripts/sectorlist_2023capss_cb6`, `…_01KM` | 병합 부문, 날짜 방식, 기준 연도 | smk_sectormerge_emf.csh | 신규 |
| 날짜 | `smoke5.2/scripts/smk_dates/2026/smk_merge_dates_2026{08,09}.txt` | 실제 날짜 ↔ 대표일 (`all` 열 사용) | smk_sectormerge_emf.csh | 기존 (04) |
| 실행 설정 | `2023capss_cb6/scripts/directory_definitions.csh`, `utils/mcip_period.py` | 경로, MCIP 기간 | 실행기 | 기존 (04) |
| 실행 | `2023capss_cb6/scripts/merge/Sector_merge_2023capss_cb6.csh` | 병합 실행기 | csh | 신규 (예제 기반) |
| 실행 | `smoke5.2/scripts/emf/smk_sectormerge_emf.csh` | 공통 병합 스크립트 | csh | 예제 + 날짜 패치 |
| 확인 | `2023capss_cb6/scripts/utils/check_merge_totals.py` | 부문 합계 비교 | python3 | 신규 |
| **결과** | `2023capss_cb6/smoke_out/2023capss_cb6/<GRID>/cmaq_cb6ae7/merged_nobeis_norwc/emis_mole_all_<날짜>_<GRID>_nobeis_norwc_2023capss_cb6.ncf` | 날짜별 병합 지면 배출 (25시간, 1층, mol/s·g/s) | → CMAQ | 생성 |
| 결과 설명 | 같은 폴더 `README_2023capss_cb6_<GRID>_nobeis_norwc_premerged_sectors.txt` | 병합된 부문 목록 | | 생성 |
| 로그 | `2023capss_cb6/scripts/logs/mrggrid_<GRID>.log`, `intermed/<GRID>/mrggrid/logs/` | 실행 화면, mrggrid 로그 | | 생성 |
| 보고서 | `2023capss_cb6/reports/mrggrid/<GRID>/cmaq_cb6ae7/domain_totals_<날짜>.rpt` | 영역 합계 (`emisqa.py`) | | 생성 |
| 중간 | `2023capss_cb6/intermed/<GRID>/merge/filelist_*.lst`, `intermed/<GRID>/mrggrid/m3stat_logs/` | 날짜별 입력 목록, 통계 | | 생성 |

파일 이름의 `nobeis_norwc`는 부문 목록에 예제의 `beis`·`rwc` 부문이 없다는 뜻으로, 예제 병합 스크립트가 자동으로 붙인다.

## 9. CMAQ로 넘기는 파일

도메인·날짜마다 다음 파일을 CCTM 배출 입력으로 쓴다(**CCTM 연결은 미검증**).

| 입력 | 파일 (`EMIS/2023capss_cb6/smoke_out/2023capss_cb6/<GRID>/cmaq_cb6ae7/`) |
|---|---|
| 지면 배출 (병합) | `merged_nobeis_norwc/emis_mole_all_<날짜>_<GRID>_nobeis_norwc_2023capss_cb6.ncf` |
| 점오염원 굴뚝 정보 | `kor_point/stack_groups_kor_point_<GRID>_2023capss_cb6.ncf` (날짜 공통) |
| 점오염원 배출 | `kor_point/inln_mole_kor_point_<날짜>_<GRID>_cmaq_cb6ae7_2023capss_cb6.ncf` |
| 생물성 | 파일 없음. CCTM 인라인 MEGAN 3.2 ([MEGAN 문서](../megan/00_README_First.md)) |

CCTM에 연결하기 전에 [03 §9.3](03_SMOKE_Emission_Improvement_Plan.md#busan-inline-megan)의 이중계상 확인(생물성이 병합 파일에 없는지)과 [03 §7.3](03_SMOKE_Emission_Improvement_Plan.md#busan-mechanism)의 배출종·단위·DESID 대응을 확인한다. CCTM 빌드 메커니즘은 `cb6r5_ae7_aq`로 확정했으며(2026-11-25), SMOKE 종분배는 CB6R3_AE7을 유지한다. CCTM 입력 연결과 모의는 미검증이다.

## 10. 완료 현황

| 단계 | 상태 (2026-11-25) |
|---|---|
| 3장 파일, 5장 설치 (입력 확인·날짜 패치·설정 설치) | 완료 |
| 설치 스크립트 자동화 (04 §7 단계 4b, 내려받기 목록 48개) | 완료 (2026-11-25, 임시 폴더에서 처음 적용·재실행 건너뜀 확인, 결과 파일이 수동 패치본과 동일) |
| 6.1 09KM 시험 | 완료 (오류 0, 2일, 합계 일치) |
| 6.2 27·03·01KM | 완료 (오류 0, 도메인마다 2일, 합계 일치) |
| 7장 확인 | 완료 (8개 파일 `ALL OK`) |
| 문서 재현 확인 | 완료 (6.0으로 결과를 지운 뒤 5.1~7.2 블록을 그대로 실행, 같은 결과) |
| 국내 `SOAALK` 반영 후 재병합 | 완료 (2026-11-25, 6.0~7.2 블록 그대로 실행, 8개 파일 `ALL OK`) |
| CCTM 메커니즘 | `cb6r5_ae7_aq` 확정 (2026-11-25, 03 §7.3) |
| CMAQ CCTM 연결 | 미실행 (9장 선행 확인 후) |

## 부록 A. 실행 중 발생한 문제 기록

| 날짜 | 증상 | 원인 | 조치 |
|---|---|---|---|
| 11-24 | 패치 전 원본으로 09KM 병합 시 `## Running merge script for 08/01/2026` 다음 `SCRIPT ERROR: data file expected but not found: …_20260801_09KM_…`, `One or more input files expected by script does not exist.` (종료 코드 1, 병합 파일 없음) | 예제 `smk_sectormerge_emf.csh`는 `RUN_MONTHS`의 모든 날짜를 병합. 부문 파일은 MCIP 기간(8/31·9/1)만 있음 | 5.2 날짜 패치 (04 `set_days_v5.csh` 패치와 같은 규칙) |
| 11-24 | 패치 적용 시 `Hunk #1 succeeded at 628 with fuzz 1` | 손으로 만든 패치의 주변 줄 공백이 원본과 달랐음 | 원본과 `diff -u`로 패치를 다시 만들어 저장소에 등록 (현재 파일은 fuzz 없이 적용됨) |
| 11-24 | (참고) 같은 날 앞서 파이썬으로 부문 파일을 직접 더해 만든 병합본 `2023capss_cb6/cmaq_ready/merged/emis_mole_all_*_cmaq_cb6ae7_2023capss_htap.ncf` 8개가 있었음 | SMOKE 공식 병합 이전의 임시 결과 | 이 문서의 결과와 비교: 61종 모두 상대차 5×10⁻⁸ 이하로 같음(임시본은 `UNK`·`VOC_INV` 2종을 뺐음). 재현 절차는 이 문서의 SMOKE 병합을 기준으로 함 |

## 부록 B. 화학종 메모

| 화학종 | 출처 | 비고 |
|---|---|---|
| `UNK`, `VOC_INV` | HTAP 종분배 (`gspro_HTAP_CB06…`) | 미지정 VOC와 VOC 인벤토리 총량 진단용. CMAQ 배출 대응표에 없으면 사용되지 않음 |
| `SOAALK` | 국내: tracer 종분배(04 §3.3, 2026-11-25 추가) / 국외: HTAP 종분배 | 장쇄 알케인 SOA 전구물질 추적자. CCTM `cb6r5_ae7_aq`가 사용 |
| `SULF` | HTAP 종분배만 | 1차 황산. 국내 CAPSS에는 아직 없음(연료 기준 대응표 필요, 03 §7.2 7순위). 01KM은 HTAP을 병합하지 않아 `SULF`·`UNK`·`VOC_INV`가 없어 60종 |
