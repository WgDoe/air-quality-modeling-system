# Rocky Linux 설치 가이드

## 1. 문서 목적

본 문서는 x86_64 기반 데스크톱 또는 워크스테이션에 **Rocky Linux 9 계열**을 설치하기 위한 표준 절차를 정리한 설치 가이드이다.

운영체제 설치 이미지 다운로드, 부팅 USB 제작, UEFI 부팅, 설치 과정의 주요 선택사항, 설치 완료 후 기본 확인 항목까지를 포함한다.

본 문서는 특정 프로젝트의 진행 단계나 향후 구축 일정이 아니라, Linux 기반 과학계산·모델링 시스템 또는 서버/워크스테이션 구축 시 재사용할 수 있는 기본 설치 절차를 목적으로 한다.

---

## 2. 대상 환경

- 시스템 유형: Desktop / Workstation / Server
- CPU Architecture: x86_64
- 운영체제: Rocky Linux 9 계열
- 설치 방식: USB 부팅을 이용한 신규 설치
- 권장 부팅 방식: UEFI
- 권장 파티션 방식: Automatic Partitioning
- 패키지 관리도구: `dnf`

Rocky Linux는 RHEL 계열과 호환되는 무료 Linux 배포판으로, 연구용·업무용·상업용 시스템의 기반 운영체제로 사용할 수 있다.

---

## 3. Rocky Linux 설치 이미지 다운로드

### 3.1 공식 다운로드 사이트

Rocky Linux 공식 다운로드 페이지:

https://rockylinux.org/download

Rocky Linux 9 x86_64 ISO 저장소:

https://download.rockylinux.org/pub/rocky/9/isos/x86_64/

### 3.2 권장 이미지

일반적인 워크스테이션 설치에서는 **DVD ISO** 사용을 권장한다.

예:

```text
Rocky-9.x-x86_64-dvd.iso
```

또는 최신 Rocky Linux 9 이미지:

```text
Rocky-9-latest-x86_64-dvd.iso
```

Rocky Linux 설치 이미지는 용도에 따라 다음과 같이 제공될 수 있다.

```text
boot.iso
minimal.iso
dvd.iso
```

| 이미지 | 용도 |
|---|---|
| Boot ISO | 네트워크 기반 설치 |
| Minimal ISO | 최소 구성 설치 |
| DVD ISO | 일반 설치 및 다양한 패키지 선택 |

GUI 환경과 개발도구 설치를 고려하는 워크스테이션에서는 DVD ISO가 편리하다.

특히 **네트워크가 없는 환경에서 설치할 경우 DVD ISO 사용을 권장**한다. DVD ISO에는 `BaseOS`, `AppStream` 등의 설치 패키지가 포함되어 있어 로컬 미디어만으로 설치할 수 있다.

---

## 4. 설치 USB 준비

DVD ISO는 비교적 용량이 크므로 충분한 용량의 USB를 준비한다.

권장:

```text
16 GB 이상
가능하면 32 GB 이상
```

> USB 제작 과정에서 기존 데이터가 삭제될 수 있으므로 필요한 자료는 사전에 백업한다.

---

## 5. Rufus를 이용한 부팅 USB 제작

Windows 환경에서는 **Rufus**를 이용하여 설치 USB를 만들 수 있다.

Rufus 공식 사이트:

https://rufus.ie/

### 5.1 기본 설정 예

```text
장치(Device)
→ 설치용 USB 선택

부트 선택(Boot selection)
→ Rocky Linux DVD ISO 선택

파티션 방식
→ GPT

대상 시스템
→ UEFI
```

기타 파일시스템 관련 설정은 특별한 이유가 없다면 Rufus 기본값을 사용한다.

---

## 6. ISOHybrid 이미지 기록 방식

Rocky Linux DVD ISO를 Rufus로 기록하는 과정에서 다음과 같은 메시지가 표시될 수 있다.

```text
ISOHybrid 이미지가 감지되었습니다.
```

Rufus에서는 다음 두 가지 방식 중 하나를 선택할 수 있다.

```text
○ ISO 이미지 모드로 쓰기
○ DD 이미지 모드로 쓰기
```

### 6.1 Rocky Linux에서는 DD 이미지 모드 권장

Rocky Linux 설치 USB를 만들 때는 다음 항목을 선택한다.

```text
● DD 이미지 모드로 쓰기
```

Rocky Linux의 ISO 이미지는 ISOHybrid 구조이므로 DD 방식으로 기록하면 원본 ISO의 디스크 구조를 그대로 USB에 복제할 수 있다.

특히 **네트워크가 없는 시스템에서 오프라인 설치를 수행할 경우 DD 이미지 모드를 사용하는 것이 중요하다.**

### 6.2 ISO 이미지 모드 사용 시 발생할 수 있는 문제

