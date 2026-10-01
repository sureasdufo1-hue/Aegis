"""
tests/test_cti_api.py
Integration & unit tests for the Live Threat Intelligence (CTI) reputation lookup engine and REST API.
Verifies AbuseIPDB scores, VirusTotal detections, GeoIP/ASN enrichment, and batch lookups.
"""

import pytest
from fastapi.testclient import TestClient

from dashboard.app import app
from dashboard.cti_engine import cti_engine, CTIEngine


@pytest.fixture
def client():
    return TestClient(app)


def test_cti_engine_lookup_malicious_c2():
    report = cti_engine.lookup("198.51.100.44")
    assert report.indicator == "198.51.100.44"
    assert report.verdict == "MALICIOUS"
    assert report.reputation_score == 100
    assert report.abuseipdb_score == 100
    assert report.total_reports >= 1000
    assert report.virustotal["positives"] >= 50
    assert "Cobalt Strike C2" in report.threat_categories
    assert "T1071.001" in report.mitre_techniques
    assert report.is_private_ip is False


def test_cti_engine_lookup_internal_safe():
    report = cti_engine.lookup("10.77.30.20")
    assert report.indicator == "10.77.30.20"
    assert report.verdict == "INTERNAL_SAFE"
    assert report.reputation_score == 0
    assert report.abuseipdb_score == 0
    assert report.is_private_ip is True


def test_cti_engine_lookup_tor_exit_node():
    report = cti_engine.lookup("185.220.101.5")
    assert report.indicator == "185.220.101.5"
    assert report.verdict in ("SUSPICIOUS", "MALICIOUS")
    assert report.abuseipdb_score >= 80
    assert "Tor Exit Node" in report.threat_categories
    assert report.geo["code"] == "DE"


def test_api_threat_intel_endpoint_c2(client):
    res = client.get("/api/threats/intel/198.51.100.44")
    assert res.status_code == 200
    data = res.json()
    assert data["indicator"] == "198.51.100.44"
    assert data["verdict"] == "MALICIOUS"
    assert data["abuseipdb_score"] == 100
    assert "virustotal" in data
    assert data["virustotal"]["positives"] > 0
    assert "geo" in data
    assert data["geo"]["flag"] == "🇺🇸"


def test_api_threat_intel_batch(client):
    payload = {
        "indicators": ["198.51.100.44", "10.77.20.20", "185.220.101.5"],
    }
    res = client.post("/api/threats/intel/batch", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) == 3
    assert data[0]["indicator"] == "198.51.100.44"
    assert data[1]["indicator"] == "10.77.20.20"
    assert data[2]["indicator"] == "185.220.101.5"
