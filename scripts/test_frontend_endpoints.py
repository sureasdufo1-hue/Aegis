import sys
sys.path.insert(0, '.')
from fastapi.testclient import TestClient
from dashboard.app import app

client = TestClient(app)

endpoints = [
    ("GET", "/"),
    ("GET", "/api/health"),
    ("GET", "/api/dashboard/summary"),
    ("GET", "/api/action-proposals"),
    ("GET", "/api/alerts?limit=100"),
    ("GET", "/api/assets"),
    ("GET", "/api/audit/logs?limit=10"),
    ("GET", "/api/incidents"),
    ("GET", "/api/network/interfaces"),
    ("GET", "/api/policies"),
    ("GET", "/api/sensors"),
    ("GET", "/api/threats/countries"),
    ("GET", "/api/network/traffic?time_range=24h"),
    ("GET", "/threat-matrix"),
    ("GET", "/static/world_paths.json"),
    ("GET", "/api/elk/health"),
    ("GET", "/api/elk/stats"),
    ("GET", "/api/elk/events"),
    ("GET", "/api/elk/timeline/10.77.20.20"),
]

print("Testing all frontend API endpoints:")
for method, ep in endpoints:
    if method == "GET":
        resp = client.get(ep)
        status = resp.status_code
        print(f" {method:4} {ep:45} -> {status}")
