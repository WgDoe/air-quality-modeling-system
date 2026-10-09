# CMAQ 통합 대기질 모델링 시스템 구축 기본계획 및 요구사항

작성일: 2026-09-23  
수정일: 2026-10-03 (CMAQ 5.5 기준 모델 버전 확정, §3.5)  
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

## 3.5 모델 버전 결정 기준 (CMAQ 우선)

### 3.5.1 원칙

모델 버전은 개별 프로그램의 최신 버전이 아니라 **최종 목적 모델인 CMAQ의 버전을 먼저 확정**하고, 나머지 구성요소를 CMAQ와의 호환성에 맞춰 결정한다.

```text
CMAQ 버전 확정
  ↓
CMAQ에 포함된 MCIP 버전 결정
  ↓
MCIP/CMAQ가 처리 가능한 WRF/WPS 버전 결정
  ↓
공통 라이브러리 호환성 확인
```

근거:

- MCIP는 CMAQ 저장소(`PREP/mcip`)에 포함되어 CMAQ와 함께 배포되므로, 처리 가능한 WRF 출력 형식은 CMAQ 버전에 종속된다.
- 과거 CMAQ v5.3 이전(MCIP v5.0 이전)은 WRF 3.9부터 도입된 hybrid 연직좌표를 처리하지 못한 사례가 있다.
- Pleim-Xiu LSM, ACM2 PBL 등 CMAQ와 짝을 이루는 WRF 물리옵션이 버전에 따라 달라진다.
- 결합형 WRF-CMAQ는 지원하는 WRF 버전 범위가 명시되어 있다(CMAQ 5.5 기준 WRF 4.4~4.5.1).

### 3.5.2 확정 버전 (2026-10-03)

| 구성요소 | 확정 버전 | 비고 |
|---|---|---|
| CMAQ | 5.5 (태그 `CMAQv5.5.0.3_11Jul2025`) | 기준 모델. 현재 공개된 5.5 계열 최신 bugfix 태그이며 GitHub Releases에서는 pre-release로 표시됨. 문서·benchmark 자료는 v5.5 기준 |
| MCIP | CMAQ 5.5.0.3 포함 버전 | `PREP/mcip` |
| ICON/BCON 등 전처리 | CMAQ 5.5.0.3 포함 버전 | `PREP/` |
| WRF | 4.5.1 (태그 `v4.5.1`) | WRF-CMAQv5.5 결합 호환범위(4.4~4.5.1)의 상한. **설치·컴파일·반복 사례 실행 검증 완료.** `TEST_20260901_REPEAT`에서 WRF dmpar 4코어가 `SUCCESS COMPLETE WRF`로 종료되고 d01~d04가 `2026-09-02_00:00:00`까지 도달함 |
| WPS | 4.5 (태그 `v4.5`) | WRF 4.5.x와 짝을 이루는 버전. **설치·컴파일·반복 사례 실행 검증 완료.** `TEST_20260901_REPEAT`에서 geogrid→ungrib→metgrid 정상 완료 |
| I/O API | 3.2-20200828 | CMAQ v5.5 공식 문서에서 tested/stable version으로 제시되는 버전. 설치 완료 |
| netCDF-C / netCDF-Fortran | 4.9.3 / 4.6.2 | 설치 완료. CMAQ 5.5는 C/Fortran 경로를 별도 변수로 지정 가능 |
| HDF5 | 1.14.6 | 설치 완료 |
| Compiler / MPI | GNU 11.5.0 / OpenMPI | 설치 완료 |
| SMOKE | 미정 | Phase 5 착수 시 CMAQ 5.5 호환 버전으로 결정 |

WRF 4.5.1을 선택한 이유:

- 분리 실행(WRF → MCIP → CMAQ)에서 CMAQ 5.5 MCIP로 처리 가능하다.
- EPA가 WRF-CMAQv5.5를 시험한 범위 안에 있어 향후 결합 실행(에어로졸-기상 피드백 등)으로 확장할 때 WRF를 재설치할 필요가 없다.
- WRF 4.6 이상은 분리 실행에는 사용할 수 있으나 결합형 WRF-CMAQv5.5 지원 범위를 벗어난다.

### 3.5.3 CMAQ 5.5 설치 시 연계 사항

