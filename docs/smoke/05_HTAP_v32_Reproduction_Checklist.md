# CMAQ 모델링 시스템 SMOKE 부산 사례 국외 배출량(HTAP_v3.2) 처리 가이드

> **문서 순서:** 01 설치 → 02 기존 체계 분석 → 03 배출량 개선 계획 → 04 국내 배출량 → **05 국외 배출량(이 문서)**. [SMOKE 문서 목차](00_README_First.md)를 확인하세요.

## 1. 목적

부산 사례(`CASES/BUSAN/TEST_20260901`)의 국외 인위 배출량을 HTAP_v3.2 2020년 0.1° 자료로 SMOKE 5.3에서 처리하는 절차를 다른 컴퓨터에서 처음부터 그대로 재현할 수 있도록 기록한다. 국내 배출량(04)과 같은 배출 시나리오 `2023capss_cb6`, 같은 사례 폴더를 쓴다. 자료 선정 근거는 [03 배출량 개선 계획](03_SMOKE_Emission_Improvement_Plan.md) §4.9에 있다.

실행 순서:

```text
3장  필요한 파일 (저장소 파일, HTAP 원자료 9개)
  ↓
5장  입력 생성 (HTAP 원자료 + CAPSS 원본 → 생성기 → 패키지)
  ↓
6장  SMOKE 패치·재컴파일·설치 (smkinven.f, ASSIGNS.emf, 사례 설치)
  ↓
7장  실행 (27·09·03KM × 8개 부문 묶음)
  ↓
8장  확인 (로그·파일, 묶음별 배출, 남한 제거, 국외/국내 비율)
```

현재 상태(2026-11-11): **27·09·03KM 8개 묶음 실행 완료, 01KM은 제공된 시험 결과상 영역 안 국외 배출 0으로 제외.** 병합·CMAQ 연계는 미실행.

## 2. 구축 환경과 선행 조건

- OS: Rocky Linux 9.8, 사용자 `woogon`, 프로젝트 루트 `/home/woogon/CMAQ_MODEL`
- 파이썬: Python 3.9, 모듈 `netCDF4`·`numpy`·`pandas`·`pyproj`
- 도구: `ncdump`, `tcsh`, `wget`, `unzip`

선행 작업 (이 문서는 아래가 끝났다고 가정한다):

| 선행 작업 | 문서 |
|---|---|
| SMOKE 5.3 설치, 공식 예제(`CASES/SMOKE_TEST/smoke_example_case_v3`) 압축 해제 | [01 SMOKE 설치 가이드](01_SMOKE_Installation_Guide.md) |
| MCIP 4개 도메인 (`CASES/BUSAN/TEST_20260901/MCIP/{27KM,09KM,03KM,01KM}`) | [MCIP 구축 가이드](../mcip/MCIP_Installation_Guide.md) |
| 국내 배출량: 저장소 파일 받기(3.1), CAPSS 원본 복사(3.2), 폴더·입력 설치(5~7장), **Grdmat 패치(7.1)** | [04 국내 배출량 가이드](04_SMOKE_Busan_Case_Run_Guide.md) |

국외 입력 생성기는 남한 제거에 **CAPSS 2023 원본**(04 §3.2의 `/home/woogon/CMAQ_MODEL/DATA/EMIS/CAPSS2023`)을, 실행은 국내 설치에서 만든 폴더·날짜 파일·`directory_definitions.csh`를 그대로 쓴다.

## 3. 필요한 파일

### 3.1 저장소 파일

04 §3.1의 파일 받기 명령으로 함께 받는다(`~/busan_smoke_files/`). 국외에 쓰는 파일:

| 파일 (`~/busan_smoke_files/` 기준) | 용도 |
|---|---|
| `2023capss/generators/make_busan_htap_v32_inputs.py` | 국외 입력 생성기 (5장) |
| `2023capss/smoke_patch/apply_htap_v32_patches.py` | `smkinven.f`·`ASSIGNS.emf` 패치 적용기 (원본 자동 백업) |
| `2023capss/smoke_patch/smkinven_htap_v32.patch` | `smkinven.f` 변경 내역 (참고용) |
| `2023capss/EMIS/smoke5.2/assigns/ASSIGNS_htap_v32.patch` | `ASSIGNS.emf` 변경 내역 (참고용) |
| `2023capss/EMIS/2023capss_cb6/scripts/directory_definitions.csh` | 도메인별 MCIP `GRIDCRO2D`를 `GRID_CRO_2D`로 지정 (국내와 공용) |
| `2023capss/EMIS/2023capss_cb6/scripts/htap/Annual_htap_2023capss_cb6.csh` | 국외 부문 묶음별 실행 스크립트 |
| `invtable_busan_2017capss_20261021.txt` | 국내 INVTABLE (생성기가 PEC·POC 줄을 더한 국외용 복사본을 만듦) |

### 3.2 HTAP_v3.2 원자료 내려받기

2020년 연간 flux 0.1° 전지구 자료 9종(물질마다 ZIP 1개, 안에 NetCDF 1개). 생성기가 ZIP에서 직접 읽으므로 압축을 풀지 않는다.

