from analyzer.models import EngineType, Severity
from analyzer.parsers.eve_parser import parse_eve_record
from analyzer.parsers.snort_parser import parse_snort_record


def test_suricata_eve_parser():
    record = {
        "timestamp": "2026-08-24T12:00:00.000000Z",
        "event_type": "alert",
        "src_ip": "198.51.100.44",
        "src_port": 45123,
        "dest_ip": "192.168.1.10",
        "dest_port": 80,
        "proto": "TCP",
        "community_id": "1:abc12345",
        "alert": {
            "action": "allowed",
            "gid": 1,
            "signature_id": 1000001,
            "rev": 1,
            "signature": "SOC-ATTACK: Web SQL Injection - UNION SELECT Attempt",
            "category": "Web Application Attack",
            "severity": 2,
            "metadata": {
                "attack_technique": ["T1190"]
            }
        },
        "http": {
            "hostname": "victim-shop.local",
            "url": "/search?q=union+select",
            "http_user_agent": "Mozilla/5.0"
        }
    }

    alert = parse_eve_record(record)
    assert alert is not None
    assert alert.engine == EngineType.SURICATA
    assert alert.sid == 1000001
    assert alert.src_ip == "198.51.100.44"
    assert alert.dst_ip == "192.168.1.10"
    assert alert.severity == Severity.HIGH
    assert alert.mitre_technique == "T1190"
    assert alert.http_uri == "/search?q=union+select"


def test_snort_parser():
    record = {
        "timestamp": "2026-08-24T12:05:00.000000Z",
        "class": "Web Application Attack",
        "gid": 1,
        "sid": 2000010,
        "rev": 1,
        "msg": "SNORT-ATTACK: Web SQL Injection UNION SELECT",
        "proto": "TCP",
        "src_addr": "203.0.113.88",
        "src_port": 50123,
        "dst_addr": "192.168.1.10",
        "dst_port": 80,
    }

    alert = parse_snort_record(record)
    assert alert is not None
    assert alert.engine == EngineType.SNORT
    assert alert.sid == 2000010
    assert alert.src_ip == "203.0.113.88"
    assert alert.severity == Severity.HIGH
