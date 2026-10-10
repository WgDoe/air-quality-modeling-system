# CMAQ 모델링 시스템 SMOKE 구축 가이드

**이 문서는 SMOKE 5.3의 소스 다운로드부터 컴파일 완료까지를 다룬다.** 공식 예제 사례(SMOKE-ExampleCase-v3) 실행은 §10에 예정 절차로 정리했으며, 실행이 끝나면 같은 문서에 이어서 기록한다.

## 1. 목적
Rocky Linux 기반 CMAQ 통합 대기질 모델링 시스템의 Phase 5(SMOKE) 설치·컴파일·오류 해결 절차를 하나의 문서로 기록한다.

이 문서는 실제 구축 과정에서 발생한 문제를 모두 해결한 뒤, **처음부터 오류 없이 재현하도록** 순서를 재구성한 것이다. 각 단계의 `> 참고` 상자에는 해당 조치가 필요한 이유와, 생략했을 때 나타나는 오류를 적었다. 실제 구축 중에 겪은 문제의 경위는 [부록 A](#부록-a-구축-중-발생한-문제-기록)에 따로 정리했다.

설치 순서:

```text
4장  공통 실행 규칙 확인
  ↓
5장  SMOKE 5.3 소스 다운로드(태그) + 설치 폴더(SMOKEv5.3) 구성
  ↓
6장  Makeinclude 수정 (GNU 옵션 + netCDF 라이브러리 경로)
  ↓
7장  컴파일 (환경변수 지정 → make dir → make → 확인)
  ↓
10장 공식 예제 사례 실행 (예정)
```

현재 상태(2026-10-10 기준): **SMOKE 5.3 설치·컴파일 완료.** gfortran 11.5.0으로 SMOKE 내부 라이브러리 3개와 실행파일 36개(주 프로그램 19개, 유틸리티 17개)가 생성되었고, `ldd`로 실행 시 필요한 라이브러리를 모두 찾는 것을 확인했다. 공식 예제 사례 실행(§10)과 CAPSS·REAS·자연배출 처리는 아직 수행하지 않았다.

완료 상태는 사용자 제공 실행 화면·컴파일 로그를 근거로 한다. 실행파일이 실제 배출량을 올바르게 계산하는지는 §10의 예제 사례로 검증한다.

## 2. 구축 환경

- OS: Rocky Linux 9.8 (Blue Onyx), x86_64, **시스템 언어 한국어**
- 사용자: `woogon`
- 프로젝트 루트: `/home/woogon/CMAQ_MODEL`
- CPU 코어: 4 / 메모리: 약 7.2 GB / `/home` 여유 공간: 약 494 GB
- GCC / GFortran: 11.5.0
- 공통 라이브러리: HDF5 1.14.6, netCDF-C 4.9.3, netCDF-Fortran 4.6.2, I/O API 3.2-20200828 (`Linux2_x86_64gfort10`)
- 셸: 명령 입력은 bash, SMOKE 실행 스크립트는 csh(tcsh, WRF 단계에서 설치)

선행 문서:

- [공통 라이브러리 구축 기록](../libraries/Common_Libraries_Installation_Guide.md) — I/O API 3.2-20200828 빌드
- [WRF/WPS 설치 가이드](../wrf/WRF_WPS_Installation_Guide.md) — §7의 `libs/netCDF-WRF` 통합 링크 디렉터리
- [MCIP 구축 가이드](../mcip/MCIP_Installation_Guide.md) — 예제 이후 실제 사례에서 SMOKE가 읽을 MCIP 기상자료·GRIDDESC

이 문서는 위 문서의 설치가 끝나 있다고 가정한다.

디렉터리 구조:

[구축 기본계획](../planning/00_CMAQ_Project_Master_Plan.md) §4.2에 따라 SMOKE 원본 저장소는 `src/SMOKE_REPO`에, 실제 빌드에 쓰는 SMOKE 본체는 프로젝트 루트의 버전명 폴더 `SMOKEv5.3`에 둔다. SMOKE는 스크립트와 `Makeinclude`가 `SMK_HOME/subsys/` 아래 구조를 전제로 경로를 찾으므로 이 구조를 그대로 따른다. 예제 사례 등 시험 실행은 `CASES/SMOKE_TEST/` 아래에 둔다.

```text
/home/woogon/CMAQ_MODEL/
├── libs/
│   ├── ioapi-3.2-20200828/        # I/O API (SMOKE가 링크로 참조)
│   └── netCDF-WRF/                # netCDF-C·Fortran 통합 링크 폴더
├── src/
│   ├── SMOKE_REPO/                # SMOKE 원본 저장소 (git clone, 태그 SMOKEv5.3_June2026)
│   └── smoke_example_case_v3.June2026.zip   # 예제 자료 원본 (§10, 예정)
├── SMOKEv5.3/                     # SMK_HOME
│   └── subsys/
│       ├── smoke/                 # SMOKE_REPO 복사본 (assigns, scripts, src, utils)
│       │   ├── src/               # Makeinclude, Makeinclude.orig, Makefile
│       │   └── Linux2_x86_64gfort10/   # 컴파일 결과: 실행파일 36개, *.a, *.mod, 컴파일 로그
│       └── ioapi -> /home/woogon/CMAQ_MODEL/libs/ioapi-3.2-20200828
└── CASES/
    ├── BUSAN/TEST_20260901/       # 실제 사례 (EMIS/에 배출량 결과 예정)
    └── SMOKE_TEST/EXAMPLE_v3/     # 공식 예제 사례 (§10, 예정)
```

---

## 3. 버전 확정

모델 버전은 CMAQ를 먼저 확정하고 나머지를 CMAQ 호환성에 맞춘다(기본계획 §3.5).

| 구성요소 | 버전 | 근거 |
|---|---|---|
| CMAQ | 5.5 | 기준 모델(기본계획 §3.5.2) |
| SMOKE | 5.3 (태그 `SMOKEv5.3_June2026`, 커밋 `f29374bbffe7425973376c3091da634d1a718a62`, 2026-06-26) | 아래 선정 근거 |

선정 근거:

- **기존 라이브러리와 직접 연결된다.** SMOKE 5.3의 `src/Makeinclude`는 I/O API의 `Makeinclude.${BIN}`과 라이브러리를 그대로 불러오므로, 이미 설치한 I/O API 3.2-20200828(`Linux2_x86_64gfort10`)과 netCDF를 새로 설치하지 않고 사용한다. GNU 기준선 원칙(기본계획 §3.4)도 유지된다.
- **CMAQ 5.5와의 호환성은 버전이 아니라 화학 메커니즘이 결정한다.** SMOKE는 I/O API 형식 배출량 파일을 만들고 CMAQ는 이를 읽는다. 실제로 맞춰야 하는 것은 종분배 프로파일(GSPRO)과 CMAQ 화학 메커니즘(예: `cb6r5_ae7_aq`)이며, CAPSS 처리 단계에서 정한다.
- **공식 문서 버전과 일치한다.** 기본계획 §24의 SMOKE 매뉴얼 링크가 5.3 문서다.
- 공식 릴리스 노트상 5.3 배포 실행파일은 GCC/GFortran 14.3.0으로 컴파일되었고 Rocky Linux 9에서 시험되었다. 이번 구축은 배포 실행파일을 쓰지 않고 GFortran 11.5.0으로 직접 컴파일했다.

> **참고: 대안 버전** 5.3은 2026-06 공개 버전이다. GNU 컴파일이나 실행에서 해결하기 어려운 문제가 생기면 직전 안정판 `SMOKEv521_Sep2025`를 대안으로 검토한다. 최신 태그라는 이유만으로 채택하지 않으며, 예제 사례(§10) 검증 결과로 최종 확정한다.

> **참고: master가 아니라 태그로 받는 이유** CMAQ 저장소를 `main`으로 받아 Phase 6 전에 태그 소스를 다시 준비해야 하는 상황이 생겼다(MCIP 가이드 §5.2). 같은 일이 반복되지 않도록 SMOKE는 처음부터 확정 태그로 받는다.

---

## 4. 공통 실행 규칙

[WRF/WPS 가이드 §4](../wrf/WRF_WPS_Installation_Guide.md)의 규칙을 그대로 따른다.

- `make`는 앞에 `LC_ALL=C`를 붙인다.
- 화면 출력은 `2>&1 | tee 로그파일이름`으로 파일에 남긴다. 컴파일 로그는 컴파일 결과 폴더(`Linux2_x86_64gfort10`)에 둔다.
- Windows에서 SFTP로 옮긴 파일은 사용 전에 줄바꿈을 정리한다([Compiler/MPI 가이드 §3.5](../compiler/GNU_Compiler_OpenMPI_Installation_Guide.md)).

```bash
sed -i 's/\r$//' 파일이름
```

> **참고: 생략하면** `Makeinclude` 변수 끝에 보이지 않는 문자(`\r`)가 붙어 경로를 찾지 못하거나, csh 스크립트가 `Command not found` 같은 오류를 낸다.

---

## 5. SMOKE 5.3 소스 다운로드와 설치 폴더 구성

### 5.1 소스 다운로드

재현성을 위해 확정 태그로 내려받는다.

```bash
cd /home/woogon/CMAQ_MODEL/src
git clone -b SMOKEv5.3_June2026 https://github.com/CEMPD/SMOKE.git SMOKE_REPO
cd /home/woogon/CMAQ_MODEL/src/SMOKE_REPO
git describe --tags
git log -1 --format='%H %cd'
ls
```

정상 결과:

```text
SMOKEv5.3_June2026
f29374bbffe7425973376c3091da634d1a718a62 Fri Jun 26 07:26:25 2026 -0400
LICENSE.txt  README.md  assigns  scripts  src  utils
```

> **참고:** 태그로 받으면 `You are in 'detached HEAD' state` 안내가 나온다. 정상이다.

### 5.2 설치 폴더 생성과 소스 복사

`SMOKEv5.3`이 `SMK_HOME`이 된다. 원본 `src/SMOKE_REPO`는 그대로 두고 복사본으로 빌드한다.

```bash
cd /home/woogon/CMAQ_MODEL
mkdir -p SMOKEv5.3/subsys
cp -r /home/woogon/CMAQ_MODEL/src/SMOKE_REPO /home/woogon/CMAQ_MODEL/SMOKEv5.3/subsys/smoke
```

### 5.3 I/O API 링크

I/O API는 새로 설치하지 않고 기존 설치본을 `subsys/ioapi`로 링크한다. 컴파일 결과물은 `subsys/smoke/Linux2_x86_64gfort10/`에 만들어지므로 `libs/` 폴더는 변경되지 않는다.

```bash
cd /home/woogon/CMAQ_MODEL/SMOKEv5.3/subsys
ln -s /home/woogon/CMAQ_MODEL/libs/ioapi-3.2-20200828 ioapi
```

명령이 성공하면 아무 메시지도 출력되지 않는다.

> **참고:** 링크 명령은 반드시 `SMOKEv5.3/subsys` 폴더에서 실행한다. 다른 폴더에서 실행하면 그 폴더에 `ioapi` 링크가 생기고 `subsys/ioapi`는 만들어지지 않는다(부록 A1).

### 5.4 구조 확인

```bash
cd /home/woogon/CMAQ_MODEL/SMOKEv5.3/subsys
ls -l
ls smoke
ls ioapi/ioapi/Makeinclude.Linux2_x86_64gfort10
ls ioapi/Linux2_x86_64gfort10/libioapi.a
ls ioapi/ioapi/fixed_src | head -5
```

정상 결과:

```text
lrwxrwxrwx. 1 woogon woogon ... ioapi -> /home/woogon/CMAQ_MODEL/libs/ioapi-3.2-20200828
drwxr-xr-x. 7 woogon woogon ... smoke
LICENSE.txt  README.md  assigns  scripts  src  utils
ioapi/ioapi/Makeinclude.Linux2_x86_64gfort10
ioapi/Linux2_x86_64gfort10/libioapi.a
ATDSC3.EXT
CONST3.EXT
FDESC3.EXT
IODECL3.EXT
NETCDF.EXT
```

| 확인 대상 | 역할 |
|---|---|
| `ioapi -> ...` | SMOKE가 I/O API를 찾는 경로(`IOBASE = ${SMK_HOME}/subsys/ioapi`) |
| `Makeinclude.Linux2_x86_64gfort10` | SMOKE가 가져오는 gfortran 컴파일 옵션 파일 |
| `libioapi.a` | SMOKE가 링크할 I/O API 라이브러리 |
| `fixed_src/*.EXT` | I/O API include 파일 |

---

## 6. Makeinclude 수정

SMOKE는 `subsys/smoke/src/Makeinclude`에 컴파일 옵션과 라이브러리 경로를 적는다. 배포본은 Intel 컴파일러 기준이고 netCDF 라이브러리 위치를 지정하지 않으므로 두 곳을 고친다.

### 6.1 netCDF 경로 확인

```bash
ls -l /home/woogon/CMAQ_MODEL/libs/netCDF-WRF/lib | grep libnetcdf
```

정상 결과: `libnetcdf.so`가 `libs/netCDF-C-4.9.3/lib/`를, `libnetcdff.so`가 `libs/netCDF-Fortran-4.6.2/lib/`를 가리키는 링크로 보인다(`.a`, `.so.*` 등 함께 표시).

> **참고: netCDF 경로** WRF·MCIP와 같은 통합 링크 폴더 `libs/netCDF-WRF/lib`를 사용한다. I/O API도 같은 netCDF로 빌드되었으므로 SMOKE도 같은 라이브러리를 써야 충돌이 없다.

### 6.2 설정 수정

아래 변경은 태그 원본 `Makeinclude`에 한 번 적용한다. 이미 수정된 파일에 반복 적용하거나 `Makeinclude.orig`를 덮어쓰지 않는다.

```bash
cd /home/woogon/CMAQ_MODEL/SMOKEv5.3/subsys/smoke/src
cp Makeinclude Makeinclude.orig

sed -i \
 -e 's/^ EFLAG = -extend-source 132 -zero/# EFLAG = -extend-source 132 -zero/' \
 -e 's/^# EFLAG = -ffixed-line-length-132  -fno-backslash/ EFLAG = -ffixed-line-length-132  -fno-backslash/' \
 -e 's|^  IOLIB = -L$(IOBIN) -lioapi -lnetcdff -lnetcdf  $|########  netCDF-C/Fortran (libs/netCDF-WRF symbolic-link folder) - added 2026-10-10\nNCLIB = /home/woogon/CMAQ_MODEL/libs/netCDF-WRF/lib\n\n  IOLIB = -L$(IOBIN) -lioapi -L$(NCLIB) -lnetcdff -lnetcdf -Wl,-rpath,$(NCLIB)|' \
 Makeinclude
```

| 설정 | 변경 내용 | 이유 |
|---|---|---|
| `EFLAG` (53~54행) | Intel 줄(`-extend-source 132 -zero`) 주석 처리, GNU 줄(`-ffixed-line-length-132 -fno-backslash`) 사용 | 고정형식 Fortran 132자 줄 옵션이 컴파일러마다 다름 |
| `NCLIB` (새 변수) | `/home/woogon/CMAQ_MODEL/libs/netCDF-WRF/lib` | netCDF 라이브러리 위치 |
| `IOLIB` | `-L$(NCLIB)` 추가 | 링크 시 `-lnetcdff -lnetcdf`를 찾을 위치 지정(부록 A3) |
| `IOLIB` | `-Wl,-rpath,$(NCLIB)` 추가 | 실행 시에도 같은 위치에서 netCDF를 찾도록 실행파일에 경로 기록. `LD_LIBRARY_PATH` 설정과 무관하게 실행됨 |
| `IFLAGS` | 변경 없음 | 배포본의 Intel 줄과 GNU 줄 내용이 동일 |
| I/O API 경로 | 변경 없음 | `${SMK_HOME}/subsys/ioapi` 기준이므로 §5.3 링크로 자동 연결 |

> **참고:** 배포본 `Makeinclude`는 I/O API 경로만 `-L$(IOBIN)`으로 지정한다. netCDF 경로를 추가하지 않으면 소스 컴파일과 SMOKE 내부 라이브러리 생성까지는 정상 진행되다가, 첫 실행파일 링크에서 `cannot find -lnetcdff`로 멈춘다.

### 6.3 수정 결과 확인

```bash
cd /home/woogon/CMAQ_MODEL/SMOKEv5.3/subsys/smoke/src
md5sum Makeinclude.orig Makeinclude
diff Makeinclude.orig Makeinclude
grep -n "EFLAG =\|NCLIB =\|IOLIB =" Makeinclude
```

정상 결과:

```text
9db5c039ee0d8d37e3e35f43fa4677cb  Makeinclude.orig
37dcac609b784d28a95e9aa444a651ed  Makeinclude
```

`grep` 결과에서 GNU `EFLAG` 줄과 `IOLIB`의 활성 줄(맨 앞 `#` 없음)이 다음과 같아야 한다.

```text
54: EFLAG = -ffixed-line-length-132  -fno-backslash       #  GNU   Fortran
71:NCLIB = /home/woogon/CMAQ_MODEL/libs/netCDF-WRF/lib
73:  IOLIB = -L$(IOBIN) -lioapi -L$(NCLIB) -lnetcdff -lnetcdf -Wl,-rpath,$(NCLIB)
```

> **참고: md5 값의 의미** `Makeinclude.orig`의 md5는 태그 `SMOKEv5.3_June2026` 원본 값이다. 다르면 소스 버전이 다르거나 이미 수정된 파일을 백업한 것이다. 수정본 md5가 다르면 `diff`로 차이를 먼저 확인한다.

---

## 7. 컴파일

### 7.1 환경변수 지정

`Makefile`과 `Makeinclude`는 `SMK_HOME`과 `BIN`으로 I/O API 위치, 컴파일 옵션 파일, 결과 폴더를 정한다. 터미널을 닫으면 사라지므로 컴파일은 같은 터미널에서 이어서 진행한다.

```bash
export SMK_HOME=/home/woogon/CMAQ_MODEL/SMOKEv5.3
export BIN=Linux2_x86_64gfort10
echo $SMK_HOME
echo $BIN
```

정상 결과: `/home/woogon/CMAQ_MODEL/SMOKEv5.3`, `Linux2_x86_64gfort10`

> **참고:** `BIN`은 I/O API 빌드 때 사용한 값과 같아야 한다. SMOKE는 `${IODIR}/Makeinclude.${BIN}`과 `${IOBASE}/${BIN}`을 찾으므로, 다른 값이면 옵션 파일이나 `libioapi.a`를 찾지 못한다.

### 7.2 compile

```bash
cd /home/woogon/CMAQ_MODEL/SMOKEv5.3/subsys/smoke/src
make dir
set -o pipefail
LC_ALL=C make 2>&1 | tee ../Linux2_x86_64gfort10/make_SMOKEv5.3_rebuild.log
```

- `make dir`은 결과 폴더 `subsys/smoke/Linux2_x86_64gfort10`을 만든다. `Making ... Linux2_x86_64gfort10`이 출력되면 정상이다.
- Fortran 모듈 생성 순서 문제를 피하기 위해 `-j` 병렬 옵션은 쓰지 않는다.
- 컴파일 중 `Warning`은 많이 출력되어도 무방하다.

> **참고: 이미 컴파일된 부분** `make`는 이미 만들어진 목적파일·라이브러리를 건너뛴다. 설정을 고친 뒤 처음부터 다시 컴파일하려면 같은 환경변수 상태에서 `make clean` 후 실행한다.

### 7.3 compile 결과 확인

```bash
cd /home/woogon/CMAQ_MODEL/SMOKEv5.3/subsys/smoke/Linux2_x86_64gfort10

# 1) 실행파일 개수
ls -F | grep '\*$' | wc -l

# 2) 실행파일 36개가 모두 있는지 이름으로 확인 (빠진 것만 출력)
for f in normbeis3 normbeis4 tmpbeis3 tmpbeis4 cntlmat smkreport grdmat \
         movesmrg met4moves laypoint elevpoint smkinven grwinven smkmerge \
         mrggrid mrgelev spcmat temporal mrgpt \
         aggwndw beld3to2 cemscan extractida geofac invsplit metcombine metscan \
         pktreduc smk2emis surgtool uam2ncf gentpro gcntl4carb layalloc \
         inlineto2d saregroup; do
  [ -x "$f" ] || echo "MISSING: $f"
done

# 3) SMOKE 내부 라이브러리
ls -l libemmod.a libsmoke.a libfileset.a

# 4) 실행 시 라이브러리 확인
ldd smkinven | grep "not found"
ldd smkinven | grep -E "netcdf|hdf5"

# 5) 컴파일 로그 오류 확인
grep -n -i -E "Error [0-9]|undefined reference|cannot find|fatal error" make_SMOKEv5.3_2.log
```

정상 결과:

- 1)은 `36`을 출력한다.
- 2)는 아무것도 출력하지 않는다.
- 3)은 라이브러리 3개가 보인다.
- 4)의 첫 명령은 아무것도 출력하지 않고, 둘째 명령은 `libnetcdff.so`, `libnetcdf.so`, `libhdf5…`가 `/home/woogon/CMAQ_MODEL/libs/...` 경로와 함께 보인다.
- 5)는 **최종 성공 로그**(`make_SMOKEv5.3_2.log`)를 검사하며 아무것도 출력하지 않는다. 새 시스템에서 §7.2를 재현했다면 `make_SMOKEv5.3_rebuild.log`를 검사한다. 최초 실패 로그(`make_SMOKEv5.3.log`)에는 알려진 netCDF 링크 오류가 있으므로 최종 성공 판정에 사용하지 않는다.

