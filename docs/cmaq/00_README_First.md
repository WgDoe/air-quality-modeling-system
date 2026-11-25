# CMAQ 문서 읽는 순서 (2026-11-25)

> **설치·컴파일과 CASE 실행을 나눠 기록한다.** 01은 새 시스템에서 한 번(또는 메커니즘·소스·라이브러리를 바꿀 때만) 따르는 설치 문서다. 02부터는 CASE가 바뀔 때마다 반복하는 실행 문서다. 기상(MCIP)과 배출량(SMOKE·MEGAN) 입력은 각 폴더 문서에서 만들고, 이 폴더는 그 입력으로 CCTM을 돌리는 단계부터 다룬다.

| 순서 | 문서 | 구분 | 읽는 목적 | 상태 |
|---|---|---|---|---|
| **01 필수(설치)** | [CCTM 구축 가이드](01_CCTM_Installation_Guide.md) | 설치·컴파일 | CCTM `cb6r5_ae7_aq`·`m3dry` 빌드, EPA 벤치마크 실행·참조 비교 | CCTM 완료. ICON·BCON 빌드는 이 문서에 추가 예정 |
| **02 필수(CASE)** | 부산 CMAQ 실행 가이드 (작성 예정) | CASE 실행 | 부산 `TEST_20260901`의 ICON·BCON 생성, CCTM 실행 스크립트(배출 입력·인라인 MEGAN·점오염원 inline), 27 → 09 → 03 → 01KM 실행·검증 | 미작성. 실제로 실행·확인한 명령만 기록 |

## 현재 작업 재개 위치

- **완료(2026-11-25 서버 확인):** CCTM 빌드와 EPA 벤치마크 2일 실행, EPA gcc 참조 결과 비교([01 §7](01_CCTM_Installation_Guide.md)).
- **CCTM 입력 준비 상태:** 배출량 병합(지면) + 점오염원 inline 파일 4개 도메인 × 2일 완료([SMOKE 06](../smoke/06_SMOKE_Busan_Sector_Merge_Guide.md)), 화학 메커니즘 `cb6r5_ae7_aq` 확정([SMOKE 03 §7.3](../smoke/03_SMOKE_Emission_Improvement_Plan.md#busan-mechanism)), 생물성 이중계상 없음(병합 단계까지, [SMOKE 03 §9.3](../smoke/03_SMOKE_Emission_Improvement_Plan.md#busan-inline-megan)), MEGAN 입력 CT3·EFMAP·LDF 완료([MEGAN 01](../megan/01_MEGAN32_Input_Preprocessing_Guide.md)).
- **다음:** ICON·BCON 빌드(01에 추가) → 부산 27KM ICON·BCON 생성과 CCTM 실행(02 작성 시작).
- **설치 파일:** [files/](files/)에 벤치마크 실행 스크립트 패치가 있다.

> 번호는 **읽는 순서**를 의미하며 모델 실행의 Phase 번호와는 별개입니다. `files/`는 설치·실행용 파일이므로 문서 순서에 포함하지 않습니다.
