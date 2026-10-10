# Air Quality Modeling System

대기질 모델링 시스템의 설치, 환경 구성, 실행 스크립트 및 기술 문서를 관리하는 저장소입니다.

## 다음 구축·실행 때 따라 할 문서

아래 링크의 순서대로 기존 문서를 따른다. 입력파일 생성과 설치 명령을 설명만으로 생략하지 않고 각 문서 안에 기록한다.

1. [Linux 설치·네트워크·필수 도구](docs/linux/Rocky_Linux_Installation_Guide.md)
2. [GNU Compiler·SSH·MPI 테스트 파일 생성과 실행](docs/compiler/GNU_Compiler_OpenMPI_Installation_Guide.md)
3. [소스 다운로드부터 HDF5·netCDF·I/O API 설치](docs/libraries/Common_Libraries_Installation_Guide.md#library-start)
4. [WRF/WPS 설치·전체 namelist 생성·개별 프로그램 실행](docs/wrf/WRF_WPS_Installation_Guide.md#case-run)
5. [CMAQ 5.5 소스·config_cmaq.csh·MCIP 컴파일, 격자 결정과 MCIP 사례 실행](docs/mcip/MCIP_Installation_Guide.md#case-run)
6. [SMOKE 5.3 소스·Makeinclude 수정·컴파일·공식 예제 실행 계획](docs/smoke/SMOKE_Installation_Guide.md)

새 시스템 프로젝트 폴더 생성은 Master Plan §4.3을 따른다. 현재 성공 기록, 재구축용 보완 명령, 향후 계획을 각 문서에서 구분한다. 사용자 제공 `SCRIPTS/download_fnl.sh` 원문·생성·호출·기간별 파일 검사 명령은 [WRF/WPS §14.3.4](docs/wrf/WRF_WPS_Installation_Guide.md#fnl-download)에 통합했다. WPS는 CASE별 `WPS/namelist.wps`를 기준으로 설치본 실행파일을 절대경로로 호출하며, `GEOGRID.TBL`/`METGRID.TBL`은 `namelist.wps`의 절대경로 옵션으로 직접 참조한다. WRF runtime 자료는 `WRFV4.5.1/run/` 전체를 링크하지 않고, 현재 물리설정에 필요한 기본 7개(`LANDUSE.TBL`, `VEGPARM.TBL`, `SOILPARM.TBL`, `GENPARM.TBL`, `RRTM_DATA`, `RRTM_DATA_DBL`, `CAMtr_volume_mixing_ratio`)만 CASE/WRF에 심볼릭 링크하는 방식으로 정리했다.

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

- [WRF/WPS 설치 가이드](docs/wrf/WRF_WPS_Installation_Guide.md)

### MCIP

- [MCIP 구축 가이드](docs/mcip/MCIP_Installation_Guide.md)

### SMOKE

- [SMOKE 5.3 설치·컴파일 및 공식 예제 실행 가이드](docs/smoke/SMOKE_Installation_Guide.md)

### Master Plan과 현재 문서의 대응

Master Plan §22의 구축 단계는 그대로 적용한다. §23의 산출물명은 계획 당시 명칭이며, 현재 저장소에서는 아래 경로를 사용한다.

| 구축 단계 | 계획 당시 산출물명 | 현재 문서 |
|---|---|---|
| Phase 1. Linux workstation 구축 | `01_Linux_Workstation_Setup.md` | [Rocky Linux 설치](docs/linux/Rocky_Linux_Installation_Guide.md) |
| Phase 2. Compiler 및 공통 library | `02_GNU_Compiler_MPI_Setup.md` | [GNU Compiler / OpenMPI](docs/compiler/GNU_Compiler_OpenMPI_Installation_Guide.md) |
| Phase 2. Compiler 및 공통 library | `03_NetCDF_HDF5_IOAPI_Setup.md` | [공통 라이브러리](docs/libraries/Common_Libraries_Installation_Guide.md) |
| Phase 3. WRF/WPS | `04_WRF_WPS_Install.md` | [WRF/WPS 설치](docs/wrf/WRF_WPS_Installation_Guide.md) |
| Phase 4. MCIP | `06_MCIP_Install_Run.md` | [MCIP 구축](docs/mcip/MCIP_Installation_Guide.md) |
| Phase 5. SMOKE | `07_SMOKE_Install.md` | [SMOKE 5.3 구축](docs/smoke/SMOKE_Installation_Guide.md) |

Rocky Linux 문서는 Phase 1의 OS 설치와 기본 확인을, Compiler/MPI 문서는 Phase 1의 SFTP 설정 및 Phase 2의 compiler/MPI 구축을 다룬다. 공통 라이브러리 문서는 I/O API 3.2-20200828의 빌드, M3TOOLS 생성, 모듈 링크·실행 테스트 및 환경변수 등록까지 다룬다. 실제 설치 기록을 기준으로 **Phase 2(Compiler 및 공통 library)는 완료**되었다. **Phase 3 WRF/WPS(WRF 4.5.1 / WPS 4.5)는 완료**되었다. 반복 검증 CASE `TEST_20260901_REPEAT`에서 WPS(geogrid→ungrib→metgrid), `real.exe`, WRF dmpar 4코어 실행이 모두 정상 완료되었고, `rsl.error.0000`에서 `SUCCESS COMPLETE WRF` 및 d01~d04가 요청 종료시각 `2026-09-02_00:00:00`까지 도달한 것을 확인했다. **Phase 4 MCIP는 완료**되었다. CASE `TEST_20260901`의 d01~d04를 MCIP 5.5로 변환해 모두 `NORMAL TERMINATION`으로 종료했고, 생성된 GRIDDESC(27KM/09KM/03KM/01KM)가 이전 운영체계 격자와 일치함을 확인했다. **Phase 5 SMOKE 5.3 설치·컴파일은 완료(2026-10-10)**되었다. GFortran 11.5.0으로 실행파일 36개·내부 라이브러리 3개를 만들고 `ldd`로 라이브러리 연결을 확인했다. SMOKE 공식 ExampleCase-v3 실행 및 CAPSS·REAS·자연배출 처리는 아직 미수행이다. 다음 단계는 SMOKE 공식 예제 검증과 CMAQ 컴파일·benchmark(Phase 6)이다.

완료 상태는 사용자 제공 실행 기록과 기존 문서에 기재된 종료 메시지·시간·격자 확인 결과를 근거로 한다. 이번 문서 검토에서는 Linux 서버의 원본 로그·netCDF 파일을 직접 열거나 모델을 재실행하지 않았다. CMAQ CCTM 실행, 입력 결측값·물리량 QA 및 기존 15층 배출량·IC/BC와 새 34층 기상의 정합성은 아직 검증되지 않았다.

설치 가이드는 기존 Linux 및 Compiler/MPI 문서처럼 번호 없는 설명형 파일명을 사용한다. 공통 라이브러리 문서의 기존 `01_common_libraries_installation.md`는 `Common_Libraries_Installation_Guide.md`로 변경했다. 기본계획의 `00_`와 향후 산출물 번호는 계획 문서 체계로 유지한다.

현재 확인된 버전은 HDF5 1.14.6, netCDF-C 4.9.3, netCDF-Fortran 4.6.2, I/O API 3.2-20200828이다. I/O API 산출물은 `/home/woogon/CMAQ_MODEL/libs/ioapi-3.2-20200828/Linux2_x86_64gfort10`, include 파일은 같은 소스 루트의 `ioapi/fixed_src`에 있다.

### 모델 버전 기준

모델 버전은 CMAQ를 먼저 확정하고 나머지를 CMAQ 호환성에 맞춘다(Master Plan §3.5).

| 구성요소 | 버전 | 상태 |
|---|---|---|
| CMAQ | 5.5 (`CMAQv5.5.0.3_11Jul2025`) | 기존 기준 태그 유지. 5.5.0.4 공개로 Phase 6 전 재검토 필요. CCTM 컴파일·benchmark 미완료 |
| MCIP | 5.5 (CMAQ 저장소 `PREP/mcip`) | **Phase 4 완료.** `TEST_20260901` d01~d04 정상 변환, 이전 운영체계 GRIDDESC와 격자 일치. 제공 기록의 설치 커밋은 `9bd3734`이며 `PREP/mcip` 소스는 5.5.0.3·5.5.0.4 태그와 동일함을 확인. CCTM 전 태그 전환 필요([MCIP 가이드 §3, §5.2](docs/mcip/MCIP_Installation_Guide.md)) |
| WRF / WPS | 4.5.1 / 4.5 | **Phase 3 완료.** `TEST_20260901_REPEAT`에서 WPS, `real.exe`, WRF dmpar 4코어 정상 완료. `SUCCESS COMPLETE WRF` 및 d01~d04 종료시각 `2026-09-02_00:00:00` 확인 |
| I/O API | 3.2-20200828 | 설치 완료 |
| SMOKE | 5.3 (`SMOKEv5.3_June2026`) | **설치·컴파일 완료**(36개 실행파일, 3개 내부 라이브러리, `ldd` 확인), 공식 ExampleCase-v3 실행 검증 대기 |

### 구축 디렉터리와 자료·사례 사용 경로 (2026-10-08 문서 정리)

```text
/home/woogon/CMAQ_MODEL/
├── libs/                    # 공통 라이브러리, netCDF-WRF, grib2
├── src/                     # 원본 압축파일·라이브러리 소스·CMAQ_REPO
├── WRFV4.5.1/               # 컴파일된 WRF 본체
├── WPS-4.5/                 # 컴파일된 WPS 본체
├── CMAQv5.5/                # CMAQ 프로젝트 폴더(bldit_project.csh로 생성), MCIP 포함
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

`src/`에는 원본 소스·압축파일 및 라이브러리 빌드용 소스를 보관한다. 실제 컴파일된 모델 본체는 프로젝트 루트의 버전별 폴더에 둔다. 라이브러리 설치 결과는 `libs/`에 두며, I/O API는 이 아래에서 직접 빌드한 기존 구성을 유지한다. 지형·기상자료와 사례별 실행폴더는 모델 설치폴더와 분리한다. 실제 경로와 케이스 변경 기준은 [WRF/WPS 설치·실행 가이드](docs/wrf/WRF_WPS_Installation_Guide.md)을 기준으로 한다.

CASE 실행 시 `namelist.wps`는 `/home/woogon/CMAQ_MODEL/CASES/<REGION>/<CASE>/WPS/`에, `namelist.input`은 같은 CASE의 `WRF/`에 둔다. WPS 설치 디렉터리에 CASE용 namelist를 두지 않는다. `GEOGRID.TBL`과 `METGRID.TBL`은 CASE에 별도 링크하지 않고 `namelist.wps`의 `opt_geogrid_tbl_path` / `opt_metgrid_tbl_path`로 설치본을 직접 참조한다.

### 설치 시 확인한 사항

- `landread.c.dist` 대체는 현재 basic nesting에서 허용한다. 향후 moving nest 사용 시 RPC/TIRPC와 원본 `landread.c` 사용 여부를 재검토한다.
- WRF warning 103건은 실행파일 생성에 영향을 주지 않았고 fatal/link 오류는 확인되지 않았다. 최종 동작 여부는 실제 테스트 case 실행으로 검증한다.
- WPS serial 빌드는 `LC_ALL=C MPI_LIB= ./compile`로 수행했다. `MPI_LIB=`는 해당 명령에만 적용하며 OpenMPI 환경을 전역으로 해제하지 않는다.

상세 원인·명령·로그는 [WRF/WPS 설치 가이드](docs/wrf/WRF_WPS_Installation_Guide.md) §10.3, §10.7, §11.5를 기준으로 한다.

## Repository structure

```text
docs/
  planning/   # master plan
  linux/
  compiler/
  libraries/
  wrf/        # 설치·실행·GHG 오류를 하나의 문서에 통합
  mcip/       # CMAQ 소스·config_cmaq.csh·MCIP 컴파일·격자 결정·사례 실행
  smoke/      # SMOKE 5.3 설치·컴파일·오류 이력·공식 예제 예정 절차
```

`scripts/`, `config/`, `examples/`, `tests/`는 향후 저장소 구성 계획이다. 서버의 `SCRIPTS/download_fnl.sh`와 GitHub에 등록된 파일을 구분한다.

현재 저장소는 초기 구성 단계이며, Linux 환경설정, compiler/MPI, 공통 라이브러리, WRF/WPS, MCIP, SMOKE, CMAQ 및 후처리 관련 문서를 같은 체계로 관리합니다.
