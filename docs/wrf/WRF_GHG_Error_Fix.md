# WRF GHG 오류: CASE runtime data 누락

## 확인된 원인

TEST_20260901에서 real.exe 성공 후 wrf.exe의 GHG 관련 오류는 CASE 실행 디렉터리에 WRF runtime data 파일이 없어서 발생했다. 실행파일을 절대경로로 호출해도 프로그램은 현재 CASE/WRF에서 런타임 자료를 찾는다.

현재 구성에서는 LANDUSE.TBL, VEGPARM.TBL, SOILPARM.TBL, GENPARM.TBL, RRTM_DATA, RRTM_DATA_DBL, CAMtr_volume_mixing_ratio를 `/home/woogon/CMAQ_MODEL/WRFV4.5.1/run`에서 CASE/WRF로 선별 심볼릭 링크한다. run 폴더 전체를 링크하지 않는다.

## 해결 및 확인

[사례 실행 가이드 §5](WRF_WPS_Case_Run.md#5-wrf-runtime-data와-realexe)의 링크·파일 존재 점검 후 §6의 `mpirun -np 4` 실행을 따른다. ls -l에 링크가 보여도 실제 대상이 없으면 해결되지 않은 것이므로 test -s로 확인한다. 진행과 종료는 rsl.error.* / rsl.out.*에서 확인한다.

`ghg_input`을 namelist에 추가하는 방법은 이 오류의 해결책이 아니다. 잘못 추가한 항목이 있으면 제거하고 검증된 namelist 설정을 유지한다. 해당 항목의 추가 명령이나 예제는 제공하지 않는다.

## 문서 출처와 범위

이 문서는 2026-10-08 사용자 제공 원인·해결 기록을 설치/실행 가이드와 일치하도록 통합한 기록이다. 사용자가 언급한 업로드 파일 `WRF_GHG_Error_Fix.md` 원문은 현재 연결된 첨부·로컬 sources·GitHub에 없어 직접 대조하지 못했다. 원문을 확인한 것으로 간주하지 않는다.
