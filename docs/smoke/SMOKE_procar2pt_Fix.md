# SMOKE 5.3 소스 수정 기록: `procar2pt.f` 포인터 초기화

**이 문서는 SMOKE 5.3을 GNU Fortran으로 컴파일했을 때 `smkinven`이 면오염원 area-to-point 처리 중 비정상 종료(Segmentation fault)되는 문제의 원인과 수정 내용을 기록한다.** 수정은 SMOKE 5.3 소스 파일 1개(`src/smkinven/procar2pt.f`)에 9줄을 추가한 것이다.

검증 근거: 사용자 제공 수정 기록이며, 이번 문서 검토에서 Linux 모델을 재실행하지 않았다. 공식 태그의 지역 포인터 선언과 사용 위치는 소스로 대조했다. 수정 후 결과는 제공 문서에 기록된 값이다. 전체 공식 예제 완료일은 2026-10-19이며 부산 사례·CMAQ 연계 검증은 미완료다.

## 1. 요약

| 항목 | 내용 |
|---|---|
| 대상 | SMOKE 5.3 (태그 `SMOKEv5.3_June2026`, 커밋 `f29374b`) |
| 컴파일러 | GNU Fortran 11.5.0 (Rocky Linux 9.8) |
| 증상 | `smkinven`이 area-to-point(ARTOPNT) 처리를 하는 부문에서 실행 2~3초 만에 `SIGSEGV: Segmentation fault`로 종료 |
| 발견 사례 | SMOKE-ExampleCase-v3의 `nonpt` 부문 (다른 부문은 정상) |
| 원인 | `procar2pt.f`의 지역 포인터들이 초기화되지 않은 상태에서 `ASSOCIATED()`로 검사됨 |
| 수정 | 처리 시작 부분에서 지역 포인터 15개를 `NULLIFY`로 초기화 |
| 결과 | `nonpt` 정상 완료 (Segmentation fault 0건, 결과 파일 9개 생성) |
| 수정일 | 2026-10-18 |

## 2. 증상

### 2.1 실행 화면

예제 `nonpt` 부문 실행 로그(`run_logs/nonpt_run.log`)에 다음이 기록되었다.

```text
Program received signal SIGSEGV: Segmentation fault - invalid memory reference.

Backtrace for this error:
#0  0x153554c238a0 in ???
...
Segmentation fault (core dumped)
...
ERROR: detected in Smkinven
ERROR: Running smk_run for one-time steps
```

`smkinven` 로그는 area-to-point 정보를 읽은 직후에서 끝나 있었다.

```text
     NOTE: The area-to-point factors file included the following SCCs and
          section numbers
```

이후 단계(`spcmat`, `grdmat`, `smkreport`, `temporal`, `smkmerge`)는 실행되지 않았고, `premerged/nonpt` 폴더는 비어 있었다.

