# CMAQ 모델링 시스템 SMOKE 부산 사례 실행 가이드

> **문서 순서:** 01 설치 → 02 기존 체계 분석 → 03 배출량 개선 계획 → 04 부산 사례 실행. [SMOKE 문서 목차](00_README_First.md)를 확인하세요.

> **저장소 파일 검증 주의 (2026-10-24):** 이 문서는 2026-10-23 작성 환경의 실행 결과와 수정 예정 스크립트를 기록한 것이다. 현재 GitHub `main`에는 `2023capss/file_list.txt`, `scripts/utils/mcip_period.py`, `EMIS/smoke5.2/scripts/run/set_days_v5.csh`가 아직 등록되지 않았으며, 저장된 생성기와 실행 스크립트도 아래에서 설명한 CAPSS 원본 ZIP 자동선택·MCIP 기간 자동설정 버전이 아니다. 따라서 **3.1절의 37개 선택 다운로드 및 6~8장의 최신 재현 절차는 현 저장소만으로 실행할 수 없다.** 해당 파일들을 검증·등록하기 전에는 이 절차를 실행하지 말고, 기존 성공한 서버 환경의 설정과 결과를 보존한다. 특히 6.2절의 `rm -rf "$PKG"`, 7장 설치 스크립트, 8.0절의 결과 삭제 명령을 기존 CASE에서 실행하지 않는다.

## 1. 목적

부산 사례(`CASES/BUSAN/TEST_20260901`)의 국내 배출량을 SMOKE 5.3으로 산정하는 절차를 다른 컴퓨터에서 처음부터 그대로 재현할 수 있도록 기록한다. 국내 배출량은 CAPSS 2023 1km 격자 자료, 배출 시나리오 이름은 `2023capss_cb6`, 도메인은 27·09·03·01KM이다. 자료 선정과 변환 규칙의 근거는 [03 배출량 개선 계획](03_SMOKE_Emission_Improvement_Plan.md)에 있다.

실행 순서:

```text
3장  필요한 파일 준비 (저장소에서 필요한 파일만 받기, CAPSS 원본 복사)
  ↓
5장  폴더 만들기
  ↓
6장  입력 생성 (CAPSS 원본 → 생성기 → 설치 패키지)
  ↓
7장  입력 설치 (설치 스크립트)
  ↓
8장  실행 (기간은 MCIP에서 자동 설정)
     8.1 국내 점 → 8.2 국내 면 → 8.3 국내 이동 → 8.4 바다   (각 4개 도메인)
```

현재 상태(2026-10-23): **5~7장 완료, 8.1 국내 점·8.2 국내 면 4개 도메인 정상 완료.** 8.3부터 진행 중.

## 2. 구축 환경

- OS: Rocky Linux 9.8, 사용자 `woogon`, 프로젝트 루트 `/home/woogon/CMAQ_MODEL`
- 메모리: 약 7.2 GB (입력 생성에 약 1.3 GB 사용)
- 파이썬: 시스템 Python 3.9, 모듈 `pandas`·`numpy`·`openpyxl`·`pyproj`
- NetCDF 도구: `ncdump` (MCIP 기간 읽기에 사용)
- 셸: 명령 입력은 bash, SMOKE 실행 스크립트는 csh

선행 문서 (이 문서는 아래 작업이 끝났다고 가정한다):

- [01 SMOKE 설치 가이드](01_SMOKE_Installation_Guide.md) — SMOKE 5.3 컴파일, 공식 예제(`CASES/SMOKE_TEST/smoke_example_case_v3`) 압축 해제·검증
- [MCIP 구축 가이드](../mcip/MCIP_Installation_Guide.md) — `CASES/BUSAN/TEST_20260901/MCIP/{27KM,09KM,03KM,01KM}`

## 3. 필요한 파일

### 3.1 저장소에서 필요한 파일만 받기

> **현재 미작동:** 아래 명령의 첫 `curl` 대상인 `file_list.txt`가 `main`에 없어 다운로드가 실패한다. 필요한 파일 목록과 새 스크립트를 저장소에 등록한 뒤 사용해야 한다.


저장소 전체를 받지 않고, 이 절차에 필요한 37개 파일만 GitHub에서 내려받아 `~/busan_smoke_files`에 저장소와 같은 폴더 구조로 둔다. 받을 파일 목록은 저장소의 `docs/smoke/files/busan/2023capss/file_list.txt`에 있다.

```bash
F=$HOME/busan_smoke_files
RAW=https://raw.githubusercontent.com/WgDoe/air-quality-modeling-system/main/docs/smoke/files/busan
mkdir -p "$F"
curl -fsSL -o "$F"/file_list.txt "$RAW"/2023capss/file_list.txt
while read -r p; do
  mkdir -p "$F/$(dirname "$p")"
  curl -fsSL -o "$F/$p" "$RAW/$p" || echo "FAIL $p"
done < "$F"/file_list.txt
find "$F" -type f | wc -l
```

정상 기준: `FAIL` 줄이 없고 마지막 숫자가 `38`(목록 파일 포함). 파일이 바뀌었을 때는 같은 명령을 다시 실행하면 최신 파일로 덮어쓴다.

