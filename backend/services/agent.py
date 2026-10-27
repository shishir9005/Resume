"""
Resume Coach agent: an LLM that answers questions by calling tools in a loop.

    user question
      -> the LLM decides: answer now, or call a tool?
      -> run the tool and add its result to the conversation
      -> repeat, at most MAX_STEPS times
      -> return the final answer, the steps taken, and the guides used

Written by hand on Groq's chat API (OpenAI-compatible tool calling) rather
than with an agent framework, so every step is visible and easy to debug.
"""
import json
import logging
import re
from typing import Any, Dict, List

from backend.services.coach_tools import TOOL_SCHEMAS, CoachTools
from backend.services.groq_parser import GROQ_MODEL, _get_client
from backend.services.rag import KnowledgeBase

logger = logging.getLogger('ats_resume_scorer')

MAX_STEPS        = 6     # tool-calling rounds before the agent must answer
MAX_HISTORY      = 10    # earlier chat messages sent to the model
REQUEST_TIMEOUT  = 30    # seconds per LLM call

#the prompt asks the model not to name its tools, but it sometimes does; swap them for plain words
TOOL_NAMES_FOR_USERS = {
    'search_guides':      'the career guides',
    'get_analysis':       'your analysis',
    'get_resume_section': 'your resume',
    'check_bullet':       'the bullet check',
}

SYSTEM_PROMPT = """You are Resume Coach, an assistant inside the ATS Resume Scorer app. \
You help students improve their resume using their own analysis results and a library of career guides.

How to work:
- Before giving advice about the user's resume, call get_analysis. Call get_resume_section when you need their actual text.
- For scores, issues, and which skills are validated, use what get_analysis returns; don't recompute them yourself.
- Explain a score only with reasons the analysis or the guides actually give. Never guess at causes you can't see, such as the file's layout or fonts.
- For general advice (formatting, bullet points, skills, projects, job search in China), call search_guides and base your answer on what it returns.
- When you rewrite a bullet point, call check_bullet on your rewrite. If a check fails, fix the bullet and check it again before showing it.
- Never invent facts about the user: no made-up numbers, employers, or technologies. Only use numbers that appear in their resume. If a rewrite needs a number you don't know, use a placeholder like [X%] or [N users] and tell the user to fill it in honestly.
- Never swap in a technology the user did not list (for example PostgreSQL when they used MySQL). If the job wants a skill their resume doesn't show, tell them it is missing and ask whether they have used it.
- If the guides don't cover a question, say so briefly instead of guessing.
- Keep answers short and practical: a few sentences or a short list. When advice comes from a guide, name it, e.g. (Guide: Writing Strong Bullet Points). Only name guides that search_guides returned.
- Don't mention tool names to the user; they only see your answer.
- Only help with resumes, job applications, and careers. Politely decline anything else."""


def run_coach(
    messages: List[Dict[str, str]],
    analysis: Dict[str, Any],
    knowledge_base: KnowledgeBase,
) -> Dict[str, Any]:
    """
    messages: the chat so far, [{'role': 'user'|'assistant', 'content': str}], ending with the user's question.
    Returns {'answer': str, 'steps': [{'tool', 'args'}], 'sources': [str]}.
    """
    client = _get_client().with_options(timeout=REQUEST_TIMEOUT)
    tools = CoachTools(analysis, knowledge_base)
    steps: List[Dict[str, Any]] = []

    conversation: List[Dict[str, Any]] = [{'role': 'system', 'content': SYSTEM_PROMPT}]
    conversation += [{'role': m['role'], 'content': m['content']} for m in messages[-MAX_HISTORY:]]

    for _ in range(MAX_STEPS):
        reply = _ask_llm(client, conversation, tool_choice='auto')

        #no tool call means the model is ready to answer
        if not reply.tool_calls:
            return _result(reply.content, steps, tools.sources)

        conversation.append({
            'role': 'assistant',
            'content': reply.content or '',
            'tool_calls': [
                {
                    'id': call.id,
                    'type': 'function',
                    'function': {'name': call.function.name, 'arguments': call.function.arguments},
                }
                for call in reply.tool_calls
            ],
        })

        for call in reply.tool_calls:
            name = call.function.name
            try:
                args = json.loads(call.function.arguments or '{}')
            except json.JSONDecodeError:
                args = {}

            #log the tool name only: arguments can contain resume text
            logger.info(f'Coach step {len(steps) + 1}: {name}')
            output = tools.run(name, args)
            steps.append({'tool': name, 'args': args})

            conversation.append({
                'role': 'tool',
                'tool_call_id': call.id,
                'content': json.dumps(output, ensure_ascii=False),
            })

    #step budget used up: ask for a final answer with tools switched off
    logger.warning(f'Coach hit MAX_STEPS ({MAX_STEPS}); forcing a final answer')
    reply = _ask_llm(client, conversation, tool_choice='none')
    return _result(reply.content, steps, tools.sources)


def _ask_llm(client, conversation: List[Dict[str, Any]], tool_choice: str):
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=conversation,
        tools=TOOL_SCHEMAS,
        tool_choice=tool_choice,
        temperature=0.2,
        max_tokens=1500,
    )
    return response.choices[0].message


def _result(answer: str | None, steps: List[Dict[str, Any]], sources: List[str]) -> Dict[str, Any]:
    return {
        'answer':  _hide_tool_names(answer or '').strip() or "Sorry, I couldn't put an answer together. Please try rephrasing.",
        'steps':   steps,
        'sources': sources,
    }


def _hide_tool_names(text: str) -> str:
    for name, plain in TOOL_NAMES_FOR_USERS.items():
        #also eat surrounding `code` or **bold** markers and a trailing "()"
        text = re.sub(rf'[`*]*\b{name}\b(\(\))?[`*]*', plain, text)
    return text
