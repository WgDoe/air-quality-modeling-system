# CMAQ 모델링 시스템 MCIP 구축 가이드

**다음 CASE 실행 명령을 보려면 [격자 결정·실행 스크립트·사례 실행](#case-run)으로 이동한다.** 이전 운영체계 격자에 맞춘 X0/Y0 계산, `run_mcip_busan.csh` 전체 생성 명령, d01~d04 실행과 결과 확인을 §10에 순서대로 정리했다.

## 1. 목적
Rocky Linux 기반 CMAQ 통합 대기질 모델링 시스템의 Phase 4(MCIP) 설치·컴파일·사례 실행·오류 해결 절차를 하나의 문서로 기록한다.

이 문서는 실제 구축 과정에서 발생한 문제를 모두 해결한 뒤, **확인된 사례 설정을 순서대로 재현하도록**로 재구성한 것이다. 각 단계의 `> 참고` 상자에는 해당 조치가 필요한 이유와, 생략했을 때 나타나는 오류를 적었다. 실제 구축 중에 겪은 문제의 경위는 [부록 A](#부록-a-구축-중-발생한-문제-기록)에 따로 정리했다.

설치 순서:

```text
4장  공통 실행 규칙 확인
  ↓
5장  CMAQ 5.5 소스 다운로드 + 프로젝트 폴더(CMAQv5.5) 생성
  ↓
6장  config_cmaq.csh 라이브러리 경로 설정
  ↓
7장  MCIP 컴파일 (Makefile gfortran 설정 → make → 확인)
  ↓
10장 사례 실행 (격자 결정 → 스크립트 생성 → d01~d04 실행 → 결과 확인)
```

현재 상태(2026-10-09 실행 검증 기준): **Phase 4 MCIP 완료.** CASE `TEST_20260901`의 d01~d04 wrfout을 MCIP 5.5로 변환했고, 네 영역 모두 `NORMAL TERMINATION`으로 종료되었다. 생성된 `GRIDDESC_27KM/09KM/03KM/01KM`의 원점·격자 크기·셀 수가 이전 운영체계 GRIDDESC와 완전히 일치함을 확인했다. 연직층은 WRF 34층, 출력 시간은 48개(2026-08-31 01 UTC ~ 09-02 00 UTC)이다.

완료 상태는 사용자 제공 실행 기록과 기존 문서에 기재된 종료 메시지·시간·격자 확인 결과를 근거로 한다. 이번 문서 검토에서는 Linux 서버의 원본 로그·netCDF 파일을 직접 열거나 모델을 재실행하지 않았다. CMAQ CCTM 실행, 입력 결측값·물리량 QA 및 기존 15층 배출량·IC/BC와 새 34층 기상의 정합성은 아직 검증되지 않았다.

## 2. 구축 환경

- OS: Rocky Linux 9.8 (Blue Onyx), x86_64, **시스템 언어 한국어**
- 사용자: `woogon`
- 프로젝트 루트: `/home/woogon/CMAQ_MODEL`
- CPU 코어: 4 / 메모리: 약 7.2 GB / `/home` 여유 공간: 약 494 GB
- GCC / GFortran: 11.5.0
- OpenMPI: 4.1.1 (Rocky Linux 패키지, Environment Modules로 활성화)
- 공통 라이브러리: HDF5 1.14.6, netCDF-C 4.9.3, netCDF-Fortran 4.6.2, I/O API 3.2-20200828
- 입력 기상자료: WRF 4.5.1 / WPS 4.5 CASE 결과(d01~d04, 하이브리드 연직좌표, `e_vert=35` → 34층)

선행 문서:

- [공통 라이브러리 구축 기록](../libraries/Common_Libraries_Installation_Guide.md)
- [WRF/WPS 설치 가이드](../wrf/WRF_WPS_Installation_Guide.md) — §7의 `libs/netCDF-WRF` 통합 링크 디렉터리, §14의 CASE 실행 결과(`wrfout`, `geo_em`)

이 문서는 위 문서의 설치·실행이 끝나 있고, `~/.bashrc`에 `CMAQ_LIBS`, netCDF/HDF5의 `LD_LIBRARY_PATH`, OpenMPI module load가 등록되어 있다고 가정한다.

디렉터리 구조:

[구축 기본계획](../planning/00_CMAQ_Project_Master_Plan.md) §4.2에 따라 CMAQ 원본 저장소는 `src/CMAQ_REPO`에, 실제 빌드·실행에 쓰는 CMAQ 프로젝트 폴더는 프로젝트 루트의 `CMAQv5.5`에 둔다. MCIP 결과와 실행 로그는 CASE의 `MCIP/<격자명>/`에 영역별로 둔다.

```text
/home/woogon/CMAQ_MODEL/
├── libs/                    # 공통 라이브러리, netCDF-WRF, grib2
├── src/
│   └── CMAQ_REPO/           # CMAQ 원본 저장소 (git clone)
├── WRFV4.5.1/  WPS-4.5/
├── CMAQv5.5/                # CMAQ 프로젝트 폴더 (bldit_project.csh로 생성)
│   ├── config_cmaq.csh
│   ├── lib/x86_64/gcc/      # ioapi, netcdf, netcdff, mpi 링크
│   └── PREP/mcip/
│       ├── src/             # Makefile, mcip.exe
│       └── scripts/         # run_mcip.csh(원본), run_mcip_busan.csh
└── CASES/BUSAN/TEST_20260901/
    ├── WPS/                 # geo_em.d01~d04.nc
    ├── WRF/                 # wrfout_d0X_YYYY-MM-DD_00:00:00
    ├── MCIP/
    │   ├── 27KM/            # GRIDDESC_27KM, MET*/GRID* 파일, mcip_d01.log
    │   ├── 09KM/
    │   ├── 03KM/
    │   └── 01KM/
    └── LOG/                 # WRF/WPS namelist·로그 사본
```

---

## 3. 버전 확정

모델 버전은 CMAQ를 먼저 확정하고 나머지를 CMAQ 호환성에 맞춘다(기본계획 §3.5).

| 구성요소 | 버전 | 근거 |
|---|---|---|
| CMAQ | 5.5 (기본계획 태그 `CMAQv5.5.0.3_11Jul2025`) | 기준 모델(기본계획 §3.5.2) |
| MCIP | 5.5 (`MCIP V5.5 FROZEN 09/19/2024`, 실행 로그 표기) | CMAQ 저장소 `PREP/mcip`에 포함 |

> **실제 설치 기록과 공식 소스 비교를 구분한다.** 제공 문서의 설치 소스는 `main` 커밋 `9bd3734176479c2e49139fea98e1d5e8a16170e3`(2025-08-25)이다. 2026-10-09 공식 Git tree 확인에서 이 커밋과 `CMAQv5.5.0.3_11Jul2025`, `CMAQv5.5.0.4_08Oct2026`의 `PREP` tree SHA는 모두 `1226fc47136a66187b1b1a8b23ba0a9ff4c37d12`로 동일했다. 따라서 `PREP/mcip` 소스도 동일하다. 서버의 로컬 수정·컴파일 옵션·라이브러리·입력파일까지 확인한 것은 아니므로 실행파일·결과의 동일성을 단정하지 않는다. 세 버전의 `CCTM` tree는 서로 다르므로 Phase 6 전에 기준 태그와 빌드 프로젝트를 일치시킨다(§5.2).

> **태그 재검토(채택 미정).** [5.5.0.4 릴리스](https://github.com/USEPA/CMAQ/releases/tag/CMAQv5.5.0.4_08Oct2026)는 2026-10-08 21:09 UTC(한국시간 10-09 06:09)에 공개되었고 `pre-release`로 표시된다. HONIT AERO_DATA 오타, STAGE 수은 양방향 flux 및 CASTNET QA 처리 수정이 포함된다. 기존 5.5.0.3 기준은 유지하며, Phase 6 전 화학기작·침적 설정과 benchmark 영향을 검토한 뒤 채택 태그를 확정한다(기본계획 §3.5.4).

---

## 4. 공통 실행 규칙

[WRF/WPS 가이드 §4](../wrf/WRF_WPS_Installation_Guide.md)의 규칙을 그대로 따른다.

- csh 스크립트(`config_cmaq.csh`, `bldit_project.csh`)와 `make`는 앞에 `LC_ALL=C`를 붙인다.
- 화면 출력은 `2>&1 | tee 로그파일이름`으로 파일에 남긴다. 단, MCIP 실행 로그는 실행 스크립트가 결과 폴더에 직접 남긴다(10.5).
- Windows에서 SFTP로 옮긴 스크립트·Makefile은 실행 전에 줄바꿈을 정리한다([Compiler/MPI 가이드 §3.5](../compiler/GNU_Compiler_OpenMPI_Installation_Guide.md)).

```bash
sed -i 's/\r$//' 파일이름
```

> **참고: 생략하면** csh 스크립트가 `Command not found`, `Unmatched "` 같은 오류를 내거나 Makefile 변수 끝에 보이지 않는 문자(`\r`)가 붙어 경로를 찾지 못한다.

---

## 5. CMAQ 5.5 소스 다운로드와 프로젝트 폴더 생성

§5.1~5.4는 새 경로에서 재구축할 때의 절차다. 기존 성공 프로젝트에 다시 실행하면 config·MCIP Makefile·실행 스크립트가 덮어써질 수 있다. 기존 구축 기록의 보존과 Phase 6 태그 준비는 §5.2를 따른다.

### 5.1 소스 다운로드

MCIP는 CMAQ 저장소 안에 들어 있으므로 CMAQ 전체를 내려받는다. 재현성을 위해 기본계획의 확정 태그로 내려받는다.

```bash
git --version || sudo dnf install -y git

cd /home/woogon/CMAQ_MODEL/src
git clone -b CMAQv5.5.0.3_11Jul2025 https://github.com/USEPA/CMAQ.git CMAQ_REPO
cd CMAQ_REPO
git log -1 --format='%h %ad %s'
ls
```

정상 결과: `CCTM  DOCS  POST  PREP  ...  bldit_project.csh` 등이 보인다.

> **참고: 이번 구축 기록** 실제로는 `git clone -b main https://github.com/USEPA/CMAQ.git CMAQ_REPO`로 내려받았다(커밋 `9bd3734`, 2025-08-25). 공식 MCIP 소스 동일성은 확인했으나 빌드·결과 동일성은 별도 검증 대상이다(3장).

### 5.2 Phase 6용 태그와 프로젝트 일치시키기 (예정 절차)

기존 `src/CMAQ_REPO`에서 태그만 checkout해도 프로젝트에 복사된 CCTM 빌드·실행 스크립트와 기존 빌드 산출물은 갱신되지 않는다. CCTM 소스는 `config_cmaq.csh`의 `CMAQ_REPO` 경로에서 참조하므로 이 경로의 태그도 함께 확인한다. 기존 MCIP 실행환경과 설정을 보존하고, 결정한 태그를 별도 소스·프로젝트 경로에 준비한다. 아래는 기존 기준 5.5.0.3을 유지할 때의 **미수행 예시**다. 5.5.0.4를 채택하면 태그와 두 경로를 함께 바꾸고 기록한다.

```bash
cd /home/woogon/CMAQ_MODEL/src/CMAQ_REPO
git rev-parse HEAD
git status --short
git diff -- bldit_project.csh

cd /home/woogon/CMAQ_MODEL/src
TAG=CMAQv5.5.0.3_11Jul2025
SRC=/home/woogon/CMAQ_MODEL/src/CMAQ_REPO_5.5.0.3
PROJECT=/home/woogon/CMAQ_MODEL/CMAQv5.5_5.5.0.3

# 기존 경로가 있으면 중단하고 내용부터 확인한다.
if [ -e "$SRC" ] || [ -e "$PROJECT" ]; then
    echo "Target exists; inspect before continuing."
else
    git clone --branch "$TAG" --single-branch https://github.com/USEPA/CMAQ.git "$SRC" &&
    (
        cd "$SRC" || exit 1
        git rev-parse HEAD
        git describe --tags --exact-match
        git diff --stat 9bd3734176479c2e49139fea98e1d5e8a16170e3 HEAD -- PREP/mcip
        cp bldit_project.csh bldit_project.csh.orig
        sed -i "s#^[[:space:]]*set CMAQ_HOME = .*#set CMAQ_HOME = $PROJECT#" bldit_project.csh
        set -o pipefail
        LC_ALL=C ./bldit_project.csh 2>&1 | tee bldit_project.log
    )
fi
```

새 프로젝트의 `config_cmaq.csh`에서 `CMAQ_HOME`과 `CMAQ_REPO`가 각각 위 `PROJECT`, `SRC`를 가리키는지 확인한다. `config_cmaq.csh`를 §6 방식으로 설정하되 `cd` 대상은 위 `PROJECT`로 바꾼다. 기존 config 전체를 덮어 복사하지 말고 태그 원본과 비교해 경로 변경만 적용한다. 태그·전체 커밋 SHA, 프로젝트 경로, 설정 diff와 빌드 로그를 보존한 후 CCTM·ICON·BCON을 빌드하고 benchmark를 수행한다. 기존 MCIP 실행파일은 보존하며 재빌드 필요 여부는 해당 태그 소스와 기존 로컬 변경을 비교해 판단한다.

### 5.3 프로젝트 폴더 위치 지정

`bldit_project.csh`의 `CMAQ_HOME`을 프로젝트 루트의 `CMAQv5.5`로 바꾼다.

```bash
cd /home/woogon/CMAQ_MODEL/src/CMAQ_REPO
cp bldit_project.csh bldit_project.csh.orig
sed -i 's#^[[:space:]]*set CMAQ_HOME = .*#set CMAQ_HOME = /home/woogon/CMAQ_MODEL/CMAQv5.5#' bldit_project.csh
grep -nE '^[[:space:]]*set CMAQ_HOME' bldit_project.csh
```

정상 결과: `set CMAQ_HOME = /home/woogon/CMAQ_MODEL/CMAQv5.5`

### 5.4 프로젝트 폴더 생성

```bash
cd /home/woogon/CMAQ_MODEL/src/CMAQ_REPO
LC_ALL=C ./bldit_project.csh 2>&1 | tee bldit_project.log
ls /home/woogon/CMAQ_MODEL/CMAQv5.5
```

정상 결과: `CCTM  POST  PREP  config_cmaq.csh  ...`가 보인다.

> **참고:** 폴더 이름은 `CMAQv5.5`로 통일한다. 다른 이름(예: `CMAQ_v5.5`)으로 이미 만들었다면 현재 실행 중인 작업·기존 링크·스크립트 참조와 대상 경로 존재 여부를 먼저 확인한다. 경로 정리는 보존 사본을 만든 뒤 수행하고 `CMAQ_HOME`, config와 실행 스크립트의 참조도 함께 갱신한다.

---

## 6. config_cmaq.csh 라이브러리 경로 설정

`config_cmaq.csh`의 gcc 항목에 I/O API, netCDF, MPI 경로를 적으면, 이 스크립트가 경로를 `CMAQv5.5/lib/x86_64/gcc/` 아래에 심볼릭 링크로 연결한다. 이후 CMAQ 구성요소(CCTM, ICON, BCON 등)의 빌드가 이 링크를 공통으로 사용한다.

### 6.1 경로 확인

```bash
cd /home/woogon/CMAQ_MODEL/libs
ls ioapi-3.2-20200828/Linux2_x86_64gfort10/libioapi.a
ls ioapi-3.2-20200828/Linux2_x86_64gfort10/m3utilio.mod
ls ioapi-3.2-20200828/ioapi/fixed_src | head
ls netCDF-WRF/lib | head
ls netCDF-WRF/include | head
mpifort --showme:incdirs
mpifort --showme:libdirs
```

정상 결과:

- `libioapi.a`, `m3utilio.mod`가 보인다.
- `fixed_src`에 `ATDSC3.EXT`, `CONST3.EXT`, `PARMS3.EXT` 등 `*.EXT` 파일이 보인다.
- `netCDF-WRF/lib`에 `libnetcdf.*`, `libnetcdff.*`가, `include`에 `netcdf.h`, `netcdf.mod`가 보인다.
- `mpifort` 결과가 `/usr/include/openmpi-x86_64`, `/usr/lib64/openmpi/lib`이다.

> **참고: netCDF 경로** 기본계획 §3.5.3은 netCDF-C와 netCDF-Fortran의 별도 설치 경로를 지정하는 방식을 예정했으나, 이번 구축에서는 WRF용으로 만든 통합 링크 디렉터리 `libs/netCDF-WRF`(WRF/WPS 가이드 §7)를 C·Fortran 양쪽에 지정했다. 이 디렉터리에서 실제 C·Fortran 라이브러리 및 헤더를 가리키는 링크를 §6.1과 §6.3으로 확인한다.

### 6.2 설정 수정

원본 `config_cmaq.csh`의 gcc 항목에는 `ioapi_inc_gcc` 같은 자리표시 문자열이 들어 있다. 아래 `sed`로 한 번에 실제 경로로 바꾼다. MPI 경로가 6.1 결과와 다르면 마지막 두 줄을 그 값으로 고친다.

```bash
cd /home/woogon/CMAQ_MODEL/CMAQv5.5
cp config_cmaq.csh config_cmaq.csh.orig

L=/home/woogon/CMAQ_MODEL/libs
sed -i \
 -e "s#netcdf_root_gcc#$L/netCDF-WRF#" \
 -e "s#ioapi_root_gcc#$L/ioapi-3.2-20200828#" \
 -e "s#ioapi_inc_gcc#$L/ioapi-3.2-20200828/ioapi/fixed_src#" \
 -e "s#ioapi_lib_gcc#$L/ioapi-3.2-20200828/Linux2_x86_64gfort10#" \
 -e "s#netcdff_lib_gcc#$L/netCDF-WRF/lib#" \
 -e "s#netcdff_inc_gcc#$L/netCDF-WRF/include#" \
 -e "s#netcdf_lib_gcc#$L/netCDF-WRF/lib#" \
 -e "s#netcdf_inc_gcc#$L/netCDF-WRF/include#" \
 -e "s#mpi_incl_gcc#/usr/include/openmpi-x86_64#" \
 -e "s#mpi_lib_gcc#/usr/lib64/openmpi/lib#" config_cmaq.csh

sed -n '/case gcc:/,/setenv myCC/p' config_cmaq.csh
```

정상 결과(주요 줄):

```text
    case gcc:
        setenv NETCDF /home/woogon/CMAQ_MODEL/libs/netCDF-WRF
        setenv IOAPI  /home/woogon/CMAQ_MODEL/libs/ioapi-3.2-20200828
        setenv IOAPI_INCL_DIR   /home/woogon/CMAQ_MODEL/libs/ioapi-3.2-20200828/ioapi/fixed_src
        setenv IOAPI_LIB_DIR    /home/woogon/CMAQ_MODEL/libs/ioapi-3.2-20200828/Linux2_x86_64gfort10
        setenv NETCDF_LIB_DIR   /home/woogon/CMAQ_MODEL/libs/netCDF-WRF/lib
        setenv NETCDF_INCL_DIR  /home/woogon/CMAQ_MODEL/libs/netCDF-WRF/include
        setenv NETCDFF_LIB_DIR  /home/woogon/CMAQ_MODEL/libs/netCDF-WRF/lib
        setenv NETCDFF_INCL_DIR /home/woogon/CMAQ_MODEL/libs/netCDF-WRF/include
        setenv MPI_INCL_DIR     /usr/include/openmpi-x86_64
        setenv MPI_LIB_DIR      /usr/lib64/openmpi/lib
        setenv myFC mpifort
        setenv myCC gcc
```

`NETCDF`, `IOAPI` 두 줄은 결합형 WRF-CMAQ용이며 MCIP·분리 실행 CCTM에는 쓰이지 않지만 함께 채워 둔다. 컴파일러 옵션(`myFSTD`, `myFFLAGS` 등)은 변경하지 않는다.

### 6.3 적용 및 확인

```bash
cd /home/woogon/CMAQ_MODEL/CMAQv5.5
LC_ALL=C ./config_cmaq.csh gcc
ls -l lib/x86_64/gcc/*
```

정상 결과: `Compiler is set to gcc` 한 줄만 출력되고, 링크는 다음과 같다.

```text
lib/x86_64/gcc/ioapi:    include_files -> .../ioapi-3.2-20200828/ioapi/fixed_src
                         lib           -> .../ioapi-3.2-20200828/Linux2_x86_64gfort10
lib/x86_64/gcc/mpi:      include -> /usr/include/openmpi-x86_64
                         lib     -> /usr/lib64/openmpi/lib
lib/x86_64/gcc/netcdf:   include -> .../netCDF-WRF/include
                         lib     -> .../netCDF-WRF/lib
lib/x86_64/gcc/netcdff:  include -> .../netCDF-WRF/include
                         lib     -> .../netCDF-WRF/lib
```

> **참고:** 이 스크립트는 마지막에 `libnetcdf.a`, `libnetcdff.a`, `libioapi.a`, `m3utilio.mod`의 존재를 검사한다. 하나라도 없으면 오류 메시지를 출력하고 끝난다. 또 `lib/` 아래 링크가 이미 있으면 다시 만들지 않으므로, **잘못된 경로로 실행했다면** `ls -ld lib`와 `ls -l lib/x86_64/gcc/*`로 내용을 확인한다. 빌드·실행 중인 작업이 없을 때 `lib`를 고유한 보존 경로로 이동한 뒤 다시 설정한다. 예: `backup=lib.before_config_$(date -u +%Y%m%dT%H%M%SZ); test ! -e "$backup" && mv -- lib "$backup" && LC_ALL=C ./config_cmaq.csh gcc`. 보존본을 재설정 직후 삭제하지 않는다.

---

## 7. MCIP 컴파일

MCIP는 `config_cmaq.csh`를 읽지 않고 `PREP/mcip/src/Makefile`에 컴파일러와 라이브러리 경로를 따로 적는다. 배포본 Makefile은 Intel(`ifort`) 설정이 켜져 있으므로 이를 주석 처리하고 gfortran 설정을 추가한다.

### 7.1 Makefile 수정

아래 변경은 태그 원본 Makefile에 한 번 적용한다. 이미 수정된 파일에 반복 적용하거나 `Makefile.orig`를 덮어쓰지 말고 기존 설정과 먼저 비교한다.

```bash
cd /home/woogon/CMAQ_MODEL/CMAQv5.5/PREP/mcip/src
cp Makefile Makefile.orig

# 1) 추가할 gfortran 설정 생성
cat > /tmp/mcip_gfort_block.txt << 'EOF'
#...gfortran (CMAQ_MODEL setup: GNU 11.5 + I/O API 3.2-20200828 + netCDF-WRF)
FC         = gfortran
NETCDF     = /home/woogon/CMAQ_MODEL/libs/netCDF-WRF
IOAPI_ROOT = /home/woogon/CMAQ_MODEL/libs/ioapi-3.2-20200828
IOAPI_BIN  = $(IOAPI_ROOT)/Linux2_x86_64gfort10
FFLAGS     = -O3 -I$(NETCDF)/include -I$(IOAPI_BIN) -I$(IOAPI_ROOT)/ioapi/fixed_src
LIBS       = -L$(IOAPI_BIN) -lioapi \
             -L$(NETCDF)/lib -lnetcdff -lnetcdf -fopenmp

EOF

# 2) Intel 블록의 FC/NETCDF/IOAPI_ROOT/FFLAGS/LIBS 줄을 주석 처리
sed -i '/^#\.\.\.Intel Fortran/,/^DEFS/{/^\(FC\|NETCDF\|IOAPI_ROOT\|FFLAGS\|LIBS\|\t\)/s/^/###/}' Makefile

# 3) Intel 블록 바로 위에 gfortran 설정 삽입
sed -i '/^#\.\.\.Intel Fortran/e cat /tmp/mcip_gfort_block.txt' Makefile

sed -n '/#...gfortran (CMAQ_MODEL/,/^DEFS/p' Makefile
```

정상 결과: 새 gfortran 블록의 `FC = gfortran` 등은 주석 없이, 그 아래 `#...Intel Fortran` 블록의 `FC = ifort` 등은 모두 `###`로 시작한다.

| 설정 | 값 | 이유 |
|---|---|---|
| `FC` | `gfortran` | GNU 기준선(기본계획 §3.4). MCIP는 serial 프로그램이므로 MPI wrapper 불필요 |
| `-I$(IOAPI_BIN)` | `Linux2_x86_64gfort10` | `m3utilio.mod` 위치 |
| `-I$(IOAPI_ROOT)/ioapi/fixed_src` | I/O API 소스 루트 | `*.EXT` 헤더 위치 |
| `-lnetcdff -lnetcdf` | Fortran → C 순서 | netCDF-Fortran이 netCDF-C를 참조 |
| `-fopenmp` | 링크 옵션 | I/O API가 OpenMP 옵션으로 빌드된 경우의 링크 오류 예방. 필요 없을 때도 무해 |

> **참고:** 배포본 예시의 gfortran 항목은 I/O API 헤더 경로를 한 곳만 지정한다. 현재 I/O API 구성(공통 라이브러리 가이드)에서는 `.mod`와 `.EXT`가 서로 다른 폴더에 있으므로 두 경로를 모두 지정한다.

### 7.2 compile

```bash
cd /home/woogon/CMAQ_MODEL/CMAQv5.5/PREP/mcip/src
make clean
set -o pipefail
LC_ALL=C make 2>&1 | tee make_mcip.log
```

### 7.3 compile 결과 확인

```bash
ls -l mcip.exe
grep -n -i -E "Error [0-9]|undefined reference|cannot find|fatal error" make_mcip.log
ldd mcip.exe | grep "not found"
```

정상 결과: `mcip.exe`가 생성되고, 두 번째·세 번째 명령은 아무것도 출력하지 않는다.

컴파일 기록 `make_mcip.log`는 이 폴더에 그대로 둔다.

---

## 8. 환경 설정 요약

### 8.1 `~/.bashrc`에 추가한 내용

없음. 공통 라이브러리·WRF/WPS 단계에서 등록한 설정(`CMAQ_LIBS`, netCDF/HDF5 `LD_LIBRARY_PATH`, OpenMPI module)을 그대로 사용한다.

### 8.2 명령 실행 시에만 붙이는 설정

| 설정 | 적용 명령 | 이유 |
|---|---|---|
| `LC_ALL=C` | `bldit_project.csh`, `config_cmaq.csh`, `make` | 한국어 로케일 출력 파싱 오류 방지 (WRF/WPS 가이드 4.1) |
| `gcc` 인자 | `./config_cmaq.csh gcc` | GNU 컴파일러 항목 선택 |

### 8.3 소스·설정 수정 사항

| 파일 | 조치 | 원본 보관 |
|---|---|---|
| `src/CMAQ_REPO/bldit_project.csh` | `CMAQ_HOME`을 `/home/woogon/CMAQ_MODEL/CMAQv5.5`로 변경 (5.3) | `bldit_project.csh.orig` |
| `CMAQv5.5/config_cmaq.csh` | gcc 항목 라이브러리 경로 10개 지정 (6.2) | `config_cmaq.csh.orig` |
| `CMAQv5.5/PREP/mcip/src/Makefile` | Intel 설정 주석 처리, gfortran 설정 추가 (7.1) | `Makefile.orig` |
| `CMAQv5.5/PREP/mcip/scripts/run_mcip_busan.csh` | 새로 생성 (10.4) | 원본 `run_mcip.csh`는 그대로 둠 |

---

## 9. 완료 현황

| 구성요소 | 버전 | 위치 | 실행파일 | 상태 |
|---|---|---|---|---|
| CMAQ 저장소 | 5.5 (`main`, 커밋 `9bd3734`) | `src/CMAQ_REPO` | - | 내려받기 완료. Phase 6 전 확정 태그 전환 필요(5.2) |
| CMAQ 프로젝트 폴더 | 5.5 | `CMAQv5.5` | - | 생성·`config_cmaq.csh` gcc 설정 완료 |
| MCIP | 5.5 | `CMAQv5.5/PREP/mcip/src` | `mcip.exe` | 컴파일 완료, TEST_20260901 d01~d04 정상 실행·격자 검증 완료 |

Phase 4 MCIP의 설치·실행과 CMAQ 격자 검증은 완료로 기록한다(2026-10-09). 이후 Phase 5 SMOKE 5.3의 **설치·컴파일은 2026-10-10 완료**되었으며, 공식 ExampleCase-v3 실행 검증과 CAPSS·REAS·자연배출량 처리는 미완료다([SMOKE 가이드](../smoke/SMOKE_Installation_Guide.md)). Phase 6 CMAQ CCTM·ICON·BCON 컴파일 및 benchmark도 미완료다.

<a id="case-run"></a>

## 10. 사례 실행: BUSAN / TEST_20260901

### 10.0. 다음 실행 때 따라 할 순서

이 장의 명령은 **Linux Bash 터미널**에서 위에서 아래로 실행한다. 설치를 다시 하는 절차가 아니라 이미 컴파일한 `mcip.exe`로 CASE의 wrfout을 변환하는 절차다.

| 순서 | 작업 | 명령 위치 |
|---|---|---|
| 1 | WRF 정상 종료·wrfout·geo_em 확인 | §10.1 |
| 2 | 격자 값 확인 (도메인이 같으면 계산 생략) | §10.3 |
| 3 | 실행 스크립트 생성 | §10.4 |
| 4 | d01 실행·확인 후 d02~d04 실행 | §10.5 |
| 5 | GRIDDESC·층수·시간 수 확인 | §10.6 |

각 영역의 `NORMAL TERMINATION`을 확인한 뒤 다음 영역으로 간다. 메모리(7.2 GB)를 고려해 **여러 영역을 동시에 실행하지 않는다.**

기존 성공 기록의 재현 절차이며, 아래 스크립트는 같은 영역의 출력을 삭제하고 로그를 덮어쓴다. 실행을 다시 검증할 때는 §10.7의 새 CASE 경로·스크립트 이름을 먼저 적용한다. MCIP 입력은 원본 `TEST_20260901`이고 WRF 재현 검증 CASE `TEST_20260901_REPEAT`와 구분한다. REPEAT를 변환하려면 WRF와 WPS 입력 경로를 모두 해당 CASE로 바꾼다.

### 10.1. 범위와 확인된 입력

2026-10-09 사용자 제공 실제 실행 기록 기준이다. 입력은 `/home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/`의 WRF·WPS 결과다.

```bash
cd /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901

# WRF 정상 종료
grep "SUCCESS COMPLETE WRF" WRF/rsl.error.0000

# 영역별 하루 단위 wrfout (d01~d04 × 3개)
ls -lh WRF/wrfout_d0*

# 네 영역의 마지막 파일에서 최종 시각 확인
for d in d01 d02 d03 d04; do
    ncdump -v Times "WRF/wrfout_${d}_2026-09-02_00:00:00" | tail -n 5
done

# 토지이용 비율 입력용 geo_em (10.2 참고)
ls -lh WPS/geo_em.d0*.nc
```

정상 결과: 영역마다 `wrfout_d0X_2026-08-31_00:00:00`, `2026-09-01_00:00:00`, `2026-09-02_00:00:00` 세 파일이 있다. 마지막 파일은 2026-09-02 00 UTC 한 시각만 담는다. `geo_em.d01.nc`~`geo_em.d04.nc`가 있다.

### 10.2. 그대로 유지할 설정과 사례별 변경값

| 구분 | 현재 기준 | 변경 시 확인 |
|---|---|---|
| CMAQ 격자 | 이전 운영체계 GRIDDESC와 동일 (좌표계 `EASTASIA`, 27KM/09KM/03KM/01KM) | WRF 도메인이 바뀌면 §10.3으로 X0/Y0 재계산 |
| 격자 잘라내기 | `BTRIM=-1` + X0/Y0/NCOLS/NROWS 윈도우 | 사방 대칭 trim(`BTRIM≥0`)으로 바꾸지 않음 |
| 기준위도 | `WRF_LC_REF_LAT=38.0` | GRIDDESC YCENT와 일치 |
| 연직층 | WRF 34층 그대로 | MCIP 5.x는 층 묶기 불가 (10.2 참고) |
| 토지이용 비율 | `IfGeo="T"`, CASE/WPS의 `geo_em.d0X.nc` | wrfout에 `LANDUSEF`가 없으므로 필수 |
| 시작 시각 | WRF 시작 + 1시간 | WRF 첫 시각은 출력 시작으로 쓸 수 없음 |
| 출력 간격 | 60분 | WRF `history_interval`과 일치 |
| 출력 위치 | `CASE/MCIP/<격자명>/` (로그 포함) | 영역별 폴더 분리 유지 |
| 출력 형식 | `IOFORM=1` (I/O API) | CMAQ 입력 형식 |

> **참고: 연직층을 이전 체계처럼 15층으로 묶을 수 없다.** 이전 운영체계 MCIP(3.6)는 `CTMLAYS`로 WRF 층을 15층으로 묶었으나, MCIP의 층 묶기 기능은 2019-06-20 수정에서 삭제되었다(`run_mcip.csh` 수정 이력). 따라서 CMAQ는 WRF의 34층을 그대로 사용한다. 층 수를 줄이려면 WRF의 `e_vert`·`eta_levels`부터 바꿔 다시 실행해야 한다.

> **참고: 결과를 격자별 폴더에 나누는 이유** MCIP는 출력 폴더를 작업 폴더로도 사용해 `namelist.mcip`와 `fort.*` 링크를 만들고 실행 전에 지운다. 여러 영역이 한 폴더를 쓰면 설정이 서로 덮어써질 수 있다. 향후 CMAQ 다중 영역 실행에서 영역별 폴더가 이후 CCTM 입력 지정에도 맞다.

### 10.3. CMAQ 격자 결정

CMAQ 격자는 이전 운영체계의 GRIDDESC와 완전히 같게 맞춘다. WRF 도메인이 이전 체계와 같으므로, WRF 격자에서 이전 격자 위치를 그대로 잘라낸다.

기준 격자(이전 운영체계 GRIDDESC). 네 영역 모두 좌표계 `EASTASIA`: Lambert Conformal(`GDTYP=2`), 표준위도 30°/60°N, 중심경도 126°E, 기준위도 38°N이다.

| 격자 | XORIG (m) | YORIG (m) | 격자 크기 (m) | NCOLS × NROWS |
|---|---|---|---|---|
| 27KM | -2349000 | -1728000 | 27000 | 174 × 128 |
| 09KM | -180000 | -585000 | 9000 | 67 × 82 |
| 03KM | 105000 | -408000 | 3000 | 83 × 83 |
| 01KM | 231000 | -332000 | 1000 | 78 × 70 |

WRF 도메인(CASE `namelist.wps`):

| 영역 | parent_grid_ratio | i_parent_start | j_parent_start | e_we | e_sn | 셀 수 |
|---|---|---|---|---|---|---|
| d01 | 1 | 1 | 1 | 177 | 131 | 176 × 130 |
| d02 | 3 | 80 | 42 | 82 | 97 | 81 × 96 |
| d03 | 3 | 39 | 27 | 88 | 88 | 87 × 87 |
| d04 | 3 | 44 | 28 | 85 | 76 | 84 × 75 |

`ref_lat=38.0`, `ref_lon=stand_lon=126.0`, `truelat1/2=30/60`, d01 `dx=27000`으로 이전 체계 좌표계와 같다.

계산 방법:

MCIP는 잘라낸 영역 바깥에 경계 1칸(`NTHIK=1`)을 두므로 다음 관계가 성립한다.

```text
XORIG = (WRF 영역 왼쪽 아래 꼭짓점 x) + X0 × dx
YORIG = (WRF 영역 왼쪽 아래 꼭짓점 y) + Y0 × dy
```

1. d01은 기준점(126°E, 38°N)이 영역 중앙이므로 꼭짓점은 x = −176/2 × 27000 = −2376000 m, y = −130/2 × 27000 = −1755000 m이다.
2. 안쪽 영역의 꼭짓점 = 부모 꼭짓점 + (parent_start − 1) × 부모 격자 크기.
3. X0 = (XORIG − 꼭짓점 x) / dx, Y0 = (YORIG − 꼭짓점 y) / dy.
4. X0 + NCOLS + 1 ≤ WRF 셀 수, Y0 + NROWS + 1 ≤ WRF 셀 수인지 확인한다(잘라낸 범위가 WRF 영역 안에 있는지).

| 영역 | WRF 꼭짓점 x (m) | WRF 꼭짓점 y (m) | X0 | Y0 | NCOLS | NROWS | 격자명 |
|---|---|---|---|---|---|---|---|
| d01 | -2376000 | -1755000 | 1 | 1 | 174 | 128 | 27KM |
| d02 | -243000 | -648000 | 7 | 7 | 67 | 82 | 09KM |
| d03 | 99000 | -414000 | 2 | 2 | 83 | 83 | 03KM |
| d04 | 228000 | -333000 | 3 | 1 | 78 | 70 | 01KM |

네 영역 모두 X0/Y0가 정수로 나왔고, d04 값(3, 1)은 이전 운영체계 1km MCIP 스크립트의 값과 일치한다. d01은 경계 1칸씩을 더하면 WRF 셀 전체(176 × 130)를 채우므로 `BTRIM=0`과 같은 범위다.

> **참고:** 결과가 정수로 나오지 않으면 WRF 도메인이 기준 격자와 맞지 않는 것이다. 이때는 MCIP를 실행하지 말고 `namelist.wps`의 도메인 값을 먼저 확인한다.

### 10.4. 실행 스크립트 생성

CMAQ 5.5의 `PREP/mcip/scripts/run_mcip.csh`를 바탕으로, 영역 인자(d01~d04) 하나로 네 영역을 실행하는 `run_mcip_busan.csh`를 만든다. 사례별로 바꾸는 값은 위쪽 "Case settings"에 모았다.

| 설정 | 값 | 이유 |
|---|---|---|
| `MCIP_START` | `2026-08-31-01:00:00.0000` | WRF 시작(00 UTC) 1시간 뒤부터 출력 가능 (부록 A1) |
| `MCIP_END` / `INTVL` | `2026-09-02-00:00:00.0000` / 60 | 출력 48시간 |
| `BTRIM` | -1 | §10.3 윈도우 사용 |
| `IfGeo` | `"T"` | wrfout에 `LANDUSEF` 없음 (부록 A2) |
| `WRF_LC_REF_LAT` | 38.0 | 이전 체계 GRIDDESC 기준위도 |
| `CoordName` | `EASTASIA` | 이전 체계 좌표계 이름 |
| `LUVBOUT` | 1 | 배포본 기본값 유지 (B격자 바람 추가 출력) |
| `IOFORM` | 1 | I/O API 형식 |
| 로그 | `MCIP/<격자명>/mcip_<영역>.log` | 스크립트가 자동 기록 |

아래 명령을 그대로 붙여넣어 스크립트를 생성한다.

```bash
cd /home/woogon/CMAQ_MODEL/CMAQv5.5/PREP/mcip/scripts

cat > run_mcip_busan.csh << 'EOF'
#!/bin/csh -f
#=======================================================================
#  run_mcip_busan.csh
#  MCIP (CMAQ v5.5) run script for BUSAN 4-nest system (27/9/3/1 km)
#
#  Usage :  ./run_mcip_busan.csh d01
#           (d01=27KM, d02=09KM, d03=03KM, d04=01KM)
#           Log is written automatically to MCIP/<GRID>/mcip_<dom>.log
#
#  Grid  :  Same CMAQ grids as the previous operational system
#           (coord. EASTASIA, LCC 30/60N, 126E, ref.lat 38N).
#           X0/Y0/NCOLS/NROWS reproduce the old GRIDDESC_27KM/09KM/03KM/01KM.
#  Layers:  MCIP v5.x removed layer collapsing (20 Jun 2019),
#           so all WRF layers are passed to CMAQ.
#  Based on CMAQv5.5/PREP/mcip/scripts/run_mcip.csh
#=======================================================================

set nonomatch

#-----------------------------------------------------------------------
# Case settings (edit here for a new case)
#-----------------------------------------------------------------------
set ROOT       = /home/woogon/CMAQ_MODEL
set CASE_DIR   = $ROOT/CASES/BUSAN/TEST_20260901
set InMetDir   = $CASE_DIR/WRF
set InGeoDir   = $CASE_DIR/WPS
set ProgDir    = $ROOT/CMAQv5.5/PREP/mcip/src

set MCIP_START = 2026-08-31-01:00:00.0000  # [UTC] must be after WRF start (00Z)
set MCIP_END   = 2026-09-02-00:00:00.0000  # [UTC]
set INTVL      = 60                        # [min]
set DATE_TAG   = 2026083100                # tag for output file names
set MetDates   = ( 2026-08-31 2026-09-01 2026-09-02 )   # wrfout daily files

#-----------------------------------------------------------------------
# Domain settings (window values derived from old GRIDDESC + namelist.wps)
#-----------------------------------------------------------------------
if ( $#argv != 1 ) then
  echo "Usage: $0 d01|d02|d03|d04"
  exit 1
endif
set DOM = $argv[1]

switch ( $DOM )
  case d01:
    set GridName = 27KM
    set X0 = 1 ; set Y0 = 1 ; set NCOLS = 174 ; set NROWS = 128
    breaksw
  case d02:
    set GridName = 09KM
    set X0 = 7 ; set Y0 = 7 ; set NCOLS = 67  ; set NROWS = 82
    breaksw
  case d03:
    set GridName = 03KM
    set X0 = 2 ; set Y0 = 2 ; set NCOLS = 83  ; set NROWS = 83
    breaksw
  case d04:
    set GridName = 01KM
    set X0 = 3 ; set Y0 = 1 ; set NCOLS = 78  ; set NROWS = 70
    breaksw
  default:
    echo "Unknown domain: $DOM  (use d01, d02, d03 or d04)"
    exit 1
endsw

set CoordName  = EASTASIA         # 16-character maximum
set APPL       = ${GridName}.${DATE_TAG}
set OutDir     = $CASE_DIR/MCIP/$GridName
set WorkDir    = $OutDir

#-----------------------------------------------------------------------
# Re-run this script with its output going to the log file in OutDir
#-----------------------------------------------------------------------
if ( ! $?MCIP_LOGGING ) then
  setenv MCIP_LOGGING 1
  mkdir -p $OutDir
  set LogFile = $OutDir/mcip_${DOM}.log
  echo "MCIP $DOM ($GridName) running ... log: $LogFile"
  $0 $DOM >& $LogFile
  set rc = $status
  tail -n 3 $LogFile
  exit $rc
endif

set InMetFiles = ( )
foreach d ( $MetDates )
  set InMetFiles = ( $InMetFiles $InMetDir/wrfout_${DOM}_${d}_00:00:00 )
end

# LANDUSEF is not in wrfout -> read fractional land use from geo_em
set IfGeo      = "T"
set InGeoFile  = $InGeoDir/geo_em.${DOM}.nc

#-----------------------------------------------------------------------
# User control options
#-----------------------------------------------------------------------
set LPV     = 0
set LWOUT   = 0
set LUVBOUT = 1
set IOFORM  = 1            # 1 = Models-3 I/O API
set BTRIM   = -1           # -1 = use window (X0, Y0, NCOLS, NROWS)
set LPRT_COL = 0
set LPRT_ROW = 0
set WRF_LC_REF_LAT = 38.0  # same as old system (GRIDDESC YCENT = 38)

#=======================================================================
# Set up and run MCIP.  Should not need to change anything below here.
#=======================================================================

set PROG = mcip

echo "=== MCIP $DOM ($GridName)  X0=$X0 Y0=$Y0 NCOLS=$NCOLS NROWS=$NROWS"
date

if ( ! -d $InMetDir ) then
  echo "No such input directory $InMetDir"
  exit 1
endif

if ( ! -d $ProgDir ) then
  echo "No such program directory $ProgDir"
  exit 1
endif

if ( $IfGeo == "T" ) then
  if ( ! -f $InGeoFile ) then
    echo "No such input file $InGeoFile"
    exit 1
  endif
endif

foreach fil ( $InMetFiles )
  if ( ! -f $fil ) then
    echo "No such input file $fil"
    exit 1
  endif
end

if ( ! -f $ProgDir/${PROG}.exe ) then
  echo "Could not find ${PROG}.exe"
  exit 1
endif

if ( ! -d $WorkDir ) then
  mkdir -p $WorkDir
  if ( $status != 0 ) then
    echo "Failed to make work directory, $WorkDir"
    exit 1
  endif
endif

cd $WorkDir

if ( $IfGeo == "T" ) then
  set InGeo = $InGeoFile
else
  set InGeo = "no_file"
endif

set FILE_GD  = $OutDir/GRIDDESC_${GridName}

#-----------------------------------------------------------------------
# Create namelist with user definitions.
#-----------------------------------------------------------------------

set Marker = "&END"

cat > $WorkDir/namelist.${PROG} << !

 &FILENAMES
  file_gd    = "$FILE_GD"
  file_mm    = "$InMetFiles[1]",
!

if ( $#InMetFiles > 1 ) then
  @ nn = 2
  while ( $nn <= $#InMetFiles )
    cat >> $WorkDir/namelist.${PROG} << !
               "$InMetFiles[$nn]",
!
    @ nn ++
  end
endif

if ( $IfGeo == "T" ) then
cat >> $WorkDir/namelist.${PROG} << !
  file_geo   = "$InGeo"
!
endif

cat >> $WorkDir/namelist.${PROG} << !
  ioform     =  $IOFORM
 $Marker

 &USERDEFS
  lpv        =  $LPV
  lwout      =  $LWOUT
  luvbout    =  $LUVBOUT
  mcip_start = "$MCIP_START"
  mcip_end   = "$MCIP_END"
  intvl      =  $INTVL
  coordnam   = "$CoordName"
  grdnam     = "$GridName"
  btrim      =  $BTRIM
  lprt_col   =  $LPRT_COL
  lprt_row   =  $LPRT_ROW
  wrf_lc_ref_lat = $WRF_LC_REF_LAT
 $Marker

 &WINDOWDEFS
  x0         =  $X0
  y0         =  $Y0
  ncolsin    =  $NCOLS
  nrowsin    =  $NROWS
 $Marker

!

#-----------------------------------------------------------------------
# Set links to FORTRAN units.
#-----------------------------------------------------------------------

rm -f fort.*
if ( -f $FILE_GD ) rm -f $FILE_GD

ln -s $FILE_GD                   fort.4
ln -s $WorkDir/namelist.${PROG}  fort.8

set NUMFIL = 0
foreach fil ( $InMetFiles )
  @ NN = $NUMFIL + 10
  ln -s $fil fort.$NN
  @ NUMFIL ++
end

#-----------------------------------------------------------------------
# Output file names
#-----------------------------------------------------------------------

setenv IOAPI_CHECK_HEADERS  T
setenv EXECUTION_ID         $PROG

setenv GRID_BDY_2D          $OutDir/GRIDBDY2D_${APPL}.nc
setenv GRID_CRO_2D          $OutDir/GRIDCRO2D_${APPL}.nc
setenv GRID_DOT_2D          $OutDir/GRIDDOT2D_${APPL}.nc
setenv MET_BDY_3D           $OutDir/METBDY3D_${APPL}.nc
setenv MET_CRO_2D           $OutDir/METCRO2D_${APPL}.nc
setenv MET_CRO_3D           $OutDir/METCRO3D_${APPL}.nc
setenv MET_DOT_3D           $OutDir/METDOT3D_${APPL}.nc
setenv LUFRAC_CRO           $OutDir/LUFRAC_CRO_${APPL}.nc
setenv SOI_CRO              $OutDir/SOI_CRO_${APPL}.nc
setenv MOSAIC_CRO           $OutDir/MOSAIC_CRO_${APPL}.nc

foreach f ( $GRID_BDY_2D $GRID_CRO_2D $GRID_DOT_2D $MET_BDY_3D \
            $MET_CRO_2D $MET_CRO_3D $MET_DOT_3D $LUFRAC_CRO \
            $SOI_CRO $MOSAIC_CRO $OutDir/mcip.nc $OutDir/mcip_bdy.nc )
  if ( -f $f ) rm -f $f
end

#-----------------------------------------------------------------------
# Execute MCIP.
#-----------------------------------------------------------------------

$ProgDir/${PROG}.exe

if ( $status == 0 ) then
  rm -f fort.*
  echo "=== MCIP $DOM ($GridName) finished normally"
  date
  exit 0
else
  echo "Error running $PROG"
  exit 1
endif
EOF

chmod +x run_mcip_busan.csh
tcsh -n run_mcip_busan.csh && echo "syntax OK"
```

정상 결과: `syntax OK`

> **참고:** 스크립트를 Windows에서 작성해 SFTP로 옮긴 경우에는 `sed -i 's/\r$//' run_mcip_busan.csh`를 먼저 실행한다(4장).

### 10.5. 실행

```bash
cd /home/woogon/CMAQ_MODEL/CMAQv5.5/PREP/mcip/scripts

# 가장 큰 d01로 먼저 확인
./run_mcip_busan.csh d01
```

정상 결과(화면):

```text
MCIP d01 (27KM) running ... log: /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/MCIP/27KM/mcip_d01.log
NORMAL TERMINATION
=== MCIP d01 (27KM) finished normally
```

d01이 정상 종료되면 나머지 영역을 순서대로 실행한다.

```bash
cd /home/woogon/CMAQ_MODEL/CMAQv5.5/PREP/mcip/scripts
for d in d02 d03 d04; do
    ./run_mcip_busan.csh "$d" || break
    g=09KM; [ "$d" = d03 ] && g=03KM; [ "$d" = d04 ] && g=01KM
    grep -q "NORMAL TERMINATION" "/home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/MCIP/$g/mcip_${d}.log" || break
done
```

> **참고:** 스크립트는 자기 자신을 다시 호출해 출력 전체를 `MCIP/<격자명>/mcip_<영역>.log`에 기록하고, 화면에는 마지막 3줄만 보여준다. 따로 `>&`나 `tee`를 붙이지 않는다. 다시 실행하면 같은 영역의 이전 출력파일과 로그를 덮어쓴다. 기존 성공 사례에 재실행하지 말고 §10.7에 따라 새 CASE를 만든다. 같은 CASE의 재실행이 꼭 필요하면 먼저 영역 폴더 전체를 고유한 보존 경로에 복사하고 사본 확인 후 진행한다.

### 10.6. 결과 확인

```bash
cd /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/MCIP

# 1) 정상 종료
grep -H "NORMAL TERMINATION" */mcip_d0*.log

# 2) 격자: 이전 GRIDDESC와 비교
grep "EASTASIA'  " */GRIDDESC_*

# 3) 층 수·크기·시간 수
for g in 27KM 09KM 03KM 01KM; do
    echo "== $g"
    ncdump -h $g/METCRO3D_$g.2026083100.nc | grep -E "LAY =|ROW =|COL =|TSTEP ="
done

# 4) 토지이용 비율 입력 확인
grep -H "FRACTIONAL LAND USE will be read from the GEO file" */mcip_d0*.log

# 5) 경고 수 (영역마다 4개라는 제공 기록과 비교; 개수만으로 품질 판정하지 않음)
grep -c -i warning */mcip_d0*.log
grep -h -i warning */mcip_d0*.log | grep -v "Vertical grid"
```

제공 문서에 기록된 결과(이번 검토에서 원본 netCDF 직접 확인은 미수행):

| 격자 | XORIG / YORIG (m) | NCOLS × NROWS | LAY | TSTEP | 이전 GRIDDESC |
|---|---|---|---|---|---|
| 27KM | -2349000 / -1728000 | 174 × 128 | 34 | 48 | 동일 |
| 09KM | -180000 / -585000 | 67 × 82 | 34 | 48 | 동일 |
| 03KM | 105000 / -408000 | 83 × 83 | 34 | 48 | 동일 |
| 01KM | 231000 / -332000 | 78 × 70 | 34 | 48 | 동일 |

- 1)은 네 줄, 4)는 네 줄이 출력된다.
- 5)의 마지막 명령은 아무것도 출력하지 않는다.
- 로그의 창 위치 `Window domain origin on met domain (col,row)`가 영역별 X0, Y0(1,1 / 7,7 / 2,2 / 3,1)와 같다.
- `LUFRAC_CRO`는 21층(MODIS 21 category)이다.

