# SMOKE–CMAQ 공식 스크립트 기반 CASE 반복 실행 원칙 및 검증 기록

> 작성: 2026-11-24 · 갱신: 2026-11-25 · 대상: BUSAN/TEST_20260901 · 상태: **공식 SMOKE 병합 검증 완료([06](../smoke/06_SMOKE_Busan_Sector_Merge_Guide.md)) / ICON·BCON 실행 미검증**
>
> 이 문서는 기존 [배출량 반복 실행](EMISSIONS_CASE_RUN.md), [CMAQ 실행 준비 상태](CMAQ_CASE_STATUS.md)를 보완한다. **공식 도구의 미실행 명령을 성공한 절차로 기록하지 않는다.** 신규 시스템에서의 설치·컴파일과 신규 CASE의 반복 실행은 분리한다.

## 1. 운영 원칙

1. **모델이 제공한 도구와 실행 스크립트를 우선 사용한다.** SMOKE의 부문별 처리와 병합은 설치된 SMOKE 5.3 실행체계를, CMAQ ICON·BCON·CCTM은 설치된 CMAQ 5.5 실행체계를 기준으로 한다.
2. 원본 설치 스크립트는 보존하고, **CASE 전용 사본**에 경로·기간·도메인·메커니즘·출력명을 설정한다. 실사용할 정확한 스크립트·실행파일·환경변수는 **서버에서 확인한 뒤** 기록한다.
3. Python은 원자료 전처리에서 기존 문서가 명시한 생성기와 **읽기 전용 QA, 독립 수치 대조**에 사용한다. 모델 공식 단계의 대체를 기본 운영절차로 간주하지 않는다.
4. 로그, 실제 실행명령, 종료 코드, 산출물, QA 결과를 **CASE·도메인·날짜별** 보존한다. 기존 산출물을 덮어쓰지 않는다.
5. GitHub에는 실행 스크립트의 재현 가능한 설정 및 명령, 문서, 소형 설정 파일만 보관한다. 원본 CAPSS/HTAP, 대형 NetCDF 배출량·농도파일, 계정 정보는 올리지 않는다. CMAQ benchmark 자료와 실행 기록은 이 CASE 문서에 추가하지 않는다.

## 2. BUSAN CASE 기준값 — 현재 확인된 사실

| 항목 | 값 또는 상태 |
|---|---|
| CASE | `/home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901` |
| 모의 시험기간 | 2026-08-31 **01:00 UTC** ~ 2026-09-02 00:00 UTC |
| MCIP | 27/09/03/01KM, 각 48시간 기록; 00시부터의 MCIP 재실행은 현재 WRF 조건에서 수행하지 않기로 확정 |
| SMOKE | CAPSS 2023: `kor_area`, `kor_mobile`, `kor_sea`, `kor_point` |
| 국외 | HTAP v3.2 기반 8개 부문; 원자료의 대한민국 배출량 제거 확인 |
| 지표면 통합 배출량 | 2026-08-31 및 09-01 × 4도메인, 8개 파일 생성 및 독립 수치 대조 **완료** |
| 통합 생성 방식 | **SMOKE 5.3 공식 병합**(`smk_sectormerge_emf.csh` → `mrggrid`, [06](../smoke/06_SMOKE_Busan_Sector_Merge_Guide.md)). 이전 Python 합산본(`cmaq_ready/merged`)은 비교 참조용 |
| 통합 화학종 | 27·09·03KM 63개(`UNK`·`VOC_INV` 포함, CMAQ 미사용), 01KM 60개(국외 제외). 국내 `SOAALK`는 2026-11-25 tracer 종분배 추가로 생성 |
| 수치 QA | 공식 병합 8개 파일: 부문 합계와 상대차 5×10⁻⁸ 이하, 음수 0(`check_merge_totals.py`). 국내 SOAALK 반영 전 공식 병합은 Python 참조본과 공통 61종 상대차 5×10⁻⁸ 이하(06 부록 A) |
| 국내 점오염원 | `inln_mole` + `stack_groups` 별도 입력; 지표면 파일과 직접 합치지 않음 |
| 생물성 | SMOKE 병합에 추가하지 않고 CMAQ inline MEGAN 3.2 적용 계획 |
| IC/BC | 부산 CASE용 ICON·BCON 산출물 및 실제 실행 **미확인·미검증** |

