# Air Quality Modeling System

대기질 모델링 시스템의 설치, 환경 구성, 실행 스크립트 및 기술 문서를 관리하는 저장소입니다.

## Documentation

### Project Planning

- [CMAQ Project Master Plan](docs/planning/00_CMAQ_Project_Master_Plan.md)

### Linux

- [Rocky Linux Installation Guide](docs/linux/Rocky_Linux_Installation_Guide.md)

### Compiler / MPI

- [GNU Compiler & OpenMPI Installation Guide](docs/compiler/GNU_Compiler_OpenMPI_Installation_Guide.md)

### Libraries

- [Common Libraries Installation (zlib / HDF5 / netCDF-C / netCDF-Fortran / I/O API)](docs/libraries/Common_Libraries_Installation_Guide.md)

### WRF / WPS

- [WRF/WPS 설치 및 검증 기록](docs/wrf/WRF_WPS_Installation_Guide.md)

### Master Plan과 현재 문서의 대응

Master Plan §22의 구축 단계는 그대로 적용한다. §23의 산출물명은 계획 당시 명칭이며, 현재 저장소에서는 아래 경로를 사용한다.

| 구축 단계 | 계획 당시 산출물명 | 현재 문서 |
|---|---|---|
| Phase 1. Linux workstation 구축 | `01_Linux_Workstation_Setup.md` | [Rocky Linux 설치](docs/linux/Rocky_Linux_Installation_Guide.md) |
| Phase 2. Compiler 및 공통 library | `02_GNU_Compiler_MPI_Setup.md` | [GNU Compiler / OpenMPI](docs/compiler/GNU_Compiler_OpenMPI_Installation_Guide.md) |
| Phase 2. Compiler 및 공통 library | `03_NetCDF_HDF5_IOAPI_Setup.md` | [공통 라이브러리](docs/libraries/Common_Libraries_Installation_Guide.md) |
| Phase 3. WRF/WPS | `04_WRF_WPS_Install.md` | [WRF/WPS 설치](docs/wrf/WRF_WPS_Installation_Guide.md) |

Rocky Linux 문서는 Phase 1의 OS 설치와 기본 확인을, Compiler/MPI 문서는 Phase 1의 SFTP 설정 및 Phase 2의 compiler/MPI 구축을 다룬다. 공통 라이브러리 문서는 I/O API 3.2-20200828의 빌드, M3TOOLS 생성, 모듈 링크·실행 테스트 및 환경변수 등록까지 다룬다. 실제 설치 기록을 기준으로 **Phase 2(Compiler 및 공통 library)는 완료**되었다. **Phase 3 WRF/WPS(WRF 4.5.1 / WPS 4.5)는 설치·컴파일·동적 라이브러리 연결 확인 완료, 실제 입력자료 실행검증 미완료** 상태이다. 다음 작업은 WPS_GEOG와 실제 기상자료를 준비하여 `geogrid → ungrib → metgrid → real.exe → wrf.exe` 전체 실행을 검증하는 것이다. Phase 3 전체 완료를 뜻하지 않으며, 실행 검증 후 MCIP(Phase 4)로 이어간다.

설치 가이드는 기존 Linux 및 Compiler/MPI 문서처럼 번호 없는 설명형 파일명을 사용한다. 공통 라이브러리 문서의 기존 `01_common_libraries_installation.md`는 `Common_Libraries_Installation_Guide.md`로 변경했다. 기본계획의 `00_`와 향후 산출물 번호는 계획 문서 체계로 유지한다.

현재 확인된 버전은 HDF5 1.14.6, netCDF-C 4.9.3, netCDF-Fortran 4.6.2, I/O API 3.2-20200828이다. I/O API 산출물은 `/home/woogon/CMAQ_MODEL/libs/ioapi-3.2-20200828/Linux2_x86_64gfort10`, include 파일은 같은 소스 루트의 `ioapi/fixed_src`에 있다.

### 모델 버전 기준

모델 버전은 CMAQ를 먼저 확정하고 나머지를 CMAQ 호환성에 맞춘다(Master Plan §3.5).

| 구성요소 | 버전 | 상태 |
|---|---|---|
| CMAQ | 5.5 (`CMAQv5.5.0.3_11Jul2025`) | 확정. 현재 GitHub Releases에서 pre-release로 표시되는 5.5 계열 최신 bugfix 태그, 설치 예정(Phase 6) |
| MCIP | CMAQ 5.5.0.3 포함 버전 | 확정, 설치 예정(Phase 4) |
| WRF / WPS | 4.5.1 / 4.5 | 설치·컴파일·동적 라이브러리 연결 확인 완료, 실제 입력자료 실행검증 미완료 (Phase 3) |
| I/O API | 3.2-20200828 | 설치 완료 |

### 현재 구축 디렉터리 (2026-10-03)

```text
/home/woogon/CMAQ_MODEL/
├── libs/
│   ├── HDF5-1.14.6/
│   ├── netCDF-C-4.9.3/
│   ├── netCDF-Fortran-4.6.2/
│   ├── netCDF-WRF/
│   ├── grib2/
│   └── ioapi-3.2-20200828/
├── src/
│   ├── grib2/
│   ├── v4.5.1.tar.gz
│   └── WPS-4.5.tar.gz
├── WRFV4.5.1/
└── WPS-4.5/
```

`src/`에는 원본 소스·압축파일 및 라이브러리 빌드용 소스를 보관한다. 실제 컴파일된 모델 본체는 프로젝트 루트의 버전별 폴더에 둔다. 라이브러리 설치 결과는 `libs/`에 두며, I/O API는 이 아래에서 직접 빌드한 기존 구성을 유지한다. 지형·기상자료와 사례별 실행폴더는 모델 설치폴더와 분리하며, 저장 위치는 아직 확정하지 않았다.

### 설치 시 확인한 사항

- `landread.c.dist` 대체는 현재 basic nesting에서 허용한다. 향후 moving nest 사용 시 RPC/TIRPC와 원본 `landread.c` 사용 여부를 재검토한다.
- WRF warning 103건은 실행파일 생성에 영향을 주지 않았고 fatal/link 오류는 없었다. 실제 test run으로 최종 검증 예정이다.
- WPS serial 빌드는 `LC_ALL=C MPI_LIB= ./compile`로 수행했다. `MPI_LIB=`는 해당 명령에만 적용하며 OpenMPI 환경을 전역으로 해제하지 않는다.

상세 원인·명령·로그는 [WRF/WPS 구축 기록](docs/wrf/WRF_WPS_Installation_Guide.md) §8.6, §9.3, §11.5를 기준으로 한다.

## Repository structure

```text
docs/
  planning/
  linux/
  compiler/
  libraries/
  wrf/
scripts/
config/
examples/
tests/
```

현재 저장소는 초기 구성 단계이며, Linux 환경설정, compiler/MPI, 공통 라이브러리, WRF/WPS, MCIP, SMOKE, CMAQ 및 후처리 관련 문서를 같은 체계로 관리합니다.