영역별 생성 파일(27KM 예):

```text
MCIP/27KM/
├── GRIDDESC_27KM
├── GRIDBDY2D_27KM.2026083100.nc   GRIDCRO2D_27KM.2026083100.nc   GRIDDOT2D_27KM.2026083100.nc
├── METBDY3D_27KM.2026083100.nc    METCRO2D_27KM.2026083100.nc
├── METCRO3D_27KM.2026083100.nc    METDOT3D_27KM.2026083100.nc
├── LUFRAC_CRO_27KM.2026083100.nc  SOI_CRO_27KM.2026083100.nc     MOSAIC_CRO_27KM.2026083100.nc
├── namelist.mcip
└── mcip_d01.log
```

파일명의 `2026083100`은 CASE 시작 시각 태그이며, 실제 첫 출력 시각은 2026-08-31 01 UTC이다.

> **참고: 경고의 범위와 후속 검증을 구분한다.** 로그에 `WARNING: Vertical grid/coordinate type: -9999 "MISSING"`이 영역마다 4번(LUFRAC_CRO, MET_CRO_3D, MET_BDY_3D, MET_DOT_3D) 나온다. WRF가 하이브리드 연직좌표를 사용했고(로그: `HYBRID VERTICAL COORDINATE was used`), I/O API에 이 좌표 유형 번호가 없어 MCIP가 `VGTYP=-9999`로 기록한 것이다. 이 제공 기록에서 MCIP 정상 종료와 함께 나타난 경고이다. 경고 개수만으로 입력 품질·CCTM 호환성을 판정하지 않는다. Phase 6에서 해당 기상파일 읽기, 수직좌표와 층 수, 배출량·IC/BC 정합성을 확인한다.