**검증 범위:** 이전 Python 합산본은 사용자 제공 `CMAQ_case_step11~14.txt`에, 공식 SMOKE 병합과 부문 합계 검증은 06 §7에 기록했다. CCTM 입력 연결 및 모의는 미검증이다.

## 3. SMOKE: 공식 병합 절차 — **검증 완료(2026-11-24~25)**

확정된 스크립트 사본·수정 사항·명령·정상 기준은 [06 부문 병합 가이드](../smoke/06_SMOKE_Busan_Sector_Merge_Guide.md)를 따른다(수정 사항 §4, 실행 §6, 확인 §7). 아래 3.1~3.3은 검증 전 계획 기록으로 남긴다.

### 3.1 기존 확인된 입력

- 도메인별 지표면 부문 입력: `EMIS/2023capss_cb6/premerged/<sector>/emis_mole_<sector>_<YYYYMMDD>_<GRID>_cmaq_cb6ae7_2023capss_cb6.ncf`
- 국내 지표면: `kor_area`, `kor_mobile`, `kor_sea`
- 국외 지표면: `htap_energy`, `htap_industry`, `htap_transport`, `htap_resident`, `htap_agriculture`, `htap_waste`, `htap_intship`, `htap_aviation`
- 국내 점: `EMIS/2023capss_cb6/smoke_out/2023capss_cb6/<GRID>/cmaq_cb6ae7/kor_point/`의 `inln_mole`, `stack_groups` (별도 연결)
- 기존 Python 통합 참조 파일: `EMIS/2023capss_cb6/cmaq_ready/merged/emis_mole_all_<YYYYMMDD>_<GRID>_cmaq_cb6ae7_2023capss_htap.ncf`

### 3.2 공식 SMOKE 병합 실행 전에 확인할 사항

- 설치된 SMOKE 5.3에 **격자 부문 병합 프로그램/스크립트**가 있는지 확인한다. `Mrggrid` 또는 해당 버전의 병합 실행 체계를 **실제 설치 디렉터리와 예제에서 확인**한다. 명칭만으로 실행 가능하다고 가정하지 않는다.
- 공식 예제 `sectorlist`, `ASSIGNS`, `directory_definitions.csh`의 입력 파일 지정 방식 및 순서를 확인한다.
- 11개 부문, 2일, 4개 도메인 입력을 연결한다. `htap_aviation`에는 `PMC`가 없으므로 누락종 처리를 확인한다.
- 61종 합집합에 대해 `SOAALK`, `SULF`를 유지하고 `UNK`, `VOC_INV`의 미사용 처리를 결정한다. **SMOKE 공식 병합 출력과 CMAQ DESID 수용 여부**를 확인한다.
- `GDNAM` 표기 차이(`<GRID>` 대 `<GRID>_CROSS`)는 격자값이 같다는 사실과 구분해 공식 도구의 입출력 요구를 검사한다.
- 기존 Python 통합파일은 덮어쓰지 않는다. 다른 출력 폴더에 생성한 후 원본 11부문 합계 및 Python 참조 결과와 대조한다.

### 3.3 공식 명령 확정 기록 양식 — 06 문서로 대체

```text
SMOKE version / installed executable path:
Original example script / commit:
CASE-specific script path:
GRIDDESC / GDNAM:
YYYYMMDD / GRID / mechanism:
sectorlist and emissions file mapping:
Actual invocation command:
Log path / completion message / exit code:
Output name / file format / species / TFLAG:
Float32 comparison to 11 input sectors:
Differences or limitations:
```

