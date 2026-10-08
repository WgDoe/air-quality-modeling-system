# 실제 디렉터리 구조

2026-10-08 사용자 제공 실제 서버 경로 기준이다. GitHub 문서 저장소와 Linux 모델링 서버의 파일 구조를 구분한다.

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

| 경로 | 역할 |
|---|---|
| libs | HDF5 1.14.6, netCDF-C 4.9.3, netCDF-Fortran 4.6.2, netCDF-WRF 통합 링크, grib2, I/O API |
| src | 원본 압축파일 및 라이브러리 빌드 소스 |
| WRFV4.5.1 / WPS-4.5 | 모델 본체; CASE에서 절대경로로 실행 |
| DATA/WPS_GEOG | 공유 정적 자료; 신규 geogrid는 MODIS 21 category 표준 |
| DATA/MET/FNL/YYYY/MM | 공유 FNL ds083.2, 1도 GRIB2, 6시간 자료 |
| CASE/WPS | namelist.wps, 테이블 링크, GRIBFILE, FILE, geo_em, met_em 및 WPS 로그 |
| CASE/WRF | namelist.input, met_em 링크, 선별 runtime 링크, real/WRF 결과와 rsl 로그 |
| CASE/LOG | 단계별 보존 로그; 실시간 rsl은 CASE/WRF에서 확인 |
| CASE/MCIP, EMIS, CMAQ, POST | 후속 작업 폴더; 존재만으로 실행 완료를 의미하지 않음 |
| SCRIPTS/download_fnl.sh | 서버 다운로드 스크립트; 원문·호출 규약은 아직 GitHub 미등록 |

현재 CASE는 `CASES/BUSAN/TEST_20260901`이다. 다른 사례는 `CASES/<지역>/<사례명>`으로 분리한다. 폴더명은 실제 모의 기간을 대신하지 않는다. 날짜는 namelist에서 확인한다.

기존 계획의 `/MODELS`, `/DATA`, `/CASES`는 역할 예시이며 현재 절대경로가 아니다. `config`, `ISAM`, 전체 workflow 스크립트는 향후 확장 계획이다. 서버의 대문자 `SCRIPTS`를 저장소의 향후 소문자 `scripts`와 혼동하지 않는다.

설치 절차는 [설치 가이드](../wrf/WRF_WPS_Installation_Guide.md), 실행 절차·고정/변경 설정은 [사례 실행 가이드](../wrf/WRF_WPS_Case_Run.md)를 기준으로 관리한다. 이 문서에는 실행 명령을 중복하지 않는다.
