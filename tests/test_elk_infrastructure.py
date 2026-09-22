"""
Unit & Infrastructure Validation Tests for Phase ELK-1 / ELK-2
Validates:
1. docker-compose.elk.yml structure, image pinning (8.17.3), port isolation (9201/5602)
2. elasticsearch.yml configuration, single-node discovery, security parameters
3. .env.elk.example structure and safety (no raw credentials)
4. docs/elk architecture and design documentation completeness
5. Port collision absence with Wazuh (wazuh 9200/5601 vs elk 9201/5602)
"""

from pathlib import Path
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_docker_compose_elk_structure_and_port_isolation():
    compose_file = REPO_ROOT / "infrastructure" / "elk" / "docker-compose.elk.yml"
    assert compose_file.exists(), "docker-compose.elk.yml must exist"

    with open(compose_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    services = data.get("services", {})
    assert "soc-elasticsearch" in services, "soc-elasticsearch service must be defined"

    es = services["soc-elasticsearch"]
    assert "elasticsearch:8.17.3" in es["image"], "Elasticsearch must be pinned to 8.17.3"
    assert es["restart"] == "unless-stopped"

    # Verify Port Isolation: MUST NOT collide with Wazuh 9200
    ports = [str(p) for p in es.get("ports", [])]
    assert any("9201:9200" in p or "ES_PORT:-9201" in p for p in ports), \
        "Elasticsearch must be exposed on 9201 to prevent conflict with Wazuh 9200"
    assert not any("127.0.0.1:9200:9200" in p or p == "9200:9200" for p in ports), \
        "Elasticsearch must NOT bind to 9200 directly (collision with Wazuh Indexer)"

    # Verify Single-Node Discovery Environment
    env = es.get("environment", [])
    env_str = str(env)
    assert "discovery.type=single-node" in env_str, "Single-node discovery must be set"
    assert "xpack.security.enabled=true" in env_str, "X-Pack security must be enabled"

    # Verify Network Isolation
    networks = es.get("networks", [])
    assert "soc-elk-net" in networks, "Service must belong to soc-elk-net bridge"


def test_elasticsearch_yml_configuration():
    cfg_file = REPO_ROOT / "infrastructure" / "elk" / "config" / "elasticsearch.yml"
    assert cfg_file.exists(), "elasticsearch.yml must exist"

    content = cfg_file.read_text(encoding="utf-8")
    cfg = yaml.safe_load(content)

    assert cfg.get("cluster.name") == "soc-elk-cluster"
    assert cfg.get("node.name") == "soc-elasticsearch"
    assert cfg.get("discovery.type") == "single-node"
    assert cfg.get("xpack.security.enabled") is True
    assert cfg.get("network.host") == "0.0.0.0"


def test_kibana_structure_and_configuration():
    compose_file = REPO_ROOT / "infrastructure" / "elk" / "docker-compose.elk.yml"
    with open(compose_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    services = data.get("services", {})
    assert "soc-kibana" in services, "soc-kibana service must be defined"

    kib = services["soc-kibana"]
    assert "kibana:8.17.3" in kib["image"], "Kibana must be pinned to 8.17.3"
    assert kib["depends_on"]["soc-elasticsearch"]["condition"] == "service_healthy"

    # Verify Port Isolation: Port 5602 to eliminate collision with Wazuh 5601
    ports = [str(p) for p in kib.get("ports", [])]
    assert any("5602:5601" in p or "KIBANA_PORT:-5602" in p for p in ports), \
        "Kibana must be exposed on host port 5602"

    cfg_file = REPO_ROOT / "infrastructure" / "elk" / "config" / "kibana.yml"
    assert cfg_file.exists(), "kibana.yml must exist"
    cfg = yaml.safe_load(cfg_file.read_text(encoding="utf-8"))
    assert cfg.get("server.name") == "soc-kibana"
    assert cfg.get("server.port") == 5601
    assert "soc-elasticsearch:9200" in str(cfg.get("elasticsearch.hosts"))
    assert cfg.get("elasticsearch.username") == "kibana_system"


def test_env_elk_example_placeholders():
    env_example = REPO_ROOT / "infrastructure" / "elk" / ".env.elk.example"
    assert env_example.exists(), ".env.elk.example must exist"

    content = env_example.read_text(encoding="utf-8")
    assert "ELASTIC_PASSWORD=" in content
    assert "ES_PORT=9201" in content
    assert "KIBANA_PORT=5602" in content
    # Ensure no actual sensitive passwords are committed
    assert "changeme" in content.lower()


def test_elk_documentation_specifications_presence():
    elk_docs = REPO_ROOT / "docs" / "elk"
    assert elk_docs.exists(), "docs/elk directory must exist"

    required_docs = [
        "README.md",
        "01-ELK-ARCHITECTURE.md",
        "02-ELK-NETWORK-DESIGN.md",
        "03-LOG-SOURCE-INVENTORY.md",
        "04-DATA-STREAM-DESIGN.md",
        "05-ECS-MAPPING.md",
    ]

    for doc in required_docs:
        doc_path = elk_docs / doc
        assert doc_path.exists(), f"Required document {doc} must exist"
        content = doc_path.read_text(encoding="utf-8")
        assert len(content) > 500, f"Document {doc} must have substantive content"


def test_wazuh_vs_elk_port_matrix_non_interference():
    wazuh_compose = REPO_ROOT / "infrastructure" / "docker" / "docker-compose.wazuh.yml"
    elk_compose = REPO_ROOT / "infrastructure" / "elk" / "docker-compose.elk.yml"

    assert wazuh_compose.exists()
    assert elk_compose.exists()

    with open(wazuh_compose, "r", encoding="utf-8") as f:
        w_data = yaml.safe_load(f)
    with open(elk_compose, "r", encoding="utf-8") as f:
        e_data = yaml.safe_load(f)

    # Extract exposed host ports
    def extract_host_port(p_str: str) -> str:
        parts = p_str.split(":")
        if len(parts) == 3:
            return parts[1]
        elif len(parts) == 2:
            return parts[0]
        return p_str

    w_ports = [extract_host_port(str(p)) for s in w_data.get("services", {}).values() for p in s.get("ports", [])]
    e_ports = [extract_host_port(str(p)) for s in e_data.get("services", {}).values() for p in s.get("ports", [])]

    # Verify no host port overlap
    assert "9200" in w_ports, "Wazuh Indexer uses 9200"
    assert "9200" not in e_ports, "ELK must not bind host 9200"
    assert any("9201" in p for p in e_ports), "ELK must bind host 9201"


def test_logstash_structure_and_pipeline_configuration():
    compose_file = REPO_ROOT / "infrastructure" / "elk" / "docker-compose.elk.yml"
    with open(compose_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    services = data.get("services", {})
    assert "soc-logstash" in services, "soc-logstash service must be defined"

    ls = services["soc-logstash"]
    assert "logstash:8.17.3" in ls["image"], "Logstash must be pinned to 8.17.3"
    assert ls["depends_on"]["soc-elasticsearch"]["condition"] == "service_healthy"

    # Verify Ingestion Ports
    ports = [str(p) for p in ls.get("ports", [])]
    assert any("5044" in p for p in ports), "Beats port 5044 must be exposed"
    assert any("5514" in p and "udp" in p for p in ports), "Syslog UDP 5514 must be exposed"

    # Verify logstash.yml
    cfg_file = REPO_ROOT / "infrastructure" / "elk" / "config" / "logstash.yml"
    assert cfg_file.exists(), "logstash.yml must exist"
    cfg = yaml.safe_load(cfg_file.read_text(encoding="utf-8"))
    assert cfg.get("node.name") == "soc-logstash"
    assert cfg.get("queue.type") == "persisted"
    assert cfg.get("dead_letter_queue.enable") is True

    # Verify pipelines.yml
    pipelines_file = REPO_ROOT / "infrastructure" / "elk" / "config" / "pipelines.yml"
    assert pipelines_file.exists(), "pipelines.yml must exist"
    pipelines = yaml.safe_load(pipelines_file.read_text(encoding="utf-8"))
    pipeline_ids = [p["pipeline.id"] for p in pipelines]
    expected_ids = ["suricata-beats", "snort-alerts", "firewall-traffic", "wazuh-alerts"]
    for eid in expected_ids:
        assert eid in pipeline_ids, f"Pipeline {eid} must be defined in pipelines.yml"

    # Verify pipeline config files exist
    pipeline_dir = REPO_ROOT / "infrastructure" / "elk" / "pipeline"
    assert (pipeline_dir / "suricata.conf").exists()
    assert (pipeline_dir / "snort.conf").exists()
    assert (pipeline_dir / "firewall.conf").exists()
    assert (pipeline_dir / "wazuh.conf").exists()


def test_suricata_pipeline_configuration_and_ecs_mapping():
    conf_path = REPO_ROOT / "infrastructure" / "elk" / "pipeline" / "suricata.conf"
    assert conf_path.exists(), "suricata.conf must exist"

    content = conf_path.read_text(encoding="utf-8")
    assert "port => 5044" in content, "Beats input on 5044 must be configured"
    assert "logs-suricata.eve-default" in content, "Target index must be logs-suricata.eve-default"
    assert "[event][dataset]\" => \"suricata.eve\"" in content
    assert "[observer][name]\" => \"suricata\"" in content
    assert "[threat][framework]\" => \"MITRE ATT&CK\"" in content
    assert "[related][ip]" in content

    # Check verification script presence
    v_script = REPO_ROOT / "infrastructure" / "elk" / "scripts" / "verify_suricata_ingest.py"
    assert v_script.exists(), "verify_suricata_ingest.py must exist"


def test_snort_pipeline_configuration_and_ecs_mapping():
    conf_path = REPO_ROOT / "infrastructure" / "elk" / "pipeline" / "snort.conf"
    assert conf_path.exists(), "snort.conf must exist"

    content = conf_path.read_text(encoding="utf-8")
    assert "port => 5045" in content, "TCP input on 5045 must be configured"
    assert "logs-snort.alert-default" in content, "Target index must be logs-snort.alert-default"
    assert "[event][dataset]\" => \"snort.alert\"" in content
    assert "[observer][name]\" => \"snort\"" in content
    assert "[threat][framework]\" => \"MITRE ATT&CK\"" in content
    assert "[related][ip]" in content

    # Check verification script presence
    v_script = REPO_ROOT / "infrastructure" / "elk" / "scripts" / "verify_snort_ingest.py"
    assert v_script.exists(), "verify_snort_ingest.py must exist"


def test_firewall_pipeline_configuration_and_ecs_mapping():
    conf_path = REPO_ROOT / "infrastructure" / "elk" / "pipeline" / "firewall.conf"
    assert conf_path.exists(), "firewall.conf must exist"

    content = conf_path.read_text(encoding="utf-8")
    assert "port => 5514" in content, "Syslog UDP input on 5514 must be configured"
    assert "logs-firewall.traffic-default" in content, "Target index must be logs-firewall.traffic-default"
    assert "[event][dataset]\" => \"firewall.traffic\"" in content
    assert "[observer][name]\" => \"soc-gateway\"" in content
    assert "[event][module]\" => \"nftables\"" in content
    assert "[event][action]\" => \"drop\"" in content
    assert "[event][action]\" => \"forward\"" in content
    assert "[related][ip]" in content

    # Check verification script presence
    v_script = REPO_ROOT / "infrastructure" / "elk" / "scripts" / "verify_firewall_ingest.py"
    assert v_script.exists(), "verify_firewall_ingest.py must exist"


def test_wazuh_pipeline_configuration_and_ecs_mapping():
    conf_path = REPO_ROOT / "infrastructure" / "elk" / "pipeline" / "wazuh.conf"
    assert conf_path.exists(), "wazuh.conf must exist"

    content = conf_path.read_text(encoding="utf-8")
    assert "port => 5046" in content, "TCP input on 5046 must be configured"
    assert "alerts.json" in content, "File input for alerts.json must be configured"
    assert "logs-wazuh.alert-default" in content, "Target index must be logs-wazuh.alert-default"
    assert "[event][dataset]\" => \"wazuh.alert\"" in content
    assert "[observer][name]\" => \"wazuh\"" in content
    assert "[event][module]\" => \"wazuh\"" in content
    assert "[threat][framework]\" => \"MITRE ATT&CK\"" in content
    assert "[related][ip]" in content

    # Check verification script presence
    v_script = REPO_ROOT / "infrastructure" / "elk" / "scripts" / "verify_wazuh_ingest.py"
    assert v_script.exists(), "verify_wazuh_ingest.py must exist"





