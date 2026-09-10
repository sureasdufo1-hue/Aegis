from analyzer.ai.rag.knowledge_store import KnowledgeStore
from analyzer.ai.schemas.analysis import KnowledgeCitation


class KnowledgeRetriever:
    """
    RAG Retriever for SOC AI Copilot.
    Extracts relevant playbook chunks based on incident signatures and attack stages,
    and formats them with source citations.
    """

    def __init__(self, store: KnowledgeStore | None = None):
        self.store = store or KnowledgeStore()

    def retrieve_for_incident(
        self,
        signatures: list[str],
        attack_stages: list[str],
        top_k: int = 2,
        max_chars_per_chunk: int = 800,
    ) -> tuple[str, list[KnowledgeCitation]]:
        """
        Builds query from signatures and stages, retrieves matching chunks,
        and produces bounded prompt context conforming to 8K token budget guidelines.
        """
        query = f"{' '.join(signatures)} {' '.join(attack_stages)}"
        results = self.store.search(query, top_k=top_k)

        if not results:
            return "No matching SOC playbooks found for this incident.", []

        context_lines = []
        citations: list[KnowledgeCitation] = []

        for chunk, score in results:
            content_text = chunk.content.strip()
            if len(content_text) > max_chars_per_chunk:
                content_text = content_text[:max_chars_per_chunk] + "\n[...Playbook excerpt bounded for context budget...]"

            context_lines.append(
                f"--- Playbook: {chunk.document_title} (ID: {chunk.chunk_id}, File: {chunk.file_path}) ---\n"
                f"{content_text}\n"
            )
            citations.append(
                KnowledgeCitation(
                    document_title=chunk.document_title,
                    chunk_id=chunk.chunk_id,
                    file_path=chunk.file_path,
                    relevance_score=round(score, 3),
                    key_takeaway=chunk.content[:200].replace("\n", " ").strip() + "...",
                )
            )

        return "\n".join(context_lines), citations
