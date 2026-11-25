# 설치·컴파일 전용 목차 — 새 시스템 재구축 시

> 대상: 신규 워크스테이션 설치, 버전 업그레이드, 바이너리 재빌드, 소스 패치. **새 Case를 돌릴 때마다 아래 단계를 반복하지 않는다.**

| 순서 | 설치·설정 원문 | 범위 |
|---|---|---|
| 1 | [Rocky Linux](../linux/Rocky_Linux_Installation_Guide.md) | OS, 계정, 네트워크, 기본 도구 |
| 2 | [GNU Compiler/OpenMPI](../compiler/GNU_Compiler_OpenMPI_Installation_Guide.md) | compiler, MPI |
| 3 | [공통 라이브러리](../libraries/Common_Libraries_Installation_Guide.md) | zlib/HDF5/netCDF/I/O API |
| 4 | [WRF/WPS §5–13](../wrf/WRF_WPS_Installation_Guide.md) | WRF 4.5.1 / WPS 4.5 설치·컴파일·검증 |
| 5 | [MCIP §5–9](../mcip/MCIP_Installation_Guide.md) | CMAQ 프로젝트, config_cmaq.csh, MCIP 컴파일 |
| 6 | [SMOKE 5.3 설치](../smoke/01_SMOKE_Installation_Guide.md) | 공식 예제·빌드 검증 |
| 7 | [SMOKE Grdmat 최초 패치 §7.1](../smoke/04_SMOKE_Busan_Case_Run_Guide.md#busan-grdmat-patch) | 국내 입력 실행 전에 적용한 genagmat.f 수정 |
| 8 | [HTAP용 smkinven 패치 §6.1](../smoke/05_HTAP_v32_Reproduction_Checklist.md#htap-install-once) | **§6.1만** 최초 설치/소스 교체 시 패치·재컴파일; [§6.2](../smoke/05_HTAP_v32_Reproduction_Checklist.md#htap-case-install)는 새 CASE마다 필수 |
| 9 | [MEGAN §5](../megan/01_MEGAN32_Input_Preprocessing_Guide.md) | 전처리 도구 설치·컴파일과 공용 자료 준비 |
| 10 | [CMAQ 5.5 CCTM 빌드·벤치마크](../cmaq/01_CCTM_Installation_Guide.md) | `cb6r5_ae7_aq` + `m3dry` 빌드, EPA 벤치마크 2일 실행·참조 비교 완료. 메커니즘·소스·라이브러리가 바뀌면 재빌드. ICON·BCON 빌드는 이 문서 §8에 미빌드로 기록 |

**설치·컴파일이 아닌 것(CASE마다):** SMOKE 부문 병합의 날짜 패치(`smk_sectormerge_emf.csh`)와 병합 설정 파일은 CASE의 `smoke5.2` 사본에 들어가므로 [04 §7 설치 스크립트](../smoke/04_SMOKE_Busan_Case_Run_Guide.md)가 CASE마다 자동 적용한다(재컴파일 없음, [06](../smoke/06_SMOKE_Busan_Sector_Merge_Guide.md)). 국내 `SOAALK` tracer 종분배 추가(2026-11-25)도 입력 파일 변경이라 재컴파일이 필요 없다.

주의: SMOKE 소스 수정 사항은 [procar2pt 기록](../smoke/90_SMOKE_procar2pt_Fix.md), [smkinven 기록](../smoke/91_SMOKE_smkinven_Fix.md)도 참조한다. **예전 sizgmat.f 패치는 폐기**되었다는 원문 기록을 따른다.

신규 설치에서 처음부터 전체 재현에 성공한 것으로 간주하지 않는다. 각 모델의 빌드 정보·버전·테스트 로그를 별도로 남긴다.

Case 수행은 [운영 목차](README.md)에서 시작한다.
