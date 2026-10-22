# SMOKE 부산 사례 실행 가이드 — CAPSS 2023 / HTAP v3.1

> **실행 기준:** SMOKE 5.3 · `CASES/BUSAN/TEST_20260901` · 신규 배출 시나리오 **`2023capss_cb6`** (2026-10-22 기준).  
> **현재 상태(2026-10-22):** 공식 예제 및 부산 공통 기반 구축 완료. **CAPSS 2023 점·면·이동·바다의 FF10·surrogate·참조·실행 스크립트 생성 완료(작성 환경 기준)**, **Linux 09KM 점 Smkinven 단독 형식 시험 정상 종료**. 다만 **ZIP 최종 일괄 설치 확인 및 점 onetime/daily·면·이동·바다의 SMOKE 전 단계 실행은 아직 미수행**.  
> **이 문서의 역할:** 새 시나리오의 **실제 실행 및 검증 기록**을 단계별로 축적. 배출량 자료 선정·변환 원칙은 [배출량 개선 계획](SMOKE_Emission_Improvement_Plan.md)을 기준으로 한다.

이전 `2017capss_cb6`의 폴더·FF10·공간/시간/종분배 준비 과정과 **실행하지 않은 국내 면 테스트 명령**은 [CAPSS 2017 기준선 작업 기록](SMOKE_Busan_Case_2017_Baseline_Archive.md)에 완전히 보존했다. 해당 명령은 **신규 2023 시나리오에 그대로 실행하지 않는다.** 설치·미국 공식 예제 검증은 [SMOKE 5.3 설치 가이드](SMOKE_Installation_Guide.md), 기존 운영자료 분석은 [SMOKE 2.7 분석](Legacy_SMOKE27_Emission_Processing.md)을 참고한다.

## 0. 진행 현황

| 구간 | 작업 | 상태 (2026-10-22) |
|---|---|---|
| 공통 0 | SMOKE 5.3 설치·공식 예제 구조 및 입력 형식 확인 | 완료 (기존 기록) |
| 공통 1 | 부산 CASE의 `EMIS/` 구조 및 MCIP 링크 연결 | 완료 (기존 기록) |
| 공통 2 | 공식 예제 스크립트·ASSIGNS 복사, 공통 설정 방식 확인 | 완료 (기존 기록) |
| 공통 3 | GRIDDESC·지역/시간대·공휴일·날짜·INVTABLE의 기존 공통 자료 준비 | 완료 (2017 기준 구성); **2023 호환성 재검토 필요** |
| 신규 A | `2023capss_cb6` 국내 점 Smkinven 입력 준비·실행 | **09KM 단독 형식 시험 정상 종료(2026-10-22)**; 점 전체 실행 미수행 |
| 국내 입력 생성 | 점·면·이동·바다 FF10·4개 도메인 surrogate·실행 스크립트 패키지 | **작성 환경 생성 완료, Linux 일괄 설치 검증 대기 (§7)** |
| 신규 B | 국내 점 Spcmat 종분배 | 예정 |
| 신규 C | 국내 점 Grdmat 공간배분 | 예정 |
| 신규 D | 국내 점 Temporal 시간분배 | 예정 |
| 신규 E | 국내 점 배출 병합/굴뚝 처리 | 예정 |
| 신규 F | Smkreport 검증 및 4개 도메인 확장 | 예정 |
| 후속 | 국내 면·이동·바다 → HTAP 국외 → 생물성 → CMAQ 병합 | 예정 |

**검증 범위:** 완료는 기존 사용자 제공 실행 화면·출력파일 기록을 뜻한다. 2023 CAPSS의 계산 성공이나 QA 완료를 뜻하지 않는다.

## 1. 공통 폴더 구조 — 유지

설치 프로그램 본체는 `/home/woogon/CMAQ_MODEL/SMOKEv5.3/`, 사례 자료는 `CASES/BUSAN/TEST_20260901/`에 구분해 둔다. 27/09/03/01KM WRF·MCIP 도메인은 바꾸지 않는다.

```text
/home/woogon/CMAQ_MODEL/
├── SMOKEv5.3/                        # SMOKE 5.3 실행파일
├── CASES/
│   ├── SMOKE_TEST/smoke_example_case_v3/     # 공식 예제
│   └── BUSAN/TEST_20260901/
│       ├── WPS/  WRF/
│       ├── MCIP/{27KM,09KM,03KM,01KM}/
│       └── EMIS/
│           ├── met -> ../MCIP               # 기상 복제 없이 링크
│           ├── ioapi/
│           ├── smoke5.2/                     # 공식 예제 실행 스크립트 폴더명 그대로 사용; 바이너리는 5.3
│           │   ├── assigns/
│           │   └── scripts/smk_dates/2026/
│           ├── ge_dat/{gridding,speciation,temporal,point,beis,smkreport}/
│           ├── 2017capss_cb6/                # 기존 입력 준비 보존, 실행 대상 아님
│           └── 2023capss_cb6/                # 신규 작업 시나리오: 실제 생성 여부 미확인
│               ├── inputs/{kor_point,kor_area,htap,biogenics}/
│               ├── scripts/{point,nonpoint,biogenics,merge,utils,logs}/
│               └── intermed/  reports/  logs/
└── DATA/  SCRIPTS/  libs/  src/
```

위 `2023capss_cb6/` 아래 구조는 **신규 계획 구조**이며 서버에 실제 생성됐다고 단정하지 않는다. 입력·결과는 시나리오별로 분리한다. `smoke5.2/` 폴더 이름과 모델 실행 버전 5.3은 별개다.

