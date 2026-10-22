# SMOKE 부산 사례 실행 가이드

> **기준 문서:** 사용자 제공 `SMOKE_Busan_Case_Run_Guide.md` (2026-10-22 갱신). 이 GitHub 문서는 해당 문서의 진행상태·경로·실행절차를 정리한 부산 사례 작업 기준본이다.  
> **목표:** SMOKE 5.3 공식 예제(SMOKE-ExampleCase-v3)의 폴더·스크립트·ASSIGNS 틀을 이용하여 `CASES/BUSAN/TEST_20260901`의 27/09/03/01 km 배출량 산정.  
> **검증 근거:** 2026-10-20~22 사용자 제공 실행 화면과 `cmaq_model_structure.txt`, `smoke_example_files.txt`, `smoke_step2_check.txt`, `smoke_invtable_check.txt`, `smoke_speciation_check.txt`, `smoke_speciation_check2.txt`. **실제 부산 SMOKE 배출량 계산은 미실행(단계 5 실행 대기).**

관련: [기존 SMOKE 2.7 배출 처리 분석](Legacy_SMOKE27_Emission_Processing.md) · [SMOKE 5.3 설치 및 공식 예제 검증](SMOKE_Installation_Guide.md).

## 1. 진행 현황 (2026-10-22)

| 단계 | 내용 | 상태 |
|---|---|---|
| 0 | 예제 실행체계·입력 형식 확인(읽기) | 완료 |
| 1 | 부산 `EMIS/` 폴더 생성, MCIP 연결 | 완료 |
| 2 | 예제 스크립트 복사·`directory_definitions.csh` 작성 | 완료 (2-A 복사·공통 설정 확인, 2026-10-21) |
| 3 | 공통 입력 5종(격자·지역·공휴일·날짜·INVTABLE) | 완료 (5종 설치 확인, 2026-10-21) |
| 4 | 국내 면 FF10·surrogate·시간·종분배·실행 스크립트 | 완료 (설치 확인, 2026-10-22, §8) |
| 5 | 국내 면 09KM 첫 실행(2026년 9월) → 4개 도메인 | 실행 대기 (명령 준비, §9) |
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
| 해상 CAPSS 2017 | 대리자료 확보 | 대리자료 확보 | 대리자료 생성 예정 | 대리자료 생성 예정 |

국외 03KM surrogate는 부산이 아닌 수도권 격자. 북한은 아시아 파일의 11002만 사용하고 별도 북한 파일을 중복 계상하지 않는다. 해상: 27/09KM 대리자료(`*_2017_2020update_sea.txt`)를 2026-10-21 확보했으며, 03/01KM은 해상 값이 없어 09KM에서 생성할 예정이다(§8.3, §9.4). 첫 국내 면 실행에는 해상 인벤토리를 넣지 않는다.

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

예상 표시: `Linux_x86_64 assigns scripts` 및 `emf run smk_dates`.

2026-10-21 결과: `EMIS/smoke5.2/scripts`에 `afdust_adj annual_report combine emf emisqa log_analyzer platform regrid run smk_dates` 등이 확인되어 복사 완료(`ls … | head` 기준 앞 10개).

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
| `invtable_busan_2017capss_20261021.txt` | `ge_dat/` | 예제 INVTABLE에서 8줄 원문 복사; 설치 확인(2026-10-21) |

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

**주의:** 다음 명령은 실제 부산 사례 설치에 사용한 절차를 기록한 것이다. 재실행하려면 `busan_step3_common.zip` 및 `invtable_busan_2017capss_20261021.txt`가 홈 폴더에 있어야 한다. 개별 공통 입력파일·생성기는 이 저장소의 [`files/busan/`](files/busan/)에서도 확인할 수 있지만 ZIP 자체는 별도로 준비해야 한다.

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

