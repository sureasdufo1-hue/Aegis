import hashlib
import re
from pathlib import Path

from pydantic import BaseModel, Field


class KnowledgeChunk(BaseModel):
    chunk_id: str
    document_title: str
    file_path: str
    content: str
    sha256: str
    keywords: list[str] = Field(default_factory=list)


class KnowledgeStore:
    """
    RAG Knowledge Store for SOC Playbooks and Detection Engineering Documents.
    Parses, chunks, hashes, and indexes Markdown playbooks.
    """

    def __init__(self, playbooks_dir: Path | None = None, docs_dir: Path | None = None):
        self.playbooks_dir = playbooks_dir or Path("playbooks")
        self.docs_dir = docs_dir or Path("docs/06-detection")
        self.chunks: list[KnowledgeChunk] = []
        self._load_and_index()

    def _load_and_index(self) -> None:
        targets = []
        if self.playbooks_dir.exists():
            targets.extend(list(self.playbooks_dir.glob("*.md")))
        if self.docs_dir.exists():
            targets.extend(list(self.docs_dir.glob("*.md")))

        for file_path in targets:
            try:
                text = file_path.read_text(encoding="utf-8")
                file_sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
                
                # Extract title from first # header
                title_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
                title = title_match.group(1).strip() if title_match else file_path.stem

                # Split by ## sections
                sections = re.split(r"\n(?=##\s+)", text)
                for idx, sec in enumerate(sections):
                    clean_sec = sec.strip()
                    if not clean_sec:
                        continue
                    
                    # Keywords extraction
                    words = re.findall(r"\b[A-Za-z0-9_-]{3,}\b", clean_sec.lower())
                    
                    chunk = KnowledgeChunk(
                        chunk_id=f"{file_path.stem}-sec{idx+1}",
                        document_title=title,
                        file_path=str(file_path).replace("\\", "/"),
                        content=clean_sec,
                        sha256=file_sha,
                        keywords=list(set(words)),
                    )
                    self.chunks.append(chunk)

            except Exception:
                # Log non-fatal error reading document
                pass

    def search(self, query: str, top_k: int = 3) -> list[tuple[KnowledgeChunk, float]]:
        """
        Hybrid keyword-overlap relevance search.
        Returns top_k chunks with normalized relevance score [0.0 - 1.0].
        """
        query_words = set(re.findall(r"\b[A-Za-z0-9_-]{3,}\b", query.lower()))
        if not query_words or not self.chunks:
            return []

        scored: list[tuple[KnowledgeChunk, float]] = []
        for chunk in self.chunks:
            intersection = query_words.intersection(set(chunk.keywords))
            if intersection:
                score = len(intersection) / len(query_words)
                scored.append((chunk, score))

        # Sort descending by score
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]