## 2. 공통 실행 기반 — 기존 작업 유지, 내용은 검토

- 예제의 `smoke5.2/{scripts,assigns}` 복사본과 `met -> ../MCIP` 링크는 유지한다.
- 격자 정의는 MCIP와 일치한 4영역 `griddesc_busan_4domains.txt`를 계속 쓴다.
- `smk_dates/2026/` 및 한국 공휴일 파일은 기존 작성본을 토대로 사용하되 **공휴일 공식 달력·노동절 여부 검증은 남아 있다**.
- **주의:** 기존 `costcy_busan_2017capss_20261021.txt`에는 2017 지역 코드가 들어 있다. **CAPSS 2023 행정구역코드(예: 바다 90100)에 맞게 새 COSTCY를 작성해야 하며, 기존 파일을 무검토 재사용하지 않는다.**
- `invtable_busan_2017capss_20261021.txt`는 기존 8물질 표준을 참고하되, CAPSS 2023 물질명·단위와 PMC 정의·예제 호환성을 확인한다.
- 기존 `directory_definitions.csh`에는 `CASE=2017capss_cb6`가 설정되어 있으므로 **신규 CASE를 대상으로 별도 수정·복사한 파일을 검증**해야 한다. 로그 파일 변수 `EMF_LOGNAME`의 경로 중첩 가능성도 확인한다.
- 기존 UTC 시간 프로파일을 사용하는 동안 COSTCY 시간대는 GMT 조합으로 유지하고, KST 프로파일과 혼합하지 않는다.
- 예제 `SMOKE-ExampleCase-v3`의 입력 파일·날짜·ASSIGNS 참조는 신규 점 부문 스크립트에서 재확인한다.

### 2.1 4개 도메인 (기존 MCIP 기준)

| 도메인 | 격자 크기 | X/Y 원점 (m) | 행렬 |
|---|---:|---|---|
| 27KM | 27,000m | -2,349,000 / -1,728,000 | 174×128 |
| 09KM | 9,000m | -180,000 / -585,000 | 67×82 |
| 03KM | 3,000m | 105,000 / -408,000 | 83×83 |
| 01KM | 1,000m | 231,000 / -332,000 | 78×70 |

좌표계는 `EASTASIA` Lambert(표준위도 30°/60°, 중심경도 126°, 기준위도 38°). **점 배출과 공간배분의 좌표 정합성은 새 FF10 변환 결과로 재검증한다.**

## 3. 신규 배출량 구성 및 작업 순서

| 부문 | 기준자료 | 목표 도메인 | 착수 순서 |
|---|---|---|---|
| **국내 점** | CAPSS 2023 1km 점 자료, 굴뚝 제원·SCC10 보완 | 09KM 우선 → 나머지 3개 | 1 |
| 국내 면·이동·바다 | CAPSS 2023 1km 격자, 신규 surrogate | 09KM 우선 → 나머지 3개 | 2 |
| 국외 | HTAP_v3.1 2020, 남한 제외 | 27/09KM | 3 |
| 생물성 | BEIS4 또는 MEGAN 3.x(선정 필요) | 4개 도메인 | 4 |
| 최종 병합 | CB6/AE7 배출파일→CMAQ 5.5 호환성 QA | 4개 도메인 | 5 |

이전 국내 면 09KM을 먼저 실행한다는 절차는 폐기했다. 신규 단계별 계산의 로그·출력·검증표는 아래 A~F에 순차 추가한다.

## 4. 국내 점 A단계: Smkinven (다음 실제 작업)

### 4.1 목표 및 실행 상태

**목표:** CAPSS 2023 점 원자료를 SMOKE 5.3에 맞는 FF10 점오염원 입력으로 변환하고, 지역코드·오염물질·단위·굴뚝 특성을 검증한 뒤 **09KM에서 Smkinven을 첫 실행**한다.

**현재 상태:** 2026-10-22 Linux에서 CAPSS 2023 점오염원 09KM **Smkinven 형식 시험은 정상 종료**했고 배출원 14,289개·8개 물질+PMC 처리를 확인했다. 단, 전체 부문 SMOKE 실행과 최종 생성 패키지 검증은 아직 미완료이며 §7에 상세 기록했다.

### 4.2 입력 점검표

| 항목 | 원자료/근거 | 2023 처리 및 검증 |
|---|---|---|
| 점 배출 원자료 | CAPSS 2023 `지역+p.txt` | 컬럼·레코드·중복·결측 확인, FF10_POINT 변환 |
| 오염물질 단위 | 원자료 kg/yr | 입력 short ton/yr: **kg ÷ 907.18474**, 물질별 합계 대조 |
| 위치 | TM km, Tokyo/Bessel 기반 | pyproj로 위경도 변환, 예시 좌표 및 도메인 포함 확인 |
| 지역 코드 | 2023 `ADMIN_CD` 10자리 | 앞 5자리(예: `11110`), 바다 `90100`; 신규 COSTCY 매핑 검토 |
| SCC | 원자료 SCC 8자리·연료 5자리 | 기존 참조용 10자리 SCC 구성, 연료 매핑 추적 |
| 신규 연료 | 2017 코드에 없는 8종 | `G1~G6`, `S1~S2` 영문 접미부 **SMOKE 5.3 지원 여부 확인 전** |
| 굴뚝 | POINT_ID, 높이·지름·온도·속도 | 결측/0 이하 값 보완 및 원본·변환값 추적 |
| INVTABLE | 기존 8물질 표 | CAPSS 2023의 TSP, SOx, PM10, PM2.5 등 표기 대응 및 PMC 정의 검증 |
| CASE 설정 | `directory_definitions.csh`, ASSIGNS | `CASE=2023capss_cb6`, `GRID=09KM`, 경로·로그 확인 |

