# CMAQ 모델링 시스템 CCTM 구축 가이드 (설치·컴파일·벤치마크)

> **문서 순서:** 00 목차 → **01 설치(이 문서)** → 02 부산 CASE 실행. [CMAQ 문서 목차](00_README_First.md)를 확인하세요.
>
> **이 문서는 설치·컴파일 문서다.** 새 시스템에서 한 번, 또는 화학 메커니즘·소스·라이브러리를 바꿀 때만 따른다. 부산 CASE의 ICON·BCON 생성과 CCTM 실행은 02 문서에서 다룬다.

## 1. 목적

Rocky Linux 기반 CMAQ 통합 대기질 모델링 시스템의 Phase 6에서 CMAQ 5.5 CCTM을 GNU 컴파일러로 빌드하고, EPA 공식 벤치마크(2018-07-01~02, 12NE3)로 빌드를 검증한 절차를 다른 시스템에서 그대로 재현할 수 있도록 기록한다.

설치 순서:

```text
선행  MCIP 가이드 §5~6: CMAQ 소스·프로젝트 폴더(CMAQv5.5)·config_cmaq.csh
  ↓
3장  소스 버전 확인 (태그 CMAQv5.5.0.3_11Jul2025)
  ↓
4장  CCTM 빌드 (bldit_cctm.csh 기본 설정, gcc)
  ↓
5장  빌드 확인
  ↓
6장  벤치마크 실행 (EPA 입력 자료, 1회)
  ↓
7장  벤치마크 결과를 EPA gcc 참조 결과와 비교
```

현재 상태(2026-11-25 서버 확인): **CCTM `cb6r5_ae7_aq` + `m3dry` 빌드 완료(2026-11-11), 벤치마크 2일 정상 종료(2026-11-22~23), EPA gcc 참조 결과와 비교 완료.** ICON·BCON은 아직 빌드하지 않았다(8장).

> 근거: 이 문서의 값은 2026-11-25에 서버의 빌드 폴더(`CCTM_v55.cfg`, `Makefile.gcc`, 실행파일), 벤치마크 실행 로그, 비교 결과 파일을 직접 읽어 확인한 것이다. 빌드 당시의 화면 기록(`bldit_cctm.log`)은 남아 있지 않아, 4장 명령은 확인된 설정과 같은 설정을 재현하기 위한 표준 명령으로 적었다.

## 2. 구축 환경과 선행 조건

- OS: Rocky Linux 9.8, 사용자 `woogon`, 프로젝트 루트 `/home/woogon/CMAQ_MODEL`, CPU 4코어, 메모리 약 7.5 GB
- 컴파일러: GCC/GFortran 11.5.0, MPI: OpenMPI 4.1.1(`mpifort`)
- 라이브러리: HDF5 1.14.6, netCDF-C 4.9.3, netCDF-Fortran 4.6.2(통합 링크 `libs/netCDF-WRF`), I/O API 3.2-20200828
- 선행 문서:
  - [공통 라이브러리](../libraries/Common_Libraries_Installation_Guide.md), [GNU Compiler/OpenMPI](../compiler/GNU_Compiler_OpenMPI_Installation_Guide.md)
  - [MCIP 가이드 §5~6](../mcip/MCIP_Installation_Guide.md): `src/CMAQ_REPO` 소스, `bldit_project.csh`로 만든 `CMAQv5.5` 프로젝트 폴더, `config_cmaq.csh`의 gcc 라이브러리 경로 10개

`config_cmaq.csh`는 MCIP 가이드 §6에서 설정한 그대로 쓴다. CCTM 빌드를 위해 따로 고친 곳은 없다. 서버의 원본 대비 변경은 `CMAQ_REPO` 경로 1줄과 gcc 항목 경로 10줄뿐이다.

## 3. 소스 버전 확인

```bash
cd /home/woogon/CMAQ_MODEL/src/CMAQ_REPO
git describe --tags --always
git log -1 --format='%H %ci'
git status --short
```

정상 결과(2026-11-25):

```text
CMAQv5.5.0.3_11Jul2025
e10d0a04f319d6be6db086bc66ba13ce4044987b 2025-07-11 08:49:44 -0400
 M PREP/mcip/src/Makefile
 M bldit_project.csh
?? PREP/mcip/src/Makefile.orig
```