실제 실행이 검증되면 이 절에 **확인된 스크립트 사본, 설정 차이, 정확한 명령, 예상 결과**를 추가한다. 그 전에는 추정 실행명령을 작성하지 않는다.

## 4. CMAQ: 공식 ICON·BCON 절차 수립 (다음 검증 대상)

1. 설치본 `/home/woogon/CMAQ_MODEL/CMAQv5.5/PREP/icon/` 및 `PREP/bcon/`의 공식 실행 스크립트·실행파일·농도 프로파일 후보를 **읽기 전용으로 확인**한다.
2. 최초 외부 27 km 도메인은 프로파일 기반 또는 신뢰할 수 있는 외부 대기화학 모델 농도자료 기반의 IC/BC 중 선택한다. **프로파일 기반 자료는 공간·시간 변화 재현에 한계**가 있어 우선 시험용으로 분류한다.
3. `MCIP/27KM/`의 `GRIDCRO2D`, `GRIDBDY2D`, `METCRO3D`, `METBDY3D`와 CCTM 화학기작 `cb6r5_ae7_aq`, 수직층을 대조한다.
4. ICON 기준시각은 **2026-08-31 01:00 UTC**, BCON은 모의 종료시각 2026-09-02 00:00 UTC까지 필요한 기록을 포함해야 한다. 프로그램이 요구하는 종료 기록 및 시각 표지 규칙은 실행 전에 확인한다.
5. 각 실행 스크립트는 설치 원본을 수정하지 않고 CASE별 사본으로 만든다. 출력은 `CASE/CMAQ/`의 별도 폴더로 격리한다.
6. 27 km CCTM을 성공적으로 수행한 후 내부 도메인의 ICON/BCON을 **상위 도메인 농도장과 시간·경계 위치를 맞추어** 준비한다.

### 공식 명령 확정 기록 양식 — **아직 미검증**

```text
ICON/BCON source version and build:
Original script and copied CASE script:
Profile or external concentration source:
CCTM chemistry and DESID configuration:
MCIP grid / vertical layers:
Start/end UTC:
Exact invocation command:
Log path / normal termination:
Output file name / dimension / species / TFLAG:
Cross-check with CCTM expected input:
```

## 5. 재사용할 때 필수로 바꾸는 CASE 매개변수

| 매개변수 | 새 CASE 적용 시 확인 |
|---|---|
| `ROOT`, `CASE`, `SMOKE_HOME`, `CMAQ_HOME` | 설치 디렉터리·스크립트 실제 존재 |
| 날짜·시간(UTC) | MCIP 실제 시작/끝, 배출량 `TFLAG`, ICON/BCON 시각 |
| `GRID`, WRF nest, `GRIDDESC` | 격자 원점·셀 크기·행열·투영·경계 |
| 배출 시나리오 | CAPSS 기준연도, HTAP 버전, 국내·국외 제외 마스크 |
| mechanism / DESID | 화학종 매핑, 가스·입자 단위, 중복·누락 화학종 |
| inline emission | 점오염원 stack 수와 `inln_mole` 날짜, MEGAN 옵션 |
| 산출물 | 기존 출력 덮어쓰기 금지, 로그·QA·버전·Git 커밋 SHA |

## 6. 참고 원문

- [SMOKE 국내 CAPSS 2023 재현 가이드](../smoke/04_SMOKE_Busan_Case_Run_Guide.md)
- [SMOKE HTAP v3.2 재현 가이드](../smoke/05_HTAP_v32_Reproduction_Checklist.md)
- [배출량 CASE 운영 목차](EMISSIONS_CASE_RUN.md)
- [CMAQ CASE 실행 준비 상태](CMAQ_CASE_STATUS.md)
- [프로젝트 기본계획](../planning/00_CMAQ_Project_Master_Plan.md)

**후속 문서화 기준:** 실제로 실행하고 성공 여부를 검사한 **공식 스크립트 원문·설정값·명령·로그·출력 검증**만 '검증 완료'로 승격한다.
