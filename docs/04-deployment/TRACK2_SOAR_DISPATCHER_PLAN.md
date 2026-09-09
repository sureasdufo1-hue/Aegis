# [Architecture & Deployment] Track 2: SOAR 실시간 침해사고 알림 디스패처

> **문서 ID:** `DEP-SOAR-001`  
> **관련 요구사항:** `REQ-SOAR-01`  
> **품질 게이트:** `GATE-SOAR-01` (`PASS`)  
> **증적:** `evidence/EV-SOAR-001/`  

---

## 1. 개요 및 목적
Aegis SOC Lab의 탐지 파이프라인에서 탐지된 **Level 14 Critical (`CONFIRMED_COMPROMISE`)** 침해사고를 보안관제 요원에게 실시간 모바일 메신저(Slack, Discord, Generic Webhook)로 다채널 전파하고, 권고 초동 격리 명령어를 즉시 제공하는 SOAR 1차 알림 체계입니다.

---

## 2. 주요 구성 요소

```text
analyzer/alerting/
├── __init__.py           # 패키지 익스포트
├── dispatcher.py         # NotificationDispatcher 코어 엔진 (Slack Block Kit, Discord Embed, Webhook)
└── notifier.py           # Rich 콘솔 및 레거시 알림 호환 모듈

scripts/
└── simulate_soar_dispatch.py  # 모의 침해사고 디스패치 시뮬레이터 CLI

dashboard/
└── app.py                # /api/notifications/* 엔드포인트 연동
```

---

## 3. 핵심 안전장치 및 기능
1. **경보 피로도 억제 (Anti-Alert Fatigue)**:
   - 동일 공격자 IP에 대해 10분(`cooldown_minutes=10`) 슬라이딩 윈도우 쿨다운 적용.
   - 단순 Ping 등 진단 트래픽(`Diagnostic / Telemetry`)은 외부 발송 자동 차단(`SUPPRESSED`).
2. **조치 권고 포함 (Actionable Incident Payload)**:
   - 메시지 본문에 Gateway 방화벽 격리 명령어(`nft add element inet filter blocklist { <IP> }`)와 대시보드 바로가기 링크를 동봉.
3. **비밀정보 안전 보장 (No Secrets in Git)**:
   - Webhook URL은 환경변수로만 주입되며, 대시보드 API 응답 시 마스킹 처리.

---

## 4. 환경변수 가이드 (`.env.example`)

```bash
# Aegis SOC Lab - SOAR Notification Dispatcher Configuration
AEGIS_SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
AEGIS_DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/YOUR/DISCORD/WEBHOOK"
AEGIS_ALERT_WEBHOOK_URL="https://your-siem.corp.internal/api/webhook"
AEGIS_ALERT_COOLDOWN_MINUTES="10"
AEGIS_DASHBOARD_URL="http://10.77.10.10:8501"
AEGIS_ALERT_DRY_RUN="false"
```
