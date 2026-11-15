# WPS/WRF Case 반복 실행 가이드 (설치 이후)

> **검증된 원문 명령을 재사용하는 실행 목차**. 설치·컴파일은 [설치 목차](INSTALLATION_INDEX.md), 실제 코드 블록은 [WRF/WPS 구축 가이드 §14](../wrf/WRF_WPS_Installation_Guide.md#14-자료-준비-및-사례-실행-busan--test_20260901)에서 확인한다.

## 검증 기록과 전제
- WRF 4.5.1 / WPS 4.5. 기존 `TEST_20260901_REPEAT` 4도메인 WPS → real.exe → WRF dmpar 4코어 정상 종료 기록.
- 예전 테스트의 성공은 새 기간·영역에 대한 성공을 보증하지 않는다.
- 새 Case를 위한 공통 컴파일 재실행은 필요하지 않지만, WRF physics/runtime 설정 변경 시 추가 파일과 빌드 호환성 확인이 필요하다.

## 같은 도메인에서 기간만 바꾸는 CASE: 먼저 확인할 값

| 변경값 | 변경 위치 | 원문 |
|---|---|---|
| CASE 폴더명 `TEST_20260901_REPEAT` | §14.3~14.6 명령의 CASE 경로 | [§14.0, §14.3](../wrf/WRF_WPS_Installation_Guide.md) |
| WPS 출력 경로 두 곳 | `opt_output_from_geogrid_path`, `opt_output_from_metgrid_path` | §14.3.2 |
| WPS 및 WRF 기간 | `&share`의 `start_date/end_date`, `&time_control`의 `run_*`·`start_*`·`end_*`(4도메인) | §14.3.3 |
| FDDA 시간창 | `gfdda_end_h`가 새 기간을 포함하는지 | §14.3.3 |
| FNL 다운로드 기간 | `download_fnl.sh`의 시작·종료 인자 및 확인 블록 날짜 | §14.3.4 |
| FNL 링크 날짜 | `link_grib.csh` 뒤 파일 목록 | §14.4.2 |

도메인이 동일하다면 격자 정의·정적 지형 설정을 무조건 바꾸지 않는다. **격자/해상도/부모 격자/정적자료가 달라질 때만** geogrid 설정부터 재검토한다. 원문 명령의 절대경로에 과거 CASE명이 남아 있는지도 실행 전 확인한다.

## 빠른 실행 순서와 원문 명령 위치
| 단계 | 실제 Case마다 확인·수정할 값 | 실행 명령/스크립트가 기록된 원문 |
|---|---|---|
| A. Case 생성/보존 | `CASES/BUSAN/<CASE_ID>`, 이전 namelist·로그·산출물 | [§14.3.1–14.3.2](../wrf/WRF_WPS_Installation_Guide.md) |
| B. 기간 편집 | WPS/WRF namelist의 시작·종료시간, FDDA | [§14.3.3](../wrf/WRF_WPS_Installation_Guide.md) |
| C. 기상자료 | FNL 시작·종료 UTC, 다운로드·완전성 | [§14.3.4: `download_fnl.sh`](../wrf/WRF_WPS_Installation_Guide.md#fnl-download) |
| D. WPS | `namelist.wps`: 기간·domain·해상도·부모 격자·정적자료 경로 | [§14.4 geogrid → ungrib → metgrid](../wrf/WRF_WPS_Installation_Guide.md) |
| E. WRF real | `namelist.input`: 기간, 기상옵션, 수직층·물리 | [§14.5 real.exe](../wrf/WRF_WPS_Installation_Guide.md) |
| F. WRF 실행 | MPI 프로세스, runtime 자료, 로그 | [§14.6 wrf.exe](../wrf/WRF_WPS_Installation_Guide.md) |
| G. 검증 | `rsl.error.0000`, `wrfout_d01~d04_*`, 끝 시각 | [§14.6](../wrf/WRF_WPS_Installation_Guide.md) |

**실행 원칙:** 각 명령은 기존 원문의 절대경로·환경변수·심볼릭 링크·옵션을 확인해 새 Case에 맞게 실행한다. 새 Case에서 원문 경로를 그대로 복사 실행하지 않는다.

## 최소 QA
- 요청한 6시간 FNL 구간과 WPS의 모든 `met_em` 시각이 일치하는가?
- WPS/WRF nested grid, 도메인 개수와 기간이 일치하는가?
- WRF `SUCCESS COMPLETE WRF`와 각 d01~d04 파일의 마지막 유효 시각을 확인했는가?
- 물리옵션을 바꾼 경우 필요한 `WRFV4.5.1/run` runtime 자료를 다시 확인했는가?

## 재실행 범위
기상자료/기간만 바뀌고 grid는 같으면 geogrid 산출물 재사용 가능 여부를 먼저 검사한다. domain이나 정적 지형이 바뀌면 geogrid부터 재생성한다. WRF physics만 바꾸는 경우 WPS 입력 재사용 가능성을 검토하되 WRF → MCIP 및 기상 의존 후속 처리 결과를 다시 확인한다.