```bash
(
set -euo pipefail
H="$HOME/CMAQ_MODEL/DATA/EMIS/HTAPv32/2020"
mkdir -p "$H" && cd "$H"
for p in CO NH3 NMVOC NOx PM10 PM2.5 SO2 BC OC; do
  wget -nc "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/EDGAR/datasets/htap_v32/gridmaps_01x01/fluxes/annual/${p}/edgar_HTAPv32_2020_${p}.zip"
done
for p in CO NH3 NMVOC NOx PM10 PM2.5 SO2 BC OC; do
  test -s "edgar_HTAPv32_2020_${p}.zip" || { echo "Missing $p"; exit 1; }
  unzip -t "edgar_HTAPv32_2020_${p}.zip" | tail -1
done
sha256sum edgar_HTAPv32_2020_*.zip > htap_v32_2020_sha256.txt
)
```

정상 기준: ZIP 9개 모두 `No errors detected`. `htap_v32_2020_sha256.txt`는 재현 기록(부록 B)에 남긴다.

### 3.3 SMOKE 공식 예제에서 가져오는 파일

생성기가 `--example`로 지정한 예제 폴더에서 읽거나 복사한다.

| 예제 파일 | 쓰는 곳 |
|---|---|
| `ge_dat/EDGAR/GRIDMASK_EDGAR.ncf`, `geocode1~4_edgar.txt` | 0.1° 셀별 국가 코드·시간대 → 부산 영역으로 잘라 `GRIDMASK_EDGAR_busan_window.ncf` 생성 |
| `ge_dat/EDGAR/HTAPv3_profiles/` (종분배 `gspro_HTAP_CB06_from_2011ei_corrected_20feb2024_nf_v1.txt`, 변환 `gscnv_edgar_HTAPv3_03Apr2024.txt`, 시간 `HTAP_2011_BaseA_tpro_{monthly,weekly,hourly}_24oct2022_nf_v1`) | 종분배·시간배분 프로파일 (그대로 복사) |
| `ge_dat/invtable_2022platform_MOVES_nonroad_15oct2024_nf_v2.txt` | 일반 `PEC`·`POC` 줄을 찾아 국외 INVTABLE에 추가 |
| `smoke5.2/scripts/emf/smk_ar_gridded_annual_emf.csh` | 격자 인벤토리 실행 체계 (국내 설치 때 복사됨) |

## 4. 처리 원칙과 결정

| 항목 | 결정 | 근거·한계 |
|---|---|---|
| 자료·연도 | HTAP_v3.2 **2020년 연간 flux** (자료 최신 연도) + 예제 HTAP 월·요일·시간 프로파일 | 월별 flux 직접 적용은 후속 개선 후보 |
| 생성 영역 | 90~162°E, 18~56°N, 720×380 = 273,600개 0.1° 셀 | 27KM 도메인 + 여유 |
| **남한 제거** | CAPSS 2023 점·면·이동·바다 1km 셀이 닿는 0.1° 셀 전체를 모든 부문·물질에서 0 | 국내는 CAPSS만 사용(이중 계상 방지). 해안·접경의 국외 배출 일부도 함께 제거될 수 있음 |
| **입자 성분** | BC → `PEC`, OC → `POC`(프로파일 0), `PM2_5`·`PM10` = 원값 − BC − OC. BC+OC > PM2.5인 셀은 BC·OC를 비례 축소 | 셀별 PM2.5 총량은 보존. BC·OC 성분 질량은 바뀜(BC 축소의 98%가 FUGITIVE 가스 플레어링) |
| **부문 묶음** | HTAP 세부 부문을 8개 묶음으로 실행 (아래 표). 묶음마다 SMOKE 부문 `htap_<묶음>` | 예제 HTAP 처리 구조 |
| 종·시간 참조 | 세부 부문을 예제의 상위 부문 프로파일에 연결. FUGITIVE·SOLVENTS → INDUSTRY는 **잠정** | 국외 전용 프로파일 없음 |
| INVTABLE | 국내 파일은 그대로 두고 별도 복사본에 일반 `PEC PEC`, `POC POC` 줄만 추가 (MOVES 배기 전용 행 제외) | |
| **도메인** | **27·09·03KM 적용, 01KM 제외** | 03KM 국외/국내 NO 1.00%(주로 국제 선박)지만 영역 안 실제 배출이라 포함. 01KM은 영역 안 국외 0 (8.4) |

부문 묶음:

| 묶음 (`HTAP_GROUP`) | 세부 부문 (SCC) | 종·시간 프로파일 |
|---|---|---|
| INTSHIP | INTSHIP (국제 선박) | SHIPS |
| AVIATION | DOMAVIA_LTO/CDS/CRS, INTAVIA_LTO/CDS/CRS (국내·국제 항공 이착륙·상승하강·순항) | AIR_LTO, AIR_CDS, AIR_CRS |
| ENERGY | ENERGY (발전) | ENERGY |
| INDUSTRY | INDUSTRY, FUGITIVE, SOLVENTS | INDUSTRY (뒤의 2개 잠정) |
| TRANSPORT | TRANSPORT, BWTW(브레이크·타이어 마모), DOMSHIP(연안 선박), OTHTRANSPORT | TRANSPORT, TRANS_BWTW, SHIPS, TRANSPORT |
| RESIDENT | RESIDENT (가정·상업) | RESIDENT |
| WASTE | WASTE (폐기물) | WASTE |
| AGRICULTURE | AGRIBURN, LIVESTOCK, CROPS | AG_BURNING, AG, AG |

## 5. 입력 생성

### 5.1 파이썬 모듈

```bash
pip3 install --user netCDF4 numpy pandas pyproj
python3 -c 'import netCDF4,numpy,pandas,pyproj; print("python modules OK")'
which tcsh ncdump
```

### 5.2 생성기 실행

