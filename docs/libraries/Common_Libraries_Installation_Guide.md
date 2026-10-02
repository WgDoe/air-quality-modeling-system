# CMAQ 모델링 시스템 공통 라이브러리 구축 기록

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

기본 디렉터리 구조:

```text
/home/woogon/CMAQ_MODEL/
├── libs/       # 설치된 라이브러리
└── src/        # 다운로드 및 압축해제한 소스
```

HDF5와 netCDF는 소스와 설치 결과를 분리하고 라이브러리 디렉터리명에는 정확한 버전을 표시한다. I/O API는 7.1절과 같이 `libs/` 아래에서 직접 빌드했다.

Compiler/MPI 설치 및 검증은 [GNU Compiler 및 OpenMPI 설치 가이드](../compiler/GNU_Compiler_OpenMPI_Installation_Guide.md)를 참고한다.

---

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

> 7.4~7.7의 모든 명령은 이 디렉터리에서 실행한다. 새 터미널을 열었다면 `ROOT`, `BIN`, `IOAPI_DIR` 변수를 다시 지정해야 한다.

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
make configure 2>&1 | tee configure.log
make all 2>&1 | tee make.log
```

> I/O API는 빌드 순서 의존성이 있으므로 `-j` 옵션 없이 실행한다.

> `| tee`를 사용하면 `echo $?`는 make가 아닌 tee의 종료 코드를 반환하므로 빌드가 실패해도 `0`이 나올 수 있다. 성공 여부는 7.7의 산출물·로그·공유 라이브러리 확인과 7.8의 링크·실행 테스트를 함께 확인하여 판단한다. 이 테스트는 모듈 연결과 초기화·종료를 확인하며, 실제 Models-3 파일 입출력이나 CMAQ 실행 검증은 후속 단계에서 수행한다.

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

매 터미널마다 경로를 다시 지정하지 않도록 `~/.bashrc`에 등록했다.

```bash
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

이로써 Phase 2(Compiler 및 공통 library) 구축을 완료했다. 다음 구축 대상은 **Phase 3 WRF/WPS**이다.

## 10. 검토 근거 및 관련 문서

위 명령과 확인 결과는 실제 구축 기록이다. 검토 시 `20200828` 태그의 커밋 `ef5d5f4e112c249b593b19426421f25d79ae094b`, Makefile 변수 및 GFortran 옵션을 다음 공식 소스와 대조했다.

- [I/O API 20200828 소스](https://github.com/cjcoats/ioapi-3.2/tree/20200828)
- [최상위 Makefile.template](https://github.com/cjcoats/ioapi-3.2/blob/20200828/Makefile.template)
- [Makeinclude.Linux2_x86_64gfort10](https://github.com/cjcoats/ioapi-3.2/blob/20200828/ioapi/Makeinclude.Linux2_x86_64gfort10)
- [구축 기본계획 및 Phase 현황](../planning/00_CMAQ_Project_Master_Plan.md)

WRF/WPS 버전과 상세 빌드 설정은 아직 이 설치 기록에서 확정하지 않았다.
