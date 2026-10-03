# CMAQ 모델링 시스템 WRF/WPS 구축 기록

## 1. 목적
Rocky Linux 기반 CMAQ 통합 대기질 모델링 시스템 구축 과정에서 Phase 3(WRF/WPS) 설치 절차를 재현할 수 있도록 기록한다. 설치 중 발생한 오류와 해결 과정도 함께 기록한다.

설치 순서:

```text
버전 확정 및 사전 점검
  ↓
netCDF 통합 링크 디렉터리 구성 (WRF용)
  ↓
GRIB2 라이브러리: libpng 1.2.50, JasPer 1.900.1 (WPS용)
  ↓
WRF 4.5.1 configure
  ↓
WRF 4.5.1 compile
  ↓
WPS 4.5 configure / compile
  ↓
지형자료(WPS_GEOG) 준비 및 테스트 사례 실행  ← 다음 단계
```

현재 상태(2026-10-03): **WRF 4.5.1과 WPS 4.5의 설치·컴파일·동적 라이브러리 연결 확인 완료, 실제 입력자료 실행검증 미완료.** 지형자료 다운로드와 테스트 사례 실행은 아직 수행하지 않았다.

## 2. 구축 환경

- OS: Rocky Linux 9.8 (Blue Onyx), x86_64
- 사용자: `woogon`
- 프로젝트 루트: `/home/woogon/CMAQ_MODEL`
- CPU 코어: 4 (`nproc`)
- 메모리: 약 7.2 GB (`free -h`)
- `/home` 여유 공간: 약 494 GB (`df -h /home`)
- GCC / GFortran: 11.5.0
- OpenMPI: 4.1.1 (Rocky Linux 패키지, Environment Modules로 활성화)
- 공통 라이브러리: HDF5 1.14.6, netCDF-C 4.9.3, netCDF-Fortran 4.6.2, I/O API 3.2-20200828

공통 라이브러리 설치는 [공통 라이브러리 구축 기록](../libraries/Common_Libraries_Installation_Guide.md)을, Compiler/MPI는 [GNU Compiler 및 OpenMPI 설치 가이드](../compiler/GNU_Compiler_OpenMPI_Installation_Guide.md)를 참고한다.

디렉터리 구조:

[구축 기본계획](../planning/00_CMAQ_Project_Master_Plan.md) §4.2의 구조에 따라 모델 본체는 `src/`가 아닌 프로젝트 루트 아래에 별도 폴더로 둔다. 폴더명에는 버전을 표시한다.

```text
/home/woogon/CMAQ_MODEL/
├── libs/
│   ├── HDF5-1.14.6/
│   ├── netCDF-C-4.9.3/
│   ├── netCDF-Fortran-4.6.2/
│   ├── netCDF-WRF/          # WRF용 netCDF 통합 링크 디렉터리 (5장)
│   ├── grib2/               # libpng, JasPer 설치 결과 (6장)
│   └── ioapi-3.2-20200828/
├── src/                     # 원본 압축파일 및 라이브러리 소스 보관
│   ├── grib2/
│   ├── v4.5.1.tar.gz        # WRF 4.5.1 릴리스 파일
│   └── WPS-4.5.tar.gz       # WPS 4.5 소스
├── WRFV4.5.1/               # WRF 본체 (7~10장)
└── WPS-4.5/                 # WPS 본체 (11장)
```

> 처음에는 WRF를 `src/WRFV4.5.1`에 풀어 configure까지 진행했으나, 기본계획의 디렉터리 구조와 맞지 않아 삭제하고 프로젝트 루트에서 처음부터 다시 진행했다.

---

## 3. 버전 확정

모델 버전은 CMAQ를 먼저 확정하고 나머지를 CMAQ 호환성에 맞춘다(기본계획 §3.5).

| 구성요소 | 버전 | 근거 |
|---|---|---|
| WRF | 4.5.1 (태그 `v4.5.1`) | 결합형 WRF-CMAQv5.5의 공식 호환범위(WRF 4.4~4.5.1)의 상한 |
| WPS | 4.5 (태그 `v4.5`) | WPS는 4.5.1 태그가 없으며 WRF 4.5.x와 짝을 이루는 버전 |

- 분리 실행(WRF → MCIP → CMAQ)은 CMAQ 5.5의 MCIP로 처리 가능하다.
- 향후 결합 실행(WRF-CMAQ)으로 확장할 때 WRF를 재설치할 필요가 없다.
- CMAS 포럼에는 WRF 4.5.2로 결합 모델을 빌드했을 때 benchmark가 중단되고, WRF 4.5.1로 재빌드하자 정상 실행된 사례가 보고되어 있다.

**상태: 확정**

---

## 4. 사전 점검

### 4.1 컴파일러 및 MPI

```bash
gcc --version | head -1
gfortran --version | head -1
which mpicc mpif90
```

### 4.2 netCDF

```bash
nc-config --version
nf-config --version
nc-config --has-nc4
echo "NETCDF=$NETCDF"
```

점검 당시 `nc-config` 명령을 찾을 수 없었고 `NETCDF` 변수도 비어 있었다. netCDF-C와 netCDF-Fortran이 서로 다른 디렉터리에 설치되어 있고, 각 `bin/`이 `PATH`에 등록되어 있지 않았기 때문이다. 5장에서 해결했다.

### 4.3 빌드 도구

```bash
which csh tcsh perl m4 make file
```

> 이 단계에서 `csh`가 없다는 것을 놓쳤고, WRF compile 시작 시점에 오류로 발견했다(9장). 결과를 한 줄씩 반드시 확인한다.

### 4.4 하드웨어 자원

```bash
nproc
free -h
df -h /home
```

