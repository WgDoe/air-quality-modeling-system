# 배출량 Case 반복 실행 가이드 — 국내 CAPSS / 국외 HTAP / MEGAN

> **설치/소스 패치는 별도** [설치 목차](INSTALLATION_INDEX.md). 이 문서에서는 새 Case에서 다시 만들어야 하는 입력과 실행 단계를 안내한다. 전체 실제 명령은 연결된 검증 원문을 사용한다.

## 1. 국내 CAPSS 2023 — SMOKE 5.3
**기존 상태:** 4부문(점·면·이동·바다) × 4도메인 27·09·03·01KM 완료(제공 실행기록). CMAQ-ready 병합·CCTM 연결 미검증.

| 반복 실행 단계 | 검토 항목 | 명령 원문 |
|---|---|---|
| 원자료 | CAPSS 2023 원본 4부문·코드리스트, 원자료 위치와 수정 여부 | [국내 가이드 §3](../smoke/04_SMOKE_Busan_Case_Run_Guide.md) |
| 생성기 | `make_busan_2023_domestic_inputs.py`, 원자료·CASE·출력 경로 | [§6](../smoke/04_SMOKE_Busan_Case_Run_Guide.md) |
| 입력 설치 | 패키지의 참조파일과 부문별 실행 스크립트 배치 | [§7](../smoke/04_SMOKE_Busan_Case_Run_Guide.md) |
| 부문 실행 | `kor_point`, `kor_area`, `kor_mobile`, `kor_sea` | [§8.1–8.4](../smoke/04_SMOKE_Busan_Case_Run_Guide.md) |
| QA | 그리드별 합계·로그·종·시간·단위 | [§8.5, §9](../smoke/04_SMOKE_Busan_Case_Run_Guide.md) |

### 새 CASE에서 바꾸는 값 (같은 도메인·CAPSS 원자료)

- 날짜는 [`mcip_period.py`](../smoke/files/busan/2023capss/EMIS/2023capss_cb6/scripts/utils/mcip_period.py)가 해당 CASE의 MCIP 파일에서 읽는다. 기간을 직접 여러 스크립트에 일괄 하드코딩하지 않는다.
- CASE 경로: [국내 가이드 §5](../smoke/04_SMOKE_Busan_Case_Run_Guide.md)의 `B=`, §8.0의 `C=`·`expected=`, §8.1–8.5의 경로 및 `directory_definitions.csh`의 `INSTALL_DIR`를 새 CASE로 변경·검사한다.
- 2026년 이외 기간의 CASE라면 `smk_dates/<연도>` 파일과 공휴일 참조파일을 먼저 준비하고 실제 연도 범위를 검사한다. **다른 연도의 실행은 아직 검증되지 않았다.**

**주의:** §7.1 genagmat.f 패치는 설치/소스 교체 시 작업이지 Case마다 재컴파일하는 단계가 아니다. §8.0 삭제·초기화 명령은 기존 산출물 보존 후 실제 Case 위치를 검증한다.

## 2. 국외 HTAP v3.2 — SMOKE 5.3
**기존 상태:** 2020년 0.1° 연간 flux를 사용, 남한 CAPSS 셀 제거, 탄소 조정 후 27·09·03KM × 8묶음 완료(제공 실행기록); 01KM 국외 0으로 제외. 이 결과는 새 grid/시나리오에도 01KM을 항상 제외하라는 규칙이 아니다.

| 반복 실행 단계 | 변경값 | 명령 원문 |
|---|---|---|
| 원자료/체크섬 | 9종 HTAP ZIP, 버전·기준연도·sha256 | [국외 가이드 §3.2](../smoke/05_HTAP_v32_Reproduction_Checklist.md) |
| 전처리 | `make_busan_htap_v32_inputs.py`: `--htap`, `--year`, `--capss`, `--example`, `--invtable`, `--final`, `--out` | [§5.2](../smoke/05_HTAP_v32_Reproduction_Checklist.md) |
| CASE별 파일 설치(새 CASE마다 필수) | 설치된 `smkinven` 패치 확인, CASE `ASSIGNS.emf`, `directory_definitions.csh`의 `INSTALL_DIR`, HTAP 실행 스크립트·입력 19개 | [§6.2](../smoke/05_HTAP_v32_Reproduction_Checklist.md#htap-case-install) |
| 국외 8묶음 | INTSHIP, AVIATION, ENERGY, INDUSTRY, TRANSPORT, RESIDENT, WASTE, AGRICULTURE | [§7](../smoke/05_HTAP_v32_Reproduction_Checklist.md) |
| 출력 검사 | 27·09·03KM 파일/로그/배출종, 남한 마스크, 01KM 0 여부, 국내·국외 비율 | [§8](../smoke/05_HTAP_v32_Reproduction_Checklist.md) |

**SMOKE 소스 수정·재컴파일은 최초 설치 또는 소스 교체 때 [§6.1](../smoke/05_HTAP_v32_Reproduction_Checklist.md#htap-install-once)에서만 수행한다.**

**기존 처리 결정과 한계:** FUGITIVE·SOLVENTS의 INDUSTRY 프로파일 대응은 잠정이며, 남한 제거 마스크는 해안·접경 국외 배출도 제거할 수 있다. BC/OC 질량 조정은 국외 문서 §4–5의 원칙을 그대로 따르며 변경 시 검증값을 다시 산정한다. 새로운 CAPSS 원본, 0.1° 격자, grid 또는 HTAP 원자료로 바꾸면 마스크·입력 생성부터 재검토한다.

## 3. MEGAN 3.2 — CMAQ inline 입력
**현재 상태(2026-11-16):** 4도메인 CT3·EFMAP 생성 기록이 있고, 수정된 LDF는 CSV/NetCDF 값 일치 및 운영 파일 MD5·`cmp` 동일성이 사용자 제공 서버 출력에서 확인됐다. **CCTM 연결·식생배출량 계산 검증은 미완료.**

- 최초 준비: [MEGAN §5 설치·컴파일](../megan/01_MEGAN32_Input_Preprocessing_Guide.md) — 새 시스템이나 도구 변경 시.
- Case별 재생성: [§6 도메인별 `run_megan_domain.sh` 절차](../megan/01_MEGAN32_Input_Preprocessing_Guide.md) — grid·식생자료·변환 설정 변경 시.
- §6.2 실행 명령의 변경값: `C`(CASE 경로), `WRF_START`(기준값 `2026-08-31_00:00:00`), `MCIP_STAMP`(기준값 `2026083100`). 새 CASE의 WRF/MCIP 시간과 맞추어 수정한다. CT3·EFMAP·LDF는 시간 불변형 입력이므로 **기간만 변경하고 도메인·식생자료·설정이 동일**하면 재사용 여부를 먼저 검토한다(새 CASE 재사용은 미검증).
- 파일·격자 검증: [§7](../megan/01_MEGAN32_Input_Preprocessing_Guide.md).
- **아직 검증되지 않음:** [§8 CCTM inline 연결 및 MEGAN_SOILOUT/MEGAN_SOILINP](../megan/01_MEGAN32_Input_Preprocessing_Guide.md).

## 4. 병합 및 CMAQ 전달 — 미완료
국내와 국외 각 부문 결과가 생성된 사실만으로 CCTM용 병합 파일이 유효하다는 뜻은 아니다. **부문별 단위·화학종·시간축·grid·수직층·중복 영역을 검증하고 병합을 수행한 다음 CCTM에 연결해야 한다.** 원문에서 미실행으로 기록한 작업을 임의의 성공 명령으로 채우지 않는다.