생성 결과를 패키지 폴더 `~/busan_htap_pkg`에 만든다. `--final`은 목록 파일에 기록되는 **최종 설치 경로**이므로 실제 사례 `EMIS` 폴더와 같아야 한다.

```bash
(
set -euo pipefail
ROOT="$HOME/CMAQ_MODEL"
F="$HOME/busan_smoke_files"
B="$ROOT/CASES/BUSAN/TEST_20260901"
HPKG="$HOME/busan_htap_pkg"
test ! -e "$HPKG" || { echo "기존 생성 패키지 먼저 백업"; exit 1; }
python3 "$F/2023capss/generators/make_busan_htap_v32_inputs.py" \
  --htap "$ROOT/DATA/EMIS/HTAPv32/2020" --year 2020 \
  --capss "$ROOT/DATA/EMIS/CAPSS2023" \
  --example "$ROOT/CASES/SMOKE_TEST/smoke_example_case_v3" \
  --invtable "$F/invtable_busan_2017capss_20261021.txt" \
  --final "$B/EMIS" --out "$HPKG" \
  2>&1 | tee "$HOME/busan_htap_generate.log"
grep -nE 'South Korea mask|BC/OC read|list files|INVTABLE|WARNING|ERROR|done' "$HOME/busan_htap_generate.log"
)
```

생성기 처리 순서: 영역 추출 → CAPSS 셀 기반 남한 제거 → BC·OC를 PEC·POC로, PM2.5·PM10에서 탄소 제외 → 변수명(16자 이하)·단위 지정 → 8개 묶음 `#LIST GRID` 목록 → 국가코드·시간대 파일 → 종·시간 참조 → INVTABLE(PEC·POC).

### 5.3 생성 결과 확인

2026-11-10 실행 로그 기준값:

```text
South Korea mask: 3176 of 273600 0.1 deg cells (GEOCODE 197000 cells: 979, of them outside mask: 0)
BC/OC read; scaled down where BC+OC > PM2.5: BC 216,739 t/yr, OC 44,876 t/yr
list files: INTSHIP=9, AVIATION=54, ENERGY=9, INDUSTRY=27, TRANSPORT=31, RESIDENT=9, WASTE=9, AGRICULTURE=27
INVTABLE PEC: invtable_2022platform_MOVES_nonroad_15oct2024_nf_v2.txt line 659
INVTABLE POC: invtable_2022platform_MOVES_nonroad_15oct2024_nf_v2.txt line 667
done
```

물질별 질량 (t/yr):

| 물질 | 영역 합계 | 남한 제거 | 남한 셀 잔여 | 탄소 조정 |
|---|---:|---:|---:|---:|
| CO | 159,059,631 | 736,683 | 0 | 0 |
| NH3 | 11,700,586 | 304,792 | 0 | 0 |
| NOX | 28,799,609 | 1,229,076 | 0 | 0 |
| VOC | 35,412,553 | 1,206,219 | 0 | 0 |
| SO2 | 12,357,628 | 265,959 | 0 | 0 |
| PM2_5 (탄소 제외) | 4,509,856 | 43,743 | 0 | 0 |
| PM10 (탄소 제외) | 7,752,766 | 128,518 | 0 | 0 |
| PEC | 1,277,291 | 14,695 | 0 | 216,739 |
| POC | 2,873,785 | 40,235 | 0 | 44,876 |

`PM2_5 + PEC + POC = 8,660,932 t/yr`로 원래 PM2.5를 보존한다. 제거된 셀 중 북한 코드 몫 0.1~1.3%, 일본 0%.

생성 파일 (`~/busan_htap_pkg/EMIS/` 기준):

| 위치 | 파일 | 의미 |
|---|---|---|
| `2023capss_cb6/inputs/htap/` | `htap_v32_2020_<물질>_busan.nc` 9개, `arinv.HTAPv32.<묶음>.lst` 8개 + `ALL`, `htap_summary_20261110.csv` (**19개**) | 영역·남한 제거·탄소 분리된 격자 배출량, 묶음별 입력 목록, 질량 요약 |
| `ge_dat/EDGAR/` | `GRIDMASK_EDGAR_busan_window.ncf`, `geocode1~4_edgar.txt` | 셀별 국가 코드·시간대 |
| `ge_dat/EDGAR/HTAPv32_profiles/` | 예제 종분배·시간 프로파일 5개, `gsref_HTAPv32_busan_20261110.txt`, `tref_HTAPv32_busan_20261110.txt` | 프로파일과 세부 부문 연결 |
| `ge_dat/` | `invtable_busan_htap_20261110.txt` | 국내 INVTABLE + PEC·POC |

## 6. SMOKE 패치·재컴파일·설치

격자 NetCDF 인벤토리를 읽을 때 `smkinven.f`의 변수 `NONPOINT`가 초기화되지 않아 Smkinven이 `Segmentation fault`로 멈춘다([91](91_SMOKE_smkinven_Fix.md)). 예제 `ASSIGNS.emf`는 MCIP `GRIDCRO2D` 파일 이름을 고정 형식으로 지정해 실제 파일을 찾지 못하므로 `directory_definitions.csh`의 값을 우선 쓰게 고친다. 국내 Grdmat 패치(04 §7.1 `genagmat.f`)는 그대로 둔다.

아래 블록은 bash 서브셸로 실행한다(실패해도 터미널은 닫히지 않음).