**상태: 점검 완료 (csh 누락은 9장에서 처리)**

---

## 5. WRF용 netCDF 통합 링크 디렉터리 구성

### 5.1 필요성

WRF는 `NETCDF` 환경변수 하나로 netCDF-C와 netCDF-Fortran의 `bin`, `include`, `lib`를 한 곳에서 찾는다. 현재는 두 라이브러리가 별도 디렉터리에 설치되어 있으므로, 원본 설치는 변경하지 않고 심볼릭 링크로 묶은 디렉터리를 만든다. CMAQ 5.5의 `config_cmaq.csh`는 C와 Fortran 경로를 따로 지정하므로 기존 구조를 그대로 사용한다(기본계획 §3.5).

### 5.2 설치 위치 확인

```bash
cd /home/woogon/CMAQ_MODEL/libs
ls
grep -n "export" ~/.bashrc
```

확인 결과:

```text
HDF5-1.14.6  ioapi-3.2-20200828  netCDF-C-4.9.3  netCDF-Fortran-4.6.2
```

### 5.3 통합 디렉터리 생성

```bash
cd /home/woogon/CMAQ_MODEL/libs
mkdir -p netCDF-WRF/bin netCDF-WRF/include netCDF-WRF/lib
```

### 5.4 심볼릭 링크 생성

```bash
ln -s /home/woogon/CMAQ_MODEL/libs/netCDF-C-4.9.3/bin/* netCDF-WRF/bin/
ln -s /home/woogon/CMAQ_MODEL/libs/netCDF-Fortran-4.6.2/bin/* netCDF-WRF/bin/

ln -s /home/woogon/CMAQ_MODEL/libs/netCDF-C-4.9.3/include/* netCDF-WRF/include/
ln -s /home/woogon/CMAQ_MODEL/libs/netCDF-Fortran-4.6.2/include/* netCDF-WRF/include/

ln -s /home/woogon/CMAQ_MODEL/libs/netCDF-C-4.9.3/lib/libnetcdf* netCDF-WRF/lib/
ln -s /home/woogon/CMAQ_MODEL/libs/netCDF-Fortran-4.6.2/lib/libnetcdf* netCDF-WRF/lib/
```

> `lib/`는 `libnetcdf*` 파일만 연결한다. 두 라이브러리에 모두 `pkgconfig` 등 같은 이름의 하위 디렉터리가 있어 전체를 연결하면 충돌한다.

### 5.5 확인

```bash
ls netCDF-WRF/bin
ls netCDF-WRF/lib
ls netCDF-WRF/include
```

확인 결과(요약):

```text
bin     : nc-config nc4print nccopy ncdump ncgen ncgen3 nf-config
lib     : libnetcdf.a libnetcdf.so libnetcdf.so.22 ... libnetcdff.a libnetcdff.so libnetcdff.so.7 ...
include : netcdf.h netcdf.inc netcdf.mod typesizes.mod netcdf_meta.h ...
```

### 5.6 환경변수 등록

```bash
cd ~
cp ~/.bashrc ~/.bashrc.bak_before_wrf
echo '' >> ~/.bashrc
echo '# netCDF for WRF (C+Fortran combined)' >> ~/.bashrc
echo 'export NETCDF=$CMAQ_LIBS/netCDF-WRF' >> ~/.bashrc
echo 'export PATH=$NETCDF/bin:$PATH' >> ~/.bashrc
source ~/.bashrc
```

확인:

```bash
echo $NETCDF
which nc-config nf-config
nc-config --version
nf-config --version
nf-config --has-nc4
```

확인 결과:

```text
/home/woogon/CMAQ_MODEL/libs/netCDF-WRF
netCDF 4.9.3
netCDF-Fortran 4.6.2
yes
```

**상태: 구성 및 확인 완료**

---

## 6. GRIB2 라이브러리 설치 (libpng, JasPer)

### 6.1 필요성

WPS의 `ungrib`이 GRIB2 형식 기상자료(GFS 등)의 압축 데이터를 풀기 위해 libpng(PNG 압축)와 JasPer(JPEG2000 압축)가 필요하다. 버전은 WRF 공식 컴파일 튜토리얼과 같은 libpng 1.2.50, JasPer 1.900.1을 사용했다.

> WPS 4.4 이상은 `--build-grib2-libs` 옵션으로 이 라이브러리를 WPS 내부에 빌드할 수 있으나, 구조를 명확히 하고 문서화하기 위해 `libs/grib2`에 별도 설치했다.

### 6.2 경로

소스:

```text
/home/woogon/CMAQ_MODEL/src/grib2
```

설치 대상:

```text
/home/woogon/CMAQ_MODEL/libs/grib2
```

### 6.3 사전 확인

```bash
rpm -q zlib-devel
```

### 6.4 소스 다운로드

```bash
mkdir -p /home/woogon/CMAQ_MODEL/src/grib2
cd /home/woogon/CMAQ_MODEL/src/grib2
wget https://www2.mmm.ucar.edu/wrf/OnLineTutorial/compile_tutorial/tar_files/libpng-1.2.50.tar.gz
wget https://www2.mmm.ucar.edu/wrf/OnLineTutorial/compile_tutorial/tar_files/jasper-1.900.1.tar.gz
ls -lh
```

### 6.5 libpng 1.2.50 설치

```bash
cd /home/woogon/CMAQ_MODEL/src/grib2
tar -xzf libpng-1.2.50.tar.gz
cd libpng-1.2.50
./configure --prefix=/home/woogon/CMAQ_MODEL/libs/grib2
make
make install
```

### 6.6 JasPer 1.900.1 설치