- CMAQ 5.5의 `config_cmaq.csh`는 `NETCDF_LIB_DIR`/`NETCDF_INCL_DIR`(netCDF-C)와 `NETCDFF_LIB_DIR`/`NETCDFF_INCL_DIR`(netCDF-Fortran)를 따로 지정하므로, 현재처럼 C와 Fortran을 별도 디렉터리에 설치한 구조를 그대로 사용한다.
- I/O API 경로는 다음과 같이 지정한다.

```text
IOAPI_INCL_DIR = /home/woogon/CMAQ_MODEL/libs/ioapi-3.2-20200828/ioapi/fixed_src
IOAPI_LIB_DIR  = /home/woogon/CMAQ_MODEL/libs/ioapi-3.2-20200828/Linux2_x86_64gfort10
```

- 재현성을 위해 CMAQ는 `main` 브랜치가 아니라 확정 태그로 내려받는다.

```bash
git clone -b CMAQv5.5.0.3_11Jul2025 https://github.com/USEPA/CMAQ.git CMAQ_REPO
```

### 3.5.4 재검토 조건

다음의 경우 버전 기준을 재검토하고 이 절을 갱신한다.

- 기존 운영 시스템 조사(Phase 0)에서 결과 연속성 확보가 필요한 CMAQ/WRF 버전이 확인된 경우
- CMAQ 차기 주요 버전이 공개되어 benchmark 자료와 문서가 갱신된 경우
- CMAQ 5.5 계열에 연구 결과에 영향을 주는 버그수정 태그가 추가된 경우

---

# 4. 하드웨어 및 운영체제 요구사항

## 4.1 대상 시스템

기본 대상:

- x86_64 Linux desktop/workstation
- 다중 CPU core
- 충분한 RAM
- 대용량 SSD 또는 NVMe 저장장치
- 장기자료 보관용 추가 HDD/NAS 선택 가능

## 4.2 현재 구축 디렉터리와 자료 분리 원칙

```text
/home/woogon/CMAQ_MODEL/
├── libs/                    # 공통 라이브러리, netCDF-WRF, grib2
├── src/                     # 원본 압축파일·라이브러리 빌드 소스
├── WRFV4.5.1/               # 컴파일된 WRF 본체
├── WPS-4.5/                 # 컴파일된 WPS 본체
├── DATA/
│   ├── WPS_GEOG/            # 정적 지형자료
│   └── MET/FNL/YYYY/MM/     # ds083.2 1도 GRIB2, 6시간 간격
├── CASES/BUSAN/TEST_20260901/
│   ├── WPS/
│   ├── WRF/
│   ├── MCIP/
│   ├── EMIS/
│   ├── CMAQ/
│   ├── POST/
│   └── LOG/
└── SCRIPTS/
    └── download_fnl.sh
```

위 구조는 2026-10-08 사용자 제공 실제 경로를 반영한다. `src/`는 원본 보관, 모델 본체는 프로젝트 루트, 라이브러리는 `libs/`, 공유 자료는 `DATA/`, 실행 결과는 CASE별로 분리한다. 자세한 역할과 현재/계획 구조는 [WRF/WPS 가이드 §2](../wrf/WRF_WPS_Installation_Guide.md)를 따른다.
---

## 4.3 새 시스템 프로젝트 폴더 생성

OS 설치 및 일반 사용자 woogon 로그인 후 실행한다. 모델 설치·자료·CASE는 같은 루트 아래에서 역할을 분리한다.

```bash
mkdir -p /home/woogon/CMAQ_MODEL/{libs,src,DATA/WPS_GEOG,DATA/MET/FNL,SCRIPTS,logs/system,logs/ioapi,tests/compiler_mpi}
mkdir -p /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/{WPS,WRF,MCIP,EMIS,CMAQ,POST,LOG}
find /home/woogon/CMAQ_MODEL -maxdepth 3 -type d | sort
df -h /home/woogon/CMAQ_MODEL
```

설치 폴더 WRFV4.5.1/WPS-4.5는 WRF 문서의 소스 압축 해제 단계에서 생성한다. 위 mkdir는 모델을 설치하거나 download_fnl.sh를 생성하지 않는다. libs/src만 있던 예전 구조와 DATA/CASES/SCRIPTS 운영 구조를 구분한다.

## 4.4 재구축 때 읽을 순서

