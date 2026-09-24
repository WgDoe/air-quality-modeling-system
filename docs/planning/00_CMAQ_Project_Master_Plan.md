# CMAQ 통합 대기질 모델링 시스템 구축 기본계획 및 요구사항

작성일: 2026-09-23  
문서 성격: 프로젝트 기본계획 / 요구사항 정의 / 공식 참고자료 인덱스  
적용 대상: Linux Desktop 기반 CMAQ 독립 운영환경 구축

---

# 1. 프로젝트 개요

## 1.1 프로젝트명

**Linux 기반 CMAQ 통합 대기질 모델링 시스템 구축**

## 1.2 구축 목적

보유 중인 Linux 데스크톱을 기반으로 WRF, WPS, MCIP, SMOKE, CMAQ 및 CMAQ-ISAM 등을 직접 설치·컴파일하고,  
국내외 기상·배출량 자료를 가공하여 사용자가 원하는 기간·영역·배출 시나리오별로 반복적으로 대기질 모델링을 수행할 수 있는 독립 운영체계를 구축한다.

최종 시스템은 단순한 CMAQ 실행 환경이 아니라 다음 기능을 포함하는 것을 목표로 한다.

- Linux 기반 모델링 서버/워크스테이션 구축
- Fortran/C/C++ compiler 및 MPI 병렬환경 구축
- netCDF, HDF5, I/O API 등 공통 라이브러리 구축
- WRF/WPS 기반 기상모델링
- MCIP 기반 CMAQ용 기상자료 생산
- SMOKE 기반 배출량 전처리
- 국내 배출량(CAPSS 등) 처리
- 국외 인위배출량(REAS 등) 처리
- 식생배출(MEGAN 또는 BEIS 계열) 처리
- 필요 시 자연배출(해염, 비산먼지, 산불, lightning NOx 등) 처리
- CMAQ CCTM 실행
- CMAQ-ISAM 기반 지역별·배출원별 기여도 분석
- 필요 시 DDM-3D 기반 민감도 분석
- 관측자료와 모델 결과 비교 및 성능평가
- R/Python/VERDI 등을 활용한 후처리
- 사례별(case-based) 자동 또는 반자동 실행체계 구축
- 모든 설치환경·버전·설정·오류·해결과정 문서화

---

# 2. 최종 구축 목표

최종적으로 다음과 같은 흐름을 사용자가 직접 운영할 수 있도록 한다.

```text
[기상 입력자료]
FNL / GFS / ERA5
        │
        ▼
       WPS
        │
        ▼
       WRF
        │
        ▼
      wrfout
        │
        ▼
       MCIP
        │
        ├───────────────────────────────┐
        │                               │
        ▼                               ▼
 CMAQ용 기상입력                 배출량 처리용 기상정보


[국내 인위배출]
CAPSS / 자체 인벤토리
        │
        ▼
 전처리 / SMOKE
        │
        ▼
 CMAQ-ready emissions


[국외 인위배출]
REAS / 기타 Asian inventory
        │
        ▼
 단위변환 / 좌표변환 / 재격자화
        │
        ▼
 시간할당 / 화학종 분배
        │
        ▼
 CMAQ-ready emissions


[자연배출]
MEGAN / BEIS
Sea Salt
Windblown Dust
Fire
Lightning NOx
        │
        ▼
 CMAQ-ready 또는 CMAQ inline emissions


        국내 + 국외 + 자연배출
                 │
                 ▼
              CMAQ CCTM
                 │
         ┌───────┴────────┐
         ▼                ▼
       ISAM             DDM-3D
         │
         ▼
 지역별 / 배출원별 / 부문별 기여도

                 │
                 ▼
       R / Python / VERDI
                 │
                 ▼
       후처리 / 통계 / 검증 / 시각화
```

---

# 3. 구축 기본 원칙

## 3.1 공식 문서 우선

설치와 설정은 블로그나 개인 자료보다 다음 출처를 우선한다.

1. USEPA CMAQ 공식 문서
2. CMAQ 공식 GitHub
3. NCAR/MMM WRF 공식 문서
4. CMAS Center
5. SMOKE 공식 매뉴얼
6. Unidata netCDF 공식 문서
7. OpenMPI 공식 문서
8. Intel/GNU compiler 공식 문서

비공식 자료는 공식 문서로 해결되지 않는 호환성 문제나 사례 확인용으로만 사용한다.

## 3.2 재현성 확보