### 4.3 변환 시 따를 확인된 규칙

**자료 비교에서 얻은 규칙(사용자 제공 개선 계획 기준):**

- 기존 점 자료 대조 2,142쌍에서 원자료 kg/yr→short ton/yr 기준을 확인했다.
- 기존 10자리 SCC의 마지막 2자리는 기존 체계 전용 연료 번호다. L-NEAS의 다른 번호 체계와 혼용하지 않는다.
- 새 연료 8종의 임시 코드와 참조 차용 규칙은 [개선 계획 §4.3~4.4](SMOKE_Emission_Improvement_Plan.md)에 기재되어 있다. 영문 혼합 SCC를 SMOKE 5.3에서 읽는지는 실행 전에 검증한다.
- 굴뚝 제원 결측은 동일 `POINT_ID`의 다른 행 → 같은 SCC·연료 중앙값 → 같은 SCC 중앙값 → 전체 중앙값 순으로 채우며, 수정 내역을 기록한다.
- 원자료 14,437행에서 온도 결측 1,660, 속도 결측 1,841, 높이 0 이하 220, 지름 0 이하 225가 관찰되었다. 동일 지역·굴뚝·SCC·연료 중복 148행의 병합 처리 기준을 점검한다.

### 4.4 실제 실행 시 기록할 사항

1. **입력 작성:** 원자료 파일명/해시, 변환기 버전, FF10 행 수·물질별 총량, 신규 COSTCY·INVTABLE 작성 결과
2. **설정 검사:** 신규 점 부문 `*.csh`와 ASSIGNS가 읽는 모든 경로, `CASE`, `GRID`, 단위, 날짜
3. **Smkinven 실행:** 정확한 실행 명령, 시작/종료 시각, 종료코드, 단계별 출력 목록 및 로그 경로
4. **정량 QA:** 원자료 kg 총량과 FF10 short ton 환산 총량의 일치, SCC별 누락/기본 참조, 공간 범위
5. **판정:** 성공/오류/보류, 재실행 필요 사항

명령어는 준비·검증된 실제 신규 스크립트가 확인되는 시점에 기재한다. 2017 기준선의 `Annual_kor_area_2017capss_cb6.csh`를 새 시나리오의 점 부문 스크립트로 사용하지 않는다.

## 5. 국내 점 B~F 단계 (향후 실행에 따라 기록)

| 단계 | 프로그램 | 검토 입력 | 핵심 QA |
|---|---|---|---|
| B | Spcmat | 2023 SCC 참조, CB6/AE7 GSREF·GSCNV·GSPRO | VOC→TOG·NOX→NO/NO2/HONO·PM 성분 확인 |
| C | Grdmat | MCIP GRIDDESC, 점 위치·공간배분 설정 | 위치·격자 포함 여부, 점 배출 처리 방식 검증 |
| D | Temporal | 시간 참조·월/요일/시간 프로파일, 2026년 날짜·공휴일 | GMT/UTC 시간 이동, 질량 보존 |
| E | 점 부문 병합/굴뚝 상승 처리 | MCIP, 굴뚝 제원·inline 방식 | 상승·층/단위·CMAQ 연계 입력 확인 |
| F | Smkreport | 시도·시군구·SCC·시군구×SCC 보고 | 원자료와 합계, 도메인 밖 몫 설명 |

09KM 검증 후 27/03/01KM로 확대한다. 별도 국외·생물성 및 최종 CMAQ 병합은 [배출량 개선 계획 §5](SMOKE_Emission_Improvement_Plan.md)를 따른다.

## 6. 파일 관리 및 검증 원칙

- **신규 2023 결과만 이 문서의 완료 내역으로 기록한다.** 기존 2017 준비본/해상 surrogate 생성안은 [보존본](SMOKE_Busan_Case_2017_Baseline_Archive.md)에 둔다.
- `docs/smoke/files/busan/`의 기존 공통 입력들은 2017 기준으로 작성된 내용이 섞여 있으므로, **2023 호환성을 검토한 뒤 신규 버전으로 구분 보관한다.**
- 원본 CAPSS 대용량 격자 데이터, FF10 대용량 자료 등은 저장소에 무조건 넣지 않고, 생성 스크립트·해시·원자료 출처·검증 절차를 관리한다.
- `2023capss_cb6` 신규 자료 작성, 09KM Smkinven 성공, 4개 영역 확장, 국외 처리, CMAQ 병합은 **모두 아직 검증 전**이다.


## 7. CAPSS 2023 국내 배출량 입력 생성·설치 및 점 Smkinven 형식 시험 (2026-10-22)

> 이 절은 사용자가 제공한 `SMOKE_2023capss_Input_Setup_Guide.md`를 **기존 실행 가이드에 통합**한 것이다. 별도 실행 가이드 파일을 새로 만들지 않는다. 문서 내 설치 상태와 시험 성공은 제공된 작업 기록을 근거로 하며, 이번 GitHub 반영 시 Linux 원본 로그를 직접 확인하거나 SMOKE를 재실행하지 않았다.

