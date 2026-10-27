from backend.utils.matching import fuzzy_match_keywords, normalize_skill


def test_aliases_normalize_to_one_name():
    assert normalize_skill('ReactJS') == 'react'
    assert normalize_skill(' Postgres ') == 'postgresql'
    assert normalize_skill('k8s') == 'kubernetes'


def test_alias_and_fuzzy_matches_count():
    result = fuzzy_match_keywords(['Postgres', 'React.js', 'Pyhton'], ['PostgreSQL', 'React', 'Python', 'Docker'])
    assert set(result['matched']) == {'PostgreSQL', 'React', 'Python'}
    assert result['missing'] == ['Docker']


def test_no_resume_keywords_means_everything_missing():
    result = fuzzy_match_keywords([], ['SQL', 'Git'])
    assert result['matched'] == []
    assert set(result['missing']) == {'SQL', 'Git'}
