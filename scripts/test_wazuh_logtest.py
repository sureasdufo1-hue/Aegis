import subprocess
from pathlib import Path

line = Path("logs/suricata/eve.json").read_text(encoding="utf-8").strip().splitlines()[0]
res = subprocess.run(
    ["docker", "exec", "-i", "soc-wazuh-manager", "/var/ossec/bin/wazuh-logtest-legacy"],
    input=line,
    text=True,
    capture_output=True
)
print("STDOUT:", res.stdout)
print("STDERR:", res.stderr)