받는 파일 (`~/busan_smoke_files/` 기준, 저장소의 `docs/smoke/files/busan/`과 같은 구조):

| 파일 | 용도 |
|---|---|
| `2023capss/generators/make_busan_2023_domestic_inputs.py` | 국내 입력 생성기 (6장) |
| `2023capss/reference/code_list_2023.xlsx`, `code_list_2017.xlsx` | CAPSS 코드리스트 (지역·SCC·연료) |
| `2023capss/reference/4_Point_Temporal_Reference_Profile.txt`, `4_Area_Temporal_Reference_Profile.txt`, `5_Point_Speciation_Reference_Profile.txt`, `5_Area_Speciation_Reference_Profile.txt`, `9_Asia_TimeZone.txt`, `9_Bio_TimeZone.txt` | 기존 운영체계(SMOKE 2.7, 2020년 버전) 시간·종분배 참조, 국외·생물성 지역 코드 |
| `2023capss/install_busan_2023capss.sh` | 설치 스크립트 (7장) |
| `2023capss/EMIS/2023capss_cb6/scripts/` | 실행 스크립트 5개, `directory_definitions.csh`, `run_settings.txt`, `utils/mcip_period.py` |
| `2023capss/EMIS/smoke5.2/scripts/run/set_days_v5.csh` | 예제 날짜 결정 스크립트의 기간 패치본 |
| `griddesc_busan_4domains.txt` | 4개 도메인 격자 |
| `invtable_busan_2017capss_20261021.txt` | 오염물질 8종 정의 |
| `holidays_korea_2012_2026_20261021.txt` | 한국 공휴일 |
| `temporal/tpro_{monthly,weekly,hourly}_busan_2020ver_*.csv` | 월·요일·시간 배분 프로파일 (시간은 UTC) |
| `smk_dates/2026/` | 2026년 날짜 파일 12개 |
| `2023capss/file_list.txt` | 위 파일 목록 (내려받기용) |


### 3.2 CAPSS 2023 원본 (저장소에 없음)

국가미세먼지정보센터 CAPSS 2023 1km 격자 배출량(쉼표 구분, kg/yr, TM 좌표). 용량이 커서 저장소에 넣지 않았고 **작성자 PC에 보관**되어 있다. 아래 원본을 **이름과 내용을 바꾸지 말고** 원본 폴더에 그대로 복사한다. 압축도 풀지 않는다.

```text
/home/woogon/CMAQ_MODEL/DATA/EMIS/CAPSS2023/
```

| 원본 | 구성 | 크기 |
|---|---|---|
| `점오염원(2023_전국)_1_기본.txt` | 전국 점오염원 1개 파일 (14,437줄) | 1,976,005 B |
| `면오염원(2023).zip` | 시도별 17개 `<시도>a(2023).txt` + 전국 `전국a(2023).txt` | 397,553,412 B |
| `이동오염원(2023).zip` | 시도별 17개 `<시도>m(2023).txt` + 전국 `전국m(2023).txt` | 354,093,747 B |
| `바다m(2023).txt` | 바다 1개 파일 (지역 `9010000000`) | 84,555,108 B |

생성기는 이 폴더를 읽어 필요한 파일을 스스로 고른다.

- 점: 이름에 `점오염원`이 들어간 파일 / 바다: 이름에 `바다`가 들어간 파일
- 면: `면오염원*.zip` 안의 파일 또는 `*a(2023).txt` / 이동: `이동오염원*.zip` 안의 파일 또는 `*m(2023).txt`(바다 제외)
- 면·이동은 전국 파일(가장 큰 파일 = 나머지 합)이 있으면 그것만 읽고, 없으면 시도 파일을 모두 읽는다. 압축을 풀어 시도 파일만 넣어 두어도 된다.

```bash
CAPSS=/home/woogon/CMAQ_MODEL/DATA/EMIS/CAPSS2023
mkdir -p "$CAPSS"
# PC에서 SFTP로 위 4개 원본을 $CAPSS 에 올린 뒤
ls -l "$CAPSS"
```

정상 기준: 4개 파일이 위 표의 크기로 보인다. 같은 폴더에 다른 CAPSS 파일(예: 점오염원 식별 파일)을 두지 않는다.

### 3.3 SMOKE 공식 예제에서 가져오는 파일

설치 스크립트(7장)가 `CASES/SMOKE_TEST/smoke_example_case_v3`에서 자동으로 복사한다: 실행 체계 `smoke5.2/`, 종분배 5개(`gscnv_SPECIATE_5_3_fromS2S_20230911_16jun2025_v1.txt`, `gspro_static_cmaq_21feb2012_v13.txt`, `gspro_PM2_5_AE6_Spec_5_3_S2S_20230911_01nov2023_v0.txt`, `gspro_CB6R3_AE7_criteria_Spec_5_3_S2S_20230911_01nov2023_v0.txt`, `gspro_nox_hono_pf4_06aug2008_v0.txt`), 굴뚝 2개(`pelvconfig_elevate_everything_17apr2020_v0.txt`, `pstk_13nov2018_v1.txt`), 보고서(`repconfig/`, `orisdesc_04dec2006_v0.txt`, `naicsdesc_20220222_29feb2024_nf_v1.txt`).

## 4. 공통 실행 규칙

