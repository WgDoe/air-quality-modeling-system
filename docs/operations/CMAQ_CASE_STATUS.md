# CMAQ CCTM / ISAM: 현재 Case 실행 준비 상태

> 기준: 2026-11-16, GitHub 기존 README/SMOKE/MEGAN 문서의 **검증 기록만** 반영. 이 문서는 현재 상태 표이며 검증된 CCTM 실행 가이드가 아니다.

## 준비된 항목
- CMAQ 5.5 시험용 CCTM 빌드 확인 기록.
- WRF/WPS 및 MCIP 4도메인 테스트 완료 기록.
- 국내 CAPSS 2023, 국외 HTAP v3.2 개별 배출처리 완료 기록.
- MEGAN 3.2 CT3·EFMAP·LDF 파일 생성 기록; 수정 후 LDF의 4도메인 CSV/NetCDF 값 일치 및 운영 LDF 파일 동일성 확인(2026-11-16 사용자 제공 서버 출력).

## 아직 수행/검증되지 않은 항목
1. SMOKE 국내·국외 부문 병합과 CCTM 입력 단위/종/시간/공간 정합성.
2. **운영 LDF의 수정본 일치 여부는 확인 완료**. 남은 일은 CCTM inline MEGAN 3.2 및 토양 NO 옵션 실제 연결·실행 검증.
3. MCIP 수직층과 배출량/IC/BC 수직층 정합성, CCTM IC/BC 준비.
4. 공식 CMAQ benchmark 및 실제 부산 CCTM 성공 실행, 로그·출력 QA.
5. CMAQ-ISAM benchmark, 기여지역/배출원 태그 입력 및 실제 실행.

## 이후 검증되면 추가할 내용
- 고정 설치 구성(버전, compiler, 바이너리 경로)과 Case 변경 설정(기간, grid, emission streams, IC/BC, mechanism, MPI layout)을 분리.
- 검증된 실행 스크립트 원문, 실행한 정확한 명령/환경변수, Case별 입력·출력·로그 경로.
- 성공판정 지표 및 오류 해결 이력, 전후 입력파일의 SHA-256/metadata.

관련 문서: [전체 진행상태](../../README.md), [국내 배출량](../smoke/04_SMOKE_Busan_Case_Run_Guide.md), [HTAP](../smoke/05_HTAP_v32_Reproduction_Checklist.md), [MEGAN](../megan/01_MEGAN32_Input_Preprocessing_Guide.md).

**현재 단계에서는 검증 없이 가상의 CCTM 실행 명령을 만들어 사용하지 않는다.**
