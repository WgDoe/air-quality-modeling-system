# CMAQ 모델링 시스템 SMOKE 부산 사례 실행 가이드

> **문서 순서:** 01 설치 → 02 기존 체계 분석 → 03 배출량 개선 계획 → 04 부산 사례 실행. [SMOKE 문서 목차](00_README_First.md)를 확인하세요.

## 1. 목적

부산 사례(`CASES/BUSAN/TEST_20260901`)의 배출량을 SMOKE 5.3으로 산정하는 절차를 다른 컴퓨터에서 처음부터 그대로 재현할 수 있도록 기록한다. 국내 배출량은 CAPSS 2023 1km 격자 자료, 배출 시나리오 이름은 `2023capss_cb6`이다. 자료 선정과 변환 규칙의 근거는 [03 배출량 개선 계획](03_SMOKE_Emission_Improvement_Plan.md)에 있다.

실행 순서:

```text
5장  폴더 만들기
  ↓
6장  입력 생성 (CAPSS 2023 원자료 → 생성기)
  ↓
7장  입력 설치 (설치 스크립트)
  ↓
8장  실행 (국내 점 onetime → 국내 점 daily → 국내 면 → 국내 이동 → 바다)
```

현재 상태(2026-10-22 제공 작업 기록 기준): **6~7장 완료, 8.1 국내 점 onetime 09KM 정상 완료(보고서 합계가 생성 값과 일치).** 8.2 이후는 미실행. 이는 제공받은 문서의 기록이며 이번 GitHub 수정에서 Linux 서버의 실행 로그를 직접 열거나 재실행하지 않았다.

## 2. 구축 환경

- OS: Rocky Linux 9.8, 사용자 `woogon`, 프로젝트 루트 `/home/woogon/CMAQ_MODEL`
- 메모리: 약 7.2 GB (입력 생성에 약 1.3 GB 사용)
- 파이썬: 시스템 Python 3.9, 사용자 설치 모듈 `pandas`·`numpy`·`openpyxl`·`pyproj`
- 셸: 명령 입력은 bash, SMOKE 실행 스크립트는 csh

선행 문서:

- [01 SMOKE 설치 가이드](01_SMOKE_Installation_Guide.md) — SMOKE 5.3 컴파일, 공식 예제(`CASES/SMOKE_TEST/smoke_example_case_v3`) 압축 해제·검증
- [MCIP 구축 가이드](../mcip/MCIP_Installation_Guide.md) — `CASES/BUSAN/TEST_20260901/MCIP/{27KM,09KM,03KM,01KM}`

이 문서는 위 문서의 작업이 끝나 있다고 가정한다.

## 3. 필요한 파일

### 3.1 저장소 파일

저장소를 홈 폴더에 받는다.

```bash
cd ~
git clone https://github.com/WgDoe/air-quality-modeling-system.git
```

이미 받았다면 `cd ~/air-quality-modeling-system && git pull`로 최신화한다. 아래에서 쓰는 파일은 모두 `docs/smoke/files/busan/` 아래에 있다.

| 파일 | 용도 |
|---|---|
| `2023capss/generators/make_busan_2023_domestic_inputs.py` | 국내 입력 생성기 (6장) |
| `2023capss/reference/code_list_2023.xlsx`, `code_list_2017.xlsx` | CAPSS 코드리스트 (지역·SCC·연료) |
| `2023capss/reference/4_*_Temporal_Reference_Profile.txt`, `5_*_Speciation_Reference_Profile.txt`, `9_Asia_TimeZone.txt`, `9_Bio_TimeZone.txt` | 기존 운영체계(SMOKE 2.7, 2020년 버전) 시간·종분배 참조, 국외·생물성 지역 코드 |
| `2023capss/install_busan_2023capss.sh` | 설치 스크립트 (7장) |
| `2023capss/EMIS/2023capss_cb6/scripts/` | 실행 스크립트·설정 (8장) |
| `griddesc_busan_4domains.txt` | 4개 도메인 격자 (MCIP GRIDDESC 합본) |
| `invtable_busan_2017capss_20261021.txt` | 오염물질 8종 정의 (예제 INVTABLE 8줄) |
| `holidays_korea_2012_2026_20261021.txt` | 한국 공휴일 |
| `temporal/tpro_{monthly,weekly,hourly}_busan_2020ver_*.csv` | 월·요일·시간 배분 프로파일 (시간은 UTC) |
| `smk_dates/2026/` | 2026년 날짜 파일 12개 |