모든 설치 및 실행 과정에서 다음을 기록한다.

- OS 버전
- kernel 버전
- compiler 버전
- MPI 버전
- netCDF-C 버전
- netCDF-Fortran 버전
- HDF5 버전
- I/O API 버전
- WRF/WPS 버전
- MCIP 버전
- SMOKE 버전
- CMAQ 버전
- 사용 화학기작
- domain 정보
- 배출량 자료 및 버전
- 실행 스크립트
- 환경변수
- compile option
- 오류 메시지와 해결방법

## 3.3 Benchmark 우선

실제 국내·동아시아 사례를 적용하기 전에 공식 benchmark 또는 tutorial case를 반드시 수행한다.

권장 순서:

```text
Library test
→ WRF test
→ WPS test
→ CMAQ benchmark
→ MCIP test
→ SMOKE example
→ ISAM benchmark
→ 실제 동아시아 domain
```

## 3.4 Compiler 계열 통일

다음 라이브러리와 모델은 동일한 compiler family를 사용하는 것을 원칙으로 한다.

- MPI
- netCDF-C
- netCDF-Fortran
- HDF5
- I/O API
- WRF
- CMAQ

초기 구축은 **GNU gcc/g++/gfortran + OpenMPI**를 기준선으로 한다.

Intel oneAPI(ifx)는 안정화 이후 성능 비교 또는 기존 시스템 호환 목적일 때 검토한다.

---

# 4. 하드웨어 및 운영체제 요구사항

## 4.1 대상 시스템

기본 대상:

- x86_64 Linux desktop/workstation
- 다중 CPU core
- 충분한 RAM
- 대용량 SSD 또는 NVMe 저장장치
- 장기자료 보관용 추가 HDD/NAS 선택 가능

## 4.2 권장 디스크 구조 예시

```text
/MODELS
    /src
    /libs
    /WRF
    /WPS
    /CMAQ
    /SMOKE

/DATA
    /MET
    /WRF
    /MCIP
    /EMIS
        /CAPSS
        /REAS
        /MEGAN
        /BIOGENIC
        /FIRE
    /CMAQ

/CASES
    /CASE_YYYYMM_NAME

/SCRIPTS

/LOGS

/POST
```

운영 과정에서 모델 프로그램과 case input/output을 분리한다.

---

# 5. Linux 기본 환경

## 5.1 권장 Linux

1차 후보:

- Ubuntu 24.04 LTS
- Rocky Linux 9 계열

선정 시 기존 운영 시스템의 OS 및 compiler compatibility를 우선 확인한다.

## 5.2 기본 개발도구

필수 또는 권장 패키지:

- gcc
- g++
- gfortran
- make
- cmake
- m4
- perl
- bash
- csh / tcsh
- git
- wget
- curl
- awk
- sed
- tar
- gzip
- bzip2
- flex
- bison
- environment-modules 또는 Lmod

---

# 6. Compiler 및 병렬환경

## 6.1 GNU

초기 기준:

- gcc
- g++
- gfortran

장점:

- 무료
- WRF/CMAQ 공식 문서 지원
- 사용 사례가 많음
- 개인 workstation 구축에 적합

## 6.2 Intel oneAPI

필요 시 별도 설치 검토.

주의:

- 과거 ifort 기반 시스템과 최신 ifx 시스템의 옵션 차이를 확인
- 기존 CMAQ/SMOKE/WRF 운영 스크립트가 Intel compiler에 의존하는지 확인

## 6.3 MPI

기본:

- OpenMPI

필수 확인:

```bash
which mpicc
which mpif90
which mpirun
mpirun --version
```

WRF dmpar 및 CMAQ 병렬 실행에 사용한다.

---

# 7. 공통 라이브러리

## 7.1 기본 구성

권장 설치 순서:

```text
zlib
→ HDF5
→ netCDF-C
→ netCDF-Fortran
→ I/O API
```

필요에 따라:

- libpng
- JasPer
- curl
- compression library

를 포함한다.

## 7.2 netCDF

WRF와 CMAQ에서 공통으로 사용하는 핵심 라이브러리.

필수:

- netCDF-C
- netCDF-Fortran

확인 명령:

```bash
nc-config --all
nf-config --all
```

## 7.3 I/O API

CMAQ 및 SMOKE 모델링 체계의 핵심 입출력 라이브러리.

주요 역할:

- Models-3 파일 입출력
- 날짜/시간 처리
- grid descriptor
- 자료 변환
- QA utility

