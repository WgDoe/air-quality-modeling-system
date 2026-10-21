# SMOKE 부산 사례 실행 가이드

> **기준 문서:** 사용자 제공 `SMOKE_Busan_Case_Run_Guide.md` (2026-10-21). 이 GitHub 문서는 해당 문서의 진행상태·경로·실행절차를 정리한 부산 사례 작업 기준본이다.  
> **목표:** SMOKE 5.3 공식 예제(SMOKE-ExampleCase-v3)의 폴더·스크립트·ASSIGNS 틀을 이용하여 `CASES/BUSAN/TEST_20260901`의 27/09/03/01 km 배출량 산정.  
> **검증 근거:** 2026-10-20~21 사용자 제공 실행 화면과 `cmaq_model_structure.txt`, `smoke_example_files.txt`, `smoke_step2_check.txt`, `smoke_invtable_check.txt`. **실제 부산 SMOKE 배출량 계산은 미실행.**

관련: [기존 SMOKE 2.7 배출 처리 분석](Legacy_SMOKE27_Emission_Processing.md) · [SMOKE 5.3 설치 및 공식 예제 검증](SMOKE_Installation_Guide.md).

## 1. 진행 현황 (2026-10-21)

| 단계 | 내용 | 상태 |
|---|---|---|
| 0 | 예제 실행체계·입력 형식 확인(읽기) | 완료 |
| 1 | 부산 `EMIS/` 폴더 생성, MCIP 연결 | 완료 |
| 2 | 예제 스크립트 복사·`directory_definitions.csh` 작성 | 공통 설정 확인 완료; 2-A 복사 결과 화면 확인 대기 |
| 3 | 공통 입력 5종(격자·지역·공휴일·날짜·INVTABLE) | 4종 설치 완료; INVTABLE 설치 확인 대기 |
| 4 | 국내 면 FF10·surrogate·시간·종분배·실행 스크립트 | 예정 |
| 5 | 국내 면 09KM 2026-09-01 첫 실행 → 4개 도메인 | 예정 |
| 6 | 국내 점 | 예정 |
| 7 | 국외(27·09KM) | 예정 |
| 8 | BEIS4 생물성 | 예정 |
| 9 | 병합 및 CMAQ 입력 | 예정 |

**원칙:** 부문 하나(국내 면)를 먼저 끝까지 검증하고 나머지 부문을 확장한다. 기상자료는 복제하지 않고 MCIP에 링크한다. 기존 파일을 변환한 값과 신규 생성 값의 출처·검증 상태를 분리한다.

## 2. 실제 경로 및 구조

```text
/home/woogon/CMAQ_MODEL/
├── CASES/
│   ├── BUSAN/TEST_20260901/
│   │   ├── WPS/  WRF/
│   │   ├── MCIP/{27KM,09KM,03KM,01KM}/
│   │   └── EMIS/
│   │       ├── ioapi/
│   │       ├── met -> ../MCIP
│   │       ├── smoke5.2/                  # 공식 예제의 스크립트·assigns 폴더 이름 유지 (SMOKE 실행 본체 버전은 5.3)
│   │       │   └── scripts/smk_dates/2026/
│   │       ├── ge_dat/
│   │       │   ├── gridding/{griddesc_busan_4domains.txt,surrogates/}
│   │       │   ├── costcy_busan_2017capss_20261021.txt
│   │       │   ├── invtable_busan_2017capss_20261021.txt
│   │       │   ├── temporal/holidays_korea_2012_2026_20261021.txt
│   │       │   ├── speciation/  point/  beis/  smkreport/
│   │       └── 2017capss_cb6/
│   │           ├── inputs/{kor_area,kor_point,asia,beis4}/
│   │           ├── scripts/{nonpoint,point,biogenics,merge,utils,logs}/
│   │           ├── scripts/directory_definitions.csh
│   │           └── intermed/  reports/  logs/
│   └── SMOKE_TEST/smoke_example_case_v3/   # 압축 해제 예제(실행 스크립트·형식 확인에 사용)
├── SMOKEv5.3/  CMAQv5.5/  WRFV4.5.1/  WPS-4.5/
└── DATA/  SCRIPTS/  libs/  src/
```

`2017capss_cb6`는 CAPSS 2017 기준, CB6 화학기작의 **배출 시나리오명**이다. `EMIS/` 직하위의 `met`, `smoke5.2`, `ge_dat`는 여러 배출 시나리오가 공유한다. 결과는 시나리오별 디렉터리에 저장한다. `premerged/`, `cmaq_cb6ae7/` 등은 실제 실행 시 생성한다.

