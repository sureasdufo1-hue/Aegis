from analyzer.ai.rag.knowledge_store import KnowledgeStore
from analyzer.ai.rag.retriever import KnowledgeRetriever


def test_rag_knowledge_store_indexing_and_search():
    store = KnowledgeStore()
    assert len(store.chunks) > 0, "Expected playbooks to be parsed and indexed"

    # Search for port scan playbook
    results = store.search("port scan reconnaissance nmap null scan", top_k=3)
    assert len(results) > 0
    top_chunk, score = results[0]
    assert score > 0.0
    all_matched_paths = [c[0].file_path for c in results]
    assert any("01_port_scan" in p or "06-detection" in p for p in all_matched_paths)


def test_rag_retriever_for_c2_incident():
    retriever = KnowledgeRetriever()
    context, citations = retriever.retrieve_for_incident(
        signatures=["SOC-MALWARE: Interactive Reverse Shell Session Established"],
        attack_stages=["3. Command & Control / Execution"],
        top_k=3,
    )

    assert len(citations) > 0
    assert citations[0].relevance_score > 0.0
    all_citation_paths = [c.file_path for c in citations]
    assert any("04_malware_c2" in p or "06-detection" in p for p in all_citation_paths)
    assert "Playbook" in context