```bash
cd /home/woogon/CMAQ_MODEL/src/grib2
tar -xzf jasper-1.900.1.tar.gz
cd jasper-1.900.1
./configure --prefix=/home/woogon/CMAQ_MODEL/libs/grib2
make
make install
```

### 6.7 설치 결과 확인

```bash
ls /home/woogon/CMAQ_MODEL/libs/grib2/lib
ls /home/woogon/CMAQ_MODEL/libs/grib2/include/jasper
```

확인 결과(요약):

```text
lib           : libjasper.a libjasper.la libpng.a libpng.so libpng12.a libpng12.so ... pkgconfig
include/jasper: jasper.h jas_cm.h jas_config.h jas_image.h jas_stream.h ...
```

JasPer 1.900.1은 기본 설정에서 정적 라이브러리(`libjasper.a`)만 생성한다. WPS는 헤더를 `jasper/jasper.h` 경로로 찾으므로 `include/jasper/` 구조가 필요하다.

### 6.8 환경변수 등록

```bash
cd ~
cp ~/.bashrc ~/.bashrc.bak_before_grib2
echo '' >> ~/.bashrc
echo '# GRIB2 libraries for WPS (libpng, JasPer)' >> ~/.bashrc
echo 'export JASPERLIB=$CMAQ_LIBS/grib2/lib' >> ~/.bashrc
echo 'export JASPERINC=$CMAQ_LIBS/grib2/include' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=$CMAQ_LIBS/grib2/lib:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc
```

확인:

```bash
echo $JASPERLIB
echo $JASPERINC
echo $LD_LIBRARY_PATH | tr ':' '\n'
```

확인 결과:

```text
/home/woogon/CMAQ_MODEL/libs/grib2/lib
/home/woogon/CMAQ_MODEL/libs/grib2/include
```

> 같은 터미널에서 `source ~/.bashrc`를 여러 번 실행하면 `LD_LIBRARY_PATH`에 같은 경로가 반복되어 보인다. 동작에는 문제가 없으며 새 터미널에서는 한 번씩만 들어간다.

**상태: 설치 및 확인 완료**

---

## 7. WRF 4.5.1 소스 배치

### 7.1 소스 다운로드

GitHub 릴리스 파일을 사용한다. 같은 페이지의 "Source code" 자동 압축파일에는 NoahMP 등 하위 모듈이 빠져 있어 컴파일 오류가 발생하므로 사용하지 않는다.

```bash
cd /home/woogon/CMAQ_MODEL/src
wget https://github.com/wrf-model/WRF/releases/download/v4.5.1/v4.5.1.tar.gz
```

### 7.2 프로젝트 루트에 압축 해제

원본 압축파일은 `src/`에 보관하고, 모델 본체는 프로젝트 루트에 푼다.

```bash
cd /home/woogon/CMAQ_MODEL
tar -xzf src/v4.5.1.tar.gz
ls
ls WRFV4.5.1
```

확인 결과:

```text
libs  src  WRFV4.5.1
```

**상태: 완료**

---

## 8. WRF configure

### 8.1 최종 configure 절차

8.3~8.6의 문제를 모두 해결한 뒤의 최종 절차는 다음과 같다.

```bash
cd /home/woogon/CMAQ_MODEL/WRFV4.5.1
LC_ALL=C ./configure 2>&1 | tee log.configure
```

선택값:

| 질문 | 입력 | 의미 |
|---|---|---|
| `Enter selection [1-79]` | `34` | GNU (gfortran/gcc), dmpar (MPI 병렬) |
| `Compile for nesting?` | `1` | basic nesting |

> `./configure`를 다시 실행하면 `configure.wrf`가 새로 생성된다. configure 이후 `configure.wrf`를 직접 수정한 경우 그 내용이 사라지므로 주의한다. 최종 절차에서는 `configure.wrf`를 직접 수정하지 않는다.

### 8.2 최종 configure 결과

`log.configure` 주요 내용:

```text
Configuration successful!

This installation of NetCDF is 64-bit
                 C compiler is 64-bit
           Fortran compiler is 64-bit
              It will build in 64-bit

NetCDF version: 4.9.3
Enabled NetCDF-4/HDF-5: yes
NetCDF built with PnetCDF: no

This build of WRF will use NETCDF4 with HDF5 compression
```

`configure.wrf` 주요 설정 확인:

```bash
grep -n -E "^(DEP_LIB_PATH|DM_FC|DM_CC|SFC|SCC|CCOMP|DMPARALLEL|FCCOMPAT|NETCDFPATH)" configure.wrf
```

| 항목 | 값 |
|---|---|
| `DMPARALLEL` | `1` |
| `SFC` / `SCC` / `CCOMP` | `gfortran` / `gcc` / `gcc` |
| `DM_FC` / `DM_CC` | `mpif90` / `mpicc` |
| `NETCDFPATH` | `/home/woogon/CMAQ_MODEL/libs/netCDF-WRF` |
| `DEP_LIB_PATH` | `-L.../netCDF-Fortran-4.6.2/lib -L.../netCDF-C-4.9.3/lib -L.../HDF5-1.14.6/lib` |
| `FCCOMPAT` | `-fallow-argument-mismatch -fallow-invalid-boz` (gfortran 10 이상 호환 옵션, 자동 추가) |

다음 경고는 남아 있으나 8.6의 조치로 처리했다.

```text
The moving nest option is not available due to missing rpc/types.h file.
Copy landread.c.dist to landread.c in share directory to bypass compile error.
```

### 8.3 문제 1: `One of compilers testing failed!` (한국어 로케일)

증상:

```text
Testing for NetCDF, C and Fortran compiler

  One of compilers testing failed!
  Please check your compiler
```

원인:

- WRF configure는 `type gcc`의 출력 문장 중 **마지막 단어**를 컴파일러 경로로 사용한다.
- 영어 환경에서는 `gcc is /usr/bin/gcc`가 출력되어 마지막 단어가 경로이지만, 한국어 로케일에서는 한국어 문장이 출력되어 경로를 얻지 못한다.
- 그 결과 컴파일러 테스트가 실패하고 configure가 그 시점에서 **중단(exit)** 된다. 이후의 Fortran 2003/2008 기능 점검, `rpc/types.h` 점검, netCDF4 점검, gfortran 호환 옵션 추가가 모두 생략된 불완전한 `configure.wrf`가 남는다. 따라서 무시하고 진행하면 안 된다.

진단:

```bash
mkdir -p ~/wrf_test
cd ~/wrf_test
printf 'int main(){return 0;}\n' > t.c
gcc -o t_c t.c
file t_c
printf '      program t\n      end program t\n' > t.f
gfortran -o t_f t.f
file t_f
type gcc gfortran
```

컴파일러는 모두 `ELF 64-bit` 실행파일을 정상 생성했고, `type` 출력이 한국어(`gcc 는 해시됨 (/usr/bin/gcc)`)로 나오는 것을 확인했다.

```bash
sh -c 'type gcc'
LC_ALL=C sh -c 'type gcc'
rm -rf ~/wrf_test
```

해결: configure와 compile을 `LC_ALL=C`로 실행한다. 해당 명령에만 영어 로케일이 적용되며 시스템 언어 설정은 변경하지 않는다.

```bash
LC_ALL=C ./configure 2>&1 | tee log.configure
```

> 처음에는 `file` 명령 누락을 원인으로 추정했으나, `file`은 이미 설치되어 있었다. 원인은 로케일이었다.

### 8.4 문제 2: netCDF4 테스트 실패 및 `configure.wrf` 삭제 (HDF5 경로)

증상:

```text
NETCDF4 IO features are requested, but this installation of NetCDF
  /home/woogon/CMAQ_MODEL/libs/netCDF-WRF
DOES NOT support these IO features.
...
!!! configure.wrf has been REMOVED !!!
```

원인: `configure.wrf`의 `HDF5 = -lhdf5_hl -lhdf5`로 HDF5를 링크하지만, `DEP_LIB_PATH`에는 netCDF-C와 netCDF-Fortran의 `lib` 경로만 있고 HDF5의 `lib` 경로가 없었다. 실행 시 사용하는 `LD_LIBRARY_PATH`와 달리, 컴파일·링크 시에는 `-L`로 경로를 지정해야 한다.

해결: WRF configure 스크립트는 `HDF5_PATH` 환경변수가 있으면 `-L$HDF5_PATH/lib`를 `DEP_LIB_PATH`에 자동으로 추가한다.

```bash
cd ~
cp ~/.bashrc ~/.bashrc.bak_before_hdf5path
echo '' >> ~/.bashrc
echo '# HDF5 path for WRF configure (adds -L to DEP_LIB_PATH)' >> ~/.bashrc
echo 'export HDF5_PATH=$CMAQ_LIBS/HDF5-1.14.6' >> ~/.bashrc
source ~/.bashrc
echo $HDF5_PATH
```

> 변수명은 반드시 `HDF5_PATH`로 한다. `HDF5` 변수는 WRF의 다른 I/O 기능을 활성화하는 용도이므로 설정하지 않는다.

> 초기에는 configure 이후 `configure.wrf`의 `DEP_LIB_PATH` 줄을 `sed`로 직접 수정하는 방법을 사용했으나, configure를 다시 실행할 때마다 수정이 사라지고 configure 내부의 netCDF4 테스트는 통과하지 못하므로 `HDF5_PATH` 방식으로 대체했다.

### 8.5 문제 3: `mpicc: command not found` (OpenMPI 경로)

증상: `HDF5_PATH` 설정 후에도 netCDF4 테스트가 실패했다. 테스트 로그(`tools/nc4_test.log`, 실패 시 삭제되지 않고 남음)를 확인했다.

```bash
cd /home/woogon/CMAQ_MODEL/WRFV4.5.1
cat tools/nc4_test.log
```

```text
/bin/sh: line 1: [: -eq: unary operator expected
/bin/sh: line 4: mpicc: command not found
```

원인:

- 첫 줄은 WRF 4.5.1 `Makefile`의 `nc4_test` 대상에서 `USENETCDFPAR` 변수가 비어 있어 생기는 오류다. 병렬 netCDF(`NETCDFPAR`)를 사용하지 않으면 이 변수가 정의되지 않아 테스트가 `mpicc`로 컴파일하는 분기로 넘어간다. `mpicc`가 있으면 문제없다.
- 실제 원인은 둘째 줄이다. Rocky Linux 패키지 OpenMPI는 `module load`로 경로를 활성화해야 하는데, `~/.bashrc`에 등록되어 있지 않아 새 터미널에서 `mpicc`/`mpif90`을 찾지 못했다. dmpar(34번) 빌드는 WRF 전체를 `mpif90`/`mpicc`로 컴파일하므로 이 상태로는 compile도 불가능하다.

해결:

```bash
cd ~
cp ~/.bashrc ~/.bashrc.bak_before_mpi
echo '' >> ~/.bashrc
echo '# OpenMPI (Rocky package, Environment Modules)' >> ~/.bashrc
echo 'source /etc/profile.d/modules.sh' >> ~/.bashrc
echo 'module load mpi/openmpi-x86_64' >> ~/.bashrc
source ~/.bashrc
```

확인:

```bash
which mpicc mpif90
mpicc --showme:command
mpif90 --showme:command
```

확인 결과:

```text
/usr/lib64/openmpi/bin/mpicc
/usr/lib64/openmpi/bin/mpif90
gcc
gfortran
```