주요 실행파일과 역할:

| 실행파일 | 역할 |
|---|---|
| `smkinven` | 배출목록 읽기 |
| `spcmat` | 화학종 분배 행렬 |
| `grdmat` | 공간 배분 행렬 |
| `temporal` | 시간 배분 |
| `laypoint`, `elevpoint` | 점오염원 수직 배분·상승고 |
| `smkmerge`, `mrggrid` | 부문별 병합, 최종 격자 배출량 병합 |
| `normbeis4`, `tmpbeis4` | 생물성 배출(BEIS4) |

> **참고:** 링크 단계에서 `libhdf5… needed by libnetcdf.so, not found` 같은 **warning**이 나올 수 있다. netCDF가 내부적으로 HDF5를 쓰기 때문이며, 실행파일 36개가 만들어지고 4)에 `not found`가 없으면 문제없다.

기존 구축의 `make_SMOKEv5.3.log`(최초 링크 실패) 및 `make_SMOKEv5.3_2.log`(설정 수정 후 최종 완료)는 결과 폴더에 모두 보존한다. §7.2의 `make_SMOKEv5.3_rebuild.log`는 **신규 재현 실행**의 로그 파일명으로 기존 이력을 덮어쓰지 않는다.

---

## 8. 환경 설정 요약

### 8.1 `~/.bashrc`에 추가한 내용