- 명령은 bash에서 입력한다. SMOKE 실행 스크립트(`*.csh`)는 `GRID=09KM ./스크립트` 형태로 부른다. 도메인은 `GRID`(27KM·09KM·03KM·01KM)로 고른다.
- **배출량 기간은 MCIP에서 자동으로 정해진다.** `scripts/directory_definitions.csh`가 `scripts/utils/mcip_period.py`로 `MCIP/<GRID>/METCRO2D*`의 시작 시각·시간 수를 읽어 `RUN_SDATE`, `RUN_EDATE`, `BASE_YEAR`, `RUN_MONTHS`를 정하고, 패치한 `set_days_v5.csh`가 그 밖의 날짜를 건너뛴다. 이번 사례 MCIP는 2026-08-31 01시 ~ 09-02 00시(UTC, 48시간)이므로 배출 파일은 **8월 31일·9월 1일 2개**(각 0시~다음날 0시, 25시간)이다. 실행 화면에 `Run period from MCIP: 2026243 - 2026244 (months: 8 9)`가 나온다.
- 실행 화면은 `tee`로 `EMIS/2023capss_cb6/scripts/logs/`에 남긴다. 프로그램 로그는 `EMIS/2023capss_cb6/intermed/<GRID>/<부문>/logs/`, 보고서는 `EMIS/2023capss_cb6/reports/`에 생긴다.
- 배출량 단위는 SMOKE 기준 short ton(907.18474 kg)이다.

## 5. 폴더 만들기

```bash
B=/home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/EMIS
mkdir -p "$B"/ioapi \
         "$B"/ge_dat/{gridding/surrogates,speciation,temporal,point,beis,smkreport} \
         "$B"/2023capss_cb6/inputs \
         "$B"/2023capss_cb6/scripts/{point,nonpoint,utils,logs} \
         "$B"/2023capss_cb6/{intermed,reports,logs}
ln -sfn ../MCIP "$B"/met
ls -l "$B"; ls "$B"/met
```

정상 기준: `met -> ../MCIP`, `ls "$B"/met`에 `01KM 03KM 09KM 27KM`.

설치 후 구조:

```text
CASES/BUSAN/TEST_20260901/EMIS/
├── met -> ../MCIP
├── smoke5.2/                        예제 실행 체계 (scripts/run/set_days_v5.csh는 패치본)
│   └── scripts/smk_dates/2026/
├── ge_dat/                          공통 입력
│   ├── costcy_busan_2023capss_20261022.txt, invtable_busan_2017capss_20261021.txt
│   ├── gridding/   griddesc_busan_4domains.txt, srgdesc_kor_2023capss_<GRID>_20261022.txt,
│   │               agref_kor_nonpoint_2023capss_20261022.txt,
│   │               surrogates/kor_2023capss_<GRID>/srg_{kor_area,kor_mobile,kor_sea}_2023capss_<GRID>.txt
│   ├── temporal/   tpro_*, tref_kor_{point,nonpoint}_2023capss_20261022.csv, holidays_*
│   ├── speciation/ gsref_kor_{point,nonpoint}_2023capss_20261022.csv, 예제 gscnv·gspro 5개
│   ├── point/      예제 pelvconfig·pstk
│   └── smkreport/  sccdesc_busan_2023capss_20261022.txt, 예제 repconfig/ orisdesc naicsdesc
└── 2023capss_cb6/
    ├── inputs/{kor_point,kor_area,kor_mobile,kor_sea}/   FF10 인벤토리
    ├── scripts/    directory_definitions.csh, run_settings.txt, point/, nonpoint/, utils/, logs/
    ├── intermed/   (실행 시 생성)
    ├── smoke_out/  (실행 시 생성: 국내 점 결과)
    ├── premerged/  (실행 시 생성: 국내 면·이동·바다 결과)
    └── reports/    (실행 시 생성)
```

## 6. 입력 생성

### 6.1 파이썬 모듈 설치

```bash
pip3 install --user pandas numpy openpyxl pyproj
python3 -c "import pandas, numpy, openpyxl, pyproj; print('ok')"
which ncdump
```

### 6.2 생성기 실행

생성기 결과를 설치 패키지 폴더 `~/busan_2023capss_pkg`에 만든다.

```bash
F=$HOME/busan_smoke_files
PKG=$HOME/busan_2023capss_pkg
rm -rf "$PKG"
python3 "$F"/2023capss/generators/make_busan_2023_domestic_inputs.py \
  --capss    /home/woogon/CMAQ_MODEL/DATA/EMIS/CAPSS2023 \
  --code2017 "$F"/2023capss/reference/code_list_2017.xlsx \
  --code2023 "$F"/2023capss/reference/code_list_2023.xlsx \
  --legacy   "$F"/2023capss/reference \
  --out      "$PKG" 2>&1 | tee ~/busan_generate.log
```

약 5~10분 걸린다. 처음 몇 줄에 생성기가 고른 원본이 나온다.

```text
point: 점오염원(2023_전국)_1_기본.txt (1,976,005 B)
sea: 바다m(2023).txt (84,555,108 B)
area: 면오염원(2023).zip:전국a(2023).txt (853,370,385 B)
mobile: 이동오염원(2023).zip:전국m(2023).txt (710,083,207 B)
```

