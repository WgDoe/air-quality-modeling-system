# CMAQ 모델링 시스템 SMOKE 구축 가이드

**공식 예제 실행 명령을 보려면 [SMOKE 공식 예제 실행](#example-run)으로 이동한다.** 압축 해제, 설정 파일, 실행 전 점검, 면오염원·점오염원·도로이동·생물성 실행, 최종 병합과 결과 확인을 §10에 순서대로 정리했다.

## 부산 실제사례 작업 범위 (2026-10-22 갱신)

공식 예제 실행 완료 이후 부산 사례 진행 기록은 [SMOKE 부산 사례 실행 가이드](SMOKE_Busan_Case_Run_Guide.md)에서 관리한다. 공통 4개 도메인 MCIP 링크, 예제 스크립트 복사·공통 입력 준비는 기존 작업을 계승하며 [부산 실행 가이드 §8](SMOKE_Busan_Case_Run_Guide.md)에 필요한 재구축·검증 내용을 통합했다. 기존 CAPSS 2017 면 입력 준비 및 미실행 명령은 현행 절차에서 제외하고, **2023 시나리오의 점 Smkinven 단독 형식 시험만 정상 종료**했으며 전체 실행은 아직 완료되지 않았다.

**새로운 실행 기준:** 2026-10-22 [배출량 개선 계획](SMOKE_Emission_Improvement_Plan.md)에 따라 `2017capss_cb6`를 미실행 비교 기준선으로 보존하고, 새 `2023capss_cb6`에서 국내 CAPSS 2023·국외 HTAP v3.1을 적용한다. 신규 부문 실행은 **국내 점 09KM부터 시작**한다. 이 문서의 설치·컴파일 및 미국 공식 예제 성공 기록은 유지되며, 부산 신규 시나리오의 SMOKE 결과와 CMAQ 입력 호환성은 별도로 검증한다.

## 1. 목적
Rocky Linux 기반 CMAQ 통합 대기질 모델링 시스템의 Phase 5(SMOKE) 설치·컴파일·소스 수정·공식 예제 검증 절차를 하나의 문서로 기록한다.

이 문서는 실제 구축 과정에서 발생한 문제를 모두 해결한 뒤, **재현에 필요한 조치를 확인할 수 있도록** 순서를 재구성한 것이다. 각 단계의 `> 참고` 상자에는 해당 조치가 필요한 이유와, 생략했을 때 나타나는 오류를 적었다. 실제 구축 중에 겪은 문제의 경위는 [부록 A](#부록-a-구축-중-발생한-문제-기록)에 따로 정리했다.

설치 순서:

```text
4장  공통 실행 규칙 확인
  ↓
5장  SMOKE 5.3 소스 다운로드(태그) + 설치 폴더(SMOKEv5.3) 구성
  ↓
6장  설정·소스 수정 (Makeinclude, procar2pt.f)
  ↓
7장  컴파일 (환경변수 지정 → make dir → make → 확인)
  ↓
10장 공식 예제 실행 (압축 해제 → 설정 → 점검 → 부문별 실행 → 병합 → 확인)
```

현재 상태(2026-10-19 실행 검증 기준): **Phase 5 SMOKE 설치·공식 예제 검증 완료.** SMOKE 5.3을 GFortran 11.5.0으로 컴파일했고(실행파일 36개), SMOKE-ExampleCase-v3(미국 12LISTOS 격자, 2022년 1월)의 면오염원 11개 부문, 점오염원 20개 스크립트, 도로이동 6개 모드와 연료별 병합, 생물성(BEIS4), 최종 병합까지 모두 오류 없이 끝났다. CMAQ 입력용 최종 병합 파일 31개와 굴뚝 배출원 파일 1,032개가 생성되었다.

검증 과정에서 SMOKE 5.3 소스의 결함 1건(`smkinven/procar2pt.f` 지역 포인터 초기화 누락)을 찾아 수정했다. 상세 기록은 [procar2pt.f 수정 기록](SMOKE_procar2pt_Fix.md)에 있다.

완료 상태는 사용자 제공 문서 2개에 기록된 실행 결과를 근거로 한다. 이번 검토에서는 서버 원본 로그·netCDF 산출물을 직접 열거나 모델을 재실행하지 않았다. 도로이동 결과는 예제에 포함된 EPA 계산 결과와 파일 구성을, 생물성 정규화 배출량은 EPA 계산 결과와 값을 직접 비교했다. 부산 사례(CAPSS·REAS·자연배출) 처리와 SMOKE 결과의 CMAQ 실행 검증은 아직 수행하지 않았다.

## 2. 구축 환경

- OS: Rocky Linux 9.8 (Blue Onyx), x86_64, **시스템 언어 한국어**
- 사용자: `woogon` (sudo 권한 없음, 시스템 패키지 설치는 `su -`로 root 전환)
- 프로젝트 루트: `/home/woogon/CMAQ_MODEL`
- CPU 코어: 4 / 메모리: 약 7.2 GB / `/home` 여유 공간: 약 494 GB
- GCC / GFortran: 11.5.0
- 공통 라이브러리: HDF5 1.14.6, netCDF-C 4.9.3, netCDF-Fortran 4.6.2, I/O API 3.2-20200828 (`Linux2_x86_64gfort10`)
- 셸: 명령 입력은 bash, SMOKE 실행 스크립트는 csh(tcsh, WRF 단계에서 설치)
- 파이썬: 시스템 기본 Python 3.9, 사용자 설치 모듈 `future`·`numpy`·`scipy`·`netCDF4`(§10.4)
- 작업 컴퓨터: 같은 구성의 컴퓨터 2대를 번갈아 사용. 사용자 계정에 설치하는 파이썬 모듈은 **컴퓨터마다 따로** 설치한다.

선행 문서:

- [공통 라이브러리 구축 기록](../libraries/Common_Libraries_Installation_Guide.md) — I/O API 3.2-20200828 빌드, M3TOOLS
- [WRF/WPS 설치 가이드](../wrf/WRF_WPS_Installation_Guide.md) — §7의 `libs/netCDF-WRF` 통합 링크 디렉터리
- [MCIP 구축 가이드](../mcip/MCIP_Installation_Guide.md) — 부산 사례에서 SMOKE가 읽을 MCIP 기상자료·GRIDDESC

이 문서는 위 문서의 설치가 끝나 있다고 가정한다.

디렉터리 구조:

[구축 기본계획](../planning/00_CMAQ_Project_Master_Plan.md) §4.2에 따라 SMOKE 원본 저장소는 `src/SMOKE_REPO`에, 실제 빌드에 쓰는 SMOKE 본체는 버전명 폴더 `SMOKEv5.3`에 둔다. SMOKE는 실행 스크립트와 `Makeinclude`가 `SMK_HOME/subsys/` 아래 구조를 전제로 경로를 찾으므로 그 구조를 따른다. 공식 예제 등 시험 실행은 `CASES/SMOKE_TEST/` 아래에 둔다.

```text
/home/woogon/CMAQ_MODEL/
├── libs/
│   ├── ioapi-3.2-20200828/        # I/O API (SMOKE가 링크로 참조)
│   └── netCDF-WRF/                # netCDF-C·Fortran 통합 링크 폴더
├── src/
│   ├── SMOKE_REPO/                # SMOKE 원본 저장소 (태그 SMOKEv5.3_June2026)
│   └── smoke_example_case_v3_June2026.zip   # 공식 예제 원본 (4.3 GB)
├── SMOKEv5.3/                     # SMK_HOME
│   └── subsys/
│       ├── smoke/                 # SMOKE_REPO 복사본
│       │   ├── src/               # Makeinclude(.orig), smkinven/procar2pt.f(.orig)
│       │   └── Linux2_x86_64gfort10/   # 실행파일 36개, *.a, *.mod, 컴파일 로그
│       └── ioapi -> /home/woogon/CMAQ_MODEL/libs/ioapi-3.2-20200828
└── CASES/
    ├── BUSAN/TEST_20260901/       # 실제 사례 (EMIS/는 이후 단계)
    └── SMOKE_TEST/
        └── smoke_example_case_v3/ # 공식 예제 (압축 해제 13 GB)
```

수정 파일 보관:

설정·소스 수정은 Windows에서 수정본을 만들어 SFTP로 덮어쓰는 방식으로 한다. 재현을 위해 이번에 제공된 수정본 4개를 이 저장소의 [`docs/smoke/files/`](files/)에 보관한다. 소스·빌드 파일은 SMOKE 태그 원본과, 예제 설정은 §10.3의 경로 변경 설명과 대조한다. 원본·수정본 md5를 §6.3·§10.3에 적었다.

| 수정본 | 덮어쓸 위치 | 사용 장 |
|---|---|---|
| `Makeinclude` | `SMOKEv5.3/subsys/smoke/src/` | 6.2 |
| `procar2pt.f` | `SMOKEv5.3/subsys/smoke/src/smkinven/` | 6.2 |
| `directory_definitions.csh` | `CASES/SMOKE_TEST/smoke_example_case_v3/2022he_cb6_22m/scripts/` | 10.3 |
| `sectorlist_2022he_cb6_22m_withbeis_withrwc` | 같은 `scripts/` | 10.3 |

---

## 3. 버전 확정

모델 버전은 CMAQ를 먼저 확정하고 나머지를 CMAQ 호환성에 맞춘다(기본계획 §3.5).

| 구성요소 | 버전 | 근거 |
|---|---|---|
| CMAQ | 5.5 | 기준 모델(기본계획 §3.5.2) |
| SMOKE | 5.3 (태그 `SMOKEv5.3_June2026`, 커밋 `f29374bbffe7425973376c3091da634d1a718a62`, 2026-06-26) | 아래 선정 근거 |
| 공식 예제 | SMOKE-ExampleCase-v3 (EPA 2022v2 플랫폼, `2022he_cb6_22m`) | SMOKE 5.3 릴리스와 함께 갱신된 예제 |

선정 근거:

- **기존 라이브러리와 직접 연결된다.** SMOKE 5.3의 `Makeinclude`는 I/O API의 `Makeinclude.${BIN}`과 라이브러리를 그대로 불러오므로, 설치된 I/O API 3.2-20200828과 netCDF를 새로 설치하지 않고 사용한다. GNU 기준선 원칙(기본계획 §3.4)도 유지된다.
- **CMAQ 5.5 입력 호환성은 화학 메커니즘·파일 형식·격자·시간·단위·inline 설정을 함께 확인한다.** SMOKE는 I/O API 형식 배출량 파일을 만들고 CMAQ가 이를 읽는다. 맞춰야 하는 것은 종분배 프로파일과 CMAQ 화학 메커니즘이며, 예제 출력 이름 `cmaq_cb6ae7`과 CMAQ benchmark(`cb6r5_ae7_aq`)가 같은 계열이라는 사실만으로 종별 대응·단위와 설정의 호환성을 보장하지 않는다. 부산 사례 및 CCTM 입력 정합성은 별도 검증한다.
- **공식 문서 버전과 일치한다.** 기본계획 §24의 SMOKE 매뉴얼 링크가 5.3 문서다.
- **공식 예제로 검증했다.** 예제 전 부문과 병합이 오류 없이 끝났다(§10).

> **참고: master가 아니라 태그로 받는 이유** CMAQ 저장소를 `main`으로 받아 Phase 6 전에 태그 소스를 다시 준비해야 하는 상황이 생겼다(MCIP 가이드 §5.2). 같은 일이 반복되지 않도록 SMOKE는 처음부터 확정 태그로 받는다.

> **참고: 대안 버전** 해결하기 어려운 문제가 생기면 직전 안정판 `SMOKEv521_Sep2025`를 대안으로 검토한다. 이때도 §6의 `procar2pt.f` 수정이 필요한지 먼저 확인한다.

---

## 4. 공통 실행 규칙

[WRF/WPS 가이드 §4](../wrf/WRF_WPS_Installation_Guide.md)의 규칙을 따르고, SMOKE에 맞춰 아래를 더한다.

**1) `make`와 SMOKE 실행 스크립트 앞에는 `LC_ALL=C`를 붙인다.**

**2) 화면 출력은 로그 파일로 남긴다.** 컴파일 로그는 결과 폴더(`Linux2_x86_64gfort10`)에, 예제 실행 로그는 `2022he_cb6_22m/run_logs/`에 둔다.