### 기존 예제와 부산 대응

| 예제 | 부산 |
|---|---|
| `met_m3wndw/` 날짜별 파일 | `met -> ../MCIP`, 도메인별 기간 파일 |
| `smoke5.2/{scripts,assigns}` | `smoke5.2/` 복사 |
| `ge_dat/gridding/griddesc_lambertonly_18jan2019_v7.txt` | `ge_dat/gridding/griddesc_busan_4domains.txt` |
| 미국 CONUS surrogate | `2017_CAPSS_<도메인>_2020`, 국외 `2010_ASIA_<도메인>_2016` |
| 예제 COSTCY / INVTABLE / holidays | 부산용 `costcy_*`, `invtable_*`, `holidays_*` |
| `smk_dates/2022/` | `smk_dates/2026/` |
| `2022he_cb6_22m/` | `2017capss_cb6/` |
| `inputs/nonpt`, `inputs/ptnonipm` | `inputs/kor_area`, `inputs/kor_point` |
| 예제 `biogenics/` | 부산 `biogenics/` |

미국 사례의 나머지 부문(`afdust`, `onroad`, `ptfire*`, `rwc` 등)은 그대로 복제하지 않는다. 기존 부산 국내 면에 도로·비도로이동 배출이 이미 포함된다.

## 3. 도메인별 배출원

| 부문 | 27KM | 09KM | 03KM | 01KM |
|---|:---:|:---:|:---:|:---:|
| 국내 면(도로·비도로 포함), CAPSS 2017 | ✓ | ✓ | ✓ | ✓ |
| 국내 점, CAPSS 2017 | ✓ | ✓ | ✓ | ✓ |
| 아시아 국외 | ✓ | ✓ | — | — |
| BEIS4 (신규 구축 예정) | ✓ | ✓ | ✓ | ✓ |
| 해상 CAPSS 2017 | 보류 | 보류 | 보류 | 보류 |

국외 03KM surrogate는 부산이 아닌 수도권 격자. 북한은 아시아 파일의 11002만 사용하고 별도 북한 파일을 중복 계상하지 않는다. 해상은 27/09KM surrogate 원본이 발견되지 않아 보류.

## 4. 단계 0: 예제 조사 (읽기 전용)

```bash
(
EX=/home/woogon/CMAQ_MODEL/CASES/SMOKE_TEST/smoke_example_case_v3
cd "$EX" || exit 1
echo "### ioapi"; ls -la ioapi
echo "### smk_dates"; ls smoke5.2/scripts/smk_dates/2022 | head -20
echo "### assigns"; ls smoke5.2/assigns
echo "### CASE scripts"; ls -la 2022he_cb6_22m/scripts
for d in nonpoint point biogenics merge utils; do
  echo "### scripts/$d"; ls "2022he_cb6_22m/scripts/$d"
done
echo "### inputs"; for d in nonpt ptnonipm beis4; do ls -la "2022he_cb6_22m/inputs/$d"; done
for d in speciation temporal point beis smkreport; do ls "ge_dat/$d"; done
echo "### run settings"
grep -v '^#' 2022he_cb6_22m/scripts/run_settings.txt | grep -v '^\s*$'
f=$(ls 2022he_cb6_22m/scripts/nonpoint/*nonpt* 2>/dev/null | head -1)
echo "$f"; cat "$f"
) > ~/smoke_example_files.txt 2>&1
wc -l ~/smoke_example_files.txt
```

실행 구조: **부문 스크립트** → `source ../directory_definitions.csh` → 입력·옵션 설정 → `$RUNSCRIPTS/emf/smk_ar_annual_emf.csh` 등 프로그램 호출.

| 예제 설정 | 부산 결정 | 이유 |
|---|---|---|
| `WEST_HSPHERE Y` | `N` | 동반구 경도 |
| `SMK_ARTOPNT_YN Y` | `N` | 미국 항공 면→점 변환 불필요 |
| `SMK_PROCESS_HAPS PARTIAL` 등 | 제외 예정 | 입력 HAP 인벤토리 없음 |
| `SMK_DEFAULT_SRGID 100` | 부산 기본 surrogate 번호 | 미국 값 사용 금지 |
| `MRGDATE_FILES` 2022 | 2026 | 기상 연도 |
| 대표일 `week` 방식 | 일별 `all` 예정 | 단기 사례 |
| `OUTZONE 0` | 유지 | UTC 출력 |

