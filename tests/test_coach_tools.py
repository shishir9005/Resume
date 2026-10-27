from backend.services.coach_tools import CoachTools


class NoSearchKB:
    def search(self, query, k=3):
        return []


def tools(analysis):
    return CoachTools(analysis, NoSearchKB())


def test_weak_bullet_fails_every_quality_check(analysis):
    result = tools(analysis).check_bullet('Responsible for the database')
    assert not result['passed']
    assert not result['checks']['starts_with_action_verb']
    assert not result['checks']['has_measurable_result']
    assert not result['checks']['length_ok']


def test_strong_grounded_bullet_passes(analysis):
    result = tools(analysis).check_bullet('Designed the MySQL schema for the FastAPI backend serving 300 students')
    assert result['passed'], result['tips']


def test_invented_number_is_caught(analysis):
    # "1,000" never appears in the resume
    result = tools(analysis).check_bullet('Designed the MySQL schema for the backend, serving 1,000 daily student orders')
    assert not result['checks']['numbers_found_in_resume']
    assert not result['passed']


def test_placeholder_counts_as_a_number(analysis):
    result = tools(analysis).check_bullet('Designed the MySQL schema for the backend, cutting query time by [X%]')
    assert result['checks']['has_measurable_result']
    assert result['checks']['numbers_found_in_resume']


def test_keyword_not_in_resume_is_flagged(analysis):
    result = tools(analysis).check_bullet(
        'Designed the PostgreSQL schema for the backend, cutting query time by [X%]', keywords=['PostgreSQL'],
    )
    assert result['checks']['contains_all_keywords']
    assert not result['checks']['keywords_found_in_resume']


def test_get_analysis_summarizes_scores_and_gaps(analysis):
    summary = tools(analysis).get_analysis()
    assert summary['ats_score'] == 61.5
    assert summary['component_scores']['skill_validation'] == '7.5/15'
    assert summary['unvalidated_skills'] == ['Docker', 'Redis']
    assert summary['jd_comparison']['missing_keywords'] == ['PostgreSQL']


def test_get_resume_section(analysis):
    t = tools(analysis)
    assert t.get_resume_section('projects')['content'][0]['title'] == 'Campus Food Ordering App'
    assert t.get_resume_section('experience')['content'] is None
    assert 'error' in t.get_resume_section('hobbies')


def test_run_reports_bad_calls_as_data(analysis):
    t = tools(analysis)
    assert 'error' in t.run('delete_everything', {})
    assert 'error' in t.run('check_bullet', {'wrong_arg': 'x'})
