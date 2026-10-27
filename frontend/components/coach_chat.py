from typing import Any, Dict

import requests
import streamlit as st

from frontend.services import api_client

SUGGESTED_QUESTIONS = [
    "Why is my score low, and what should I fix first?",
    "Rewrite my weakest project bullet point.",
    "How do I validate my unvalidated skills?",
    "When should I apply for summer internships in China?",
]

TOOL_LABELS = {
    "search_guides":      "Searched the career guides",
    "get_analysis":       "Read your analysis results",
    "get_resume_section": "Read your resume",
    "check_bullet":       "Checked a rewritten bullet",
}


def _render_reply_details(steps, sources) -> None:
    """Show what the agent did (tool calls) and which guides it used."""
    if not steps and not sources:
        return
    with st.expander(f"How the coach answered ({len(steps)} step{'s' if len(steps) != 1 else ''})"):
        for i, step in enumerate(steps, start=1):
            label = TOOL_LABELS.get(step.get("tool"), step.get("tool"))
            detail = step.get("args", {}).get("query") or step.get("args", {}).get("section") or ""
            st.markdown(f"{i}. {label}" + (f": *{detail}*" if detail else ""))
        if sources:
            st.markdown("**Guides used**")
            for source in sources:
                st.markdown(f"- {source}")


def _error_message(exc: requests.RequestException) -> str:
    if isinstance(exc, requests.HTTPError) and exc.response is not None:
        try:
            detail = exc.response.json().get("detail")
        except ValueError:
            detail = None
        if isinstance(detail, str):
            return detail
        return "The coach ran into a problem. Please try again."
    if isinstance(exc, requests.Timeout):
        return "The coach took too long to answer. Please try again."
    return "Can't reach the coach right now. Please try again in a minute."


def display_resume_coach(analysis: Dict[str, Any]) -> None:
    """
    Chat with the Resume Coach agent about this analysis.
    The chat history lives in st.session_state["coach_messages"] and is
    cleared by the scorer page whenever a new resume is analyzed.
    """
    st.markdown("### 🤖 Resume Coach")
    st.caption(
        "Ask about your results. The coach reads your analysis and a library of career guides, "
        "checks any bullet it rewrites, and shows the steps it took."
    )

    access_token = st.session_state.get("access_token")
    if not access_token:
        st.info("Sign in from the sidebar to chat with the coach.")
        return

    history = st.session_state.setdefault("coach_messages", [])

    if not history:
        cols = st.columns(2)
        for i, question in enumerate(SUGGESTED_QUESTIONS):
            if cols[i % 2].button(question, key=f"coach_suggestion_{i}", use_container_width=True):
                st.session_state["coach_pending"] = question

    for message in history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant":
                _render_reply_details(message.get("steps", []), message.get("sources", []))

    question = st.chat_input("Ask the coach about your resume...", key="coach_input")
    question = question or st.session_state.pop("coach_pending", None)
    if not question:
        return

    history.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        try:
            with st.spinner("Thinking..."):
                reply = api_client.coach_chat(
                    #the backend accepts at most 30 messages of 4000 characters and only reads the last 10
                    messages=[{"role": m["role"], "content": m["content"][:4000]} for m in history[-10:]],
                    analysis=analysis,
                    access_token=access_token,
                )
        except requests.RequestException as exc:
            history.pop()   # drop the unanswered question so it can be asked again
            st.error(_error_message(exc))
            return

        st.markdown(reply["answer"])
        _render_reply_details(reply.get("steps", []), reply.get("sources", []))

    history.append({
        "role": "assistant",
        "content": reply["answer"],
        "steps": reply.get("steps", []),
        "sources": reply.get("sources", []),
    })

    # Rerun once so the suggestion buttons disappear after the first question.
    if len(history) == 2:
        st.rerun()