---

# 8. WRF/WPS 구축 요구사항

## 8.1 목적

기상 입력자료를 사용하여 CMAQ domain에 대응하는 3차원 기상장을 생산한다.

## 8.2 입력자료 후보

- NCEP FNL
- GFS
- ERA5
- 기존 운영시스템 자료

최종 선택은 기존 시스템 설정과 연구 목적을 비교하여 결정한다.

## 8.3 WPS 처리

```text
geogrid.exe
→ ungrib.exe
→ metgrid.exe
```

## 8.4 WRF 처리

```text
real.exe
→ wrf.exe
```

결과:

```text
wrfout_d01_*
wrfout_d02_*
...
```

## 8.5 확인 항목

- projection
- domain nesting
- horizontal resolution
- vertical layers
- physics options
- PBL scheme
- land surface model
- microphysics
- radiation
- cumulus scheme
- SST 처리
- soil initialization
- nudging 여부

기존 운영 시스템 namelist를 확보하면 우선 비교분석한다.

---

# 9. MCIP 구축 요구사항

## 9.1 목적

WRF 결과를 CMAQ 및 배출처리에 사용할 수 있는 기상 입력파일로 변환한다.

흐름:

```text
wrfout
→ MCIP
→ METCRO2D
→ METCRO3D
→ GRIDCRO2D
→ GRIDDOT2D
→ 기타 CMAQ 입력
```

## 9.2 확인 항목

- WRF와 CMAQ horizontal grid 일치
- vertical layer collapsing
- land-use mapping
- time zone
- 시작/종료시간
- MCIP 버전
- CMAQ 버전 compatibility

---

# 10. SMOKE 구축 요구사항

## 10.1 목적

배출량 인벤토리를 CMAQ용 공간·시간·화학종 해상도로 변환한다.

기본 처리:

```text
Emission Inventory
→ Spatial Allocation
→ Temporal Allocation
→ Chemical Speciation
→ Elevated Point Source Processing
→ Merge
→ CMAQ-ready Emissions
```

## 10.2 초기 구축

1. SMOKE 공식 example case 성공
2. 기존 국내 배출량 처리방식 분석
3. 국내 CAPSS 처리
4. REAS 처리
5. 자연배출 처리
6. 최종 merge 및 QA

---

# 11. 국내 인위배출량 처리 요구사항

대상:

- CAPSS
- 자체 구축 인벤토리
- 필요 시 지자체 상세 배출자료

처리 항목:

- 점오염원
- 면오염원
- 이동오염원
- 도로이동오염원
- 비도로이동오염원
- 산업
- 발전
- 농업
- 선박
- 항공 등

검토사항:

- 기준연도
- 좌표계
- SCC 또는 source category 체계
- 시간분배 profile
- 공간 surrogate
- chemical speciation
- 배출량 단위
- 수직분배
- plume rise

---

# 12. 국외 인위배출량 처리 요구사항

## 12.1 대상

주요 후보:

- REAS
- 기타 동아시아 배출 inventory
- 필요 시 중국/일본/국제 선박 배출 inventory

## 12.2 REAS 처리 시 요구사항

확인 항목:

- 버전
- base year
- spatial resolution
- temporal resolution
- species
- units
- projection
- longitude/latitude grid
- vertical information

처리 절차 예:

```text
REAS 원자료
→ 변수/단위 확인
→ domain subset
→ 좌표 및 grid 변환
→ CMAQ grid 재격자화
→ temporal allocation
→ chemical speciation
→ CMAQ mechanism species mapping
→ I/O API 또는 CMAQ-ready netCDF 변환
→ 국내 배출과 merge
```

## 12.3 중복 처리 검토

특히 다음 영역의 중복 여부를 반드시 확인한다.

- 대한민국 영역
- 선박
- 항공
- 국경지역
- point source
- biomass burning

---

# 13. 자연배출량 처리 요구사항

## 13.1 식생배출

후보:

- MEGAN
- BEIS

최종 시스템에서는 기존 운영방식을 먼저 확인한다.

확인 항목:

- emission factor
- plant functional type
- land cover
- LAI
- light dependence
- temperature dependence
- soil NO 여부
- online 또는 offline 방식

## 13.2 기타 자연배출

필요 시 포함:

- Sea salt
- Windblown dust
- Wildfire / biomass burning
- Lightning NOx
- Marine gas
- Soil NO