> **목적:** [배출량 개선 계획](SMOKE_Emission_Improvement_Plan.md)에 따라 부산 사례(`CASES/BUSAN/TEST_20260901`)의 국내 배출량을 CAPSS 2023 1km 격자 자료로 교체한 SMOKE 5.3 입력 전체를 만들고 한 번에 설치한다.
> **작성:** 2026-10-22. 입력 생성은 작성 환경에서 실행·검증했고, Linux에서는 국내 점오염원 Smkinven 형식 시험(①)까지 실행했다. **부문별 SMOKE 전 단계 실행(③)은 아직 하지 않았다.**
> 관련: [배출량 개선 계획](SMOKE_Emission_Improvement_Plan.md) · 현재 실행 가이드 · [SMOKE 설치 가이드](SMOKE_Installation_Guide.md)

### 1. 지금까지 한 일

| 날짜 | 내용 | 결과 |
|---|---|---|
| 10-10~19 | SMOKE 5.3 설치, 공식 예제 전 부문·병합 검증 | 완료 ([설치 가이드](SMOKE_Installation_Guide.md)) |
| 10-19~21 | 기존 운영체계(SMOKE 2.7, 2020년 버전, CAPSS 2017) 입력 분석 | 기준선 확보 ([분석 문서](Legacy_SMOKE27_Emission_Processing.md)) |
| 10-20~21 | 부산 `EMIS/` 폴더, 공통 설정, 공통 입력(격자·공휴일·날짜·INVTABLE), 시간 프로파일 변환 | 설치 완료 ([실행 가이드](SMOKE_Busan_Case_Run_Guide.md) §0~§3) |
| 10-22 | 목표 확정: 국내 CAPSS 2023, 국외 HTAP_v3.1, 프로파일 개선 | [배출량 개선 계획](SMOKE_Emission_Improvement_Plan.md) |
| 10-22 | CAPSS 2017 원자료와 기존 IDA 대조 → 단위(short ton)·2자리 연료 번호 규칙 확인 | 개선 계획 §4.2~§4.3 |
| 10-22 | **① 공통 형식 시험:** 2023 점오염원 FF10을 Smkinven으로 읽음 | **통과** (§6) |
| 10-22 | **② 국내 입력 일괄 생성:** 점·면·이동·바다 인벤토리, 4개 도메인 대리자료, 시간·종분배 참조, 실행 스크립트 | 이 문서 §2~§5 |

진행 방식(개선 계획 §5): ① 공통 형식 시험 → ② 부문별 입력을 생성기로 한꺼번에 생성 → ③ 부문 단위로 SMOKE 전 단계 실행·검증. 문제가 생기면 생성기를 고쳐 다시 만든다.

### 2. 원자료와 생성기

| 원자료 | 파일 | 규모 |
|---|---|---|
| CAPSS 2023 점오염원 | `점오염원_2023_전국__1_기본.txt` | 14,437줄 |
| CAPSS 2023 면오염원 | 압축 `면오염원(2023).zip` 안의 전국 파일 `전국a(2023).txt` | 9,615,471줄, 853 MB (시도 파일 17개를 이어 붙인 것이라 중간에 머리줄 16개 포함) |
| CAPSS 2023 이동오염원 | 압축 `이동오염원(2023).zip` 안의 전국 파일 `전국m(2023).txt` | 7,612,113줄, 710 MB |
| CAPSS 2023 바다 | `바다m(2023).txt` | 820,602줄 (지역 `9010000000`, 열 이름 `NOX`·`SOX` 대문자) |
| 코드리스트 | `코드리스트(2023).xlsx`, `02_코드리스트(2017).xlsx` | 2017 연료 목록은 2자리 연료 번호 계산에 사용 |
| 기존 참조 | 기존 체계 `4_Point/4_Area_Temporal_Reference_Profile.txt`, `5_Point/5_Area_Speciation_Reference_Profile.txt`, `9_Asia/9_Bio_TimeZone.txt` | 2020년 버전 |

생성기 `make_busan_2023_domestic_inputs.py` (첨부 ZIP의 `generators/`에 포함; GitHub에는 미등록) 한 번 실행으로 §3의 국내 입력이 모두 만들어진다(작성 환경 약 5분, 메모리 약 1.3 GB).

```bash
# capss/ 폴더에 point.txt, area.txt, mobile.txt, sea.txt 이름으로 원자료를 두거나 링크
python3 make_busan_2023_domestic_inputs.py --capss capss --code2017 코드리스트_2017.xlsx \
  --code2023 코드리스트_2023.xlsx --legacy <기존 참조 파일 폴더> --out <출력 폴더>
```

필요 모듈: `pandas`, `numpy`, `openpyxl`, `pyproj`.

### 3. 설치 패키지 구성

사용자 제공 `busan_2023capss_full_setup_20261022.zip` 하나에 들어 있다. **패키지 자체 및 생성기·부문 스크립트 원본은 아직 GitHub에 업로드하지 않았다.** 구분: **신규** = CAPSS 2023으로 새로 만듦, **개선** = 기존을 고쳐 다시 만듦, **기존** = 앞 단계에서 만든 것 그대로, **예제** = SMOKE 예제에서 설치 스크립트가 복사.

#### 3.1 공통 입력 (`EMIS/ge_dat/` 등)

| 파일 | 용도 | 쓰는 프로그램 | 구분 |
|---|---|---|---|
| `ge_dat/gridding/griddesc_busan_4domains.txt` | 27·09·03·01km 격자 | Grdmat, Smkmerge 등 | 기존 |
| `ge_dat/costcy_busan_2023capss_20261022.txt` | 지역 코드표: 2023 시군구 251(바다 포함) + 국외 7 + 생물성 1, 시간대 GMT | Smkinven | 신규 |
| `ge_dat/invtable_busan_2017capss_20261021.txt` | 오염물질 8종 정의 | Smkinven | 기존 |
| `ge_dat/temporal/holidays_korea_2012_2026_20261021.txt` | 공휴일 | Temporal | 기존 |
| `ge_dat/temporal/tpro_monthly·weekly·hourly_busan_2020ver_*.csv` | 월·요일·시간 프로파일 (시간은 UTC 기준) | Temporal | 기존 (프로파일 유지) |
| `smoke5.2/scripts/smk_dates/2026/` (12개) | 2026년 날짜 파일 | 실행 스크립트 | 기존 |
| `ge_dat/smkreport/sccdesc_busan_2023capss_20261022.txt` | SCC10 이름 (CAPSS 2023 SCC명 \| 연료명) | Smkreport | 신규 |