**3) SFTP로 올린 파일은 md5로 확인한다.** 이 문서의 수정본은 [`docs/smoke/files/`](files/)에 보관했고, 원본·수정본 md5를 해당 단계에 적어 두었다. Windows에서 내려받을 때 파일 이름 뒤에 `_1`이나 `.txt`가 붙지 않았는지 확인한다. Windows 줄바꿈이 섞였으면 아래로 정리한다.

```bash
(
sed -i 's/\r$//' 파일이름
)
```

**4) 종료 상태·단계별 로그·산출물 내용을 함께 확인한다. 오류 검색은 보조 점검이다.**

```bash
(
grep -c -E "Segmentation fault|SIGSEGV|ERROR: detected|ERROR: Running" <로그파일>
)
```

결과 `0`은 해당 패턴이 없다는 뜻이며 성공을 보장하지 않는다. `grep` 종료값 1은 패턴 없음, 2 이상은 파일 누락·읽기 오류 등 검사 실패이므로 구분한다. 다음을 모두 확인한 뒤 다음 단계로 진행한다.

- 실행 직후 `$?`로 종료 상태를 보존하고 0인지 확인한다. csh 래퍼가 내부 실패를 숨길 수 있으므로 프로그램별 정상 종료 메시지와 필요한 단계가 모두 실행됐는지도 확인한다.
- 로그가 존재하고 비어 있지 않으며 이번 실행 시각의 기록인지 확인한다. 이전 실행 결과가 섞이지 않은 별도 CASE·로그를 사용한다.
- §10의 부문별 예상 날짜·파일 수·파일 크기와 대표일 매핑을 확인한다. 파일 개수만으로 성공 처리하지 않는다.
- `ncdump -h <결과파일>` 등으로 실제 파일의 가독성, 격자·차원·화학종·단위와 `TFLAG`의 기간·시간 간격을 확인한다. 결측·NaN·비정상 음수 및 배출량 합계·부문별 기여를 QA 보고서와 비교한다.
- 최종 31일 결과의 날짜 누락·중복과 inline/격자 배출량 중복 입력 여부를 확인한다. 도로이동 비교는 파일 구성 확인이며 수치 일치 검증을 뜻하지 않는다.

아래 Bash 블록은 `( … )` 서브셸에서 실행해 실패 시 해당 블록만 중단하며 터미널·SSH 접속은 유지한다. 블록 안의 `cd`는 부모 터미널의 위치를 바꾸지 않는다. 독립 확인 명령은 해당 절의 설치·예제 경로를 기준으로 실행한다. 실패 메시지가 나오면 다음 블록으로 진행하지 않는다.

Bash에서 `tee`를 쓸 때는 `set -o pipefail`을 먼저 설정하고 파이프라인 직후 종료값을 확인한다. 실패하면 후속 계산을 멈춘다. 예제 부문 루프는 비정상 종료 시 중단하도록 아래에 보완했다. 종료값이 0이어도 위 산출물 QA는 별도로 수행한다.

> **참고: 마지막 줄만 보면 비정상 종료를 놓친다** 예제 스크립트는 끝에 로그 분석기를 실행하고 `All message priorities > 1`(정상)을 출력한다. 그런데 로그 분석기는 실제로 만들어진 로그만 검사하므로, 프로그램이 비정상 종료되어 로그에 오류를 남기지 못하면 마지막 줄이 정상으로 나온다. 실제로 `nonpt` 부문에서 `smkinven`이 Segmentation fault로 멈췄는데도 마지막 줄은 정상이었다(부록 A3).

---

## 5. SMOKE 5.3 소스 다운로드와 설치 폴더 구성

### 5.1 소스 다운로드

```bash
(
cd /home/woogon/CMAQ_MODEL/src || exit 1
git clone -b SMOKEv5.3_June2026 https://github.com/CEMPD/SMOKE.git SMOKE_REPO
cd /home/woogon/CMAQ_MODEL/src/SMOKE_REPO || exit 1
git describe --tags
git log -1 --format='%H %cd'
ls
)
```

정상 결과:

```text
SMOKEv5.3_June2026
f29374bbffe7425973376c3091da634d1a718a62 Fri Jun 26 07:26:25 2026 -0400
LICENSE.txt  README.md  assigns  scripts  src  utils
```

> **참고:** 태그로 받으면 `You are in 'detached HEAD' state` 안내가 나온다. 정상이다. `src/SMOKE_REPO`는 원본으로 보관하고 직접 수정하지 않는다.

### 5.2 설치 폴더 생성과 소스 복사

`SMOKEv5.3`이 `SMK_HOME`이 된다. 재설치 시 기존 설치본과 로그는 지우지 않고 실행 시각이 붙은 백업 폴더(`SMOKEv5.3.backup.날짜시각`)로 옮겨 보존한다.

```bash
(
cd /home/woogon/CMAQ_MODEL || exit 1
if [ -e SMOKEv5.3 ] || [ -L SMOKEv5.3 ]; then
  backup="SMOKEv5.3.backup.$(date +%Y%m%dT%H%M%S)"
  [ ! -e "$backup" ] && [ ! -L "$backup" ] || { echo "백업 경로 충돌"; exit 1; }
  mv -T -- SMOKEv5.3 "$backup" || exit 1
fi
mkdir -p SMOKEv5.3/subsys
cp -r src/SMOKE_REPO SMOKEv5.3/subsys/smoke
)
```