중복 입력을 방지하기 위해 CMAQ inline emission과 외부 SMOKE emission을 동시에 사용할 때 설정을 명확히 확인한다.

---

# 14. CMAQ 구축 요구사항

## 14.1 핵심 모델

- CMAQ CCTM

## 14.2 주요 설정항목

- CMAQ version
- chemical mechanism
- aerosol module
- photolysis
- deposition
- emission streams
- IC/BC
- vertical layers
- domain
- start/end date
- restart
- MPI processor layout

## 14.3 초기 검증

공식 benchmark 수행 후 reference result와 비교한다.

---

# 15. CMAQ-ISAM 구축 요구사항

## 15.1 목적

다음 항목의 기여도를 정량화한다.

- 지역별
- 국가별
- 배출부문별
- source sector별
- 특정 배출원별

## 15.2 적용 목표

예시:

```text
한국
중국
일본
북한
해상
기타 동아시아
```

또는

```text
산업
발전
도로이동
비도로
선박
농업
주거
자연배출
```

등으로 source tagging 체계를 구축한다.

기존 CAMx PSAT/OSAT 분석체계와 비교·연계할 수 있도록 설계한다.

---

# 16. CMAQ-DDM-3D

필요 시 구축.

ISAM이 source contribution을 계산하는 데 비해 DDM-3D는 배출량 변화에 대한 농도 민감도 분석에 활용한다.

초기 구축 우선순위는 ISAM보다 낮게 둔다.

---

# 17. 초기 및 경계조건(IC/BC)

검토 대상:

- global model 기반 BC
- nested CMAQ
- profile 기반 IC/BC
- 기존 시스템 방식

확인 항목:

- 외부 모델
- chemical species mapping
- time interpolation
- vertical interpolation
- domain boundary processing

---

# 18. 후처리 및 검증

## 18.1 도구

- R
- Python
- VERDI
- NCO
- CDO
- netCDF utilities

## 18.2 모델 평가

필요한 통계:

- MB
- MNB
- MNE
- NMB
- NME
- RMSE
- correlation
- IOA
- 시간별/일별 비교
- 공간분포 비교

## 18.3 관측자료

후보:

- 도시대기측정망
- 국가대기측정망
- 기상관측망
- 위성자료
- 별도 연구자료

---

# 19. Case 기반 운영체계

최종 시스템은 프로그램별 설치폴더와 사례별 실행폴더를 분리한다.

예:

```text
/CASES
    /CASE_202307_O3
        /config
        /WPS
        /WRF
        /MCIP
        /EMIS
        /CMAQ
        /ISAM
        /POST
        /LOG
```

case별 변경항목:

- 기간
- domain
- 기상자료
- 배출량
- 배출 시나리오
- chemical mechanism
- IC/BC
- source tag
- processor 수

공통 프로그램은 다시 compile하지 않는다.

---

# 20. 자동화 목표

장기적으로 다음 형태의 실행체계를 목표로 한다.

예:

```bash
./run_case.sh CASE_202307_O3
```

또는

```bash
./run_case.sh   --start 2023-07-01   --end 2023-07-10   --domain BUSAN_D03   --met FNL   --emis CAPSS_REAS_MEGAN   --cmaq 5.5   --isam yes
```

단계별 성공 여부를 log로 기록하도록 한다.

```text
01_WPS      OK
02_WRF      OK
03_MCIP     OK
04_SMOKE    OK
05_CMAQ     OK
06_ISAM     OK
07_POST     OK
```

---

# 21. 기존 운영시스템 분석 계획

현재 운영 중인 시스템을 신규 Linux desktop에 재현하기 위해 다음 자료를 순차적으로 분석한다.

## 21.1 시스템 정보

- OS
- compiler
- MPI
- netCDF
- I/O API
- WRF
- WPS
- SMOKE
- CMAQ
- MCIP
- 관련 라이브러리

## 21.2 디렉터리 구조

권장 확인:

```bash
tree -L 2
```

또는

```bash
find . -maxdepth 2 -type d
```

## 21.3 주요 실행 스크립트

우선순위:

1. CMAQ CCTM run script
2. 전체 workflow script
3. MCIP script
4. SMOKE script
5. REAS 처리 script
6. 식생배출 처리 script
7. WRF/WPS namelist
8. 후처리 script

## 21.4 입력파일 header 확인

예:

```bash
ncdump -h filename.nc
```

이를 통해 다음 정보를 확인한다.