> **참고: 로그 마지막 줄만으로는 발견되지 않는다** 이 경우에도 실행 로그의 마지막 줄은 `All message priorities > 1`(정상 판정)이었다. 로그 분석기는 실제로 만들어진 로그만 검사하는데, 프로그램이 비정상 종료되면서 로그에 오류 문구를 남기지 못했기 때문이다. 아래 오류 검색과 함께 종료 상태, 단계별 정상 종료 및 산출물 날짜·내용을 확인해야 한다. 오류 0건만으로 성공을 판정하지 않는다([설치 가이드 §4](SMOKE_Installation_Guide.md#4-공통-실행-규칙)).
>
> ```bash
> grep -c -E "Segmentation fault|SIGSEGV|ERROR: detected" <부문>_run.log
> ```

### 2.2 재현성

- 예제를 지우고 zip에서 새로 압축 해제한 깨끗한 상태에서도 같은 오류가 재현되었다.
- 스택 한도를 늘려도(`ulimit -s unlimited`) 같은 오류가 났다. 단순한 메모리 한도 문제가 아니다.
- 같은 예제의 다른 면오염원 10개 부문, 점오염원, 도로이동, 생물성 부문은 모두 정상이었다.

## 3. 원인 진단

### 3.1 진단 방법: 디버그 빌드

배포용 실행파일은 최적화(`-O3` 등)되어 있어 오류 위치를 `???`로만 표시한다. 설치본은 그대로 두고, 별도 폴더에 디버그 옵션으로 다시 컴파일해서 같은 계산을 실행했다.

```bash
cd /home/woogon/CMAQ_MODEL || exit 1
[ ! -e SMOKEv5.3_debug ] && [ ! -L SMOKEv5.3_debug ] || { echo "기존 디버그 폴더를 보존하고 별도 경로를 선택하세요"; exit 1; }
cp -a SMOKEv5.3 SMOKEv5.3_debug || exit 1

export SMK_HOME=/home/woogon/CMAQ_MODEL/SMOKEv5.3_debug
export BIN=Linux2_x86_64gfort10
cd $SMK_HOME/subsys/smoke/src || exit 1
make clean || exit 1
set -o pipefail
LC_ALL=C make FOPTFLAGS="-O0 -g -fbacktrace -fcheck=bounds -fallow-argument-mismatch -m64" 2>&1 | tee ../Linux2_x86_64gfort10/make_debug.log
build_rc=$?; [ "$build_rc" -eq 0 ] || { echo "빌드 실패: $build_rc"; exit "$build_rc"; }
```

| 옵션 | 역할 |
|---|---|
| `-O0 -g` | 최적화 없이 소스 줄 정보 포함 |
| `-fbacktrace` | 오류 시 호출 경로 출력 |
| `-fcheck=bounds` | 배열 범위를 벗어난 접근을 즉시 오류로 잡음 |
| `-fallow-argument-mismatch` | SMOKE의 오래된 인자 전달 방식을 허용 (GFortran 10 이상 필수) |

> **참고: `-fallow-argument-mismatch`를 빠뜨리면** `FOPTFLAGS`를 지정하면 I/O API 옵션 파일의 기본 옵션이 통째로 대체된다. 이 옵션이 빠지면 `rdinvchr.f` 등에서 `Type mismatch between actual argument ... (REAL(8)/INTEGER(4))` 컴파일 오류가 난다.

예제 `directory_definitions.csh`의 `SMOKE_LOCATION`만 디버그 빌드 경로로 바꿔 `nonpt`를 실행하자, 다음 위치에서 멈췄다.

```text
At line 448 of file .../subsys/smoke/src/smkinven/procar2pt.f
Fortran runtime error: Index '1' of dimension 1 of array 'oldcmact' below lower bound of 35921
```

### 3.2 원인 분석

`procar2pt.f`는 면오염원 일부를 점 위치로 옮기는(area-to-point) 처리를 한다. 배출원 배열을 늘리기 위해 기존 배열을 지역 포인터(`OLDCMACT` 등)로 잠시 가리켜 두고, 새 배열에 값을 옮긴다.

```fortran
C...........   Local pointers
        CHARACTER(MACLEN3), POINTER :: OLDCMACT  ( : )  ! MACT code
        ...
            IF( ASSOCIATED( CMACT ) ) THEN
                OLDCMACT   => CMACT
                OLDCNAICS  => CNAICS
            END IF
        ...
                    IF( ASSOCIATED( OLDCMACT ) ) THEN
                        CMACT  ( NEWSRCPOS ) = OLDCMACT  ( S )     ! 448행
```

문제는 지역 포인터들이 **선언만 되고 초기화되지 않았다**는 점이다.

- `nonpt` 배출목록에는 MACT 코드가 없어 `CMACT`가 할당되지 않으므로, `OLDCMACT`는 한 번도 연결되지 않는다.
- Fortran 규격상 초기화되지 않은 포인터의 연결 상태는 "정의되지 않음"이며, 이 상태에서 `ASSOCIATED()`를 호출한 결과는 보장되지 않는다.
- GNU Fortran에서는 지역 포인터가 스택의 쓰레기 값을 그대로 가져 `ASSOCIATED( OLDCMACT )`가 `.TRUE.`로 판정되었다. 그 결과 존재하지 않는 배열에 접근했다. 오류 메시지의 하한 `35921`은 그 쓰레기 값이다.
- 예제에는 Intel 빌드 보조 실행파일이 포함되어 있다. 원 작성자는 컴파일러 차이로 결함이 가려졌을 가능성을 제시했으나 Intel에서 동일 소스를 비교 실행한 자료는 제공되지 않았다. Intel 환경의 초기화 동작이나 EPA 전체 시험 범위를 단정하지 않는다.

같은 방식의 지역 포인터가 `OLDCNAICS`, `OLDCINTGR`, `OLDCEXTORL`, `OLDCSHAPE` 등 모두 15개 있다. 이번에는 `OLDCMACT`에서 먼저 드러났을 뿐, 다른 포인터도 같은 위험이 있다.

> **참고: 영향 범위** area-to-point 처리(`SMK_ARTOPNT_YN = Y`이고 ARTOPNT 대상 SCC가 있는 경우)를 하는 부문에서만 이 코드가 실행된다. ARTOPNT는 미국 배출목록 전용 기능(공항 주변 배출을 점으로 배치하는 등)이므로, CAPSS 처리에서 사용하지 않으면 영향이 없다. 다만 수정은 동작을 바꾸지 않고 정의되지 않은 상태만 제거하므로, 모든 경우에 적용해 두는 것이 안전하다.

## 4. 수정 내용

### 4.1 변경 사항

처리 시작 부분(`begin body of subroutine PROCAR2PT` 직후)에 지역 포인터 15개를 모두 `NULLIFY`(연결 안 됨)로 초기화하는 코드를 추가했다. 기존 코드는 바꾸지 않았다.

```diff
@@ -128,6 +128,15 @@

 C***********************************************************************
 C   begin body of subroutine PROCAR2PT
+C.........  CMAQ_MODEL fix (2026-10-18): local pointers have undefined
+C           association status until set. With gfortran, ASSOCIATED() on
+C           an undefined pointer can return .TRUE., causing a segfault
+C           when OLDCMACT etc. are used for sources without MACT data.
+        NULLIFY( OLDNPCNT, OLDIPOSCOD, OLDTPFLAG, OLDINVYR, OLDPOLVAL,
+     &           OLDCIFIP, OLDCSOURC, OLDCSCC, OLDCISIC, OLDCMACT,
+     &           OLDCNAICS, OLDCSRCTYP, OLDCEXTORL, OLDCINTGR,
+     &           OLDCSHAPE )
+

 C.........  Determine total number of sources to be added; if source only
```

`NULLIFY`는 포인터를 "아무것도 가리키지 않음" 상태로 확정한다. 그 뒤로는 실제로 연결된 포인터만 `ASSOCIATED()`가 `.TRUE.`가 되므로, 원래 의도대로 동작한다.

> **참고: 선언부 초기화(`=> NULL()`)를 쓰지 않은 이유** 선언에서 `POINTER :: OLDCMACT(:) => NULL()`로 초기화하면 Fortran 규격상 그 변수에 암묵적으로 `SAVE` 속성이 붙는다. 서브루틴이 여러 번 호출되면 이전 호출의 연결 상태가 남는다. 실행부에서 매번 `NULLIFY`하는 방식은 호출할 때마다 초기 상태가 보장된다.

### 4.2 파일 정보

| 파일 | md5 |
|---|---|
| 원본 `procar2pt.f` (태그 `SMOKEv5.3_June2026`) | `18f8b22c7742fc607db12c0634a0e555` |
| 수정본 `procar2pt.f` | `965d553d45920aec73f55eb87ae49a20` |

원본은 같은 폴더에 `procar2pt.f.orig`로 보관한다.

## 5. 적용 절차

설치본 `SMOKEv5.3`에 적용한다. **실제 수정본은 첨부되지 않아 확보가 필요하다.** §4.1 diff로 직접 수정하거나 원 작성자의 사용본을 확보해 검토한 뒤 적용한다. 아래 md5는 제공 문서 기록값이다.

**1) 원본 백업**

```bash
cd /home/woogon/CMAQ_MODEL/SMOKEv5.3/subsys/smoke/src/smkinven || exit 1
cp -n procar2pt.f procar2pt.f.orig
```

**2) 수정본을 같은 폴더에 덮어쓰고 확인**