#### 10.6.1. 이번 CASE의 완료 판정

사용자 제공 기록에 따르면 `TEST_20260901`의 d01~d04 MCIP 로그에서 모두 `NORMAL TERMINATION`을 확인했다. 생성된 GRIDDESC 4개의 원점·격자 크기·셀 수가 이전 운영체계 GRIDDESC와 일치했다. 4km 미만 격자(03KM, 01KM)의 원점도 이전 값과 같았다. 이 근거로 Phase 4의 MCIP 정상 변환·수평 격자 확인 완료를 기록한다. 실제 출력의 `TFLAG`·결측값·물리량 QA와 CCTM 입력 검증은 미완료이다.

### 10.7. 새 CASE에 적용

도메인이 같고 기간만 다른 CASE는 스크립트를 복사한 뒤 "Case settings"의 다섯 줄만 바꾼다.

```bash
cd /home/woogon/CMAQ_MODEL/CMAQv5.5/PREP/mcip/scripts
NEW_CASE=TEST_20261001   # 실제 새 사례명으로 수정
cp -n run_mcip_busan.csh "run_mcip_${NEW_CASE}.csh"
```

| 변수 | 의미 | 예 (2026-10-01 00 UTC ~ 10-03 00 UTC) |
|---|---|---|
| `CASE_DIR` | CASE 폴더 | `$ROOT/CASES/BUSAN/<CASE명>` |
| `MCIP_START` | WRF 시작 + 1시간 | `2026-10-01-01:00:00.0000` |
| `MCIP_END` | WRF 종료 시각 | `2026-10-03-00:00:00.0000` |
| `DATE_TAG` | 출력파일명 태그(WRF 시작) | `2026100100` |
| `MetDates` | wrfout 파일 날짜 전체 | `( 2026-10-01 2026-10-02 2026-10-03 )` |