2026-10-21 확인: 코드표 11,879B, GRIDDESC 453B, 공휴일 7,589B, 날짜 파일 12개 설치. INVTABLE은 `grep -v '^#'` 결과 `CO NOX VOC NH3 SO2 PM10 PM2_5 PMC` 8줄(모두 `Y 1.0 N tons/yr`)이 확인되었다. 화면에서 줄 사이가 빈 줄처럼 보이는 것은 예제 원문 줄 끝의 공백(약 170열)이 터미널 폭에서 줄바꿈된 것이며 파일 내용 문제는 아니다.

재생성 도구 [`files/busan/make_busan_common_inputs.py`](files/busan/make_busan_common_inputs.py)는 기존 `9_*_TimeZone.txt` 및 `holidays_korea.txt`, MCIP GRIDDESC, 예제 INVTABLE 원본이 필요하다. 2026-10-21 작성본과 같은 결과를 내는 것을 확인했다(작성 환경에서 비교). 실행 명령:

```bash
python3 make_busan_common_inputs.py \
  --mcip /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/MCIP \
  --legacy <기존_코드표와_공휴일_폴더> \
  --invtab /home/woogon/CMAQ_MODEL/CASES/SMOKE_TEST/smoke_example_case_v3/ge_dat/invtable_2022platform_integrate_15sep2025_nf_v3.txt \
  --out <출력_폴더>
```

## 8. 단계 4: 국내 면 입력 준비 (완료, 2026-10-21~22)

단계 4는 **SMOKE 실행 전** 국내 면(`kor_area`)의 입력을 SMOKE 5.3 형식으로 만들어 설치한 단계다. 점·국외 부문을 위한 시간·종분배 참조와 국외 FF10도 일부 함께 준비했다. 아래 설치·동일성 검증은 사용자 제공 기록 기준이며 이번 GitHub 반영 과정에서 Linux 서버를 재실행하지 않았다.

| 묶음 | 내용 | 후속 프로그램 | 상태 |
|---|---|---|---|
| 4-A | FF10 인벤토리, 시간 프로파일·참조 | Smkinven, Temporal | 설치 확인 |
| 4-B | surrogate 복사, 설명·공간 참조 | Grdmat | 설치 확인 |
| 4-C | 종분배 참조·예제 프로파일, SCC 목록 | Spcmat, Smkreport | 설치 확인 |
| 4-D | 국내 면 실행 스크립트 | 전체 | 설치 확인 |

### 8.1 사용한 운영서버 원자료(2020년 버전)

| 파일 | md5 앞 12자리 | 역할 |
|---|---|---|
| `1_Area_Inventory_File.txt` | `3d797b0650d2` | 국내 면 |
| `1_Area_Inventory_File_sea.txt` | `b0b93e1dcae6` | 해상 |
| `1_New_Asia_Area_Inventory_File.txt` | `0545830e13dc` | 국외 |
| `7_Area_Temporal_Profile.txt` | `56fe5ce067b7` | 시간 프로파일 |
| `4_Area/4_Point/4_New_ASIA_*_Temporal_Reference_Profile.txt` | `a98466d3742d` / `1f10c2e258af` / `c4fb30136b8f` | 시간 참조 |
| `5_Area/5_Point/5_Asia_*_Speciation_Reference_Profile.txt` | `ba21b7be6798` / `ced38161fe59` / `208238c12fc9` | 종분배 참조 |
| `4_Area_Gridding_Surrogate_file.txt` / `4_New_ASIA_Area_Gridding_Surrogate_file.txt` | `7d1421fa1c7a` / `a24f413ef956` | 공간 참조 |

대리자료 설명(국내 4영역·국외 27/09KM)과 면·점·국외 SCC 설명 파일도 원자료로 사용했다. **이는 입력 파일에 기록된 md5 일부이며, 이번 GitHub 업로드에서 재산출한 값은 아니다.**

### 8.2 4-A: FF10 인벤토리·시간분배