DVD ISO를 사용했더라도 Rufus의 **ISO 이미지 모드**로 USB를 만든 경우 다음과 같은 현상이 발생할 수 있다.

- USB 자체는 정상적으로 부팅됨
- USB 내부에 `BaseOS`, `AppStream` 폴더가 존재함
- 그러나 Rocky Linux 설치 프로그램의 **Installation Source(설치 원천)** 에서 로컬 미디어를 정상적으로 인식하지 못함
- 설치 원천으로 `Closest mirror`만 표시될 수 있음
- 네트워크가 없는 환경에서는 설치를 계속 진행할 수 없음

이 경우 USB를 **DD 이미지 모드로 다시 작성**하면 설치 프로그램이 로컬 설치 미디어를 정상적으로 인식할 수 있다.

### 6.3 정상적인 오프라인 설치 미디어 확인

DVD ISO가 정상적으로 사용된 경우 원본 미디어에는 일반적으로 다음과 같은 디렉터리가 포함된다.

```text
AppStream/
BaseOS/
EFI/
images/
isolinux/
```

다만 위 디렉터리가 보인다고 해서 Rufus의 ISO 이미지 모드가 항상 정상적인 오프라인 설치 미디어로 인식되는 것은 아니다.

오프라인 설치에서는 다음 조합을 권장한다.

```text
Rocky Linux DVD ISO
        ↓
Rufus
        ↓
DD 이미지 모드
        ↓
UEFI USB 부팅
        ↓
Local Media / Auto-detected installation media
        ↓
오프라인 설치
```

### 6.4 DD 모드 작성 후 Windows에서의 USB 표시

DD 이미지 모드로 USB를 만들면 Windows에서 해당 USB를 다시 연결했을 때 일반 데이터 USB처럼 표시되지 않거나, 일부 파티션만 보이거나, 포맷이 필요하다는 메시지가 표시될 수 있다.

이는 DD 방식으로 Linux 설치 미디어 구조가 그대로 기록된 결과일 수 있으며, 설치 USB 자체가 잘못 만들어졌다는 의미는 아니다.

Windows가 포맷을 요구하는 경우 설치 전에 포맷하지 않는다.

---

## 7. USB 부팅

설치 USB 제작이 완료되면 대상 컴퓨터에 USB를 연결한 뒤 시스템을 재부팅한다.

부팅 직후 제조사별 Boot Menu 또는 BIOS/UEFI 진입키를 사용한다.

대표적인 키:

```text
F2
F8
F10
F11
F12
DEL
ESC
```

부팅 메뉴에서 같은 USB가 여러 형태로 나타나는 경우에는 가능하면 다음 형태를 선택한다.

```text
UEFI: USB 장치명
```

Legacy/CSM 방식보다는 UEFI 방식 사용을 권장한다.

---

## 8. Rocky Linux 설치 시작

USB 부팅이 정상적으로 이루어지면 Rocky Linux 설치 메뉴가 표시된다.

```text
Install Rocky Linux
Test this media & Install Rocky Linux
```

설치 미디어의 무결성을 먼저 확인하려면 `Test this media & Install Rocky Linux`를 선택한다.

---

## 9. 설치 원천(Installation Source) 확인

DVD ISO를 DD 이미지 모드로 정상적으로 작성한 경우 설치 프로그램은 USB를 로컬 설치 미디어로 자동 인식해야 한다.

정상적인 예:

```text
Local Media
Auto-detected installation media
```

네트워크가 없는 시스템에서는 설치 원천이 로컬 미디어로 인식되는지 반드시 확인한다.

### 9.1 Closest mirror만 표시되는 경우

다음과 같은 경우 설치 원천이 `Closest mirror`만 표시될 수 있다.

- Boot ISO를 사용한 경우
- 네트워크 설치용 이미지를 사용한 경우
- DVD ISO를 Rufus의 ISO 이미지 모드로 기록하여 로컬 repository 인식에 문제가 발생한 경우
- 설치 USB가 비정상적으로 작성된 경우

이 경우 가장 먼저 다음을 확인한다.

```text
1. ISO 파일이 dvd.iso인지 확인
2. USB를 Rufus에서 DD 이미지 모드로 다시 작성
3. 다시 UEFI 방식으로 부팅
4. Installation Source에서 Local Media 인식 여부 확인
```

오프라인 환경에서는 `Closest mirror`를 사용할 수 없으므로 반드시 로컬 미디어가 인식되어야 한다.

---

## 10. 설치 언어 및 기본 설정

### 10.1 시간대

대한민국에서 사용하는 경우:

```text
Asia/Seoul
```

### 10.2 키보드

```text
English (US)
Korean
```

운영체제 및 개발환경 설정에서는 영문 키보드를 기본으로 사용하는 것이 편리하다.

---

