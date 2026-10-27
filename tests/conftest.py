"""
Shared test helpers. Nothing here downloads a model or calls an API, so the
whole suite runs offline in a few seconds.
"""
import hashlib

import numpy as np
import pytest


class FakeEmbedder:
    """
    Stands in for the MiniLM embedder. Each word maps to a fixed random vector,
    and a text is the average of its words, so texts that share words are
    similar and unrelated texts are close to orthogonal.
    """

    dim = 256

    def _word_vector(self, word: str) -> np.ndarray:
        seed = int(hashlib.md5(word.encode()).hexdigest()[:8], 16)
        return np.random.default_rng(seed).standard_normal(self.dim)

    def encode(self, text: str, convert_to_tensor: bool = False) -> np.ndarray:
        words = [w for w in text.lower().replace('.', ' ').replace(',', ' ').split() if w]
        if not words:
            return np.ones(self.dim, dtype=np.float32)
        return np.mean([self._word_vector(w) for w in words], axis=0).astype(np.float32)

    def encode_many(self, texts):
        return np.stack([self.encode(t) for t in texts])


@pytest.fixture
def embedder():
    return FakeEmbedder()


@pytest.fixture
def analysis():
    """A trimmed AnalysisResponse, as the frontend sends it to the coach."""
    return {
        'ATS_score': 61.5,
        'interpretation': 'Fair.',
        'component_scores': {
            'formatting': 16, 'keywords': 18, 'content': 14,
            'skill_validation': 7.5, 'ats_compatibility': 13,
        },
        'detailed_feedback': [
            {'issue_title': 'Bullet Points Lack Strong Action Verbs', 'severity_level': 'High',
             'how_to_fix': 'Start every bullet with a past-tense action verb.'},
        ],
        'skill_validation_details': {'unvalidated': ['Docker', 'Redis']},
        'jd_comparison': {'match_percentage': 48.0, 'missing_keywords': ['PostgreSQL'], 'skills_gap': []},
        'resume_sections': {
            'summary': 'CS student.',
            'skills': ['Python', 'FastAPI', 'MySQL', 'Docker', 'Redis'],
            'experience': [],
            'projects': [{
                'title': 'Campus Food Ordering App',
                'technologies': ['FastAPI', 'MySQL'],
                'description': 'Worked on the backend for 300 students. Responsible for the database.',
            }],
            'education': [],
        },
    }