#### 3.2 국내 점오염원 (`kor_point`)

| 파일 | 용도 | 쓰는 프로그램 | 구분 |
|---|---|---|---|
| `2023capss_cb6/inputs/kor_point/kor_point_CAPSS2023_ff10_20261022.csv` | 점 인벤토리 FF10 (89,319줄, 굴뚝 14,289개) | Smkinven | 신규 |
| `2023capss_cb6/inputs/kor_point/stack_fill_log_20261022.csv` | 굴뚝 제원 보완 기록 | 검토용 | 신규 |
| `ge_dat/temporal/tref_kor_point_2023capss_20261022.csv` | 점 SCC10 → 시간 프로파일 | Temporal | 신규 |
| `ge_dat/speciation/gsref_kor_point_2023capss_20261022.csv` | 점 SCC10 → 종분배 프로파일 | Spcmat | 신규 |
| `ge_dat/point/pelvconfig_elevate_everything_17apr2020_v0.txt`, `pstk_13nov2018_v1.txt` | 굴뚝 상승 대상·기본 굴뚝 제원 | Elevpoint, Smkinven | 예제 |
| `2023capss_cb6/scripts/point/Annual_kor_point_onetime_2023capss_cb6.csh` | Smkinven·Spcmat·Grdmat·Smkreport·Elevpoint (1회) | — | 신규 |
| `2023capss_cb6/scripts/point/Annual_kor_point_daily_2023capss_cb6.csh` | Temporal·Smkmerge (날짜별, CMAQ inline 굴뚝 처리) | — | 신규 |

#### 3.3 국내 면·이동·바다 (`kor_area`, `kor_mobile`, `kor_sea`)

| 파일 | 용도 | 쓰는 프로그램 | 구분 |
|---|---|---|---|
| `2023capss_cb6/inputs/kor_area/kor_area_CAPSS2023_ff10_20261022.csv` | 면 인벤토리 (145,564줄) | Smkinven | 신규 |
| `2023capss_cb6/inputs/kor_mobile/kor_mobile_CAPSS2023_ff10_20261022.csv` | 이동 인벤토리: 도로 07, 비도로 08, 도로비산 12 (163,810줄) | Smkinven | 신규 |
| `2023capss_cb6/inputs/kor_sea/kor_sea_CAPSS2023_ff10_20261022.csv` | 바다 인벤토리: 지역 90100, 선박 SCC10 9종 (63줄) | Smkinven | 신규 |
| `ge_dat/gridding/surrogates/kor_2023capss_<GRID>/srg_<부문>_2023capss_<GRID>.txt` (12개) | **1km 격자 기반 대리자료** (4개 도메인 × 3부문) | Grdmat | 신규 |
| `ge_dat/gridding/srgdesc_kor_2023capss_<GRID>_20261022.txt` (4개) | 대리자료 번호 → 파일 | Grdmat | 신규 |
| `ge_dat/gridding/agref_kor_nonpoint_2023capss_20261022.txt` | SCC10 → 대리자료 번호 (면 1001~, 이동 3001~, 바다 5001~, 부문 기본 900·901·902) | Grdmat | 신규 |
| `ge_dat/temporal/tref_kor_nonpoint_2023capss_20261022.csv` | SCC10 → 시간 프로파일 | Temporal | 신규 |
| `ge_dat/speciation/gsref_kor_nonpoint_2023capss_20261022.csv` | SCC10 → 종분배 프로파일 | Spcmat | 신규 |
| `2023capss_cb6/scripts/nonpoint/Annual_kor_area·mobile·sea_2023capss_cb6.csh` | 부문 전 단계 실행 | — | 신규 |

#### 3.4 공통 종분배·보고서 (예제)

| 파일 | 용도 |
|---|---|
| `gscnv_SPECIATE_5_3_fromS2S_20230911_16jun2025_v1.txt` | VOC→TOG 프로파일별 계수 |
| `gspro_CB6R3_AE7_criteria_Spec_5_3_S2S_20230911_01nov2023_v0.txt` | VOC(TOG) → CB6 물질 |
| `gspro_PM2_5_AE6_Spec_5_3_S2S_20230911_01nov2023_v0.txt` | PM2.5 → AE 성분 |
| `gspro_static_cmaq_21feb2012_v13.txt` | CO·NH3·SO2(`0000`), PMC(`99999`) |
| `gspro_nox_hono_pf4_06aug2008_v0.txt` | NOX → NO 0.9 / NO2 0.092 / HONO 0.008 |
| `smkreport/repconfig/`, `orisdesc…`, `naicsdesc…` | 보고서 설정 |

#### 3.5 시나리오 설정과 검토 파일