예제는 FF10_NONPOINT 쉼표 구분, 시간 참조 CSV(MONTHLY/WEEKLY/ALLDAY), 시간 프로파일 12/7/24열 CSV, INVTABLE 고정폭. 부산 기존 IDA 및 세미콜론 참조자료를 변환해야 한다. MCIP 기상파일은 예제의 날짜별 이름과 다르므로 점·생물성 단계에서 대응이 필요하다.

## 5. 단계 1: 부산 EMIS 폴더 생성

```bash
(
B=/home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/EMIS
CASE=2017capss_cb6
mkdir -p "$B"/{ioapi,smoke5.2} \
  "$B"/ge_dat/{gridding/surrogates,speciation,temporal,point,beis,smkreport} \
  "$B/$CASE"/inputs/{kor_area,kor_point,asia,beis4} \
  "$B/$CASE"/scripts/{nonpoint,point,biogenics,merge,utils} \
  "$B/$CASE"/{intermed,reports,logs}
ln -sfn ../MCIP "$B/met"
find "$B" -maxdepth 4 | sort
ls -l "$B/met"
ls "$B/met/"
)
```

2026-10-21 결과: 폴더 및 `met -> ../MCIP`가 생성되었고 `01KM 03KM 09KM 27KM` 확인.

## 6. 단계 2: 공식 예제 실행 체계 복사

```bash
(
EX=/home/woogon/CMAQ_MODEL/CASES/SMOKE_TEST/smoke_example_case_v3
B=/home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/EMIS
du -sh "$EX/smoke5.2"
cp -a "$EX/smoke5.2/." "$B/smoke5.2/"
ls "$B/smoke5.2"
ls "$B/smoke5.2/scripts"
)
```

예상 표시: `Linux_x86_64 assigns scripts` 및 `emf run smk_dates`. **2-A 복사 결과 화면 확인 대기**.

### 6.1 부산 `directory_definitions.csh`

경로: `EMIS/2017capss_cb6/scripts/directory_definitions.csh`. **다음은 사용자 제공 문서 §7.2 기준 초안**으로 실제 사례 실행 전 로그 변수 및 EMF 스크립트 참조를 점검한다.

```csh
#!/bin/csh -f
if (! $?SECTOR ) setenv SECTOR ''
if (! $?GRID ) setenv GRID "09KM"
setenv INSTALL_DIR "/home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/EMIS"
setenv MET_ROOT "$INSTALL_DIR/met/$GRID"
setenv MET_ROOT_3D $MET_ROOT
setenv CASE "2017capss_cb6"
setenv REGION "Busan $GRID"
setenv REGION_ABBREV "$GRID"
setenv REGION_IOAPI_GRIDNAME "$GRID"
setenv EMF_SPC "cmaq_cb6ae7"
setenv SMOKE_LOCATION /home/woogon/CMAQ_MODEL/SMOKEv5.3/subsys/smoke/Linux2_x86_64gfort10
setenv IOAPI_LOCATION /home/woogon/CMAQ_MODEL/libs/ioapi-3.2-20200828/Linux2_x86_64gfort10
setenv MODEL_LABEL "SMOKE5.2"
setenv PROJECT "$CASE"
setenv OUT_ROOT "$INSTALL_DIR"
setenv PROJECT_ROOT "$INSTALL_DIR"
setenv CASE_ROOT "$PROJECT_ROOT/$CASE"
setenv IMD_ROOT "$PROJECT_ROOT/$CASE/intermed/$GRID"
setenv DAT_ROOT $PROJECT_ROOT
setenv SMK_HOME "$INSTALL_DIR"
setenv CASEINPUTS "$INSTALL_DIR/$CASE/inputs"
setenv GE_DAT "$INSTALL_DIR/ge_dat"
setenv CASESCRIPTS "$PROJECT_ROOT/$CASE/scripts"
setenv RUNSCRIPTS "$INSTALL_DIR/smoke5.2/scripts"
setenv RUNSET "$CASESCRIPTS/run_settings.txt"
setenv ASSIGNS_FILE "$INSTALL_DIR/smoke5.2/assigns/ASSIGNS.emf"
setenv EMF_CLIENT false
setenv EMF_AQM "CMAQ v5.2"
setenv EMF_JOBNAME "Annual_area"
setenv EMF_SCRIPTDIR "${CASESCRIPTS}"
setenv EMF_SCRIPTNAME "${CASESCRIPTS}/${EMF_JOBNAME}.csh"
setenv EMF_LOGNAME "${CASESCRIPTS}/logs/$EMF_SCRIPTNAME.log"
setenv EMF_JOBKEY "busan_2017capss_cb6"
setenv EMF_LOGGERPYTHONDIR "$EMF_SCRIPTDIR/case_logs_python"
setenv EMF_JOBID "1"
```

