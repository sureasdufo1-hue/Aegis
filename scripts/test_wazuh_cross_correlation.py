import subprocess

logs = [
    # 1. Suricata Network Anomaly
    '{"timestamp": "2026-09-09T08:00:00.000000Z", "event_type": "alert", "src_ip": "10.77.20.20", "dest_ip": "10.77.30.20", "alert": {"signature_id": 9020001, "signature": "SOC-ANOMALY: High-Frequency SSH Connection Threshold Exceeded"}}',
    # 2. Host Auth Failure
    'Sep  9 08:00:05 soc-victim sshd[12345]: Failed password for invalid user admin from 10.77.20.20 port 45100 ssh2',
    # 3. Host Auth Failure 2
    'Sep  9 08:00:07 soc-victim sshd[12347]: Failed password for invalid user admin from 10.77.20.20 port 45102 ssh2',
    # 4. Host Auth Success (Takeover)
    'Sep  9 08:00:10 soc-victim sshd[12348]: Accepted password for root from 10.77.20.20 port 45104 ssh2',
]

input_data = "\n".join(logs) + "\n"

res = subprocess.run(
    ["docker", "exec", "-i", "soc-wazuh-manager", "/var/ossec/bin/wazuh-logtest-legacy"],
    input=input_data,
    text=True,
    capture_output=True
)

output = res.stderr
lines = output.splitlines()

print("=" * 70)
print(" Wazuh Cross-Correlation Test: Network Anomaly + Host Auth Logs")
print("=" * 70)

current_event = 0
for line in lines:
    if "Rule id:" in line or "Level:" in line or "Description:" in line or "Phase 1" in line:
        if "Phase 1" in line:
            current_event += 1
            print(f"\n--- Event {current_event} ---")
        print(" ", line.strip())
