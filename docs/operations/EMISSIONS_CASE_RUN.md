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

**주의:** §7.1 genagmat.f 패치는 설치/소스 교체 시 작업이지 Case마다 재컴파일하는 단계가 아니다. §8.0 삭제·초기화 명령은 기존 산출물 보존 후 실제 Case 위치를 검증한다.

## 2. 국외 HTAP v3.2 — SMOKE 5.3
**기존 상태:** 2020년 0.1° 연간 flux를 사용, 남한 CAPSS 셀 제거, 탄소 조정 후 27·09·03KM × 8묶음 완료(제공 실행기록); 01KM 국외 0으로 제외. 이 결과는 새 grid/시나리오에도 01KM을 항상 제외하라는 규칙이 아니다.

| 반복 실행 단계 | 변경값 | 명령 원문 |
|---|---|---|
| 원자료/체크섬 | 9종 HTAP ZIP, 버전·기준연도·sha256 | [국외 가이드 §3.2](../smoke/05_HTAP_v32_Reproduction_Checklist.md) |
| 전처리 | `make_busan_htap_v32_inputs.py`: `--htap`, `--year`, `--capss`, `--example`, `--invtable`, `--final`, `--out` | [§5.2](../smoke/05_HTAP_v32_Reproduction_Checklist.md) |
| 설치된 실행환경 확인 | `smkinven.f`/ASSIGNS 패치 이미 적용됐는지 확인; 수정 필요할 때만 재컴파일 | [§6](../smoke/05_HTAP_v32_Reproduction_Checklist.md) |
| 국외 8묶음 | INTSHIP, AVIATION, ENERGY, INDUSTRY, TRANSPORT, RESIDENT, WASTE, AGRICULTURE | [§7](../smoke/05_HTAP_v32_Reproduction_Checklist.md) |
| 출력 검사 | 27·09·03KM 파일/로그/배출종, 남한 마스크, 01KM 0 여부, 국내·국외 비율 | [§8](../smoke/05_HTAP_v32_Reproduction_Checklist.md) |

**기존 처리 결정과 한계:** FUGITIVE·SOLVENTS의 INDUSTRY 프로파일 대응은 잠정이며, 남한 제거 마스크는 해안·접경 국외 배출도 제거할 수 있다. BC/OC 질량 조정은 국외 문서 §4–5의 원칙을 그대로 따르며 변경 시 검증값을 다시 산정한다. 새로운 CAPSS 원본, 0.1° 격자, grid 또는 HTAP 원자료로 바꾸면 마스크·입력 생성부터 재검토한다.

## 3. MEGAN 3.2 — CMAQ inline 입력
**기존 상태:** 4도메인 CT3·EFMAP·LDF 생성/재현 기록. 운영 LDF 교체 및 CCTM 연결은 미완료.

- 최초 준비: [MEGAN §5 설치·컴파일](../megan/01_MEGAN32_Input_Preprocessing_Guide.md) — 새 시스템이나 도구 변경 시.
- Case별 재생성: [§6 도메인별 `run_megan_domain.sh` 절차](../megan/01_MEGAN32_Input_Preprocessing_Guide.md) — grid·식생자료·변환 설정 변경 시.
- 파일·격자 검증: [§7](../megan/01_MEGAN32_Input_Preprocessing_Guide.md).
- **아직 검증되지 않음:** [§8 CCTM inline 연결 및 MEGAN_SOILOUT/MEGAN_SOILINP](../megan/01_MEGAN32_Input_Preprocessing_Guide.md).

## 4. 병합 및 CMAQ 전달 — 미완료
국내와 국외 각 부문 결과가 생성된 사실만으로 CCTM용 병합 파일이 유효하다는 뜻은 아니다. **부문별 단위·화학종·시간축·grid·수직층·중복 영역을 검증하고 병합을 수행한 다음 CCTM에 연결해야 한다.** 원문에서 미실행으로 기록한 작업을 임의의 성공 명령으로 채우지 않는다.