| 파일 | 용도 |
|---|---|
| `2023capss_cb6/scripts/directory_definitions.csh` | 경로, `CASE=2023capss_cb6`, `GRID` 선택 |
| `2023capss_cb6/scripts/run_settings.txt` | 프로그램 끄기 설정 (`부문, 격자, 프로그램, ALL, 0, 0, N`) |
| `2023capss_cb6/inputs/scc10_reference_map_20261022.csv` | 4개 부문 802개 SCC·연료 조합의 10자리 SCC와 참조 출처 |
| `2023capss_cb6/inputs/generation_summary_20261022.csv` | 부문별 FF10 줄 수·합계·대리자료 줄 수 |
| `generators/` | 생성기 3개 (공통 입력, 시간 프로파일 변환, 2023 국내 입력) |

### 4. 설치

#### 4.1 한 번에 설치

압축 파일을 Linux 홈 폴더에 두고 실행한다.

```bash
unzip -o ~/busan_2023capss_full_setup_20261022.zip -d ~/busan_setup
bash ~/busan_setup/install_busan_2023capss.sh 2>&1 | tee ~/busan_install.log
```

설치 스크립트(`install_busan_2023capss.sh`)가 하는 일:

| 순서 | 내용 |
|---|---|
| 1 | `EMIS/` 폴더 구조와 `met → ../MCIP` 링크 (없으면 생성) |
| 2 | SMOKE 예제 실행 체계 `smoke5.2/` (없으면 예제에서 복사) |
| 3 | 패키지의 `EMIS/` 파일 55개 설치 (같은 이름은 덮어씀) |
| 4 | 예제 종분배·굴뚝·보고서 파일 복사 (이미 있으면 그대로) |
| 5 | 쓰지 않는 파일 삭제: 형식 시험 결과 `intermed/09KM/kor_point`, 옛 대응표, 국외 2010 인벤토리(`inputs/asia`) |
| 6 | **5개 실행 스크립트 × 4개 도메인이 참조하는 파일이 모두 있는지 확인** |
| 7 | 대리자료 폴더 크기, FF10 파일 목록 출력 |

#### 4.2 정상 설치 기준

- 6번에서 `all referenced files exist (5 scripts x 4 domains)`와 `ok` 5줄
- 7번에서 대리자료 폴더 4개(01KM 32M, 03KM 43M, 09KM 24M, 27KM 7.0M)와 FF10 4개

`MISSING`이 나오면 그 줄을 보고 빠진 파일을 확인한다. 작성 환경에서 가상 경로로 설치 스크립트를 시험해 위 결과를 확인했다. **사용자 Linux 서버의 최종 일괄 설치 성공 여부는 별도 로그 확인이 필요하다.**

### 5. 입력 생성 규칙 요약

상세 근거는 [배출량 개선 계획](SMOKE_Emission_Improvement_Plan.md) §4.

| 항목 | 규칙 |
|---|---|
| 단위 | kg/yr ÷ 907.18474 = short ton/yr. FF10 저감효율 칸은 `0` |
| 지역 코드 | 행정구역코드 앞 5자리 (바다 `90100`), FF10 머리말 `#COUNTRY=ASIA` |
| SCC10 | SCC 8자리 + 기존 2자리 연료 번호 (2017 연료 목록에서 `xx00` 줄을 뺀 순번, `20500`→44, `999xx`→99). 2017 목록에 없는 연료: `23101` G1, `50101~50103` G2~G4, `50201·50202` G5·G6, `41300`(CNG) C1 → LNG `82` 참조 / `80201·80202` S1·S2 → 유연탄 `07` 참조 |
| 참조 보완 | ① 정확 일치 → ② 빌린 연료 → ③ 같은 SCC·**같은 연료 계열**(연료 5자리 앞 3자리, 가장 가까운 번호) → ④ 같은 SCC 다른 연료 → ⑤ 같은 상위 분류(앞 6자리) → ⑥ SMOKE 기본값. 점은 기존 점 참조, 면·이동·바다는 기존 면 참조 사용 |
| 굴뚝 제원 | 결측·0 이하: 같은 굴뚝 → 같은 SCC·연료 중앙값 → 같은 SCC 중앙값 → 전체 중앙값. 중복 148줄 합침. FF10은 ft, °F, ft/s |
| 좌표 | TM(Bessel, Tokyo 측지계, 중부원점 127°00′10.405″, FE 200 km, FN 500 km) → 위경도 → 모델 Lambert(구 6,370 km) |
| 대리자료 | (지역, SCC10)별 1km 격자 분포. 가중치는 그 SCC10의 전국 최대 오염물질. 1km 격자를 작은 점으로 나눠(27km 2×2, 09km 3×3, 03km 5×5, 01km 10×10) 모델 격자와 겹치는 비율 계산. 비율은 지역 전체 대비라 영역 밖 몫은 빠짐. 부문 기본 대리자료(900·901·902)는 전체 오염물질 질량 분포 |

#### 5.1 생성 결과 (short ton/yr)

| 부문 | FF10 줄 | CO | NOx | SO2 | PM10 | PM2.5 | VOC | NH3 |
|---|---|---|---|---|---|---|---|---|
| kor_point | 89,319 | 347,311 | 201,410 | 106,298 | 12,258 | 9,071 | 221,154 | 25,362 |
| kor_area | 145,564 | 214,732 | 139,736 | 25,210 | 56,848 | 15,844 | 668,272 | 240,057 |
| kor_mobile | 163,810 | 275,848 | 459,587 | 4,059 | 58,424 | 24,527 | 86,731 | 1,909 |
| kor_sea | 63 | 46,890 | 90,191 | 3,609 | 3,678 | 3,422 | 15,324 | 8 |

#### 5.2 참조 출처 비율 (종분배, 배출량 기준)