**주의:** `MODEL_LABEL SMOKE5.2`와 `EMF_AQM CMAQ v5.2`는 예제 스크립트의 레이블을 유지한 것일 뿐, SMOKE 실행 바이너리는 5.3, 계획 CMAQ는 5.5이다. `EMF_LOGNAME`에 경로를 포함한 `EMF_SCRIPTNAME`이 중첩되는 문제 가능성도 실제 실행 전 점검한다.

```bash
f=/home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/EMIS/2017capss_cb6/scripts/directory_definitions.csh
for g in 27KM 09KM 03KM 01KM; do
  csh -c "setenv GRID $g; source $f; echo \"== \$GRID IMD_ROOT=\$IMD_ROOT\"; ls \$MET_ROOT | head -2"
done
csh -c "source $f; ls \$SMOKE_LOCATION | head -5"
```

2026-10-21 확인: 영역별 `intermed/<도메인>`, MCIP `GRIDBDY2D_*`/`GRIDCRO2D_*`, SMOKE 실행파일 폴더를 확인했다.

## 7. 단계 3: 공통 입력 5종

| 파일 | EMIS 아래 위치 | 출처·검증 |
|---|---|---|
| `griddesc_busan_4domains.txt` | `ge_dat/gridding/` | 4개 MCIP GRIDDESC 원문 값 |
| `costcy_busan_2017capss_20261021.txt` | `ge_dat/` | 기존 국내/아시아/BIO 지역 코드 261개, GMT |
| `holidays_korea_2012_2026_20261021.txt` | `ge_dat/temporal/` | 기존 2012~2020 + 신규 2026; 공식 달력 검증 필요 |
| `smk_merge_dates_202601~202612.txt` | `smoke5.2/scripts/smk_dates/2026/` | 8열 예제 형식; 대표일 규칙 추정 |
| `invtable_busan_2017capss_20261021.txt` | `ge_dat/` | 예제 INVTABLE에서 8줄 원문 복사; 설치 확인 대기 |

### 7.1 격자

`EASTASIA`: Lambert (2), 표준위도 30°/60°, 중심경도 126°, 기준위도 38°.

| 격자 | X/Y 원점(m) | 셀(m) | 열×행 |
|---|---|---:|---:|
| 27KM | -2,349,000 / -1,728,000 | 27,000 | 174×128 |
| 09KM | -180,000 / -585,000 | 9,000 | 67×82 |
| 03KM | 105,000 / -408,000 | 3,000 | 83×83 |
| 01KM | 231,000 / -332,000 | 1,000 | 78×70 |

### 7.2 COSTCY

기존 `9_Area_TimeZone.txt` 253, `9_Asia_TimeZone.txt` 7, `9_Bio_TimeZone.txt` 1 = 261개 지역 코드. SMOKE 5.3 `rdstcy.f` 고정폭에 맞춰 이름 5~24열, 국가 26열, 시도 27~28열, 시군구 29~31열, 시간대 40~42열로 작성. 기존처럼 `GMT` 사용. 기존 일변화 프로파일은 UTC 기준이므로 **KST 시간대와 혼용 금지**.

### 7.3 공휴일 및 날짜 파일

기존 파일의 2021~2030년 월 `01` 오류를 피하기 위해 2012~2020년은 기존값, 2026년은 신규 작성. 2021~2025년 제외.

| 2026년 | 공휴일 (문서에 반영된 값; **공식 검증 필요**) |
|---|---|
| 1월 | 1/1 |
| 2월 | 2/16~18 |
| 3월 | 3/1~2 |
| 5월 | 5/5, 5/24~25 |
| 6월 | 6/3, 6/6 |
| 8월 | 8/15, 8/17 |
| 9월 | 9/24~26 |
| 10월 | 10/3, 10/5, 10/9 |
| 12월 | 12/25 |

노동절 5/1 포함 여부는 원자료에서 미확인으로 기록. 사례일 9/1은 공휴일이 아님.

날짜 파일은 예제와 동일한 `Date, aveday_N, aveday_Y, mwdss_N, mwdss_Y, week_N, week_Y, all` 8열. 대표 주간은 해당 월 공휴일 없는 첫 월~일요일 주간을 기준으로 한 **추정 규칙**이다. 신규 사례는 `all` 열 사용 예정이므로 대표일 필드 값은 향후 별도 QA한다.

### 7.4 INVTABLE

