"""
Tools the Resume Coach agent can call.

Each tool is a plain Python method plus a JSON schema (TOOL_SCHEMAS) that
tells the LLM what the tool does and what arguments it takes. The agent loop
in agent.py runs whichever tool the model asks for and sends the result back.
All tools are read-only: they look at the user's analysis or the guides and
never change anything.
"""
import json
import re
from typing import Any, Dict, List, Optional

from backend.services.rag import KnowledgeBase
from backend.services.scorer import ACHIEVEMENT_PATTERNS

RESUME_SECTIONS = ['summary', 'skills', 'experience', 'projects', 'education']

COMPONENT_MAX = {
    'formatting': 20, 'keywords': 25, 'content': 25,
    'skill_validation': 15, 'ats_compatibility': 15,
}

WEAK_OPENERS = (
    'responsible for', 'worked on', 'helped', 'assisted', 'involved in',
    'participated in', 'was part of', 'tasked with', 'was ', 'did ',
)

#past-tense action verbs that don't end in -ed
IRREGULAR_ACTION_VERBS = {
    'built', 'led', 'wrote', 'ran', 'won', 'made', 'cut', 'drove', 'grew',
    'taught', 'set', 'sold', 'spoke', 'began', 'brought', 'oversaw', 'rebuilt',
    'rewrote', 'undertook', 'took', 'shot', 'found', 'held', 'beat',
}

