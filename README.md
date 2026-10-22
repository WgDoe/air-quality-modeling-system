# Air Quality Modeling System

대기질 모델링 시스템의 설치, 환경 구성, 실행 스크립트 및 기술 문서를 관리하는 저장소입니다.

## 다음 구축·실행 때 따라 할 문서

아래 링크의 순서대로 기존 문서를 따른다. 입력파일 생성과 설치 명령을 설명만으로 생략하지 않고 각 문서 안에 기록한다.

1. [Linux 설치·네트워크·필수 도구](docs/linux/Rocky_Linux_Installation_Guide.md)
2. [GNU Compiler·SSH·MPI 테스트 파일 생성과 실행](docs/compiler/GNU_Compiler_OpenMPI_Installation_Guide.md)
3. [소스 다운로드부터 HDF5·netCDF·I/O API 설치](docs/libraries/Common_Libraries_Installation_Guide.md#library-start)
4. [WRF/WPS 설치·전체 namelist 생성·개별 프로그램 실행](docs/wrf/WRF_WPS_Installation_Guide.md#case-run)
5. [CMAQ 5.5 소스·config_cmaq.csh·MCIP 컴파일, 격자 결정과 MCIP 사례 실행](docs/mcip/MCIP_Installation_Guide.md#case-run)
6. [SMOKE 5.3 소스·포인터 수정·컴파일·공식 예제 검증](docs/smoke/01_SMOKE_Installation_Guide.md)
7. [부산 배출량 개선 계획: CAPSS 2023·HTAP v3.1·신규 시나리오](docs/smoke/03_SMOKE_Emission_Improvement_Plan.md)
8. [부산 실제사례 실행 가이드 — CAPSS 2023 입력 생성·설치와 점 onetime 완료 (§8.1)](docs/smoke/04_SMOKE_Busan_Case_Run_Guide.md)

기존 CAPSS 2017 입력 준비 문서는 현행 목록에서 제외했다. 2023에도 필요한 공통 설정·검증 절차는 [부산 실행 가이드 §8](docs/smoke/04_SMOKE_Busan_Case_Run_Guide.md)에 통합했으며, 과거 원문은 Git 이력에서 확인할 수 있다.

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

**[00. SMOKE 문서 읽는 순서 및 재작업 시작점](docs/smoke/00_README_First.md)** — 01 설치 → 02 기존 체계 분석 → 03 개선 계획 → 04 부산 실제 실행, 90 오류 수정 참고자료.

- [SMOKE 5.3 설치·컴파일 및 공식 예제 실행 가이드](docs/smoke/01_SMOKE_Installation_Guide.md)
- [procar2pt.f 포인터 초기화 수정 기록](docs/smoke/90_SMOKE_procar2pt_Fix.md)
- [기존 SMOKE 2.7 배출량 산정체계 분석 (신규 5.3 전환 참고)](docs/smoke/02_Legacy_SMOKE27_Emission_Processing.md)
- [SMOKE 부산 배출량 개선 계획: CAPSS 2023 / HTAP v3.1 전환 기준](docs/smoke/03_SMOKE_Emission_Improvement_Plan.md)
- [SMOKE 부산 실제사례 실행 가이드: CAPSS 2023 입력 일괄 설치와 점 onetime 09KM 완료 (§8.1)](docs/smoke/04_SMOKE_Busan_Case_Run_Guide.md)

### Master Plan과 현재 문서의 대응

Master Plan §22의 구축 단계는 그대로 적용한다. §23의 산출물명은 계획 당시 명칭이며, 현재 저장소에서는 아래 경로를 사용한다.

| 구축 단계 | 계획 당시 산출물명 | 현재 문서 |
|---|---|---|
| Phase 1. Linux workstation 구축 | `01_Linux_Workstation_Setup.md` | [Rocky Linux 설치](docs/linux/Rocky_Linux_Installation_Guide.md) |
| Phase 2. Compiler 및 공통 library | `02_GNU_Compiler_MPI_Setup.md` | [GNU Compiler / OpenMPI](docs/compiler/GNU_Compiler_OpenMPI_Installation_Guide.md) |
| Phase 2. Compiler 및 공통 library | `03_NetCDF_HDF5_IOAPI_Setup.md` | [공통 라이브러리](docs/libraries/Common_Libraries_Installation_Guide.md) |
| Phase 3. WRF/WPS | `04_WRF_WPS_Install.md` | [WRF/WPS 설치](docs/wrf/WRF_WPS_Installation_Guide.md) |
| Phase 4. MCIP | `06_MCIP_Install_Run.md` | [MCIP 구축](docs/mcip/MCIP_Installation_Guide.md) |
| Phase 5. SMOKE | `07_SMOKE_Install.md` | [SMOKE 5.3 구축](docs/smoke/01_SMOKE_Installation_Guide.md) |

### 구축 진행 현황 (2026-10-22 기준)

| Phase | 구성요소 | 검증된 진행 상태 | 다음 확인 사항 |
|---|---|---|---|
| Phase 1 | Rocky Linux 및 기본 환경 | OS 설치, SFTP 등 기본 환경 설정 완료 | 필요 시 운영환경 유지관리 |
| Phase 2 | GNU Compiler / OpenMPI / 공통 라이브러리 | GCC/GFortran 11.5.0, OpenMPI, HDF5, netCDF, I/O API 설치·테스트 완료 | 개별 모델과의 호환성 지속 확인 |
| Phase 3 | WRF 4.5.1 / WPS 4.5 | 반복 사례 `TEST_20260901_REPEAT`에서 WPS, `real.exe`, WRF dmpar 4코어 실행 완료 | 실제 대기질 사례의 입력·출력 QA |
| Phase 4 | MCIP 5.5 | `TEST_20260901` d01~d04 변환 및 격자 일치 확인 완료 | CCTM 기상 입력 및 수직층 정합성 검증 |
| Phase 5 | SMOKE 5.3 | 공식 예제 검증 완료; CAPSS 2017 구 입력은 실행 대상에서 제외. CAPSS 2023 국내 4부문 입력 생성·설치 및 점 09KM onetime 정상 종료·시도별 보고서 합계 일치(2026-10-22 제공 기록) | 국내 점 09KM daily 실행 및 면·이동·바다·나머지 격자·국외·생물성·병합 후속 검증 |
| Phase 6 | CMAQ CCTM | 컴파일·benchmark 미완료 | 기준 태그 확정, 컴파일 및 benchmark |
| Phase 7 | CMAQ-ISAM | 미수행 | benchmark 및 배출원 기여도 분석 |

WRF 반복 검증에서는 `rsl.error.0000`의 `SUCCESS COMPLETE WRF` 메시지와 d01~d04의 요청 종료시각(`2026-09-02_00:00:00`) 도달을 확인했다. MCIP는 네 영역 모두 `NORMAL TERMINATION`으로 종료되었고, GRIDDESC(27KM/09KM/03KM/01KM)가 기존 운영체계 격자와 일치했다.

**SMOKE 공식 예제 검증 완료(2026-10-19).** 면오염원·점오염원·도로이동·BEIS4 및 최종 병합 완료 기록은 사용자 제공 문서에 근거한다. 부산 사례의 **기존 CAPSS 2017 기준선**은 `TEST_20260901/EMIS/` 폴더·공통 입력 5종 및 국내 면 FF10·공간/시간/종분배·실행 스크립트 준비까지 사용자 기록상 완료했으나 부산 SMOKE 배출량 계산 및 CMAQ 연계 검증은 미완료다. [부산 사례 실행 가이드](docs/smoke/04_SMOKE_Busan_Case_Run_Guide.md)를 따른다. [설치·예제 가이드](docs/smoke/01_SMOKE_Installation_Guide.md), [procar2pt 수정 기록](docs/smoke/90_SMOKE_procar2pt_Fix.md)을 참고한다. 재설치에 쓰는 수정본 4개는 [`docs/smoke/files/`](docs/smoke/files/)에 보관했다.

재설치할 때 필요한 수정과 적용 순서는 다음과 같다. 수정본은 모두 [`docs/smoke/files/`](docs/smoke/files/)에 있다.

| 적용 단계 | 파일 | 변경 내용 |
|---|---|---|
| 컴파일 전 | `Makeinclude` | GNU Fortran 옵션, netCDF 라이브러리 경로·rpath 지정 |
| 컴파일 전 | `procar2pt.f` | 지역 포인터 15개 초기화 |
| 예제 실행 전 | `directory_definitions.csh` | 예제·SMOKE 실행파일·I/O API 경로 지정 |
| 최종 병합 전 | `sectorlist_2022he_cb6_22m_withbeis_withrwc` | 교육 서버 경로를 실제 예제 경로로 변경 |

적용 위치와 원본·수정본 md5는 [설치 가이드 §6·§10.3](docs/smoke/01_SMOKE_Installation_Guide.md)에 있다. 예제의 `afdust_adj` 보조 실행파일은 EPA 제공 Intel 빌드를 사용했으므로 전체 GNU 빌드 검증 완료를 의미하지 않는다. 다음 작업은 해당 보조 프로그램의 GNU 빌드·대체 방법 확인, 부산 배출량 처리와 CMAQ 입력 정합성 검증이다.

**검증 범위:** 완료 표시는 사용자 제공 실행 화면·로그와 기존 문서에 기록된 종료 메시지·시간·격자 확인 결과에 근거한다. 이번 GitHub 문서 수정 과정에서 Linux 서버의 원본 로그·netCDF 파일을 직접 열거나 모델을 재실행하지 않았다. CMAQ CCTM 실행, 입력 결측값·물리량 QA, 기존 15층 배출량·IC/BC와 새로운 34층 기상의 정합성은 아직 검증되지 않았다.

SMOKE 하위 문서는 재작업 시 읽는 순서를 드러내기 위해 `00_` 안내 → `01_` 설치 → `02_` 기존 체계 분석 → `03_` 배출량 개선 → `04_` 실제 실행으로 번호를 붙였다. `90_`은 오류 수정용 참고자료다. 공통 라이브러리 문서의 기존 `01_common_libraries_installation.md`는 `Common_Libraries_Installation_Guide.md`로 변경했다. 기본계획의 `00_`와 향후 산출물 번호는 계획 문서 체계로 유지한다.

현재 확인된 버전은 HDF5 1.14.6, netCDF-C 4.9.3, netCDF-Fortran 4.6.2, I/O API 3.2-20200828이다. I/O API 산출물은 `/home/woogon/CMAQ_MODEL/libs/ioapi-3.2-20200828/Linux2_x86_64gfort10`, include 파일은 같은 소스 루트의 `ioapi/fixed_src`에 있다.

**2026-10-22 CAPSS 2023 실행 갱신:** 국내 점·면·이동·바다 입력자료 생성 및 일괄 설치, **09KM 국내 점 onetime 정상 종료·시도별 배출량 보고서 합계 일치**(제공받은 실행 기록 기준). 다음 단계는 **09KM 국내 점 daily** 실행이다. 국외 적용 예정 자료는 HTAP v3.1(2020년)이다. [04 부산 실행 가이드](docs/smoke/04_SMOKE_Busan_Case_Run_Guide.md) §8~§9 및 [03 배출량 개선 계획](docs/smoke/03_SMOKE_Emission_Improvement_Plan.md)을 따른다. GitHub에는 [2023capss 설치·생성·실행 스크립트](docs/smoke/files/busan/2023capss/)가 있으며 대용량 FF10·surrogate는 별도 ZIP 원본 또는 생성기로 관리한다. 기존 2017 작업에서 계승할 공통 검증 기준은 04 가이드 부록 B에 통합했다. CAPSS 코드표 XLSX 2개와 운영체계 참조 TXT 6개는 입력 재현에 필요하며 [reference/](docs/smoke/files/busan/2023capss/reference/)에 등록했다(2026-10-22).

### 모델 버전 기준

모델 버전은 CMAQ를 먼저 확정하고 나머지를 CMAQ 호환성에 맞춘다(Master Plan §3.5).

| 구성요소 | 버전 | 상태 |
|---|---|---|
| CMAQ | 5.5 (`CMAQv5.5.0.3_11Jul2025`) | 기존 기준 태그 유지. 5.5.0.4 공개로 Phase 6 전 재검토 필요. CCTM 컴파일·benchmark 미완료 |
| MCIP | 5.5 (CMAQ 저장소 `PREP/mcip`) | **Phase 4 완료.** `TEST_20260901` d01~d04 정상 변환, 이전 운영체계 GRIDDESC와 격자 일치. 제공 기록의 설치 커밋은 `9bd3734`이며 `PREP/mcip` 소스는 5.5.0.3·5.5.0.4 태그와 동일함을 확인. CCTM 전 태그 전환 필요([MCIP 가이드 §3, §5.2](docs/mcip/MCIP_Installation_Guide.md)) |
| WRF / WPS | 4.5.1 / 4.5 | **Phase 3 완료.** `TEST_20260901_REPEAT`에서 WPS, `real.exe`, WRF dmpar 4코어 정상 완료. `SUCCESS COMPLETE WRF` 및 d01~d04 종료시각 `2026-09-02_00:00:00` 확인 |
| I/O API | 3.2-20200828 | 설치 완료 |
| SMOKE | 5.3 (`SMOKEv5.3_June2026`) | 설치·컴파일 및 공식 SMOKE-ExampleCase-v3 검증 완료(2026-10-19, 사용자 제공 문서 기준). 최종 병합 31개·굴뚝/inline 파일 1,032개 생성 기록. 부산 CAPSS·REAS·자연배출 및 CMAQ 연계 검증은 미완료 |

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
  smoke/      # SMOKE 5.3 설치·예제 검증, 기존 2.7 분석, CAPSS 2023 개선 계획, 부산 사례 실행 기록
```

`scripts/`, `config/`, `examples/`, `tests/`는 향후 저장소 구성 계획이다. 서버의 `SCRIPTS/download_fnl.sh`와 GitHub에 등록된 파일을 구분한다.

현재 저장소는 초기 구성 단계이며, Linux 환경설정, compiler/MPI, 공통 라이브러리, WRF/WPS, MCIP, SMOKE, CMAQ 및 후처리 관련 문서를 같은 체계로 관리합니다.