| 생성 파일 | 설치 위치(`EMIS/` 기준) | 결과 |
|---|---|---|
| `kor_area_CAPSS2017_ff10_20261021.csv` | `2017capss_cb6/inputs/kor_area/` | 264,505줄, 21,528,767 bytes, md5 `ce7d4eecfb5b…` |
| `kor_sea_CAPSS2017_ff10_20261021.csv` | 동일 | 49줄, 4,885 bytes, md5 `5394a4220dd6…`(첫 실행 제외) |
| `asia_2010_ff10_20261021.csv` | `2017capss_cb6/inputs/asia/` | 333줄, md5 `1eec8bb04f9a…`(단계 7) |
| `tpro_monthly_busan_2020ver_20261021.csv` 외 weekly/hourly | `ge_dat/temporal/` | 월 833, 요일 48, 시간 87개 프로파일 |
| `tref_kor_area_*`, `tref_kor_point_*`, `tref_asia_*` | `ge_dat/temporal/` | SCC 610/252/147개 참조 |

IDA 면 형식의 지역(1~5열), SCC(6~15열), 물질별 47자 묶음의 연간 배출량(앞 10자)을 읽고 **한 줄/한 물질, 46열 FF10_NONPOINT**로 변환했다. `#POLID` 순서는 `SO2 NOX CO PM10 VOC NH3 PM2_5`. 0 이하 값은 제외했다. 머리말 `#COUNTRY=ASIA`와 COSTCY `1 ASIA` 연결 및 내부 지역코드(11100→111100)는 SMOKE 5.3 `gethdr.f`·`rdsrcff10ar.f`와 대조한 기록이다. 북한은 아시아 파일의 11002만 사용한다.

시간 프로파일은 기존 정수값을 합 1인 비율로 변환했다. 기존 평일/주말 시간별 변화가 87개 전부 같아서 참조는 `ALLDAY` 하나로 정리했다. **UTC 일변화 프로파일+GMT 지역코드** 조합 유지.

**FF10과 IDA 원본의 국내 면 물질별 연간 합계 일치(ton/yr):**

| 부문 | SO2 | NOX | CO | PM10 | VOC | NH3 | PM2_5 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 국내 면 | 111,330 | 885,640 | 730,535 | 222,732 | 878,861 | 290,567 | 86,742 |
| 해상 | 12,428 | 99,817 | 51,378 | 3,704 | 16,804 | 9 | 3,459 |

### 8.3 4-B: 공간배분 자료

기존 운영 서버의 surrogate 폴더는 Linux 사례의 `EMIS/ge_dat/gridding/surrogates/`로 복사했으며 약 170 MB로 기록된다. 저장소에는 보관하지 않는다.

| 폴더 | 파일 수 | 용량 | 원점/범위 확인 |
|---|---:|---:|---|
| `2017_CAPSS_27KM_2020` | 101 | 11M | 27KM, 174×128 |
| `2017_CAPSS_09KM_2020` | 101 | 29M | 09KM, 67×82 |
| `2017_CAPSS_03KM_2020` | 100 | 49M | 03KM, 83×83 |
| `2017_CAPSS_01KM_2020` | 100 | 37M | 01KM, 78×70 |
| `2010_ASIA_27KM_2016` | 100 | 37M | 27KM |
| `2010_ASIA_09KM_2016` | 100 | 2.3M | 09KM |
| `2010_ASIA_03KM_2016` | 100 | 4.3M | **수도권 65×65, 부산에 미사용** |

국내 4개 영역의 100개 조각, 국외 27/09KM의 설명 파일에서 사용된 71개 조각에 결손이 없다고 확인됐다.

**설명 및 참조:** 기존 `KOREA,번호,SCC,파일` 및 `지역 SCC 번호` 형식을 SMOKE 5.3 `rdsrgdesc.f`, `rdgref.f`가 읽을 수 있어 내용은 유지하고 출처 주석만 추가했다. 국내 면 FF10 SCC 602개 모두 참조 존재, 기본 surrogate ID 999.

| 생성 파일 | 위치 | 기존 자료 |
|---|---|---|
| `srgdesc_kor_<27KM·09KM·03KM·01KM>_2017_2020update.txt` | `ge_dat/gridding/` | 국내 description |
| `srgdesc_asia_<27KM·09KM>_2016update.txt` | `ge_dat/gridding/` | 국외 description |
| `agref_kor_area_2017capss_2020ver.txt` | `ge_dat/gridding/` | 국내 gridding reference (SCC 612개) |
| `agref_asia_2016.txt` | `ge_dat/gridding/` | 국외 gridding reference |

