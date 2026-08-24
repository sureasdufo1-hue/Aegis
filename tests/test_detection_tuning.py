from scripts.verify_detection_tuning import evaluate_suricata_rule


def test_baseline_rule_false_positive():
    # Baseline rev 1: Any GET triggers alert
    is_normal_alert = evaluate_suricata_rule(rule_rev=1, http_method="GET", http_uri="/index.html")
    assert is_normal_alert is True, "Baseline rev 1 should generate FP on normal GET"


def test_tuned_rule_fp_reduction_and_attack_retention():
    # Tuned rev 2: Normal GET does not alert, suspicious marker alerts
    is_normal_alert = evaluate_suricata_rule(rule_rev=2, http_method="GET", http_uri="/index.html")
    is_attack_alert = evaluate_suricata_rule(rule_rev=2, http_method="GET", http_uri="/soc-lab-suspicious")

    assert is_normal_alert is False, "Tuned rev 2 must eliminate FP on normal GET"
    assert is_attack_alert is True, "Tuned rev 2 must retain alert on attack marker"
