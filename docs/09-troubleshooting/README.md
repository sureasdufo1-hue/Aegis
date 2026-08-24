# 🛠️ 09. 장애 해결 및 문제 해결 가이드 (Troubleshooting Standard)

> **기준 규정**: AGENTS.md Section 24 (Troubleshooting)  

---

## 1. 주요 장애 해결 트리 (Key Troubleshooting Trees)

### 1.1 TRB-001: Suricata Alert 미발생 시 조치 트리

```text
공격 트래픽이 실제 발신되었는가?
├─ NO  ➔ 공격 스크립트 실행 상태 확인
└─ YES
    ↓
희생 서버(soc-victim)에 패킷이 도달했는가? (tcpdump on soc-victim)
├─ NO  ➔ 게이트웨이 nftables 포워딩 정책 & 라우팅 테이블 점검
└─ YES
    ↓
Hyper-V Port Mirroring이 정상 구성되었는가? (Get-VMNetworkAdapter)
├─ NO  ➔ Set-VMNetworkAdapter Source/Destination 재지정
└─ YES
    ↓
센서 nic-monitor에서 tcpdump로 패킷이 관측되는가?
├─ NO  ➔ 동일 vSwitch(soc-vsw-victim) 연결 여부 확인
└─ YES
    ↓
Suricata 서비스가 구동 중이며 해당 NIC를 바인딩하고 있는가?
├─ NO  ➔ systemctl restart suricata / af-packet 인터페이스 확인
└─ YES
    ↓
Suricata Rule이 정상 로드되었는가? (suricata -T)
├─ NO  ➔ 룰 문법 및 SID 중복 여부 확인
└─ YES ➔ EVE JSON 출력 설정 (eve-log.enabled = yes) 확인
```

---

### 1.2 TRB-002: Suricata Alert는 발생하나 Wazuh SIEM에 수집되지 않는 경우

```text
/var/log/suricata/eve.json 파일에 신규 alert 이벤트가 기록되는가?
├─ NO  ➔ Suricata EVE 로깅 설정 점검
└─ YES
    ↓
Wazuh Agent 서비스(wazuh-agent)가 실행 중인가?
├─ NO  ➔ sudo systemctl restart wazuh-agent
└─ YES
    ↓
Wazuh Agent 설정(ossec.conf)에 <localfile> eve.json이 포함되어 있는가?
├─ NO  ➔ ossec.conf에 json 수집 블록 추가
└─ YES
    ↓
센서에서 Wazuh Manager(10.77.10.10) 1514/1515 포트 연결이 가능한가?
├─ NO  ➔ 게이트웨이 방화벽 허용 정책 확인 (1514/1515 TCP)
└─ YES
    ↓
Wazuh Dashboard에서 'agent.name:soc-sensor'로 검색되는가?
└─ YES ➔ local_rules.xml 디코더 룰셋 매칭 확인
```