### 8.6 문제 4: `rpc/types.h` 없음 (Rocky Linux 9)

증상:

```text
The moving nest option is not available due to missing rpc/types.h file.
Copy landread.c.dist to landread.c in share directory to bypass compile error.
```

원인: Rocky Linux 9(glibc 2.34 이상)에는 Sun RPC 헤더가 기본 포함되지 않는다. `libtirpc-devel`을 설치해도 WRF의 `rpc_test`가 `-I/usr/include/tirpc` 없이 컴파일하므로 `netconfig.h`를 찾지 못해 실패한다.

```bash
sudo dnf install -y libtirpc-devel
ls /usr/include/tirpc/rpc/types.h
cd /home/woogon/CMAQ_MODEL/WRFV4.5.1
gcc -DUSE_TIRPC -o /tmp/rpc_test.exe tools/rpc_test.c
```

```text
/usr/include/tirpc/rpc/types.h:98:10: fatal error: netconfig.h: 그런 파일이나 디렉터리가 없습니다
```

`RPC_TYPES`가 정의되지 않으면 `share/landread.c`의 XDR 관련 코드가 컴파일되지 않는다.

해결: configure 경고가 안내하는 대로 `share/landread.c`를 기능이 비어 있는 대체 파일(`landread.c.dist`)로 교체한다. 본 구축에서는 moving nest(이동 격자)를 사용하지 않고 nesting 1번(basic)만 사용하므로 현재 설정에서는 이 대체를 허용한다. 향후 moving nest를 사용할 경우 RPC/TIRPC 설정과 원본 `landread.c` 사용 여부를 재검토한다.

```bash
cd /home/woogon/CMAQ_MODEL/WRFV4.5.1/share
cp landread.c landread.c.orig
cp landread.c.dist landread.c
ls landread*
```

확인 결과:

```text
landread.c  landread.c.dist  landread.c.orig
```

> 설치한 `libtirpc-devel`은 그대로 두었다. configure의 rpc 경고는 이 조치 후에도 계속 출력되며, 현재 basic nesting 설정에서는 대체 조치로 처리한다. 향후 moving nest 사용 시에는 RPC/TIRPC 및 원본 `landread.c` 사용 여부를 재검토한다.

**상태: configure 완료**

---

## 9. WRF compile

### 9.1 문제 5: `/bin/csh: 잘못된 인터프리터`

증상:

```text
bash: ./compile: /bin/csh: 잘못된 인터프리터: 그런 파일이나 디렉터리가 없습니다
```

원인: WRF의 `compile` 스크립트는 csh로 작성되어 있으나 시스템에 csh가 설치되어 있지 않았다. 컴파일이 시작되기 전에 중단되었으므로 configure를 다시 할 필요는 없었다.

해결:

```bash
sudo dnf install -y tcsh
ls -l /bin/csh
which csh tcsh
which perl m4 make
```

### 9.2 compile 실행

```bash
cd /home/woogon/CMAQ_MODEL/WRFV4.5.1
which mpif90
LC_ALL=C ./compile -j 2 em_real 2>&1 | tee log.compile
```

| 옵션 | 의미 |
|---|---|
| `LC_ALL=C` | 한국어 로케일로 인한 스크립트 오동작 방지 (8.3) |
| `-j 2` | 2코어 병렬 컴파일. 메모리 7.2 GB를 고려해 4코어 대신 2코어 사용 |
| `em_real` | 실제 기상자료 사례용 빌드 (`real.exe`, `wrf.exe` 생성) |
| `2>&1 \| tee log.compile` | 화면 출력과 동시에 `log.compile`에 저장 |

> 컴파일 중인 터미널은 닫거나 Ctrl+C를 누르지 않는다. 다른 터미널에서 `tail -f log.compile`로 진행 상황을 볼 수 있다.

### 9.3 결과 확인

```bash
tail -20 log.compile
ls -l main/*.exe
grep -n -i -E "Error [0-9]|undefined reference|cannot find|fatal error" log.compile
```

`log.compile` 마지막 부분:

```text
build started:   Sat Oct  3 20:24:24 KST 2026
build completed: Sat Oct 3 20:43:43 KST 2026

--->                  Executables successfully built                  <---

-rwxr-xr-x. 1 woogon woogon 46892664 Oct  3 20:43 main/ndown.exe
-rwxr-xr-x. 1 woogon woogon 47011488 Oct  3 20:43 main/real.exe
-rwxr-xr-x. 1 woogon woogon 46167896 Oct  3 20:43 main/tc.exe
-rwxr-xr-x. 1 woogon woogon 55102440 Oct  3 20:42 main/wrf.exe
```

- 빌드 시간: 약 19분 (`-j 2`)
- 오류(`Error`, `undefined reference`, `cannot find`, `fatal error`): 없음
- `warning`: 103건. 실행파일 생성에는 영향을 주지 않았으며 fatal/link 오류는 없었다. 실제 test run을 통해 최종 동작 검증 예정.

**상태: compile 완료, 실제 입력자료 test run을 통한 최종 동작 검증 미완료 (2026-10-03)**

---

## 10. WRF 실행파일 라이브러리 연결 확인

실행파일이 생성되었더라도 실행 시 필요한 공유 라이브러리를 찾을 수 있는지 별도로 확인한다.

```bash
cd /home/woogon/CMAQ_MODEL/WRFV4.5.1
ldd main/wrf.exe | grep "not found"
ldd main/wrf.exe | grep -E "netcdf|hdf5|mpi"
```

확인 결과:

- `not found`: 없음
- netCDF / HDF5: 이번 프로젝트에서 설치한 라이브러리에 연결됨