```bash
(
set -euo pipefail
export SMK_HOME=/home/woogon/CMAQ_MODEL/SMOKEv5.3
export BIN=Linux2_x86_64gfort10
F=$HOME/busan_smoke_files/2023capss
B=/home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/EMIS
C=$B/2023capss_cb6
S=$SMK_HOME/subsys/smoke/src/smkinven/smkinven.f
m() { md5sum "$1" | awk '{print $1}'; }
test -f "$S"; test -f "$B/smoke5.2/assigns/ASSIGNS.emf"
# 패치 (원본은 .before_htap_v32로 자동 백업, 이미 패치된 파일은 건너뜀)
python3 "$F/smoke_patch/apply_htap_v32_patches.py" --smkinven "$S" --assigns "$B/smoke5.2/assigns/ASSIGNS.emf"
[ "$(m "$S")" = 23530fc0a55cd5dcdef6c3a314510dc9 ] || { echo 'ERROR: smkinven.f 해시'; exit 1; }
[ "$(m "$B/smoke5.2/assigns/ASSIGNS.emf")" = 058cffcc054f4ad9440b28f24640494e ] || { echo 'ERROR: ASSIGNS.emf 해시'; exit 1; }
# 재컴파일
cd "$SMK_HOME/subsys/smoke/src"
LC_ALL=C make 2>&1 | tee "$SMK_HOME/subsys/smoke/$BIN/make_SMOKEv5.3_fix_smkinven.log"
ls -l --time-style=long-iso "$SMK_HOME/subsys/smoke/$BIN/smkinven"
# 사례 설정·생성 결과 설치
[ -e "$C/scripts/directory_definitions.csh.before_htap" ] || cp -p "$C/scripts/directory_definitions.csh" "$C/scripts/directory_definitions.csh.before_htap"
cp "$F/EMIS/2023capss_cb6/scripts/directory_definitions.csh" "$C/scripts/"
[ "$(m "$C/scripts/directory_definitions.csh")" = 9a5c4c8a894661af75b6e815e77f676f ] || { echo 'ERROR: directory_definitions.csh 해시'; exit 1; }
mkdir -p "$C/scripts/htap" "$C/scripts/logs"
cp "$F/EMIS/2023capss_cb6/scripts/htap/Annual_htap_2023capss_cb6.csh" "$C/scripts/htap/"
chmod +x "$C/scripts/htap/Annual_htap_2023capss_cb6.csh"
cp -r "$HOME/busan_htap_pkg/EMIS/." "$B/"
ls -l "$B/smoke5.2/scripts/emf/smk_ar_gridded_annual_emf.csh"
echo "inputs/htap 파일 수: $(find "$C/inputs/htap" -maxdepth 1 -type f | wc -l) (19 정상)"
)
```

정상 기준: MD5 3개 일치(원본 `smkinven.f`는 `0a1c220d886eb812c76ad028f44fbfe4`), 컴파일 `Error:` 0건, `smkinven` 실행파일 시각 갱신, HTAP 입력 19개. 해시가 다르면 소스 버전·기존 수정·줄바꿈을 먼저 확인하고 억지로 덮어쓰지 않는다. 컴파일에는 `SMK_HOME`, `BIN`이 반드시 필요하다.

## 7. 실행

### 7.1 입력 파일과 생성 파일

**입력 파일** (`EMIS/` 기준, 3개 도메인 공통. 출처의 "생성기"는 5.2, "예제"는 SMOKE 공식 예제)

| 역할 | 파일 | 의미 | 출처 | 프로그램 |
|---|---|---|---|---|
| 배출량 | `2023capss_cb6/inputs/htap/arinv.HTAPv32.<묶음>.lst` | 묶음에 속한 세부 부문별 격자 배출 변수 목록(`#LIST GRID`) | 생성기 | Smkinven |
| | `2023capss_cb6/inputs/htap/htap_v32_2020_<물질>_busan.nc` (9개) | 부산 영역 0.1° 격자 연간 배출 flux(kg m⁻² s⁻¹), 남한 0, 탄소 분리 | 생성기: HTAP_v3.2 2020 | Smkinven |
| 공통 정의 | `ge_dat/invtable_busan_htap_20261110.txt` | 국내 8종 + PEC·POC | 생성기: 국내 INVTABLE + 예제 PEC·POC 줄 | Smkinven, Spcmat |
| | `ge_dat/EDGAR/GRIDMASK_EDGAR_busan_window.ncf`, `geocode1~4_edgar.txt` | 셀별 국가 코드·시간대 (`USE_EXP_GEO_CODES Y`, 국내 COSTCY 대신 사용) | 예제를 영역으로 자름 | Smkinven |
| 격자 | `ge_dat/gridding/griddesc_busan_4domains.txt` | 4개 도메인 격자 | 국내와 공용 | Grdmat, Smkmerge |
| | `met/<GRID>/GRIDCRO2D_<GRID>.*.nc` (`GRID_CRO_2D`) | 모델 격자 위경도 (0.1° 격자 → 모델 격자 배분) | MCIP, `directory_definitions.csh`가 지정 | Grdmat |
| 종분배 | `ge_dat/EDGAR/HTAPv32_profiles/gsref_HTAPv32_busan_20261110.txt` | 세부 부문 → 종분배 프로파일 | 생성기 | Spcmat |
| | `…/gspro_HTAP_CB06_from_2011ei_corrected_20feb2024_nf_v1.txt`, `…/gscnv_edgar_HTAPv3_03Apr2024.txt` | CB6 분배 비율, VOC→TOG 계수 | 예제 | Spcmat |
| 시간배분 | `ge_dat/EDGAR/HTAPv32_profiles/tref_HTAPv32_busan_20261110.txt` | 세부 부문 → 시간 프로파일 | 생성기 | Temporal |
| | `…/HTAP_2011_BaseA_tpro_{monthly,weekly,hourly}_24oct2022_nf_v1` | 월·요일·시간 비율 | 예제 | Temporal |
| | `smoke5.2/scripts/smk_dates/2026/`, `ge_dat/temporal/holidays_korea_…` | 날짜 대응, 공휴일 (`RUN_HOLIDAYS N`) | 국내와 공용 | Temporal |
| 실행 설정 | `2023capss_cb6/scripts/htap/Annual_htap_2023capss_cb6.csh` | 묶음별 입력·설정 (`IMPORT_GRDNETCDF_YN Y`, `NETCDF_POL_UNIT 'kg m-2 s-1'`, `NETCDF_INV_YEAR 2020`, `WEST_HSPHERE N`) | 예제 `Annual_htap_12LISTOS.csh`를 부산용으로 작성 (저장소) | — |
| | `2023capss_cb6/scripts/directory_definitions.csh`, `utils/mcip_period.py` | 경로, MCIP 기간, `GRID_CRO_2D` | 저장소 (국내와 공용) | — |
| | `smoke5.2/scripts/emf/smk_ar_gridded_annual_emf.csh`, `smoke5.2/assigns/ASSIGNS.emf` | 격자 인벤토리 실행 체계 | 예제 (`ASSIGNS.emf`는 패치본) | — |
| 프로그램 | `smkinven`, `grdmat` | | SMOKE 5.3 + `smkinven.f`(6장)·`genagmat.f`(04 §7.1) 패치 | |