**해상 surrogate 확보(2026-10-21):** 해상 SCC 7종(98…)은 ID 606~612를 쓴다. 27/09KM의 `<도메인>_d0X_2017_2020update_sea.txt`에서 지역 111352 분포가 확인됐다(27KM 비율 합 0.91~1.00, 09KM 0.83~1.00). 03/01KM 설명이 지정한 조각에는 해상 값이 없어, 기존 운영에서도 3·1km 해상 배출이 배분되지 않았을 것으로 판단한다. **09KM 기반 신규 생성은 계획 단계**이며 (§9.4), 이번 첫 실행에는 해상을 넣지 않는다.

### 8.4 4-C: 화학종 분배

기존 SCC의 SPECIATE 프로파일 번호를 공식 예제 **CB6R3_AE7 / SPECIATE 5.3** 파일에 연결했다. VOC 프로파일 57개와 PM2.5 프로파일 42개 모두 예제 파일에 존재했고, VOC 57개 모두 `gscnv_SPECIATE_5_3_fromS2S_20230911_16jun2025_v1.txt`에 VOC→TOG 계수가 있는 것으로 기록됐다.

신규 예제 계수와 기존 SCC별 계수로 계산한 국내 면 TOG 총량은 각각 **1,586,808 vs 1,624,664 ton/yr(97.7%)**. 예제 계수를 사용하기로 했으며, 이전 계수로 복원하려면 `GSCNV`만 바꾼다. 기존 계수의 큰 값(예: 매립지 가스 3002, 156.25)은 프로파일 성격과 관련되어 있을 수 있다.

| 파일 | 목적 |
|---|---|
| `gsref_kor_area_2017capss_2020ver.csv` | VOC/PM2.5 각 610개 SCC 매핑 |
| `gsref_kor_point_2017capss_2020ver.csv` | VOC/PM2.5 각 252개 SCC 매핑(단계 6) |
| `gsref_asia_2016.csv` | 국외 각 147개 SCC, TOG→VOC 통일(단계 7) |
| `sccdesc_busan_2017capss_20261021.txt` | SCC 1,001개, 코드만 기록 |
| `gscnv_SPECIATE_5_3_fromS2S_20230911_16jun2025_v1.txt` | VOC 변환 |
| `gspro_static_cmaq_21feb2012_v13.txt` | CO, NH3, SO2 기본 `0000`; PMC `99999` |
| `gspro_PM2_5_AE6_Spec_5_3_S2S_20230911_01nov2023_v0.txt` | PM2.5 |
| `gspro_CB6R3_AE7_criteria_Spec_5_3_S2S_20230911_01nov2023_v0.txt` | VOC |
| `gspro_nox_hono_pf4_06aug2008_v0.txt` | NOX→NO 0.9 / NO2 0.092 / HONO 0.008 |

참조 형식은 예제와 같은 CSV(`"SCC","profile","pollutant",...`). 기본 SCC `0000000000`은 CO/NH3/SO2 `0000`, PMC `99999`, NOX `HONO`, VOC `0000`, PM2.5 `91117`.

**발견한 오류와 수정:** 최초 PMC 기본 프로파일을 `0000`으로 작성했으나 예제 정적 프로파일에는 `0000;"PMC"`가 없다. 기존 체계도 `0 99999 PMC`를 사용했다. 3개 참조 파일을 `99999`로 수정해 설치·확인했다.

```bash
S=/home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/EMIS/ge_dat/speciation
sed -i 's/^"0000000000","0000","PMC"/"0000000000","99999","PMC"/' $S/gsref_*.csv
grep -H '"PMC"' $S/gsref_*.csv
```

### 8.5 4-D: 국내 면 실행 스크립트

`Annual_kor_area_2017capss_cb6.csh`를 공식 예제 `Annual_nonpt_12US1_2022he_cb6_22m.csh`에서 변형했다. 단일 스크립트로 `GRID` 변경 시 4개 영역 대리자료 파일을 고른다.

