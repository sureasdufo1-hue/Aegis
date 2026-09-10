from pathlib import Path
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_github_pages_index_html_exists():
    index_path = REPO_ROOT / "docs" / "index.html"
    assert index_path.exists(), "docs/index.html must exist for GitHub Pages hosting"

    html = index_path.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in html
    assert "Aegis SOC Detection & Monitoring Lab" in html
    assert "charset=\"UTF-8\"" in html


def test_github_pages_core_sections_presence():
    index_path = REPO_ROOT / "docs" / "index.html"
    html = index_path.read_text(encoding="utf-8")

    # Hero & Pillars
    assert "Suricata 8.0.6" in html
    assert "Snort 3.12.2" in html
    assert "Wazuh 4.14.7" in html
    assert "3-Zone 격리 & 스텔스 센서" in html
    assert "Detection-as-Code & SOAR" in html
    assert "TLS 1.3 복호화 리버스 프록시" in html

    # Benchmark Data
    assert "92.31%" in html  # Precision
    assert "85.71%" in html  # Recall
    assert "10.00%" in html  # FPR
    assert "0.00%" in html   # SQLi FP

    # 15-Step Pipeline
    assert "15단계 무결성 증적 파이프라인" in html

    # Defense Guide 23 FAQ & Search
    assert "기술 면접 방어 가이드 23선" in html
    assert "id=\"faqSearch\"" in html
    assert "id=\"faqList\"" in html
    assert "Q1." in html
    assert "Q21." in html
    assert "Q22." in html
    assert "Q23." in html


def test_github_pages_workflow_syntax():
    workflow_path = REPO_ROOT / ".github" / "workflows" / "pages.yml"
    assert workflow_path.exists(), ".github/workflows/pages.yml must exist"

    with open(workflow_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert "deploy" in data.get("jobs", {})
    deploy_job = data["jobs"]["deploy"]
    assert deploy_job.get("runs-on") == "ubuntu-latest"
    assert any("upload-pages-artifact" in str(step.get("uses", "")) for step in deploy_job.get("steps", []))
    assert any("deploy-pages" in str(step.get("uses", "")) for step in deploy_job.get("steps", []))