**생성 파일**

| 종류 | 위치 | 파일 |
|---|---|---|
| 최종 (병합 전) | `2023capss_cb6/premerged/htap_<묶음>/` | `emis_mole_htap_<묶음>_<날짜>_<GRID>_cmaq_cb6ae7_2023capss_cb6.ncf` (도메인별 2개, 격자별 시간 배출, 가스 mol/s·입자 g/s) |
| 중간 | `2023capss_cb6/intermed/<GRID>/htap_<묶음>/` | 인벤토리, 종분배·격자 행렬, 시간배분, `logs/` |
| 보고서 | `2023capss_cb6/reports/` | `log_analyzer/rep_logs_htap_<묶음>_…level1.csv` 등 |
| 실행 기록 | `2023capss_cb6/scripts/logs/` | `htap_<묶음>_<GRID>.log` |

### 7.2 시험 실행 (27KM ENERGY 한 묶음)

```bash
C="$HOME/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/EMIS/2023capss_cb6"
cd "$C/scripts/htap"
GRID=27KM HTAP_GROUP=ENERGY ./Annual_htap_2023capss_cb6.csh > ../logs/htap_energy_27KM.log 2>&1
grep -nE 'ERROR detected in|Segmentation fault|ERROR ABORT' ../logs/htap_energy_27KM.log
```

정상 기준: `grep` 결과가 없고 `premerged/htap_energy/`에 27KM 파일 2개.

### 7.3 전체 실행 (27·09·03KM × 8개 묶음)

반복은 로그의 명시적인 오류 문구에서만 멈춘다. 종료 코드가 0이 아니어도 오류 문구가 없으면 경고로 표시하고 계속하며, 그 실행은 8장 확인을 반드시 거친다(03·01KM AVIATION 사례, 8.5).

```bash
cd /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/EMIS/2023capss_cb6/scripts/htap
for G in 27KM 09KM 03KM; do
  for g in INTSHIP AVIATION ENERGY INDUSTRY TRANSPORT RESIDENT WASTE AGRICULTURE; do
    GRID=$G HTAP_GROUP=$g ./Annual_htap_2023capss_cb6.csh > ../logs/htap_${g,,}_$G.log 2>&1
    rc=$?
    if grep -Eq 'ERROR detected in|Segmentation fault|ERROR ABORT' "../logs/htap_${g,,}_$G.log"; then
      echo "ERROR: $G $g (exit=$rc) - 로그 확인"; break 2
    fi
    if [ "$rc" -ne 0 ]; then
      echo "WARNING: $G $g (exit=$rc) - 로그 오류 문구 없음, 8장 확인 필요"
    else
      echo "$(date +%H:%M) $G $g 실행 종료 (exit=$rc)"
    fi
  done
done
```

01KM은 실행하지 않는다(8.4).

## 8. 확인

### 8.1 로그·파일 수

```bash
C=/home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/EMIS/2023capss_cb6
for G in 27KM 09KM 03KM; do
  for g in intship aviation energy industry transport resident waste agriculture; do
    e=$(grep -c 'ERROR detected in\|Segmentation fault\|ERROR ABORT' "$C/scripts/logs/htap_${g}_$G.log" 2>/dev/null)
    n=$(find "$C/premerged/htap_$g" -maxdepth 1 -name "emis_mole_htap_${g}_2026*_${G}_*.ncf" 2>/dev/null | wc -l)
    printf '%-5s %-12s 오류 %s  파일 %s\n' "$G" "$g" "${e:-로그없음}" "$n"
  done
done
```

정상 기준: 24줄 모두 `오류 0`, `파일 2`. 2026-11-10~11 결과: 모두 정상.

### 8.2 묶음별 배출 (8월 31일 파일, 25시간·격자 합)

가스 mol/s, 입자 g/s. 물질끼리 더하지 않는다.