| 부문 | 정확 일치 (NOx / VOC) | 같은 연료 계열 | 그 밖의 보완 | 기본값 |
|---|---|---|---|---|
| kor_point | 83.5% / 96.2% | 0.1% / 3.4% | 16.2% / 0.4% | 0.2% / 0% |
| kor_area | 93.0% / 96.9% | 5.1% / 2.8% | 0% / 0% | 1.9% / 0.3% |
| kor_mobile | 0% / 0% | 96.8% / 90.5% | 3.2% / 9.5% | 0% / 0% |
| kor_sea | 0% / 0% | 99.9% / 100% | 0.1% / 0% | 0% / 0% |

이동·바다는 2023 연료가 2017보다 저유황 등급(예: 경유 0.001%)으로 바뀌어 연료 번호가 달라졌다. "같은 연료 계열" 규칙으로 같은 경유·휘발유 참조를 이어받는다. 면의 기본값 1.9%는 기존 참조에 없는 SCC 3종(`01010500`, `11020100`, `11020200`)이다.

#### 5.3 대리자료 검증

| 확인 | 결과 |
|---|---|
| (지역, 번호)별 비율 합 > 1 | 12개 파일 모두 0건 |
| 27·09km 비율 합 중앙값 | 1.0000 (영역 안에 전부 배분) |
| 바다 03·01km | 값 있음 (3km 16,562줄, 1km 15,790줄). 전국 바다 배출 중 01km 영역 몫 약 2.3% → **기존 3·1km 해상 대리자료 부재 해결** |

### 6. ① 공통 형식 시험 결과 (2026-10-22, Linux)

2023 점오염원 FF10(저감효율 칸 비움)을 09KM로 Smkinven만 실행했다(`run_settings.txt`로 Spcmat·Grdmat·Elevpoint 등 끔).

| 확인 | 결과 |
|---|---|
| Smkinven | `Normal Completion`, 배출원 14,289개(생성기 결과와 일치), 8개 물질 + PMC 계산 |
| 2023 코드표·지역 코드 | 오류 없음 |
| 영문 SCC (`…G6` 등) | `000000000002010100G6`처럼 20자리로 읽힘 → 그대로 사용 |
| 굴뚝 제원 | 결측 대체 0건(생성기에서 모두 보완). 높이 0.1~0.4 m 69줄만 SMOKE 하한 0.5 m로 조정(NOx 28.7 t) |
| 경고 | 평균 일배출량·저감효율 빈칸 경고(무해) → 생성기에서 저감효율 `0` 기입으로 해결 |
| Smkreport 오류 | `PSSUP` 없음: 시험에서 Spcmat를 꺼서 생긴 것, 전체 실행에서 해소 |

### 7. 다음: ③ 부문별 실행

각 부문을 09KM로 먼저 통과시킨 뒤 27·03·01KM로 넓힌다.

| 순서 | 부문 | 명령 (`EMIS/2023capss_cb6/scripts/` 아래 폴더에서) |
|---|---|---|
| 1 | 국내 점 (1회) | `cd point; GRID=09KM ./Annual_kor_point_onetime_2023capss_cb6.csh 2>&1 \| tee ../logs/kor_point_onetime_09KM.log` |
| 2 | 국내 점 (날짜별) | `GRID=09KM ./Annual_kor_point_daily_2023capss_cb6.csh 2>&1 \| tee ../logs/kor_point_daily_09KM.log` |
| 3 | 국내 면 | `cd nonpoint; GRID=09KM ./Annual_kor_area_2023capss_cb6.csh 2>&1 \| tee ../logs/kor_area_09KM.log` |
| 4 | 국내 이동 | `GRID=09KM ./Annual_kor_mobile_2023capss_cb6.csh 2>&1 \| tee ../logs/kor_mobile_09KM.log` |
| 5 | 바다 | `GRID=09KM ./Annual_kor_sea_2023capss_cb6.csh 2>&1 \| tee ../logs/kor_sea_09KM.log` |

검증: 각 부문의 Smkreport 시도·시군구·SCC 합계를 `generation_summary`의 short ton 합계와 비교한다(영역 밖 몫은 따로 계산).

### 8. 남은 사항

| 항목 | 시점 |
|---|---|
| 점오염원 날짜별 실행에서 기상(MCIP) 파일 이름 대응 필요 여부 (inline 방식은 Laypoint 미사용) | ③-2 |
| 이동오염원 도로 구분: 원자료에 도로 코드가 없어 SCC10은 연료만 반영 | ③-4 검토 |
| 국외 HTAP_v3.1 다운로드·남한 제외·예제 HTAP 부문 적용 | 국외 부문 |
| 생물성 BEIS4 / MEGAN 3.x | 생물성 부문 |
| CMAQ 5.5 메커니즘과 배출 물질 대응 | 병합 |
| 2026년 공휴일 공식 달력 대조 | 실행 전 |

> **GitHub 파일 상태(2026-10-22):** 이 절은 기존 `SMOKE_Busan_Case_Run_Guide.md`에 직접 통합했다. [2023capss 스크립트 폴더](files/busan/2023capss/)에 **설치 스크립트 1개, CASE 설정 파일 2개, 실행 스크립트 5개**를 등록했다. 반면 **CAPSS 2023 주요 생성기 1개는 GitHub에 등록했다. 공통 생성기 1개는 기존 `files/busan/`에 이미 등록되어 있다. 이전 단계 변환 생성기 1개, 실제 FF10 4개, surrogate 12개, 참조표 등 ZIP의 전체 입력자료는 GitHub에 모두 등록된 상태가 아니다.** 따라서 저장소 파일만으로 단독 설치할 수 없으며 전체 설치에는 사용자가 제공한 ZIP 원본이 필요하다.


