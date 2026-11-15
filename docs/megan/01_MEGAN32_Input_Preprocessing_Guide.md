# CMAQ 모델링 시스템 식생 배출량(MEGAN 3.2) 입력 전처리 가이드

> **문서 순서:** [00 읽는 순서](00_README_First.md) → **01 입력 전처리(이 문서)**. 생물성 처리 방식 결정 근거는 [SMOKE 03 §9](../smoke/03_SMOKE_Emission_Improvement_Plan.md#busan-inline-megan)에 있다.

## 1. 목적

부산 사례(`CASES/BUSAN/TEST_20260901`)의 생물성(식생) 배출량을 CMAQ 5.5 CCTM 인라인 MEGAN 3.2로 계산하기 위해, CCTM이 읽는 **시간 불변 입력 3종**을 4개 도메인(27·09·03·01KM)에 대해 만드는 절차를 다른 컴퓨터에서 처음부터 그대로 재현할 수 있도록 기록한다.

| CCTM 환경변수 | 생성 파일 | 내용 |
|---|---|---|
| `MEGAN_CTS` | `CT3_<도메인>.ncf` | 캐노피 유형 6종 피복 비율(%) — 침엽수·열대수·활엽수·관목·초본·작물 |
| `MEGAN_EFS` | `EFMAP_<도메인>.ncf` | 표준 조건 배출계수 19종(nmol/m²/s) — 이소프렌, 모노테르펜 계열, NO 등 |
| `MEGAN_LDF` | `LDF_<도메인>.ncf` | 광의존 비율 4종 |

인라인 방식에서는 기상에 따라 변하는 계산(기온·일사·LAI·토양 NO)을 CCTM이 실행 중에 MCIP 자료로 직접 한다. 따라서 이 문서의 결과는 **격자에만 묶인 고정 지도**이며, SMOKE 처리와 서로 영향을 주지 않는다. 오프라인 MEGAN(MEGCAN·MEGVEA·MGN2MECH 등)은 실행하지 않는다.

실행 순서:

```text
3장  필요한 파일 (저장소 파일 7개, 내려받는 자료 7개)
  ↓
5장  설치·컴파일·공용 자료 준비   setup_megan32.sh   (한 번만)
       전처리기 3개·txt2ioapi 컴파일, EFP 수정, 원자료 정리, 캐노피 입력 6종(동아시아)
  ↓
6장  도메인별 입력 생성          run_megan_domain.sh <사례> 01KM 03KM 09KM 27KM
       생태유형·생육형·캐노피 → 생태유형 결측 채우기 → 배출계수(EFP) → NetCDF 변환 → 공용 폴더 설치
  ↓
7장  확인 (로그·격자·값 점검, 재현 검증)
  ↓
8장  CCTM 연결 (예정)
```

현재 상태(2026-11-16): **4개 도메인(27·09·03·01KM)의 LDF 재생성 후 `LDF03`~`LDF06` 16개 변수 모두 EFP CSV/NetCDF 값과 0~1 범위 검증을 통과했고, 사례 폴더와 운영 `DATA/EMIS/MEGAN/GRID/`의 LDF 파일이 도메인별 MD5 및 `cmp` 비교에서 동일함을 사용자 제공 서버 출력으로 확인했다.** CCTM 연결·실제 식생배출량 진단은 아직 미실행이다. 변환기 수정은 §5.2·§7.2에 기록되어 있다.

## 2. 구축 환경과 선행 조건

- OS: Rocky Linux 9.8, 사용자 `woogon`, 프로젝트 루트 `/home/woogon/CMAQ_MODEL` (메모리 약 7.2GB, 4코어)
- 컴파일러: GNU Fortran 11.5.0 (`gfortran`)
- 라이브러리: `libs/netCDF-WRF`(netCDF-C 4.9.3 + netCDF-Fortran 4.6.2), `libs/ioapi-3.2-20200828/Linux2_x86_64gfort10/libioapi.a`
- 파이썬: Python 3.9, 모듈 `netCDF4`(1.7.2)·`numpy`(2.0.2)·`pandas`(2.3.3)
- 도구: `curl`, `unzip`, `iconv`, `patch`, `md5sum`, `ncdump`, `/usr/bin/time`
- 디스크: 약 11GB (`DATA/EMIS/MEGAN` 약 9.6GB — NCAR 파일 4.1GB, 압축 해제한 EVT3d 1.4GB·GFv7 2.8GB·관목 수정본 0.7GB 포함; `MEGAN` 약 1GB)
- 메모리: 생태유형·생육형 전처리 단계가 최대 약 6.0GB 사용 (7.2GB 서버에서 다른 큰 작업과 동시에 돌리지 않는다)

선행 작업 (이 문서는 아래가 끝났다고 가정한다):

| 선행 작업 | 문서 |
|---|---|
| 공통 라이브러리(netCDF, I/O API) 설치 | [공통 라이브러리](../libraries/Common_Libraries_Installation_Guide.md) |
| WRF 4개 영역 실행: `CASES/BUSAN/TEST_20260901/WRF/wrfout_d0{1..4}_*` | [WRF/WPS 가이드](../wrf/WRF_WPS_Installation_Guide.md) |
| MCIP 4개 도메인: `MCIP/{27KM,09KM,03KM,01KM}/` 의 `namelist.mcip`, `GRIDDESC_<도메인>`, `GRIDCRO2D_<도메인>.*.nc` | [MCIP 구축 가이드](../mcip/MCIP_Installation_Guide.md) |

전처리기는 WRF `wrfout` 파일에서 격자 좌표를 읽고, MCIP이 WRF 격자에서 잘라낸 창(`namelist.mcip`의 `btrim = -1`, `x0`, `y0`, `ncolsin`, `nrowsin`)으로 결과를 잘라 MCIP 격자와 맞춘다.

## 3. 필요한 파일

### 3.1 저장소에서 필요한 파일만 받기

저장소 전체를 받지 않고, 이 절차에 필요한 7개 파일만 GitHub에서 내려받아 `~/megan_files`에 저장소와 같은 폴더 구조로 둔다. 받을 파일 목록은 저장소의 `docs/megan/files/file_list.txt`에 있다.

```bash
(
set -euo pipefail
F=$HOME/megan_files
: "${REF:?GitHub 게시 및 검증을 마친 40자리 커밋 SHA를 REF로 지정하세요}"
[[ "$REF" =~ ^[0-9a-f]{40}$ ]] || { echo "ERROR: REF must be a 40-character commit SHA"; exit 1; }
RAW=https://raw.githubusercontent.com/WgDoe/air-quality-modeling-system/$REF/docs/megan/files
mkdir -p "$F"
curl -fsSL -o "$F/file_list.txt.part" "$RAW/file_list.txt"
mv -- "$F/file_list.txt.part" "$F/file_list.txt"
count=0
while IFS= read -r p || [ -n "$p" ]; do
  case "$p" in ''|/*|*..*) echo "ERROR: invalid path: $p"; exit 1 ;; esac
  mkdir -p "$F/$(dirname "$p")"
  curl -fsSL -o "$F/$p.part" "$RAW/$p" || { echo "FAIL $p"; exit 1; }
  mv -- "$F/$p.part" "$F/$p"
  count=$((count + 1))
done < "$F/file_list.txt"
[ "$count" -eq 7 ] || { echo "ERROR: expected 7 files, got $count"; exit 1; }
echo "Downloaded $count files (+ file_list.txt)"
)
```

정상 기준: `Downloaded 7 files (+ file_list.txt)`가 나온다.

GitHub에 게시하기 전에는 위 다운로드 명령 대신 이 ZIP의 `docs/megan/files/`를 그대로 사용한다. 게시 후에는 가이드와 파일 7개가 모두 있는 커밋을 확인해 `REF`로 지정한다.

| 파일 (`~/megan_files/` 기준) | 용도 |
|---|---|
| `setup_megan32.sh` | 내려받기·수정·컴파일·공용 원자료 준비 (5장, 한 번만) |
| `run_megan_domain.sh` | 도메인별 입력 생성·설치 (6장) |
| `megan_fix_sc30s7.py` | 관목 피복 파일의 잘못된 변수 이름 수정본 생성 (5장에서 호출) |
| `make_megan_cantype_inputs.py` | 캐노피 입력 6종을 동아시아 범위로 생성 (5장에서 호출) |
| `fill_megan_ecotype.py` | 생태유형 결측(65535) 채우기와 셀별 기록 (6장에서 호출) |
| `make_efp_inputs.py` | 도메인별 EFP 입력·실행 파일 생성 (6장에서 호출) |
| `patches/prepmegan4cmaq_grwform_lowmem.patch` | 생육형 전처리기 저메모리판 패치 (5장에서 적용) |
| `file_list.txt` | 위 파일 목록 (내려받기용) |

### 3.2 내려받는 자료 (설치 스크립트가 자동으로 받음)

`setup_megan32.sh`가 아래 7개를 받고 md5로 확인한다. 이미 있으면 받지 않고 md5만 다시 확인한다.

| 저장 위치 (`$HOME/CMAQ_MODEL/` 기준) | 크기 | md5 | 출처 | 내용 |
|---|---:|---|---|---|
| `MEGAN/archives/MEGAN32_Prep_Code_Jan_2022.tar.gz` | 14MB | `74ce3cb0d51c36491aee1f154aea5f2c` | [Zenodo 19478384](https://zenodo.org/records/19478384) | MEGAN 3.2 전처리기(Fortran) — 생태유형·생육형·캐노피 |
| `MEGAN/archives/MEGANv3.21.tar.gz` | 268MB | `c0b414050ded9a0ec729c9de535d4272` | [Zenodo 10526206](https://zenodo.org/records/10526206) | MEGAN 3.21 — 이 중 `src/TXT2IOAPI`만 사용 |
| `MEGAN/archives/MEGEFP321.zip` | 37MB | `d508f490f21d9c2dbfa07e26b4f7e058` | UCI MEGAN 자료 페이지의 Google Drive 링크 | 배출계수 처리기 EFP(파이썬) |
| `DATA/EMIS/MEGAN/EFP240120.zip` | 0.4MB | `6386b90e27c2e6257bb8566d91f30f4c` | [Zenodo 10939297](https://zenodo.org/records/10939297) | 배출계수표 `EFv240120.csv`, 종 구성표 4종 |
| `DATA/EMIS/MEGAN/EVT3d.zip` | 11MB | `802690a4ff267389efe2cfc68539fdac` | 같음 | 생태유형 30초 전지구 `EVT3d.nc`(1.4GB) |
| `DATA/EMIS/MEGAN/GFv7nc.zip` | 358MB | `536817caab2c66f78d48d969e9bfe4d7` | 같음 | 생육형 피복(%) 30초 전지구 `TC/SC/GC/CC30s7.nc` |
| `DATA/EMIS/MEGAN/NCAR_d312006/veg_GrowthFormFracions.nc` | 4.1GB | `4ce552caa67171b68652406d219235cb` | [NCAR GDEX d312006](https://gdex.ucar.edu/datasets/d312006/) | 이 중 `nl_tree`(나무 중 침엽수 %)·`trop_tree`(나무 중 열대수 %)만 사용 |

NCAR 파일은 약 1.2~1.7MB/s로 40분 정도 걸렸다(2026-11-15). 같은 자료실의 `veg_Ecotypes.nc`·`veg_LAIv.nc`·`soil_*.nc`는 받지 않는다(생태유형은 `EVT3d.nc` 사용, LAI는 MCIP 값 사용, 토양 NO는 YL95라 BDSNP 입력 불필요).

## 4. 처리 원칙과 결정

| 항목 | 결정 | 이유 |
|---|---|---|
| 생물성 모델 | CCTM 인라인 MEGAN 3.2, 4개 도메인 공통 | [SMOKE 03 §9.2](../smoke/03_SMOKE_Emission_Improvement_Plan.md#busan-inline-megan) |
| 전처리 범위 | 전처리기 → EFP → txt2ioapi까지만 | CMAQ 5.4 이상에서는 시간 의존 계산을 CCTM이 함. 오프라인 MEGAN 단계는 실행하지 않음 |
| 식생 원자료 | 전지구 자료(EVT3d, GFv7, NCAR `nl_tree`·`trop_tree`) | 27KM(중국·일본 포함)부터 01KM까지 같은 자료로 일관 처리. 국내 임상도 반영은 후속 개선(§10) |
| 침엽/열대 비율 | NCAR d312006 `nl_tree`, `trop_tree` ÷ 100 | 캐노피 전처리기가 요구하는 `NTfrac`·`tropfrac`(나무 중 비율, 0~1)과 같은 정의. 부산 주변 표본에서 나무 피복 2%·76% 셀이 모두 85~100으로 나와 "나무 중 %"임을 확인 |
| 캐노피 입력 범위 | 위도 18~56°, 경도 90~162°로 잘라 사용 | 27KM 영역(위도 19.6~54.2°, 경도 91.2~160.8°) 포함. 전처리기가 입력 변수를 실수 두 벌로 읽어 전지구는 약 5.8GB 필요 → 7GB 서버에서 위험 |
| 생육형 전처리 | 저메모리판(`grwform_lowmem`) 사용 | 원본은 4개 입력의 격자 캐시를 끝까지 들고 있어 27KM에서 메모리 부족. 결과는 원본과 바이트 단위로 같음(01KM 확인) |
| 생태유형 결측(65535) | 셀 안에 유효 값이 일부 있으면 그 값들로 비율 재배분, 셀 전체가 결측이면 격자 거리로 가장 가까운 유효 셀의 구성 복사 | 해안 셀이 대부분. 수면 셀은 MCIP LAI가 0에 가까워 배출 영향이 작으므로 육지·수면에 같은 규칙 적용. 셀별 처리 기록을 남김 |
| EFP 종 구성표 | 도메인에 있는 생태유형만 남겨 사용 | 전체 표를 쓰면 배출계수 없는 수종 확인 질문에서 멈추고, 부산 도메인에 불필요한 대량 계산 발생 |
| 단위 | CT3는 %(0~100) 그대로 | CMAQ 5.5 `megan_fx_mod.f90`이 캐노피 값에 `0.01`을 곱함(직접 확인) |
| LAI | MCIP LAI 사용(`USE_MEGAN_LAI N`) | LAI 입력 파일은 만들지 않음 |
| 토양 NO | YL95(`BDSNP_MEGAN N`) | BDSNP 입력 5종은 만들지 않음 |
| 결과 보관 | `DATA/EMIS/MEGAN/GRID/<좌표계>_<도메인>/` | 사례가 아니라 격자에 묶인 자료. 격자가 같으면 다른 기간·사례에서 재사용 |

## 5. 설치·컴파일·공용 자료 준비 (한 번만)

### 5.1 실행

```bash
cd ~/megan_files
nohup bash setup_megan32.sh > ~/megan_setup.log 2>&1 &
tail -f ~/megan_setup.log        # 끝 줄에 "setup_megan32.sh 완료"
```

프로젝트 루트가 다르면 `MODEL=/경로 bash setup_megan32.sh`로 실행한다. 이미 받은 파일·만든 폴더는 건너뛰므로 끊기면 같은 명령을 다시 실행한다. 내려받기를 빼면 약 3~4분 걸린다(캐노피 입력 생성 약 20초).

### 5.2 스크립트가 하는 일과 원본 대비 수정 사항

| 단계 | 내용 | 원본 대비 수정 |
|---|---|---|
| 1. 내려받기 | 3.2의 7개 파일, md5 확인 | — |
| 2. 압축 풀기 | `MEGAN/MEGAN32_Prep_Code_Jan_2022/`, `MEGAN/MEGANv3.21/`, `MEGAN/MEGEFP32/` | — |
| 3. 전처리기 컴파일 | `prepmegan4cmaq_{ecotype,grwform_lowmem,cantype}.x` 3개 | ① `prepmegan4cmaq_cantype.f90` 979행 출력 형식 `I` → `I0` (gfortran은 폭 없는 `I` 형식을 오류로 처리) ② `prepmegan4cmaq_grwform_lowmem.f90`을 패치로 생성 (입력 변수마다 `clear_grid_cache` 호출). 배포본 `Makefile`은 `ifort` 전용이라 쓰지 않고 `gfortran -O2 -fallow-argument-mismatch`로 직접 컴파일 |
| 4. txt2ioapi 컴파일 | `MEGAN/MEGANv3.21/bin/txt2ioapi` | 배포본 `makefile`의 `-qopenmp`를 `-fopenmp`로 바꾼 `makefile.gcc` 사용. I/O API 헤더(`*.EXT`)를 72열에서 잘라 `ioapi_fixed/`에 복사해 포함(고정형식 소스와 함께 읽을 때 오류 방지). `-ffixed-line-length-132 -std=legacy` |
| 5. EFP 수정 | `MEGAN/MEGEFP32/src/run_M3EFP.py` | pandas 2.x에서 없어진 `DataFrame.append`를 `pd.concat`으로 교체(원본은 `.orig`) |
| 6. 원자료 정리 | `EVT3d.nc`, `GFv7nc/`, `EFP240120/` 압축 해제 | ① `efp_utf8/`: 배출계수표·종 구성표를 cp1252 → UTF-8 변환(원본 그대로는 EFP가 `UnicodeDecodeError`) ② `GFv7nc/SC30s7_SCpercent.nc`: 배포본 관목 파일의 변수 이름이 `CCpercent`로 잘못 들어 있어 `SCpercent`로만 바꾼 복사본 |
| 7. 캐노피 입력 | `DATA/EMIS/MEGAN/cantype_EA/` 6개 | §4의 침엽/열대 비율, 동아시아 범위 |

txt2ioapi 컴파일 중 `Initialization string ... was truncated` 경고가 많이 나오지만 정상이다(배포본 `.EXT`의 변수 설명 문자열 길이 문제).

`setup_megan32.sh`는 `cnvt_LDF.F`에서 LDF 읽기 시작 열을 20열에서 21열로 바꾸고 `txt2ioapi`를 다시 컴파일한다. 설치 이력이 있는 시스템에서도 수정된 설치 스크립트를 먼저 실행한다.

### 5.3 확인

```bash
grep -c "FAILED" ~/megan_setup.log                             # 0 (md5 불일치 없음)
ls -l ~/CMAQ_MODEL/MEGAN/MEGAN32_Prep_Code_Jan_2022/prepmegan4cmaq_{ecotype,grwform_lowmem,cantype}.x
ls -l ~/CMAQ_MODEL/MEGAN/MEGANv3.21/bin/txt2ioapi               # → ../src/TXT2IOAPI/txt2ioapi
ls ~/CMAQ_MODEL/DATA/EMIS/MEGAN/efp_utf8 ~/CMAQ_MODEL/DATA/EMIS/MEGAN/cantype_EA
tail -12 ~/megan_setup.log
```

정상 기준(2026-11-15 실행):

```text
crop rows 2880 7440 cols 32400 41040 -> 4560 x 8640
wrote .../cantype_EA/TC30s7.nc TCpercent 0.0 127.0
wrote .../cantype_EA/SC30s7.nc SCpercent 0.0 78.0
wrote .../cantype_EA/GC30s7.nc GCpercent 0.0 100.0
wrote .../cantype_EA/CC30s7.nc CCpercent 0.0 100.0
max coord mismatch (deg): lat 0.0003966483493229589 lon 2.5348292325588773e-05
nl_tree missing/out-of-range cells set to 0: 0
wrote .../cantype_EA/NTfrac_EA.nc NTfrac 0.0 1.0
trop_tree missing/out-of-range cells set to 0: 0
wrote .../cantype_EA/tropfrac_EA.nc tropfrac 0.0 1.0
done
setup_megan32.sh 완료
```

`TCpercent` 최댓값 127은 결측값(127)이다. 전처리기가 `treefillvalue='127'`로 제외한다. 좌표 차이는 30초 격자 간격(0.00833°)의 절반보다 충분히 작다.

## 6. 도메인별 입력 생성

### 6.1 입력 파일과 생성 파일

**입력 (도메인마다 사용)**

| 역할 | 위치·파일 | 쓰는 프로그램 | 구분 |
|---|---|---|---|
| 격자 좌표 | `CASES/BUSAN/TEST_20260901/WRF/wrfout_<dNN>_2026-08-31_00:00:00` | 전처리기 3개 | 기존(WRF) |
| 잘라낼 창 | `MCIP/<도메인>/namelist.mcip`의 `x0, y0, ncolsin, nrowsin` | `run_megan_domain.sh`가 읽어 `.inp`에 기록 | 기존(MCIP) |
| 육지·수면 | `MCIP/<도메인>/GRIDCRO2D_<도메인>.2026083100.nc`의 `LWMASK` | `fill_megan_ecotype.py` (기록용) | 기존(MCIP) |
| 격자 정의 | `MCIP/<도메인>/GRIDDESC_<도메인>` | txt2ioapi | 기존(MCIP) |
| 생태유형 | `DATA/EMIS/MEGAN/EVT3d.nc` (변수 `EVT`, 결측 65535) | `prepmegan4cmaq_ecotype.x` | 신규(내려받음) |
| 생육형 4종 | `DATA/EMIS/MEGAN/GFv7nc/{TC,GC,CC}30s7.nc`, `SC30s7_SCpercent.nc` (결측 127) | `prepmegan4cmaq_grwform_lowmem.x` | 신규(내려받음, SC는 이름 수정본) |
| 캐노피 입력 6종 | `DATA/EMIS/MEGAN/cantype_EA/` | `prepmegan4cmaq_cantype.x` | 신규(5장 생성) |
| 배출계수·종 구성표 | `DATA/EMIS/MEGAN/efp_utf8/EFv240120.csv`, `Speciation{Crop,Herb,Shrub}230822.csv`, `SpeciationTree230921.csv` | `make_efp_inputs.py` → EFP | 신규(UTF-8 변환본) |
| EFP 실행 틀 | `MEGAN/MEGEFP32/MEGAN_EFP.py` | `make_efp_inputs.py` | 배포본 |

**생성 (`CASES/BUSAN/TEST_20260901/EMIS/MEGAN/` 아래)**

| 위치·파일 | 내용 | 만드는 프로그램 |
|---|---|---|
| `<도메인>/ecotype.inp`, `growthform.inp`, `cantype.inp` | 전처리기 설정 (namelist) | `run_megan_domain.sh` |
| `<도메인>/grid_ecotype.csv` | 셀별 생태유형 ID·비율 (결측 65535 포함) | `prepmegan4cmaq_ecotype.x` |
| `<도메인>/grid_growth_form.csv` | 셀별 나무·작물·관목·초본 비율 (0~1) | `prepmegan4cmaq_grwform_lowmem.x` |
| `<도메인>/CT3.csv` | 셀별 캐노피 6종 비율 (%) | `prepmegan4cmaq_cantype.x` |
| `<도메인>/filled/grid_ecotype.csv` | 결측을 채운 생태유형 | `fill_megan_ecotype.py` |
| `<도메인>/filled/ecotype_fill_record.csv` | 셀별 처리 방법·참조 셀·거리·LWMASK·식생 비율 | `fill_megan_ecotype.py` |
| `EFP/MEGAN_EFP_<도메인>.py`, `EFP/inputs/EFP/*.<도메인>.csv` | EFP 실행 파일과 도메인용 입력 | `make_efp_inputs.py` |
| `EFP/outputs/OutputGridEF.<도메인>.csv` | 셀별 배출계수 19종·광의존 비율 4종 | EFP |
| `<도메인>/CT3_<도메인>.ncf`, `EFMAP_<도메인>.ncf`, `LDF_<도메인>.ncf` | CCTM 입력 (I/O API NetCDF) | txt2ioapi |
| `../../LOG/megan_<도메인>_{ecotype,growthform,cantype,ecotype_fill,efp_inputs,efp,txt2ioapi}.log` | 단계별 로그 | 각 단계 |

**최종 설치 (`DATA/EMIS/MEGAN/GRID/EASTASIA_<도메인>/`)**: 위 NetCDF 3개, `GRIDDESC_<도메인>`, `md5sum.txt`.

### 6.2 실행

```bash
cd ~/megan_files
C=$HOME/CMAQ_MODEL/CASES/BUSAN/TEST_20260901
WRF_START=2026-08-31_00:00:00 MCIP_STAMP=2026083100 \
  nohup bash run_megan_domain.sh "$C" 01KM 03KM 09KM 27KM > "$C/LOG/megan_run_domains.log" 2>&1 &
tail -f $C/LOG/megan_run_domains.log      # 끝 줄에 "run_megan_domain.sh 완료"
```

다른 사례에서는 `WRF_START`와 `MCIP_STAMP`에 사용할 파일명의 시각을 각각 지정한다. 스크립트는 해당 이름과 일치하는 입력을 사용하며, 파일을 읽을 수 없으면 중단한다. 도메인 하나만 다시 만들 때는 같은 명령에서 도메인 목록을 `01KM` 하나로 줄인다. 같은 도메인을 다시 실행하면 결과를 덮어쓴다.

### 6.3 도메인마다 하는 일

| 순서 | 단계 | 내용 | 걸린 시간·메모리 (2026-11-15) |
|---|---|---|---|
| 1 | 생태유형 | `EVT3d.nc`를 MCIP 격자로 면적 가중 집계 → `grid_ecotype.csv` | 18~32초, 최대 약 6.0GB |
| 2 | 생육형 | GFv7 4종 → `grid_growth_form.csv` | 1분 5초~2분 5초, 최대 약 6.0GB |
| 3 | 캐노피 유형 | `cantype_EA` 6종 → `CT3.csv` (침엽 = 나무×(1−열대)×NT, 활엽 = 나무×(1−열대)×(1−NT), 열대 = 나무×열대) | 5~8초(27KM 1분 31초), 약 0.6GB |
| 4 | 결측 채우기 | `fill_megan_ecotype.py` (§4 규칙). 모든 셀의 비율 합을 1로 맞춤 | 수 초 |
| 5 | EFP | `make_efp_inputs.py`로 입력·실행 파일 생성 후 `MEGAN_EFP_<도메인>.py` 실행 | 약 4초 |
| 6 | NetCDF 변환 | txt2ioapi (`RUN_EFS/LDF/CANTYP=T`, 나머지 `F`) | 1초 미만 |
| 7 | 설치 | `DATA/EMIS/MEGAN/GRID/EASTASIA_<도메인>/`에 복사, md5 기록 | — |

각 단계가 실패하면 스크립트가 바로 멈춘다(`set -e`, 전처리기 로그의 `megan_bio_emiss is done`, 셀 수, txt2ioapi의 `Normal Completion` 확인).

txt2ioapi 환경변수 중 캐노피 출력 파일의 논리 이름은 배포본 실행 예제의 `CANTYP`가 아니라 **`CANTYPFILE`**이다(`txt2ioapi.F`). `CANTYP`로 지정하면 실행 폴더에 `CANTYPFILE`이라는 이름의 파일이 생긴다.

## 7. 확인

### 7.1 로그

```bash
C=$HOME/CMAQ_MODEL/CASES/BUSAN/TEST_20260901
grep -e "^==" -e "installed" -e "vegetated" -e "ecotypes in domain" -e "완료" $C/LOG/megan_run_domains.log
grep -l "Normal Completion" $C/LOG/megan_*_txt2ioapi.log | wc -l          # 4
grep -h "VegIDs without EF" $C/LOG/megan_*_efp_inputs.log | grep -v "EF 0 \[\]"   # 출력 없음이 정상
```

### 7.2 격자 대조와 값 점검

```bash
python3 - <<'EOF'
from netCDF4 import Dataset
import numpy as np
M="/home/woogon/CMAQ_MODEL"; C=M+"/CASES/BUSAN/TEST_20260901"
for dom in ["01KM","03KM","09KM","27KM"]:
    g=Dataset(f"{C}/MCIP/{dom}/GRIDCRO2D_{dom}.2026083100.nc"); lw=np.asarray(g["LWMASK"][0,0])
    G=f"{M}/DATA/EMIS/MEGAN/GRID/EASTASIA_{dom}"
    fs={f:Dataset(f"{G}/{f}_{dom}.ncf") for f in ["CT3","EFMAP","LDF"]}
    ok=all((x.NCOLS,x.NROWS,x.XORIG,x.YORIG,x.XCELL)==(g.NCOLS,g.NROWS,g.XORIG,g.YORIG,g.XCELL) for x in fs.values())
    c=np.asarray(fs["CT3"]["CTS"][:,0]); tree=c[0]+c[1]+c[2]
    iso=np.asarray(fs["EFMAP"]["EF_ISOP"][0,0]); mt=np.asarray(fs["EFMAP"]["EF_MT_PINE"][0,0])
    nan=sum(int(np.isnan(np.asarray(x[v][:])).sum()) for x in fs.values() for v in x.variables if v!="TFLAG")
    print(dom, "MCIP격자일치",ok, "NaN",nan, "육지식생%% %.1f"%c.sum(0)[lw==1].mean(),
          "침엽/나무%% %.0f"%(100*c[0].sum()/tree.sum()), "EF_ISOP육지 %.2f"%iso[lw==1].mean(),
          "EF_MT_PINE육지 %.3f"%mt[lw==1].mean())
EOF
```

정상 기준(2026-11-15):

| 도메인 | 격자 (열×행, 간격) | 생태유형 수 | 결측 채운 식생 셀 (MCIP 육지/수면) | 육지 식생 피복 평균 | 나무 중 침엽수 | EF_ISOP 육지 평균 | EF_MT_PINE 육지 평균 |
|---|---|---:|---|---:|---:|---:|---:|
| 01KM | 78×70, 1km | 2 | 628 (325/303) | 74.8% | 73% | 4.64 | 0.402 |
| 03KM | 83×83, 3km | 3 | 866 (418/448) | 87.3% | 62% | 6.18 | 0.456 |
| 09KM | 67×82, 9km | 5 | 901 (366/535) | 84.8% | 53% | 5.31 | 0.376 |
| 27KM | 174×128, 27km | 70 | 1,482 (613/869) | 81.7% | 71% | 3.72 | 0.261 |

기존 세 파일은 MCIP 격자와 일치했고 NaN은 0개였다. 결측 채운 식생 셀 수는 결측 처리 전 집계(`LOG/megan_ecotype_gap_summary.tsv`)와 4개 도메인 모두 일치한다. 27KM의 70개 생태유형은 모두 배출계수표에 대응 수종이 있어 0으로 처리된 수종이 없다.

**LDF 열 매핑 검증.** EFP CSV는 `gridID, EF1…EF19, LDF3…LDF6` 순서다. 기존 변환기는 20열부터 읽어 `EF19`를 `LDF03`에 넣고 `LDF6`을 누락했다. 01KM에서 `LDF03`이 1을 넘는 육지 셀은 9개였으며, 최대 셀(`gridID=4873`)의 NetCDF 값 `1.0025`는 CSV의 `EF19`와 같았다. 해당 셀의 실제 CSV `LDF3`는 `0.50125`다. 값 자르기로 처리하지 않고 읽기 시작 열을 바로잡았다. 다른 도메인에도 동일한 열 매핑 오류가 적용된다.

수정본은 설치 전에 `LDF03…LDF06` 각각을 CSV의 `LDF3…LDF6`와 모든 격자에서 대조한다. 결측·비유한 값·0~1 범위 초과·값 불일치가 하나라도 있으면 중단하고, 통과 결과는 `LOG/megan_<도메인>_ldf_validation.log`에 남긴다.

수정한 변환기를 별도 임시 폴더에서 컴파일해 기존 네 도메인의 EFP CSV를 변환했다. 01·03·09·27KM 모두 네 LDF 변수의 범위와 CSV 일치 검사를 통과했다. **이후 2026-11-16 사용자 제공 운영 서버 출력에서 새로 생성한 도메인별 검증 로그와 운영 LDF 파일의 일치가 확인되어, 기존 '운영 LDF 교체 필요' 항목은 완료로 갱신한다(아래 7.2.1).**

CT3 관목·초본·작물은 `grid_growth_form.csv`와 0.0001 이내로 같다. 나무 합(침엽+열대+활엽)은 01KM에서 평균 0.2%p, 최대 2%p 차이가 있다(별도 원인 확인하지 않음, 영향 작음).

### 7.2.1 운영 LDF 최종 확인 (2026-11-16 사용자 제공 Linux 서버 출력)

CASE: `/home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901`. 운영 경로: `/home/woogon/CMAQ_MODEL/DATA/EMIS/MEGAN/GRID/EASTASIA_<도메인>/`.

1. `CASE/LOG/megan_<도메인>_ldf_validation.log`를 확인했다. 4도메인 × 4변수(`LDF03`~`LDF06`)에서 모두 `CSV/NetCDF match`가 출력되었다. 최솟값은 전부 0이고 최대값은 아래 표와 같이 1 이하다.
2. `CASE/EMIS/MEGAN/<도메인>/LDF_<도메인>.ncf`와 운영 `DATA/EMIS/MEGAN/GRID/EASTASIA_<도메인>/LDF_<도메인>.ncf`를 `md5sum` 및 `cmp -s`로 비교했다. 4도메인 모두 해시 동일 및 **운영 파일 일치**가 출력되었다.

| 도메인 | LDF03 최대 | LDF04 최대 | LDF05 최대 | LDF06 최대 | LDF MD5 (사례=운영) | 판정 |
|---|---:|---:|---:|---:|---|---|
| 27KM | 0.499700 | 0.799520 | 0.299820 | 0.399760 | `6f13d108626d7614d371fef5151f16a3` | 통과 |
| 09KM | 0.497400 | 0.795840 | 0.298440 | 0.397920 | `00d1f70e3ff2f76542ca0dd0e2c5aab3` | 통과 |
| 03KM | 0.498950 | 0.798320 | 0.299370 | 0.399160 | `46fd164e3b886c1afca89f8f96c37c5d` | 통과 |
| 01KM | 0.501250 | 0.802000 | 0.300750 | 0.401000 | `4bb3ff52d9a3cd4114fcf6da1b5d95b7` | 통과 |

**검증 범위:** 위 결과는 사용자가 제공한 서버 터미널 출력에 근거한다. GitHub 문서 수정 과정에서 서버에 직접 접속하거나 NetCDF를 별도 재분석하지 않았다. LDF 전처리의 값 일치·운영본 동일성은 확인되었지만 **CCTM에서 실제로 해당 파일을 읽고 식생배출량을 계산하는지는 미검증**이다.

### 7.3 재현 검증 (2026-11-15)

이 문서의 `files/` 7개만으로 처음부터 다시 만들어 기존 결과와 비교했다. 같은 서버의 별도 폴더(`/home/woogon/megan_repro/MODEL`)에서 `MODEL`을 바꿔 `setup_megan32.sh`와 `run_megan_domain.sh <사례> 01KM 03KM 09KM 27KM`를 실행했다. 대용량 원자료·배포 압축파일은 다시 받지 않고 링크로 연결했으며, md5 확인·압축 해제·수정·컴파일·자료 정리·도메인 실행은 모두 새로 했다. WRF·MCIP 폴더는 기존 사례를 링크했다.

당시 결과는 4개 도메인 모두 중간 CSV 5종과 NetCDF 3종이 일치했다. 두 실행 모두 수정 전 변환기를 사용했으므로, 이 일치는 LDF 열 매핑의 정확성을 검증하지 않는다. 수정 후 LDF는 §7.2의 CSV 대조 기준으로 검증한다.

| 도메인 | `grid_ecotype.csv` | `grid_growth_form.csv` | `CT3.csv` | 결측 채운 생태유형 | EFP 출력 CSV | `CT3`(1변수) | `EFMAP`(19변수) | `LDF`(4변수) |
|---|---|---|---|---|---|---|---|---|
| 01KM | 바이트 동일 | 바이트 동일 | 바이트 동일 | 바이트 동일 | 바이트 동일 | 값·격자 동일 | 값·격자 동일 | 값·격자 동일 |
| 03KM | 바이트 동일 | 바이트 동일 | 바이트 동일 | 바이트 동일 | 바이트 동일 | 값·격자 동일 | 값·격자 동일 | 값·격자 동일 |
| 09KM | 바이트 동일 | 바이트 동일 | 바이트 동일 | 바이트 동일 | 바이트 동일 | 값·격자 동일 | 값·격자 동일 | 값·격자 동일 |
| 27KM | 바이트 동일 | 바이트 동일 | 바이트 동일 | 바이트 동일 | 바이트 동일 | 값·격자 동일 | 값·격자 동일 | 값·격자 동일 |

NetCDF는 생성 시각이 헤더에 들어가므로 파일 자체가 아니라 `TFLAG`를 뺀 모든 변수 값과 격자 속성(`NCOLS, NROWS, XORIG, YORIG, XCELL, YCELL, GDNAM, P_ALP, P_BET, P_GAM, XCENT, YCENT`)을 비교했다. 4개 도메인 실행에 약 11분 걸렸다(21:20~21:31).

이 검증은 같은 서버·같은 컴파일러·같은 라이브러리에서 한 것이다. 다른 컴퓨터에서는 부록 C 양식으로 기록하고 7.2 표와 비교한다.

## 8. CCTM 연결 (예정, 미실행)

수정된 운영 LDF 파일은 2026-11-16 제공 로그·파일 비교 기준으로 4개 도메인 모두 검증을 통과했다(§7.2.1). **다만 아래 CCTM 연결·실행은 미실행**이므로, 실제 실행에서는 CT3·EFMAP·LDF 경로와 인라인 MEGAN 설정을 추가로 확인한다.

CCTM 실행 스크립트에 아래를 넣는다. 변수 이름과 기본값은 [SMOKE 03 §9.3](../smoke/03_SMOKE_Emission_Improvement_Plan.md#busan-inline-megan)과 같다. `GRID`는 실행 도메인(27KM·09KM·03KM·01KM)이다.

```csh
setenv CTM_BIOGEMIS_MG Y     # 인라인 MEGAN 사용
setenv CTM_BIOGEMIS_BE N     # BEIS 끔 (공식 예제 스크립트는 Y이므로 반드시 N으로 지정)
setenv BDSNP_MEGAN     N     # 토양 NO = YL95
setenv USE_MEGAN_LAI   N     # LAI = MCIP 값
set MGN = $HOME/CMAQ_MODEL/DATA/EMIS/MEGAN/GRID/EASTASIA_${GRID}
setenv MEGAN_CTS  $MGN/CT3_${GRID}.ncf
setenv MEGAN_EFS  $MGN/EFMAP_${GRID}.ncf
setenv MEGAN_LDF  $MGN/LDF_${GRID}.ncf
# 연속 실행: 전날 MEGAN_SOILOUT을 다음 날 MEGAN_SOILINP로 연결 (첫날은 새로 시작)
```

첫 실행에서 확인할 것:

- CCTM 로그에 MEGAN 활성화와 위 세 파일의 열기 기록이 있는지
- 인라인 MEGAN은 배출량 파일을 따로 출력하지 않으므로, `CMAQ_Control_DESID.nml`의 `Desid_DiagVars`에 MEGAN 스트림 진단 규칙을 추가해 이소프렌·모노테르펜·토양 NO의 단위·일변화·공간 분포를 확인
- SMOKE 병합 목록과 CCTM 입력에 생물성 배출(BEIS `b3gts*`, 과거 오프라인 MEGAN 산출물)이 섞이지 않았는지
- 국외 HTAP 농업 부문의 농경지 토양 NOx와 MEGAN 토양 NO의 중복 여부(국외 지역)

## 9. 완료 현황

| 단계 | 상태 |
|---|---|
| 5장 설치·컴파일·공용 자료 | 완료 (2026-11-11 설치, 2026-11-15 NCAR 자료·캐노피 입력 추가) |
| 6장 01·03·09·27KM | CT3·EFMAP 생성 기록, 수정 후 LDF 4개 재생성·CSV/NetCDF 검증 통과 및 운영 파일과 바이트 동일 확인(2026-11-16 사용자 제공 서버 출력) |
| 7.3 별도 폴더 재현 | 기존 전체 전처리 재현은 수정 전 변환기로 2026-11-15 수행. 수정 후 LDF의 CSV 값 일치·운영 파일 동일성은 2026-11-16 별도 확인(§7.2.1). 전체 전처리를 수정본으로 다른 환경에서 재현한 것은 아님 |
| 8장 CCTM 연결·검증 | 미실행 |

## 부록 A. 실행 중 발생한 문제 기록

| 날짜 | 증상 | 원인 | 조치 |
|---|---|---|---|
| 11-11 | `prepmegan4cmaq_cantype.f90:979` 컴파일 오류 `Nonnegative width required` | gfortran은 폭 없는 `I` 형식 불허 | `I` → `I0` (5.2) |
| 11-11 | txt2ioapi `cnvt_cantyp.F` 구문 오류(`-ffixed-line-length-72`) | 72열을 넘는 행 | `-ffixed-line-length-132`, I/O API 헤더는 72열로 잘라 `ioapi_fixed/`에서 포함 (5.2) |
| 11-11 | EFP `UnicodeDecodeError: 'utf-8' codec can't decode byte 0xe1` | 배출계수표·종 구성표가 cp1252 | `iconv -f cp1252 -t utf-8` → `efp_utf8/` |
| 11-11 | EFP `DataFrame.append` 오류 | pandas 2.x에서 삭제 | `pd.concat`으로 교체 |
| 11-11 | 전체 종 구성표로 EFP 실행 시 `Do you want to continue ... (Y/N)` 대기 | 도메인에 없는 생태유형까지 포함, 일부 수종 배출계수 없음 | 도메인 생태유형만 남김(`make_efp_inputs.py`). 남은 질문은 `echo Y`로 응답 |
| 11-11 | 생육형 관목 변수 읽기 실패 | `SC30s7.nc` 변수 이름이 `CCpercent` | 이름만 `SCpercent`로 바꾼 복사본 |
| 11-12 | 27KM 생육형 메모리 부족 | 원본이 4개 입력 격자 캐시 유지 | 저메모리판 패치. 01KM 결과 원본과 바이트 단위 동일 확인 |
| 11-15 | 캐노피 입력 `NTfrac_reorder_lat.nc`, `tropfrac_reorder_lat.nc` 없음 | 배포 설정이 개발자 서버 경로를 가리키고 파일이 배포되지 않음 | NCAR d312006 `nl_tree`·`trop_tree`로 대체(§4) |
| 11-15 | 전지구 입력으로 캐노피 전처리 시 약 5.8GB 필요 | 입력 변수를 실수 두 벌로 읽음 | 동아시아 범위로 자름 |
| 11-15 | txt2ioapi 실행 후 캐노피 출력이 실행 폴더에 `CANTYPFILE`로 생성 | 논리 이름이 `CANTYPFILE` | 환경변수 이름 수정 (6.3) |
| 11-15 | 09·27KM 결측 처리에서 비율 합 검사 실패 | 원자료 CSV가 소수 4자리로 반올림되어 합이 0.9999~1.0001 | 모든 셀 비율을 합 1로 정규화 |
| 11-15 | 03·09·27KM EFP 결과 셀 누락(27KM 22,272셀 중 670셀) | EFP 실행 파일이 01KM 종 구성표(생태유형 2개)를 가리킴 | 실행 파일 생성 방식 수정 후 재실행, 전체 셀 출력 확인 |
| 11-15 | 11-11 01KM 시험 결과(`busan01_covered`)가 이번 결과와 다름 | 생태유형은 정렬 전 창(x0=0, y0=0), 생육형은 정렬 후 창(x0=3, y0=1)으로 만든 것으로 보임 | 사용하지 않음. 이번 결과는 모두 MCIP 창 사용 |

## 부록 B. 현재 서버와 이 문서의 경로 차이

이 문서의 스크립트는 다른 시스템에서 깨끗하게 재현하도록 정리한 것이다. 현재 서버(`/home/woogon/CMAQ_MODEL`)에는 정리 전 작업 경로가 함께 남아 있다. 최종 결과(`DATA/EMIS/MEGAN/GRID/`)는 같은 값이다(§7.3).

| 항목 | 이 문서 | 현재 서버의 기존 작업 |
|---|---|---|
| 01KM 중간 산출물 폴더 | `EMIS/MEGAN/01KM/` | `EMIS/MEGAN/busan01/` (`aligned/`, `checked/`, `filled/`) |
| 관목 이름 수정본 | `DATA/EMIS/MEGAN/GFv7nc/SC30s7_SCpercent.nc` | `EMIS/MEGAN/busan01/checked/growth_inputs/SC30s7_busan.nc` (값·좌표 동일) |
| EFP 시나리오 이름 | `<도메인>` (예: `01KM`) | `busan01_filled`, `busan03_filled`, `busan09_filled`, `busan27_filled` |
| 실행 스크립트 | `run_megan_domain.sh` 하나 | `run_remaining_grids*.sh`, `run_cantype.sh`, `run_txt2ioapi.sh`, `SCRIPTS/megan/*.py` |
| 전처리기 배포 설정 | 사용 안 함 | `MEGAN32_Prep_Code_Jan_2022/*.inp`, `input/`이 개발자 서버 경로(`/glade/...`) 그대로 |

## 부록 C. 재현 기록 양식

```text
작업일시 / 실행자:
호스트 / OS / gfortran / Python·netCDF4·numpy·pandas 버전:
netCDF / I/O API 경로:
GitHub 저장소 커밋 SHA:
내려받은 7개 파일 md5 확인 결과:
사례 / WRF / MCIP 경로, 각 도메인 namelist.mcip의 x0·y0·ncolsin·nrowsin:
도메인별 셀 수 / 생태유형 수 / 결측 채운 식생 셀(육지·수면) / EFP 출력 셀 수:
7.2 표 값과의 차이:
관측된 문제 / 해결 / 남은 검증 항목:
```

## 10. 검토 근거와 과학적 한계

- **식생 자료:** 전지구 위성 기반 자료다. 부산 01KM의 나무 중 침엽수 비율 73%는 실제보다 높을 수 있다. 침엽수는 모노테르펜, 활엽수(참나무류)는 이소프렌 배출계수가 커서 배출 구성에 직접 영향을 준다. 3·1KM는 국내 임상도(침엽·활엽·혼효, 수종)로 침엽 비율과 종 구성을 바꾸는 개선을 후속으로 검토한다. 이때 27·09KM와의 경계 일관성을 함께 확인한다.
- **결측 채우기:** 가장 가까운 유효 셀의 구성을 복사하는 방식은 단순 대체다. 01KM에서 식생 셀이 참조한 셀은 최대 12셀(12km) 떨어져 있다. 도메인별 육지·수면 셀 수와 대체 거리는 기록하고, 이소프렌·모노테르펜 배출에 미치는 영향은 CCTM 진단에서 확인한다.
- **침엽/열대 비율 자료:** 원래 전처리기 입력(`NTfrac_reorder_lat.nc` 등)을 구할 수 없어 같은 정의의 NCAR 자료로 대체했다. 생육형(GFv7)과 출처·버전이 달라 같은 셀에서 정의가 완전히 맞지는 않을 수 있다.
- **MEGAN 3.2 성숙도:** 개발자는 MEGAN 3 공식 논문·사용자 지침이 없고 일반 사용자 지원을 하지 않는다고 밝히고 있다. CMAS 포럼에서는 MEGAN 3.2가 모노테르펜을 많이 만들어 PM2.5를 높이고, MEGAN-YL이 BEIS-YL보다 토양 NO를 적게 모의한다고 안내한다. 기존 체계(27·9km MEGAN v2.04, 3·1km BEIS 3.12)와 결과를 비교할 때 이 차이를 고려한다.
- **검증 범위:** 이 문서의 완료는 입력 파일 생성·격자 일치·값 범위·재현성까지다. 실제 배출량이 맞는지는 CCTM 실행 후 진단 출력으로 확인한다(8장).

관련 문서: [SMOKE 03 §9 생물성 결정](../smoke/03_SMOKE_Emission_Improvement_Plan.md#busan-inline-megan) · [MCIP 가이드](../mcip/MCIP_Installation_Guide.md) · [UCI MEGAN 자료·코드](https://bai.ess.uci.edu/megan/data-and-code) · [MEGAN 3.2 입력 자료(Zenodo 10939297)](https://zenodo.org/records/10939297) · [NCAR GDEX d312006](https://gdex.ucar.edu/datasets/d312006/) · [CMAS 포럼: CMAQ용 MEGAN 3.2 전처리](https://forum.cmascenter.org/t/run-meganv3-2-preprocessor-to-make-needed-files-for-cmaqv5-4/4039)