> **참고: 백업 폴더 정리** 새 설치본으로 컴파일·검증(§7.3)이 끝나면 `ls -d /home/woogon/CMAQ_MODEL/SMOKEv5.3.backup.*`로 백업 폴더를 확인하고, 더 필요 없으면 직접 지운다. 백업은 자동으로 지워지지 않는다.

### 5.3 I/O API 링크

I/O API는 새로 설치하지 않고 기존 설치본을 `subsys/ioapi`로 링크한다. 컴파일 결과는 `subsys/smoke/Linux2_x86_64gfort10/`에 만들어지므로 `libs/` 폴더는 변경되지 않는다.

```bash
(
cd /home/woogon/CMAQ_MODEL/SMOKEv5.3/subsys || exit 1
ln -s /home/woogon/CMAQ_MODEL/libs/ioapi-3.2-20200828 ioapi
)
```

> **참고:** 링크 명령은 반드시 `SMOKEv5.3/subsys` 폴더에서 실행한다. 다른 폴더에서 실행하면 `subsys/ioapi`가 만들어지지 않는다(부록 A1).

### 5.4 구조 확인

```bash
(
cd /home/woogon/CMAQ_MODEL/SMOKEv5.3/subsys || exit 1
ls -l
ls ioapi/ioapi/Makeinclude.Linux2_x86_64gfort10
ls ioapi/Linux2_x86_64gfort10/libioapi.a
ls ioapi/ioapi/fixed_src | head -3
)
```

정상 결과:

```text
lrwxrwxrwx. 1 woogon woogon ... ioapi -> /home/woogon/CMAQ_MODEL/libs/ioapi-3.2-20200828
drwxr-xr-x. 7 woogon woogon ... smoke
ioapi/ioapi/Makeinclude.Linux2_x86_64gfort10
ioapi/Linux2_x86_64gfort10/libioapi.a
ATDSC3.EXT
CONST3.EXT
FDESC3.EXT
```

| 확인 대상 | 역할 |
|---|---|
| `ioapi -> ...` | SMOKE가 I/O API를 찾는 경로(`IOBASE = ${SMK_HOME}/subsys/ioapi`) |
| `Makeinclude.Linux2_x86_64gfort10` | SMOKE가 가져오는 gfortran 컴파일 옵션 파일 |
| `libioapi.a` | SMOKE가 링크할 I/O API 라이브러리 |
| `fixed_src/*.EXT` | I/O API include 파일 |

---

## 6. 설정·소스 수정

배포본 그대로는 GNU 컴파일러 환경에서 컴파일·실행되지 않는 부분이 두 곳 있다. 수정본 2개를 **컴파일 전에** 넣는다.

### 6.1 netCDF 경로 확인

```bash
(
ls -l /home/woogon/CMAQ_MODEL/libs/netCDF-WRF/lib | grep -E "libnetcdf\.so |libnetcdff\.so "
)
```

정상 결과: `libnetcdf.so`가 `libs/netCDF-C-4.9.3/lib/`를, `libnetcdff.so`가 `libs/netCDF-Fortran-4.6.2/lib/`를 가리키는 링크로 보인다.

> **참고: netCDF 경로** WRF·MCIP와 같은 통합 링크 폴더 `libs/netCDF-WRF/lib`를 사용한다. I/O API도 같은 netCDF로 빌드되었으므로 SMOKE도 같은 라이브러리를 써야 충돌이 없다.

### 6.2 수정본 넣기

**1) 원본 백업**

```bash
(
cd /home/woogon/CMAQ_MODEL/SMOKEv5.3/subsys/smoke/src || exit 1
cp -n Makeinclude Makeinclude.orig
cp -n smkinven/procar2pt.f smkinven/procar2pt.f.orig
)
```

**2) SFTP로 수정본 2개 덮어쓰기**

```text
Makeinclude  →  /home/woogon/CMAQ_MODEL/SMOKEv5.3/subsys/smoke/src/
procar2pt.f  →  /home/woogon/CMAQ_MODEL/SMOKEv5.3/subsys/smoke/src/smkinven/
```

수정 내용:

| 파일 | 위치 | 변경 내용 | 이유 |
|---|---|---|---|
| `Makeinclude` | 53~54행 `EFLAG` | Intel 줄(`-extend-source 132 -zero`) 주석 처리, GNU 줄(`-ffixed-line-length-132 -fno-backslash`) 사용 | 고정형식 Fortran 132자 줄 옵션이 컴파일러마다 다름 |
| `Makeinclude` | 70행 부근 `IOLIB` | `NCLIB = /home/woogon/CMAQ_MODEL/libs/netCDF-WRF/lib` 추가, `IOLIB`에 `-L$(NCLIB)`와 `-Wl,-rpath,$(NCLIB)` 추가 | 배포본에는 netCDF 라이브러리 경로가 없어 링크가 실패함. rpath로 실행 시에도 같은 라이브러리를 찾음 |
| `procar2pt.f` | 처리 시작부(130행 다음) | 지역 포인터 15개를 `NULLIFY`로 초기화하는 9줄 추가 | 초기화되지 않은 포인터 때문에 area-to-point 처리 부문(`nonpt`)에서 `smkinven`이 비정상 종료됨 |

`Makeinclude`의 수정 결과:

```text
53:# EFLAG = -extend-source 132 -zero                       #  Intel Fortran
54: EFLAG = -ffixed-line-length-132  -fno-backslash       #  GNU   Fortran
...
70:########  netCDF-C/Fortran (libs/netCDF-WRF symbolic-link folder) - added 2026-10-10
71:NCLIB = /home/woogon/CMAQ_MODEL/libs/netCDF-WRF/lib
72:
73:  IOLIB = -L$(IOBIN) -lioapi -L$(NCLIB) -lnetcdff -lnetcdf -Wl,-rpath,$(NCLIB)
```

`procar2pt.f`에 추가한 코드:

```fortran
C   begin body of subroutine PROCAR2PT
C.........  CMAQ_MODEL fix (2026-10-18): local pointers have undefined
C           association status until set. With gfortran, ASSOCIATED() on
C           an undefined pointer can return .TRUE., causing a segfault
C           when OLDCMACT etc. are used for sources without MACT data.
        NULLIFY( OLDNPCNT, OLDIPOSCOD, OLDTPFLAG, OLDINVYR, OLDPOLVAL,
     &           OLDCIFIP, OLDCSOURC, OLDCSCC, OLDCISIC, OLDCMACT,
     &           OLDCNAICS, OLDCSRCTYP, OLDCEXTORL, OLDCINTGR,
     &           OLDCSHAPE )
```

> **참고: `Makeinclude`를 고치지 않으면** EFLAG를 그대로 두면 gfortran이 Intel 옵션을 인식하지 못하고, `IOLIB`를 그대로 두면 소스 컴파일과 SMOKE 내부 라이브러리 생성까지는 진행되다가 첫 실행파일 링크에서 `/usr/bin/ld: cannot find -lnetcdff`로 멈춘다(부록 A2).

> **참고: `procar2pt.f`를 고치지 않으면** 컴파일은 정상으로 끝나지만, 예제 `nonpt` 부문에서 `smkinven`이 2~3초 만에 `SIGSEGV: Segmentation fault`로 멈추고, 마지막 병합에서 `nonpt` 파일을 찾지 못해 실패한다. 원인 진단 과정과 근거는 [procar2pt.f 수정 기록](SMOKE_procar2pt_Fix.md)에 있다.

### 6.3 수정 확인

```bash
(
cd /home/woogon/CMAQ_MODEL/SMOKEv5.3/subsys/smoke/src || exit 1
md5sum Makeinclude.orig Makeinclude
md5sum smkinven/procar2pt.f.orig smkinven/procar2pt.f
)
```

정상 결과:

| 파일 | md5 |
|---|---|
| `Makeinclude.orig` (태그 원본) | `9db5c039ee0d8d37e3e35f43fa4677cb` |
| `Makeinclude` (수정본) | `37dcac609b784d28a95e9aa444a651ed` |
| `procar2pt.f.orig` (태그 원본) | `18f8b22c7742fc607db12c0634a0e555` |
| `procar2pt.f` (수정본) | `965d553d45920aec73f55eb87ae49a20` |

> **참고: 원본 md5가 다르면** 소스 버전이 다르거나 이미 수정된 파일을 백업한 것이다. 5.2부터 진행하기 전에 태그와 diff를 확인한다.

---

## 7. 컴파일

### 7.1 환경변수 지정

`Makefile`과 `Makeinclude`는 `SMK_HOME`과 `BIN`으로 I/O API 위치, 컴파일 옵션 파일, 결과 폴더를 정한다. 아래 환경 확인은 서브셸 안에서 이루어지므로, 실제 컴파일·결과 확인 블록에도 같은 환경변수를 각각 지정한다.