```text
libnetcdff.so.7   => /home/woogon/CMAQ_MODEL/libs/netCDF-Fortran-4.6.2/lib/libnetcdff.so.7
libnetcdf.so.22   => /home/woogon/CMAQ_MODEL/libs/netCDF-C-4.9.3/lib/libnetcdf.so.22
libhdf5_hl.so.310 => /home/woogon/CMAQ_MODEL/libs/HDF5-1.14.6/lib/libhdf5_hl.so.310
libhdf5.so.310    => /home/woogon/CMAQ_MODEL/libs/HDF5-1.14.6/lib/libhdf5.so.310
libmpi.so.40      => /usr/lib64/openmpi/lib/libmpi.so.40
```

**상태: WRF 4.5.1 설치·컴파일·동적 라이브러리 연결 확인 완료, 실제 입력자료 실행검증 미완료**

---

## 11. WPS 4.5 설치

### 11.1 소스 다운로드

WPS는 하위 모듈이 없으므로 GitHub 태그 압축파일을 그대로 사용한다. 다른 압축파일과 구분되도록 저장 이름을 지정한다.

```bash
cd /home/woogon/CMAQ_MODEL/src
wget -O WPS-4.5.tar.gz https://github.com/wrf-model/WPS/archive/refs/tags/v4.5.tar.gz
ls -lh
```

### 11.2 프로젝트 루트에 압축 해제

```bash
cd /home/woogon/CMAQ_MODEL
tar -xzf src/WPS-4.5.tar.gz
ls
```

확인 결과:

```text
libs  src  WPS-4.5  WRFV4.5.1
```

### 11.3 configure

WPS는 기본적으로 바로 위 디렉터리의 `WRF`, `WRFV3` 등 정해진 이름의 폴더에서 컴파일된 WRF를 찾는다. 이번 구축의 폴더명은 `WRFV4.5.1`이므로 `WRF_DIR`로 위치를 지정한다.

```bash
cd /home/woogon/CMAQ_MODEL/WPS-4.5
LC_ALL=C WRF_DIR=/home/woogon/CMAQ_MODEL/WRFV4.5.1 ./configure
```

선택값:

| 질문 | 입력 | 의미 |
|---|---|---|
| `Enter selection [1-40]` | `1` | Linux x86_64, gfortran (serial), GRIB2 지원 |

> WPS는 serial로 빌드한다. WRF(dmpar)와 WPS(serial) 조합은 WRF 공식 튜토리얼의 기본 조합이다. `NO_GRIB2`가 붙은 번호는 GRIB2 자료(GFS 등)를 읽지 못하므로 선택하지 않는다.

configure 출력:

```text
Will use NETCDF in dir: /home/woogon/CMAQ_MODEL/libs/netCDF-WRF
Using WRF I/O library in WRF build identified by $WRF_DIR: /home/woogon/CMAQ_MODEL/WRFV4.5.1
Found Jasper environment variables for GRIB2 support...
  $JASPERLIB = /home/woogon/CMAQ_MODEL/libs/grib2/lib
  $JASPERINC = /home/woogon/CMAQ_MODEL/libs/grib2/include
...
Configuration successful. To build the WPS, type: compile

Testing for NetCDF, C and Fortran compiler

This installation NetCDF is 64-bit
C compiler is 64-bit
Fortran compiler is 64-bit
```

`configure.wps` 확인:

```bash
ls -l configure.wps
grep -n "Settings for" configure.wps
grep -n -E "^(WRF_DIR|COMPRESSION_LIBS|COMPRESSION_INC|SFC|SCC)" configure.wps
```

| 항목 | 값 |
|---|---|
| `WRF_DIR` | `/home/woogon/CMAQ_MODEL/WRFV4.5.1` |
| `COMPRESSION_LIBS` | `-L/home/woogon/CMAQ_MODEL/libs/grib2/lib -ljasper -lpng -lz` |
| `COMPRESSION_INC` | `-I/home/woogon/CMAQ_MODEL/libs/grib2/include` |
| `SFC` / `SCC` | `gfortran` / `gcc` |

> `configure.wps`에는 `COMPRESSION_LIBS`, `COMPRESSION_INC`가 두 번씩 나온다. 앞의 것은 "아래에서 채우라"는 빈 자리이고 실제 값은 뒤의 줄에 들어 있다.

### 11.4 문제 6: configure 선택 목록이 표시되지 않음

증상: `| tee log.configure`를 붙여 실행하자 아래 두 줄 이후 화면이 멈춘 것처럼 보였다.

```text
Will use NETCDF in dir: /home/woogon/CMAQ_MODEL/libs/netCDF-WRF
Using WRF I/O library in WRF build identified by $WRF_DIR: /home/woogon/CMAQ_MODEL/WRFV4.5.1
```

원인: WPS configure는 JasPer 확인 메시지와 선택 목록을 perl 스크립트(`arch/Config.pl`)로 출력한다. 출력이 파이프(`| tee`)로 넘어가면 perl이 출력을 모아 두었다가 한꺼번에 내보내므로, 목록이 화면에 나오지 않은 상태에서 번호 입력을 기다리게 된다.

해결: Ctrl+C로 중단한 뒤 `tee` 없이 실행했다. 로그를 남겨야 할 때는 실제 터미널처럼 동작하는 `script`를 사용한다.

```bash
script -q -c "LC_ALL=C WRF_DIR=/home/woogon/CMAQ_MODEL/WRFV4.5.1 ./configure" log.configure
```

> 화면이 점선(`-----`)에서 멈춘 것처럼 보이면 Enter를 한 번 누른다. 입력 대기 중이었다면 `Invalid response (0)`과 함께 목록이 다시 출력된다.

