# CMAQ 모델링 시스템 공통 라이브러리 구축 기록

## 1. 목적
Rocky Linux 기반 CMAQ 통합 대기질 모델링 시스템 구축 과정에서 I/O API 설치 이전까지 완료한 공통 라이브러리 설치 절차를 재현할 수 있도록 기록한다.

설치 순서:

```text
zlib 확인
  ↓
HDF5 1.14.6
  ↓
netCDF-C 4.9.3
  ↓
netCDF-Fortran 4.6.2
```

I/O API는 설치 완료 후 별도 문서로 기록한다.

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

소스와 설치 결과를 분리하고 라이브러리 디렉터리명에는 정확한 버전을 표시한다.

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

## 7. 최종 확인

```bash
/home/woogon/CMAQ_MODEL/libs/HDF5-1.14.6/bin/h5cc -showconfig
/home/woogon/CMAQ_MODEL/libs/netCDF-C-4.9.3/bin/nc-config --version
/home/woogon/CMAQ_MODEL/libs/netCDF-C-4.9.3/bin/nc-config --has-nc4
/home/woogon/CMAQ_MODEL/libs/netCDF-C-4.9.3/bin/nc-config --has-hdf5
/home/woogon/CMAQ_MODEL/libs/netCDF-Fortran-4.6.2/bin/nf-config --version
/home/woogon/CMAQ_MODEL/libs/netCDF-Fortran-4.6.2/bin/nf-config --all
```

완료 현황:

| 구성요소 | 버전 | 설치 방법 | 상태 |
|---|---:|---|---|
| zlib | 1.2.11 | Rocky Linux 시스템 패키지 | 확인 완료 |
| HDF5 | 1.14.6 | 소스 빌드 | 설치·검증 완료 |
| netCDF-C | 4.9.3 | 소스 빌드 | 설치·검증 완료 |
| netCDF-Fortran | 4.6.2 | 소스 빌드 | 설치·검증 완료 |

현재 의존관계:

```text
Rocky Linux zlib
       ↓
HDF5 1.14.6
       ↓
netCDF-C 4.9.3
       ↓
netCDF-Fortran 4.6.2
```

다음 구축 대상은 **I/O API 3.2-20200828**이다.