**참조파일 등록 완료:** 코드리스트 XLSX 2개와 기존 참조 TXT 6개는 `2023capss/reference/`에 등록되어 있다(2026-10-22). 이 파일이 없으면 6.2의 생성기 명령이 동작하지 않으므로 `git pull` 후 8개가 모두 있는지 확인한다.

### 3.2 CAPSS 2023 원자료 (저장소에 없음)

국가미세먼지정보센터 CAPSS 2023 1km 격자 배출량(쉼표 구분, kg/yr, TM 좌표)의 **전국 파일 4개**가 필요하다. 시도별 파일은 쓰지 않는다.

| 생성기가 읽는 이름 | 원자료 | 확인 값 |
|---|---|---|
| `point.txt` | 점오염원 전국 파일 (예: `점오염원(2023_전국)_1_기본.txt`) | 14,437줄 |
| `area.txt` | 면오염원 압축 안의 전국 파일 (`전국` + `a`) | 9,615,471줄 + 머리줄 17 |
| `mobile.txt` | 이동오염원 압축 안의 전국 파일 (`전국` + `m`) | 7,612,113줄 + 머리줄 |
| `sea.txt` | 바다 파일 (예: `바다m(2023).txt`) | 820,602줄 |

```bash
CAPSS=/home/woogon/CMAQ_MODEL/DATA/EMIS/CAPSS2023
mkdir -p "$CAPSS"
# 위 4개 원자료를 $CAPSS에 복사한 뒤, 실제 파일 이름에 맞게 링크를 만든다
cd "$CAPSS"
ln -sf "<점오염원 전국 파일>"  point.txt
ln -sf "<면오염원 전국 파일>"  area.txt
ln -sf "<이동오염원 전국 파일>" mobile.txt
ln -sf "<바다 파일>"          sea.txt
wc -l point.txt sea.txt
```

### 3.3 SMOKE 공식 예제에서 가져오는 파일

설치 스크립트(7장)가 `CASES/SMOKE_TEST/smoke_example_case_v3`에서 자동으로 복사한다: 실행 체계 `smoke5.2/`, 종분배 5개(`gscnv_SPECIATE_5_3…`, `gspro_static_cmaq…`, `gspro_PM2_5_AE6…`, `gspro_CB6R3_AE7_criteria…`, `gspro_nox_hono…`), 굴뚝 2개(`pelvconfig_elevate_everything…`, `pstk…`), 보고서(`repconfig/`, `orisdesc…`, `naicsdesc…`).

## 4. 공통 실행 규칙

- 모든 명령은 bash에서 입력한다. SMOKE 실행 스크립트(`*.csh`)는 `GRID=09KM ./스크립트` 형태로 bash에서 부른다.
- 도메인은 `GRID`(27KM·09KM·03KM·01KM)로 고른다. 각 부문을 09KM로 먼저 통과시킨 뒤 나머지로 넓힌다.
- 실행 화면은 `tee`로 `EMIS/2023capss_cb6/scripts/logs/`에 남긴다. 프로그램 로그는 `EMIS/2023capss_cb6/intermed/<GRID>/<부문>/logs/`, 보고서는 `EMIS/2023capss_cb6/reports/`에 생긴다.
- 배출량 단위는 SMOKE 기준 short ton(907.18474 kg)이다. 원자료(kg) 합계와 비교할 때 이 값으로 나눈다.

## 5. 폴더 만들기

```bash
B=/home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/EMIS
mkdir -p "$B"/ioapi \
         "$B"/ge_dat/{gridding/surrogates,speciation,temporal,point,beis,smkreport} \
         "$B"/2023capss_cb6/inputs \
         "$B"/2023capss_cb6/scripts/{point,nonpoint,logs} \
         "$B"/2023capss_cb6/{intermed,reports,logs}
ln -sfn ../MCIP "$B"/met
ls -l "$B"; ls "$B"/met
```

`met`가 `../MCIP`를 가리키고 `01KM 03KM 09KM 27KM`이 보이면 된다. 설치 후 구조는 다음과 같다.

