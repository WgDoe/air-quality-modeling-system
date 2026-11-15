# MCIP Case 반복 실행 가이드 (설치 이후)

> 설치/컴파일: [MCIP 기존 가이드 §5–9](../mcip/MCIP_Installation_Guide.md). 실제 실행 명령·스크립트 원문: [MCIP 기존 가이드 §10](../mcip/MCIP_Installation_Guide.md).

## 현재 기준 상태
MCIP 5.5, `TEST_20260901` d01~d04(27·09·03·01KM) 변환 및 기존 GRIDDESC와 격자 일치, 각 도메인 정상종료 기록. CCTM에서 이 결과의 실제 사용·정합성은 미검증.

## 기간만 변경하는 경우: 원문 §10.7 Case settings 5개

`run_mcip_busan.csh`를 새 CASE로 복사한 뒤 아래 다섯 변수를 먼저 수정한다. 예시 날짜는 설명용이며 실제 새 CASE의 WRF 출력 날짜와 비교해야 한다.

| 변수 | 기존 TEST_20260901 | 예시(2026-10-01 ~ 10-03) |
|---|---|---|
| `CASE_DIR` | `$ROOT/CASES/BUSAN/TEST_20260901` | `$ROOT/CASES/BUSAN/<CASE명>` |
| `MCIP_START` | `2026-08-31-01:00:00.0000` | `2026-10-01-01:00:00.0000` |
| `MCIP_END` | `2026-09-02-00:00:00.0000` | `2026-10-03-00:00:00.0000` |
| `DATE_TAG` | `2026083100` | `2026100100` |
| `MetDates` | `( 2026-08-31 2026-09-01 2026-09-02 )` | `( 2026-10-01 2026-10-02 2026-10-03 )` |

그리드가 같으면 기존 GRIDDESC·window를 유지할 수 있다. 도메인이 달라지면 §10.3의 격자 설정·도메인 매핑·`geo_em`·MCIP 출력과 하위 배출량 격자를 모두 다시 확인한다.

## 새 Case에 대해 확인할 순서
1. WRF 출력 준비: `wrfout_d01~d04_*`의 **요청 시각 범위**, 도메인, 수직층 확인. 새 Case 입력을 기존 시험입력과 혼동하지 않는다.
2. [§10.2–10.3](../mcip/MCIP_Installation_Guide.md): Case 경로·MCIP 도메인 매핑 d01→27KM, d02→09KM, d03→03KM, d04→01KM, `GRIDDESC`·window·grid 일치 검토.
3. [§10.4](../mcip/MCIP_Installation_Guide.md): 문서의 `run_mcip_busan.csh` 생성 블록을 새 Case의 환경·입출력 경로·날짜에 맞춰 적용. **이 스크립트는 소스 컴파일 명령이 아니라 반복 실행용이다.**
4. [§10.5](../mcip/MCIP_Installation_Guide.md): `./run_mcip_busan.csh d01` 방식으로 각 도메인을 선택 실행(원문 경로·실행권한 확인).
5. [§10.6–10.8](../mcip/MCIP_Installation_Guide.md): 각 `mcip_<dom>.log`의 정상종료, `METCRO2D/3D`, `GRIDCRO2D`, `GRIDDOT2D`, 기간·grid·수직층·LANDUSEF 검증.

## Case 변경점 기록
| 항목 | 바꾸는 위치/확인점 |
|---|---|
| Case ID와 WRF 입력 | 원문 §10.4 스크립트 입력 폴더/파일 |
| 시작/종료 UTC | 원문 §10.4 기간 옵션, wrfout 시각 |
| 도메인 | `d01~d04` 매핑과 출력 폴더 |
| grid | 원문 §10.3 GRIDDESC 정의·window |
| 토지이용 | 해당 도메인의 `geo_em` 파일과 LANDUSEF |
| 출력 | Case의 `MCIP/<GRID>`와 로그 경로 |

WRF 변화가 없다면 MCIP의 설정/출력만 다시 생성할 수 있다. 반대로 WRF 기간·grid가 바뀌었는데 옛 MCIP 파일을 그대로 연결하지 않는다. 새 출력이 배출량 시간분배·점오염원 플룸상승·MEGAN에 미치는 영향도 확인한다.