- dimension
- species
- units
- grid
- time structure
- vertical layers
- metadata

---

# 22. 단계별 구축 계획

## Phase 0. 기존 시스템 조사

- 기존 운영 Linux 시스템 정보 수집
- 디렉터리 구조 확인
- 모델 버전 확인
- run script 확보
- 배출자료 처리흐름 파악
- 기존 자료 중 재사용 가능한 항목 확인

## Phase 1. Linux workstation 구축

- OS 설치
- 사용자/디스크 구조 구성
- 개발도구 설치
- shell 환경 설정
- SSH/원격접속 설정
- 저장공간 구성

## Phase 2. Compiler 및 공통 library

- GNU compiler
- OpenMPI
- zlib
- HDF5
- netCDF-C
- netCDF-Fortran
- I/O API

## Phase 3. WRF/WPS

- WRF compile
- WPS compile
- official test
- 기상자료 download
- 동아시아 domain test

## Phase 4. MCIP

- compile
- WRF output 변환
- CMAQ grid 검증

## Phase 5. SMOKE

- install
- example case
- CAPSS test
- REAS test
- natural emissions test

## Phase 6. CMAQ

- compile
- official benchmark
- 실제 domain base run

## Phase 7. ISAM

- benchmark
- 국가별 tagging
- 배출부문별 tagging
- real case

## Phase 8. 자동화 및 후처리

- case manager
- batch scripts
- logging
- R/Python postprocessing
- 관측자료 검증

---

# 23. 프로젝트 산출물

최종 산출물은 다음과 같이 구성한다.

```text
00_CMAQ_Project_Master_Plan.md

01_Linux_Workstation_Setup.md
02_GNU_Compiler_MPI_Setup.md
03_NetCDF_HDF5_IOAPI_Setup.md

04_WRF_WPS_Install.md
05_WRF_Case_Run.md

06_MCIP_Install_Run.md

07_SMOKE_Install.md
08_CAPSS_Processing.md
09_REAS_Processing.md
10_Biogenic_Emissions.md

11_CMAQ_Install_Benchmark.md
12_CMAQ_Real_Case.md
13_CMAQ_ISAM.md
14_CMAQ_DDM.md

15_IC_BC_Processing.md
16_PostProcessing_Evaluation.md

17_Case_Automation.md
18_Troubleshooting_Log.md
19_System_Version_Record.md
20_Existing_System_Analysis.md
```

---

# 24. 공식 참고 페이지

## CMAQ

EPA CMAQ:
https://www.epa.gov/cmaq

CMAQ Documentation:
https://www.epa.gov/cmaq/cmaq-documentation

USEPA CMAQ GitHub:
https://github.com/USEPA/CMAQ

CMAS CMAQ:
https://www.cmascenter.org/cmaq/

CMAQ Linux environment:
https://github.com/USEPA/CMAQ/blob/main/DOCS/Users_Guide/Tutorials/CMAQ_UG_tutorial_configure_linux_environment.md

CMAQ compute environment:
https://github.com/USEPA/CMAQ/blob/main/DOCS/Users_Guide/CMAQ_UG_ch03_preparing_compute_environment.md

CMAQ model inputs:
https://github.com/USEPA/CMAQ/blob/main/DOCS/Users_Guide/CMAQ_UG_ch04_model_inputs.md

CMAQ simulation:
https://github.com/USEPA/CMAQ/blob/main/DOCS/Users_Guide/CMAQ_UG_ch05_running_a_simulation.md

CMAQ configuration:
https://github.com/USEPA/CMAQ/blob/main/DOCS/Users_Guide/CMAQ_UG_ch06_model_configuration_options.md

CMAQ benchmark:
https://github.com/USEPA/CMAQ/blob/main/DOCS/Users_Guide/Tutorials/CMAQ_UG_tutorial_benchmark.md

CMAQ ISAM:
https://github.com/USEPA/CMAQ/blob/main/DOCS/Users_Guide/Tutorials/CMAQ_UG_tutorial_ISAM.md

---

## WRF / WPS

WRF Users Page:
https://www2.mmm.ucar.edu/wrf/users/

WRF User Guide:
https://www2.mmm.ucar.edu/wrf/users/wrf_users_guide/build/html/

WRF compilation:
https://www2.mmm.ucar.edu/wrf/users/wrf_users_guide/build/html/compiling.html