### 11.5 문제 7: geogrid / metgrid 링크 실패 (`MPI_LIB` 환경변수)

첫 compile:

```bash
LC_ALL=C ./compile 2>&1 | tee log.compile
```

결과: `ungrib.exe`만 생성되고 `geogrid.exe`, `metgrid.exe`는 생성되지 않았다.

```text
gfortran -o geogrid.exe ... -lnetcdff -lnetcdf \
	/usr/lib64/openmpi/lib
/usr/bin/ld: error: /usr/lib64/openmpi/lib: read: Is a directory
collect2: error: ld returned 1 exit status
make[1]: [Makefile:13: geogrid.exe] Error 1 (ignored)
```

원인:

- WPS의 `geogrid/src/Makefile`, `metgrid/src/Makefile`은 링크 명령 끝에 `$(MPI_LIB)`를 붙인다. serial 빌드에서는 이 값이 비어 있어야 한다.
- 8.5에서 `~/.bashrc`에 등록한 `module load mpi/openmpi-x86_64`가 같은 이름의 환경변수 `MPI_LIB=/usr/lib64/openmpi/lib`를 설정한다.
- make가 이 환경변수를 Makefile 변수로 사용하면서 디렉터리 경로가 링크 대상으로 들어갔다.
- `ungrib`의 링크 명령에는 `$(MPI_LIB)`가 없어 영향을 받지 않았다.

해결: compile 명령에만 `MPI_LIB`를 빈 값으로 지정한다. WRF 실행에 필요한 OpenMPI 설정은 그대로 유지된다. configure는 다시 하지 않는다.

```bash
cd /home/woogon/CMAQ_MODEL/WPS-4.5
./clean
ls -l configure.wps
LC_ALL=C MPI_LIB= ./compile 2>&1 | tee log.compile
```

> `./clean -a`는 `configure.wps`까지 삭제하므로 사용하지 않는다.

### 11.6 compile 결과 확인

```bash
ls -l *.exe
grep -n "Is a directory" log.compile
grep -n -i -E "error|undefined reference|cannot find" log.compile
ldd geogrid/src/geogrid.exe ungrib/src/ungrib.exe metgrid/src/metgrid.exe | grep "not found"
```

확인 결과:

```text
geogrid.exe -> geogrid/src/geogrid.exe
metgrid.exe -> metgrid/src/metgrid.exe
ungrib.exe -> ungrib/src/ungrib.exe
```

- 재컴파일 로그에서 오류 메시지 없음
- geogrid 링크 명령 끝의 `/usr/lib64/openmpi/lib` 제거 확인
- `ungrib.exe`는 `-L/home/woogon/CMAQ_MODEL/libs/grib2/lib -ljasper -lpng -lz`로 GRIB2 라이브러리 연결

**상태: WPS 4.5 설치·컴파일·동적 라이브러리 연결 확인 완료, 실제 입력자료 실행검증 미완료 (2026-10-03)**

---

## 12. 환경변수 등록 현황

이번 단계에서 `~/.bashrc`에 추가한 내용:

```bash
# netCDF for WRF (C+Fortran combined)
export NETCDF=$CMAQ_LIBS/netCDF-WRF
export PATH=$NETCDF/bin:$PATH

# GRIB2 libraries for WPS (libpng, JasPer)
export JASPERLIB=$CMAQ_LIBS/grib2/lib
export JASPERINC=$CMAQ_LIBS/grib2/include
export LD_LIBRARY_PATH=$CMAQ_LIBS/grib2/lib:$LD_LIBRARY_PATH

# HDF5 path for WRF configure (adds -L to DEP_LIB_PATH)
export HDF5_PATH=$CMAQ_LIBS/HDF5-1.14.6

# OpenMPI (Rocky package, Environment Modules)
source /etc/profile.d/modules.sh
module load mpi/openmpi-x86_64
```

백업 파일:

```text
~/.bashrc.bak_before_wrf
~/.bashrc.bak_before_grib2
~/.bashrc.bak_before_hdf5path
~/.bashrc.bak_before_mpi
```

> `$CMAQ_LIBS`는 공통 라이브러리 단계에서 등록한 변수(`/home/woogon/CMAQ_MODEL/libs`)이므로, 위 설정은 그 아래에 위치해야 한다.

> OpenMPI module은 `MPI_LIB` 등의 환경변수도 함께 설정한다. 다른 모델의 Makefile이 같은 이름의 변수를 사용하는 경우 11.5와 같은 문제가 생길 수 있다.

명령 실행 시에만 적용하는 설정(`.bashrc`에 등록하지 않음):

| 설정 | 적용 대상 | 이유 |
|---|---|---|
| `LC_ALL=C` | WRF/WPS configure, compile | 한국어 로케일 출력 파싱 오류 방지 (8.3) |
| `WRF_DIR=/home/woogon/CMAQ_MODEL/WRFV4.5.1` | WPS configure | WRF 폴더명이 기본 탐색 이름과 다름 (11.3) |
| `MPI_LIB=` | WPS compile | OpenMPI module의 `MPI_LIB`가 링크 명령에 들어가는 것을 방지 (11.5) |

---

## 13. 추가 설치 패키지

| 패키지 | 용도 | 비고 |
|---|---|---|
| `file` | WRF configure의 64-bit 점검 | 이미 설치되어 있었음 |
| `libtirpc-devel` | `rpc/types.h` 제공 | 설치했으나 WRF rpc 테스트는 계속 실패, 8.6의 조치로 대체 |
| `tcsh` | WRF `compile` 스크립트 실행(csh) | 9.1 |

---

## 14. 문제 해결 요약

