# WRF/WPS 사례 실행: BUSAN / TEST_20260901

## 1. 범위와 확인된 상태

2026-10-08 사용자 제공 실제 실행 기록 기준이다. 설치·컴파일은 [설치 가이드](WRF_WPS_Installation_Guide.md), 경로는 [디렉터리 구조](../planning/Directory_Structure.md)를 따른다.

WPS와 real.exe는 성공했고 WRF는 모델 시간이 증가하는 계산 진행까지 확인되었다. `SUCCESS COMPLETE WRF` 및 모의 종료 시각의 출력 확인은 아직 제공되지 않았다. MCIP/CMAQ 실행 완료를 뜻하지 않는다.

## 2. 그대로 유지할 설정과 사례별 변경값

| 구분 | 현재 기준 | 변경 시 확인 |
|---|---|---|
| 모델/병렬 실행 | WRF 4.5.1 dmpar, WPS 4.5 serial, WRF 4코어 | 동일 compiler/MPI/library 환경 |
| 도메인 | d01~d04, max_dom=4 | WPS/WRF 격자·투영·nest 관계 일치 |
| 신규 지형 생성 | MODIS 21 category | geo_em의 MMINLU=MODIFIED_IGBP_MODIS_NOAH, NUM_LAND_CAT=21; WRF num_land_cat=21 |
| 기상 입력 | FNL ds083.2, 1도 GRIB2, 6시간 | 다른 제품을 사용할 때 Vtable·간격·층수 재검증 |
| 입력자료 시간 간격 | interval_seconds=21600 | WPS/WRF 동일; time_step과 다른 값 |
| 입력자료 연직층 | num_metgrid_levels=34 | met_em header 기준; WRF e_vert와 다른 값 |
| 물리·FDDA | 성공한 CASE namelist.input 유지; d01~d04 wrffdda 생성 구성 | 옵션·계수·시간창을 일괄 변경하지 않음 |
| 모의 기간/출력 주기 | 사례별 변경 | start/end, run_*, history_interval, FDDA 시간창 및 자료 범위 정합 |
| 사례 폴더 | TEST_20260901 | 폴더명에서 실제 모의 시작·종료를 추정하지 않음 |

현재 namelist 원문은 이 저장소에 없다. 격자 크기, nest ratio, 물리옵션 번호, FDDA 계수는 확인되지 않은 값을 만들어 적지 않는다. 동일 사례를 완전히 재현하려면 실제 성공한 `namelist.wps`, `namelist.input`을 보존해야 한다. 아래 조각은 해당 section에 반영할 항목이며 완전한 namelist 대체 파일이 아니다.

날짜는 모두 UTC 모델 시각이다. 예를 들어 2026-08-31 00 UTC ~ 2026-09-02 00 UTC는 설명용 기간이며 확정된 실제 기간이 아니다. 네 도메인의 start/end를 일치시키고 run_*와 FDDA 종료 시간, 입력자료 마지막 시각을 함께 조정한다. domain/physics/FDDA의 현재 공간·물리 설정과 날짜 변경을 구분한다.

## 3. 새 시스템에서 자료·CASE 준비

먼저 설치 가이드의 환경 등록을 적용하고 확인한다.

```bash
source ~/.bashrc
source /etc/profile.d/modules.sh
module load mpi/openmpi-x86_64
which mpirun
mpirun --version
ldd /home/woogon/CMAQ_MODEL/WRFV4.5.1/main/wrf.exe
ldd /home/woogon/CMAQ_MODEL/WPS-4.5/geogrid/src/geogrid.exe
ldd /home/woogon/CMAQ_MODEL/WPS-4.5/ungrib/src/ungrib.exe
ldd /home/woogon/CMAQ_MODEL/WPS-4.5/metgrid/src/metgrid.exe
mkdir -p /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/{WPS,WRF,MCIP,EMIS,CMAQ,POST,LOG}
mkdir -p /home/woogon/CMAQ_MODEL/DATA/WPS_GEOG
mkdir -p /home/woogon/CMAQ_MODEL/DATA/MET/FNL
```