없음. 컴파일은 §7.1의 `export`로 처리했다. 예제·사례 실행 때 필요한 `SMK_HOME` 등은 SMOKE 실행 스크립트(ASSIGNS, `directory_definitions.csh`)에서 지정한다(§10, 예정).

### 8.2 명령 실행 시에만 붙이는 설정

| 설정 | 적용 명령 | 이유 |
|---|---|---|
| `export SMK_HOME=/home/woogon/CMAQ_MODEL/SMOKEv5.3` | `make` | SMOKE 소스·I/O API 경로 기준 |
| `export BIN=Linux2_x86_64gfort10` | `make` | I/O API 옵션 파일·라이브러리 폴더 이름, 결과 폴더 이름 |
| `LC_ALL=C` | `make` | 한국어 로케일 출력 파싱 오류 방지 (WRF/WPS 가이드 4.1) |

### 8.3 소스·설정 수정 사항

| 파일 | 조치 | 원본 보관 |
|---|---|---|
| `SMOKEv5.3/subsys/ioapi` | `libs/ioapi-3.2-20200828` 심볼릭 링크 생성 (5.3) | - |
| `SMOKEv5.3/subsys/smoke/src/Makeinclude` | EFLAG GNU 전환, `NCLIB` 추가, `IOLIB`에 netCDF 경로·rpath 추가 (6.2) | `Makeinclude.orig` |