```text
CASES/BUSAN/TEST_20260901/EMIS/
├── met -> ../MCIP
├── smoke5.2/                        # 예제 실행 체계 (7장에서 복사)
│   └── scripts/smk_dates/2026/
├── ge_dat/                          # 공통 입력
│   ├── costcy_busan_2023capss_20261022.txt
│   ├── invtable_busan_2017capss_20261021.txt
│   ├── gridding/   griddesc_busan_4domains.txt, srgdesc_kor_2023capss_<GRID>_20261022.txt,
│   │               agref_kor_nonpoint_2023capss_20261022.txt,
│   │               surrogates/kor_2023capss_<GRID>/srg_{kor_area,kor_mobile,kor_sea}_2023capss_<GRID>.txt
│   ├── temporal/   tpro_*, tref_kor_{point,nonpoint}_2023capss_20261022.csv, holidays_*
│   ├── speciation/ gsref_kor_{point,nonpoint}_2023capss_20261022.csv, 예제 gscnv·gspro
│   ├── point/      예제 pelvconfig·pstk
│   └── smkreport/  sccdesc_busan_2023capss_20261022.txt, 예제 repconfig/
└── 2023capss_cb6/
    ├── inputs/{kor_point,kor_area,kor_mobile,kor_sea}/   FF10 인벤토리
    ├── scripts/    directory_definitions.csh, run_settings.txt, point/, nonpoint/, logs/
    ├── intermed/   (실행 시 생성)
    └── reports/    (실행 시 생성)
```

## 6. 입력 생성

### 6.1 파이썬 모듈 설치

```bash
pip3 install --user pandas numpy openpyxl pyproj
python3 -c "import pandas, numpy, openpyxl, pyproj; print('ok')"
```

### 6.2 생성기 실행

생성기 결과를 설치용 패키지 폴더 `~/busan_2023capss_pkg`에 바로 만든다.

```bash
REPO=$HOME/air-quality-modeling-system
F=$REPO/docs/smoke/files/busan
PKG=$HOME/busan_2023capss_pkg
python3 "$F"/2023capss/generators/make_busan_2023_domestic_inputs.py \
  --capss    /home/woogon/CMAQ_MODEL/DATA/EMIS/CAPSS2023 \
  --code2017 "$F"/2023capss/reference/code_list_2017.xlsx \
  --code2023 "$F"/2023capss/reference/code_list_2023.xlsx \
  --legacy   "$F"/2023capss/reference \
  --out      "$PKG" 2>&1 | tee ~/busan_generate.log
```

마지막 줄이 `done`이면 된다. 소요 시간은 장비와 원자료에 따라 달라진다.

### 6.3 생성 결과 확인

```bash
cat "$PKG"/EMIS/2023capss_cb6/inputs/generation_summary_20261022.csv | grep -E "FF10 lines|NOX"
head -2 "$PKG"/EMIS/ge_dat/smkreport/sccdesc_busan_2023capss_20261022.txt
```

| 부문 | FF10 줄 | NOx (short ton/yr) |
|---|---:|---:|
| kor_point | 89,319 | 201,410 |
| kor_area | 145,564 | 139,736 |
| kor_mobile | 163,810 | 459,587 |
| kor_sea | 63 | 90,191 |

`sccdesc` 첫 줄은 `#DELIMITED`여야 한다.

### 6.4 공통 입력·실행 스크립트를 패키지에 넣기

```bash
mkdir -p "$PKG"/EMIS/ge_dat/gridding "$PKG"/EMIS/ge_dat/temporal "$PKG"/EMIS/smoke5.2/scripts/smk_dates
cp "$F"/griddesc_busan_4domains.txt           "$PKG"/EMIS/ge_dat/gridding/
cp "$F"/invtable_busan_2017capss_20261021.txt "$PKG"/EMIS/ge_dat/
cp "$F"/holidays_korea_2012_2026_20261021.txt "$PKG"/EMIS/ge_dat/temporal/
cp "$F"/temporal/tpro_*.csv                   "$PKG"/EMIS/ge_dat/temporal/
cp -r "$F"/smk_dates/2026                     "$PKG"/EMIS/smoke5.2/scripts/smk_dates/
cp -r "$F"/2023capss/EMIS/.                   "$PKG"/EMIS/
cp "$F"/2023capss/install_busan_2023capss.sh "$PKG"/
find "$PKG" -type f | wc -l
```

> 참고: 같은 내용을 묶은 설치 ZIP(`busan_2023capss_full_setup_20261022.zip`)이 있으면 6장 대신 `unzip -o <ZIP> -d ~/busan_2023capss_pkg`로 패키지 폴더를 만들 수 있다.

## 7. 입력 설치

```bash
bash ~/busan_2023capss_pkg/install_busan_2023capss.sh 2>&1 | tee ~/busan_install.log
```

설치 스크립트가 하는 일: 폴더·`met` 링크 확인 → 예제 `smoke5.2/` 복사(없을 때만) → 패키지 `EMIS/` 설치 → 예제 종분배·굴뚝·보고서 파일 복사 → 이전 시험 결과 삭제(`2023capss_cb6/intermed/09KM/kor_point`, `inputs/asia`) → 실행 스크립트가 참조하는 파일 점검.

