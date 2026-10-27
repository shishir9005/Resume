"""
Retrieval evaluation for the Resume Coach knowledge base.

Each test question names the guide that should answer it. The script reports
hit@1 and hit@3 (did the right guide appear in the top 1 / top 3 results?)
and the mean reciprocal rank. Run it after editing guides or changing the
embedding model, to check retrieval did not get worse.

    python -m backend.evals.retrieval_eval
"""
import sys

from backend.core.config import SENTENCE_TRANSFORMER_MODEL
from backend.services.embedder import Embedder
from backend.services.rag import KnowledgeBase

# (question, doc_id of the guide that should answer it)
TEST_SET = [
    ("Can the ATS read my two-column resume template?",                 "ats-formatting"),
    ("Should I put my home address on my resume?",                      "ats-formatting"),
    ("How do I add numbers to my bullet points?",                       "bullet-points"),
    ("Rewrite 'worked on the frontend' to sound stronger",             "bullet-points"),
    ("What can I say instead of 'responsible for'?",                    "action-verbs"),
    ("Good verbs for data analysis work",                               "action-verbs"),
    ("Some of my skills are unvalidated, how do I fix that?",           "skills-section"),
    ("Should I list soft skills like teamwork?",                        "skills-section"),
    ("What should a project entry on my resume include?",               "projects-section"),
    ("Which projects should I put on my resume?",                       "projects-section"),
    ("How do I add missing keywords from the job description?",         "tailoring-to-jd"),
    ("How do I customize my resume for a specific job posting?",        "tailoring-to-jd"),
    ("How long should my professional summary be?",                     "summary-section"),
    ("Should I include my GPA and coursework?",                         "internship-resumes"),
    ("I have no work experience, what should I put on my resume?",      "internship-resumes"),
    ("When do Chinese tech companies open summer internship applications?", "china-internships"),
    ("Which websites list internships in China?",                       "china-internships"),
    ("What skills does a backend engineering intern need?",             "role-skills-software"),
    ("What do recruiters want for a frontend developer internship?",    "role-skills-software"),
    ("What should I learn for an LLM or RAG engineer internship?",      "role-skills-data-ai"),
    ("Skills needed for a data analyst intern",                         "role-skills-data-ai"),
    ("Is it okay to repeat keywords many times?",                       "common-mistakes"),
    ("Why is my content quality score low?",                            "ats-score-explained"),
    ("Why did I get a penalty for missing job description keywords?",   "ats-score-explained"),
    ("Show me an example resume for a backend engineering internship",  "example-resume-backend"),
    ("What does a good AI or LLM project section look like on a resume?", "example-resume-ai"),
    ("Sample data analyst intern resume with SQL and Tableau",          "example-resume-data"),
]


def evaluate(kb: KnowledgeBase, k: int = 3) -> dict:
    hits_at_1 = hits_at_k = 0
    reciprocal_ranks = []
    misses = []

    for question, expected in TEST_SET:
        results = kb.search(question, k=k, min_score=0.0)
        ranked_docs = [r['doc_id'] for r in results]

        if ranked_docs[:1] == [expected]:
            hits_at_1 += 1
        if expected in ranked_docs:
            hits_at_k += 1
            reciprocal_ranks.append(1 / (ranked_docs.index(expected) + 1))
        else:
            reciprocal_ranks.append(0.0)
            misses.append((question, expected, ranked_docs))

    n = len(TEST_SET)
    return {
        'questions': n,
        'hit@1':     hits_at_1 / n,
        f'hit@{k}':  hits_at_k / n,
        'mrr':       sum(reciprocal_ranks) / n,
        'misses':    misses,
    }


if __name__ == '__main__':
    kb = KnowledgeBase(Embedder(SENTENCE_TRANSFORMER_MODEL or 'all-MiniLM-L6-v2'))
    report = evaluate(kb)

    print(f"Chunks: {len(kb.chunks)}   Questions: {report['questions']}")
    print(f"hit@1: {report['hit@1']:.0%}   hit@3: {report['hit@3']:.0%}   MRR: {report['mrr']:.2f}")
    for question, expected, got in report['misses']:
        print(f"  MISS  {question!r}\n        expected {expected}, got {got}")

    #non-zero exit lets CI fail the build if retrieval quality drops
    sys.exit(0 if report['hit@3'] >= 0.8 else 1)
