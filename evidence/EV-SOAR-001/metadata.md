# Evidence Record: EV-SOAR-001

## 1. Metadata Summary

| Field | Value |
|---|---|
| **Evidence ID** | `EV-SOAR-001` |
| **Requirement** | `REQ-SOAR-01` (Real-Time Incident Notification & Actionable Response) |
| **Design Reference** | `docs/04-deployment/TRACK2_SOAR_DISPATCHER_PLAN.md` / `AGENTS.md` Sec 1, 14, 17, 18 |
| **Implementation Phase** | Track 2: SOAR Real-Time Multi-Channel Alert Dispatcher |
| **Test** | Multi-Channel Dispatch (Slack Block Kit, Discord Embed, Generic JSON Webhook), Cooldown Deduplication, Diagnostic Suppression, Mock Transport Delivery |
| **Scenario ID** | `SCN-SOAR-001` (Account Takeover & C2 Multi-Stage Incident Dispatch) |
| **Timestamp** | `2026-09-10T08:53:00+09:00` |
| **Component** | `analyzer/alerting/dispatcher.py` ➔ FastAPI Dashboard (`/api/notifications/*`) ➔ Multi-channel Outbound |
| **Expected** | Level 14 Critical incidents dispatched in real time with actionable isolation commands (`nft add element ...`), Slack/Discord/Webhook formatting, 10m sliding window cooldown to prevent alert fatigue |
| **Actual** | 100% PASS: 9/9 dispatcher unit tests pass, 3/3 dashboard notification API tests pass, CLI simulator verified, zero secret hardcoding |
| **Result** | **`PASS`** |
| **Completion Gate** | **`GATE-SOAR-01 = PASS`** |

---

## 2. Multi-Channel Payload Specifications

### 2.1 Supported Outbound Channels
1. **Slack Block Kit**:
   - Header with Critical badge
   - 2-Column Fields: Incident ID, Activity Status, Attacker IP, Victim Assets, MITRE ATT&CK, Total Alerts
   - Code block with recommended gateway firewall isolation command:
     `nft add element inet filter blocklist { 10.77.20.20 }`
   - Interactive action button linking to 3D Web Dashboard (`http://10.77.10.10:8501/`)
2. **Discord Rich Embed**:
   - Severity-based color coding (`0xE02424` for Critical Red, `0xF59E0B` for High Orange)
   - Inline fields for 5-Tuple, ATT&CK techniques, Playbook reference
   - Full-width code block for NFTables isolation
3. **Generic SIEM/SOAR JSON Webhook**:
   - RFC-compliant structured JSON for upstream SOAR ingestion

---

## 3. Anti-Alert Fatigue & Safety Guardrails

- **Sliding-Window Throttling**:
  - 기본 10분(`cooldown_minutes=10`) 이내 동일 공격자 IP에서 발생한 중복 경보는 `THROTTLED` 상태로 자동 억제.
  - 긴급 상황 시 `force=True` 옵션으로 쿨다운 우회 지원.
- **Diagnostic Noise Suppression**:
  - 단순 Ping(ICMP Echo), 정상 헬스체크 등 `Diagnostic / Telemetry` 성격의 이벤트는 외부 알림 발송 차단(`SUPPRESSED`).
- **Secret Protection**:
  - Webhook URL은 환경변수(`AEGIS_SLACK_WEBHOOK_URL`, `AEGIS_DISCORD_WEBHOOK_URL`, `AEGIS_ALERT_WEBHOOK_URL`)로만 주입.
  - API 조회 시 마스킹 처리(`https://hooks.slack.com/.../T0***/***`) 보장.

---

## 4. Test Verification Summary

```text
============================= test session starts =============================
tests/test_notification_dispatcher.py::test_slack_block_kit_formatting PASSED [ 11%]
tests/test_notification_dispatcher.py::test_discord_embed_formatting PASSED [ 22%]
tests/test_notification_dispatcher.py::test_generic_webhook_formatting PASSED [ 33%]
tests/test_notification_dispatcher.py::test_mock_webhook_delivery_success PASSED [ 44%]
tests/test_notification_dispatcher.py::test_cooldown_deduplication PASSED [ 55%]
tests/test_notification_dispatcher.py::test_diagnostic_suppression PASSED [ 66%]
tests/test_notification_dispatcher.py::test_webhook_failure_resilience PASSED [ 77%]
tests/test_notification_dispatcher.py::test_send_test_notification PASSED [ 88%]
tests/test_notification_dispatcher.py::test_masked_config PASSED         [100%]
tests/test_dashboard_api.py::test_dashboard_api_notifications_config PASSED
tests/test_dashboard_api.py::test_dashboard_api_notifications_history PASSED
tests/test_dashboard_api.py::test_dashboard_api_notifications_test_dispatch PASSED

============================== 12 passed in 0.84s ==============================
```

---

## 5. Artifact Files
- `evidence/EV-SOAR-001/metadata.md`: 본 증적 요약
- `evidence/EV-SOAR-001/payload_sample_slack.json`: Slack Block Kit 샘플
- `evidence/EV-SOAR-001/payload_sample_discord.json`: Discord Embed 샘플
- `evidence/EV-SOAR-001/payload_sample_generic.json`: Generic Webhook 샘플
- `evidence/EV-SOAR-001/dispatch_test_log.txt`: CLI 시뮬레이터 실행 로그