실행과 확인은 §10.5~10.6과 같다. `MetDates`는 `MCIP_END`를 담은 마지막 wrfout 파일까지 포함해야 한다.

WRF 도메인(`e_we`, `e_sn`, `i_parent_start`, `j_parent_start`, `dx`, `ref_lat/lon`, `truelat1/2`)이 바뀌면 §10.3 방법으로 X0/Y0/NCOLS/NROWS를 다시 계산하고 스크립트의 `switch` 블록을 고친다.

### 10.8. 재현에 필요한 보존 자료

`config_cmaq.csh`와 `.orig`, MCIP `Makefile`과 `.orig`, `make_mcip.log`, `run_mcip_busan.csh`, CASE `namelist.wps`, 이전 운영체계 GRIDDESC 4개, 영역별 `namelist.mcip`·`mcip_d0X.log`·`GRIDDESC_*`를 보존한다. 원본 WRF/WPS 입력, 전체 CMAQ commit SHA, `git status --short`·`git diff`, 라이브러리 버전, 입력·실행파일·출력의 `sha256sum` 및 실제 출력 `TFLAG`도 기록한다. 이는 앞으로 보완할 보존 항목이며 현재 모두 확보됐다는 뜻은 아니다. 이 문서 §6.2, §7.1, §10.4에 수정·생성 명령 전문을 반영했다.

