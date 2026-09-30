# 현재 관측 아키텍처와 M1/M2 목표

관측 시점: 2026-09-23 KST. 연결선은 **관측/설정/목표**를 구분한다.

```text
[현재 Windows PC DESKTOP-QIFELML, 10.10.70.151/25]
    ├─ VMware Workstation: soc-attacker / gateway / victim / sensor / siem (실행 중)
    │    └─ 기존 10.77.* SOC Lab. 게스트별 서비스·물리망 연결은 미검증.
    ├─ Docker Desktop: ELK 8.17.3, Wazuh 4.14.7 (컨테이너 실행 중)
    │    └─ 저장소 설정·로컬 Docker 볼륨. 물리 LOG 서버 위치 아님.
    └─ 저장소: Suricata·Snort·FastAPI·상관분석 코드와 과거 로컬 로그

[M1/M2 목표 — 현재 장비 상태 미검증]
10.10.70.128/25 → TrusGuard(.214)
                     ├─ DMZ Web 172.16.10.10
                     └─ 192.168.40.1/30 ↔ L3 .40.2/30
                                            ├─ VLAN10 Admin .10.2
                                            ├─ VLAN20 User .20.2
                                            └─ VLAN30 DB .30.2 / LOG .30.3
                         L3 Gi1/0/24 ──SPAN──> Gi1/0/13 → Analyse PC2 (수집 NIC 무IP)
```

현재 PC의 물리 이더넷은 `10.10.70.151/25`이고 두 번째 이더넷은 비활성이다. 따라서 이 PC를 관리자 PC `.10.2`, LOG `.30.3`, Analyse PC2 중 하나로 **동일시할 수 없다**. `10.77.*` VMware VM과 Docker 컨테이너가 실제 M1/M2 장비에 연결됐다는 증거도 없다.

## 가시성 경계

Gi1/0/24 Transit SPAN은 방화벽↔L3 통과 트래픽의 후보 수집점이다. TrusGuard WAN↔DMZ Web(`eth1↔eth3`), 같은 VLAN 내부, L3가 로컬 라우팅한 트래픽 전부를 보장하지 않는다. PC2의 실제 NIC/패킷 수신을 `tcpdump` 등으로 확인하기 전 Suricata 배포 게이트는 `BLOCKED`다. Snort는 현 승인 기준상 동일 PCAP의 보조·오프라인 검증 도구다.

## 아직 미확정인 배치

- LOG `.30.3`의 원문 수집·RAID·자원·서비스는 현장 접속 증거가 없다.
- M5/M6 정정 계획은 LOG와 ELK의 동일 호스트 설치를 제안하나, 현재 Docker ELK만의 순간 메모리 약 9.36GiB가 제안 LOG RAM 8GiB를 넘는다. 용량 산정 후 통합/분리 결정이 필요하다.
- Wazuh·FastAPI·상관분석의 물리망 운영 호스트/IP는 미배정이다. 기존 PC의 Docker 실행을 목표 배치로 간주하지 않는다.
- 관리자 PC는 브라우저 접근 역할을 목표로 하고 수집·분석 백엔드는 서버에서 독립 실행해야 한다.