WRF online compilation tutorial:
https://www2.mmm.ucar.edu/wrf/OnLineTutorial/compilation_tutorial.php

WRF GitHub:
https://github.com/wrf-model/WRF

---

## SMOKE

SMOKE official:
https://www.cmascenter.org/smoke/

SMOKE documentation:
https://www.cmascenter.org/smoke/documentation/5.3/html/

SMOKE Concepts:
https://www.cmascenter.org/smoke/documentation/5.3/html/ch02.html

CMAS Training:
https://www.cmascenter.org/training/classes.cfm

CMAS Forum:
https://forum.cmascenter.org/

---

## CMAS / I/O API

CMAS Center:
https://www.cmascenter.org/

I/O API:
https://cmascenter.org/ioapi/

I/O API GitHub:
https://github.com/cjcoats/ioapi-3.2

---

## netCDF

netCDF-C:
https://docs.unidata.ucar.edu/netcdf-c/current/

netCDF-Fortran:
https://docs.unidata.ucar.edu/netcdf-fortran/current/

---

## OpenMPI

OpenMPI Documentation:
https://docs.open-mpi.org/en/main/

OpenMPI Installation:
https://docs.open-mpi.org/en/main/installing-open-mpi/quickstart.html

---

## GNU Compiler

GCC:
https://gcc.gnu.org/

GNU Fortran:
https://gcc.gnu.org/fortran/

GNU Fortran manual:
https://gcc.gnu.org/onlinedocs/gfortran/

---

## Intel oneAPI

Intel Fortran:
https://www.intel.com/content/www/us/en/developer/tools/oneapi/fortran-compiler.html

Intel oneAPI:
https://www.intel.com/content/www/us/en/developer/tools/oneapi/oneapi-toolkit.html

---

## REAS

NIES REAS:
https://www.nies.go.jp/REAS/

REAS는 버전별 자료기간, species, grid, format이 다를 수 있으므로 실제 사용자료를 확인한 뒤 별도 문서에서 처리방법을 기록한다.

---

# 25. 향후 추가 조사 대상

다음 항목은 기존 운영 시스템 확인 후 확정한다.

- 실제 Linux 배포판
- compiler family
- WRF version
- CMAQ version
- SMOKE version
- chemical mechanism
- aerosol module
- meteorological input
- FNL/GFS/ERA5 사용 여부
- CAPSS 기준연도
- REAS version
- MEGAN/BEIS 사용 여부
- 화재배출 처리 여부
- 선박 배출원
- sea salt 처리
- windblown dust 처리
- IC/BC 생성방법
- CMAQ nesting 여부
- ISAM tag 체계
- 후처리 도구
- 자동화 방식
- 저장공간 및 backup 체계

---

# 26. 성공 기준

본 프로젝트는 다음 조건을 만족할 때 기본 구축이 완료된 것으로 본다.

1. Linux 시스템에서 WRF/WPS를 정상 compile 및 실행할 수 있다.
2. WRF 결과를 MCIP로 정상 변환할 수 있다.
3. SMOKE example case를 실행할 수 있다.
4. CMAQ official benchmark를 reference 수준으로 재현할 수 있다.
5. 실제 동아시아/부산 domain의 WRF-CMAQ base case를 실행할 수 있다.
6. CAPSS 국내 배출량을 CMAQ input으로 사용할 수 있다.
7. REAS 국외 배출량을 CMAQ input으로 사용할 수 있다.
8. 식생배출을 정상 반영할 수 있다.
9. ISAM을 이용해 지역/배출원 기여도를 계산할 수 있다.
10. 관측자료와 모델 결과를 비교할 수 있다.
11. case별 반복 실행이 가능한 구조를 갖춘다.
12. 전체 설치·실행·오류·수정 이력이 문서화되어 있다.

---

# 27. 프로젝트 운영 원칙

이 문서는 프로젝트의 최상위 기준 문서로 사용한다.

세부 설치 및 분석이 진행되면 다음 사항을 지속적으로 업데이트한다.

- 확정된 버전
- 실제 사용 명령어
- 실제 directory path
- 실제 compiler option
- 기존 시스템에서 확인된 설정
- 변경한 설정
- benchmark 결과
- 오류와 해결방법
- 실제 case run 결과

기존 운영 시스템의 스크립트와 자료는 가능한 한 그대로 분석하되,
단순 복사보다는 각 단계의 역할과 의존성을 이해하여 신규 시스템에 재현 가능한 형태로 정리한다.