```bash
cd /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/EMIS/2023capss_cb6/premerged
python3 - <<'PY'
import glob, netCDF4 as nc, numpy as np
for G in ['27KM','09KM','03KM']:
    print('==',G)
    for g in ['intship','aviation','energy','industry','transport','resident','waste','agriculture']:
        fs=sorted(glob.glob(f'htap_{g}/emis_mole_htap_{g}_*_{G}_*.ncf'))
        if not fs: print(g,'파일 없음'); continue
        with nc.Dataset(fs[0]) as d:
            z={v:float(np.asarray(d[v][:]).sum()) for v in ['NO','SO2','NH3','PEC','POC','TOL'] if v in d.variables}
        print(f'{g:12s} '+'  '.join(f'{k} {v:.3g}' for k,v in z.items()))
PY
```

27KM 기준값 (2026-11-10):

| 묶음 | NO | SO2 | NH3 | PEC | POC | TOL |
|---|---:|---:|---:|---:|---:|---:|
| intship | 3.55e4 | 4.59e3 | 9.34 | 3.5e4 | 1.75e4 | 81.3 |
| aviation | 5.69e3 | 428 | 247 | 1.01e3 | 505 | 1.27 |
| energy | 6.32e4 | 2.26e4 | 2.26e3 | 2.59e3 | 1.85e3 | 42.8 |
| industry | 1.49e5 | 7.49e4 | 1.38e4 | 1.98e5 | 2.12e5 | 7.98e3 |
| transport | 1.18e5 | 2.42e3 | 3.13e3 | 2.03e5 | 8.44e4 | 1.42e3 |
| resident | 1.11e4 | 1.56e4 | 8.12e3 | 2.26e5 | 6.46e5 | 1.57e3 |
| waste | 940 | 408 | 1.91e3 | 4.82e3 | 1.17e4 | 0 |
| agriculture | 1.7e4 | 669 | 4.23e5 | 6.35e4 | 4.55e5 | 199 |

09KM 기준값 (2026-11-11, 괄호는 27KM 대비):

| 묶음 | NO | SO2 | NH3 | PEC | POC |
|---|---:|---:|---:|---:|---:|
| intship | 866 (2.4%) | 121 (2.6%) | 0.236 (2.5%) | 884 (2.5%) | 442 (2.5%) |
| aviation | 55.1 (1.0%) | 3.65 (0.9%) | 2.09 (0.8%) | 8.62 (0.9%) | 4.26 (0.8%) |
| energy | 208 (0.3%) | 200 (0.9%) | 1.44 (0.1%) | 30.9 (1.2%) | 11.2 (0.6%) |
| industry | 1.38e3 (0.9%) | 1.01e3 (1.4%) | 238 (1.7%) | 2.88e3 (1.5%) | 1.66e4 (7.9%) |
| transport | 1.79e3 (1.5%) | 323 (13.4%) | 24.1 (0.8%) | 1.68e3 (0.8%) | 1.57e3 (1.9%) |
| resident | 86.2 (0.8%) | 38.9 (0.2%) | 49.5 (0.6%) | 1.54e3 (0.7%) | 5.66e3 (0.9%) |
| waste | 20.6 (2.2%) | 3.09 (0.8%) | 51.1 (2.7%) | 6.15 (0.1%) | 19 (0.2%) |
| agriculture | 44.4 (0.3%) | 1.59 (0.2%) | 1.41e3 (0.3%) | 160 (0.3%) | 1.11e3 (0.2%) |

09KM에는 중국 본토가 없어 대부분 27KM의 0.1~2.7%다. TRANSPORT SO2 13.4%는 연안 선박(DOMSHIP)이 대한해협·규슈 연안에 있기 때문이고, INDUSTRY POC 7.9%는 북한 남부 산업 부문 몫으로 본다.

### 8.3 남한 제거 확인 (ENERGY, 도시 주변 3×3 격자 NO 25시간 합)

```bash
cd /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/EMIS/2023capss_cb6/premerged/htap_energy
python3 - <<'PY'
import glob, netCDF4 as nc, numpy as np
pts={'27KM':[('서울',90,62),('부산',97,52),('평양',86,68),('베이징',57,73),('상하이',71,37),('도쿄',131,58)],
     '09KM':[('서울',29,59),('부산',50,30),('평양',17,77),('후쿠오카',64,12),('대마도',53,22)]}
for G,cities in pts.items():
    fs=sorted(glob.glob(f'emis_mole_htap_energy_*_{G}_*.ncf'))
    if not fs: print(G,'파일 없음'); continue
    with nc.Dataset(fs[0]) as d: no=np.asarray(d['NO'][:]).sum(axis=(0,1))
    print(G,'  '.join(f'{n} {no[r-2:r+1,c-2:c+1].sum():.4g}' for n,c,r in cities))
PY
```

도시 좌표는 GRIDDESC 기준 1부터 세는 열·행이며, 명령은 그 칸을 가운데로 3×3을 잡는다. 27KM 값은 이전 판 명령(3×3이 한 칸 어긋남)으로 계산한 **과거 참고값**이며, 위 수정된 식으로 다시 산정하기 전까지 최종 합격 판정의 수치 기준으로 사용하지 않는다. 과거 참고값: 27KM 서울 0, 부산 0, 평양 55.81, 베이징 457.8, 상하이 961.2, 도쿄 357.9 / 09KM 서울 0, 부산 0, 평양 51.07, 후쿠오카 0.016(도메인 가장자리), 대마도 1.745. 서울·부산 0, 나머지 양수면 정상이다. 몇 지점 확인만으로 마스크 전체의 완전성을 단정하지 않는다.