```bash
(
export SMK_HOME=/home/woogon/CMAQ_MODEL/SMOKEv5.3
export BIN=Linux2_x86_64gfort10
echo $SMK_HOME
echo $BIN
)
```

정상 결과: `/home/woogon/CMAQ_MODEL/SMOKEv5.3`, `Linux2_x86_64gfort10`

> **참고:** `BIN`은 I/O API 빌드 때 사용한 값과 같아야 한다. SMOKE는 `${IODIR}/Makeinclude.${BIN}`과 `${IOBASE}/${BIN}`을 찾는다.

### 7.2 compile

```bash
(
export SMK_HOME=/home/woogon/CMAQ_MODEL/SMOKEv5.3
export BIN=Linux2_x86_64gfort10
cd $SMK_HOME/subsys/smoke/src || exit 1
make dir || exit 1
set -o pipefail
LC_ALL=C make 2>&1 | tee ../Linux2_x86_64gfort10/make_SMOKEv5.3.log
build_rc=$?; [ "$build_rc" -eq 0 ] || { echo "빌드 실패: $build_rc (다음 단계로 진행하지 말고 로그를 확인한다)"; exit 1; }
)
```

- `make dir`은 결과 폴더 `subsys/smoke/Linux2_x86_64gfort10`을 만든다.
- 몇 분 걸린다. `Warning`도 내용을 검토하며 형식·인자 불일치 등 결과에 영향을 줄 수 있는 경고를 무시하지 않는다.
- Fortran 모듈 생성 순서 문제를 피하기 위해 `-j` 병렬 옵션은 쓰지 않는다.

### 7.3 compile 결과 확인

```bash
(
export SMK_HOME=/home/woogon/CMAQ_MODEL/SMOKEv5.3
export BIN=Linux2_x86_64gfort10
cd $SMK_HOME/subsys/smoke/Linux2_x86_64gfort10 || exit 1
ls -F | grep -c '\*$'
grep -c -E "Error|cannot find|undefined reference" make_SMOKEv5.3.log
ldd smkinven | grep -c "not found"
grep -c "NULLIFY" ../src/smkinven/procar2pt.f
)
```

정상 결과:

| 확인 | 결과 | 의미 |
|---|---|---|
| 실행파일 개수 | `36` | 주 프로그램 19개 + 유틸리티 17개 |
| 컴파일·링크 오류 | `0` | |
| 라이브러리 누락 | `0` | netCDF·HDF5를 모두 찾음 |
| `NULLIFY` 줄 | `7` | 원본에 있던 6줄 + 수정으로 추가한 1줄 |

주요 실행파일과 역할:

| 실행파일 | 역할 |
|---|---|
| `smkinven` | 배출목록 읽기 |
| `spcmat` | 화학종 분배 행렬 |
| `grdmat` | 공간 배분 행렬 |
| `temporal` | 시간 배분 |
| `laypoint`, `elevpoint` | 점오염원 수직 배분·상승고 |
| `smkmerge`, `movesmrg` | 부문별 병합, 도로이동 배출량 계산(활동도 × MOVES 배출계수) |
| `mrggrid` | 부문 결과를 최종 격자 배출량으로 병합 |
| `normbeis4`, `tmpbeis4` | 생물성 배출(BEIS4) |

---

## 8. 환경 설정 요약

### 8.1 `~/.bashrc`에 추가한 내용

없음. 컴파일은 §7.1의 `export`로 처리했고, 예제 실행에 필요한 경로는 예제 스크립트가 `directory_definitions.csh`에서 지정한다.

### 8.2 명령 실행 시에만 붙이는 설정

| 설정 | 적용 명령 | 이유 |
|---|---|---|
| `export SMK_HOME=/home/woogon/CMAQ_MODEL/SMOKEv5.3` | `make` | SMOKE 소스·I/O API 경로 기준 |
| `export BIN=Linux2_x86_64gfort10` | `make` | I/O API 옵션 파일·라이브러리 폴더 이름, 결과 폴더 이름 |
| `LC_ALL=C` | `make`, 예제 실행 스크립트 | 한국어 로케일 출력 파싱 오류 방지 |

### 8.3 소스·설정 수정 사항

| 파일 | 조치 | 원본 보관 |
|---|---|---|
| `SMOKEv5.3/subsys/ioapi` | `libs/ioapi-3.2-20200828` 링크 생성 (5.3) | - |
| `SMOKEv5.3/subsys/smoke/src/Makeinclude` | EFLAG GNU 전환, netCDF 경로·rpath 추가 (6.2) | `Makeinclude.orig` |
| `SMOKEv5.3/subsys/smoke/src/smkinven/procar2pt.f` | 지역 포인터 `NULLIFY` 추가 (6.2) | `procar2pt.f.orig` |
| 예제 `scripts/directory_definitions.csh` | 3곳 수정 (10.3) | `directory_definitions.csh.orig` |
| 예제 `scripts/sectorlist_2022he_cb6_22m_withbeis_withrwc` | 병합 경로 15줄 수정 (10.3) | `….orig` |

### 8.4 컴퓨터마다 필요한 설치

사용자 계정에 설치하므로 작업 컴퓨터마다 한 번씩 설치한다(§10.4).

| 항목 | 설치 방법 | 사용처 |
|---|---|---|
| `python3-pip` | `su -` → `dnf install -y python3-pip` (pip가 없을 때만) | 파이썬 모듈 설치 |
| `future` 1.0.0, `numpy` 2.0.2, `scipy` 1.13.1 | `python3 -m pip install --user future numpy scipy` | `afdust_adj` 연간 요약 |
| `netCDF4` | `python3 -m pip install --user netCDF4` (자체 netCDF·HDF5 포함, `libs/`와 별개) | 병합 후 영역 합계 점검 |

---

## 9. 완료 현황

| 구성요소 | 버전 | 위치 | 결과 | 상태 |
|---|---|---|---|---|
| SMOKE 저장소 | 5.3 (태그 `SMOKEv5.3_June2026`, 커밋 `f29374b`) | `src/SMOKE_REPO` | - | 내려받기 완료 |
| SMOKE 본체 | 5.3 + `procar2pt.f` 수정 | `SMOKEv5.3/subsys/smoke` | 실행파일 36개 | 컴파일 완료(2026-10-19) |
| 공식 예제 | ExampleCase-v3 (2022년 1월, 12LISTOS) | `CASES/SMOKE_TEST/smoke_example_case_v3` | 병합 파일 31개, 굴뚝 배출원 파일 1,032개 | 전 부문 검증 완료(2026-10-19) |

Phase 5 SMOKE 중 설치·컴파일·공식 예제 검증을 완료로 기록한다. 다음 작업은 기본계획 §10.2의 "기존 국내 배출량 처리방식 분석"과 CAPSS 처리다.

---

<a id="example-run"></a>
## 10. SMOKE 공식 예제 실행

### 10.0. 다음 실행 때 따라 할 순서

```text
10.2 압축 풀기
  ↓
10.3 설정 파일 2개 넣기 (directory_definitions.csh, sectorlist)
  ↓
10.4 실행 전 점검 (파이썬 모듈, 실행 권한, 로그 폴더)
  ↓
10.5 면오염원 11개 → 10.6 점오염원 20개 → 10.7 도로이동 8개 → 10.8 생물성
  ↓
10.9 병합과 최종 확인
```

예제 실행 원칙: 폴더 구조·입력자료·스크립트를 유지하고 SMOKE 주 실행파일과 I/O API 도구 경로를 설치본으로 지정한다. 다만 `afdust_adj` 보조 실행파일은 EPA 제공 Intel 빌드를 사용했다(§10.10). 따라서 전체 계산을 GNU 빌드만으로 검증한 것은 아니다.

### 10.1. 예제 개요