마지막 줄이 `done`이면 된다.

### 6.3 생성 결과 확인

```bash
grep -E "FF10 lines|NOX" "$PKG"/EMIS/2023capss_cb6/inputs/generation_summary_20261022.csv
head -1 "$PKG"/EMIS/ge_dat/smkreport/sccdesc_busan_2023capss_20261022.txt
grep -c '^"0000000000"' "$PKG"/EMIS/ge_dat/temporal/tref_kor_point_2023capss_20261022.csv
grep "all_sources" "$PKG"/EMIS/ge_dat/gridding/srgdesc_kor_2023capss_09KM_20261022.txt
```

정상 기준:

| 부문 | FF10 줄 | NOx (short ton/yr) |
|---|---|---|
| kor_point | 89,319 | 201,410 |
| kor_area | 145,564 | 139,736 |
| kor_mobile | 163,810 | 459,587 |
| kor_sea | 63 | 90,191 |

`sccdesc` 첫 줄 `#DELIMITED`, 시간 참조 기본값 줄 `3`, 대리자료 설명에 `kor_area_all_sources` 등 3줄.

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
ls "$PKG"/EMIS/2023capss_cb6/scripts "$PKG"/EMIS/smoke5.2/scripts/run
```

정상 기준: `scripts`에 `directory_definitions.csh nonpoint point run_settings.txt utils`, `run`에 `set_days_v5.csh`.

## 7. 입력 설치

```bash
bash ~/busan_2023capss_pkg/install_busan_2023capss.sh 2>&1 | tee ~/busan_install.log
```

설치 스크립트가 하는 일: 폴더·`met` 링크 확인 → 예제 `smoke5.2/` 복사(없을 때만) → 패키지 `EMIS/` 설치(패치한 `set_days_v5.csh` 포함) → 예제 종분배·굴뚝·보고서 파일 복사 → 이전 결과 일부 삭제(`2023capss_cb6/intermed/09KM/kor_point`, `inputs/asia`) → MCIP 기간 표시 → 실행 스크립트가 참조하는 파일 점검.

정상 기준:

- `run period from MCIP: 2026243 2026244 2026 8 9`
- `all referenced files exist (5 scripts x 4 domains)`
- `ok` 5줄 (`smk_pt_annual_onetime_emf.csh`, `smk_pt_annual_byday_emf.csh`, `smk_ar_annual_emf.csh`, `directory_definitions.csh`, `run_settings.txt`)
- 대리자료 폴더 4개 (01KM 32M, 03KM 43M, 09KM 24M, 27KM 7.0M)와 FF10 4개

> 참고: 설치 스크립트는 다시 돌리면 `intermed/09KM/kor_point`를 지운다. 실행 결과가 있는 상태에서 다시 설치하지 않는다.

## 8. 실행

### 8.0 이전 결과 지우기 (다시 실행할 때만)

입력(`inputs/`)과 스크립트(`scripts/`)는 남기고 실행 결과만 지운다.

```bash
C=/home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/EMIS/2023capss_cb6
rm -rf "$C"/intermed "$C"/premerged "$C"/smoke_out "$C"/reports "$C"/logs "$C"/scripts/logs/*
mkdir -p "$C"/intermed "$C"/reports "$C"/logs "$C"/scripts/logs
```

### 8.1 국내 점오염원 (`kor_point`)

**처리:** onetime — Smkinven(인벤토리) → Spcmat(종분배) → Grdmat(격자 배정) → Smkreport(보고서) → Elevpoint(모든 굴뚝 CMAQ inline 지정) / daily — Temporal(요일별 시간배분, UTC) → Smkmerge(날짜별 굴뚝 배출).

**입력 파일** (`EMIS/` 기준, 4개 도메인 공통)

| 역할 | 파일 | 내용 | 프로그램 | 구분 |
|---|---|---|---|---|
| 배출량 | `2023capss_cb6/inputs/kor_point/kor_point_CAPSS2023_ff10_20261022.csv` | 굴뚝 14,289개, 연간 배출량(short ton), 위치·제원 | Smkinven | 신규 |
| 공통 정의 | `ge_dat/gridding/griddesc_busan_4domains.txt` | 4개 도메인 격자 | Grdmat, Smkmerge | 기존 |
| | `ge_dat/costcy_busan_2023capss_20261022.txt` | 지역 코드표 (시간대 GMT) | Smkinven | 신규 |
| | `ge_dat/invtable_busan_2017capss_20261021.txt` | 오염물질 8종 | Smkinven | 예제 발췌 |
| | `ge_dat/point/pstk_13nov2018_v1.txt` | 굴뚝 제원 기본값 (사용 안 됨) | Smkinven | 예제 |
| 종분배 | `ge_dat/speciation/gsref_kor_point_2023capss_20261022.csv` | SCC → 종분배 프로파일 | Spcmat | 신규 |
| | `ge_dat/speciation/gscnv_SPECIATE_5_3_fromS2S_20230911_16jun2025_v1.txt` | VOC → TOG 계수 | Spcmat | 예제 |
| | `ge_dat/speciation/gspro_CB6R3_AE7_criteria_…`, `gspro_PM2_5_AE6_…`, `gspro_nox_hono_…`, `gspro_static_cmaq_…` | 분배 비율 | Spcmat | 예제 |
| 시간배분 | `ge_dat/temporal/tref_kor_point_2023capss_20261022.csv` | SCC → 월·요일·시간 프로파일 (기본값 262/7/24 포함) | Temporal | 신규 |
| | `ge_dat/temporal/tpro_monthly·weekly·hourly_busan_2020ver_*.csv` | 배분 비율 (시간은 UTC) | Temporal | 기존 |
| | `ge_dat/temporal/holidays_korea_2012_2026_20261021.txt`, `smoke5.2/scripts/smk_dates/2026/` | 공휴일, 날짜 대응 | Temporal | 기존 |
| 굴뚝 | `ge_dat/point/pelvconfig_elevate_everything_17apr2020_v0.txt` | 모든 굴뚝 inline 지정 | Elevpoint | 예제 |
| 보고서 | `ge_dat/smkreport/sccdesc_busan_2023capss_20261022.txt`, `repconfig/repconfig_point_*`, `orisdesc_…`, `naicsdesc_…` | SCC 이름, 보고서 설정 | Smkreport | 신규 / 예제 |
| 실행 설정 | `2023capss_cb6/scripts/point/Annual_kor_point_onetime_2023capss_cb6.csh`, `Annual_kor_point_daily_2023capss_cb6.csh` | 부문 스크립트 (daily는 `L_TYPE week`) | — | 신규 |
| | `2023capss_cb6/scripts/directory_definitions.csh`, `utils/mcip_period.py`, `run_settings.txt` | 경로·CASE·GRID, MCIP 기간, 프로그램 끄기 | — | 신규 |
| | `smoke5.2/scripts/emf/smk_pt_annual_onetime_emf.csh`, `smk_pt_annual_byday_emf.csh`, `smoke5.2/scripts/run/set_days_v5.csh` | 예제 실행 체계 | — | 예제 / 예제 수정 |

**생성 파일**

| 종류 | 위치 | 파일 |
|---|---|---|
| 최종 (CMAQ 입력) | `2023capss_cb6/smoke_out/2023capss_cb6/<GRID>/cmaq_cb6ae7/kor_point/` | `inln_mole_kor_point_<날짜>_<GRID>_cmaq_cb6ae7_2023capss_cb6.ncf` 2개 (날짜별 굴뚝 배출, 25시간, CB6 물질 59종, moles/s), `stack_groups_kor_point_<GRID>_…ncf` 1개 (굴뚝 위치·제원) |
| 중간 | `2023capss_cb6/intermed/<GRID>/kor_point/` | `pnts_*`(인벤토리), `psmat_*`(종분배), `pgmat_*`(격자), `pelv_*`, `ptmp_*`(시간배분), `logs/` |
| 보고서 | `2023capss_cb6/reports/` | `inv/rep_kor_point_2023capss_cb6_inv_state.txt` 등, `log_analyzer/rep_logs_kor_point_…level1.csv` |
| 실행 기록 | `2023capss_cb6/scripts/logs/` | `kor_point_onetime_<GRID>.log`, `kor_point_daily_<GRID>.log` |

**실행**

```bash
cd /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/EMIS/2023capss_cb6/scripts/point
for g in 27KM 09KM 03KM 01KM; do
  GRID=$g ./Annual_kor_point_onetime_2023capss_cb6.csh 2>&1 | tee ../logs/kor_point_onetime_$g.log
  GRID=$g ./Annual_kor_point_daily_2023capss_cb6.csh   2>&1 | tee ../logs/kor_point_daily_$g.log
done
```

**확인**

```bash
C=/home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/EMIS/2023capss_cb6
printf "%-6s %7s %7s %6s %10s %12s\n" GRID ERRLOG PRIO01 FILES STACKGRP STACKS
for g in 27KM 09KM 03KM 01KM; do
  L=$C/intermed/$g/kor_point/logs; O=$C/smoke_out/2023capss_cb6/$g/cmaq_cb6ae7/kor_point
  e=$(grep -l -i 'ERROR ABORT\|abnormal' $L/*.log 2>/dev/null | wc -l)
  p=$(cat $C/reports/log_analyzer/rep_logs_kor_point_2023capss_cb6_${g}_*level1.csv 2>/dev/null | grep -c '^[01],')
  n=$(ls $O/inln_mole_*.ncf 2>/dev/null | wc -l); sg=$(ls $O/stack_groups_* 2>/dev/null | wc -l)
  st=$(ncdump -h $(ls $O/stack_groups_* 2>/dev/null | head -1) 2>/dev/null | grep "ROW =" | tr -dc 0-9)
  printf "%-6s %7s %7s %6s %10s %12s\n" $g $e $p $n $sg $st
done
ls $C/smoke_out/2023capss_cb6/*/cmaq_cb6ae7/kor_point/inln_mole_* | sed 's/.*kor_point_//' | cut -c1-13
```

정상 기준과 2026-10-23 결과:

| GRID | ERRLOG | PRIO01 | FILES | STACKGRP | STACKS |
|---|---|---|---|---|---|
| 27KM | 0 | 0 | 2 | 1 | 14,289 |
| 09KM | 0 | 0 | 2 | 1 | 14,289 |
| 03KM | 0 | 0 | 2 | 1 | 6,140 |
| 01KM | 0 | 0 | 2 | 1 | 2,855 |

날짜는 도메인마다 `20260831`, `20260901`. 시도 보고서 합계(short ton): CO 347,311 / NOx 201,410 / VOC 221,154 / NH3 25,362 / SO2 106,298 / PM2.5 9,071 — 6.3 값과 일치. NOx 종분배 NO 181,269 + NO2 18,530 + HONO 1,611.

> 참고: 남는 경고 `No speciation profiles found for pollutant "PM10"`(PM10은 PM2.5+PMC로 처리), `Records in GSCNV … "EVP__VOC" ignored`, `Description of NAICS`, `No grouping criteria in PELVCONFIG`, `Missing average day emissions`, `Inventory base year 2023 is inconsistent`(2023 배출량을 2026 기상에 적용), `Not registering Smkmerge reports`는 정상이다.

### 8.2 국내 면오염원 (`kor_area`)

**처리:** Smkinven → Spcmat → Grdmat(대리자료로 시군구 → 격자) → Smkreport → Temporal → Smkmerge. 스크립트 하나가 모두 실행한다.

**입력 파일** (8.1과 같은 공통 정의·종분배 프로파일·시간 프로파일·공휴일·날짜는 생략)

| 역할 | 파일 | 내용 | 프로그램 | 구분 |
|---|---|---|---|---|
| 배출량 | `2023capss_cb6/inputs/kor_area/kor_area_CAPSS2023_ff10_20261022.csv` | 시군구 × SCC 145,564줄 | Smkinven | 신규 |
| 공간배분 | `ge_dat/gridding/srgdesc_kor_2023capss_<GRID>_20261022.txt` | 대리자료 번호 → 파일 | Grdmat | 신규 |
| | `ge_dat/gridding/agref_kor_nonpoint_2023capss_20261022.txt` | SCC → 대리자료 번호 (면 1001~, 기본 900) | Grdmat | 신규 |
| | `ge_dat/gridding/surrogates/kor_2023capss_<GRID>/srg_kor_area_2023capss_<GRID>.txt` | CAPSS 2023 1km 격자 기반 대리자료 | Grdmat | 신규 |
| 종분배 | `ge_dat/speciation/gsref_kor_nonpoint_2023capss_20261022.csv` | SCC → 종분배 프로파일 | Spcmat | 신규 |
| 시간배분 | `ge_dat/temporal/tref_kor_nonpoint_2023capss_20261022.csv` | SCC → 시간 프로파일 (기본값 포함) | Temporal | 신규 |
| 보고서 | `ge_dat/smkreport/repconfig/repconfig_area_*` | 보고서 설정 | Smkreport | 예제 |
| 실행 설정 | `2023capss_cb6/scripts/nonpoint/Annual_kor_area_2023capss_cb6.csh`, `smoke5.2/scripts/emf/smk_ar_annual_emf.csh` | 부문 스크립트, 예제 실행 체계 | — | 신규 / 예제 |

**생성 파일**

| 종류 | 위치 | 파일 |
|---|---|---|
| 최종 (병합 전) | `2023capss_cb6/premerged/kor_area/` | `emis_mole_kor_area_<날짜>_<GRID>_cmaq_cb6ae7_2023capss_cb6.ncf` (격자별 시간 배출, 지표 1층, moles/s, 도메인별 2개) |
| 중간 | `2023capss_cb6/intermed/<GRID>/kor_area/` | `area_*`(인벤토리), `asmat_*`(종분배), `agmat_*`(격자 배분), `atmp_*`(시간배분), `logs/` |
| 보고서 | `2023capss_cb6/reports/` | `inv/rep_kor_area_…`, `smkmerge/kor_area/…`, `log_analyzer/…` |

**실행**

```bash
cd /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/EMIS/2023capss_cb6/scripts/nonpoint
for g in 27KM 09KM 03KM 01KM; do
  GRID=$g ./Annual_kor_area_2023capss_cb6.csh 2>&1 | tee ../logs/kor_area_$g.log
