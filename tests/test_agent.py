"""
Tests for the agent loop with a fake LLM client, so no Groq calls are made.
The fake returns scripted replies in order and records what it was sent.
"""
from types import SimpleNamespace

import backend.services.agent as agent


class NoSearchKB:
    def search(self, query, k=3):
        return []


def tool_call(name, arguments='{}', call_id='call_1'):
    return SimpleNamespace(id=call_id, function=SimpleNamespace(name=name, arguments=arguments))


def reply(content=None, tool_calls=None):
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content, tool_calls=tool_calls))])


class FakeClient:
    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def with_options(self, **kwargs):
        return self

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        return self.replies.pop(0)


def run(monkeypatch, replies, analysis):
    client = FakeClient(replies)
    monkeypatch.setattr(agent, '_get_client', lambda: client)
    result = agent.run_coach([{'role': 'user', 'content': 'Why is my score low?'}], analysis, NoSearchKB())
    return result, client


def test_tool_call_then_answer(monkeypatch, analysis):
    result, client = run(monkeypatch, [
        reply(tool_calls=[tool_call('get_analysis')]),
        reply(content='Your content score is low.'),
    ], analysis)

    assert result['answer'] == 'Your content score is low.'
    assert result['steps'] == [{'tool': 'get_analysis', 'args': {}}]
    # the tool's output went back to the model as a 'tool' message
    tool_messages = [m for m in client.calls[1]['messages'] if m['role'] == 'tool']
    assert '61.5' in tool_messages[0]['content']


def test_bad_tool_arguments_do_not_crash(monkeypatch, analysis):
    result, _ = run(monkeypatch, [
        reply(tool_calls=[tool_call('get_resume_section', arguments='not json')]),
        reply(content='Done.'),
    ], analysis)
    assert result['answer'] == 'Done.'


def test_step_limit_forces_a_final_answer(monkeypatch, analysis):
    looping = [reply(tool_calls=[tool_call('get_analysis')]) for _ in range(agent.MAX_STEPS)]
    result, client = run(monkeypatch, looping + [reply(content='Final answer.')], analysis)

    assert result['answer'] == 'Final answer.'
    assert len(result['steps']) == agent.MAX_STEPS
    assert client.calls[-1]['tool_choice'] == 'none'


def test_empty_answer_gets_a_fallback(monkeypatch, analysis):
    result, _ = run(monkeypatch, [reply(content='')], analysis)
    assert result['answer'].startswith('Sorry')


def test_tool_names_are_hidden_from_users():
    text = agent._hide_tool_names('Run it through **check_bullet** and `search_guides()`.')
    assert text == 'Run it through the bullet check and the career guides.'
