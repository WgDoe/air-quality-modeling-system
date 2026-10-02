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

### Master Plan과 현재 문서의 대응

Master Plan §22의 구축 단계는 그대로 적용한다. §23의 산출물명은 계획 당시 명칭이며, 현재 저장소에서는 아래 경로를 사용한다.

| 구축 단계 | 계획 당시 산출물명 | 현재 문서 |
|---|---|---|
| Phase 1. Linux workstation 구축 | `01_Linux_Workstation_Setup.md` | [Rocky Linux 설치](docs/linux/Rocky_Linux_Installation_Guide.md) |
| Phase 2. Compiler 및 공통 library | `02_GNU_Compiler_MPI_Setup.md` | [GNU Compiler / OpenMPI](docs/compiler/GNU_Compiler_OpenMPI_Installation_Guide.md) |
| Phase 2. Compiler 및 공통 library | `03_NetCDF_HDF5_IOAPI_Setup.md` | [공통 라이브러리](docs/libraries/Common_Libraries_Installation_Guide.md) |

Rocky Linux 문서는 Phase 1의 OS 설치와 기본 확인을, Compiler/MPI 문서는 Phase 1의 SFTP 설정 및 Phase 2의 compiler/MPI 구축을 다룬다. 공통 라이브러리 문서는 I/O API 3.2-20200828의 빌드, M3TOOLS 생성, 모듈 링크·실행 테스트 및 환경변수 등록까지 다룬다. 실제 설치 기록을 기준으로 **Phase 2(Compiler 및 공통 library)는 완료**되었으며, 다음 구축 대상은 **Phase 3 WRF/WPS**이다. WRF/WPS 설치·실행 완료를 뜻하지 않는다.

설치 가이드는 기존 Linux 및 Compiler/MPI 문서처럼 번호 없는 설명형 파일명을 사용한다. 공통 라이브러리 문서의 기존 `01_common_libraries_installation.md`는 `Common_Libraries_Installation_Guide.md`로 변경했다. 기본계획의 `00_`와 향후 산출물 번호는 계획 문서 체계로 유지한다.

현재 확인된 버전은 HDF5 1.14.6, netCDF-C 4.9.3, netCDF-Fortran 4.6.2, I/O API 3.2-20200828이다. I/O API 산출물은 `/home/woogon/CMAQ_MODEL/libs/ioapi-3.2-20200828/Linux2_x86_64gfort10`, include 파일은 같은 소스 루트의 `ioapi/fixed_src`에 있다.

## Repository structure

```text
docs/
  planning/
  linux/
  compiler/
  libraries/
scripts/
config/
examples/
tests/
```

현재 저장소는 초기 구성 단계이며, Linux 환경설정, compiler/MPI, 공통 라이브러리, WRF/WPS, MCIP, SMOKE, CMAQ 및 후처리 관련 문서를 같은 체계로 관리합니다.
