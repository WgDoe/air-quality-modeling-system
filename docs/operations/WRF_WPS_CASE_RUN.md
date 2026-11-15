# WPS/WRF Case 반복 실행 가이드 (설치 이후)

> **검증된 원문 명령을 재사용하는 실행 목차**. 설치·컴파일은 [설치 목차](INSTALLATION_INDEX.md), 실제 코드 블록은 [WRF/WPS 구축 가이드 §14](../wrf/WRF_WPS_Installation_Guide.md#14-자료-준비-및-사례-실행-busan--test_20260901)에서 확인한다.

## 검증 기록과 전제
- WRF 4.5.1 / WPS 4.5. 기존 `TEST_20260901_REPEAT` 4도메인 WPS → real.exe → WRF dmpar 4코어 정상 종료 기록.
- 예전 테스트의 성공은 새 기간·영역에 대한 성공을 보증하지 않는다.
- 새 Case를 위한 공통 컴파일 재실행은 필요하지 않지만, WRF physics/runtime 설정 변경 시 추가 파일과 빌드 호환성 확인이 필요하다.

## 빠른 실행 순서와 원문 명령 위치
| 단계 | 실제 Case마다 확인·수정할 값 | 실행 명령/스크립트가 기록된 원문 |
|---|---|---|
| A. Case 생성/보존 | `CASES/BUSAN/<CASE_ID>`, 이전 namelist·로그·산출물 | [§14.3.1–14.3.2](../wrf/WRF_WPS_Installation_Guide.md) |
| B. 기상자료 | FNL 시작·종료 UTC, 파일 구간, 다운로드·완전성 | [§14.3.3–14.3.4: `download_fnl.sh`](../wrf/WRF_WPS_Installation_Guide.md#fnl-download) |
| C. WPS | `namelist.wps`: 기간·domain·해상도·부모 격자·정적자료 경로 | [§14.4 geogrid → ungrib → metgrid](../wrf/WRF_WPS_Installation_Guide.md) |
| D. WRF real | `namelist.input`: 기간, 기상옵션, 수직층·물리 | [§14.5 real.exe](../wrf/WRF_WPS_Installation_Guide.md) |
| E. WRF 실행 | MPI 프로세스, runtime 자료, 로그 | [§14.6 wrf.exe](../wrf/WRF_WPS_Installation_Guide.md) |
| F. 검증 | `rsl.error.0000`, `wrfout_d01~d04_*`, 끝 시각 | [§14.6](../wrf/WRF_WPS_Installation_Guide.md) |

**실행 원칙:** 각 명령은 기존 원문의 절대경로·환경변수·심볼릭 링크·옵션을 확인해 새 Case에 맞게 실행한다. 새 Case에서 원문 경로를 그대로 복사 실행하지 않는다.

## 최소 QA
- 요청한 6시간 FNL 구간과 WPS의 모든 `met_em` 시각이 일치하는가?
- WPS/WRF nested grid, 도메인 개수와 기간이 일치하는가?
- WRF `SUCCESS COMPLETE WRF`와 각 d01~d04 파일의 마지막 유효 시각을 확인했는가?
- 물리옵션을 바꾼 경우 필요한 `WRFV4.5.1/run` runtime 자료를 다시 확인했는가?

## 재실행 범위
기상자료/기간만 바뀌고 grid는 같으면 geogrid 산출물 재사용 가능 여부를 먼저 검사한다. domain이나 정적 지형이 바뀌면 geogrid부터 재생성한다. WRF physics만 바꾸는 경우 WPS 입력 재사용 가능성을 검토하되 WRF → MCIP 및 기상 의존 후속 처리 결과를 다시 확인한다.