```bash
md5sum procar2pt.f.orig procar2pt.f
```

기대값: §4.2의 기록값이다. 실제 사용본 확보 전에는 동일성을 확인한 것으로 처리하지 않는다.

**3) 다시 컴파일**

```bash
export SMK_HOME=/home/woogon/CMAQ_MODEL/SMOKEv5.3
export BIN=Linux2_x86_64gfort10
cd $SMK_HOME/subsys/smoke/src || exit 1
set -o pipefail
LC_ALL=C make 2>&1 | tee ../Linux2_x86_64gfort10/make_SMOKEv5.3_fix_procar2pt.log
build_rc=$?; [ "$build_rc" -eq 0 ] || { echo "빌드 실패: $build_rc"; exit "$build_rc"; }
grep -c "Error:" ../Linux2_x86_64gfort10/make_SMOKEv5.3_fix_procar2pt.log
ls -l --time-style=long-iso ../Linux2_x86_64gfort10/smkinven
```

- `make`는 바뀐 파일만 다시 컴파일하고 관련 실행파일을 다시 링크하므로 금방 끝난다.
- make 종료값이 0인지, 변경 소스가 실제 재컴파일·재링크되었는지 빌드 로그에서 확인한다. 오류 검색·수정 시각만으로 반영을 확정하지 말고 실행 경로와 §6 재실행 산출물을 확인한다.