정상 기준:

- `all referenced files exist (5 scripts x 4 domains)`
- `ok` 5줄 (`smk_pt_annual_onetime_emf.csh`, `smk_pt_annual_byday_emf.csh`, `smk_ar_annual_emf.csh`, `directory_definitions.csh`, `run_settings.txt`)
- 대리자료 폴더 4개 (01KM 32M, 03KM 43M, 09KM 24M, 27KM 7.0M)와 FF10 4개

> **주의:** 설치 스크립트는 `2023capss_cb6/intermed/09KM/kor_point`를 지운다. 이미 실행한 결과를 보존하려면 설치 전에 백업한다. **특히 8.1 onetime 완료 이후 설치 스크립트를 그대로 재실행해서는 안 된다.**

## 8. 실행

공통 확인 명령(부문 이름 `S`와 실행 단위 `T`만 바꿔 쓴다):

```bash
C=/home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/EMIS/2023capss_cb6
S=kor_point; T=onetime
L="$C"/intermed/09KM/"$S"/logs
grep -l "Normal Completion" "$L"/*.log
grep -l -i "ERROR ABORT\|abnormal" "$L"/*.log
cat "$C"/reports/log_analyzer/rep_logs_"$S"_2023capss_cb6_09KM_*"$T"*level1.csv
```

### 8.1 국내 점 onetime

Smkinven(인벤토리) → Spcmat(종분배) → Grdmat(격자 배정) → Smkreport(보고서) → Elevpoint(inline 대상 지정).

```bash
cd /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/EMIS/2023capss_cb6/scripts/point
GRID=09KM ./Annual_kor_point_onetime_2023capss_cb6.csh 2>&1 | tee ../logs/kor_point_onetime_09KM.log
```

정상 기준: 프로그램 로그 총 6개(`smkinven`, `spcmat`, `grdmat`, `smkreport` 2개, `elevpoint`) 모두 `Normal Completion`, 오류 로그 없음. `reports/inv/rep_kor_point_2023capss_cb6_inv_state.txt` 17개 시도 합계가 6.3의 kor_point 값과 같음.

2026-10-22 제공 결과: 정상 완료. 시도 합계 CO 347,311 / NOx 201,410 / VOC 221,154 / NH3 25,362 / SO2 106,298 / PM2.5 9,071 short ton으로 생성 값과 일치. NOx 종분배 NO 181,269 + NO2 18,530 + HONO 1,611.

> 참고: 제공 로그상 경고 `No speciation profiles found for pollutant "PM10"`, `Records in GSCNV file for pollutant "EVP__VOC" ignored`, `Description of NAICS`, `No grouping criteria in PELVCONFIG`, `Missing average day emissions`가 남아 있다. 정상 종료 여부와 별개로 CMAQ 기여율·오염물질 정확도 관점에서 이 경고의 영향은 추후 확인해야 한다.

### 8.2 국내 점 daily

Temporal(연간→시간, UTC) → Smkmerge(굴뚝별 시간 배출, CMAQ inline 파일). 2026년 9월 30일분.

```bash
cd /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/EMIS/2023capss_cb6/scripts/point
GRID=09KM ./Annual_kor_point_daily_2023capss_cb6.csh 2>&1 | tee ../logs/kor_point_daily_09KM.log
find /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/EMIS/2023capss_cb6 -name "inln*kor_point*" | wc -l
```

### 8.3 국내 면

```bash
cd /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/EMIS/2023capss_cb6/scripts/nonpoint
GRID=09KM ./Annual_kor_area_2023capss_cb6.csh 2>&1 | tee ../logs/kor_area_09KM.log
```

### 8.4 국내 이동

```bash
cd /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/EMIS/2023capss_cb6/scripts/nonpoint
GRID=09KM ./Annual_kor_mobile_2023capss_cb6.csh 2>&1 | tee ../logs/kor_mobile_09KM.log
```

### 8.5 바다

```bash
cd /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/EMIS/2023capss_cb6/scripts/nonpoint
GRID=09KM ./Annual_kor_sea_2023capss_cb6.csh 2>&1 | tee ../logs/kor_sea_09KM.log
```

### 8.6 나머지 도메인

8.1~8.5를 `GRID=27KM`, `GRID=03KM`, `GRID=01KM`으로 반복한다.

## 9. 완료 현황