| 번호 | 단계 | 증상 | 원인 | 해결 |
|---|---|---|---|---|
| 1 | 사전 점검 | `nc-config: command not found` | netCDF `bin`이 `PATH`에 없음, C/Fortran 분리 설치 | `libs/netCDF-WRF` 통합 링크, `NETCDF`/`PATH` 등록 (5장) |
| 2 | WRF configure | `One of compilers testing failed!` | 한국어 로케일에서 `type` 출력 파싱 실패 | `LC_ALL=C`로 실행 (8.3) |
| 3 | WRF configure | netCDF4 테스트 실패, `configure.wrf` 삭제 | `DEP_LIB_PATH`에 HDF5 `lib` 경로 누락 | `HDF5_PATH` 환경변수 등록 (8.4) |
| 4 | WRF configure | `mpicc: command not found` | OpenMPI module이 `.bashrc`에 미등록 | `module load mpi/openmpi-x86_64` 등록 (8.5) |
| 5 | WRF configure | `rpc/types.h` 경고 | Rocky 9에 Sun RPC 헤더 없음, tirpc 헤더 경로 불일치 | `share/landread.c` ← `landread.c.dist` (현재 basic nesting에서 허용, 향후 moving nest 사용 시 RPC/TIRPC 및 원본 사용 여부 재검토; 8.6) |
| 6 | WRF compile | `/bin/csh: 잘못된 인터프리터` | csh 미설치 | `tcsh` 설치 (9.1) |
| 7 | WPS configure | 선택 목록이 표시되지 않음 | perl 출력이 파이프(`tee`)에서 버퍼링됨 | `tee` 없이 실행 또는 `script -q -c` 사용 (11.4) |
| 8 | WPS compile | geogrid/metgrid `Is a directory` 링크 오류 | OpenMPI module의 `MPI_LIB` 환경변수가 Makefile에 유입 | `MPI_LIB=`로 비워서 compile (11.5) |

---

## 15. 완료 현황

| 구성요소 | 버전 | 위치 | 실행파일 | 상태 |
|---|---|---|---|---|
| libpng | 1.2.50 | `libs/grib2` | - | 설치 완료 |
| JasPer | 1.900.1 | `libs/grib2` | - | 설치 완료 |
| netCDF 통합 링크 | 4.9.3 / 4.6.2 | `libs/netCDF-WRF` | - | 구성 완료 |
| WRF | 4.5.1 | `WRFV4.5.1` | `wrf.exe`, `real.exe`, `ndown.exe`, `tc.exe` | 설치·컴파일·동적 라이브러리 연결 확인 완료, 실제 입력자료 실행검증 미완료 |
| WPS | 4.5 | `WPS-4.5` | `geogrid.exe`, `ungrib.exe`, `metgrid.exe` | 설치·컴파일·동적 라이브러리 연결 확인 완료, 실제 입력자료 실행검증 미완료 |

이로써 Phase 3(WRF/WPS)의 **설치·컴파일·동적 라이브러리 연결 확인**을 완료했다. **실제 입력자료 실행검증은 미완료**이며, 지형자료 준비와 테스트 사례 실행은 아직 수행하지 않았다. Phase 3 전체 완료(실행 검증)를 뜻하지 않는다.

## 16. 다음 단계

1. 정적 지형자료(WPS_GEOG, 고해상도 필수 자료) 다운로드 및 압축 해제. 저장 위치는 기본계획 §4.2의 모델/자료 분리 원칙에 따라 결정
2. 테스트 사례용 기상자료(GFS 또는 ERA5) 준비
3. 사례별 실행폴더 구성: 설치 폴더가 아닌 별도 폴더에서 실행(기본계획 §19)
4. `geogrid.exe` → `ungrib.exe` → `metgrid.exe` → `real.exe` → `wrf.exe` 순서로 실제 입력자료 테스트 실행. `ungrib.exe`의 실제 GRIB2 입력 및 `FILE:*` 중간파일 생성과 WRF test run의 정상 완료·출력(`wrfout`)을 확인하여 최종 동작을 검증하고, 성공 시 Phase 3 실행 검증 완료로 기록
5. 실제 입력자료 실행검증 완료 후 WRF 출력(`wrfout`)을 MCIP 입력으로 사용(Phase 4)

## 17. 검토 근거 및 관련 문서

- [CMAQ 5.5 WRF-CMAQ 호환 WRF 버전](https://github.com/USEPA/CMAQ/blob/main/DOCS/Users_Guide/CMAQ_UG_ch13_WRF-CMAQ.md)
- [WRF v4.5.1 릴리스](https://github.com/wrf-model/WRF/releases/tag/v4.5.1)
- [WPS v4.5 소스](https://github.com/wrf-model/WPS/tree/v4.5)
- [WRF User's Guide: Compiling](https://www2.mmm.ucar.edu/wrf/users/wrf_users_guide/build/html/compiling.html)
- [WRF online compilation tutorial](https://www2.mmm.ucar.edu/wrf/OnLineTutorial/compilation_tutorial.php)
- WRF 4.5.1 `configure` 스크립트(컴파일러 64-bit 테스트, `HDF5_PATH` 처리, rpc/netCDF4 테스트) 및 `Makefile`의 `nc4_test`/`rpc_test` 대상
- WPS 4.5 `configure`, `arch/Config.pl`(선택 목록 출력), `geogrid/src/Makefile`(`$(MPI_LIB)` 사용)
- [구축 기본계획 및 Phase 현황](../planning/00_CMAQ_Project_Master_Plan.md)
- [공통 라이브러리 구축 기록](../libraries/Common_Libraries_Installation_Guide.md)
- [GNU Compiler 및 OpenMPI 설치 가이드](../compiler/GNU_Compiler_OpenMPI_Installation_Guide.md)