### 7.3 ZIP 패키지 원본 및 재현에 필요한 파일 관리

2026-10-22 제공된 `busan_2023capss_full_setup_20261022.zip`에는 설치 스크립트 `install_busan_2023capss.sh`, 생성기 3개, 국내 점·면·이동·바다 FF10 4개, 4개 도메인 × 3부문 surrogate 12개, 실행 스크립트 5개, 공통 참조·설정 및 검증 CSV가 포함된다.

- **재현 파일 관리:** 설치 스크립트·핵심 생성기·CASE 실행 스크립트는 `docs/smoke/files/busan/2023capss/`에 원래 상대경로를 유지해 보관한다. 공통 입력 생성기는 이전 `docs/smoke/files/busan/make_busan_common_inputs.py`에 이미 있다. 나머지 실제 입력자료는 원본 ZIP이 필요하다.
- **대용량 원자료 분리:** 약 155 MB의 설치 해제 데이터 중 대형 FF10 및 surrogate는 저장소 용량을 고려해 ZIP 원본 별도 보관과 생성기·무결성 검증값으로 관리한다. GitHub에 등록된 파일만으로 전체 설치가 가능하다고 오인해서는 안 된다.
- **파괴적 설치 동작:** `install_busan_2023capss.sh`는 기존 파일을 덮어쓰고, `2023capss_cb6/intermed/09KM/kor_point` 및 `2023capss_cb6/inputs/asia` 등을 삭제한다. 재실행 전에 백업과 경로 확인이 필요하다.
- **실행 수준 구별:** 09KM 점 Smkinven **시험 정상 종료**와 점 `onetime` 전체 정상 종료는 서로 다른 상태다. `Spcmat`가 비활성화된 형식 시험에서 `PSSUP` 미생성으로 Smkreport 오류가 발생했으며, 전체 실행의 성공은 아직 검증되지 않았다.

다음 실제 진행은 **국내 점 09KM onetime → daily → 국내 면 → 이동 → 바다**의 순서이며, 각 부문에서 실제 실행 로그와 Smkreport 총량 QA를 별도로 기록한다.

### 7.4 GitHub에 등록한 설치·실행 스크립트

이 경로들은 사용자 제공 ZIP의 2026-10-22 국내 배출량 시나리오를 위한 스크립트다. **개별 GitHub 파일의 Linux 동작 검증은 수행하지 않았고, 입력자료 일괄 설치·부문 전체 실행도 아직 확인되지 않았다.**

| 역할 | GitHub 파일 |
|---|---|
| 전체 입력 설치 | [`install_busan_2023capss.sh`](files/busan/2023capss/install_busan_2023capss.sh) (원본 ZIP과 일치) |
| CAPSS 2023 국내 입력 생성 | [`make_busan_2023_domestic_inputs.py`](files/busan/2023capss/generators/make_busan_2023_domestic_inputs.py) (원본 ZIP과 일치) |
| CASE 기본 경로·변수 | [`directory_definitions.csh`](files/busan/2023capss/EMIS/2023capss_cb6/scripts/directory_definitions.csh) |
| 프로그램 실행 설정 | [`run_settings.txt`](files/busan/2023capss/EMIS/2023capss_cb6/scripts/run_settings.txt) |
| 국내 점 onetime | [`Annual_kor_point_onetime_2023capss_cb6.csh`](files/busan/2023capss/EMIS/2023capss_cb6/scripts/point/Annual_kor_point_onetime_2023capss_cb6.csh) |
| 국내 점 daily | [`Annual_kor_point_daily_2023capss_cb6.csh`](files/busan/2023capss/EMIS/2023capss_cb6/scripts/point/Annual_kor_point_daily_2023capss_cb6.csh) |
| 국내 면 | [`Annual_kor_area_2023capss_cb6.csh`](files/busan/2023capss/EMIS/2023capss_cb6/scripts/nonpoint/Annual_kor_area_2023capss_cb6.csh) |
| 국내 이동 | [`Annual_kor_mobile_2023capss_cb6.csh`](files/busan/2023capss/EMIS/2023capss_cb6/scripts/nonpoint/Annual_kor_mobile_2023capss_cb6.csh) |
| 국내 바다 | [`Annual_kor_sea_2023capss_cb6.csh`](files/busan/2023capss/EMIS/2023capss_cb6/scripts/nonpoint/Annual_kor_sea_2023capss_cb6.csh) |

등록된 핵심 생성기: [`make_busan_2023_domestic_inputs.py`](files/busan/2023capss/generators/make_busan_2023_domestic_inputs.py) (GitHub 파일과 사용자 제공 ZIP 원본의 Git blob SHA 일치). 기존 공통 생성기: [`make_busan_common_inputs.py`](files/busan/make_busan_common_inputs.py) (ZIP과 일치). `make_busan_step4_inputs.py`는 ZIP 내부에 있지만 이 경로에는 별도 등록하지 않았다.

설치 ZIP 원본: `busan_2023capss_full_setup_20261022.zip` (SHA-256: `34f5c8b7b8134cf2867de44cff0e1a838a8caa4831a35bce88179e2abddfb367`, 검사 결과 ZIP 내부 오류 없음). **GitHub에 ZIP 전체를 올린 것은 아니다.**

**주의:** `directory_definitions.csh`의 `EMF_LOGNAME`은 절대경로가 중복 결합될 가능성이 있으므로 실제 실행 전 수정·검증이 필요하다. 설치 스크립트는 중간결과를 지우므로 해당 경로 백업 여부를 확인하고 수행한다.