SMOKE 5.3 릴리스에서 예제가 [SMOKE-ExampleCase-v3](https://github.com/CEMPD/SMOKE-ExampleCase-v3)로 갱신되었다. GitHub에는 설명서만 있고, 자료는 Google Drive에서 받는다.

| 항목 | 내용 |
|---|---|
| 자료 | EPA 2022v2 배출 모델링 플랫폼, 시나리오 `2022he_cb6_22m` |
| 영역 | 미국 롱아일랜드 일대 12 km, 25×25 격자(`12LISTOS`) |
| 기간 | **2022년 1월** (예제 설명서 일부에 8월로 적혀 있으나 실제 설정은 1월) |
| 출력 메커니즘 | `cmaq_cb6ae7` |
| 기상 | `met_m3wndw` (MCIP 자료) |

예제 자료 내려받기(최초 1회):

```text
https://drive.google.com/file/d/1C8euCzvgv7CSlaL75hRH2U0NTOyYNeQ_/view?usp=sharing
```

리눅스 데스크톱 웹브라우저에서 내려받아 `src/`로 옮긴다. 용량이 커서 바이러스 검사 안내가 나오면 "무시하고 다운로드"를 선택한다.

```bash
(
mv ~/다운로드/smoke_example_case_v3_June2026.zip /home/woogon/CMAQ_MODEL/src/
ls -lh /home/woogon/CMAQ_MODEL/src/smoke_example_case_v3_June2026.zip
file /home/woogon/CMAQ_MODEL/src/smoke_example_case_v3_June2026.zip
)
```

정상 결과: 4.3 GB, `Zip archive data`.

> **참고: 파일 이름과 형식** 실제 파일 이름은 `smoke_example_case_v3_June2026.zip`(밑줄)이다. 공식 설명서는 `tar -xvzf`로 풀도록 안내하지만 실제 형식은 zip이므로 `unzip`을 쓴다.

### 10.2. 압축 풀기

재실행 시 기존 예제 입력·로그·결과는 지우지 않고 실행 시각이 붙은 백업 폴더(`smoke_example_case_v3.backup.날짜시각`)로 옮긴 뒤 새로 푼다. 예제는 풀면 13 GB이므로 `df -h`로 여유 공간을 먼저 확인한다.

```bash
(
mkdir -p /home/woogon/CMAQ_MODEL/CASES/SMOKE_TEST
cd /home/woogon/CMAQ_MODEL/CASES/SMOKE_TEST || exit 1
df -h .
if [ -e smoke_example_case_v3 ] || [ -L smoke_example_case_v3 ]; then
  backup="smoke_example_case_v3.backup.$(date +%Y%m%dT%H%M%S)"
  [ ! -e "$backup" ] && [ ! -L "$backup" ] || { echo "백업 경로 충돌"; exit 1; }
  mv -T -- smoke_example_case_v3 "$backup" || exit 1
fi
cd /home/woogon/CMAQ_MODEL/src || exit 1
unzip -q smoke_example_case_v3_June2026.zip -d /home/woogon/CMAQ_MODEL/CASES/SMOKE_TEST
ls /home/woogon/CMAQ_MODEL/CASES/SMOKE_TEST/smoke_example_case_v3
)
```

정상 결과:

```text
2022he_cb6_22m  clean_up.csh  ge_dat  ioapi  met_m3wndw  met_m3wndw_7day  smoke5.2
```

> **참고: 백업 폴더 정리** 백업은 한 번에 13 GB씩 쌓인다. 새 실행이 끝나 결과를 확인하면 `ls -d /home/woogon/CMAQ_MODEL/CASES/SMOKE_TEST/smoke_example_case_v3.backup.*`로 확인하고, 더 필요 없는 백업은 직접 지운다.

> **참고:** `clean_up.csh`는 결과 정리용 스크립트이므로 실행하지 않는다. `2022he_cb6_22m/RPD_RPHO_RPS_RPV.premerged.tar.gz`는 EPA가 미리 계산한 도로이동 결과(비교용)다. 압축 경로가 `premerged/...`라서 풀면 우리 결과 폴더를 덮어쓰므로 **풀지 않는다**.

### 10.3. 설정 파일 2개 넣기

**1) 원본 백업**

```bash
(
cd /home/woogon/CMAQ_MODEL/CASES/SMOKE_TEST/smoke_example_case_v3/2022he_cb6_22m/scripts || exit 1
cp -n directory_definitions.csh directory_definitions.csh.orig
cp -n sectorlist_2022he_cb6_22m_withbeis_withrwc sectorlist_2022he_cb6_22m_withbeis_withrwc.orig
)
```

**2) SFTP로 수정본 2개를 같은 `scripts/` 폴더에 덮어쓰기**

수정 내용:

| 파일 | 위치 | 원래 값 | 바꾼 값 |
|---|---|---|---|
| `directory_definitions.csh` | 14행 `INSTALL_DIR` | `/proj/ie/proj/SMOKE/htran/smoke_example_case_v3` (EPA 서버) | `/home/woogon/CMAQ_MODEL/CASES/SMOKE_TEST/smoke_example_case_v3` |
| | 46행 `SMOKE_LOCATION` | `$INSTALL_DIR/smoke5.2/Linux_x86_64` (예제 포함 실행파일) | `/home/woogon/CMAQ_MODEL/SMOKEv5.3/subsys/smoke/Linux2_x86_64gfort10` |
| | 54행 `IOAPI_LOCATION` | `$INSTALL_DIR/ioapi` (예제 포함 도구) | `/home/woogon/CMAQ_MODEL/libs/ioapi-3.2-20200828/Linux2_x86_64gfort10` |
| `sectorlist_2022he_cb6_22m_withbeis_withrwc` | 15줄의 `projectroot` 칸 | `/home/cmas/training` (CMAS 교육 서버) | `/home/woogon/CMAQ_MODEL/CASES/SMOKE_TEST/smoke_example_case_v3` |

`directory_definitions.csh`의 원래 줄은 지우지 않고 주석으로 남겼다. 그 밖의 설정(기상자료, 메커니즘, 병합 방식, 병합 대상 부문)은 원본 그대로다.

**3) 확인**

```bash
(
cd /home/woogon/CMAQ_MODEL/CASES/SMOKE_TEST/smoke_example_case_v3/2022he_cb6_22m/scripts || exit 1
md5sum directory_definitions.csh.orig directory_definitions.csh
md5sum sectorlist_2022he_cb6_22m_withbeis_withrwc.orig sectorlist_2022he_cb6_22m_withbeis_withrwc
grep -n "^setenv INSTALL_DIR\|^setenv SMOKE_LOCATION\|^setenv IOAPI_LOCATION" directory_definitions.csh
grep -c "/home/cmas" sectorlist_2022he_cb6_22m_withbeis_withrwc
)
```

정상 결과:

| 파일 | md5 |
|---|---|
| `directory_definitions.csh.orig` | `2f057744d54f0dc4ad45ad4147eb7c52` |
| `directory_definitions.csh` | `930f9da6e9770cc47c55fc6c9ce35098` |
| `sectorlist_….orig` | `3e5070fe98b4a3336b650177ea5c6690` |
| `sectorlist_…` | `cef6ec7f7829bd1ed6770564b43e16c0` |

`grep -n` 결과의 세 줄이 모두 `/home/woogon/CMAQ_MODEL/...`를 가리키고, 마지막 `grep -c`가 `0`이어야 한다.

> **참고: `sectorlist` 경로를 고치지 않으면** 부문별 처리는 모두 정상인데 마지막 병합에서 `/home/cmas/training/...` 아래 파일을 찾지 못해 실패한다.

> **참고: 예제 스크립트·ASSIGNS는 예제 것을 쓴다** `RUNSCRIPTS`(`smoke5.2/scripts`)와 `ASSIGNS_FILE`(`smoke5.2/assigns/ASSIGNS.emf`)은 실행파일이 아니라 EPA 플랫폼용 csh·설정 파일이고, SMOKE 5.3 저장소에는 `ASSIGNS.emf`가 없어 예제 것을 그대로 쓴다.

### 10.4. 실행 전 점검

**1) 파이썬 모듈 설치(컴퓨터마다 최초 1회)**

예제의 일부 보조 스크립트가 파이썬 모듈을 쓴다. `woogon` 계정으로 설치한다.

```bash
(
python3 -m pip --version
)
```

pip가 없다고 나오면 root로 전환해 설치한 뒤 `woogon`으로 돌아온다.

```bash
su -
dnf install -y python3-pip
exit
```

`future`·`numpy`·`scipy` 설치와 확인:

```bash
(
python3 -m pip install --user future numpy scipy
python3 -c "import past, numpy, scipy; print('OK', numpy.__version__, scipy.__version__)"
)
```

정상 결과: `OK 2.0.2 1.13.1` (검증에 사용한 버전: future 1.0.0, numpy 2.0.2, scipy 1.13.1)

`netCDF4` 설치와 확인:

`netCDF4`는 파이썬에서 netCDF 파일을 읽고 쓰는 모듈이다. 예제 병합 스크립트가 하루치를 합칠 때마다 영역 전체 배출량 합계를 계산하는 점검 스크립트(`smoke5.2/scripts/emisqa/emisqa.py`)를 실행하는데, 이 스크립트가 병합 결과 파일을 읽는 데 쓴다.

```bash
(
python3 -m pip install --user netCDF4
python3 -c "import netCDF4; print('OK', netCDF4.__version__, netCDF4.__netcdf4libversion__, netCDF4.__hdf5libversion__)"
)
```

정상 결과: `OK`와 모듈 버전, 모듈이 사용하는 netCDF-C·HDF5 라이브러리 버전이 출력된다.