## 11. 파티션 설정

일반적인 신규 설치에서는 **Automatic Partitioning**을 사용할 수 있다.

설치 프로그램은 시스템 환경에 따라 다음 영역을 자동으로 구성한다.

```text
EFI System Partition
/boot
swap
Linux system 영역
```

단일 디스크 워크스테이션에서는 자동 파티셔닝이 관리하기 편리하다.

수동 파티셔닝은 OS와 데이터 디스크를 물리적으로 분리하거나 RAID, 별도 `/home`, `/data`, `/work` 파일시스템이 필요한 경우에 검토한다.

---

## 12. 소프트웨어 설치 유형

예:

```text
Workstation
Server with GUI
Server
Minimal Install
```

일반적인 모델링 또는 과학계산 워크스테이션에서는 GUI가 필요한 경우 `Workstation` 또는 `Server with GUI`가 편리하다.

---

## 13. 네트워크 설정

네트워크를 사용할 수 있는 경우 설치 단계에서 네트워크 인터페이스를 활성화한다.

설치 후 인터넷 연결은 운영체제 업데이트, 개발도구 설치, Git 사용, 외부 라이브러리 다운로드 등에 필요하다.

네트워크가 없는 환경에서도 DVD ISO와 정상적인 로컬 설치 미디어를 사용하면 Rocky Linux 기본 설치는 가능하다.

---

## 13. USB 무선랜 어댑터를 이용한 네트워크 연결

유선 네트워크가 없는 시스템에서는 USB 무선랜 어댑터를 이용해 인터넷에 연결할 수 있다.

본 환경에서는 **ipTIME N150UA**를 연결하여 확인하였으며, 장치 내부 칩셋은 다음과 같이 인식되었다.

```text
Ralink Technology, Corp. MT7601U Wireless Adapter
```

### 14.1 USB 장치 인식 확인

USB 무선랜을 연결한 뒤 다음 명령으로 장치가 보이는지 확인한다.

```bash
lsusb
```

MT7601U가 정상 인식된 예:

```text
Ralink Technology, Corp. MT7601U Wireless Adapter
```

`lsusb`에 장치가 보이면 USB 장치 자체는 운영체제에서 인식된 상태이다.

---

### 14.2 네트워크 인터페이스 확인

다음 명령을 실행한다.

```bash
nmcli device
```

Wi-Fi 장치가 정상적으로 생성된 경우 `TYPE`이 `wifi`인 항목이 표시된다.

예:

```text
DEVICE        TYPE      STATE
wlan0         wifi      disconnected
enp3s0        ethernet  disconnected
lo            loopback  unmanaged
```

인터페이스 이름은 시스템에 따라 `wlan0`, `wlp...` 등으로 다르게 표시될 수 있다.

추가 확인:

```bash
ip link
```

---

### 14.3 MT7601U driver 확인

MT7601U 칩셋의 kernel module이 로드되었는지 확인한다.

```bash
lsmod | grep mt7601u
```

필요하면 kernel message도 확인한다.

```bash
dmesg | grep -i -E "mt7601|firmware|wlan|wifi"
```

다음과 같은 firmware 오류가 있는 경우 추가 firmware package가 필요할 수 있다.

```text
firmware: failed to load ...
```

---

### 14.4 Wi-Fi 활성화

Wi-Fi radio가 꺼져 있는 경우 다음 명령으로 활성화한다.

```bash
nmcli radio wifi on
```

주변 Wi-Fi 검색:

```bash
nmcli device wifi list
```

---

### 14.5 숨김 SSID 연결

SSID가 숨겨져 있어 일반적인 Wi-Fi 검색 목록에 표시되지 않는 경우에는 NetworkManager 연결 프로파일을 먼저 생성하는 방법이 안정적이다.

먼저 Wi-Fi 장치 이름을 확인한다.

```bash
nmcli device
```

예를 들어 Wi-Fi interface가 `wlan0`이라면 다음과 같이 연결 프로파일을 생성한다.

```bash
nmcli connection add type wifi ifname wlan0 con-name AirNew2G ssid "AirNew.2G"
```

숨김 SSID임을 지정한다.

```bash
nmcli connection modify AirNew2G 802-11-wireless.hidden yes
```

WPA2-PSK 보안을 사용하는 경우 보안 방식을 설정한다.

```bash
nmcli connection modify AirNew2G wifi-sec.key-mgmt wpa-psk
```

비밀번호는 실제 값을 문서에 기록하지 않고 다음과 같이 입력한다.

```bash
nmcli connection modify AirNew2G wifi-sec.psk 'WIFI_PASSWORD'
```

위 설정까지 완료하면 GNOME의 Wi-Fi 설정 화면에서 해당 숨김 네트워크가 인식될 수 있으며, 화면에서 비밀번호를 입력하여 연결할 수도 있다.