| 단계 | 상태 (2026-10-22 제공 기록) |
|---|---|
| 5장 폴더 | 완료 |
| 6장 입력 생성 | 완료 |
| 7장 입력 설치 | 완료 |
| 8.1 국내 점 onetime 09KM | 완료, 합계 일치 |
| 8.2 국내 점 daily 09KM | 미실행 |
| 8.3~8.5 국내 면·이동·바다 09KM | 미실행 |
| 8.6 27·03·01KM | 미실행 |
| 국외(HTAP v3.1)·생물성·병합 | 미착수 ([03 개선 계획 §5](03_SMOKE_Emission_Improvement_Plan.md)) |

## 부록 A. 실행 중 발생한 문제 기록

| 날짜 | 증상 | 원인 | 조치 |
|---|---|---|---|
| 10-22 | 국내 점 형식 시험(Smkinven만 실행)에서 Smkreport `input file not found: PSSUP` | Spcmat를 꺼서 종분배 보조 파일이 없었음 | 전체 실행(8.1)에서 해소 |
| 10-22 | Smkinven 경고 `Missing control efficiency` 반복 | FF10 저감효율 칸이 비어 있음 | 생성기에서 저감효율 `0` 기입 |
| 10-22 | 높이 0.1~0.4 m 굴뚝 69줄 `Height < min` | 원자료 값이 SMOKE 하한 0.5 m보다 작음 | 조치 없음 (SMOKE가 0.5 m로 조정, NOx 28.7 t) |
| 10-22 | 8.1에서 Smkreport `Missing file format header in the SCC description file` | SMOKE 5.3 `lib/rdsccdsc.f`는 SCC 이름 파일 첫 줄에 `#DELIMITED` 또는 `#FIXED`를 요구 | 생성기에 `#DELIMITED` 추가. 이전 생성본은 `sed -i '1i #DELIMITED' <sccdesc 파일>` |

## 10. 검토 근거 및 관련 문서

- 생성 결과는 작성 환경에서 생성기를 실행해 확인했다. 8.1 결과는 **사용자가 제공한 Linux 실행·보고 기록**으로 확인했다. 이 GitHub 수정 과정에서 실제 실행 로그 파일을 직접 재확인하지 않았다.
- [03 배출량 개선 계획](03_SMOKE_Emission_Improvement_Plan.md) §4 — 단위, SCC10·연료 번호, 참조 보완, 굴뚝 보완, 대리자료 규칙
- [01 SMOKE 설치 가이드](01_SMOKE_Installation_Guide.md) §10 — 공식 예제 실행 구조
- [02 기존 체계 분석](02_Legacy_SMOKE27_Emission_Processing.md) — `reference/` 파일의 출처

## 부록 B. 공통 입력 검증 기준 (이전 작업에서 계승)

기존 CAPSS 2017 기반 공통 입력 준비에서 2023에도 유효한 기준만 계승한다. 2017 국내 면 FF10·해상 surrogate와 미실행 명령은 현재 단계의 실행 지침으로 사용하지 않는다.

| 파일·설정 | 2023 적용·검증 포인트 |
|---|---|
| `GRIDDESC` | MCIP와 27KM/09KM/03KM/01KM 격자명·원점·크기·행열 일치 |
| `COSTCY` | 2023 신규 `costcy_busan_2023capss_20261022.txt` 사용. 지역코드 이름 5–24열, 국가 26열, 시도 27–28열, 시군구 29–31열, 시간대 40–42열 |
| 시간배분 | 한국 지역코드는 GMT, 시간 프로파일은 UTC 전환본. KST와 혼용 금지 |
| 공휴일 | `holidays_korea_2012_2026_20261021.txt`의 2026 법정 공휴일·노동절 포함 여부 공식 검증 필요 |
| 날짜 파일 | `Date, aveday_N, aveday_Y, mwdss_N, mwdss_Y, week_N, week_Y, all` 8열, 대표일 파생 규칙은 별도 QA |
| `INVTABLE` | 이름이 2017인 파일을 CO, NOX, VOC, NH3, SO2, PM10, PM2_5, PMC 8종에 재사용. `PMC=PM10-PM2_5` 호환 확인 |
| 예제 라벨 | `smoke5.2` 디렉터리명, `MODEL_LABEL SMOKE5.2`와 `EMF_AQM CMAQ v5.2`는 예제 레이블이며 실제 SMOKE 바이너리는 5.3 |
| 로그 설정 | `EMF_LOGNAME`에 `EMF_SCRIPTNAME` 절대경로가 중복될 수 있어 실제 실행 전 점검 |

