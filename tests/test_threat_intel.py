from analyzer.detection.threat_intel import ThreatIntelEngine


def test_threat_intel_ip_match():
    match = ThreatIntelEngine.check_ip("198.51.100.44")
    assert match is not None
    assert match.threat_group == "CobaltStrike_C2"
    assert match.confidence >= 0.90


def test_threat_intel_domain_match():
    match = ThreatIntelEngine.check_domain("evil-c2.lab")
    assert match is not None
    assert match.indicator_type == "DOMAIN"


def test_threat_intel_benign_ip():
    match = ThreatIntelEngine.check_ip("8.8.8.8")
    assert match is None
