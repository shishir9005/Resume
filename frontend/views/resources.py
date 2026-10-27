import streamlit as st


def render():
    """Render the resources page"""
    
    st.title("📚 Resources & Tips")
    st.markdown("Learn how to optimize your resume for ATS systems")
    
    # ATS Tips
    st.markdown("## 🎯 ATS Optimization Tips")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### ✅ Do's
        - Use standard section headings
        - Include relevant keywords from job description
        - Use simple, clean formatting
        - List skills explicitly
        - Quantify achievements with numbers
        - Use standard fonts (Arial, Calibri, Times New Roman)
        - Save as PDF or DOCX
        """)
    
    with col2:
        st.markdown("""
        ### ❌ Don'ts
        - Avoid tables and text boxes
        - Don't use headers/footers for important info
        - Avoid images and graphics
        - Don't use unusual fonts
        - Avoid columns (use single column layout)
        - Don't keyword stuff
        - Avoid abbreviations without spelling out first
        """)
    
    st.markdown("---")
    
    # Common ATS Keywords
    st.markdown("## 🔑 Common ATS Keywords by Industry")
    
    tab1, tab2, tab3 = st.tabs(["💻 Tech", "💼 Business", "🎨 Creative"])
    
    with tab1:
        st.markdown("""
        **Software Development:**
        - Programming languages (Python, Java, JavaScript)
        - Frameworks (React, Django, Spring)
        - Tools (Git, Docker, Kubernetes)
        - Methodologies (Agile, Scrum, CI/CD)
        """)
    
    with tab2:
        st.markdown("""
        **Business & Management:**
        - Project management
        - Stakeholder engagement
        - Budget management
        - Strategic planning
        - Team leadership
        """)
    
    with tab3:
        st.markdown("""
        **Creative & Design:**
        - Adobe Creative Suite
        - UI/UX Design
        - Wireframing & Prototyping
        - Brand identity
        - Visual communication
        """)
    
    st.markdown("---")
    
    _render_bullet_rewrites()

    st.markdown("---")

    _render_example_resumes()


# Weak bullet -> strong bullet, following the action + task + result formula
BULLET_REWRITES = [
    ("Responsible for the database of a food ordering app.",
     "Designed a PostgreSQL schema of 11 tables with indexes on order lookups, cutting the slowest query from 900 ms to 40 ms."),
    ("Worked on the frontend of a web app.",
     "Built 8 responsive React pages with TypeScript, cutting page load time by 35%."),
    ("Helped with data cleaning.",
     "Cleaned and merged 3 datasets (120K rows) with Pandas, removing 9% duplicate records before model training."),
    ("Was responsible for testing.",
     "Wrote 85 Pytest unit tests for the payment service, raising coverage from 40% to 88%."),
    ("Made a chatbot using AI.",
     "Built a RAG chatbot over 300 pages of lecture notes, raising retrieval hit@3 from 71% to 89% on 150 test questions."),
]


def _render_bullet_rewrites() -> None:
    st.markdown("## ✍️ Weak vs. Strong Bullet Points")
    st.markdown(
        "Strong bullets follow **action + what you did + measurable result**. "
        "Start with a past-tense verb, name the tools, and add a number. "
        "Only use numbers you can explain in an interview."
    )
    for weak, strong in BULLET_REWRITES:
        c1, c2 = st.columns(2)
        c1.error(f"❌ {weak}")
        c2.success(f"✅ {strong}")


def _render_example_resumes() -> None:
    from frontend.services.resume_examples import load_examples, to_docx

    st.markdown("## 📄 Example Resumes and Templates")
    st.markdown(
        "Three one-page internship resumes for fictional students, written to pass ATS screening. "
        "Download any of them as a single-column Word template and replace the content with your own."
    )

    examples = load_examples()
    if not examples:
        st.info("Example resumes are unavailable right now.")
        return

    for tab, example in zip(st.tabs([e.label for e in examples]), examples):
        with tab:
            c1, c2 = st.columns([3, 1])
            c1.caption(f"{example.title} · fictional candidate, all details are made up")
            c2.metric("Score in this app", f"~{example.score}/100")
            st.download_button(
                "⬇️ Download as Word template (.docx)",
                data=to_docx(example),
                file_name=f"{example.slug}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key=f"download_{example.slug}",
            )
            with st.container(border=True):
                # two trailing spaces = markdown line break, so the name and contact line stay on separate lines
                body = example.body.replace("\n## ", "\n#### ")   # smaller section headings on the page
                st.markdown(body.replace("\n", "  \n"))

    st.caption(
        "Tip: what makes these score well is that every listed skill appears in a project or job bullet, "
        "and most bullets carry a number. Ask the Resume Coach to compare your resume with one of them."
    )