| 설정 | 부산 값 | 설명 |
|---|---|---|
| `RUN_MONTHS`/`BASE_YEAR` | `9`/`2026` | 2026년 9월 |
| `L_TYPE`, `M_TYPE` | `all` | 일별 |
| `MRGDATE_FILES` | `smk_dates/2026/smk_merge_dates_202609.txt` | |
| `SRGDESC`, `AGREF`, `SRGPRO` | 도메인별 파일, 기존 참조, `.00` 조각 | |
| `ATREF`, `ATPRO_*`, `HOLIDAYS` | §8.2 참조 | |
| `GSREFTMP_A`, `GSPROTMP_*`, `GSCNV` | §8.4 자료 | |
| `EMISINV_A` | 국내 면 FF10만 | **첫 실행 시 해상 제외** |
| `WEST_HSPHERE`, `SMK_DEFAULT_SRGID` | `N`, `999` | |
| `SMK_ARTOPNT_YN`, `DEFAULT_CONV_FAC_ERROR` | `N`, `Y` | |
| `SMKINVEN_FORMULA`, `OUTZONE`, `IOAPI_ISPH` | `PMC=PM10-PM2_5`, `0`, `20` | |
| HAP 처리 | 미사용 | 인벤토리에 HAP 없음 |

### 8.6 입력 재생성과 배치

`make_busan_step4_inputs.py`는 사용자 기록상 기존 원자료를 모아 `EMIS/` 구조로 4-A~4-C를 생성하며 작성 환경에서 설치본과 결과가 같았다고 한다. **이번 업로드에 생성기 실물은 포함되지 않았고, 현재 GitHub에도 없음**. 따라서 재생성 명령은 파일을 별도 확보한 뒤 실행한다.

```bash
python3 make_busan_step4_inputs.py --legacy <기존_자료_폴더> --out <출력_폴더>
```

FF10 21.5MB는 저장소에 넣지 않고 생성기와 md5로 관리한다. 기존 SMOKE 예제 종분배 파일 5개 및 `smkreport/repconfig`, `run_settings.txt`는 공식 예제 배포본에서 복사한다. 사용자 기록의 후속 명령:

```bash
(
B=/home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/EMIS
EX=/home/woogon/CMAQ_MODEL/CASES/SMOKE_TEST/smoke_example_case_v3
for f in gscnv_SPECIATE_5_3_fromS2S_20230911_16jun2025_v1.txt \
         gspro_static_cmaq_21feb2012_v13.txt \
         gspro_PM2_5_AE6_Spec_5_3_S2S_20230911_01nov2023_v0.txt \
         gspro_CB6R3_AE7_criteria_Spec_5_3_S2S_20230911_01nov2023_v0.txt \
         gspro_nox_hono_pf4_06aug2008_v0.txt; do
  cp "$EX/ge_dat/speciation/$f" "$B/ge_dat/speciation/"
done
cp -r "$EX/ge_dat/smkreport/repconfig" "$B/ge_dat/smkreport/"
cp "$EX/2022he_cb6_22m/scripts/run_settings.txt" "$B/2017capss_cb6/scripts/"
# Annual_kor_area_2017capss_cb6.csh 파일도 별도 확보하여
# "$B/2017capss_cb6/scripts/nonpoint/"에 설치하고 chmod +x 적용
)
```

## 9. 단계 5: 국내 면 첫 실행 (대기)

**아직 부산 실제 배출량 계산은 수행하지 않았다.** 09KM에서 먼저 2026년 9월을 테스트하고 통과하면 27/03/01KM으로 확장한다.

### 9.1 프로그램 순서