done
```

**확인** (8.2~8.4 공통, `S`만 바꿔 쓴다)

```bash
C=/home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/EMIS/2023capss_cb6
S=kor_area
printf "%-6s %7s %7s %9s %6s\n" GRID ERRLOG PRIO01 OUTDOMAIN FILES
for g in 27KM 09KM 03KM 01KM; do
  L=$C/intermed/$g/$S/logs; R=$(ls $C/reports/log_analyzer/rep_logs_${S}_2023capss_cb6_${g}_*level1.csv 2>/dev/null)
  e=$(grep -l -i 'ERROR ABORT\|abnormal' $L/*.log 2>/dev/null | wc -l)
  o=$(cat $R 2>/dev/null | grep '^[01],' | grep -c 'does not exist within a')
  p=$(cat $R 2>/dev/null | grep '^[01],' | grep -vc 'does not exist within a')
  n=$(ls $C/premerged/$S/emis_mole_${S}_2026*_${g}_*.ncf 2>/dev/null | wc -l)
  printf "%-6s %7s %7s %9s %6s\n" $g $e $p $o $n
done
awk -F'|' '/^#Label/{for(i=1;i<=NF;i++){g=$i;gsub(/ /,"",g);if(g=="NOX")c=i}} /^kor_/{s+=$c} END{printf "NOx %.0f\n", s}' $C/reports/inv/rep_${S}_2023capss_cb6_inv_state.txt
```

정상 기준: `ERRLOG 0`, `PRIO01 0`, `FILES 2`. `OUTDOMAIN`은 영역 안에 배출 위치가 없는 SCC 경고로, 27·09KM 0, 03·01KM은 있을 수 있다(정상, 부록 A). NOx는 6.3 값과 같다.

2026-10-23 결과: ERRLOG 0, PRIO01 0(영역 밖 경고 제외), FILES 2(4개 도메인), OUTDOMAIN 27KM 0 / 09KM 0 / 03KM 72 / 01KM 150, NOx 139,736.

### 8.3 국내 이동오염원 (`kor_mobile`)

8.2와 같고 다음만 다르다.

| 항목 | 내용 |
|---|---|
| 배출량 | `2023capss_cb6/inputs/kor_mobile/kor_mobile_CAPSS2023_ff10_20261022.csv` (163,810줄: 도로 07, 비도로 08, 도로비산 12) |
| 대리자료 | `ge_dat/gridding/surrogates/kor_2023capss_<GRID>/srg_kor_mobile_2023capss_<GRID>.txt` (번호 3001~, 기본 901) |
| 스크립트 | `2023capss_cb6/scripts/nonpoint/Annual_kor_mobile_2023capss_cb6.csh` |
| 결과 | `2023capss_cb6/premerged/kor_mobile/emis_mole_kor_mobile_<날짜>_<GRID>_…ncf` |
| 확인 | 8.2 확인 명령에서 `S=kor_mobile`, 기대 NOx 459,587 |

```bash
cd /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/EMIS/2023capss_cb6/scripts/nonpoint
for g in 27KM 09KM 03KM 01KM; do
  GRID=$g ./Annual_kor_mobile_2023capss_cb6.csh 2>&1 | tee ../logs/kor_mobile_$g.log
done
```

### 8.4 바다 (`kor_sea`)

8.2와 같고 다음만 다르다.

| 항목 | 내용 |
|---|---|
| 배출량 | `2023capss_cb6/inputs/kor_sea/kor_sea_CAPSS2023_ff10_20261022.csv` (지역 90100, 선박 SCC 9종) |
| 대리자료 | `ge_dat/gridding/surrogates/kor_2023capss_<GRID>/srg_kor_sea_2023capss_<GRID>.txt` (번호 5001~, 기본 902, 4개 도메인 모두 값 있음) |
| 스크립트 | `2023capss_cb6/scripts/nonpoint/Annual_kor_sea_2023capss_cb6.csh` |
| 결과 | `2023capss_cb6/premerged/kor_sea/emis_mole_kor_sea_<날짜>_<GRID>_…ncf` |
| 확인 | 8.2 확인 명령에서 `S=kor_sea`, 기대 NOx 90,191 |

```bash
cd /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/EMIS/2023capss_cb6/scripts/nonpoint
for g in 27KM 09KM 03KM 01KM; do
  GRID=$g ./Annual_kor_sea_2023capss_cb6.csh 2>&1 | tee ../logs/kor_sea_$g.log
done
```

## 9. 완료 현황

| 단계 | 상태 (2026-10-23) |
|---|---|
| 5~7장 폴더·입력 생성·설치 | 완료 |
| 8.1 국내 점 4개 도메인 | 완료 (MCIP 기간 2일, 합계 일치) |
| 8.2 국내 면 4개 도메인 | 완료 |
| 8.3 국내 이동 4개 도메인 | 진행 |
| 8.4 바다 4개 도메인 | 미실행 |
| 국외(HTAP v3.1, 27·09KM)·생물성·병합 | 미착수 ([03 개선 계획 §5](03_SMOKE_Emission_Improvement_Plan.md)) |

## 부록 A. 실행 중 발생한 문제 기록

| 날짜 | 증상 | 원인 | 조치 |
|---|---|---|---|
| 10-22 | 국내 점 형식 시험(Smkinven만 실행)에서 Smkreport `input file not found: PSSUP` | Spcmat를 꺼서 종분배 보조 파일이 없었음 | 전체 실행에서 해소 |
| 10-22 | Smkinven 경고 `Missing control efficiency` 반복 | FF10 저감효율 칸이 비어 있음 | 생성기에서 저감효율 `0` 기입 |
| 10-22 | 높이 0.1~0.4 m 굴뚝 69줄 `Height < min` | 원자료 값이 SMOKE 하한 0.5 m보다 작음 | 조치 없음 (SMOKE가 0.5 m로 조정, NOx 28.7 t) |
| 10-22 | Smkreport `Missing file format header in the SCC description file` | SMOKE 5.3 `lib/rdsccdsc.f`는 SCC 이름 파일 첫 줄에 `#DELIMITED` 또는 `#FIXED`를 요구 | 생성기에 `#DELIMITED` 추가 |
| 10-22 | 점 daily Temporal `No month-of-year profile found for source …` | 기존 참조가 없어 기본값으로 분류된 SCC(점 11개 등)에 대한 기본 시간 참조 줄이 없었음 | 생성기가 시간 참조 두 파일에 기본값 `"0000000000"` MONTHLY 262 / WEEKLY 7 / ALLDAY 24(균등, L-NEAS 기본값과 같음)를 넣음 |
| 10-22 | 점 daily `setenv: Too many arguments` (`mondate is 2026250 2026257 …` 뒤) | 예제 `smk_pt_annual_byday_emf.csh`는 요일마다 대표일 하나로 Temporal을 돌리는 구조라 `L_TYPE all`을 지원하지 않음 | 점 daily 스크립트 `L_TYPE "week"`, `M_TYPE "all"`. 프로파일이 월·요일·시간 기반이라 결과는 날짜별 계산과 같음 |
| 10-22 | 면 Grdmat `ERROR: Overflow prevented while parsing line PARSLINE` | 대리자료 설명 줄 `KOREA,900,kor_area all sources,…`의 띄어쓰기를 SMOKE가 칸 구분으로 읽어 4칸을 넘음 | 설명을 `kor_area_all_sources`로 쓰도록 생성기 수정 |
| 10-22 | 면 Grdmat `Re-normalizing county total surrogate fractions … greater than 1` 다수 | 대리자료 비율을 소수점 8자리로 반올림해 합이 1을 아주 조금 넘음 | 조치 없음 (SMOKE가 1로 맞춤) |
| 10-23 | 9월 1~30일로 실행되고 8월 31일이 빠짐 | 부문 스크립트에 `RUN_MONTHS "9"` 고정, 예제 `set_days_v5.csh`는 월 단위로만 날짜를 고름 | `utils/mcip_period.py`·`directory_definitions.csh`로 MCIP 기간을 읽고, 부문 스크립트 고정값 삭제, `set_days_v5.csh`에 `RUN_SDATE`~`RUN_EDATE` 밖 날짜를 건너뛰는 4줄 추가 |
| 10-23 | 03·01KM Grdmat `The surrogate NNNN does not exist within a domain range: … set to zero`(로그 분석기 우선순위 0) | 그 SCC의 CAPSS 배출 위치가 도메인 안에 하나도 없음 | 조치 없음 (영역 안 실제 배출이 0). 확인 명령에서 `OUTDOMAIN`으로 따로 셈 |
| 10-23 | 문서대로 재현할 때 CAPSS 원본 위치·사용 파일이 불명확 | 생성기가 미리 이름을 바꾼 파일(`point.txt` 등)을 요구했음 | 생성기가 원본 폴더(`--capss`)를 그대로 읽어 점·면·이동·바다 파일을 자동으로 고르도록 수정 (3.2) |

## 10. 검토 근거 및 관련 문서

- 6장 생성 결과는 작성 환경에서 CAPSS 원본 4개를 원본 폴더에 그대로 두고 생성기를 실행해 확인했다. 7장 설치 점검은 작성 환경의 모의 경로로 확인했다. 8장 결과는 사용자가 제공한 Linux 실행 기록으로 확인했다.
- [03 배출량 개선 계획](03_SMOKE_Emission_Improvement_Plan.md) §4 — 단위, SCC10·연료 번호, 참조 보완, 굴뚝 보완, 대리자료 규칙
- [01 SMOKE 설치 가이드](01_SMOKE_Installation_Guide.md) §10 — 공식 예제 실행 구조
- [02 기존 체계 분석](02_Legacy_SMOKE27_Emission_Processing.md) — `reference/` 파일의 출처

## 부록 B. 공통 입력 검증 기준 (이전 작업에서 계승)

기존 CAPSS 2017 기반 공통 입력 준비에서 2023에도 유효한 기준만 계승한다.

| 파일·설정 | 2023 적용·검증 포인트 |
|---|---|
| `GRIDDESC` | MCIP와 27KM/09KM/03KM/01KM 격자명·원점·크기·행열 일치 |
| `COSTCY` | 2023 신규 `costcy_busan_2023capss_20261022.txt` 사용. 지역코드 이름 5–24열, 국가 26열, 시도 27–28열, 시군구 29–31열, 시간대 40–42열 |
| 시간배분 | 한국 지역코드는 GMT, 시간 프로파일은 UTC 전환본. KST와 혼용 금지 |
| 공휴일 | `holidays_korea_2012_2026_20261021.txt`의 2026 법정 공휴일·노동절 포함 여부 공식 검증 필요 |
| 날짜 파일 | `Date, aveday_N, aveday_Y, mwdss_N, mwdss_Y, week_N, week_Y, all` 8열. 처리 날짜는 MCIP 기간으로 제한(4장) |
| `INVTABLE` | 이름이 2017인 파일을 CO, NOX, VOC, NH3, SO2, PM10, PM2_5, PMC 8종에 재사용. `PMC=PM10-PM2_5` 호환 확인 |
| 예제 라벨 | `smoke5.2` 디렉터리명, `MODEL_LABEL SMOKE5.2`와 `EMF_AQM CMAQ v5.2`는 예제 레이블이며 실제 SMOKE 바이너리는 5.3 |
| 로그 설정 | `EMF_LOGNAME`에 `EMF_SCRIPTNAME` 절대경로가 중복될 수 있으나 2026-10-22~23 실행에서 문제 없었음 |