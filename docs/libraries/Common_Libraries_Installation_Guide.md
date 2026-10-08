# CMAQ 모델링 시스템 공통 라이브러리 구축 기록

**새 시스템에서 시작할 때는 [사전 준비와 소스 다운로드](#library-start)를 먼저 실행한 뒤 §3~9를 순서대로 따른다.**

## 1. 목적
Rocky Linux 기반 CMAQ 통합 대기질 모델링 시스템 구축 과정에서 CMAQ 계열 모델 빌드에 필요한 공통 라이브러리(zlib, HDF5, netCDF, I/O API) 설치 절차를 재현할 수 있도록 기록한다.

설치 순서:

```text
zlib 확인
  ↓
HDF5 1.14.6
  ↓
netCDF-C 4.9.3
  ↓
netCDF-Fortran 4.6.2
  ↓
I/O API 3.2-20200828
```

## 2. 구축 환경

- OS: Rocky Linux 9.8 (Blue Onyx), x86_64
- 사용자: `woogon`
- 프로젝트 루트: `/home/woogon/CMAQ_MODEL`
- GCC: 11.5.0 (`/usr/bin/gcc`)
- GFortran: 11.5.0 (`/usr/bin/gfortran`)
- GNU Make 설치 완료
- OpenMPI 설치 및 동작 확인
- CPU 코어 확인: `nproc` → 4

현재 구축 디렉터리의 최소 구조(2026-10-03):

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

위 구조는 공통 라이브러리 구축 단계의 경로만 표시한다. 현재 모델 본체·DATA·CASES·SCRIPTS를 포함한 전체 구조는 [기본계획 §4.2](../planning/00_CMAQ_Project_Master_Plan.md)를 따른다. 이 문서의 `logs/ioapi`는 라이브러리 빌드 로그 보관 경로이며 CASE의 `LOG` 및 `WRF/rsl.*`와 용도가 다르다.

`src/`는 원본 소스·압축파일 및 라이브러리 빌드용 소스 보관용이다. 아래 HDF5/netCDF 빌드에 사용한 소스 디렉터리 등은 최소 구조에서 생략했다. 실제 컴파일된 모델 본체는 프로젝트 루트의 버전별 폴더에 둔다.

HDF5와 netCDF는 소스와 설치 결과를 분리하고 라이브러리 디렉터리명에는 정확한 버전을 표시한다. I/O API는 7.1절과 같이 `libs/` 아래에서 직접 빌드했다.

Compiler/MPI 설치 및 검증은 [GNU Compiler 및 OpenMPI 설치 가이드](../compiler/GNU_Compiler_OpenMPI_Installation_Guide.md)를 참고한다.

---

<a id="library-start"></a>

## 2.1 재구축 순서와 실행 규칙

아래 명령은 Linux Bash, 일반 사용자 woogon 기준이다. 시스템 패키지 설치만 sudo로 수행한다. 기존 성공 설치를 재빌드할 필요는 없다. 새 시스템에서 빠졌던 다운로드·폴더 준비 명령은 공식 버전별 소스를 확인해 보완했다(2026-10-08). 과거 대화에서 실제 실행된 것으로 확인한 명령·결과와 이 보완 명령을 구분한다.

| 순서 | 작업 | 위치 |
|---|---|---|
| 1 | GNU Compiler/OpenMPI 설치·테스트 | Compiler/MPI 가이드 |
| 2 | 사전 패키지·폴더·소스 준비 | §2.2~2.3 |
| 3 | zlib 확인 | §3 |
| 4 | HDF5 configure → make → check → install | §4 |
| 5 | netCDF-C configure → make → check → install | §5 |
| 6 | netCDF-Fortran configure → make → check → install | §6 |
| 7 | I/O API 태그 → Makefile → 빌드 → 실행 테스트 | §7 |
| 8 | .bashrc 등록·최종 확인 | §8~9 |

명령 실행 후 성공 여부를 확인하고 다음 단계로 간다. echo $?는 확인할 명령 직후에 실행해야 한다. 이전 단계 실패를 무시하고 make install로 넘어가지 않는다. 기존 src 소스가 있으면 압축을 다시 풀어 덮어쓰지 않는다.

## 2.2 사전 패키지와 폴더 생성

Compiler/MPI 가이드의 gcc/g++/gfortran/make 설치가 먼저 완료되어 있어야 한다.

```bash
sudo dnf install -y wget git tar gzip autoconf automake libtool zlib-devel libxml2-devel
mkdir -p /home/woogon/CMAQ_MODEL/src
mkdir -p /home/woogon/CMAQ_MODEL/libs
mkdir -p /home/woogon/CMAQ_MODEL/logs/ioapi
gcc --version
gfortran --version
make --version
rpm -q zlib zlib-devel libxml2-devel
export CC=gcc
export CXX=g++
export FC=gfortran
# 새 shell에서 빌드용 옵션을 초기화한다.
unset CPPFLAGS LDFLAGS LIBS
```

zlib-devel은 시스템 zlib header를 제공한다. libxml2-devel은 §5.4에서 실제로 필요했던 패키지이므로 새 시스템에서는 미리 설치한다.

## 2.3 버전을 고정한 소스 다운로드와 압축 해제

아래는 공식 HDF5 1.14.6 릴리스와 Unidata의 netCDF-C v4.9.3 / netCDF-Fortran v4.6.2 태그를 사용한다. 최신 버전을 자동 선택하지 않는다. netCDF 태그 소스에 configure가 포함되어 있는 것을 확인했다. 이 URL들은 재구축용으로 보완한 경로이며 과거에 사용한 다운로드 URL이라고 단정하지 않는다.

**HDF5 1.14.6:**

```bash
cd /home/woogon/CMAQ_MODEL/src
wget -O hdf5-1.14.6.tar.gz https://github.com/HDFGroup/hdf5/releases/download/hdf5_1.14.6/hdf5-1.14.6.tar.gz
tar -tzf hdf5-1.14.6.tar.gz | head
tar -xzf hdf5-1.14.6.tar.gz
ls -l /home/woogon/CMAQ_MODEL/src/hdf5-1.14.6/configure
```

**netCDF-C 4.9.3:**

```bash
cd /home/woogon/CMAQ_MODEL/src
wget -O netcdf-c-4.9.3.tar.gz https://github.com/Unidata/netcdf-c/archive/refs/tags/v4.9.3.tar.gz
tar -tzf netcdf-c-4.9.3.tar.gz | head
tar -xzf netcdf-c-4.9.3.tar.gz
ls -l /home/woogon/CMAQ_MODEL/src/netcdf-c-4.9.3/configure
```

**netCDF-Fortran 4.6.2:**

```bash
cd /home/woogon/CMAQ_MODEL/src
wget -O netcdf-fortran-4.6.2.tar.gz https://github.com/Unidata/netcdf-fortran/archive/refs/tags/v4.6.2.tar.gz
tar -tzf netcdf-fortran-4.6.2.tar.gz | head
tar -xzf netcdf-fortran-4.6.2.tar.gz
ls -l /home/woogon/CMAQ_MODEL/src/netcdf-fortran-4.6.2/configure
sha256sum hdf5-1.14.6.tar.gz netcdf-c-4.9.3.tar.gz netcdf-fortran-4.6.2.tar.gz > source_sha256.txt
cat source_sha256.txt
```

wgetが失敗した場合やtarで読めない場合は続行しない。configureが各所に存在することを確認し、§3→4→5→6の順でビルドする。sha256sumは取得した原本の記録であり、公表済みチェックサムとの照合を代わりに行うものではない。

公式ソース: [HDF5 1.14.6](https://github.com/HDFGroup/hdf5/releases/tag/hdf5_1.14.6)、[netCDF-C v4.9.3](https://github.com/Unidata/netcdf-c/releases/tag/v4.9.3)、[netCDF-Fortran v4.6.2](https://github.com/Unidata/netcdf-fortran/releases/tag/v4.6.2)。

## 3. zlib 확인

Rocky Linux에 설치된 시스템 zlib을 사용했다. 별도 소스 컴파일은 하지 않았다.

### 3.1 패키지 확인

```bash
rpm -qa | grep '^zlib'
```

확인된 패키지:

```text
zlib-1.2.11-40.el9.x86_64
zlib-devel-1.2.11-40.el9.x86_64
```

따라서 HDF5 빌드에는 Rocky Linux 시스템 zlib을 사용했다.

**상태: 확인 완료**

---

## 4. HDF5 1.14.6 설치

### 4.1 경로

소스:

```text
/home/woogon/CMAQ_MODEL/src/hdf5-1.14.6
```

설치 대상:

```text
/home/woogon/CMAQ_MODEL/libs/HDF5-1.14.6
```

### 4.2 소스 디렉터리 이동

```bash
cd /home/woogon/CMAQ_MODEL/src/hdf5-1.14.6
```

확인:

```bash
pwd
```

### 4.3 컴파일러 지정

새 shell에서 실행하거나 WRF 빌드 뒤 다시 구축한다면 §2.2의 옵션 초기화를 먼저 적용한다. HDF5를 새로 빌드할 때 기존 CPPFLAGS/LDFLAGS를 그대로 물려받지 않는다.

```bash
export CC=gcc
export CXX=g++
export FC=gfortran
```

확인:

```bash
gcc --version
gfortran --version
```

이번 구축에서는 GCC/GFortran 11.5.0을 사용했다.

### 4.4 Configure

HDF5를 별도 `libs` 디렉터리에 설치하고 Fortran 인터페이스를 사용할 수 있도록 구성했다.

```bash
./configure \
  --prefix=/home/woogon/CMAQ_MODEL/libs/HDF5-1.14.6 \
  --enable-fortran \
  --enable-shared \
  --enable-static
```

Configure 종료 후 성공 여부를 확인한다.

```bash
echo $?
```

`0`이면 정상이다.

### 4.5 컴파일

CPU 4코어 환경이므로 다음과 같이 수행했다.

```bash
make -j4
```

확인:

```bash
echo $?
```

### 4.6 테스트

```bash
make check
```

확인:

```bash
echo $?
```

이번 설치에서는 `make check`가 정상 완료되었다.

### 4.7 설치

```bash
make install
```

확인:

```bash
echo $?
```

### 4.8 설치 결과 확인

```bash
/home/woogon/CMAQ_MODEL/libs/HDF5-1.14.6/bin/h5cc -showconfig
```

또는 설치 디렉터리에서 실행하는 경우:

```bash
./h5cc -showconfig
```

> 현재 디렉터리는 기본적으로 PATH에 포함되지 않으므로 프로그램이 현재 디렉터리에 있다면 `./h5cc`처럼 실행한다.

최종 설치 위치:

```text
/home/woogon/CMAQ_MODEL/libs/HDF5-1.14.6
```

**상태: 컴파일, 테스트, 설치 및 검증 완료**

---

## 5. netCDF-C 4.9.3 설치

### 5.1 경로

소스:

```text
/home/woogon/CMAQ_MODEL/src/netcdf-c-4.9.3
```

설치 대상:

```text
/home/woogon/CMAQ_MODEL/libs/netCDF-C-4.9.3
```

사용할 HDF5:

```text
/home/woogon/CMAQ_MODEL/libs/HDF5-1.14.6
```

### 5.2 소스 디렉터리 이동

```bash
cd /home/woogon/CMAQ_MODEL/src/netcdf-c-4.9.3
```

### 5.3 HDF5 환경 설정

```bash
export HDF5=/home/woogon/CMAQ_MODEL/libs/HDF5-1.14.6
export CPPFLAGS="-I$HDF5/include"
export LDFLAGS="-L$HDF5/lib"
export LD_LIBRARY_PATH="$HDF5/lib:${LD_LIBRARY_PATH}"
```

확인:

```bash
echo $HDF5
echo $CPPFLAGS
echo $LDFLAGS
echo $LD_LIBRARY_PATH
```

### 5.4 Configure

```bash
./configure \
  --prefix=/home/woogon/CMAQ_MODEL/libs/netCDF-C-4.9.3 \
  --disable-dap
```

초기 Configure 과정에서 `xml2-config`를 찾지 못해 중단되었다. 따라서 Rocky Linux 개발 패키지를 추가 설치했다.

```bash
sudo dnf install libxml2-devel
```

설치 후 다시 동일한 Configure 명령을 실행했다.

```bash
./configure \
  --prefix=/home/woogon/CMAQ_MODEL/libs/netCDF-C-4.9.3 \
  --disable-dap
```

Configure 종료 확인:

```bash
echo $?
```

결과 `0`을 확인했다.

### 5.5 컴파일

```bash
make -j4
```

### 5.6 테스트

```bash
make check
```

### 5.7 설치

```bash
make install
```

각 단계에서 필요하면 다음으로 종료 코드를 확인한다.

```bash
echo $?
```

이번 구축에서는 컴파일, 테스트, 설치가 모두 정상 완료되었다.

### 5.8 netCDF-C 검증

버전 확인:

```bash
/home/woogon/CMAQ_MODEL/libs/netCDF-C-4.9.3/bin/nc-config --version
```

netCDF-4 지원 확인:

```bash
/home/woogon/CMAQ_MODEL/libs/netCDF-C-4.9.3/bin/nc-config --has-nc4
```

HDF5 지원 확인:

```bash
/home/woogon/CMAQ_MODEL/libs/netCDF-C-4.9.3/bin/nc-config --has-hdf5
```

확인 결과:

```text
netCDF 4.9.3
yes
yes
```

전체 설정 확인:

```bash
/home/woogon/CMAQ_MODEL/libs/netCDF-C-4.9.3/bin/nc-config --all
```

**상태: 컴파일, 테스트, 설치 및 검증 완료**

---

## 6. netCDF-Fortran 4.6.2 설치

### 6.1 경로

소스:

```text
/home/woogon/CMAQ_MODEL/src/netcdf-fortran-4.6.2
```

설치 대상:

```text
/home/woogon/CMAQ_MODEL/libs/netCDF-Fortran-4.6.2
```

연결할 netCDF-C:

```text
/home/woogon/CMAQ_MODEL/libs/netCDF-C-4.9.3
```

### 6.2 소스 디렉터리 이동

```bash
cd /home/woogon/CMAQ_MODEL/src/netcdf-fortran-4.6.2
```

### 6.3 netCDF-C 환경 설정

```bash
export CC=gcc
export FC=gfortran
export NETCDF=/home/woogon/CMAQ_MODEL/libs/netCDF-C-4.9.3
export CPPFLAGS="-I$NETCDF/include"
export LDFLAGS="-L$NETCDF/lib"
export LD_LIBRARY_PATH="$NETCDF/lib:/home/woogon/CMAQ_MODEL/libs/HDF5-1.14.6/lib:${LD_LIBRARY_PATH}"
```

확인:

```bash
echo $NETCDF
echo $CPPFLAGS
echo $LDFLAGS
echo $LD_LIBRARY_PATH
```

### 6.4 Configure

```bash
./configure \
  --prefix=/home/woogon/CMAQ_MODEL/libs/netCDF-Fortran-4.6.2
```

종료 코드 확인:

```bash
echo $?
```

결과 `0`을 확인했다.

### 6.5 컴파일

```bash
make -j4
```

### 6.6 테스트

```bash
make check
```

### 6.7 설치

```bash
make install
```

이번 구축에서는 세 단계가 모두 정상 완료되었다.

### 6.8 netCDF-Fortran 검증

전체 설정 확인:

```bash
/home/woogon/CMAQ_MODEL/libs/netCDF-Fortran-4.6.2/bin/nf-config --all
```

주요 확인 결과:

```text
cc       : gcc
fc       : gfortran
has-f03  : yes
has-nc2  : yes
has-nc4  : yes
prefix   : /home/woogon/CMAQ_MODEL/libs/netCDF-Fortran-4.6.2
version  : netCDF-Fortran 4.6.2
```

Fortran 링크 옵션 확인:

```bash
/home/woogon/CMAQ_MODEL/libs/netCDF-Fortran-4.6.2/bin/nf-config --flibs
```

확인된 출력:

```text
-L/home/woogon/CMAQ_MODEL/libs/netCDF-Fortran-4.6.2/lib -lnetcdff -L/home/woogon/CMAQ_MODEL/libs/netCDF-C-4.9.3/lib -lnetcdf -lnetcdf -lm
```

netCDF-C 링크 옵션도 확인했다.

```bash
/home/woogon/CMAQ_MODEL/libs/netCDF-C-4.9.3/bin/nc-config --libs
```

확인된 출력:

```text
-L/home/woogon/CMAQ_MODEL/libs/netCDF-C-4.9.3/lib -lnetcdf
```

최종 설치 위치:

```text
/home/woogon/CMAQ_MODEL/libs/netCDF-Fortran-4.6.2
```

**상태: 컴파일, 테스트, 설치 및 검증 완료**

---

## 7. I/O API 3.2-20200828 설치

### 7.1 경로

소스 및 빌드 디렉터리:

```text
/home/woogon/CMAQ_MODEL/libs/ioapi-3.2-20200828
```

빌드 결과(라이브러리, 모듈, M3TOOLS 실행파일):

```text
/home/woogon/CMAQ_MODEL/libs/ioapi-3.2-20200828/Linux2_x86_64gfort10
```

연결할 netCDF:

```text
/home/woogon/CMAQ_MODEL/libs/netCDF-Fortran-4.6.2
/home/woogon/CMAQ_MODEL/libs/netCDF-C-4.9.3
```

> 다른 라이브러리와 달리 I/O API는 `src/`가 아닌 `libs/` 아래에서 직접 빌드했다. CMAQ 빌드 시 `libioapi.a`뿐 아니라 빌드 디렉터리의 `.mod` 파일과 `ioapi/fixed_src` include 파일을 함께 참조하는데, `make install`은 라이브러리와 실행파일만 복사하기 때문이다.

### 7.2 주요 설정 결정사항

| 항목 | 설정 | 이유 |
|---|---|---|
| BIN | `Linux2_x86_64gfort10` | GFortran 10 이상에서 필요한 `-fallow-argument-mismatch` 플래그 포함 |
| CPLMODE | `nocpl` | PVM 결합모드 미사용(CMAQ 표준 구성) |
| OpenMP | 비활성화 | CMAQ 가이드 권장 구성 |
| NCFLIBS | netCDF-Fortran, netCDF-C 경로 각각 지정 | 두 라이브러리가 서로 다른 디렉터리에 설치되어 있음 |

> 기본값 `BIN=Linux2_x86_64gfort`로 GFortran 11.5에서 빌드하면 `Error: Rank mismatch between actual argument at (1) and actual argument at (2)` 오류로 컴파일이 중단된다. 반드시 `gfort10` 계열 Makeinclude를 사용한다.

### 7.3 소스 다운로드

```bash
export ROOT=/home/woogon/CMAQ_MODEL
cd $ROOT/libs
git clone https://github.com/cjcoats/ioapi-3.2 ioapi-3.2-20200828
cd ioapi-3.2-20200828
git checkout 20200828
```

버전 확인:

```bash
git log --oneline -1
```

확인 결과:

```text
ef5d5f4 Makeinclude-changes for "gfortran-10" and related changes -- CJC
```

현재 위치 확인:

```bash
pwd
```

```text
/home/woogon/CMAQ_MODEL/libs/ioapi-3.2-20200828
```

> 7.4~7.7의 모든 명령은 이 디렉터리에서 실행한다. 새 터미널에서 이어갈 때는 아래를 실행한다.

```bash
export ROOT=/home/woogon/CMAQ_MODEL
export BIN=Linux2_x86_64gfort10
export IOAPI_DIR=$ROOT/libs/ioapi-3.2-20200828
cd "$IOAPI_DIR"
export LD_LIBRARY_PATH=$ROOT/libs/netCDF-Fortran-4.6.2/lib:$ROOT/libs/netCDF-C-4.9.3/lib:$ROOT/libs/HDF5-1.14.6/lib:${LD_LIBRARY_PATH:-}
```

### 7.4 최상위 Makefile 작성

```bash
export BIN=Linux2_x86_64gfort10
export IOAPI_DIR=$ROOT/libs/ioapi-3.2-20200828
cp Makefile.template Makefile
```

`BASEDIR`을 절대경로로, `NCFLIBS`를 실제 netCDF 설치 경로로 수정한다.

```bash
sed -i \
 -e "s|^BASEDIR    = \${PWD}|BASEDIR    = $IOAPI_DIR|" \
 -e "s|^NCFLIBS    = -lnetcdff -lnetcdf|NCFLIBS    = -L$ROOT/libs/netCDF-Fortran-4.6.2/lib -lnetcdff -L$ROOT/libs/netCDF-C-4.9.3/lib -lnetcdf|" \
 Makefile
```

`CPLMODE`, `INSTALL`, `LIBINST`, `BININST`를 추가한다.

```bash
sed -i "/^VERSION    = /i CPLMODE    = nocpl\nINSTALL    = $IOAPI_DIR\nLIBINST    = \$(INSTALL)/\$(BIN)\nBININST    = \$(INSTALL)/\$(BIN)\n" Makefile
```

확인:

```bash
grep -E "^(CPLMODE|INSTALL|LIBINST|BININST|BASEDIR|NCFLIBS)" Makefile
```

기대 결과:

```text
CPLMODE    = nocpl
INSTALL    = /home/woogon/CMAQ_MODEL/libs/ioapi-3.2-20200828
LIBINST    = $(INSTALL)/$(BIN)
BININST    = $(INSTALL)/$(BIN)
BASEDIR    = /home/woogon/CMAQ_MODEL/libs/ioapi-3.2-20200828
NCFLIBS    = -L/home/woogon/CMAQ_MODEL/libs/netCDF-Fortran-4.6.2/lib -lnetcdff -L/home/woogon/CMAQ_MODEL/libs/netCDF-C-4.9.3/lib -lnetcdf
```

### 7.5 OpenMP 비활성화 및 하위 Makefile 준비

```bash
sed -i -e 's/^OMPFLAGS  = -fopenmp/OMPFLAGS  = # -fopenmp/' \
       -e 's/^OMPLIBS   = -fopenmp/OMPLIBS   = # -fopenmp/' \
       ioapi/Makeinclude.$BIN
```

확인:

```bash
grep -E "^OMP" ioapi/Makeinclude.$BIN
```

```text
OMPFLAGS  = # -fopenmp
OMPLIBS   = # -fopenmp
```

비결합(nocpl) 모드 Makefile 복사:

```bash
cp ioapi/Makefile.nocpl ioapi/Makefile
cp m3tools/Makefile.nocpl m3tools/Makefile
```

### 7.6 컴파일

netCDF/HDF5 공유 라이브러리 경로 지정:

```bash
export LD_LIBRARY_PATH=$ROOT/libs/netCDF-Fortran-4.6.2/lib:$ROOT/libs/netCDF-C-4.9.3/lib:$ROOT/libs/HDF5-1.14.6/lib:$LD_LIBRARY_PATH
```

Makefile 생성 및 빌드:

```bash
set -o pipefail
make configure 2>&1 | tee configure.log
# 직후 종료 코드가 0인지 확인하고 make all을 실행한다.
echo $?
make all 2>&1 | tee make.log
echo $?
```

> I/O API는 빌드 순서 의존성이 있으므로 `-j` 옵션 없이 실행한다.

> 위 명령은 `set -o pipefail`을 적용하여 make 실패가 파이프 종료 코드에 반영되게 했다. pipefail 없이 `| tee`를 사용하면 `echo $?`는 tee의 코드만 반환하여 빌드 실패에도 `0`일 수 있다. 성공 여부는 7.7의 산출물·로그·공유 라이브러리 확인과 7.8의 링크·실행 테스트를 함께 확인하여 판단한다. 이 테스트는 모듈 연결과 초기화·종료를 확인하며, 실제 Models-3 파일 입출력이나 CMAQ 실행 검증은 후속 단계에서 수행한다.

### 7.7 설치 결과 확인

주요 산출물 확인:

```bash
ls $BIN/libioapi.a $BIN/m3utilio.mod $BIN/m3xtract $BIN/m3stat
```

빌드 로그 오류 확인:

```bash
grep -c -i " error" make.log
```

결과 `0`을 확인했다.

```bash
tail -5 make.log
```

`make[1]: Leaving directory '.../m3tools'`로 정상 종료됨을 확인했다.

M3TOOLS의 netCDF 공유 라이브러리 연결 확인:

```bash
ldd $BIN/m3xtract | grep -E "netcdf|not found"
```

`not found` 항목이 없음을 확인했다.

### 7.8 링크·실행 테스트

I/O API 모듈(`M3UTILIO`)을 사용하는 테스트 프로그램을 작성해 컴파일·링크·실행까지 확인했다.

```bash
cat > /tmp/iotest.f90 <<'EOF'
program iotest
  use m3utilio
  implicit none
  integer :: logdev
  logdev = init3()
  write(*,*) 'I/O API OK, logdev=', logdev
  if (.not. shut3()) stop 1
end program iotest
EOF
```

```bash
gfortran -I$IOAPI_DIR/$BIN -I$IOAPI_DIR/ioapi/fixed_src /tmp/iotest.f90 \
  -L$IOAPI_DIR/$BIN -lioapi \
  -L$ROOT/libs/netCDF-Fortran-4.6.2/lib -lnetcdff -L$ROOT/libs/netCDF-C-4.9.3/lib -lnetcdf \
  -o /tmp/iotest && /tmp/iotest
```

확인 결과:

```text
 I/O API OK, logdev=           6
```

> 함께 출력되는 `Missing environment variable EXECUTION_ID`는 실행 ID 환경변수가 없다는 경고이며 정상이다.

### 7.9 빌드 기록 보관

```bash
mkdir -p /home/woogon/CMAQ_MODEL/logs/ioapi
cp /home/woogon/CMAQ_MODEL/libs/ioapi-3.2-20200828/{configure.log,make.log,Makefile} \
   /home/woogon/CMAQ_MODEL/logs/ioapi/
cp /home/woogon/CMAQ_MODEL/libs/ioapi-3.2-20200828/ioapi/Makeinclude.Linux2_x86_64gfort10 \
   /home/woogon/CMAQ_MODEL/logs/ioapi/
```

최종 위치:

```text
라이브러리·모듈·M3TOOLS : /home/woogon/CMAQ_MODEL/libs/ioapi-3.2-20200828/Linux2_x86_64gfort10
include               : /home/woogon/CMAQ_MODEL/libs/ioapi-3.2-20200828/ioapi/fixed_src
```

**상태: 컴파일, 링크 테스트 및 검증 완료**

---

## 8. 환경변수 등록

이 문서의 netCDF 빌드 단계에서 사용한 `HDF5`, `NETCDF`는 당시의 빌드용 변수이다. 이후 WRF configure에서는 `HDF5_PATH=$CMAQ_LIBS/HDF5-1.14.6`과 `NETCDF=$CMAQ_LIBS/netCDF-WRF`를 사용한다. netCDF 빌드 때 남은 `HDF5` 변수는 WRF의 다른 I/O 기능을 활성화하므로 WRF 빌드 shell에서 해제하고, 상세 설정은 [WRF/WPS 설치 가이드](../wrf/WRF_WPS_Installation_Guide.md) §7.5, §12를 따른다.

매 터미널마다 경로를 다시 지정하지 않도록 `~/.bashrc`에 등록했다.

```bash
cp -p ~/.bashrc ~/.bashrc.bak_libraries_$(date -u +%Y%m%dT%H%M%SZ)
cat >> ~/.bashrc <<'EOF'
# CMAQ libraries
export CMAQ_LIBS=/home/woogon/CMAQ_MODEL/libs
export LD_LIBRARY_PATH=$CMAQ_LIBS/netCDF-Fortran-4.6.2/lib:$CMAQ_LIBS/netCDF-C-4.9.3/lib:$CMAQ_LIBS/HDF5-1.14.6/lib:$LD_LIBRARY_PATH
export IOAPI_DIR=$CMAQ_LIBS/ioapi-3.2-20200828
export PATH=$IOAPI_DIR/Linux2_x86_64gfort10:$PATH
EOF
```

> `>>`(추가)를 사용해야 한다. `>`를 쓰면 기존 `.bashrc` 내용이 지워진다. 이 명령은 한 번만 실행한다.

적용 및 확인:

```bash
source ~/.bashrc
tail -6 ~/.bashrc
echo $IOAPI_DIR
which m3xtract
```

확인 결과:

```text
/home/woogon/CMAQ_MODEL/libs/ioapi-3.2-20200828
/home/woogon/CMAQ_MODEL/libs/ioapi-3.2-20200828/Linux2_x86_64gfort10/m3xtract
```

**상태: 등록 및 확인 완료**

---

## 9. 최종 확인

```bash
/home/woogon/CMAQ_MODEL/libs/HDF5-1.14.6/bin/h5cc -showconfig
/home/woogon/CMAQ_MODEL/libs/netCDF-C-4.9.3/bin/nc-config --version
/home/woogon/CMAQ_MODEL/libs/netCDF-C-4.9.3/bin/nc-config --has-nc4
/home/woogon/CMAQ_MODEL/libs/netCDF-C-4.9.3/bin/nc-config --has-hdf5
/home/woogon/CMAQ_MODEL/libs/netCDF-Fortran-4.6.2/bin/nf-config --version
/home/woogon/CMAQ_MODEL/libs/netCDF-Fortran-4.6.2/bin/nf-config --all
ls $IOAPI_DIR/Linux2_x86_64gfort10/libioapi.a
which m3xtract
```

완료 현황:

| 구성요소 | 버전 | 설치 방법 | 상태 |
|---|---:|---|---|
| zlib | 1.2.11 | Rocky Linux 시스템 패키지 | 확인 완료 |
| HDF5 | 1.14.6 | 소스 빌드 | 설치·검증 완료 |
| netCDF-C | 4.9.3 | 소스 빌드 | 설치·검증 완료 |
| netCDF-Fortran | 4.6.2 | 소스 빌드 | 설치·검증 완료 |
| I/O API | 3.2-20200828 | 소스 빌드 (`Linux2_x86_64gfort10`, nocpl, OpenMP 미사용) | 빌드·링크 테스트 완료 |

최종 의존관계:

```text
Rocky Linux zlib
       ↓
HDF5 1.14.6
       ↓
netCDF-C 4.9.3
       ↓
netCDF-Fortran 4.6.2
       ↓
I/O API 3.2-20200828
```

CMAQ 빌드(`config_cmaq.csh`)에서 참조할 I/O API 경로:

```text
IOAPI_INCL_DIR = /home/woogon/CMAQ_MODEL/libs/ioapi-3.2-20200828/ioapi/fixed_src
IOAPI_LIB_DIR  = /home/woogon/CMAQ_MODEL/libs/ioapi-3.2-20200828/Linux2_x86_64gfort10
```

이로써 Phase 2(Compiler 및 공통 library) 구축을 완료했다. 후속 Phase 3은 실제 FNL 사례의 WPS·real.exe와 WRF 실행 및 wrfout 생성에 성공했다(2026-10-08 사용자 확인). 현재 WRF는 오류 없이 실행 중이며, 모의 종료 후 최종 시각을 확인하고 MCIP 구축·입력 변환으로 이어간다. 절차는 [WRF/WPS 설치·실행 가이드](../wrf/WRF_WPS_Installation_Guide.md) §14를 따른다.

## 10. 검토 근거 및 관련 문서

§3~9의 기존 빌드 명령과 확인 결과는 실제 구축 기록이다. §2.1~2.3은 기존 기록에서 빠진 새 시스템 사전 준비·다운로드를 공식 소스로 보완한 명령이다. 검토 시 `20200828` 태그의 커밋 `ef5d5f4e112c249b593b19426421f25d79ae094b`, Makefile 변수 및 GFortran 옵션을 다음 공식 소스와 대조했다.

- [I/O API 20200828 소스](https://github.com/cjcoats/ioapi-3.2/tree/20200828)
- [최상위 Makefile.template](https://github.com/cjcoats/ioapi-3.2/blob/20200828/Makefile.template)
- [Makeinclude.Linux2_x86_64gfort10](https://github.com/cjcoats/ioapi-3.2/blob/20200828/ioapi/Makeinclude.Linux2_x86_64gfort10)
- [구축 기본계획 및 Phase 현황](../planning/00_CMAQ_Project_Master_Plan.md)

WRF/WPS 버전·빌드 설정 및 오류 해결의 상세 기준은 [WRF/WPS 설치 가이드](../wrf/WRF_WPS_Installation_Guide.md)이다. WRF용 `netCDF-WRF` 통합 링크(§7), GRIB2 라이브러리(§8), basic nesting의 `landread.c.dist` 대체와 moving nest 재검토(§10.3), warning 103건 및 실제 test run 검증 예정(§10.7), WPS 명령에 한정한 `MPI_LIB=` 처리(§11.5)는 해당 문서에서 관리한다.