### 8.4 도메인별 국외/국내 비율 (03·01KM 포함 여부)

8월 31일 하루, 국내는 면·이동·바다 `premerged` + 점 `inln_mole` 합. 01KM을 판단하려면 01KM도 한 번 실행해야 한다(7.3 반복에 `01KM`을 넣어 시험).

```bash
cd /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/EMIS/2023capss_cb6
python3 - <<'PY'
import glob, netCDF4 as nc, numpy as np
V=['NO','SO2','PEC']
def tot(pat):
    fs=sorted(glob.glob(pat))
    if not fs: return None
    with nc.Dataset(fs[0]) as d: return {v:float(np.asarray(d[v][:]).sum()) if v in d.variables else 0.0 for v in V}
grp=['intship','aviation','energy','industry','transport','resident','waste','agriculture']
for G in ['09KM','03KM','01KM']:
    dom={v:0.0 for v in V}
    for p in [f'premerged/{s}/emis_mole_{s}_20260831_{G}_*.ncf' for s in ['kor_area','kor_mobile','kor_sea']]+[f'smoke_out/2023capss_cb6/{G}/cmaq_cb6ae7/kor_point/inln_mole_kor_point_20260831_{G}_*.ncf']:
        t=tot(p)
        if t: dom={v:dom[v]+t[v] for v in V}
    fr={v:0.0 for v in V}
    for g in grp:
        t=tot(f'premerged/htap_{g}/emis_mole_htap_{g}_20260831_{G}_*.ncf')
        if t: fr={v:fr[v]+t[v] for v in V}
    print(G,'  '.join(f"{v} 국내 {dom[v]:.3g} / 국외 {fr[v]:.3g} ({100*fr[v]/dom[v]:.2f}%)" for v in V if dom[v]>0))
PY
```

2026-11-11 결과와 결정:

| 도메인 | NO 국외/국내 | SO2 | PEC | 국외 상위 묶음 | 결정 |
|---|---:|---:|---:|---|---|
| 09KM | 35.27% | 111.06% | 81.69% | transport, industry, intship | 포함 |
| 03KM | 1.00% | 0.79% | 1.73% | intship(NO 26.9), transport(14.8), energy(2.42) | **포함** — 작지만 영역 안 실제 배출(대한해협·대마도 주변 선박 등)이고, 바깥 도메인 경계조건으로 대신할 수 없음 |
| 01KM | 0% | 0% | 0% | 없음 | **제외** — 영역 안 국외 배출 없음. 국외 영향은 03KM 결과를 경계조건으로 받음 |

#### 01KM 제외 판정 시 파일 미생성과 실제 0 배출 구분

§8.4의 비교 코드는 입력 파일이 없을 때 해당 항목을 0으로 초기화한다. 따라서 **그 표의 0%만으로 국외배출량이 실제 0이라고 입증할 수는 없다.** 2026-11-11 사용자가 확인한 01KM 제외 결정을 기록하되, 새 컴퓨터에서 재현할 때는 다음 검사로 파일 존재 여부와 해당 파일 내 **전체 배출종**의 수치적 0을 별도로 확인한다. 01KM 시험 실행 파일이 없으면 '0'이 아닌 **미검증**으로 판정한다.

```bash
cd /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/EMIS/2023capss_cb6
python3 - <<'PY'
import glob, os, numpy as np
from netCDF4 import Dataset
groups = ['intship','aviation','energy','industry','transport','resident','waste','agriculture']
missing, nonzero, checked = [], [], 0
for g in groups:
    fs = sorted(glob.glob(f'premerged/htap_{g}/emis_mole_htap_{g}_*_01KM_*.ncf'))
    if len(fs) != 2:
        missing.append((g, len(fs)))
        continue
    for fn in fs:
        with Dataset(fn) as ds:
            variables = [v for v in ds.variables if v != 'TFLAG' and ds[v].ndim >= 3 and np.issubdtype(ds[v].dtype, np.number)]
            for v in variables:
                x = np.asarray(ds[v][:])
                checked += 1
                if not np.isfinite(x).all() or np.any(x != 0):
                    nonzero.append((g, os.path.basename(fn), v, float(np.max(np.abs(x)))))
print('검사한 변수-파일 수:', checked)
print('파일 미충족:', missing)
print('0이 아닌 변수 또는 비유한값:', nonzero)
print('01KM 판단:', '0 배출 확인' if not missing and not nonzero and checked else '미검증 또는 비영 배출')
PY
```

이 기준은 이번 2일 시험기간(도메인별 묶음당 2개 파일)에 한정한다. 다른 기간에는 기대 파일 수를 변경해야 한다. 모델 재실행 없이 저장소만 검토한 상태에서는 01KM 파일 존재·전 물질의 0을 독립적으로 재확인하지 않았다.

### 8.5 정상 경고

| 메시지 | 뜻 |
|---|---|
| 로그 분석기 수준 2 `No speciation profiles found for pollutant "PM10"` | PM10은 PM2_5 + PMC로 처리 |
| Smkinven `Resetting negative value of annual "PMC"` | 약 −3×10⁻⁶ t의 반올림 차이 |
| 03·01KM **AVIATION `exit=1`**, 로그 분석기 우선순위 0 `WARNING: All computed values are zero. Nothing to output` (Smkinven) | 영역 안에 국외 항공 배출이 없음. 모든 프로그램 정상 종료, 오류 로그 0, 배출 파일 2개(0 값) — 2026-11-11 확인 |