명령줄에서 직접 연결하려면 다음을 실행한다.

```bash
nmcli connection up AirNew2G
```

> 비밀번호에 `!` 문자가 포함된 경우 Bash history expansion 때문에 `event not found` 오류가 발생할 수 있으므로 비밀번호는 **작은따옴표(' ')** 로 감싼다.

실제 운영 비밀번호는 문서나 Git 저장소에 기록하지 않는다.

---

### 14.6 2.4 GHz / 5 GHz 주의

본 환경에서 확인된 **MT7601U는 2.4 GHz 계열 무선랜**으로 사용하였다.

따라서 5 GHz 전용 SSID에는 연결할 수 없을 수 있다.

지원 주파수 확인:

```bash
iw list
```

2.4 GHz 주파수 예:

```text
2412 MHz
2437 MHz
2462 MHz
```

5 GHz 주파수 예:

```text
5180 MHz
5200 MHz
5220 MHz
```

주변 공유기가 5 GHz 전용으로 구성되어 있다면 2.4 GHz SSID를 별도로 사용하거나, 2.4 GHz를 지원하는 다른 액세스 포인트를 이용해야 한다.

---

### 14.7 iPhone 개인용 핫스팟 연결

유선망이나 2.4 GHz 공유기를 사용할 수 없는 경우 iPhone 개인용 핫스팟을 사용할 수 있다.

iPhone에서 다음 항목을 설정한다.

```text
설정
→ 개인용 핫스팟
→ 다른 사람의 연결 허용
→ 호환성 최대화 활성화
```

`호환성 최대화`를 활성화하면 구형 2.4 GHz Wi-Fi 장치와의 연결 호환성이 좋아질 수 있다.

Rocky Linux에서 주변 AP를 다시 검색한다.

```bash
nmcli radio wifi off
nmcli radio wifi on
nmcli device wifi rescan
nmcli device wifi list
```

iPhone hotspot SSID가 보이면 연결한다.

```bash
nmcli device wifi connect "IPHONE_SSID" password 'HOTSPOT_PASSWORD'
```

본 환경에서는 **ipTIME N150UA (MT7601U) + iPhone 개인용 핫스팟의 호환성 최대화 설정으로 인터넷 연결이 정상적으로 동작함을 확인하였다.**

---

### 14.8 연결 상태 확인

```bash
nmcli device
```

Wi-Fi 장치의 상태가 다음과 같이 표시되면 정상이다.

```text
connected
```

현재 연결 profile 확인:

```bash
nmcli connection show
```

IP 주소 확인:

```bash
ip addr
```

Routing table 확인:

```bash
ip route
```

---

## 15. 사용자 계정 및 관리자 권한

일반 사용자 계정을 생성하고 필요 시 관리자 권한을 부여한다.

시스템 패키지 설치 등 관리자 권한이 필요한 작업에는 `sudo`를 사용한다.

```bash
sudo dnf update
sudo dnf install package_name
```

---

## 16. 설치 완료 및 재부팅

필수 설정이 완료되면 설치를 시작한다.

설치 완료 후 재부팅하고 설치 USB를 제거하거나 BIOS/UEFI 부팅 순서를 내부 SSD/NVMe 우선으로 설정한다.

---

## 17. 설치 완료 후 기본 시스템 확인

### 운영체제 버전

```bash
cat /etc/os-release
```

### Kernel

```bash
uname -r
uname -a
```

### CPU

```bash
lscpu
```

### 메모리

```bash
free -h
```

### 저장장치

```bash
lsblk
df -h
```

### 네트워크

```bash
ip addr
```

### Hostname

```bash
hostname
hostnamectl
```

---

## 18. 설치 기록 권장 항목

상업용 시스템, 연구용 시스템 또는 장기간 유지해야 하는 모델링 시스템에서는 다음 항목을 기록한다.

```text
OS 배포판
OS 버전
Kernel 버전
CPU 모델
CPU core/thread
RAM 용량
Disk 구성
파일시스템
Hostname
Network 설정
설치 ISO 종류
USB 작성 도구
USB 작성 방식(DD/ISO)
설치일자
업데이트 이력
```

이 기록은 동일 시스템 재구축, 장애 복구, 버전 비교, 고객 시스템 납품 및 유지보수에 활용할 수 있다.

---

## 19. 참고 사이트

- Rocky Linux: https://rockylinux.org/
- Rocky Linux Documentation: https://docs.rockylinux.org/
- Rocky Linux Download: https://rockylinux.org/download
- Rufus: https://rufus.ie/

---

## 문서 정보

```text
문서명: Rocky_Linux_Installation_Guide.md
문서유형: Linux 운영체제 설치 가이드
적용대상: x86_64 Desktop / Workstation / Server
운영체제: Rocky Linux 9 계열
```