---

## 부록 A. 구축 중 발생한 문제 기록

이 문서의 절차는 아래 문제들을 해결한 결과다. 같은 증상을 만났을 때 원인을 찾는 용도로 남긴다.

| 번호 | 단계 | 증상 | 원인 | 예방 조치 |
|---|---|---|---|---|
| A1 | MCIP 실행 | `MCIP output must start after meteorology start time` 후 `ERROR ABORT in subroutine SETGRIDDEFS` | `MCIP_START`를 WRF 첫 시각(00 UTC)과 같게 지정. 첫 시각은 초기값이라 누적량 차이를 계산할 수 없음 | 10.4 `MCIP_START` = WRF 시작 + 1시간 |
| A2 | MCIP 실행 | `DID NOT FIND FRACTIONAL LAND USE IN wrfout AND DID NOT FIND GEOGRID FILE` | wrfout에 `LANDUSEF` 없음, `IfGeo="F"` | 10.4 `IfGeo="T"`, CASE/WPS `geo_em` 사용 |
| A3 | MCIP 설정 | 이전 체계 `CTMLAYS`(15층 묶기) 지정 항목 없음 | MCIP 2019-06-20 수정에서 층 묶기 삭제 | 10.2 WRF 34층 사용 |
| A4 | MCIP 설정 | 이전 체계 스크립트의 `LDDEP`, `LUVCOUT`, `IfTer` 항목 없음 | MCIP 3.6 형식. 현재는 `LUVBOUT`, `IfGeo`, `IOFORM` 사용 | 10.4 MCIP 5.5 원본 스크립트 기반으로 작성 |
| A5 | MCIP compile | 배포본 Makefile이 `ifort`로 설정됨 | 배포본 기본값이 Intel | 7.1 gfortran 설정 |
| A6 | config_cmaq.csh | 경로를 고쳐 다시 실행해도 링크가 바뀌지 않음 | `lib/` 아래 링크가 이미 있으면 다시 만들지 않음 | 6.3 링크 확인·lib 보존 이동 후 재실행 |
| A7 | 전반 | Windows에서 옮긴 파일 실행 오류 | CRLF 줄바꿈 | 4장 `sed -i 's/\r$//'` |

