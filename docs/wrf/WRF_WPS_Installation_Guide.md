# CMAQ 모델링 시스템 WRF/WPS 구축 가이드

**다음 CASE 실행 명령을 보려면 [입력파일 준비와 프로그램별 실행 순서](#case-run)로 이동한다.** WPS/WRF namelist 복사·편집, geogrid, ungrib, metgrid, real.exe, wrf.exe 명령을 §14에 순서대로 정리했다.

## 1. 목적
Rocky Linux 기반 CMAQ 통합 대기질 모델링 시스템의 Phase 3(WRF/WPS) 설치·자료 준비·사례 실행·오류 해결 절차를 하나의 문서로 기록한다.

이 문서는 실제 구축 과정에서 발생한 문제를 모두 해결한 뒤, **처음부터 오류 없이 따라 할 수 있는 순서**로 재구성한 것이다. 각 단계의 `> 참고` 상자에는 해당 조치가 필요한 이유와, 생략했을 때 나타나는 오류를 적었다. 실제 구축 중에 겪은 문제의 경위는 [부록 A](#부록-a-구축-중-발생한-문제-기록)에 따로 정리했다.

설치 순서:

```text
4장  공통 실행 규칙 확인
  ↓
5장  시스템 패키지 설치 (tcsh 등)
  ↓
6장  OpenMPI 환경 등록
  ↓
7장  netCDF 통합 링크 디렉터리 + HDF5 경로 등록
  ↓
8장  GRIB2 라이브러리 (libpng, JasPer)
  ↓
9장  설치 전 환경 최종 점검
  ↓
10장 WRF 4.5.1 (다운로드 → landread 교체 → configure → compile → 확인)
  ↓
11장 WPS 4.5   (다운로드 → configure → compile → 확인)
```

현재 상태(2026-10-08 사용자 제공 실행 기록 기준): **설치·컴파일 및 사례 실행 성공. TEST_20260901의 WPS·real.exe 성공, WRF dmpar 4코어 오류 없이 실행 중이며 wrfout 결과파일 생성 확인(사용자 확인)**. 설치는 아래 절차, 자료 준비·namelist·실행·출력 확인은 이 문서 §14를 따른다.

## 2. 구축 환경

- OS: Rocky Linux 9.8 (Blue Onyx), x86_64, **시스템 언어 한국어**
- 사용자: `woogon`
- 프로젝트 루트: `/home/woogon/CMAQ_MODEL`
- CPU 코어: 4 / 메모리: 약 7.2 GB / `/home` 여유 공간: 약 494 GB
- GCC / GFortran: 11.5.0
- OpenMPI: 4.1.1 (Rocky Linux 패키지, Environment Modules로 활성화)
- 공통 라이브러리: HDF5 1.14.6, netCDF-C 4.9.3, netCDF-Fortran 4.6.2, I/O API 3.2-20200828

선행 문서:

- [GNU Compiler 및 OpenMPI 설치 가이드](../compiler/GNU_Compiler_OpenMPI_Installation_Guide.md)
- [공통 라이브러리 구축 기록](../libraries/Common_Libraries_Installation_Guide.md)

이 문서는 위 두 문서의 설치가 끝나 있고, `~/.bashrc`에 `CMAQ_LIBS=/home/woogon/CMAQ_MODEL/libs`와 netCDF/HDF5의 `LD_LIBRARY_PATH`가 등록되어 있다고 가정한다.

디렉터리 구조:

[구축 기본계획](../planning/00_CMAQ_Project_Master_Plan.md) §4.2에 따라 모델 본체는 프로젝트 루트 아래 별도 폴더에 두고, 폴더명에 버전을 표시한다. `src/`에는 원본 압축파일과 라이브러리 소스만 보관한다.

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

---

실제 경로와 역할은 이 문서 §2와 기본계획 §4.2를 기준으로 한다. CASE 하위 폴더 존재는 MCIP/CMAQ 실행 완료를 의미하지 않는다.

## 3. 버전 확정

모델 버전은 CMAQ를 먼저 확정하고 나머지를 CMAQ 호환성에 맞춘다(기본계획 §3.5).

| 구성요소 | 버전 | 근거 |
|---|---|---|
| WRF | 4.5.1 (태그 `v4.5.1`) | 결합형 WRF-CMAQv5.5의 공식 호환범위(WRF 4.4~4.5.1)의 상한 |
| WPS | 4.5 (태그 `v4.5`) | WRF 4.5.x와 짝을 이루는 버전 |
| libpng | 1.2.50 | WRF 공식 컴파일 튜토리얼 버전 |
| JasPer | 1.900.1 | WRF 공식 컴파일 튜토리얼 버전 |

- 분리 실행(WRF → MCIP → CMAQ)은 CMAQ 5.5의 MCIP로 처리한다.
- 향후 결합 실행(WRF-CMAQ)으로 확장할 때 WRF를 재설치할 필요가 없다.
- CMAS 포럼에는 WRF 4.5.2로 결합 모델을 빌드했을 때 benchmark가 중단되고, WRF 4.5.1로 재빌드하자 정상 실행된 사례가 보고되어 있다.

---

## 4. 공통 실행 규칙

이 문서의 모든 configure, compile 명령은 아래 규칙을 따른다.

### 4.1 `LC_ALL=C`를 앞에 붙인다

```bash
LC_ALL=C ./configure
LC_ALL=C ./compile ...
```

`LC_ALL=C`는 **그 명령 하나만** 영어 환경으로 실행한다. 시스템 언어 설정은 바뀌지 않는다.

> **참고: 생략하면** WRF configure 마지막에 `One of compilers testing failed!`가 출력되고 configure가 중간에 종료된다. WRF configure는 `type gcc` 명령의 영어 출력(`gcc is /usr/bin/gcc`)에서 마지막 단어를 컴파일러 경로로 사용하는데, 한국어 환경에서는 한국어 문장이 출력되어 경로를 얻지 못하기 때문이다. 이때 이후 점검(gfortran 호환 옵션, netCDF4 점검 등)이 모두 생략된 불완전한 `configure.wrf`가 남으므로 무시하고 진행하면 안 된다.

### 4.2 화면 출력을 파일로 남긴다

```bash
명령어 2>&1 | tee 로그파일이름
```

화면에 보여주면서 동시에 파일에 저장한다. `2>&1`은 오류 메시지까지 함께 저장한다.

> **참고: 예외** WRF 사례 실행은 별도 `wrf.log` 없이 `rsl.error.*` / `rsl.out.*`를 사용한다. WPS configure처럼 **번호 입력을 받는 명령**에는 `tee`를 쓰지 않는다(11.3). 로그가 꼭 필요하면 `script -q -c "명령어" 로그파일이름`을 사용한다.

### 4.3 configure 이후 `configure.wrf`는 직접 수정하지 않는다

`./configure`를 다시 실행하면 `configure.wrf`가 새로 만들어져 직접 수정한 내용이 사라진다. 이 문서의 절차는 필요한 설정을 모두 환경변수로 미리 준비하므로 `configure.wrf`를 수정할 필요가 없다.

### 4.4 비밀번호 입력

`sudo` 명령에서 비밀번호를 물으면 woogon 계정의 로그인 비밀번호를 입력한다. 입력하는 동안 화면에 글자가 표시되지 않는 것은 정상이다.

---

## 5. 시스템 패키지 설치

### 5.1 설치

어느 폴더에서든 실행할 수 있다.

```bash
sudo dnf install -y tcsh file
```

| 패키지 | 용도 |
|---|---|
| `tcsh` | WRF의 `compile` 스크립트를 실행하는 csh 제공 |
| `file` | WRF/WPS configure의 64-bit 점검에 사용 |

> **참고: tcsh를 생략하면** WRF compile 시작 시 `bash: ./compile: /bin/csh: 잘못된 인터프리터: 그런 파일이나 디렉터리가 없습니다` 오류가 나고 컴파일이 시작되지 않는다.

### 5.2 확인

```bash
ls -l /bin/csh
which csh tcsh perl m4 make file
rpm -q zlib-devel
```

정상 결과:

- `/bin/csh -> tcsh` 형태의 바로가기가 보인다.
- `which` 결과 6줄 모두 경로가 나온다. `no ... in` 메시지가 하나라도 있으면 해당 도구를 먼저 설치한다.
- `zlib-devel-1.2.11-...` 패키지 이름이 나온다(libpng 빌드에 필요).

---

## 6. OpenMPI 환경 등록

### 6.1 `.bashrc`에 module load 등록

```bash
cd ~
cp ~/.bashrc ~/.bashrc.bak_before_wrf
```

```bash
cat >> ~/.bashrc <<'EOF'

# OpenMPI (Rocky package, Environment Modules)
source /etc/profile.d/modules.sh
module load mpi/openmpi-x86_64
EOF
```

`cat >> ~/.bashrc <<'EOF'` 부터 마지막 `EOF` 줄까지를 **한 번에 복사해 붙여넣고** Enter를 누른다. 그 사이의 내용이 `.bashrc` 끝에 그대로 추가된다.

> **참고:** `>>`(꺾쇠 두 개)는 파일 끝에 추가한다. `>`(하나)를 쓰면 `.bashrc` 내용이 전부 지워지므로 주의한다. 첫 `'EOF'`의 작은따옴표는 `$` 기호가 바뀌지 않고 그대로 기록되게 한다.

> **참고: 생략하면** 새 터미널에서 `mpicc`, `mpif90`을 찾지 못한다. WRF configure 중 netCDF4 테스트가 `mpicc: command not found`로 실패하고 `!!! configure.wrf has been REMOVED !!!`가 출력된다. dmpar 빌드는 WRF 전체를 `mpif90`/`mpicc`로 컴파일하므로 compile도 불가능하다.

### 6.2 적용 및 확인

```bash
source ~/.bashrc
which mpicc mpif90
mpicc --showme:command
mpif90 --showme:command
```

정상 결과:

```text
/usr/lib64/openmpi/bin/mpicc
/usr/lib64/openmpi/bin/mpif90
gcc
gfortran
```

> **참고:** OpenMPI module은 `MPI_LIB=/usr/lib64/openmpi/lib` 등의 환경변수도 함께 설정한다. 이 변수는 WPS compile에 영향을 주므로 11.5에서 처리한다.

---

## 7. netCDF 통합 링크 디렉터리 및 HDF5 경로

### 7.1 필요성

WRF는 `NETCDF` 환경변수 **하나의 폴더**에서 netCDF-C와 netCDF-Fortran의 `bin`, `include`, `lib`를 모두 찾는다. 공통 라이브러리 단계에서 두 라이브러리를 별도 폴더에 설치했으므로, 원본은 그대로 두고 심볼릭 링크(바로가기)로 묶은 폴더를 만든다. CMAQ는 C와 Fortran 경로를 따로 지정하므로 기존 구조를 그대로 사용한다(기본계획 §3.5).

### 7.2 통합 디렉터리 생성

```bash
cd /home/woogon/CMAQ_MODEL/libs
mkdir -p netCDF-WRF/bin netCDF-WRF/include netCDF-WRF/lib
```

### 7.3 심볼릭 링크 생성

현재 위치(`libs`)에서 한 줄씩 실행한다.

```bash
ln -s /home/woogon/CMAQ_MODEL/libs/netCDF-C-4.9.3/bin/* netCDF-WRF/bin/
ln -s /home/woogon/CMAQ_MODEL/libs/netCDF-Fortran-4.6.2/bin/* netCDF-WRF/bin/

ln -s /home/woogon/CMAQ_MODEL/libs/netCDF-C-4.9.3/include/* netCDF-WRF/include/
ln -s /home/woogon/CMAQ_MODEL/libs/netCDF-Fortran-4.6.2/include/* netCDF-WRF/include/

ln -s /home/woogon/CMAQ_MODEL/libs/netCDF-C-4.9.3/lib/libnetcdf* netCDF-WRF/lib/
ln -s /home/woogon/CMAQ_MODEL/libs/netCDF-Fortran-4.6.2/lib/libnetcdf* netCDF-WRF/lib/
```

> **참고:** `lib/`는 `libnetcdf*` 파일만 연결한다. 두 라이브러리에 같은 이름의 하위 폴더(`pkgconfig` 등)가 있어서 전체를 연결하면 `File exists` 충돌이 난다.

### 7.4 링크 확인

```bash
ls netCDF-WRF/bin
ls netCDF-WRF/lib
ls netCDF-WRF/include
```

정상 결과(요약):

```text
bin     : nc-config nc4print nccopy ncdump ncgen ncgen3 nf-config
lib     : libnetcdf.a libnetcdf.so libnetcdf.so.22 ... libnetcdff.a libnetcdff.so libnetcdff.so.7 ...
include : netcdf.h netcdf.inc netcdf.mod typesizes.mod netcdf_meta.h ...
```

C용(`nc-config`, `libnetcdf.so`, `netcdf.h`)과 Fortran용(`nf-config`, `libnetcdff.so`, `netcdf.mod`)이 **함께** 있어야 한다.

### 7.5 환경변수 등록

```bash
cd ~
cat >> ~/.bashrc <<'EOF'

# netCDF for WRF (C+Fortran combined)
export NETCDF=$CMAQ_LIBS/netCDF-WRF
export PATH=$NETCDF/bin:$PATH

# HDF5 path for WRF configure (adds -L to DEP_LIB_PATH)
export HDF5_PATH=$CMAQ_LIBS/HDF5-1.14.6
EOF
```

> **참고: `HDF5_PATH`를 생략하면** `configure.wrf`의 `DEP_LIB_PATH`에 HDF5 `lib` 경로가 빠진다. WRF configure의 netCDF4 테스트가 HDF5를 찾지 못해 `NETCDF4 IO features are requested, but this installation of NetCDF ... DOES NOT support these IO features`와 함께 `configure.wrf`가 삭제된다. WRF configure는 `HDF5_PATH`가 있으면 `-L$HDF5_PATH/lib`를 자동으로 추가한다.

> **참고:** 변수명은 반드시 `HDF5_PATH`로 한다. `HDF5`라는 변수는 WRF의 다른 I/O 기능을 켜는 용도이므로 설정하지 않는다. 공통 라이브러리 빌드 때 남은 변수가 있으면 WRF 빌드 shell에서 아래 명령으로 해제한다.

```bash
unset HDF5
```

### 7.6 적용 및 확인

```bash
source ~/.bashrc
echo $NETCDF
echo $HDF5_PATH
which nc-config nf-config
nc-config --version
nf-config --version
nf-config --has-nc4
```

정상 결과:

```text
/home/woogon/CMAQ_MODEL/libs/netCDF-WRF
/home/woogon/CMAQ_MODEL/libs/HDF5-1.14.6
/home/woogon/CMAQ_MODEL/libs/netCDF-WRF/bin/nc-config
/home/woogon/CMAQ_MODEL/libs/netCDF-WRF/bin/nf-config
netCDF 4.9.3
netCDF-Fortran 4.6.2
yes
```

---

## 8. GRIB2 라이브러리 설치 (libpng, JasPer)

### 8.1 필요성

WPS의 `ungrib`이 GRIB2 형식 기상자료(GFS 등)의 압축 데이터를 풀 때 libpng(PNG 압축)와 JasPer(JPEG2000 압축)를 사용한다.

| 구분 | 경로 |
|---|---|
| 소스 | `/home/woogon/CMAQ_MODEL/src/grib2` |
| 설치 | `/home/woogon/CMAQ_MODEL/libs/grib2` |

> **참고:** WPS 4.4 이상은 `--build-grib2-libs` 옵션으로 WPS 내부에 빌드할 수도 있으나, 구조를 명확히 하기 위해 `libs/grib2`에 별도 설치한다.

### 8.2 소스 다운로드

```bash
mkdir -p /home/woogon/CMAQ_MODEL/src/grib2
cd /home/woogon/CMAQ_MODEL/src/grib2
wget https://www2.mmm.ucar.edu/wrf/OnLineTutorial/compile_tutorial/tar_files/libpng-1.2.50.tar.gz
wget https://www2.mmm.ucar.edu/wrf/OnLineTutorial/compile_tutorial/tar_files/jasper-1.900.1.tar.gz
ls -lh
```

### 8.3 libpng 1.2.50 설치

```bash
cd /home/woogon/CMAQ_MODEL/src/grib2
tar -xzf libpng-1.2.50.tar.gz
cd libpng-1.2.50
./configure --prefix=/home/woogon/CMAQ_MODEL/libs/grib2
make
make install
```

`configure`의 마지막과 `make`의 마지막에 `error`가 없는지 확인한다. `warning`은 무시해도 된다.

### 8.4 JasPer 1.900.1 설치

```bash
cd /home/woogon/CMAQ_MODEL/src/grib2
tar -xzf jasper-1.900.1.tar.gz
cd jasper-1.900.1
./configure --prefix=/home/woogon/CMAQ_MODEL/libs/grib2
make
make install
```

### 8.5 설치 확인

```bash
ls /home/woogon/CMAQ_MODEL/libs/grib2/lib
ls /home/woogon/CMAQ_MODEL/libs/grib2/include/jasper
```

정상 결과(요약):

```text
lib           : libjasper.a libjasper.la libpng.a libpng.so libpng12.a libpng12.so ... pkgconfig
include/jasper: jasper.h jas_cm.h jas_config.h jas_image.h jas_stream.h ...
```

> **참고:** JasPer 1.900.1은 기본 설정에서 정적 라이브러리(`libjasper.a`)만 만든다. `libjasper.so`가 없어도 정상이다. WPS는 헤더를 `jasper/jasper.h` 경로로 찾으므로 `include/jasper/` 구조가 필요하다.

### 8.6 환경변수 등록

```bash
cd ~
cat >> ~/.bashrc <<'EOF'

# GRIB2 libraries for WPS (libpng, JasPer)
export JASPERLIB=$CMAQ_LIBS/grib2/lib
export JASPERINC=$CMAQ_LIBS/grib2/include
export LD_LIBRARY_PATH=$CMAQ_LIBS/grib2/lib:$LD_LIBRARY_PATH
EOF
source ~/.bashrc
```

---

## 9. 설치 전 환경 최종 점검

WRF 설치를 시작하기 전에 **새 터미널을 열어** 아래를 확인한다. 새 터미널에서 확인해야 `.bashrc` 설정이 자동으로 적용되는지 알 수 있다.

```bash
echo $NETCDF
echo $HDF5_PATH
echo $JASPERLIB
echo $JASPERINC
which mpicc mpif90 nc-config nf-config csh
```

정상 결과:

```text
/home/woogon/CMAQ_MODEL/libs/netCDF-WRF
/home/woogon/CMAQ_MODEL/libs/HDF5-1.14.6
/home/woogon/CMAQ_MODEL/libs/grib2/lib
/home/woogon/CMAQ_MODEL/libs/grib2/include
/usr/lib64/openmpi/bin/mpicc
/usr/lib64/openmpi/bin/mpif90
/home/woogon/CMAQ_MODEL/libs/netCDF-WRF/bin/nc-config
/home/woogon/CMAQ_MODEL/libs/netCDF-WRF/bin/nf-config
/usr/bin/csh
```

하나라도 비어 있거나 다르면 해당 장(5~8장)으로 돌아가 다시 확인한다.

---

## 10. WRF 4.5.1 설치

### 10.1 소스 다운로드

GitHub **릴리스 파일**을 사용한다.

```bash
cd /home/woogon/CMAQ_MODEL/src
wget https://github.com/wrf-model/WRF/releases/download/v4.5.1/v4.5.1.tar.gz
```

> **참고:** 같은 릴리스 페이지의 "Source code (tar.gz)" 자동 압축파일은 NoahMP 등 하위 모듈이 빠져 있어 컴파일 오류가 난다. 반드시 위 주소의 `v4.5.1.tar.gz`를 사용한다.

### 10.2 프로젝트 루트에 압축 해제

```bash
cd /home/woogon/CMAQ_MODEL
tar -xzf src/v4.5.1.tar.gz
ls
```

정상 결과: `libs  src  WRFV4.5.1`

### 10.3 `share/landread.c` 교체

```bash
cd /home/woogon/CMAQ_MODEL/WRFV4.5.1/share
cp landread.c landread.c.orig
cp landread.c.dist landread.c
ls landread*
```

정상 결과: `landread.c  landread.c.dist  landread.c.orig`

> **참고: 이유** Rocky Linux 9(glibc 2.34 이상)에는 Sun RPC 헤더(`rpc/types.h`)가 기본 포함되어 있지 않다. 이 경우 `landread.c`의 XDR 관련 코드가 컴파일되지 않는다. `landread.c.dist`는 이 기능을 비워 둔 WRF 제공 대체 파일이다. 해당 코드는 **moving nest(이동 격자)** 의 고해상도 지형·토지이용 입력에만 쓰이며, 현재 구축은 moving nest를 사용하지 않고 basic nesting만 사용하므로 `landread.c.dist`로 대체한다. 향후 moving nest 사용 시 RPC/TIRPC 설정 및 원본 `landread.c` 사용 여부를 재검토해야 한다.

> **참고:** `libtirpc-devel` 패키지를 설치해도 WRF의 rpc 테스트가 `-I/usr/include/tirpc` 없이 컴파일하므로 `netconfig.h`를 찾지 못해 실패한다. 따라서 이 교체 방식을 사용한다.

### 10.4 configure

```bash
cd /home/woogon/CMAQ_MODEL/WRFV4.5.1
LC_ALL=C ./configure 2>&1 | tee log.configure
```

선택값:

| 질문 | 입력 | 의미 |
|---|---|---|
| `Enter selection [1-79]` | `34` | GNU (gfortran/gcc), dmpar (MPI 병렬) |
| `Compile for nesting?` | `1` | basic nesting |

> **참고:** 입력 전에 목록의 `GNU (gfortran/gcc)` 줄에서 34번이 `(dmpar)` 위치에 있는지 확인한다.

정상 결과(`log.configure` 주요 내용):

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

> **참고: 이 경고는 정상이다.** 10.3에서 `landread.c`를 이미 교체했으므로 무시한다.
>
> ```text
> The moving nest option is not available due to missing rpc/types.h file.
> Copy landread.c.dist to landread.c in share directory to bypass compile error.
> ```

> **참고:** `One of compilers testing failed!`가 나오면 `LC_ALL=C`를 빠뜨린 것이다(4.1). `!!! configure.wrf has been REMOVED !!!`가 나오면 6장(OpenMPI) 또는 7.5(`HDF5_PATH`)를 확인한다. 실패 원인은 `tools/nc4_test.log`에 남는다.

### 10.5 configure.wrf 확인

```bash
grep -n -E "^(DMPARALLEL|SFC|SCC|CCOMP|DM_FC|DM_CC|NETCDFPATH|DEP_LIB_PATH|FCCOMPAT)" configure.wrf
```

| 항목 | 정상 값 |
|---|---|
| `DMPARALLEL` | `1` |
| `SFC` / `SCC` / `CCOMP` | `gfortran` / `gcc` / `gcc` |
| `DM_FC` / `DM_CC` | `mpif90` / `mpicc` |
| `NETCDFPATH` | `/home/woogon/CMAQ_MODEL/libs/netCDF-WRF` |
| `DEP_LIB_PATH` | `... -L/home/woogon/CMAQ_MODEL/libs/HDF5-1.14.6/lib`로 끝남 |
| `FCCOMPAT` | `-fallow-argument-mismatch -fallow-invalid-boz` |

> **참고:** `FCCOMPAT`는 gfortran 10 이상에서 WRF의 오래된 코드가 오류를 내지 않도록 configure가 자동으로 넣는 옵션이다. 이 줄이 비어 있으면 configure가 중간에 종료된 것이므로 compile하지 말고 10.4를 다시 확인한다.

### 10.6 compile

```bash
cd /home/woogon/CMAQ_MODEL/WRFV4.5.1
LC_ALL=C ./compile -j 2 em_real 2>&1 | tee log.compile
```

| 옵션 | 의미 |
|---|---|
| `-j 2` | 2코어 병렬 컴파일. 메모리 7.2 GB를 고려해 4코어 대신 2코어 사용 |
| `em_real` | 실제 기상자료 사례용 빌드 (`real.exe`, `wrf.exe` 생성) |

소요시간: 약 19분(이번 구축 기준).

> **참고:** 컴파일 중인 터미널은 닫거나 Ctrl+C를 누르지 않는다. 진행 상황은 다른 터미널에서 `tail -f /home/woogon/CMAQ_MODEL/WRFV4.5.1/log.compile`로 볼 수 있다.

### 10.7 compile 결과 확인

```bash
tail -20 log.compile
ls -l main/*.exe
grep -n -i -E "Error [0-9]|undefined reference|cannot find|fatal error" log.compile
```

정상 결과:

```text
--->                  Executables successfully built                  <---

-rwxr-xr-x. 1 woogon woogon 46892664 Oct  3 20:43 main/ndown.exe
-rwxr-xr-x. 1 woogon woogon 47011488 Oct  3 20:43 main/real.exe
-rwxr-xr-x. 1 woogon woogon 46167896 Oct  3 20:43 main/tc.exe
-rwxr-xr-x. 1 woogon woogon 55102440 Oct  3 20:42 main/wrf.exe
```

마지막 `grep`은 아무것도 출력하지 않아야 한다. 이번 구축에서는 warning 103건이 발생했으나 실행파일 생성에는 영향을 주지 않았고, fatal/link 오류는 확인되지 않았다. 최종 동작 여부는 실제 테스트 case 실행으로 검증한다.

### 10.8 라이브러리 연결 확인

```bash
ldd main/wrf.exe | grep "not found"
ldd main/wrf.exe | grep -E "netcdf|hdf5|mpi"
```

정상 결과: 첫 명령은 아무것도 출력하지 않는다. 두 번째 명령의 주요 결과는 다음과 같다.

```text
libnetcdff.so.7   => /home/woogon/CMAQ_MODEL/libs/netCDF-Fortran-4.6.2/lib/libnetcdff.so.7
libnetcdf.so.22   => /home/woogon/CMAQ_MODEL/libs/netCDF-C-4.9.3/lib/libnetcdf.so.22
libhdf5_hl.so.310 => /home/woogon/CMAQ_MODEL/libs/HDF5-1.14.6/lib/libhdf5_hl.so.310
libhdf5.so.310    => /home/woogon/CMAQ_MODEL/libs/HDF5-1.14.6/lib/libhdf5.so.310
libmpi.so.40      => /usr/lib64/openmpi/lib/libmpi.so.40
```

netCDF와 HDF5가 시스템의 다른 라이브러리가 아닌 **프로젝트 `libs/`의 라이브러리**에 연결되어 있어야 한다.

**상태: WRF 4.5.1 설치·컴파일 및 사례 실행 성공. TEST_20260901의 WPS·real.exe 성공, WRF dmpar 4코어 오류 없이 실행 중이며 wrfout 결과파일 생성 확인(사용자 확인) (컴파일 확인: 2026-10-03)**

---

## 11. WPS 4.5 설치

### 11.1 소스 다운로드

WPS는 하위 모듈이 없으므로 GitHub 태그 압축파일을 그대로 사용한다. 다른 압축파일과 구분되도록 저장 이름을 지정한다.

```bash
cd /home/woogon/CMAQ_MODEL/src
wget -O WPS-4.5.tar.gz https://github.com/wrf-model/WPS/archive/refs/tags/v4.5.tar.gz
```

### 11.2 프로젝트 루트에 압축 해제

```bash
cd /home/woogon/CMAQ_MODEL
tar -xzf src/WPS-4.5.tar.gz
ls
```

정상 결과: `libs  src  WPS-4.5  WRFV4.5.1`

### 11.3 configure

```bash
cd /home/woogon/CMAQ_MODEL/WPS-4.5
LC_ALL=C WRF_DIR=/home/woogon/CMAQ_MODEL/WRFV4.5.1 ./configure
```

| 설정 | 이유 |
|---|---|
| `LC_ALL=C` | 4.1과 같음 |
| `WRF_DIR=...` | WPS는 기본적으로 바로 위 폴더의 `WRF`, `WRFV3` 등 정해진 이름에서 WRF를 찾는다. 이 구축의 폴더명은 `WRFV4.5.1`이므로 위치를 지정한다 |

> **참고: `| tee`를 붙이지 않는다.** WPS configure는 선택 목록을 perl 스크립트로 출력하는데, 출력이 파이프로 넘어가면 perl이 출력을 모아 두었다가 내보낸다. 그래서 목록이 화면에 나오지 않은 채 번호 입력을 기다리는 상태가 된다. 로그가 필요하면 다음과 같이 실행한다.
>
> ```bash
> script -q -c "LC_ALL=C WRF_DIR=/home/woogon/CMAQ_MODEL/WRFV4.5.1 ./configure" log.configure
> ```

> **참고:** 화면이 점선(`-----`)에서 멈춘 것처럼 보이면 Enter를 한 번 누른다. 입력 대기 중이었다면 `Invalid response (0)`과 함께 목록이 다시 나온다.

선택 목록이 나오기 전에 다음이 출력되어야 한다.

```text
Will use NETCDF in dir: /home/woogon/CMAQ_MODEL/libs/netCDF-WRF
Using WRF I/O library in WRF build identified by $WRF_DIR: /home/woogon/CMAQ_MODEL/WRFV4.5.1
Found Jasper environment variables for GRIB2 support...
  $JASPERLIB = /home/woogon/CMAQ_MODEL/libs/grib2/lib
  $JASPERINC = /home/woogon/CMAQ_MODEL/libs/grib2/include
```

선택값:

| 질문 | 입력 | 의미 |
|---|---|---|
| `Enter selection [1-40]` | `1` | Linux x86_64, gfortran (serial), GRIB2 지원 |

> **참고:** WPS는 serial로 빌드한다. WRF(dmpar)와 WPS(serial) 조합은 WRF 공식 튜토리얼의 기본 조합이다. `NO_GRIB2`가 붙은 번호는 GRIB2 자료를 읽지 못하므로 선택하지 않는다.

정상 결과:

```text
Configuration successful. To build the WPS, type: compile

Testing for NetCDF, C and Fortran compiler

This installation NetCDF is 64-bit
C compiler is 64-bit
Fortran compiler is 64-bit
```

### 11.4 configure.wps 확인

```bash
grep -n "Settings for" configure.wps
grep -n -E "^(WRF_DIR|COMPRESSION_LIBS|COMPRESSION_INC|SFC|SCC)" configure.wps
```

| 항목 | 정상 값 |
|---|---|
| `Settings for` | `Linux x86_64, gfortran (serial)` |
| `WRF_DIR` | `/home/woogon/CMAQ_MODEL/WRFV4.5.1` |
| `COMPRESSION_LIBS` | `-L/home/woogon/CMAQ_MODEL/libs/grib2/lib -ljasper -lpng -lz` |
| `COMPRESSION_INC` | `-I/home/woogon/CMAQ_MODEL/libs/grib2/include` |
| `SFC` / `SCC` | `gfortran` / `gcc` |

> **참고:** `COMPRESSION_LIBS`와 `COMPRESSION_INC`는 두 번씩 나온다. 앞의 것은 "아래에서 채우라"는 빈 자리이고, 실제 값은 뒤의 줄에 있다.

### 11.5 compile

```bash
cd /home/woogon/CMAQ_MODEL/WPS-4.5
LC_ALL=C MPI_LIB= ./compile 2>&1 | tee log.compile
```

`MPI_LIB=` 뒤에는 아무것도 쓰지 않는다. "이 명령을 실행하는 동안 `MPI_LIB`는 빈 값"이라는 뜻이다.

> **참고: `MPI_LIB=`를 생략하면** `ungrib.exe`만 만들어지고 `geogrid.exe`, `metgrid.exe`는 `/usr/bin/ld: error: /usr/lib64/openmpi/lib: read: Is a directory`로 링크에 실패한다. WPS의 geogrid/metgrid Makefile은 링크 명령 끝에 `$(MPI_LIB)`를 붙이는데(serial 빌드에서는 비어 있어야 함), 6장의 OpenMPI module이 같은 이름의 환경변수를 설정하기 때문이다.

> **참고:** 실패 후 다시 compile할 때는 `./clean`을 먼저 실행한다. `./clean -a`는 `configure.wps`까지 삭제하므로 사용하지 않는다.

소요시간: 수 분.

### 11.6 compile 결과 확인

```bash
ls -l *.exe
grep -n -i -E "error|undefined reference|cannot find|Is a directory" log.compile
ldd geogrid/src/geogrid.exe ungrib/src/ungrib.exe metgrid/src/metgrid.exe | grep "not found"
```

정상 결과:

```text
geogrid.exe -> geogrid/src/geogrid.exe
metgrid.exe -> metgrid/src/metgrid.exe
ungrib.exe -> ungrib/src/ungrib.exe
```

두 번째와 세 번째 명령은 아무것도 출력하지 않아야 한다.

**상태: WPS 4.5 설치·컴파일 및 사례 실행 성공. TEST_20260901의 WPS·real.exe 성공, WRF dmpar 4코어 오류 없이 실행 중이며 wrfout 결과파일 생성 확인(사용자 확인) (컴파일 확인: 2026-10-03)**

---

## 12. 환경 설정 요약

### 12.1 `~/.bashrc`에 추가한 내용

```bash
# OpenMPI (Rocky package, Environment Modules)
source /etc/profile.d/modules.sh
module load mpi/openmpi-x86_64

# netCDF for WRF (C+Fortran combined)
export NETCDF=$CMAQ_LIBS/netCDF-WRF
export PATH=$NETCDF/bin:$PATH

# HDF5 path for WRF configure (adds -L to DEP_LIB_PATH)
export HDF5_PATH=$CMAQ_LIBS/HDF5-1.14.6

# GRIB2 libraries for WPS (libpng, JasPer)
export JASPERLIB=$CMAQ_LIBS/grib2/lib
export JASPERINC=$CMAQ_LIBS/grib2/include
export LD_LIBRARY_PATH=$CMAQ_LIBS/grib2/lib:$LD_LIBRARY_PATH
```

> **참고:** `$CMAQ_LIBS`는 공통 라이브러리 단계에서 등록한 변수이므로, 위 설정은 그 아래에 있어야 한다.

### 12.2 명령 실행 시에만 붙이는 설정

`.bashrc`에 등록하지 않고 해당 명령 앞에만 붙인다.

| 설정 | 적용 명령 | 이유 |
|---|---|---|
| `LC_ALL=C` | WRF/WPS configure, compile | 한국어 로케일 출력 파싱 오류 방지 (4.1) |
| `WRF_DIR=/home/woogon/CMAQ_MODEL/WRFV4.5.1` | WPS configure | WRF 폴더명이 WPS 기본 탐색 이름과 다름 (11.3) |
| `MPI_LIB=` | WPS compile | OpenMPI module의 `MPI_LIB`가 링크 명령에 들어가는 것 방지 (11.5) |

### 12.3 소스 수정 사항

| 파일 | 조치 | 이유 |
|---|---|---|
| `WRFV4.5.1/share/landread.c` | `landread.c.dist`로 교체 (원본은 `landread.c.orig`) | Rocky 9의 rpc 헤더 부재, moving nest 미사용 (10.3) |

---

## 13. 완료 현황

| 구성요소 | 버전 | 위치 | 실행파일 | 상태 |
|---|---|---|---|---|
| libpng | 1.2.50 | `libs/grib2` | - | 설치 완료 |
| JasPer | 1.900.1 | `libs/grib2` | - | 설치 완료 |
| netCDF 통합 링크 | 4.9.3 / 4.6.2 | `libs/netCDF-WRF` | - | 구성 완료 |
| WRF | 4.5.1 | `WRFV4.5.1` | `wrf.exe`, `real.exe`, `ndown.exe`, `tc.exe` | 설치·컴파일 및 사례 실행 성공. TEST_20260901의 WPS·real.exe 성공, WRF dmpar 4코어 오류 없이 실행 중이며 wrfout 결과파일 생성 확인(사용자 확인) |
| WPS | 4.5 | `WPS-4.5` | `geogrid.exe`, `ungrib.exe`, `metgrid.exe` | 설치·컴파일 및 사례 실행 성공. TEST_20260901의 WPS·real.exe 성공, WRF dmpar 4코어 오류 없이 실행 중이며 wrfout 결과파일 생성 확인(사용자 확인) |

Phase 3의 설치·사례 실행과 결과파일 생성은 성공으로 기록한다(2026-10-08 사용자 확인). WRF는 현재 오류 없이 실행 중이다. 이 성공은 실행·출력 생성 기준이며, 전체 기간 정상 종료는 모의 종료 후 `SUCCESS COMPLETE WRF`와 마지막 Times를 확인해 별도 기록한다. 다음 구축 단계는 MCIP 설치·입력 변환이다.

<a id="case-run"></a>

## 14. 자료 준비 및 사례 실행: BUSAN / TEST_20260901

### 14.0. 다음 실행 때 따라 할 순서

이 장의 명령은 **Linux Bash 터미널**에서 위에서 아래로 실행한다. 설치를 다시 하는 절차가 아니라 이미 구축한 WRF/WPS로 다음 CASE를 실행하는 절차다.

현재 `TEST_20260901`은 실행 중인 성공 사례이므로 그 입력·출력을 덮어쓰지 않는다. 다음 명령 예시는 새 폴더 `TEST_20260901_REPEAT`에 현재 성공한 입력파일을 복사하여 재실행하는 방식이다. 다른 사례명으로 실행하려면 아래 모든 `TEST_20260901_REPEAT` 경로를 원하는 이름으로 함께 바꾼다. 실행파일은 계속 설치 폴더의 **절대경로**로 직접 호출한다.

| 순서 | 작업 | 명령 위치 |
|---|---|---|
| 1 | 환경 불러오기·폴더 생성 | §14.3 |
| 2 | 성공한 namelist 보존·복사·기간 변경 | §14.3.1~14.3.3 |
| 3 | 지형자료·FNL 준비 | §14.3.4 |
| 4 | WPS 테이블 링크 및 geogrid 실행 | §14.4.1 |
| 5 | FNL 링크 및 ungrib 실행 | §14.4.2 |
| 6 | metgrid 실행·34층 확인 | §14.4.3 |
| 7 | WRF 입력 링크·runtime data 준비 | §14.5.1 |
| 8 | real.exe 실행·9개 산출물 확인 | §14.5.2 |
| 9 | wrf.exe 4코어 실행 | §14.6 |
| 10 | 다른 터미널에서 진행·결과 확인 | §14.6 |

각 프로그램의 성공 메시지와 산출물을 확인한 뒤 다음 단계로 간다. **모든 프로그램을 한 번에 붙여넣어 연속 실행하지 않는다.**

### 14.1. 범위와 확인된 상태

2026-10-08 사용자 제공 실제 실행 기록 기준이다. 설치·컴파일은 이 문서 §4~12, 경로는 §2와 기본계획 §4.2를 따른다.

현재 CASE의 결과 위치는 `/home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/WRF/wrfout_d0*`이다. 사용자 확인을 기준으로 기록했으며 이 작업에서 서버 파일이나 계산을 직접 검사·재실행하지 않았다.

WPS와 real.exe는 성공했다. WRF도 현재까지 오류 없이 실행되고 wrfout 결과파일이 생성되는 것으로 사용자 확인을 받아 **WRF 실행·결과파일 생성 성공**으로 기록한다(2026-10-08). 전체 모의 종료 메시지와 최종 출력 시각은 종료 후 확인한다. MCIP/CMAQ 실행 완료를 뜻하지 않는다.

### 14.2. 그대로 유지할 설정과 사례별 변경값

| 구분 | 현재 기준 | 변경 시 확인 |
|---|---|---|
| 모델/병렬 실행 | WRF 4.5.1 dmpar, WPS 4.5 serial, WRF 4코어 | 동일 compiler/MPI/library 환경 |
| 도메인 | d01~d04, max_dom=4 | WPS/WRF 격자·투영·nest 관계 일치 |
| 신규 지형 생성 | MODIS 21 category | geo_em의 MMINLU=MODIFIED_IGBP_MODIS_NOAH, NUM_LAND_CAT=21; WRF num_land_cat=21 |
| 기상 입력 | FNL ds083.2, 1도 GRIB2, 6시간 | 다른 제품을 사용할 때 Vtable·간격·층수 재검증 |
| 입력자료 시간 간격 | interval_seconds=21600 | WPS/WRF 동일; time_step과 다른 값 |
| 입력자료 연직층 | num_metgrid_levels=34 | met_em header 기준; WRF e_vert와 다른 값 |
| 물리·FDDA | 성공한 CASE namelist.input 유지; d01~d04 wrffdda 생성 구성 | 옵션·계수·시간창을 일괄 변경하지 않음 |
| 모의 기간/출력 주기 | 사례별 변경 | start/end, run_*, history_interval, FDDA 시간창 및 자료 범위 정합 |
| 사례 폴더 | TEST_20260901 | 폴더명에서 실제 모의 시작·종료를 추정하지 않음 |

현재 namelist 원문은 이 저장소에 없다. 격자 크기, nest ratio, 물리옵션 번호, FDDA 계수는 확인되지 않은 값을 만들어 적지 않는다. 동일 사례를 완전히 재현하려면 실제 성공한 `namelist.wps`, `namelist.input`을 보존해야 한다. §14.3.2는 성공한 원본 파일을 복사하는 명령이며, §14.3.3은 날짜 변경 위치를 보여준다. 날짜 조각만으로 완전한 namelist를 새로 만들 수는 없다.

날짜는 모두 UTC 모델 시각이다. 예를 들어 2026-08-31 00 UTC ~ 2026-09-02 00 UTC는 설명용 기간이며 확정된 실제 기간이 아니다. 네 도메인의 start/end를 일치시키고 run_*와 FDDA 종료 시간, 입력자료 마지막 시각을 함께 조정한다. domain/physics/FDDA의 현재 공간·물리 설정과 날짜 변경을 구분한다.

### 14.3. 새 시스템에서 자료·CASE 준비

먼저 설치 가이드의 환경 등록을 적용하고 확인한다.

```bash
source ~/.bashrc
source /etc/profile.d/modules.sh
module load mpi/openmpi-x86_64
which mpirun
mpirun --version
ldd /home/woogon/CMAQ_MODEL/WRFV4.5.1/main/wrf.exe
ldd /home/woogon/CMAQ_MODEL/WPS-4.5/geogrid/src/geogrid.exe
ldd /home/woogon/CMAQ_MODEL/WPS-4.5/ungrib/src/ungrib.exe
ldd /home/woogon/CMAQ_MODEL/WPS-4.5/metgrid/src/metgrid.exe
mkdir -p /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901_REPEAT/{WPS,WRF,MCIP,EMIS,CMAQ,POST,LOG}
mkdir -p /home/woogon/CMAQ_MODEL/DATA/WPS_GEOG
mkdir -p /home/woogon/CMAQ_MODEL/DATA/MET/FNL
```

ldd에 `not found`가 있으면 먼저 공통 라이브러리 환경을 복구한다.

#### 14.3.1. 성공한 입력파일을 먼저 보존한다

현재 성공한 입력파일은 아래 두 경로에 있다. 이 파일들은 새 namelist를 만드는 기준이다. 설치 폴더의 기본 namelist 예제를 복사하면 현재 도메인·물리·FDDA 설정이 사라질 수 있으므로 사용하지 않는다.

```bash
ls -lh /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/WPS/namelist.wps
ls -lh /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/WRF/namelist.input
input_archive=/home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/LOG/inputs_$(date -u +%Y%m%dT%H%M%SZ)
mkdir -p "$input_archive"
cp -p /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/WPS/namelist.wps "$input_archive"/
cp -p /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/WRF/namelist.input "$input_archive"/
```

ls에서 파일이 없으면 진행하지 않는다. 아래 준비는 새 실행 폴더에서만 한다.

#### 14.3.2. WPS와 WRF 입력파일을 새 CASE에 복사한다

```bash
mkdir -p /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901_REPEAT/{WPS,WRF,MCIP,EMIS,CMAQ,POST,LOG}
# 두 대상 파일이 모두 없을 때만 복사한다.
if [ ! -e /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901_REPEAT/WPS/namelist.wps ] &&
   [ ! -e /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901_REPEAT/WRF/namelist.input ]; then
    cp -p /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/WPS/namelist.wps /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901_REPEAT/WPS/
    cp -p /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/WRF/namelist.input /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901_REPEAT/WRF/
else
    echo "STOP: 대상 CASE에 입력파일이 이미 있습니다. 새로운 CASE 이름을 사용하세요."
fi
ls -lh /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901_REPEAT/WPS/namelist.wps
ls -lh /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901_REPEAT/WRF/namelist.input
```

STOP이 출력되면 아래 실행을 진행하지 않고 새로운 CASE 이름으로 준비한다. 동일 기간·도메인을 재현하면 복사한 성공 설정을 그대로 사용한다. 새 시스템에서는 성공 사례의 두 파일을 먼저 위 원본 경로로 가져와야 하며, 이 저장소에는 원문이 아직 없어 다운로드 명령으로 대체할 수 없다.

#### 14.3.3. 기간을 바꿀 때 입력파일을 편집하고 확인한다

기간이 같으면 날짜를 바꾸지 않는다. 기간을 바꿀 때만 새 CASE의 두 입력파일을 편집한다.

```bash
vi /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901_REPEAT/WPS/namelist.wps
vi /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901_REPEAT/WRF/namelist.input
```

vi에서는 `i`로 수정하고 Esc → `:wq` → Enter로 저장한다. 아래는 **수정 위치를 보여주는 조각**이며 전체 namelist를 덮어쓰는 입력파일이 아니다. 시작/종료 시각은 예시이다.

WPS의 기존 `&share` section에서 네 도메인의 날짜를 같은 기간으로 맞춘다.

```fortran
 max_dom = 4,
 start_date = '2026-08-31_00:00:00', '2026-08-31_00:00:00', '2026-08-31_00:00:00', '2026-08-31_00:00:00',
 end_date   = '2026-09-02_00:00:00', '2026-09-02_00:00:00', '2026-09-02_00:00:00', '2026-09-02_00:00:00',
 interval_seconds = 21600,
```

WRF의 기존 `&time_control` section은 같은 UTC 기간으로 맞춘다. 아래 run_days=2는 위 48시간 예시 기간에만 해당한다.

```fortran
 run_days = 2,
 run_hours = 0,
 run_minutes = 0,
 run_seconds = 0,
 start_year   = 2026, 2026, 2026, 2026,
 start_month  = 08, 08, 08, 08,
 start_day    = 31, 31, 31, 31,
 start_hour   = 00, 00, 00, 00,
 start_minute = 00, 00, 00, 00,
 start_second = 00, 00, 00, 00,
 end_year     = 2026, 2026, 2026, 2026,
 end_month    = 09, 09, 09, 09,
 end_day      = 02, 02, 02, 02,
 end_hour     = 00, 00, 00, 00,
 end_minute   = 00, 00, 00, 00,
 end_second   = 00, 00, 00, 00,
 interval_seconds = 21600,
```

기존 `&fdda`의 `gfdda_end_h` 등 시간창도 새 모의 기간에 맞춰 검토한다. FDDA 방식·도메인별 적용·계수는 성공한 설정을 유지한다. `&domains`의 `num_metgrid_levels=34`와 `&physics`의 `num_land_cat=21`을 확인하되 격자·물리 설정은 임의로 바꾸지 않는다.

```bash
grep -nE 'max_dom|start_date|end_date|interval_seconds|geog_data_path|geog_data_res|prefix|fg_name' /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901_REPEAT/WPS/namelist.wps
grep -nE 'run_days|run_hours|run_minutes|run_seconds|start_|end_|interval_seconds|max_dom|num_metgrid_levels|num_metgrid_soil_levels|num_land_cat|grid_fdda|gfdda' /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901_REPEAT/WRF/namelist.input
diff -u /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/WPS/namelist.wps /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901_REPEAT/WPS/namelist.wps
diff -u /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/WRF/namelist.input /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901_REPEAT/WRF/namelist.input
```

동일 기간 복사라면 diff 출력이 없어야 한다. 기간 변경 사례라면 의도한 날짜·실행기간·시간창만 바뀌었는지 확인한다.

#### 14.3.4. 정적 자료와 FNL 준비

정적 자료는 [공식 WPS 지형자료 페이지](https://www2.mmm.ucar.edu/wrf/users/download/get_sources_wps_geog.html)에서 현재 GEOGRID.TBL이 요구하는 지형·토양·식생·MODIS 자료를 준비하고 WPS_GEOG에 압축 해제한다. 기존 서버에서는 준비된 자료를 재사용한다. 신규 geogrid는 MODIS 21 category를 표준으로 한다. `geog_data_res='default',...`는 로컬 GEOGRID.TBL의 LANDUSEF 항목이 21-category MODIS 자료를 선택하는지 확인한 뒤 사용한다. USGS 기반 기존 geo_em에 WRF의 num_land_cat만 21로 바꾸지 않는다.

FNL은 [NCAR ds083.2 / d083002](https://gdex.ucar.edu/datasets/d083002/)의 1도 GRIB2 분석자료를 사용한다. 00/06/12/18 UTC 자료를 모의 시작부터 종료까지 빠짐없이 준비한다. 월 경계를 넘으면 모든 해당 월을 준비한다. 예시 파일명은 `fnl_20260831_00_00.grib2`이다.

서버의 다운로드 스크립트는 `/home/woogon/CMAQ_MODEL/SCRIPTS/download_fnl.sh`이다. 원문과 인자 규약은 아직 저장소에 없으므로 실행 인자를 추정하지 않는다.

```bash
sed -n '1,200p' /home/woogon/CMAQ_MODEL/SCRIPTS/download_fnl.sh
ls -lh /home/woogon/CMAQ_MODEL/DATA/MET/FNL/2026/08/fnl_*.grib2
ls -lh /home/woogon/CMAQ_MODEL/DATA/MET/FNL/2026/09/fnl_*.grib2
```

위 월은 예시이다. 자료 크기와 시각 목록을 확인하고, 다운로드된 파일이 로그인 HTML이나 빈 파일이 아닌 GRIB2인지 점검한다. 계정 인증 정보는 문서나 Git에 넣지 않는다.

### 14.4. WPS: geogrid → ungrib → metgrid

성공한 CASE의 namelist.wps를 CASE/WPS에 준비하고 기간을 변경한다. &share에 `max_dom=4`, `interval_seconds=21600`, &geogrid에 `geog_data_path='/home/woogon/CMAQ_MODEL/DATA/WPS_GEOG'`, &ungrib에 `out_format='WPS'`, `prefix='FILE'`, &metgrid에 `fg_name='FILE'`을 설정한다. out_opt=2는 netCDF 출력 기준이다. 도메인의 parent_id, parent_grid_ratio, i/j_parent_start, e_we/e_sn, dx/dy 및 투영은 검증된 값을 유지한다.

#### 14.4.1. WPS 테이블 준비와 geogrid.exe 실행

현재 작업 디렉터리가 입력·출력 위치를 결정한다. 실행파일은 설치 폴더의 절대경로로 호출한다.

```bash
cd /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901_REPEAT/WPS
mkdir -p geogrid metgrid
ln -sfn /home/woogon/CMAQ_MODEL/WPS-4.5/geogrid/GEOGRID.TBL.ARW geogrid/GEOGRID.TBL
ln -sfn /home/woogon/CMAQ_MODEL/WPS-4.5/metgrid/METGRID.TBL.ARW metgrid/METGRID.TBL
ln -sfn /home/woogon/CMAQ_MODEL/WPS-4.5/ungrib/Variable_Tables/Vtable.GFS Vtable
ls -l namelist.wps geogrid/GEOGRID.TBL metgrid/METGRID.TBL Vtable
/home/woogon/CMAQ_MODEL/WPS-4.5/geogrid.exe
tail -30 geogrid.log
ls -lh geo_em.d0*.nc
ncdump -h geo_em.d01.nc | grep -E 'MMINLU|NUM_LAND_CAT'
```

geogrid 성공 메시지와 d01~d04 geo_em, MODIS 21 category를 확인한다. d02~d04 header도 동일하게 확인한다. 사용 자료나 도메인을 바꾸면 geogrid부터 재생성한다.

#### 14.4.2. FNL 링크와 ungrib.exe 실행

다음 명령의 날짜 패턴은 위 설명용 기간에 맞춘 예시이다. 실제 기간의 파일만 링크하고 다른 사례 GRIBFILE 링크가 섞이지 않은 새 실행 폴더를 사용한다. WPS 입력자료 목록이 파일로 출력되는지 확인한 뒤 ungrib을 시작한다.

```bash
cd /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901_REPEAT/WPS
/home/woogon/CMAQ_MODEL/WPS-4.5/link_grib.csh /home/woogon/CMAQ_MODEL/DATA/MET/FNL/2026/08/fnl_20260831_*.grib2 /home/woogon/CMAQ_MODEL/DATA/MET/FNL/2026/09/fnl_2026090[12]_*.grib2
ls -l GRIBFILE.*
/home/woogon/CMAQ_MODEL/WPS-4.5/ungrib.exe
tail -30 ungrib.log
ls -lh FILE:*
```

ungrib 성공 메시지와 FILE:*의 시작·종료 시각 및 6시간 간격을 확인한다.

#### 14.4.3. metgrid.exe 실행

```bash
cd /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901_REPEAT/WPS
/home/woogon/CMAQ_MODEL/WPS-4.5/metgrid.exe
tail -30 metgrid.log
ls -lh met_em.d0*.nc
```

header는 아래처럼 실제 생성된 한 파일을 명시해 확인한다.

```bash
# 날짜는 예시이며 실제 생성된 파일명으로 변경한다.
ncdump -h met_em.d01.2026-08-31_00:00:00.nc | grep -E 'num_metgrid_levels|num_st_layers'
```

ungrib/metgrid 각각 성공 메시지를 확인한 뒤 다음 단계로 진행한다. FILE:*가 6시간 간격으로 시작~종료 시각을 포함하는지, met_em이 네 도메인과 전체 입력 시각에 대해 생성됐는지 확인한다. 현재 met_em의 num_metgrid_levels는 34이며 namelist.input도 34로 맞춘다. 토양층수 num_metgrid_soil_levels는 실제 num_st_layers와 맞춘다. 34를 WRF 모델층 e_vert에 복사하지 않는다.

### 14.5. WRF runtime data와 real.exe

CASE/WRF에 검증된 namelist.input을 준비한다. &time_control의 start/end와 run_*는 WPS 기간과 일치시키고 `interval_seconds=21600`을 사용한다. &domains의 `max_dom=4`, `num_metgrid_levels=34`, &physics의 `num_land_cat=21` 및 현재 물리 설정을 확인한다. FDDA 원문 설정을 유지하고 시간창은 변경한 모의 기간과 맞춘다.

#### 14.5.1. met_em 입력과 runtime data 링크 준비

런타임 자료는 real.exe와 wrf.exe 실행 전에 준비한다. run 전체를 링크하지 않고 현재 설정에 필요한 일곱 파일만 연결한다.

```bash
cd /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901_REPEAT/WRF
ls -lh /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901_REPEAT/WPS/met_em.d0*.nc
ln -s /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901_REPEAT/WPS/met_em.d0*.nc .
ls -lh namelist.input met_em.d0*.nc
WRFRUN=/home/woogon/CMAQ_MODEL/WRFV4.5.1/run
for runtime_file in LANDUSE.TBL VEGPARM.TBL SOILPARM.TBL GENPARM.TBL RRTM_DATA RRTM_DATA_DBL CAMtr_volume_mixing_ratio; do
    test -s "$WRFRUN/$runtime_file" || { echo "Missing runtime data: $runtime_file"; break; }
    ln -sfn "$WRFRUN/$runtime_file" .
done
ls -l LANDUSE.TBL VEGPARM.TBL SOILPARM.TBL GENPARM.TBL RRTM_DATA RRTM_DATA_DBL CAMtr_volume_mixing_ratio
for runtime_file in LANDUSE.TBL VEGPARM.TBL SOILPARM.TBL GENPARM.TBL RRTM_DATA RRTM_DATA_DBL CAMtr_volume_mixing_ratio; do
    test -s "$runtime_file" || echo "STOP: missing/broken $runtime_file"
done
```

STOP 또는 누락 메시지가 있으면 실행을 진행하지 않는다. 물리옵션을 바꾸었을 때는 요구하는 추가 runtime data만 검토해 연결한다. GHG 오류의 실제 원인은 CASE 실행 폴더의 runtime data 누락이며 부록 B를 참고한다.

#### 14.5.2. real.exe 실행

```bash
cd /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901_REPEAT/WRF
source /etc/profile.d/modules.sh
module load mpi/openmpi-x86_64
mpirun -np 4 /home/woogon/CMAQ_MODEL/WRFV4.5.1/main/real.exe
grep "SUCCESS COMPLETE REAL" rsl.error.0000
ls -lh wrfinput_d01 wrfinput_d02 wrfinput_d03 wrfinput_d04 wrfbdy_d01 wrffdda_d01 wrffdda_d02 wrffdda_d03 wrffdda_d04
```

SUCCESS COMPLETE REAL과 모든 산출물을 확인한 뒤 진행한다. 현재 FDDA 사용 구성에서는 wrffdda_d01~d04가 필요하다. FDDA를 사용하지 않는 다른 사례에 이 산출물 요구를 그대로 적용하지 않는다.

### 14.6. WRF dmpar 4코어 실행과 확인

real.exe 로그를 보존한 뒤 wrf.exe를 시작한다. 기존 계산이 실행 중이면 아래 명령으로 재실행하지 않는다. 실패 실행의 wrfout/rsl은 별도 보관하고, 새 사례 폴더를 사용하는 것을 우선한다. 정상 출력 파일을 일괄 삭제하는 절차는 포함하지 않는다.

```bash
cd /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901_REPEAT/WRF
real_log_archive=../LOG/real_$(date -u +%Y%m%dT%H%M%SZ)
mkdir -p "$real_log_archive"
cp -p rsl.error.* rsl.out.* "$real_log_archive"/
mpirun -np 4 /home/woogon/CMAQ_MODEL/WRFV4.5.1/main/wrf.exe
```

wrf.log를 별도 생성하지 않는다. 로그는 CASE/WRF의 rsl.error.* / rsl.out.*를 사용한다. 실행 중 두 번째 터미널에서 확인한다.

```bash
tail -f /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901_REPEAT/WRF/rsl.error.0000
```

tail 감시를 끝내는 Ctrl+C는 해당 감시 터미널에서만 누른다. 실제 모델 실행 터미널에서 누르면 계산을 중단할 수 있다. 커서 깜빡임이나 로그 숫자 증가만으로 정상 계산을 단정하지 않고 모델 시각을 확인한다.

```bash
grep "Timing for main" /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901_REPEAT/WRF/rsl.error.0000 | tail
```

모델 시간이 증가하면 계산 진행 중이다. 종료 후 확인:

```bash
cd /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901_REPEAT/WRF
grep "SUCCESS COMPLETE WRF" rsl.error.0000
tail -30 rsl.error.0000
grep -niE 'FATAL|segmentation|MPI_ABORT' rsl.error.* rsl.out.*
ls -lh wrfout_d0*
# 실제 생성된 파일 하나를 지정해 Times를 확인한다(아래 날짜는 예시).
ncdump -v Times wrfout_d01_2026-08-31_00:00:00 | tail -30
```

성공 메시지, d01~d04 출력 존재, 각 도메인의 마지막 Times가 요청한 종료 시각까지 도달했는지를 함께 확인한다. 출력이 여러 파일로 나뉘면 마지막 파일도 확인한다. 실행 시작 직후 wrfout이 존재하는 것만으로 완료 처리하지 않는다. 검증 완료 후 MCIP 입력으로 전달한다.

### 14.7. 재현에 필요한 보존 자료

CASE의 namelist.wps/namelist.input, FNL 파일 목록·기간, geo_em/met_em header, runtime 링크 목록, compiler/MPI/library 버전, rsl 로그와 성공 메시지를 보존한다. 현재 다운로드 스크립트와 실제 namelist 원문은 미수집이므로, 새 시스템에서 동일 과학 설정을 완전히 재현하는 데에는 이 원문 확보가 필요하다.

절차와 Vtable의 공식 근거: [WRF Users Guide — WPS](https://www2.mmm.ucar.edu/wrf/users/wrf_users_guide/build/html/wps.html).

---

## 부록 A. 구축 중 발생한 문제 기록

이 문서의 절차는 아래 문제들을 해결한 결과다. 같은 증상을 만났을 때 원인을 찾는 용도로 남긴다.

| 번호 | 단계 | 증상 | 원인 | 예방 조치 |
|---|---|---|---|---|
| A1 | 사전 점검 | `nc-config: command not found` | netCDF C/Fortran 분리 설치, `bin`이 `PATH`에 없음 | 7장 |
| A2 | WRF configure | `One of compilers testing failed!` | 한국어 로케일에서 `type` 출력 파싱 실패 | 4.1 `LC_ALL=C` |
| A3 | WRF configure | netCDF4 테스트 실패, `configure.wrf` 삭제 | `DEP_LIB_PATH`에 HDF5 `lib` 경로 누락 | 7.5 `HDF5_PATH` |
| A4 | WRF configure | `mpicc: command not found` (`tools/nc4_test.log`) | OpenMPI module이 `.bashrc`에 미등록 | 6장 |
| A5 | WRF configure | `rpc/types.h` 경고 | Rocky 9에 Sun RPC 헤더 없음 | 10.3 `landread.c` 교체 |
| A6 | WRF compile | `/bin/csh: 잘못된 인터프리터` | csh 미설치 | 5장 `tcsh` |
| A7 | WPS configure | 선택 목록이 표시되지 않음 | perl 출력이 파이프(`tee`)에서 버퍼링됨 | 11.3 `tee` 미사용 |
| A8 | WPS compile | geogrid/metgrid `Is a directory` 링크 오류 | OpenMPI module의 `MPI_LIB` 환경변수가 Makefile에 유입 | 11.5 `MPI_LIB=` |

진단에 사용한 명령:

```bash
# A2: 컴파일러 자체는 정상인지, 로케일이 원인인지 확인
sh -c 'type gcc'
LC_ALL=C sh -c 'type gcc'

# A3, A4: netCDF4 테스트 실패 원인 (실패 시 로그가 남음)
cat /home/woogon/CMAQ_MODEL/WRFV4.5.1/tools/nc4_test.log

# A5: rpc 테스트 직접 재현
cd /home/woogon/CMAQ_MODEL/WRFV4.5.1
gcc -DUSE_TIRPC -o /tmp/rpc_test.exe tools/rpc_test.c

# A8: 링크 실패 위치 확인
grep -n -B2 "Is a directory" /home/woogon/CMAQ_MODEL/WPS-4.5/log.compile
```

구축 경위:

- 처음에는 WRF를 `src/WRFV4.5.1`에 풀어 진행했으나, 기본계획의 디렉터리 구조와 맞지 않아 삭제하고 프로젝트 루트에서 다시 진행했다.
- A2의 원인을 처음에는 `file` 명령 누락으로 추정했으나, `file`은 이미 설치되어 있었다.
- A3 대응으로 처음에는 `configure.wrf`의 `DEP_LIB_PATH`를 `sed`로 직접 수정했다. 그러나 configure 내부의 netCDF4 테스트는 통과하지 못하고 configure를 다시 실행할 때마다 수정이 사라지므로, `HDF5_PATH` 방식으로 대체했다.
- A5 대응으로 `libtirpc-devel`을 설치했으나 해결되지 않아 `landread.c` 교체로 처리했다. 설치한 패키지는 그대로 두었다.

## 부록 B. WRF GHG 오류: CASE runtime data 누락

### 확인된 원인

TEST_20260901에서 real.exe 성공 후 wrf.exe의 GHG 관련 오류는 CASE 실행 디렉터리에 WRF runtime data 파일이 없어서 발생했다. 실행파일을 절대경로로 호출해도 프로그램은 현재 CASE/WRF에서 런타임 자료를 찾는다.

현재 구성에서는 LANDUSE.TBL, VEGPARM.TBL, SOILPARM.TBL, GENPARM.TBL, RRTM_DATA, RRTM_DATA_DBL, CAMtr_volume_mixing_ratio를 `/home/woogon/CMAQ_MODEL/WRFV4.5.1/run`에서 CASE/WRF로 선별 심볼릭 링크한다. run 폴더 전체를 링크하지 않는다.

### 해결 및 확인

§14.5의 링크·파일 존재 점검 후 §14.6의 `mpirun -np 4` 실행을 따른다. ls -l에 링크가 보여도 실제 대상이 없으면 해결되지 않은 것이므로 test -s로 확인한다. 진행과 종료는 rsl.error.* / rsl.out.*에서 확인한다.

`ghg_input`을 namelist에 추가하는 방법은 이 오류의 해결책이 아니다. 잘못 추가한 항목이 있으면 제거하고 검증된 namelist 설정을 유지한다. 해당 항목의 추가 명령이나 예제는 제공하지 않는다.

### 문서 출처와 범위

이 문서는 2026-10-08 사용자 제공 원인·해결 기록을 설치/실행 가이드와 일치하도록 통합한 기록이다. 사용자가 언급한 업로드 파일 `WRF_GHG_Error_Fix.md` 원문은 현재 연결된 첨부·로컬 sources·GitHub에 없어 직접 대조하지 못했다. 원문을 확인한 것으로 간주하지 않는다.


## 15. 검토 근거 및 관련 문서

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