**AVIATION의 비영 종료코드 1은 자동으로 성공을 의미하지 않는다.** 이 시험에서는 로그의 명시적 오류 0건, 예상 일별 출력파일 2개, 해당 격자의 모든 관련 배출종이 0인 것을 함께 확인한 경우에 한해 조건부 정상으로 판단하였다. 같은 경고가 다른 부문·도메인·입력에서 나타나면 원인을 다시 검증한다.

## 9. 완료 현황

| 단계 | 상태 |
|---|---|
| 3.2 원자료, 5장 생성, 6장 패치·설치 | 완료 (2026-11-10) |
| 27KM 8개 묶음 | 완료 (2026-11-10, 오류 0, 남한 0, PEC·POC 포함) |
| 09KM 8개 묶음 | 완료 (2026-11-11, 오류 0, 서울·부산 0, 평양·대마도·후쿠오카 양수) |
| 03KM 8개 묶음 | 완료 (2026-11-11, 국외/국내 NO 1.00% → 포함) |
| 01KM | 제외 (제공된 시험 결과상 영역 안 국외 0; 새 시스템에서는 §8.4 파일 존재·전 물질 0 검사 필수) |
| 국내·국외·생물성 병합, CMAQ 연계 | 미실행 |

## 부록 A. 실행 중 발생한 문제 기록

| 날짜 | 증상 | 원인 | 조치 |
|---|---|---|---|
| 11-10 | Smkinven `CELLID` 기록 직후 `Segmentation fault` | 격자 NetCDF 경로에서 `NONPOINT` 비초기화, 할당되지 않은 `CMACT`/`CNAICS` 접근 | `smkinven.f` 초기값 `.FALSE.` 패치 후 재컴파일 (6장, [91](91_SMOKE_smkinven_Fix.md)) |
| 11-10 | Grdmat `GRID_CRO_2D` 파일 미발견 | 예제 ASSIGNS의 고정 파일 이름과 실제 MCIP 파일 이름 불일치 | `directory_definitions.csh`에서 실제 파일 지정, `ASSIGNS.emf`는 그 값을 유지하도록 패치 |
| 11-10 | PEC·POC 출력 없음 | 예제 PM2.5 종분배로 탄소가 다른 성분에 섞임 | BC→PEC, OC→POC, PM2.5 잔여분 분리, GSREF·INVTABLE 보완 |
| 11-10 | PEC/POC INVTABLE keep flag 오류 | MOVES 전용 PEC 행을 먼저 선택 | 일반 `PEC PEC`, `POC POC` 행만 채택 |
| 11-10 | 탄소 분리 후 PM2.5가 원자료보다 약 26만 t 큼 | 일부 부문의 BC+OC가 PM2.5 초과 | BC·OC 비례 축소. FUGITIVE 플레어링 BC 축소는 남는 한계 |
| 11-11 | 03·01KM AVIATION `exit=1` | 영역 안 국외 항공 배출 0 → Smkinven 경고를 로그 분석기가 순위 0으로 분류 | 조치 없음 (8.5) |

## 부록 B. 재현 기록 양식

```text
작업일시 / 실행자:
호스트 / OS / Python 및 라이브러리 버전:
SMOKE / CMAQ / I/O API 버전 및 소스 커밋:
GitHub 저장소 커밋 SHA:
HTAP 원본 파일명 및 sha256sum (9개):
CAPSS 원본 파일명 및 sha256sum:
CASE / EMIS / MCIP / GRIDDESC / GRID_CRO_2D 실제 경로:
생성 명령 / 실행 명령 / 종료코드:
도메인 / 묶음 / 기간 / 기대파일 수 / 실제파일 수:
오류 / 남한 마스크(8.3) / 질량 보존(5.3) / 국외·국내 비율(8.4):
수정 전후 소스 diff / 컴파일 로그:
관측된 문제 / 해결 / 잔여 검증 항목:
```

## 10. 검토 근거와 과학적 한계

- 5.3·8장 수치는 사용자 제공 2026-11-10~11 Linux 실행 기록이다. 다른 컴퓨터에서 생성부터 실행까지 독립 재현한 기록은 부록 B 양식으로 따로 남긴다.
- **남한 제거:** CAPSS 1km 셀이 닿는 0.1° 셀 전체를 0으로 하므로 해안·접경의 국외 배출 일부도 빠질 수 있다. 남한 중복 제거와 국외 배출 보존은 서로 다른 검증 목표다.
- **BC·OC 비례 축소:** PM2.5 총량은 보존하지만 성분별 질량은 원자료와 다르다.
- **프로파일:** FUGITIVE·SOLVENTS의 INDUSTRY 대체와 예제 시간 프로파일 사용은 잠정이다(03 §7 최신화 대상).
- 로그 오류 0건만으로 질량 보존이나 CMAQ 적용 성공을 선언하지 않는다. 병합·CMAQ 연계는 별도로 검증한다.

관련 문서: [03 배출량 개선 계획](03_SMOKE_Emission_Improvement_Plan.md) §4.9·§8 · [04 국내 배출량 가이드](04_SMOKE_Busan_Case_Run_Guide.md) · [91 Smkinven 수정](91_SMOKE_smkinven_Fix.md) · HTAP_v3.2 [JRC EDGAR](https://edgar.jrc.ec.europa.eu/dataset_htap_v32), [Zenodo](https://zenodo.org/records/17086684)