진단에 사용한 명령:

```bash
# A1: WRF 첫 시각과 MCIP 시작 시각 비교
ncdump -v Times /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/WRF/wrfout_d01_2026-08-31_00:00:00 | grep -A2 "Times ="
grep -n -A3 "SETGRIDDEFS" /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/MCIP/27KM/mcip_d01.log

# A2: wrfout에 LANDUSEF가 있는지 확인
ncdump -h /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/WRF/wrfout_d01_2026-08-31_00:00:00 | grep -c LANDUSEF

# A3: 층 묶기 삭제 이력 확인
grep -n -A2 "Removed layer collapsing" /home/woogon/CMAQ_MODEL/CMAQv5.5/PREP/mcip/scripts/run_mcip.csh

# A6: 링크 대상 확인
ls -l /home/woogon/CMAQ_MODEL/CMAQv5.5/lib/x86_64/gcc/*
```

구축 경위:

- CMAQ 프로젝트 폴더 이름을 처음에는 `CMAQ_v5.5`로 안내했으나, 기존 버전명 폴더 규칙에 맞춰 `CMAQv5.5`로 확정했다.
- 처음에는 MCIP 로그를 CASE의 `LOG/`에 저장했으나, 결과와 함께 관리하도록 `MCIP/<격자명>/`에 저장하는 방식으로 바꾸고 스크립트가 자동 기록하게 했다. 실패한 첫 실행 로그(`LOG/mcip_d01.log`)도 오류 이력으로 보존한다.
- 이전 운영체계 1km 스크립트(`eni_mcip_wrf_run.csh`, MCIP 3.6)의 윈도우 방식과 GRIDDESC 4개, CASE `namelist.wps`로 §10.3의 X0/Y0를 계산했다. d04 계산값이 이전 스크립트 값과 일치해 방법을 검증했다.
- CMAQ 저장소는 `main` 커밋 `9bd3734`로 내려받았다는 제공 기록이다. 공식 `PREP/mcip` 소스 동일성은 확인했다. CCTM 전에 별도 태그 소스·프로젝트를 준비하는 작업은 아직 수행되지 않았다(5.2).