TOOL_SCHEMAS = [
    {
        'type': 'function',
        'function': {
            'name': 'search_guides',
            'description': (
                'Search the library of career guides (ATS formatting, bullet points, action verbs, '
                'skills, projects, tailoring to a job description, internships in China, skills by role, '
                'and how this app calculates its score). Returns the most relevant guide sections.'
            ),
            'parameters': {
                'type': 'object',
                'properties': {
                    'query': {'type': 'string', 'description': 'What to look up, in plain English.'},
                },
                'required': ['query'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'get_analysis',
            'description': (
                "Get the user's ATS analysis: overall score, the five component scores, the main issues "
                'found, unvalidated skills, and the job description comparison if they provided one.'
            ),
            'parameters': {'type': 'object', 'properties': {}},
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'get_resume_section',
            'description': "Get the text of one section of the user's resume, as parsed from their file.",
            'parameters': {
                'type': 'object',
                'properties': {
                    'section': {'type': 'string', 'enum': RESUME_SECTIONS},
                },
                'required': ['section'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'check_bullet',
            'description': (
                'Check one resume bullet point with the same rules the ATS score uses: starts with a '
                'past-tense action verb, contains a measurable result, has a sensible length, and '
                'includes any target keywords. It also checks that every number and keyword already '
                "appears in the user's resume, so nothing is invented. Use it to verify every bullet you rewrite."
            ),
            'parameters': {
                'type': 'object',
                'properties': {
                    'bullet':   {'type': 'string', 'description': 'The bullet point text.'},
                    'keywords': {
                        'type': 'array', 'items': {'type': 'string'},
                        'description': 'Optional keywords the bullet should contain, e.g. from the job description.',
                    },
                },
                'required': ['bullet'],
            },
        },
    },
]


class CoachTools:

    def __init__(self, analysis: Dict[str, Any], knowledge_base: KnowledgeBase):
        self.analysis = analysis
        self.kb = knowledge_base
        self.sources: List[str] = []   # guide sections retrieved during this chat turn

    def run(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch a tool call from the model. Errors go back to the model as data, not exceptions."""
        tool = {
            'search_guides':      self.search_guides,
            'get_analysis':       self.get_analysis,
            'get_resume_section': self.get_resume_section,
            'check_bullet':       self.check_bullet,
        }.get(name)
        if tool is None:
            return {'error': f'Unknown tool: {name}'}
        try:
            return tool(**args)
        except TypeError as exc:
            return {'error': f'Bad arguments for {name}: {exc}'}

    def search_guides(self, query: str) -> Dict[str, Any]:
        results = self.kb.search(query, k=3)
        if not results:
            return {'results': [], 'note': 'No guide covers this topic.'}

        for r in results:
            if r['source'] not in self.sources:
                self.sources.append(r['source'])
        return {'results': [{'source': r['source'], 'text': r['text']} for r in results]}

    def get_analysis(self) -> Dict[str, Any]:
        a = self.analysis
        scores = a.get('component_scores') or {}
        jd = a.get('jd_comparison') or a.get('jd_match_analysis')

        return {
            'ats_score':      a.get('ATS_score', a.get('ats_score')),
            'interpretation': a.get('interpretation', ''),
            'component_scores': {
                name: f'{scores.get(name, 0)}/{max_pts}' for name, max_pts in COMPONENT_MAX.items()
            },
            'issues': [
                {
                    'title':      issue.get('issue_title'),
                    'severity':   issue.get('severity_level'),
                    'how_to_fix': issue.get('how_to_fix'),
                }
                for issue in (a.get('detailed_feedback') or [])[:8]
            ],
            'unvalidated_skills': (a.get('skill_validation_details') or {}).get('unvalidated', [])[:15],
            'jd_comparison': {
                'match_percentage': jd.get('match_percentage'),
                'missing_keywords': jd.get('missing_keywords', [])[:15],
                'skills_gap':       jd.get('skills_gap', [])[:10],
            } if jd else None,
        }

    def get_resume_section(self, section: str) -> Dict[str, Any]:
        if section not in RESUME_SECTIONS:
            return {'error': f'section must be one of {RESUME_SECTIONS}'}

        content = (self.analysis.get('resume_sections') or {}).get(section)
        if not content:
            return {'section': section, 'content': None, 'note': 'This section is empty or was not found.'}
        return {'section': section, 'content': content}

    def check_bullet(self, bullet: str, keywords: Optional[List[str]] = None) -> Dict[str, Any]:
        text = bullet.strip().lstrip('•-*◦ ').strip()
        lower = text.lower()
        first_word = re.sub(r'[^a-z]', '', lower.split()[0]) if text else ''
        word_count = len(text.split())

        weak_opener = lower.startswith(WEAK_OPENERS)
        action_verb = not weak_opener and (first_word.endswith('ed') or first_word in IRREGULAR_ACTION_VERBS)
        counted_metric = any(re.search(p, text, re.IGNORECASE) for p in ACHIEVEMENT_PATTERNS)
        #a placeholder like [X%] counts, so the agent never has to invent a number to pass
        has_number = bool(re.search(r'\d|\[[^\]]+\]', text))
        missing_keywords = [k for k in (keywords or []) if k.lower() not in lower]

        #grounding: anything the rewrite claims must already be somewhere in the user's resume
        resume_text = self._resume_text()
        invented_numbers = [n for n in re.findall(r'\d[\d,.]*\d|\d', text) if n not in resume_text]
        unbacked_keywords = [k for k in (keywords or []) if k.lower() not in resume_text]

        checks = {
            'starts_with_action_verb':      action_verb,
            'has_measurable_result':        has_number,
            'length_ok':                    8 <= word_count <= 30,
            'contains_all_keywords':        not missing_keywords,
            'numbers_found_in_resume':      not invented_numbers,
            'keywords_found_in_resume':     not unbacked_keywords,
        }

        tips = []
        if weak_opener:
            tips.append('Replace the weak opener (e.g. "Responsible for", "Worked on") with an action verb.')
        elif not action_verb:
            tips.append('Start with a past-tense action verb such as Built, Designed, or Reduced.')
        if not has_number:
            tips.append('Add a number: a percentage, a count, time saved, or scale. Use a placeholder like [X%] if unknown.')
        elif not counted_metric:
            tips.append('A percentage, money amount, or "N users/projects/hours" counts toward the content score.')
        if word_count < 8:
            tips.append(f'Too short ({word_count} words); add how you did it or what changed.')
        elif word_count > 30:
            tips.append(f'Too long ({word_count} words); keep it to one or two lines.')
        if missing_keywords:
            tips.append(f'Missing keywords: {", ".join(missing_keywords)}.')
        if invented_numbers:
            tips.append(
                f'These numbers are not in the resume: {", ".join(invented_numbers)}. '
                'Replace them with placeholders like [X%] for the user to fill in.'
            )
        if unbacked_keywords:
            tips.append(
                f'The resume never mentions: {", ".join(unbacked_keywords)}. Do not claim them; '
                'ask the user whether they have actually used them.'
            )

        return {
            'bullet':     text,
            'passed':     all(checks.values()),
            'checks':     checks,
            'word_count': word_count,
            'tips':       tips,
        }

    def _resume_text(self) -> str:
        sections = self.analysis.get('resume_sections') or {}
        return json.dumps(sections, ensure_ascii=False).lower()