> **참고: 공통 라이브러리와 충돌하지 않는다** `pip`로 설치하는 `netCDF4`는 netCDF-C·HDF5 라이브러리를 모듈 안에 함께 담아 설치된다(`~/.local/lib/python3.9/site-packages/netCDF4.libs/`). 그래서 마지막 명령에 표시되는 라이브러리 버전은 `libs/`에 설치한 netCDF-C 4.9.3·HDF5 1.14.6과 다를 수 있으며, 정상이다. SMOKE·I/O API·WRF·CMAQ는 계속 `libs/`의 라이브러리를 쓰고, 이 모듈은 파이썬 점검 스크립트에서만 쓴다. `LD_LIBRARY_PATH`나 `~/.bashrc`를 바꿀 필요도 없다.

> **참고: 설치가 안 될 때** `pip`가 미리 만들어진 설치 파일(wheel)을 내려받지 못하면 소스에서 빌드하려다 `nc-config not found` 같은 오류가 날 수 있다. 이때는 먼저 `python3 -m pip install --user --upgrade pip`로 pip를 최신으로 올린 뒤 다시 설치한다.

전체 확인과 버전 기록:

```bash
(
python3 -m pip list --user | grep -i -E "future|numpy|scipy|netcdf4"
)
```

출력된 네 모듈의 버전을 작업 기록에 남긴다. 두 번째 컴퓨터에서도 같은 버전이 설치되었는지 이 명령으로 비교한다.

| 모듈 | 사용 스크립트 | 없을 때 증상 |
|---|---|---|
| `future`(`past`), `numpy`, `scipy` | `afdust_adj/afdust_ann_report.py` | `afdust_adj` 마지막에 `ModuleNotFoundError: No module named 'past'`, `ERROR: Running annual summary for adjusted emissions` (부록 A5) |
| `netCDF4` | `emisqa/emisqa.py` (병합 후 영역 합계 점검) | 병합이 첫날 파일만 만들고 `ModuleNotFoundError: No module named 'netCDF4'`, `ERROR: running domain totals for 20220101`로 멈춤 (부록 A6) |

> **참고: `--user`로 설치하는 이유** 모듈이 `woogon` 계정(`~/.local/lib/python3.9/site-packages`)에 설치되어 SMOKE를 실행하는 같은 계정에서 바로 찾는다. `sudo pip install`은 `dnf`가 관리하는 시스템 파이썬과 섞여 충돌할 수 있으므로 쓰지 않는다. 같은 이유로 **작업 컴퓨터마다** 따로 설치해야 한다.

> **참고: root 전환** `woogon`은 sudoers에 없으므로 `sudo`를 쓰면 `sudoers 파일에 없습니다`가 나온다. `su -`로 root 암호를 입력해 전환한다.

**2) 실행 권한과 로그 폴더**

```bash
(
cd /home/woogon/CMAQ_MODEL/CASES/SMOKE_TEST/smoke_example_case_v3/2022he_cb6_22m/scripts || exit 1
find . -name "*.csh" ! -perm -u+x | wc -l
find . -name "*.csh" ! -perm -u+x -exec chmod u+x {} \;
find . -name "*.csh" ! -perm -u+x | wc -l
mkdir -p ../run_logs
)
```

정상 결과: 마지막 `find`가 `0`이다. 첫 `find`는 압축을 푼 상태에 따라 0~2로 나온다(검증 때는 `2`).

> **참고:** 예제 압축본에는 `Annual_ptfire-rx_onetime_…csh` 등 실행 권한이 빠진 스크립트가 있다. 그대로 두면 해당 단계에서 `Permission denied`로 멈춘다.

### 10.5. 면오염원 11개 부문

`afdust`가 `afdust_adj`(기상 보정)보다 먼저 실행되어야 한다.

```bash
(
cd /home/woogon/CMAQ_MODEL/CASES/SMOKE_TEST/smoke_example_case_v3/2022he_cb6_22m/scripts/nonpoint || exit 1

set -o pipefail
{
for s in Annual_rwc Annual_afdust Annual_afdust_adj Annual_nonpt Annual_np_oilgas Annual_np_solvents \
         Annual_openburn Annual_rail Monthly_fertilizer Monthly_livestock Monthly_nonroad; do
  sec=${s#*_}
  echo "===== START $sec $(date '+%F %T')"
  LC_ALL=C ./${s}_12US1_2022he_cb6_22m.csh > ../../run_logs/${sec}_run.log 2>&1
  run_rc=$?; [ "$run_rc" -eq 0 ] || { echo "실행 실패: $run_rc"; exit "$run_rc"; }
  echo "===== END   $sec $(date '+%F %T')"
done
} 2>&1 | tee ../../run_logs/nonpoint_all_summary.log
run_rc=$?; [ "$run_rc" -eq 0 ] || { echo "부문 실행 실패: $run_rc (다음 단계로 진행하지 말고 로그를 확인한다)"; exit 1; }
)
```

> **참고: 실패 시 동작** 한 부문이 실패하면 남은 부문을 중단한다. 바깥 서브셸도 실패 상태로 끝나지만 부모 터미널·SSH 접속은 유지된다. 실패 메시지가 나오면 다음 단계로 가지 말고 해당 부문 로그를 확인한다. 점오염원·도로이동 반복문도 같다.

판정:

```bash
(
cd /home/woogon/CMAQ_MODEL/CASES/SMOKE_TEST/smoke_example_case_v3/2022he_cb6_22m/run_logs || exit 1
for s in rwc afdust afdust_adj nonpt np_oilgas np_solvents openburn rail fertilizer livestock nonroad; do
  n=$(grep -c -E "Segmentation fault|SIGSEGV|ERROR: detected|ERROR: Running" ${s}_run.log)
  printf "%-12s 오류 %s\n" "$s" "$n"
done
ls ../premerged
)
```

정상 결과:

- 11개 부문 모두 `오류 0`
- `premerged`에 13개 폴더: `afdust afdust_adj fertilizer livestock nonpt nonroad nonroad_diesel nonroad_gas np_oilgas np_solvents openburn rail rwc`

> **참고:** 실행 중 `grep: .../logs: Is a directory`는 예제 스크립트가 로그 폴더를 검색하며 내는 안내이며 오류가 아니다. `nonroad`는 병합 목록에서 연료별로 쓰기 때문에 `nonroad`, `nonroad_diesel`, `nonroad_gas` 세 폴더로 저장된다.

> **참고: `nonpt` 결과는 9개 날짜** `nonpt`는 대표일 방식으로 처리되어 2022-01-01~01-09의 9개 날짜만 만들어진다. 병합 목록의 `nonpt` 병합 방식 `week_Y`(대표 1주일 + 공휴일)가 요구하는 날짜와 같다.

### 10.6. 점오염원 20개 스크립트

부문마다 `onetime`(배출목록·종분배·공간배분, 굴뚝 배출원 선별)을 모두 먼저 실행한 뒤 `daily`(날짜별 시간배분·병합, 상승고 계산)를 실행한다.

| 실행 | 부문 | 스크립트 |
|---|---|---|
| ○ | airports, cmv_c1c2, cmv_c3, pt_oilgas, ptagfire, ptnonipm | onetime → daily |
| ○ | ptegu | onetime → **winter_daily만** |
| ○ | ptfire-rx, ptfire-wild | onetime → high_daily, low_daily |
| × | ptegu spring·summer·fall daily | 예제 기간(1월) 밖 |
| × | `Annual_ptegu_3d_…_12US2_…` 2개 | 다른 격자(12US2)용, 예제 처리 대상 아님 |

```bash
(
cd /home/woogon/CMAQ_MODEL/CASES/SMOKE_TEST/smoke_example_case_v3/2022he_cb6_22m/scripts/point || exit 1

set -o pipefail
{
for s in airports_onetime cmv_c1c2_onetime cmv_c3_onetime pt_oilgas_onetime ptagfire_onetime \
         ptegu_onetime ptfire-rx_onetime ptfire-wild_onetime ptnonipm_onetime \
         airports_daily cmv_c1c2_daily cmv_c3_daily pt_oilgas_daily ptagfire_daily \
         ptegu_winter_daily ptfire-rx_high_daily ptfire-rx_low_daily \
         ptfire-wild_high_daily ptfire-wild_low_daily ptnonipm_daily; do
  echo "===== START $s $(date '+%F %T')"
  LC_ALL=C ./Annual_${s}_12US1_2022he_cb6_22m.csh > ../../run_logs/pt_${s}_run.log 2>&1
  run_rc=$?; [ "$run_rc" -eq 0 ] || { echo "실행 실패: $run_rc"; exit "$run_rc"; }
  echo "===== END   $s $(date '+%F %T')"
done
} 2>&1 | tee ../../run_logs/point_all_summary.log
run_rc=$?; [ "$run_rc" -eq 0 ] || { echo "부문 실행 실패: $run_rc (다음 단계로 진행하지 말고 로그를 확인한다)"; exit 1; }
)
```

판정:

```bash
(
cd /home/woogon/CMAQ_MODEL/CASES/SMOKE_TEST/smoke_example_case_v3/2022he_cb6_22m/run_logs || exit 1
for f in pt_*_run.log; do
  n=$(grep -c -E "Segmentation fault|SIGSEGV|ERROR: detected|ERROR: Running" $f)
  printf "%-38s 오류 %s\n" "$f" "$n"
done
ls pt_*_run.log | wc -l
ls ../premerged
find ../smoke_out -type f | wc -l
)
```

정상 결과:

- 20개 로그 모두 `오류 0`, 로그 개수 `20` (onetime 9 + daily 11)
- `premerged`에 점오염원 9개 폴더 추가: `airports cmv_c1c2_12 cmv_c3_12 pt_oilgas ptagfire ptegu ptfire-rx ptfire-wild ptnonipm`
- `smoke_out` 파일 `1032`개: 부문별 굴뚝 정보 파일(`stack_groups_…ncf`)과 날짜별 inline 배출량 파일(`inln_mole_…_2022MMDD_…ncf`). CMAQ가 병합 없이 직접 읽는 파일이다.

### 10.7. 도로이동 8개 스크립트

도로이동은 활동도(주행거리·차량 대수·시동 횟수 등)에 MOVES 배출계수를 곱해 배출량을 계산한다. 모드별 6개를 실행한 뒤 연료별로 병합한다.

| 스크립트 | 모드 |
|---|---|
| `RPD` | 주행 중 배출 (주행거리) |
| `RPH` | 화물차 장시간 공회전 |
| `RPHO` | 도로 외 공회전 |
| `RPP` | 연료 증발 (차량 대수 + 기온) |
| `RPS` | 시동 |
| `RPV` | 차량당 (증발 등) |
| `merge_diesel`, `merge_gas` | 위 결과를 연료별로 병합 |

```bash
(
cd /home/woogon/CMAQ_MODEL/CASES/SMOKE_TEST/smoke_example_case_v3/2022he_cb6_22m/scripts/onroad || exit 1

set -o pipefail
{
for s in RPD RPH RPHO RPP RPS RPV merge_diesel merge_gas; do
  echo "===== START $s $(date '+%F %T')"
  LC_ALL=C ./Monthly_onroad_${s}_daily_12US1_2022he_cb6_22m.csh > ../../run_logs/onroad_${s}_run.log 2>&1
  run_rc=$?; [ "$run_rc" -eq 0 ] || { echo "실행 실패: $run_rc"; exit "$run_rc"; }
  echo "===== END   $s $(date '+%F %T')"
done
} 2>&1 | tee ../../run_logs/onroad_all_summary.log
run_rc=$?; [ "$run_rc" -eq 0 ] || { echo "부문 실행 실패: $run_rc (다음 단계로 진행하지 말고 로그를 확인한다)"; exit 1; }
)
```

예제에서 가장 오래 걸리는 단계다(검증 때 약 2~4시간, 대부분 `RPD`). 진행 상황은 다른 터미널에서 `cat .../run_logs/onroad_all_summary.log`로 본다.

판정:

```bash
(
cd /home/woogon/CMAQ_MODEL/CASES/SMOKE_TEST/smoke_example_case_v3/2022he_cb6_22m/run_logs || exit 1
for s in RPD RPH RPHO RPP RPS RPV merge_diesel merge_gas; do
  n=$(grep -c -E "Segmentation fault|SIGSEGV|ERROR: detected|ERROR: Running" onroad_${s}_run.log)
  printf "%-14s 오류 %s\n" "$s" "$n"
done
cd .. || exit 1
for d in premerged/onroad*/*; do [ -d "$d" ] && printf "%-30s %s\n" "$d" "$(ls $d | wc -l)"; done
)
```

정상 결과: 8개 모두 `오류 0`, 폴더별 파일 수는 아래와 같다.

| 폴더 | 파일 수 | 설명 |
|---|---|---|
| `onroad*/RPH` (3개) | 31 | 날짜별 파일 |
| `onroad_diesel/RPP`, `onroad_diesel/RPV` | **0** | 경유차는 증발 배출이 없음. EPA 결과도 0개 |
| 나머지 | 36 | 날짜별 31 + 토요일마다 1주일치 묶음(`…_multiday.ncf.gz`) 5 |

`onroad_gas`, `onroad_diesel` 폴더에는 연료별 병합 결과 `emis_mole_onroad_{gas,diesel}_2022MMDD_…ncf`가 31개씩 만들어진다.

> **참고:** `merge_diesel`, `merge_gas` 로그의 마지막 줄은 `No warning or error messages. Exiting`이다. 계산 프로그램 없이 파일만 합치므로 로그 분석기가 분석할 내용이 없다는 뜻이며 정상이다.

> **참고: EPA 결과와 비교** 예제에 포함된 EPA 결과와 RPD·RPHO·RPS·RPV 12개 폴더의 날짜별 파일 수(31개, 경유 RPV는 0개)가 일치했다. 압축은 풀지 않고 목록만 센다.
>
> ```bash
> tar -tzf RPD_RPHO_RPS_RPV.premerged.tar.gz | grep "^premerged/onroad/RPD/." | wc -l
> ```

### 10.8. 생물성(BEIS4)

예제 기본 설정은 EPA가 미리 계산한 정규화 배출량(`intermed/beis4/beis_norm_emis_12LISTOS_2022he_cb6_22m.ncf`)에 날짜별 기상을 적용하는 `tmpbeis4`만 실행한다. 스크립트 폴더 이름은 `biogenics`다.

```bash
(
cd /home/woogon/CMAQ_MODEL/CASES/SMOKE_TEST/smoke_example_case_v3/2022he_cb6_22m/scripts/biogenics || exit 1
LC_ALL=C ./Annual_beis4_12US1_2022he_cb6_22m.csh > ../../run_logs/beis4_run.log 2>&1
run_rc=$?; [ "$run_rc" -eq 0 ] || { echo "실행 실패: $run_rc (다음 단계로 진행하지 말고 로그를 확인한다)"; exit 1; }
grep -c -E "Segmentation fault|SIGSEGV|ERROR: detected|ERROR: Running" ../../run_logs/beis4_run.log
ls ../../premerged/beis4 | wc -l
)
```

정상 결과: `0`, `62` (날짜별 mass·mole 파일 각 31개)

> **참고: `normbeis4` 검증(선택)** 부산 격자에서는 정규화 배출량을 직접 계산해야 하므로 `normbeis4`도 확인했다(2026-10-13). `scripts/run_settings.txt`의 `beis4, 12LISTOS, normbeis4, ALL, 0, 0, N`을 주석 처리하고 같은 줄을 `Y`로 추가한 뒤(원본 md5 `ee2536e15000c8d8dd0bde6c5ee3dd62` → 수정본 `f46f63148c3cb9fa157d6aefd5f4ff97`), EPA 정규화 파일을 `.EPA`로 보관하고 다시 실행했다. 새로 계산된 파일과 EPA 파일의 변수 77개를 비교한 최대 상대 차이는 **2.85×10⁻⁷**로, 단정밀도 반올림 수준이었다. 설정 줄 끝에는 주석을 붙이지 않는다. 쉼표로 칸을 나누는 파일이라 마지막 값이 잘못 읽힐 수 있다.

### 10.9. 병합과 최종 확인

`mrggrid`가 병합 대상 8개 부문(beis4, airports, nonroad, np_solvents, onroad_gas, onroad_diesel, nonpt, rwc)을 날짜마다 하나의 CMAQ 입력 파일로 합친다. 굴뚝 배출원(`pt_oilgas`, `ptegu`, `ptnonipm` 등)은 병합하지 않고 `smoke_out`의 inline 파일로 CMAQ에 직접 들어간다.

```bash
(
cd /home/woogon/CMAQ_MODEL/CASES/SMOKE_TEST/smoke_example_case_v3/2022he_cb6_22m/scripts/merge || exit 1
LC_ALL=C ./Sector_merge_12US1_2022he_cb6_22m_withbeis_withrwc.csh > ../../run_logs/merge_run.log 2>&1
run_rc=$?; [ "$run_rc" -eq 0 ] || { echo "실행 실패: $run_rc (다음 단계로 진행하지 말고 로그를 확인한다)"; exit 1; }
)
```

판정:

```bash
(
cd /home/woogon/CMAQ_MODEL/CASES/SMOKE_TEST/smoke_example_case_v3/2022he_cb6_22m || exit 1
grep -c -E "Segmentation fault|SIGSEGV|ERROR|does not exist|ModuleNotFoundError" run_logs/merge_run.log
M=smoke_out/2022he_cb6_22m/12LISTOS/cmaq_cb6ae7/merged_withbeis_withrwc
ls $M | grep -c "^emis_mole_all"
ls $M | head -3
)
```

정상 결과:

- 오류 문구 `0`
- 최종 병합 파일 `31`개: `emis_mole_all_20220101_12LISTOS_withbeis_withrwc_2022he_cb6_22m.ncf` ~ `…20220131…`
- 병합 부문 목록 `README_2022he_cb6_22m_12LISTOS_withbeis_withrwc_premerged_sectors.txt`

> **참고: 병합 실패 시 확인할 곳** 오류 부분과 그 앞을 함께 본다. 앞부분에 어느 날짜의 어느 부문 파일을 찾지 못했는지가 나온다.
>
> ```bash
> grep -n -B12 -A3 -E "ERROR|does not exist" run_logs/merge_run.log
> ```

**CMAQ 입력 묶음:** 최종 병합 파일 31개(`merged_withbeis_withrwc/`)와 굴뚝 배출원 파일 1,032개(`smoke_out/…/cmaq_cb6ae7/<부문>/stack_groups_…`, `inln_mole_…`)가 CMAQ 배출량 입력이 된다.

### 10.10. 알려진 예외와 남은 과제

| 항목 | 내용 | 처리 계획 |
|---|---|---|
| `afdust_adj` 보조 프로그램 | 날짜별 강수 보정에 예제 `smoke5.2/scripts/afdust_adj/`의 `apply_precip_adj_wrf.x`, `mult.x`를 사용한다. EPA가 Intel(ifx)로 미리 컴파일한 것이다(로그의 `Linux2_x86_64ifx`, `ioapi-3.2 … 2023`, `netCDF 4.9.2`). `SMOKE_LOCATION`으로는 바뀌지 않는다. | 부산 사례 구성 때 `apply_precip_adj_wrf.f`(SMOKE 5.3 `scripts/platform/afdust_adj/`)를 gfortran으로 컴파일한다. `mult.x`는 SMOKE 5.3 저장소에서 소스를 찾지 못했으므로 역할을 확인해 대체 방법을 정한다. |
| 미국 전용 기능 | `procar2pt.f`가 관련된 area-to-point(ARTOPNT)는 미국 배출목록 기능이다. | CAPSS 처리에서 사용 여부를 확인한다. |
| 폴더 구조 | 예제는 예제 자체 폴더 구조로 실행했다. | 예제 자료를 프로젝트 구조(`DATA/EMIS/…`, `CASES/<지역>/<사례>/EMIS/…`)로 재배치해 같은 결과가 나오는지 확인한 뒤 CAPSS에 적용한다. |

---

## 부록 A. 구축 중 발생한 문제 기록

이 문서의 절차는 아래 문제들을 해결한 결과다. 같은 증상을 만났을 때 원인을 찾는 용도로 남긴다.

| 번호 | 단계 | 증상 | 원인 | 예방 조치 |
|---|---|---|---|---|
| A1 | 설치 폴더 구성 | `ls -l`에 `smoke`만 있고 `ioapi/...` 확인 시 `그런 파일이나 디렉터리가 없습니다` | `subsys` 폴더에서 `ln -s`가 실행되지 않음 | 5.3 `subsys`에서 링크 생성, 5.4 확인 |
| A2 | compile(링크) | 소스·내부 라이브러리 컴파일 후 `normbeis3` 링크에서 `/usr/bin/ld: cannot find -lnetcdff`, `cannot find -lnetcdf` | 배포본 `IOLIB`에 netCDF 경로가 없음 | 6.2 `Makeinclude` 수정본 |
| A3 | 예제 `nonpt` | `smkinven`이 2~3초 만에 `SIGSEGV: Segmentation fault`. 로그 마지막 줄은 `All message priorities > 1`이라 정상처럼 보임. 이후 병합에서 `emis_mole_nonpt_20220101…` 파일 없음 | `procar2pt.f` 지역 포인터 미초기화. GFortran에서 `ASSOCIATED()`가 쓰레기 값으로 `.TRUE.` 판정 | 6.2 `procar2pt.f` 수정본, 4장 판정 방법 |
| A4 | 예제 점오염원 | `Permission denied` | 예제 압축본에 실행 권한이 빠진 스크립트 | 10.4 `chmod` 점검 |
| A5 | 예제 `afdust_adj` | `ModuleNotFoundError: No module named 'past'`, `ERROR: Running annual summary for adjusted emissions` | 연간 요약 파이썬 스크립트용 모듈 없음 | 10.4 `future numpy scipy` 설치 |
| A6 | 예제 병합 | 첫날 파일 1개만 만들고 `No module named 'netCDF4'`, `ERROR: running domain totals for 20220101` | 병합 후 영역 합계 점검 스크립트용 모듈 없음 | 10.4 `netCDF4` 설치 |
| A7 | 예제 병합 | `/home/cmas/training/...` 파일 없음 | `sectorlist`의 `projectroot`가 CMAS 교육 서버 경로 | 10.3 `sectorlist` 수정본 |
| A8 | 파이썬 설치 | `sudo` 사용 시 `sudoers 파일에 없습니다` | `woogon`에 sudo 권한 없음 | 10.4 `su -`로 root 전환 |
| A9 | 다른 컴퓨터에서 실행 | 한 컴퓨터에서 설치한 모듈이 다른 컴퓨터에 없음 | `--user` 설치는 계정·컴퓨터별 | 8.4, 10.4 컴퓨터마다 설치 |

진단에 사용한 명령:

```bash
(
# A3: 비정상 종료 찾기와 실제로 실행된 프로그램 확인
grep -l -E "Segmentation fault|SIGSEGV|ERROR: detected|ERROR: Running" run_logs/*_run.log
ls intermed/nonpt/logs | sed 's/_.*//' | sort | uniq -c

# A3: 오류 위치 찾기 (디버그 빌드, 상세는 SMOKE_procar2pt_Fix.md §3)
LC_ALL=C make FOPTFLAGS="-O0 -g -fbacktrace -fcheck=bounds -fallow-argument-mismatch -m64"

# A5, A6: 파이썬 모듈 확인
python3 -c "import past, numpy, scipy, netCDF4"
)
```

구축 경위:

- 처음에는 `Makeinclude`를 두 차례(EFLAG만 → netCDF 경로 추가)에 나눠 고쳤다. 이 문서는 최종 수정본 하나로 정리했다.
- 첫 예제 실행에서는 부문별 판정을 로그 마지막 줄로 해서 `nonpt`의 비정상 종료를 놓쳤고, 병합 단계에서 처음 드러났다. 디버그 빌드로 `procar2pt.f` 448행을 찾아 수정했다.
- 파이썬 모듈은 필요한 단계에 도달할 때마다 하나씩 드러났다(`afdust_adj` → 병합). 이 문서는 실행 전에 모두 설치하도록 정리했다.
- 제공 문서는 수정 후 새 설치·예제 실행이 완료되었다고 기록한다(2026-10-19). 이번 문서의 재실행 절차는 기존 결과를 백업하도록 보완했다.

## 11. 검토 근거 및 관련 문서

공식 소스 확인: 태그 `SMOKEv5.3_June2026`의 커밋과 `src/Makeinclude`, `src/Makefile`(실행파일 목록·`make dir` 규칙), `assigns/ASSIGNS.*`(`SMK_HOME/subsys` 구조), `src/smkinven/procar2pt.f`를 공식 저장소에서 직접 확인했다. 예제는 SMOKE-ExampleCase-v3 저장소의 부문별 설명서를 참고했다. 이번에 제공된 `docs/smoke/files/`의 수정본 4개는 문서의 수정본 md5와 일치함을 확인했다. `Makeinclude`와 `procar2pt.f`는 보관 중인 공식 태그 소스와 diff를 대조했고, 예제 설정 파일은 설치·실행 경로 변경 내용을 확인했다. 서버 설치 파일과의 직접 대조나 재실행은 수행하지 않았다. 서버의 컴파일·실행 결과와 수치 비교는 사용자 제공 문서에 근거한다.

- [procar2pt.f 수정 기록](SMOKE_procar2pt_Fix.md)
- [SMOKE GitHub 저장소](https://github.com/CEMPD/SMOKE)
- [SMOKE v5.3 릴리스 노트](https://github.com/CEMPD/SMOKE/releases/tag/SMOKEv5.3_June2026)
- [SMOKE 공식 홈페이지](https://www.cmascenter.org/smoke/)
- [SMOKE 5.3 User's Guide](https://www.cmascenter.org/smoke/documentation/5.3/html/)
- [SMOKE-ExampleCase-v3](https://github.com/CEMPD/SMOKE-ExampleCase-v3)
- [구축 기본계획 및 Phase 현황](../planning/00_CMAQ_Project_Master_Plan.md) §3.5, §10, §22 Phase 5
- [MCIP 구축 가이드](../mcip/MCIP_Installation_Guide.md)
- [WRF/WPS 설치 가이드](../wrf/WRF_WPS_Installation_Guide.md)
- [공통 라이브러리 구축 기록](../libraries/Common_Libraries_Installation_Guide.md)
