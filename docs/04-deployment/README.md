# 🚀 04. SOC Detection & Monitoring Lab Implementation Plan (v1.0)

> **원본 문서**: [`SOC_Detection__Monitoring_Lab_Implementation_Plan_v1.0.pdf`](./SOC_Detection__Monitoring_Lab_Implementation_Plan_v1.0.pdf)  
> **문서 버전**: v1.0 (64 Pages)  
> **기준 일자**: 2026-08-24  
> **프로젝트 명**: SOC Detection & Monitoring Lab  

---

## 1. 30단계 구축 단계 및 품질 게이트 (Phase & Gate Roadmap)

```
[Phase 0~8: 인프라 & 패킷 가시성]
  Phase 0: Host Readiness ➔ GATE-HOST-01
  Phase 1: Repository Baseline
  Phase 2: Hyper-V Virtual Network
  Phase 3: VM Provisioning
  Phase 4: IP Address Configuration ➔ GATE-NET-01
  Phase 5: Gateway Routing
  Phase 6: Gateway Firewall ➔ GATE-FW-01
  Phase 7: Port Mirroring ➔ GATE-MIRROR-01
  Phase 8: Packet Visibility Validation (tcpdump) ➔ GATE-NET-01 [CRITICAL]
        │
        ▼
[Phase 9~14: 듀얼 IDS 배포 & 룰셋 검증]
  Phase 9: Suricata Deployment
  Phase 10: Suricata Configuration ➔ GATE-SURI-01
  Phase 11: Detection Validation ➔ GATE-DETECT-01
  Phase 12: PCAP Evidence Generation ➔ GATE-PCAP-01
  Phase 13: Snort Deployment ➔ GATE-SNORT-01
  Phase 14: Snort Offline PCAP Validation
        │
        ▼
[Phase 15~20: Wazuh SIEM 통합 & 대시보드]
  Phase 15: Wazuh Host Readiness
  Phase 16: Wazuh Deployment ➔ GATE-WAZUH-01
  Phase 17: Sensor Wazuh Agent
  Phase 18: Victim Wazuh Agent
  Phase 19: Suricata-Wazuh Integration ➔ GATE-SIEM-01
  Phase 20: Dashboard Validation
        │
        ▼
[Phase 21~30: 관제 분석, 튜닝, 증적 및 릴리즈]
  Phase 21: Attack Scenario Execution
  Phase 22: SOC Investigation ➔ GATE-ANALYSIS-01
  Phase 23: MITRE ATT&CK Mapping
  Phase 24: False Positive Analysis
  Phase 25: Detection Tuning ➔ GATE-TUNE-01
  Phase 26: Re-test Verification
  Phase 27: End-to-End Validation ➔ GATE-E2E-01
  Phase 28: Evidence Packaging
  Phase 29: Portfolio Documentation ➔ GATE-PORTFOLIO-01
  Phase 30: Final Release Gate ➔ GATE-FINAL-01
```

---

## 2. 절대 원칙: 패킷 가시성 우선 (Packet Visibility Before IDS)

> [!IMPORTANT]
> **패킷 가시성 검증(GATE-NET-01) 완료 전에는 다운스트림 IDS 및 SIEM 통합 작업을 절대 진행하지 않습니다.**
> - 공격자(`10.77.20.20`)에서 희생 서버(`10.77.30.20`)로의 트래픽이 센서 모니터링 인터페이스(`nic-monitor`)에서 `tcpdump`로 온전히 관측되어야만 Suricata/Snort 룰 검증을 개시합니다.
