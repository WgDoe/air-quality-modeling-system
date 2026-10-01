# CMAQ 모델링 시스템 공통 라이브러리 구축 기록

## 1. 목적
Rocky Linux 기반 CMAQ 통합 대기질 모델링 시스템 구축 과정에서 I/O API 설치 이전까지 완료한 공통 라이브러리 설치 내역을 기록한다.

현재까지의 순서는 **zlib 확인 → HDF5 1.14.6 → netCDF-C 4.9.3 → netCDF-Fortran 4.6.2**이다. I/O API 설치 과정은 별도 문서로 관리한다.

## 2. 구축 환경
- OS: Rocky Linux 9.8 (Blue Onyx), x86_64
- 사용자: `woogon`
- 프로젝트 루트: `/home/woogon/CMAQ_MODEL`
- GCC/GFortran: 11.5.0
- GNU Make, OpenMPI 설치 및 동작 확인
- 원칙: 소스는 `src`, 설치 결과는 `libs`에 분리하고 디렉터리명에 정확한 버전을 표시

```text
/home/woogon/CMAQ_MODEL/
├── libs/
│   ├── HDF5-1.14.6/
│   ├── netCDF-C-4.9.3/
│   └── netCDF-Fortran-4.6.2/
└── src/
    ├── hdf5-1.14.6/
    ├── netcdf-c-4.9.3/
    └── netcdf-fortran-4.6.2/
```

## 3. zlib
Rocky Linux 시스템에 이미 설치된 zlib을 사용했으며 별도 소스 컴파일은 하지 않았다.

확인 패키지:
```text
zlib-1.2.11-40.el9.x86_64
zlib-devel-1.2.11-40.el9.x86_64
```

## 4. HDF5 1.14.6
- 소스: `/home/woogon/CMAQ_MODEL/src/hdf5-1.14.6`
- 설치: `/home/woogon/CMAQ_MODEL/libs/HDF5-1.14.6`
- gcc/g++/gfortran 사용
- Fortran 지원 활성화
- shared/static library 생성
- 시스템 zlib 사용

검증:
```bash
make -j4
make check
make install
```
모두 정상 완료했으며 `h5cc -showconfig`로 설치 설정을 확인했다.

**상태: 설치 및 검증 완료**

## 5. netCDF-C 4.9.3
- 소스: `/home/woogon/CMAQ_MODEL/src/netcdf-c-4.9.3`
- 설치: `/home/woogon/CMAQ_MODEL/libs/netCDF-C-4.9.3`
- HDF5: `/home/woogon/CMAQ_MODEL/libs/HDF5-1.14.6`

Configure:
```bash
./configure --prefix=/home/woogon/CMAQ_MODEL/libs/netCDF-C-4.9.3 --disable-dap
```

Configure 과정에서 `xml2-config`가 필요하여 Rocky Linux의 `libxml2-devel` 패키지를 추가 설치했다.

검증:
```bash
make -j4
make check
make install
```

`nc-config` 확인 결과:
```text
version  : netCDF 4.9.3
netCDF-4 : yes
HDF5     : yes
```

**상태: 설치 및 검증 완료**

## 6. netCDF-Fortran 4.6.2
- 소스: `/home/woogon/CMAQ_MODEL/src/netcdf-fortran-4.6.2`
- 설치: `/home/woogon/CMAQ_MODEL/libs/netCDF-Fortran-4.6.2`
- 연결 netCDF-C: `/home/woogon/CMAQ_MODEL/libs/netCDF-C-4.9.3`

Configure:
```bash
./configure --prefix=/home/woogon/CMAQ_MODEL/libs/netCDF-Fortran-4.6.2
```

검증:
```bash
make -j4
make check
make install
```

`nf-config --all` 확인 결과:
```text
C compiler       : gcc
Fortran compiler : gfortran
Fortran 2003     : yes
netCDF-2 API     : yes
netCDF-4         : yes
Version          : netCDF-Fortran 4.6.2
```

주요 Fortran 인터페이스:
```text
/home/woogon/CMAQ_MODEL/libs/netCDF-Fortran-4.6.2/include/netcdf.mod
/home/woogon/CMAQ_MODEL/libs/netCDF-Fortran-4.6.2/include/netcdf.inc
```

**상태: 설치 및 검증 완료**

## 7. 완료 현황
| 구성요소 | 버전 | 상태 |
|---|---:|---|
| zlib | 1.2.11 | 시스템 설치 확인 |
| HDF5 | 1.14.6 | 설치·검증 완료 |
| netCDF-C | 4.9.3 | 설치·검증 완료 |
| netCDF-Fortran | 4.6.2 | 설치·검증 완료 |

의존관계:
```text
Rocky Linux system zlib
        ↓
HDF5 1.14.6
        ↓
netCDF-C 4.9.3
        ↓
netCDF-Fortran 4.6.2
```

다음 구축 대상은 **I/O API 3.2-20200828**이다.