| 단계 | 실제 명령·입력파일 위치 |
|---|---|
| Linux 설치·네트워크·사전 도구 | [Linux 설치 가이드](../linux/Rocky_Linux_Installation_Guide.md) §3~17 |
| Compiler 설치·SSH·MPI 소스 생성 및 실행 | [Compiler/MPI 가이드](../compiler/GNU_Compiler_OpenMPI_Installation_Guide.md) §3~10 |
| HDF5/netCDF 원본 다운로드·빌드·I/O API | [공통 라이브러리](../libraries/Common_Libraries_Installation_Guide.md) §2.1~9 |
| WRF/WPS 빌드와 전체 namelist·개별 실행 | [WRF/WPS 가이드](../wrf/WRF_WPS_Installation_Guide.md) §4~14 |

이미 설치된 프로그램은 재컴파일하지 않고 CASE만 새로 만든다. MCIP·배출량·CMAQ 등 아직 수행되지 않은 단계는 계획이다. 실제로 성공한 명령이 확보되는 즉시 해당 기존 문서 체계에 기록한다. FNL 다운로드 스크립트 원문·파일 생성·시작/종료 UTC 인자·기간별 검사 명령은 [WRF/WPS §14.3.4](../wrf/WRF_WPS_Installation_Guide.md#fnl-download)에 통합했다.

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

## 8.6 버전 및 빌드 확인사항

- 버전: WRF 4.5.1, WPS 4.5 (§3.5 CMAQ 5.5 기준)
- WRF용 `NETCDF`는 별도 설치된 C/Fortran 라이브러리를 묶은 `libs/netCDF-WRF` 통합 링크 디렉터리로 구성 완료했다. CMAQ는 §3.5.3의 C/Fortran 별도 경로를 사용한다.
- WPS GRIB2 라이브러리 libpng 1.2.50, JasPer 1.900.1은 `libs/grib2`에 설치 완료했다. 현재 FNL GRIB2 입력을 사용한 ungrib·metgrid 성공이 확인되었다.
- 빌드 스크립트용 `tcsh`(csh)를 설치하고 `perl`, `m4`를 확인했다.
- CMAQ 연계를 고려하여 PX LSM, ACM2 PBL 등 CMAQ 권장 물리옵션 조합을 우선 검토한다.

현재 상태: **WRF 4.5.1 / WPS 4.5 설치·컴파일 및 사례 실행 성공. TEST_20260901의 WPS·real.exe 성공, WRF dmpar 4코어 오류 없이 실행 중이며 wrfout 결과파일 생성 확인(사용자 확인)**. WRF는 GNU dmpar, basic nesting으로, WPS는 GNU serial, GRIB2 지원으로 빌드했다. 현재 FNL 사례 실행은 [사례 실행 가이드](../wrf/WRF_WPS_Installation_Guide.md)를 따른다. WRF 실행·출력 생성은 성공으로 기록한다. 다음 단계는 MCIP 구축·입력 변환 준비이며, 현재 모의 종료 후 최종 시각을 확인해 출력을 전달한다.

설치 시 확인한 중요 사항(상세 기록: [WRF/WPS 설치 가이드](../wrf/WRF_WPS_Installation_Guide.md)):

- §10.3: `landread.c.dist` 대체는 현재 basic nesting에서 허용하며, 향후 moving nest 사용 시 RPC/TIRPC 및 원본 `landread.c` 사용 여부를 재검토한다.
- §10.7: WRF warning 103건은 실행파일 생성에 영향을 주지 않았고 fatal/link 오류는 확인되지 않았다. 최종 동작 여부는 실제 테스트 case 실행으로 검증한다.
- §11.5: OpenMPI module의 `MPI_LIB`가 WPS 링크 명령과 충돌하여 `LC_ALL=C MPI_LIB= ./compile`로 해결했다. `MPI_LIB=`는 WPS compile 명령에만 적용하고 전역 MPI 환경은 유지한다.

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
- MCIP 버전: CMAQ 5.5.0.3 포함 버전(`PREP/mcip`) 사용
- CMAQ 버전 compatibility: CMAQ 5.5와 동일 태그에서 빌드하여 일치시킴

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

- CMAQ version: 5.5 (`CMAQv5.5.0.3_11Jul2025`, §3.5)
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

CMAQ 5.5 공식 benchmark:

- 사례: 2018년 7월 1~2일, 2일 모의
- 영역: 미국 북동부 12 km(12NE3), 100 × 105 격자, 35층
- 화학기작: `cb6r5_ae7_aq`, 건성침적 `m3dry`
- 입력자료: `CMAQv5.4_2018_12NE3_Benchmark_2Day_Input.tar.gz`
- 비교용 출력: `output_CCTM_v55_gcc_Bench_2018_12NE3_cb6r5_ae7_aq_m3dry.tar.gz`
- 출처: CMAS Center Data Warehouse(AWS S3, `v5_5/`)

benchmark 입력에는 MCIP 기상자료, 배출량, IC/BC가 포함되어 있으므로 WRF/SMOKE 구축 이전에도 수행할 수 있다.

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

현재 실행 사례는 `/home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901`이다. 내부 폴더는 `WPS`, `WRF`, `MCIP`, `EMIS`, `CMAQ`, `POST`, `LOG`이며, `config`와 `ISAM`은 향후 확장 계획이다. 실행은 CASE 폴더에서 모델 실행파일의 절대경로를 직접 호출한다. [실행 기준](../wrf/WRF_WPS_Installation_Guide.md)을 따른다.

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

현재 운영은 CASE 폴더에서 WPS/WRF 실행파일을 절대경로로 직접 호출한다. `run_case.sh`는 아직 구현되지 않은 장기 자동화 목표이며 다음 호출은 계획 예시이다.

예:

```bash
./run_case.sh BUSAN/TEST_20260901
```

또는

```bash
./run_case.sh   --start 2023-07-01   --end 2023-07-10   --domain BUSAN_D03   --met FNL   --emis CAPSS_REAS_MEGAN   --cmaq 5.5   --isam yes
```

단계별 성공 여부를 log로 기록하도록 한다. 아래 `OK`는 향후 성공 로그의 형식 예시이며 현재 실행 상태가 아니다. 현재 WPS·real.exe와 WRF 실행·결과파일 생성은 성공으로 기록했다. WRF는 오류 없이 실행 중이며 종료 메시지와 최종 출력 시각은 모의 종료 후 확인한다.

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

## 현재 진행상황 (설치 확인: 2026-10-03, 실행 기록 반영: 2026-10-08)

실제 설치 명령과 확인 결과는 [공통 라이브러리 구축 기록](../libraries/Common_Libraries_Installation_Guide.md) 및 [WRF/WPS 설치 가이드](../wrf/WRF_WPS_Installation_Guide.md)을 기준으로 한다.

- **Phase 2 완료**: GNU GCC/GFortran 11.5.0 및 OpenMPI 설치·동작 확인, 시스템 zlib 확인, HDF5 1.14.6, netCDF-C 4.9.3, netCDF-Fortran 4.6.2 설치·검증 완료.
- **I/O API 3.2-20200828 완료**: `Linux2_x86_64gfort10`, `nocpl`, OpenMP 미사용 구성으로 라이브러리·모듈·M3TOOLS 빌드와 링크·실행 테스트 완료. 환경변수 등록 및 경로 확인 완료.
- I/O API 라이브러리·모듈·실행파일: `/home/woogon/CMAQ_MODEL/libs/ioapi-3.2-20200828/Linux2_x86_64gfort10`.
- I/O API include: `/home/woogon/CMAQ_MODEL/libs/ioapi-3.2-20200828/ioapi/fixed_src`.
- **모델 버전 확정 (2026-10-03)**: CMAQ 5.5(`CMAQv5.5.0.3_11Jul2025`)를 기준으로 MCIP(CMAQ 포함), WRF 4.5.1, WPS 4.5로 결정. 상세 기준은 §3.5.
- **Phase 3 설치·사례 실행 성공**: WRF 4.5.1 / WPS 4.5 설치·컴파일 및 사례 실행 성공. TEST_20260901의 WPS·real.exe 성공, WRF dmpar 4코어 오류 없이 실행 중이며 wrfout 결과파일 생성 확인(사용자 확인). 모델 본체 경로는 §4.2, 상세 빌드·오류 해결은 WRF/WPS 설치 가이드를 참조한다.
- **다음 작업**: MCIP(Phase 4) 설치·컴파일 및 입력 변환 준비. 현재 WRF 모의 종료 후 `SUCCESS COMPLETE WRF`와 d01~d04 최종 출력 시각을 확인하여 MCIP에 전달한다. MCIP·CMAQ 결과는 아직 완료로 기록하지 않는다.

아래 Phase 목록은 전체 구축 계획이며, 이후 단계의 완료 기록이 아니다.

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

- 버전: WRF 4.5.1 / WPS 4.5 (§3.5)

| 항목 | 현재 상태 |
|---|---|
| netCDF 통합 링크, libpng 1.2.50, JasPer 1.900.1 | 구성·설치 완료 |
| WRF 4.5.1 | 설치·컴파일 및 사례 실행 성공. TEST_20260901의 WPS·real.exe 성공, WRF dmpar 4코어 오류 없이 실행 중이며 wrfout 결과파일 생성 확인(사용자 확인) |
| WPS 4.5 | 설치·컴파일 및 사례 실행 성공. TEST_20260901의 WPS·real.exe 성공, WRF dmpar 4코어 오류 없이 실행 중이며 wrfout 결과파일 생성 확인(사용자 확인) |
| WPS_GEOG 및 FNL ds083.2 자료 준비 | 현재 사례 실행에 사용 |
| `geogrid → ungrib → metgrid → real.exe → wrf.exe` 전체 실행 검증 | 실행 및 wrfout 생성 성공(사용자 확인); 현재 WRF 오류 없이 실행 중 |
| official test / 동아시아 domain test | 미완료 |

현재 사례는 FNL GRIB2 → FNL:* → met_em → real.exe → WRF 실행과 wrfout 생성까지 성공했다. 이 성공 기록은 현재까지 오류 없는 실행·출력 생성을 뜻하며 전체 모의 기간의 정상 종료는 종료 메시지와 최종 Times를 확인한 뒤 별도 기록한다.

## Phase 4. MCIP

현재 다음 구축 단계이다. 폴더가 있다는 것과 설치·실행 완료는 구분한다. WRF 모의 종료 후 d01~d04 출력·시간 범위를 확인하고 변환을 수행한다.

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

- 버전: CMAQ 5.5 (`CMAQv5.5.0.3_11Jul2025`)
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

아래 목록은 계획 당시 산출물명이다. 현재 작성된 설치 가이드는 번호 없는 설명형 파일명을 사용하며, 향후 문서명은 작성 시 확정한다.

| 계획 당시 산출물명 | 현재 저장소 문서 |
|---|---|
| `01_Linux_Workstation_Setup.md` | [Rocky Linux 설치 가이드](../linux/Rocky_Linux_Installation_Guide.md) |
| `02_GNU_Compiler_MPI_Setup.md` | [GNU Compiler 및 OpenMPI 설치 가이드](../compiler/GNU_Compiler_OpenMPI_Installation_Guide.md) |
| `03_NetCDF_HDF5_IOAPI_Setup.md` | [공통 라이브러리 구축 기록](../libraries/Common_Libraries_Installation_Guide.md) |
| `04_WRF_WPS_Install.md` | [WRF/WPS 설치 가이드](../wrf/WRF_WPS_Installation_Guide.md) |
| `05_WRF_Case_Run.md` | 별도 파일 대신 WRF/WPS 설치 가이드 §14에 통합 |

계획 당시 전체 산출물 목록:

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

WRF-CMAQ (호환 WRF 버전):
https://github.com/USEPA/CMAQ/blob/main/DOCS/Users_Guide/CMAQ_UG_ch13_WRF-CMAQ.md

CMAQ releases / tags:
https://github.com/USEPA/CMAQ/releases

CMAQ benchmark data (v5.5):
https://cmaq-release-benchmark-data-for-easy-download.s3.amazonaws.com/index.html#v5_5/

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

WPS GitHub:
https://github.com/wrf-model/WPS

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

- 기존 운영 시스템의 실제 Linux 배포판 및 compiler family(신규 구축 환경은 Rocky Linux 9.8, GNU 11.5.0으로 확인됨)
- WRF version (신규 구축은 4.5.1로 확정, §3.5. 기존 시스템 버전은 비교용으로 확인)
- CMAQ version (신규 구축은 5.5로 확정, §3.5. 기존 시스템 버전은 비교용으로 확인)
- SMOKE version
- chemical mechanism
- aerosol module
- meteorological input
- 현재 사례는 FNL ds083.2 사용; 다른 사례의 GFS/ERA5 변경 여부
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

- 확정된 버전(§3.5)
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