| 순서 | 프로그램 | 수행 역할 | 주요 입력 |
|---|---|---|---|
| 1 | Smkinven | FF10 인벤토리 읽기, PMC, 지역·시간대 | FF10, INVTABLE, COSTCY |
| 2 | Spcmat | VOC→TOG→CB6, PM2.5→AE, NOX→NO/NO2/HONO | GSREF/GSCNV/GSPRO |
| 3 | Grdmat | 시군구·SCC→격자 | GRIDDESC/SRGDESC/AGREF/surrogate |
| 4 | Temporal | 날짜별 시간분배 | TREF/TPRO/공휴일/날짜 |
| 5 | Smkmerge | 격자·시간·물질별 파일 | 1~4 단계 결과 |
| 6 | Smkreport | 지역·SCC 보고서 | repconfig/SCCDESC |

### 9.2 09KM 실행 명령 (예정)

**아래는 실행 준비된 명령으로, 실행 스크립트 파일이 실제 설치되어 있어야 한다.**

```bash
cd /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/EMIS/2017capss_cb6/scripts/nonpoint
GRID=09KM ./Annual_kor_area_2017capss_cb6.csh 2>&1 | tee ../logs/kor_area_09KM_run1.log
```

파이프라인에서 실행 스크립트 오류가 `tee`의 성공 코드에 가려지지 않도록 Bash에서 `set -o pipefail`을 먼저 사용해도 된다. 실제 실행 후 내부 프로그램 로그를 별도로 확인한다.

### 9.3 실행 결과 확인(예정)

```bash
(
C=/home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/EMIS/2017capss_cb6
tail -40 "$C/scripts/logs/kor_area_09KM_run1.log"
grep -ci "error" "$C/scripts/logs/kor_area_09KM_run1.log"
grep -ci "warning" "$C/scripts/logs/kor_area_09KM_run1.log"
find "$C" -name "*.log" -path "*kor_area*" | sort | head -30
)
```

검증 기준: 프로그램 정상 종료, FF10과 영역 내 격자 배출 총량 비교, 시간분배 UTC 정합성, 기존 SMOKE 2.7 산출물과 비교.

### 9.4 해상 처리(실행 후 후속 과제)

03/01KM 해상 surrogate는 09KM 해상 값을 각각 9개(3km), 81개(1km) 작은 셀에 동일 분배하는 방법을 계획했다. 원점이 9km 격자선과 완전히 일치하지 않더라도 9km/3km/1km 셀 경계를 고려해야 한다는 원문 조건을 보존한다. 제공 문서상 작성 환경에서 가상 자료로 면적 중첩 계산과 일치했다고 기록되어 있으나 **Linux 본 실행은 미수행**. 새 surrogate 생성 후 03/01KM 설명 파일의 606~612 항목을 연결하고 해상 FF10을 추가한다. `make_busan_sea_surrogates.py` 파일은 현재 GitHub에 없어 별도 확보가 필요하다.

## 10. 저장소 파일 및 추가 필요 자료

**GitHub에 현재 존재가 확인된 기존 공통 입력파일:** [`files/busan/`](files/busan/)의 `directory_definitions.csh`, `griddesc_busan_4domains.txt`, `costcy_busan_2017capss_20261021.txt`, `holidays_korea_2012_2026_20261021.txt`, `smk_dates/2026/`, `invtable_busan_2017capss_20261021.txt`, `make_busan_common_inputs.py`.

**추가 업로드 필요:** `make_busan_step4_inputs.py`, `files/busan/step4/ge_dat/` 하위의 생성 결과, `scripts/nonpoint/Annual_kor_area_2017capss_cb6.csh`, `make_busan_sea_surrogates.py`. 이들은 이번 대화의 Markdown 첨부에 경로만 기록되어 있으며 원본 바이트는 전달되지 않았다. 존재하지 않는 링크는 생성하지 않는다.

**GitHub에 보관하지 않을 대용량 자료:** 기존 CAPSS/ASIA surrogate 약 170MB, 국내 면 FF10 약 21.5MB, 예제에서 재복사 가능한 종분배 원본.

**검증 경계:** 단계 4의 완료는 사용자 제공 설치·비교 기록을 근거로 한다. 실제 부산 SMOKE 5.3 실행, SMOKE→CMAQ 연계 검증, 해상 03/01KM 신규 surrogate의 Linux 검증은 아직 수행되지 않았다.