예제 `invtable_2022platform_integrate_15sep2025_nf_v3.txt`에서 다음 8종 줄만 선택: `CO`(533), `NOX`(657), `VOC`(702), `NH3`(653), `SO2`(687), `PM10`(663), `PM2_5`(665), `PMC`(667). 예제의 HAP/도로세분화 추가 물질은 제외. `PMC=PM10-PM2_5`는 Smkinven에서 계산 예정이고 VOC→TOG 변환은 종분배 단계에서 검증한다.

### 7.5 사용자 제공 공통 자료 설치 절차

**주의:** 다음 명령은 사용자 문서의 설치 방법이다. `busan_step3_common.zip` 및 `invtable_busan_2017capss_20261021.txt`가 홈 폴더에 실제 존재해야 한다. 이 GitHub Markdown 등록만으로 ZIP·파이썬 생성기·입력파일이 업로드되는 것은 아니다.

```bash
(
cd /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901 || exit 1
unzip -o ~/busan_step3_common.zip
ls -l EMIS/ge_dat/gridding/griddesc_busan_4domains.txt \
  EMIS/ge_dat/costcy_busan_2017capss_20261021.txt \
  EMIS/ge_dat/temporal/holidays_korea_2012_2026_20261021.txt
ls EMIS/smoke5.2/scripts/smk_dates/2026 | wc -l
)
cp ~/invtable_busan_2017capss_20261021.txt \
  /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/EMIS/ge_dat/
grep -v '^#' /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/EMIS/ge_dat/invtable_busan_2017capss_20261021.txt
```

2026-10-21 확인: 코드표 11,879B, GRIDDESC 453B, 공휴일 7,589B, 날짜 파일 12개 설치. **INVTABLE 설치 결과 확인 대기.**

사용자 문서의 `make_busan_common_inputs.py` 재생성 도구는 기존 `9_*_TimeZone.txt` 및 `holidays_korea.txt`, MCIP GRIDDESC, 예제 INVTABLE 원본이 필요하다. 생성기 파일이 별도로 제공되지 않았으므로 이 페이지에 실행 명령만 남긴다:

```bash
python3 make_busan_common_inputs.py \
  --mcip /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/MCIP \
  --legacy <기존_코드표와_공휴일_폴더> \
  --invtab /home/woogon/CMAQ_MODEL/CASES/SMOKE_TEST/smoke_example_case_v3/ge_dat/invtable_2022platform_integrate_15sep2025_nf_v3.txt \
  --out <출력_폴더>
```

## 8. 다음 작업: 국내 면 입력 (단계 4)

| 대상 | 기존 출처 | 다음 조치 |
|---|---|---|
| FF10 국내 면 | `1_Area_Inventory_File.txt` | IDA→FF10 |
| 시간 참조/프로파일 | `7_Area_Temporal_Profile.txt`, `4_Area_Temporal_Reference_Profile.txt` | CSV 변환 |
| 종분배 참조/계수 | `5_*`, `6_Area_*`, 예제 CB6 프로파일 | SCC 매핑 작성·QA |
| 공간 참조/설명 | 기존 `4_Area_Gridding_Surrogate_file.txt`, 설명 파일 | SMOKE 5.3용 작성 |
| surrogate 조각 | `2017_CAPSS_<도메인>_2020` 4개 폴더 | 기존 서버에서 복사 |
| 실행 스크립트 | 예제 `Annual_nonpt_12US1_2022he_cb6_22m.csh` | 부산 설정으로 수정 |

**실행 순서:** 국내 면 09KM · 2026-09-01 → 로그·격자·시간·질량보존 검증 → 4개 도메인 확장 → 점 → 국외 → BEIS4 → 병합.

## 9. 자료 보관·추가 확보 목록

사용자 제공 원문 §10에는 아래 파일들이 `docs/smoke/files/busan/`에 보관될 예정이라고 명시되어 있으나 **이번 업로드에는 Markdown 가이드만 포함**되어 있다. 실제 파일 업로드 전까지 이 경로가 유효한 링크라고 표시하지 않는다.

- `directory_definitions.csh`
- `griddesc_busan_4domains.txt`
- `costcy_busan_2017capss_20261021.txt`
- `holidays_korea_2012_2026_20261021.txt`
- `smk_dates/2026/` (월별 12개)
- `invtable_busan_2017capss_20261021.txt`
- `make_busan_common_inputs.py`

**검증 구분:** 본 문서는 사용자 제공 실행 기록에 근거한다. GitHub 등록 중 서버 원본 파일/로그를 직접 열거나 신규 SMOKE 부산 사례를 재실행하지 않았다. 향후 완료된 단계와 확인 대기 항목은 실행 증빙을 확보하여 갱신한다.