ldd에 `not found`가 있으면 먼저 공통 라이브러리 환경을 복구한다.

정적 자료는 [공식 WPS 지형자료 페이지](https://www2.mmm.ucar.edu/wrf/users/download/get_sources_wps_geog.html)에서 현재 GEOGRID.TBL이 요구하는 지형·토양·식생·MODIS 자료를 준비하고 WPS_GEOG에 압축 해제한다. 기존 서버에서는 준비된 자료를 재사용한다. 신규 geogrid는 MODIS 21 category를 표준으로 한다. `geog_data_res='default',...`는 로컬 GEOGRID.TBL의 LANDUSEF 항목이 21-category MODIS 자료를 선택하는지 확인한 뒤 사용한다. USGS 기반 기존 geo_em에 WRF의 num_land_cat만 21로 바꾸지 않는다.

FNL은 [NCAR ds083.2 / d083002](https://gdex.ucar.edu/datasets/d083002/)의 1도 GRIB2 분석자료를 사용한다. 00/06/12/18 UTC 자료를 모의 시작부터 종료까지 빠짐없이 준비한다. 월 경계를 넘으면 모든 해당 월을 준비한다. 예시 파일명은 `fnl_20260831_00_00.grib2`이다.

서버의 다운로드 스크립트는 `/home/woogon/CMAQ_MODEL/SCRIPTS/download_fnl.sh`이다. 원문과 인자 규약은 아직 저장소에 없으므로 실행 인자를 추정하지 않는다.

```bash
sed -n '1,200p' /home/woogon/CMAQ_MODEL/SCRIPTS/download_fnl.sh
ls -lh /home/woogon/CMAQ_MODEL/DATA/MET/FNL/2026/08/fnl_*.grib2
ls -lh /home/woogon/CMAQ_MODEL/DATA/MET/FNL/2026/09/fnl_*.grib2
```

위 월은 예시이다. 자료 크기와 시각 목록을 확인하고, 다운로드된 파일이 로그인 HTML이나 빈 파일이 아닌 GRIB2인지 점검한다. 계정 인증 정보는 문서나 Git에 넣지 않는다.

## 4. WPS: geogrid → ungrib → metgrid

성공한 CASE의 namelist.wps를 CASE/WPS에 준비하고 기간을 변경한다. &share에 `max_dom=4`, `interval_seconds=21600`, &geogrid에 `geog_data_path='/home/woogon/CMAQ_MODEL/DATA/WPS_GEOG'`, &ungrib에 `out_format='WPS'`, `prefix='FILE'`, &metgrid에 `fg_name='FILE'`을 설정한다. out_opt=2는 netCDF 출력 기준이다. 도메인의 parent_id, parent_grid_ratio, i/j_parent_start, e_we/e_sn, dx/dy 및 투영은 검증된 값을 유지한다.

현재 작업 디렉터리가 입력·출력 위치를 결정한다. 실행파일은 설치 폴더의 절대경로로 호출한다.

```bash
cd /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/WPS
mkdir -p geogrid metgrid
ln -sfn /home/woogon/CMAQ_MODEL/WPS-4.5/geogrid/GEOGRID.TBL.ARW geogrid/GEOGRID.TBL
ln -sfn /home/woogon/CMAQ_MODEL/WPS-4.5/metgrid/METGRID.TBL.ARW metgrid/METGRID.TBL
ln -sfn /home/woogon/CMAQ_MODEL/WPS-4.5/ungrib/Variable_Tables/Vtable.GFS Vtable
ls -l namelist.wps geogrid/GEOGRID.TBL metgrid/METGRID.TBL Vtable
/home/woogon/CMAQ_MODEL/WPS-4.5/geogrid.exe
tail -30 geogrid.log
ls -lh geo_em.d0*.nc
ncdump -h geo_em.d01.nc | grep -E 'MMINLU|NUM_LAND_CAT'
```

geogrid 성공 메시지와 d01~d04 geo_em, MODIS 21 category를 확인한다. d02~d04 header도 동일하게 확인한다. 사용 자료나 도메인을 바꾸면 geogrid부터 재생성한다.

다음 명령의 날짜 패턴은 위 설명용 기간에 맞춘 예시이다. 실제 기간의 파일만 링크하고 다른 사례 GRIBFILE 링크가 섞이지 않은 새 실행 폴더를 사용한다.

```bash
/home/woogon/CMAQ_MODEL/WPS-4.5/link_grib.csh /home/woogon/CMAQ_MODEL/DATA/MET/FNL/2026/08/fnl_20260831_*.grib2 /home/woogon/CMAQ_MODEL/DATA/MET/FNL/2026/09/fnl_2026090[12]_*.grib2
ls -l GRIBFILE.*
/home/woogon/CMAQ_MODEL/WPS-4.5/ungrib.exe
tail -30 ungrib.log
ls -lh FILE:*
/home/woogon/CMAQ_MODEL/WPS-4.5/metgrid.exe
tail -30 metgrid.log
ls -lh met_em.d0*.nc
```

header는 아래처럼 실제 생성된 한 파일을 명시해 확인한다.

```bash
# 날짜는 예시이며 실제 생성된 파일명으로 변경한다.
ncdump -h met_em.d01.2026-08-31_00:00:00.nc | grep -E 'num_metgrid_levels|num_st_layers'
```

ungrib/metgrid 각각 성공 메시지를 확인한 뒤 다음 단계로 진행한다. FILE:*가 6시간 간격으로 시작~종료 시각을 포함하는지, met_em이 네 도메인과 전체 입력 시각에 대해 생성됐는지 확인한다. 현재 met_em의 num_metgrid_levels는 34이며 namelist.input도 34로 맞춘다. 토양층수 num_metgrid_soil_levels는 실제 num_st_layers와 맞춘다. 34를 WRF 모델층 e_vert에 복사하지 않는다.

## 5. WRF runtime data와 real.exe

CASE/WRF에 검증된 namelist.input을 준비한다. &time_control의 start/end와 run_*는 WPS 기간과 일치시키고 `interval_seconds=21600`을 사용한다. &domains의 `max_dom=4`, `num_metgrid_levels=34`, &physics의 `num_land_cat=21` 및 현재 물리 설정을 확인한다. FDDA 원문 설정을 유지하고 시간창은 변경한 모의 기간과 맞춘다.

런타임 자료는 real.exe와 wrf.exe 실행 전에 준비한다. run 전체를 링크하지 않고 현재 설정에 필요한 일곱 파일만 연결한다.

```bash
cd /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/WRF
ln -s /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/WPS/met_em.d0*.nc .
WRFRUN=/home/woogon/CMAQ_MODEL/WRFV4.5.1/run
for runtime_file in LANDUSE.TBL VEGPARM.TBL SOILPARM.TBL GENPARM.TBL RRTM_DATA RRTM_DATA_DBL CAMtr_volume_mixing_ratio; do
    test -s "$WRFRUN/$runtime_file" || { echo "Missing runtime data: $runtime_file"; break; }
    ln -sfn "$WRFRUN/$runtime_file" .
done
ls -l LANDUSE.TBL VEGPARM.TBL SOILPARM.TBL GENPARM.TBL RRTM_DATA RRTM_DATA_DBL CAMtr_volume_mixing_ratio
for runtime_file in LANDUSE.TBL VEGPARM.TBL SOILPARM.TBL GENPARM.TBL RRTM_DATA RRTM_DATA_DBL CAMtr_volume_mixing_ratio; do
    test -s "$runtime_file" || echo "STOP: missing/broken $runtime_file"
done
```

STOP 또는 누락 메시지가 있으면 실행을 진행하지 않는다. 물리옵션을 바꾸었을 때는 요구하는 추가 runtime data만 검토해 연결한다. GHG 오류의 실제 원인은 CASE 실행 폴더의 runtime data 누락이며 [GHG 오류 기록](WRF_GHG_Error_Fix.md)을 참고한다.

```bash
source /etc/profile.d/modules.sh
module load mpi/openmpi-x86_64
mpirun -np 4 /home/woogon/CMAQ_MODEL/WRFV4.5.1/main/real.exe
grep "SUCCESS COMPLETE REAL" rsl.error.0000
ls -lh wrfinput_d01 wrfinput_d02 wrfinput_d03 wrfinput_d04 wrfbdy_d01 wrffdda_d01 wrffdda_d02 wrffdda_d03 wrffdda_d04
```

SUCCESS COMPLETE REAL과 모든 산출물을 확인한 뒤 진행한다. 현재 FDDA 사용 구성에서는 wrffdda_d01~d04가 필요하다. FDDA를 사용하지 않는 다른 사례에 이 산출물 요구를 그대로 적용하지 않는다.

## 6. WRF dmpar 4코어 실행과 확인

real.exe 로그를 보존한 뒤 wrf.exe를 시작한다. 기존 계산이 실행 중이면 아래 명령으로 재실행하지 않는다. 실패 실행의 wrfout/rsl은 별도 보관하고, 새 사례 폴더를 사용하는 것을 우선한다. 정상 출력 파일을 일괄 삭제하는 절차는 포함하지 않는다.

```bash
cd /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/WRF
real_log_archive=../LOG/real_$(date -u +%Y%m%dT%H%M%SZ)
mkdir -p "$real_log_archive"
cp -p rsl.error.* rsl.out.* "$real_log_archive"/
mpirun -np 4 /home/woogon/CMAQ_MODEL/WRFV4.5.1/main/wrf.exe
```

wrf.log를 별도 생성하지 않는다. 로그는 CASE/WRF의 rsl.error.* / rsl.out.*를 사용한다. 실행 중 두 번째 터미널에서 확인한다.

```bash
tail -f /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/WRF/rsl.error.0000
```

tail 감시를 끝내는 Ctrl+C는 해당 감시 터미널에서만 누른다. 실제 모델 실행 터미널에서 누르면 계산을 중단할 수 있다. 커서 깜빡임이나 로그 숫자 증가만으로 정상 계산을 단정하지 않고 모델 시각을 확인한다.

```bash
grep "Timing for main" /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/WRF/rsl.error.0000 | tail
```

모델 시간이 증가하면 계산 진행 중이다. 종료 후 확인:

```bash
cd /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/WRF
grep "SUCCESS COMPLETE WRF" rsl.error.0000
tail -30 rsl.error.0000
grep -niE 'FATAL|segmentation|MPI_ABORT' rsl.error.* rsl.out.*
ls -lh wrfout_d0*
# 실제 생성된 파일 하나를 지정해 Times를 확인한다(아래 날짜는 예시).
ncdump -v Times wrfout_d01_2026-08-31_00:00:00 | tail -30
```

성공 메시지, d01~d04 출력 존재, 각 도메인의 마지막 Times가 요청한 종료 시각까지 도달했는지를 함께 확인한다. 출력이 여러 파일로 나뉘면 마지막 파일도 확인한다. 실행 시작 직후 wrfout이 존재하는 것만으로 완료 처리하지 않는다. 검증 완료 후 MCIP 입력으로 전달한다.

## 7. 재현에 필요한 보존 자료

CASE의 namelist.wps/namelist.input, FNL 파일 목록·기간, geo_em/met_em header, runtime 링크 목록, compiler/MPI/library 버전, rsl 로그와 성공 메시지를 보존한다. 현재 다운로드 스크립트와 실제 namelist 원문은 미수집이므로, 새 시스템에서 동일 과학 설정을 완전히 재현하는 데에는 이 원문 확보가 필요하다.

절차와 Vtable의 공식 근거: [WRF Users Guide — WPS](https://www2.mmm.ucar.edu/wrf/users/wrf_users_guide/build/html/wps.html).
