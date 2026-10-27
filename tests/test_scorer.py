from backend.services.scorer import (
    _calc_content_score,
    calculate_overall_score,
    is_spoken_language,
    validate_skills_with_projects,
)
from backend.utils.util import get_default_grammar_results, get_default_location_results

PROJECTS = [{
    'title': 'Campus Canteen API',
    'description': 'Built a REST API for 600 students',
    'technologies': ['Python', 'FastAPI', 'PostgreSQL'],
}]


def test_tech_stack_counts_as_skill_evidence(embedder):
    result = validate_skills_with_projects(['Python', 'FastAPI', 'PostgreSQL'], PROJECTS, [], embedder)
    assert {v['skill'] for v in result['validated_skills']} == {'Python', 'FastAPI', 'PostgreSQL'}
    assert result['unvalidated_skills'] == []


def test_tech_stack_given_as_one_string(embedder):
    projects = [{'title': 'Dashboard', 'description': 'Weather charts', 'technologies': 'JavaScript, React'}]
    result = validate_skills_with_projects(['React'], projects, [], embedder)
    assert [v['skill'] for v in result['validated_skills']] == ['React']


def test_skill_without_evidence_is_unvalidated(embedder):
    result = validate_skills_with_projects(['Kubernetes'], PROJECTS, [], embedder)
    assert result['unvalidated_skills'] == ['Kubernetes']
    assert result['validation_score'] == 0


def test_experience_counts_as_evidence(embedder):
    experience = [{'job_title': 'Data Intern', 'company': 'Shop', 'description': 'Automated reports with SQL'}]
    result = validate_skills_with_projects(['SQL'], [], experience, embedder)
    assert result['validated_skills'][0]['projects'] == ['Experience Section']


def test_spoken_languages_are_not_validated(embedder):
    skills = ['Python', 'Chinese (native)', 'English (CET-6)', 'HSK 4']
    result = validate_skills_with_projects(skills, PROJECTS, [], embedder)
    # only Python is a real skill here, and it is validated, so the score is full
    assert result['validation_percentage'] == 1.0


def test_is_spoken_language():
    for language in ['Chinese (native)', 'English - fluent', 'Hindi', 'IELTS 7.5', 'HSK 5']:
        assert is_spoken_language(language)
    for skill in ['Python', 'Go', 'Java', 'Machine Learning', 'SQL']:
        assert not is_spoken_language(skill)


def test_content_score_ignores_unchecked_grammar():
    grammar = get_default_grammar_results()  # grammar checking is unavailable
    verbs = ['built'] * 15
    metrics = ' '.join(['cut costs by 10%'] * 10)
    assert _calc_content_score(metrics, verbs, grammar) == 25.0
    # no verbs and no numbers must not earn free grammar points
    assert _calc_content_score('', [], grammar) == 0.0


def test_overall_score_stays_in_range(embedder):
    parsed = {'experience': [], 'education': [], 'skills': [], 'projects': [], 'professional_summary': ''}
    empty = calculate_overall_score(
        text='', parsed_resume=parsed, skills=[], keywords=[], action_verbs=[],
        skill_validation_results=validate_skills_with_projects([], [], [], embedder),
        grammar_results=get_default_grammar_results(),
        location_results=get_default_location_results(),
    )
    assert 0 <= empty['overall_score'] <= 100
    assert 'perfect_grammar' not in empty['bonuses']