로컬 수정은 MCIP 가이드에서 바꾼 두 파일뿐이며 CCTM 소스는 원본 그대로다. 기준 태그는 [03 개선 계획 §7.3](../smoke/03_SMOKE_Emission_Improvement_Plan.md#busan-mechanism)과 같다.

## 4. CCTM 빌드

### 4.1 빌드 설정 (원본 `bldit_cctm.csh` 기본값, 수정 없음)

`CMAQv5.5/CCTM/scripts/bldit_cctm.csh`는 `src/CMAQ_REPO/CCTM/scripts/bldit_cctm.csh`와 내용이 같다(수정 없음). 기본값으로 다음 빌드가 만들어진다.

| 항목 | 값 | 설정 위치 |
|---|---|---|
| 컴파일러 | `gcc` (`mpifort`, `gcc`) | 실행 인자 |
| 화학 메커니즘 | `cb6r5_ae7_aq` | `bldit_cctm.csh` 기본값 ([03 §7.3](../smoke/03_SMOKE_Emission_Improvement_Plan.md#busan-mechanism)에서 확정) |
| 건성침적 | `m3dry` (`DepMod`) | 기본값 |
| 병렬 | MPI (`ParOpt`) | 기본값 |
| 추적자 | `trac0` | 기본값 |
| ISAM·DDM-3D·WRF 양방향 | 끔 | 기본값 |
| 최적화 플래그 | `-O3 -funroll-loops -finit-character=32 -Wtabs -Wsurprising -ftree-vectorize -ftree-loop-if-convert -finline-limit=512` | `config_cmaq.csh` gcc 항목 |
| 빌드 폴더 | `CMAQv5.5/CCTM/scripts/BLD_CCTM_v55_gcc_cb6r5_ae7_aq_m3dry/` | 자동 |

### 4.2 빌드 재현 절차

```bash
cd /home/woogon/CMAQ_MODEL/CMAQv5.5/CCTM/scripts
set -o pipefail
LC_ALL=C ./bldit_cctm.csh gcc 2>&1 | tee bldit_cctm.log
```

4코어에서 수십 분 걸린다. `bldit_cctm.csh`가 `config_cmaq.csh gcc`를 스스로 읽으므로 따로 `source`하지 않는다. 다시 빌드할 때는 기존 `BLD_…` 폴더를 다른 이름으로 옮긴 뒤 실행하고, `bldit_cctm.log`를 남긴다.

## 5. 빌드 확인

```bash
B=/home/woogon/CMAQ_MODEL/CMAQv5.5/CCTM/scripts/BLD_CCTM_v55_gcc_cb6r5_ae7_aq_m3dry
ls -l $B/CCTM_v55.exe
grep -E '^(sha_ID|mechanism|f_compiler)' $B/CCTM_v55.cfg
grep -o -- '-Dm3dry_opt\|-Dparallel' $B/CCTM_v55.cfg | sort -u
test -x "$B/CCTM_v55.exe" || exit 1
links=$(ldd "$B/CCTM_v55.exe") || exit 1
if grep -F "not found" <<< "$links"; then exit 1; fi
```

정상 결과:

```text
-rwxr-xr-x. 1 woogon woogon 152516832 11월 11 20:08 …/CCTM_v55.exe
sha_ID      e10d0a04f3;
mechanism   cb6r5_ae7_aq;
f_compiler  mpifort;
-Dm3dry_opt
-Dparallel
```

`ldd`가 성공하고 라이브러리 목록에 `not found`가 없어야 한다. 실행파일은 `libs/netCDF-Fortran-4.6.2`, `libs/netCDF-C-4.9.3`, `libs/HDF5-1.14.6`, `/usr/lib64/openmpi/lib`의 라이브러리를 쓴다. 빌드 폴더에는 메커니즘 파일(`GC/AE/NR_cb6r5_ae7_aq.nml`, `CMAQ_Control_DESID*.nml`, `CSQY_DATA_cb6r5_ae7_aq`, `OMI_1979_to_2019.dat` 등)이 함께 복사되며, 실행 스크립트가 이 폴더를 `NMLpath`로 쓴다.

## 6. 벤치마크 실행 (빌드 검증, 1회)

### 6.1 자료

| 자료 | 위치 | 출처 |
|---|---|---|
| 입력 | `DATA/CMAQ_BENCHMARK/CMAQv5.4_2018_12NE3_Benchmark_2Day_Input/` (압축 `…tar.gz` 11,076,011,430 B) | [EPA/CMAS 배포 입력](https://cmaq-release-benchmark-data-for-easy-download.s3.amazonaws.com/v5_5/CMAQv5.4_2018_12NE3_Benchmark_2Day_Input.tar.gz). 기존 서버 파일의 다운로드 주소 기록은 없음 |
| 참조 결과 | `DATA/CMAQ_BENCHMARK/REF_OUTPUT/output_CCTM_v55_gcc_Bench_2018_12NE3_cb6r5_ae7_aq_m3dry/` (압축 16,112,328,634 B) | `https://cmaq-release-benchmark-data-for-easy-download.s3.amazonaws.com/v5_5/output_CCTM_v55_gcc_Bench_2018_12NE3_cb6r5_ae7_aq_m3dry.tar.gz` (2026-11-23 내려받기 기록) |

새 시스템에서는 아래 방법으로 입력과 참조 결과를 준비한다. 배포본의 공식 체크섬은 이 문서에서 확인하지 못했다. 아래 SHA-256은 내려받은 파일을 후속 재현에서 식별하는 데 쓴다.

```bash
(
set -euo pipefail
D=/home/woogon/CMAQ_MODEL/DATA/CMAQ_BENCHMARK
mkdir -p "$D/REF_OUTPUT"
cd "$D"
BASE=https://cmaq-release-benchmark-data-for-easy-download.s3.amazonaws.com/v5_5
INPUT=CMAQv5.4_2018_12NE3_Benchmark_2Day_Input.tar.gz
REF=output_CCTM_v55_gcc_Bench_2018_12NE3_cb6r5_ae7_aq_m3dry.tar.gz
curl -fL --retry 3 -o "$INPUT.part" "$BASE/$INPUT"
mv "$INPUT.part" "$INPUT"
curl -fL --retry 3 -o "$REF.part" "$BASE/$REF"
mv "$REF.part" "$REF"
sha256sum "$INPUT" "$REF" > benchmark_archives.sha256
tar -xzf "$INPUT"
tar -xzf "$REF" -C REF_OUTPUT
)
```

### 6.2 CASE 폴더

입력은 복사하지 않고 링크로 연결한다.

```bash
D=/home/woogon/CMAQ_MODEL/DATA/CMAQ_BENCHMARK/CMAQv5.4_2018_12NE3_Benchmark_2Day_Input/2018_12NE3
C=/home/woogon/CMAQ_MODEL/CASES/CMAQTEST/CMAQ_benchmark
mkdir -p $C/{config,CMAQ/input,CMAQ/output,EMIS,MCIP,LOG,POST}
ln -sfn $D/icbc     $C/CMAQ/input/icbc
ln -sfn $D/epic     $C/CMAQ/input/epic
ln -sfn $D/surface  $C/CMAQ/input/surface
ln -sfn $D/emis     $C/EMIS/emis
ln -sfn $D/met/mcipv5.4 $C/MCIP/mcipv5.4
```

### 6.3 실행 스크립트 (공식 스크립트의 CASE 사본)

공식 `CMAQv5.5/CCTM/scripts/run_cctm_Bench_2018_12NE3_CB6R5.csh`(MD5 `39a30cbf79e5d35a040b829512691110`, 저장소 원본과 동일)를 복사해 [`files/run_cctm_benchmark.patch`](files/run_cctm_benchmark.patch)를 적용한다.

```bash
C=/home/woogon/CMAQ_MODEL/CASES/CMAQTEST/CMAQ_benchmark
(
set -euo pipefail
mkdir -p "$HOME/cmaq_files"
REF=main # 재현 기록에는 실제 커밋 SHA를 남긴다.
curl -fsSL -o "$HOME/cmaq_files/run_cctm_benchmark.patch" "https://raw.githubusercontent.com/WgDoe/air-quality-modeling-system/$REF/docs/cmaq/files/run_cctm_benchmark.patch"
cd "$C/config"
SRC=/home/woogon/CMAQ_MODEL/CMAQv5.5/CCTM/scripts/run_cctm_Bench_2018_12NE3_CB6R5.csh
test ! -e run_cctm_benchmark.csh
cp "$SRC" run_cctm_benchmark.csh
patch -p1 --dry-run < "$HOME/cmaq_files/run_cctm_benchmark.patch"
patch -p1 < "$HOME/cmaq_files/run_cctm_benchmark.patch"
chmod +x run_cctm_benchmark.csh
md5sum run_cctm_benchmark.csh
)
```

`~/cmaq_files/`는 저장소의 `docs/cmaq/files/`에서 패치 파일을 받아 둔 폴더다. 정상 결과: EPA 태그 원본에 저장소의 수정 패치를 적용한 사본의 MD5는 `d4edd6444b668437532cefb7c499eaf5`다. 아래 벤치마크 결과는 기존 서버 실행 기록이며, 수정 패치로 모델을 다시 실행한 결과는 아니다.

패치 내용:

| 변경 | 원본 | 벤치마크 사본 | 이유 |
|---|---|---|---|
| 컴파일러 | `intel` | `gcc` | GNU 빌드 사용 |
| 작업 폴더·입출력 | `${CMAQ_DATA}/…` | `CASES/CMAQTEST/CMAQ_benchmark/` 아래 `config`, `CMAQ/output`, `LOG`, 링크된 입력 | CASE 폴더 규칙 |
| 프로세서 | `NPCOL 8 × NPROW 4` (32개) | `1 × 1` | 시험 당시 설정. 4코어 장비에서는 `2 × 2`도 가능하나 미검증 |
| `CLOBBER_DATA` | `TRUE` | `FALSE` | 기존 출력이 있으면 덮어쓰지 않고 중단 |
| CMAQ 환경 설정 | 실행 위치 기준 상대 경로 | `CMAQv5.5`에서 `config_cmaq.csh`를 읽고 CASE의 `config`로 복귀 | CASE 사본의 실행 위치에서 설정을 찾을 수 있도록 함 |
| 재실행 안내 | 덮어쓰기 옵션 안내 | 기존 출력과 로그를 보관한 후 재실행 | 기존 결과 보호 |

### 6.4 실행

`CLOBBER_DATA=FALSE`로 기존 출력과 로그를 보호한다. 재실행 전 이전 출력·로그를 보관하고, 빈 출력·로그 디렉터리를 준비한다.

```bash
cd /home/woogon/CMAQ_MODEL/CASES/CMAQTEST/CMAQ_benchmark/config
nohup ./run_cctm_benchmark.csh > ../LOG/benchmark_run.log 2>&1 &
echo $! > ../LOG/benchmark.pid
```

확인:

```bash
C=/home/woogon/CMAQ_MODEL/CASES/CMAQTEST/CMAQ_benchmark
tail -6 $C/LOG/benchmark_run.log
grep -c 'PROGRAM COMPLETED SUCCESSFULLY' $C/LOG/CTM_LOG_000.*
ls $C/CMAQ/output | wc -l
```

정상 결과(2026-11-22 18:48 시작, 프로세서 1개):

```text
Num  Day        Wall Time
01   2018-07-01   33144.02
02   2018-07-02   34700.09
     Total Time = 67844.11
      Avg. Time = 33922.05
```

`CTM_LOG_000.*` 두 파일 모두 `1`. 출력은 날짜별 `CCTM_ACONC/AELMO/BSOILOUT/BUDGET/CGRID/CONC/DRYDEP/MEDIA_CONC/WETDEP1` 등이며 전체 약 18 GB다. 프로세서 1개로 하루 약 9.2시간 걸린다.

## 7. 벤치마크 결과 비교 (EPA gcc 참조 결과)

비교는 `CASES/CMAQTEST/CMAQ_benchmark/POST/`의 파이썬 스크립트(`compare_epa_surface.py`, `compare_epa_3d.py`, `compare_epa_aerosol.py`, `diagnose_aerosol.py`, `check_nitrate_layers.py`)로 했다. 스크립트는 저장소에 아직 등록하지 않았다. 비교할 때 날짜별 동일 시각·격자·층을 맞추고 CONC 파일의 기체와 입자 변수를 대조한다. 기체는 지표층과 전체 35층에서 RMSE와 최대 절대차를 구하고 지표층 Pearson 상관계수를 기록한다. ppmV를 ppb로 표시할 때는 1,000을 곱한다. 입자는 각 결과에서 I·J 모드를 합산한 뒤 지표층·전체 층 RMSE와 최대 절대차를 계산하고 최대 차의 시각·층을 기록한다.

**기체** (`compare_epa_surface.py`·`compare_epa_3d.py`, CONC 파일)

| 날짜 | 물질 | 지표층 r | 지표층 RMSE (ppmV) | 35층 전체 RMSE (ppb) | 35층 최대 차 (ppb) |
|---|---|---:|---:|---:|---:|
| 2018-07-01 | O3 | 1.00000000 | 5.2×10⁻⁷ | 0.00088 | 0.082 |
| | NO2 | 1.00000000 | 1.4×10⁻⁷ | 0.00013 | 0.038 |
| | SO2 | 0.99999998 | 9.1×10⁻⁸ | 0.00003 | 0.019 |
| 2018-07-02 | O3 | 1.00000000 | 6.9×10⁻⁷ | 0.00121 | 0.110 |
| | NO2 | 0.99999999 | 2.1×10⁻⁷ | 0.00024 | 0.044 |
| | SO2 | 0.99999999 | 6.4×10⁻⁸ | 0.00005 | 0.017 |

**입자** (`diagnose_aerosol.py`, µg/m³, I+J 모드 합)

| 날짜 | 성분 | 지표층 RMSE | 35층 전체 RMSE | 최대 차 (위치) |
|---|---|---:|---:|---|
| 2018-07-01 | 질산염 ANO3 | 0.0014 | 0.050 | 2.45 (19시, 29층) |
| | 황산염 ASO4 | 0.0014 | 0.0004 | 0.20 (20시, 1층) |
| | 암모늄 ANH4 | 0.0005 | 0.0043 | 0.40 (21시, 27층) |
| 2018-07-02 | 질산염 ANO3 | 0.0004 | 0.048 | 2.02 (02시, 29층) |
| | 황산염 ASO4 | 0.0004 | 0.0001 | 0.07 (22시, 1층) |
| | 암모늄 ANH4 | 0.0007 | 0.0046 | 0.36 (01시, 27층) |

시각은 UTC, 층 번호는 1부터 센 값이다.

판정(이 문서): 기체는 EPA gcc 참조 결과와 사실상 같다. 입자의 지표층 RMSE는 0.0015 µg/m³ 이하다. 격자별 최대 차는 질산염 상층(27~29층)에서 2 µg/m³ 안팎이지만, 층 평균 차이는 모든 층에서 0.0004 µg/m³ 이하다(`nitrate_layer_analysis.txt`). 이 수치는 이번 빌드 환경에서 참조 결과와 비교한 관측값이다. MPI 프로세서 수와 시스템 라이브러리 차이는 가능한 원인으로 남아 있다.

## 8. 완료 현황

| 구성요소 | 위치 | 상태 |
|---|---|---|
| CMAQ 소스 | `src/CMAQ_REPO` (`CMAQv5.5.0.3_11Jul2025`, `e10d0a0`) | 확인 완료 |
| CCTM `cb6r5_ae7_aq` `m3dry` | `CMAQv5.5/CCTM/scripts/BLD_CCTM_v55_gcc_cb6r5_ae7_aq_m3dry/CCTM_v55.exe` | 빌드 완료 (2026-11-11) |
| 벤치마크 2일 | `CASES/CMAQTEST/CMAQ_benchmark` | 정상 종료, EPA 참조 비교 완료 (2026-11-22~24) |
| ICON | `CMAQv5.5/PREP/icon/scripts/bldit_icon.csh` | **미빌드** — 부산 CASE 준비 전에 빌드 |
| BCON | `CMAQv5.5/PREP/bcon/scripts/bldit_bcon.csh` | **미빌드** |
| ISAM 빌드 | — | 미수행 (Phase 7) |

메커니즘을 바꾸면(예: CRACMM) `bldit_cctm.csh`의 메커니즘을 바꿔 새 빌드 폴더를 만들고, 벤치마크(해당 메커니즘 스크립트)부터 다시 검증한다. 배출량 종분배·DESID 대응도 함께 바꿔야 한다([03 §7.3](../smoke/03_SMOKE_Emission_Improvement_Plan.md#busan-mechanism)).
