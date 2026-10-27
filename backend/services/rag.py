"""
Retrieval over the career guides in backend/knowledge/ (the "R" in RAG).

Each guide is a Markdown file. It is split into chunks at its '## ' headings,
every chunk is embedded once at startup, and a query returns the chunks with
the highest cosine similarity. A few dozen chunks fit easily in memory, so a
NumPy matrix is enough; no vector database is needed at this size.
"""
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import numpy as np

from backend.services.embedder import Embedder

logger = logging.getLogger('ats_resume_scorer')

KNOWLEDGE_DIR = Path(__file__).resolve().parents[1] / 'knowledge'


@dataclass
class Chunk:
    doc_id: str    # file name without .md, e.g. 'bullet-points'
    title: str     # the guide's '# ' heading
    section: str   # the chunk's '## ' heading
    text: str

    @property
    def source(self) -> str:
        return f'{self.title} > {self.section}'


def load_chunks(knowledge_dir: Path = KNOWLEDGE_DIR) -> List[Chunk]:
    chunks = []
    for path in sorted(knowledge_dir.glob('*.md')):
        raw = path.read_text(encoding='utf-8')
        title_match = re.search(r'^# (.+)$', raw, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else path.stem

        #everything before the first '## ' is the title line, so skip it
        for part in re.split(r'^## ', raw, flags=re.MULTILINE)[1:]:
            heading, _, body = part.partition('\n')
            body = body.strip()
            if body:
                chunks.append(Chunk(path.stem, title, heading.strip(), body))
    return chunks


class KnowledgeBase:

    def __init__(self, embedder: Embedder, knowledge_dir: Path = KNOWLEDGE_DIR):
        self._embedder = embedder
        self.chunks = load_chunks(knowledge_dir)
        if not self.chunks:
            raise ValueError(f'No knowledge chunks found in {knowledge_dir}')

        #title + heading go into the embedding so short sections keep their topic
        texts = [f'{c.title}. {c.section}. {c.text}' for c in self.chunks]
        vectors = embedder.encode_many(texts)

        #normalise once, so search is a single matrix-vector product
        self._vectors = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
        logger.info(f'Knowledge base ready: {len(self.chunks)} chunks from {knowledge_dir.name}/')

    def search(self, query: str, k: int = 3, min_score: float = 0.2) -> List[Dict]:
        """Return up to k chunks most similar to the query, best first."""
        query_vec = self._embedder.encode(query)
        query_vec = query_vec / np.linalg.norm(query_vec)

        scores = self._vectors @ query_vec
        best = np.argsort(scores)[::-1][:k]

        return [
            {
                'doc_id':  self.chunks[i].doc_id,
                'source':  self.chunks[i].source,
                'text':    self.chunks[i].text,
                'score':   round(float(scores[i]), 3),
            }
            for i in best
            if scores[i] >= min_score
        ]