## 11. 검토 근거 및 관련 문서

공식 소스 비교(2026-10-09): `9bd3734`, 5.5.0.3, 5.5.0.4의 `PREP` tree 동일성은 GitHub API로 확인했다. 서버의 해당 커밋 사용·로컬 수정 및 실행 결과는 제공 문서에 근거한다.

- [CMAQ GitHub 저장소](https://github.com/USEPA/CMAQ)
- [CMAQv5.5.0.3_11Jul2025 태그](https://github.com/USEPA/CMAQ/releases/tag/CMAQv5.5.0.3_11Jul2025)
- [CMAQ User's Guide: Preparing to run (MCIP 포함)](https://github.com/USEPA/CMAQ/blob/main/DOCS/Users_Guide/CMAQ_UG_ch04_model_inputs.md)
- [CMAQ User's Guide: Running a simulation](https://github.com/USEPA/CMAQ/blob/main/DOCS/Users_Guide/CMAQ_UG_ch05_running_a_simulation.md)
- CMAQ 5.5 `PREP/mcip/scripts/run_mcip.csh`(BTRIM·윈도우·IfGeo 설명, 2019-06-20 층 묶기 삭제 이력), `PREP/mcip/src/Makefile`(컴파일러별 예시), `config_cmaq.csh`(gcc 항목, 라이브러리 존재 검사)
- [구축 기본계획 및 Phase 현황](../planning/00_CMAQ_Project_Master_Plan.md) §3.5, §9, §22 Phase 4
- [WRF/WPS 설치 가이드](../wrf/WRF_WPS_Installation_Guide.md)
- [공통 라이브러리 구축 기록](../libraries/Common_Libraries_Installation_Guide.md)
- [GNU Compiler 및 OpenMPI 설치 가이드](../compiler/GNU_Compiler_OpenMPI_Installation_Guide.md)