---

## 9. 완료 현황

| 구성요소 | 버전 | 위치 | 결과 | 상태 |
|---|---|---|---|---|
| SMOKE 저장소 | 5.3 (태그 `SMOKEv5.3_June2026`, 커밋 `f29374b`) | `src/SMOKE_REPO` | - | 내려받기 완료 |
| SMOKE 본체 | 5.3 | `SMOKEv5.3/subsys/smoke` | `Linux2_x86_64gfort10/` 실행파일 36개 | 컴파일 완료(2026-10-10), `ldd` 확인 완료 |
| 공식 예제 사례 | ExampleCase-v3 (EPA 2022v2, CB6) | `CASES/SMOKE_TEST/EXAMPLE_v3` | - | 미수행(§10) |

Phase 5 SMOKE 중 설치·컴파일은 완료로 기록한다(2026-10-10). 다음 작업은 공식 예제 사례 실행(기본계획 §10.2의 1번)이다.

---

## 10. 공식 예제 사례 실행 (예정)

**아래는 아직 수행하지 않은 예정 절차다.** 실행이 끝나면 실제 명령과 결과로 이 장을 갱신한다.

### 10.1 예제 사례 개요

SMOKE 5.3 릴리스에서 예제가 [SMOKE-ExampleCase-v3](https://github.com/CEMPD/SMOKE-ExampleCase-v3)로 갱신되었다.

- 자료: 미국 EPA 2022v2 배출 모델링 플랫폼, 시나리오 `2022he_cb6_22m`(CB6 계열)
- 영역: 미국 롱아일랜드 일대 12 km, 25×25 격자(LISTOS 격자)
- 부문: 면오염원(afdust, rail, rwc, fertilizer, livestock, nonpt, nonroad, np_oilgas), 점오염원(pt_oilgas, ptnonipm, ptegu, ptfire, cmv, airports 등), 도로이동(onroad), 생물성(BEIS4)
- 출력: 하루 단위 저고도 격자 배출량 1개 + inline 점오염원 배출량 파일들

### 10.2 폴더 배치

예제는 설치 검증용 시험 사례이므로 계산 결과가 쌓이는 `CASES/` 아래에 둔다. 원본 압축파일은 `src/`에 보관한다. 예제 패키지의 자체 폴더 구조(`2022he_cb6_22m`, `ge_dat`, `ioapi`, `met`, `smoke5.2`)를 그대로 사용하며, 실행 로그는 결과 폴더 안에 함께 저장한다.

```text
src/smoke_example_case_v3.June2026.zip       # 원본 보관
CASES/SMOKE_TEST/EXAMPLE_v3/                 # 압축 해제·실행
```

### 10.3 자료 내려받기

예제 자료는 GitHub가 아니라 Google Drive에 있다. 리눅스 데스크톱 웹브라우저에서 아래 주소를 열어 내려받는다. 용량이 커서 바이러스 검사 안내가 나오면 "무시하고 다운로드"를 선택한다.

```text
https://drive.google.com/file/d/1C8euCzvgv7CSlaL75hRH2U0NTOyYNeQ_/view?usp=sharing
```

```bash
mv ~/다운로드/smoke_example_case_v3.June2026.zip /home/woogon/CMAQ_MODEL/src/
cd /home/woogon/CMAQ_MODEL/src
ls -lh smoke_example_case_v3.June2026.zip
file smoke_example_case_v3.June2026.zip
mkdir -p /home/woogon/CMAQ_MODEL/CASES/SMOKE_TEST/EXAMPLE_v3
```

> **참고:** 공식 설명서는 파일 이름이 `.zip`인데 압축 해제는 `tar -xvzf`로 안내한다. `file` 결과로 실제 형식을 확인한 뒤 맞는 명령으로 푼다.

### 10.4 이후 예정 단계

1. `CASES/SMOKE_TEST/EXAMPLE_v3`에 압축 해제
2. `2022he_cb6_22m/scripts/directory_definitions.csh`의 `INSTALL_DIR`을 예제 폴더로 수정
3. 예제에 포함된 `smoke5.2` 실행파일 대신 **이번에 컴파일한 SMOKE 5.3 실행파일**(`SMOKEv5.3/subsys/smoke/Linux2_x86_64gfort10`)을 쓰도록 실행 경로 지정 — 이번 예제의 목적은 직접 컴파일한 실행파일의 검증이다
4. 부문 순서(nonpoint → point → onroad → beis4 → merge)대로 실행하고 정상 종료 확인

---

## 부록 A. 구축 중 발생한 문제 기록

이 문서의 절차는 아래 문제들을 해결한 결과다. 같은 증상을 만났을 때 원인을 찾는 용도로 남긴다.

| 번호 | 단계 | 증상 | 원인 | 예방 조치 |
|---|---|---|---|---|
| A1 | 설치 폴더 구성 | `ls -l` 결과에 `smoke`만 있고 `ioapi/...` 파일 확인 시 `그런 파일이나 디렉터리가 없습니다` | `subsys` 폴더에서 `ln -s`가 실행되지 않아 `subsys/ioapi` 링크가 없음 | 5.3 `subsys`에서 링크 생성, 5.4 `ls -l`로 화살표 확인 |
| A2 | Makeinclude | 배포본 컴파일 옵션이 Intel(`-extend-source 132 -zero`) | 배포본 기본값이 Intel Fortran | 6.2 EFLAG GNU 줄로 전환 |
| A3 | compile(링크) | 소스·내부 라이브러리 컴파일 후 `normbeis3` 링크에서 `/usr/bin/ld: cannot find -lnetcdff`, `cannot find -lnetcdf`, `make: *** [Makefile:687: normbeis3] Error 1` | 배포본 `IOLIB`에 netCDF 라이브러리 경로(`-L`)가 없음 | 6.2 `NCLIB` 추가, `IOLIB`에 `-L$(NCLIB)`, `-Wl,-rpath,$(NCLIB)` 추가 |
| A4 | 전반 | Windows에서 옮긴 파일 사용 오류 | CRLF 줄바꿈 | 4장 `sed -i 's/\r$//'` |

진단에 사용한 명령:

```bash
# A1: 링크 존재 확인
ls -l /home/woogon/CMAQ_MODEL/SMOKEv5.3/subsys

# A3: 링크 오류 위치와 netCDF 라이브러리 확인
tail -5 /home/woogon/CMAQ_MODEL/SMOKEv5.3/subsys/smoke/Linux2_x86_64gfort10/make_SMOKEv5.3.log
ls -l /home/woogon/CMAQ_MODEL/libs/netCDF-WRF/lib | grep libnetcdf
grep -n "IOLIB =" /home/woogon/CMAQ_MODEL/SMOKEv5.3/subsys/smoke/src/Makeinclude
```

구축 경위:

- 처음에는 `master` 브랜치로 내려받도록 안내했으나, 기본계획의 재현성 원칙에 따라 확정 태그 `SMOKEv5.3_June2026`으로 내려받는 방식으로 정했다.
- `Makeinclude`는 실제로 두 차례에 나눠 수정했다. 첫 수정은 EFLAG만 바꿨고(md5 `370ed46db430703b8461440ba048b406`), A3 오류 후 netCDF 경로를 추가했다(md5 `37dcac609b784d28a95e9aa444a651ed`). 두 수정 모두 Windows에서 만든 파일을 SFTP로 덮어쓰는 방식이었다. 이 문서의 §6.2는 같은 최종 결과를 `sed` 한 번으로 만드는 명령이며, 최종 md5가 일치함을 확인했다.
- 실제 컴파일 로그는 두 개다. `make_SMOKEv5.3.log`는 A3 오류로 멈춘 첫 실행, `make_SMOKEv5.3_2.log`는 netCDF 경로 추가 후 링크부터 이어서 완료한 실행이다. 두 로그 모두 이력으로 보존한다. §7.2의 `_rebuild.log`는 이후 신규 재현 시 덮어쓰기를 피하기 위한 별도 이름이다.
- 예제 사례 위치는 처음에 `tests/smoke_example_v3`로 검토했으나, 계산 결과가 쌓이는 곳을 `CASES/`로 통일하기 위해 `CASES/SMOKE_TEST/EXAMPLE_v3`로 정했다.

## 11. 검토 근거 및 관련 문서

공식 소스 확인(2026-10-10): 태그 `SMOKEv5.3_June2026`의 커밋과 `src/Makeinclude`, `src/Makefile`(실행파일 목록·`make dir` 규칙), `assigns/ASSIGNS.*`(`SMK_HOME/subsys` 구조) 내용을 공식 저장소에서 직접 확인했다. §6.2 `sed` 명령은 태그 원본에 적용해 최종 md5가 실제 사용한 파일과 같음을 확인했다. 서버의 컴파일 결과는 사용자 제공 화면·로그에 근거한다.

- [SMOKE GitHub 저장소](https://github.com/CEMPD/SMOKE)
- [SMOKE v5.3 릴리스 노트](https://github.com/CEMPD/SMOKE/releases/tag/SMOKEv5.3_June2026)
- [SMOKE 공식 홈페이지](https://www.cmascenter.org/smoke/)
- [SMOKE 5.3 User's Guide](https://www.cmascenter.org/smoke/documentation/5.3/html/)
- [SMOKE Wiki: Instructions for SMOKE Installation](https://github.com/CEMPD/SMOKE/wiki/B.-Instructions-for-SMOKE-Installation)
- [SMOKE-ExampleCase-v3](https://github.com/CEMPD/SMOKE-ExampleCase-v3)
- [구축 기본계획 및 Phase 현황](../planning/00_CMAQ_Project_Master_Plan.md) §3.5, §10, §22 Phase 5
- [MCIP 구축 가이드](../mcip/MCIP_Installation_Guide.md)
- [WRF/WPS 설치 가이드](../wrf/WRF_WPS_Installation_Guide.md)
- [공통 라이브러리 구축 기록](../libraries/Common_Libraries_Installation_Guide.md)