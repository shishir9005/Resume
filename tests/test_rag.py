from backend.services.rag import KNOWLEDGE_DIR, KnowledgeBase, load_chunks


def test_chunks_split_at_level_two_headings(tmp_path):
    (tmp_path / 'guide.md').write_text(
        '# My Guide\n\nIntro text that is skipped.\n\n## First\nAlpha text.\n\n## Second\nBeta text.\n'
    )
    chunks = load_chunks(tmp_path)
    assert [(c.title, c.section, c.text) for c in chunks] == [
        ('My Guide', 'First', 'Alpha text.'),
        ('My Guide', 'Second', 'Beta text.'),
    ]
    assert chunks[0].source == 'My Guide > First'


def test_search_returns_the_most_similar_chunk(tmp_path, embedder):
    (tmp_path / 'a.md').write_text('# Verbs\n\n## Weak openers\nreplace responsible for with built designed\n')
    (tmp_path / 'b.md').write_text('# China\n\n## Seasons\nsummer internship applications open in spring\n')
    kb = KnowledgeBase(embedder, tmp_path)

    results = kb.search('when do summer internship applications open', k=1, min_score=0.0)
    assert results[0]['doc_id'] == 'b'


def test_real_knowledge_base_loads():
    chunks = load_chunks(KNOWLEDGE_DIR)
    doc_ids = {c.doc_id for c in chunks}
    assert len(chunks) > 50
    assert {'bullet-points', 'china-internships', 'example-resume-backend'} <= doc_ids
    assert all(c.text.strip() for c in chunks)