> **참고:** `SMK_HOME`이 설치본(`SMOKEv5.3`)을 가리키는지 `echo $SMK_HOME`으로 반드시 확인한다. 진단용 폴더를 가리킨 채로 컴파일하면 설치본에 반영되지 않는다.

## 6. 검증

예제 `nonpt` 부문을 수정된 SMOKE로 다시 실행했다(2026-10-18).

```bash
cd /home/woogon/CMAQ_MODEL/CASES/SMOKE_TEST/smoke_example_case_v3/2022he_cb6_22m/scripts/nonpoint || exit 1
LC_ALL=C ./Annual_nonpt_12US1_2022he_cb6_22m.csh > ../../run_logs/nonpt_run2.log 2>&1
  run_rc=$?; [ "$run_rc" -eq 0 ] || { echo "실행 실패: $run_rc"; exit "$run_rc"; }
grep -c "Segmentation fault" ../../run_logs/nonpt_run2.log
ls ../../intermed/nonpt/logs | sed 's/_.*//' | sort | uniq -c
ls ../../premerged/nonpt | wc -l
```

| 확인 | 수정 전 | 수정 후 |
|---|---|---|
| Segmentation fault | 2건 | **0건** |
| 실행된 프로그램 로그 | `smkinven` 1개 | `smkinven` 1, `spcmat` 1, `grdmat` 1, `smkreport` 5, `temporal` 1, `smkmerge` 9 |
| `premerged/nonpt` 결과 파일 | 0개 | **9개** |

결과 날짜는 2022-01-01 ~ 01-09로, 병합 목록(`sectorlist`)의 `nonpt` 병합 방식 `week_Y`가 요구하는 날짜(대표 1주일 + 공휴일)와 정확히 일치했다.

```text
[만들어진 nonpt 날짜]      20220101 ~ 20220109 (9개)
[week_Y 방식이 필요로 하는 날짜] 20220101 ~ 20220109 (9개)
```

## 7. 후속 조치

- **진단용 폴더 정리**: `SMOKEv5.3_debug`와 진단용 설정 파일(`directory_definitions_debug.csh` 등)은 진단 후 로그·설정 diff와 결과를 보관하고 백업 폴더로 이동한다. 경로를 확인하지 않은 재귀 삭제는 수행하지 않는다.
- **설치 가이드 반영**: [SMOKE 구축 가이드](SMOKE_Installation_Guide.md)의 Makeinclude 수정 다음 단계에 "소스 수정(`procar2pt.f`)"을 추가해, 처음부터 수정된 소스로 컴파일하도록 순서를 재구성한다.
- **SMOKE 개발팀 보고(권장)**: 같은 결함이 다음 버전에도 남아 있을 수 있으므로, [CEMPD/SMOKE Issues](https://github.com/CEMPD/SMOKE/issues)에 증상·원인·수정 내용을 보고한다. SMOKE를 새 버전으로 바꿀 때는 이 수정이 반영되었는지 먼저 확인한다.
- **유사 사례 점검**: SMOKE의 다른 소스에도 초기화되지 않은 지역 포인터를 `ASSOCIATED()`로 검사하는 코드가 있을 수 있다. 다른 부문이나 CAPSS 처리에서 비슷한 Segmentation fault가 나면, 3.1의 디버그 빌드로 같은 방식으로 위치를 찾는다.

## 8. 관련 문서

- [SMOKE 구축 가이드](SMOKE_Installation_Guide.md)
- [SMOKE GitHub 저장소](https://github.com/CEMPD/SMOKE) — 원본 `src/smkinven/procar2pt.f`
- [SMOKE-ExampleCase-v3](https://github.com/CEMPD/SMOKE-ExampleCase-v3)
