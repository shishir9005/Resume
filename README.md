# ATS Resume Scorer

[![CI](https://github.com/shishir9005/Resume/actions/workflows/ci.yml/badge.svg)](https://github.com/shishir9005/Resume/actions/workflows/ci.yml)

Upload a resume, optionally paste a job description, and get a 0–100 ATS score with a breakdown, prioritized fixes, and a downloadable PDF report.

**Live demo:** https://shishir-ats-scorer.streamlit.app
(Free hosting. If the app has been idle, the first load takes about a minute while it wakes up.)

<details>
<summary><b>中文简介</b></summary>

上传简历（可选粘贴岗位描述），即可获得 0–100 的 ATS 评分、分项得分、按严重程度排序的修改建议，以及可下载的 PDF 报告。

- **五项评分：** 格式、关键词与技能、内容质量、技能验证、ATS 兼容性
- **技能验证：** 用语义相似度检查简历中列出的技能是否有项目或经历支撑
- **岗位描述匹配：** 匹配度、语义相似度、已匹配和缺失的关键词、技能差距
- **账号与历史：** 邮箱登录，分析结果保存在个人账户中，可随时删除
- **简历教练（RAG + Agent）：** 基于分析结果和求职指南知识库的对话助手。Agent 通过工具调用检索指南、读取简历、改写要点，并用评分规则校验改写内容，不编造数字或技能。检索评测：hit@3 为 96%
- **技术栈：** Streamlit、FastAPI、spaCy、MiniLM 句向量（ONNX）、Groq API（含工具调用）、Supabase、WeasyPrint

在线演示使用免费服务器：空闲后首次打开约需一分钟唤醒，在中国大陆网络下可能更慢。

</details>


## What it does

- **Example resumes.** Three one-page internship resumes (backend, AI/LLM, data analyst) on the Resources page, each scoring 88–91 here and downloadable as a Word template, plus weak vs. strong bullet examples.
- **Five-part score.** Formatting, keywords and skills, content quality, skill validation, and ATS compatibility, each on its own scale.
- **Skill validation.** Checks whether each skill listed on the resume is backed by a project or experience bullet, using semantic similarity.
- **Job description match.** Match percentage, semantic similarity, matched and missing keywords, and a skills gap list.
- **Actionable feedback.** Issues grouped by severity, with what's wrong, where it appears, how to fix it, and an example.
- **Resume Coach (RAG + agent).** A chat under your results. It reads your analysis and a library of career guides, rewrites bullets and checks them against the scoring rules, and shows each step it took and the guides it used.
- **Exports.** PDF report and plain-text summary.
- **Accounts and history.** Email sign-in; every analysis is saved to your account, and you can delete it any time.

## How the score is built

| Component | Max points |
|---|---|
| Formatting | 20 |
| Keywords & Skills | 25 |
| Content Quality | 25 |
| Skill Validation | 15 |
| ATS Compatibility | 15 |
| **Total** | **100** |

## Resume Coach: how the RAG and agent work

```
question ──► agent loop (Groq, tool calling, max 6 rounds)
               │
               ├── search_guides(query)       RAG: MiniLM embeddings + cosine search over backend/knowledge/*.md
               ├── get_analysis()             the user's scores, issues, unvalidated skills, JD gaps
               ├── get_resume_section(name)   the user's parsed summary / skills / experience / projects
               └── check_bullet(text)         scoring rules + grounding check on any rewritten bullet
               ▼
answer + steps taken + guides used
```

**Retrieval (RAG).** The knowledge base is 13 short Markdown guides plus 3 example resumes in `backend/knowledge/`. The guides cover ATS formatting, bullet points, action verbs, skills, projects, tailoring to a job description, internships in China, skills by role, and how this app's score works. Each file is split at its `##` headings (81 chunks). Every chunk is embedded once at startup with the same MiniLM model the scorer already uses, and a query is a single matrix-vector product. At this size a NumPy matrix is faster and simpler than a vector database. Code: `backend/services/rag.py`.

**Agent.** A hand-written tool-calling loop on Groq's OpenAI-compatible API, about 100 lines, with no agent framework. Each round, the model either answers or asks for tools. The backend runs them and feeds the results back. After 6 rounds it must answer. Code: `backend/services/agent.py` (loop) and `backend/services/coach_tools.py` (tools).

**Guardrails.**
- `check_bullet` fails any rewrite whose numbers or keywords don't appear in the user's resume. This forces the agent to use placeholders like `[X%]`, or to ask the user, instead of inventing results or swapping in technologies they never used.
- All tools are read-only.
- The coach declines off-topic requests.
- Each LLM call has a 30-second timeout.
- Only tool names are logged, never resume text.

**Evaluation.** `backend/evals/retrieval_eval.py` asks 27 test questions with known answers and reports hit@1, hit@3, and MRR. Current results: **hit@1 89%, hit@3 96%, MRR 0.92**. It exits non-zero if hit@3 drops below 80%, and CI runs it on every push.

```bash
python -m backend.evals.retrieval_eval
```

To add knowledge, drop a Markdown file with `##` sections into `backend/knowledge/`, add a test question for it to the eval, and restart the backend.

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

34 tests cover the scoring rules, keyword matching, the coach's tools and grounding check, chunking and search, the agent loop (with a fake LLM, so no API calls), the coach API's input validation, and the Word templates. They run offline in a few seconds. GitHub Actions runs them and the retrieval eval on every push.

## Tech stack

- **Frontend:** Streamlit
- **Backend:** FastAPI
- **NLP:** spaCy (`en_core_web_sm`) for entities and noun phrases; `all-MiniLM-L6-v2` sentence embeddings through ONNX (`fastembed`) for semantic matching
- **LLM:** Groq API, used to extract structured data (skills, experience, projects) from resume and job description text, and to run the Resume Coach agent with tool calling
- **RAG:** the same MiniLM embeddings over a Markdown knowledge base, with in-memory cosine search
- **Auth and database:** Supabase (email auth, Postgres)
- **Parsing:** pdfplumber, PyPDF2, python-docx
- **PDF reports:** Jinja2 templates rendered with WeasyPrint
- **Hosting:** Streamlit Community Cloud

## Architecture

The Streamlit app is the only thing deployed. On startup it launches the FastAPI backend in a background thread on `127.0.0.1:8000` and talks to it over HTTP, so the same code also runs as two separate services if you want that.

The embedding model runs on ONNX instead of PyTorch. That cut peak memory by several hundred MB, which is what made free hosting possible.

## Run it locally

Requires Python 3.11 or newer.

```bash
git clone https://github.com/shishir9005/Resume.git
cd Resume
python -m venv .venv
source .venv/bin/activate
pip install -r frontend/requirements.txt
```

Create a `.env` file in the project root:

```
SUPABASE_URL=...
SUPABASE_KEY=...          # the service_role key (keep private)
SUPABASE_ANON_KEY=...     # the anon (public) key
SUPABASE_JWT_SECRET=...
GROQ_API_KEY=...
```

In Supabase, create one table named `analyses` with the columns `id` (primary key), `user_id`, `filename`, `ats_score`, `keyword_match`, `missing_keywords` (JSON), `created_at`, and `analysis_result` (JSON).

Then run:

```bash
streamlit run frontend/streamlit_app.py
```

The backend starts by itself, so no second terminal is needed.

**PDF reports need system libraries.** On Linux, install the packages listed in `packages.txt`. On macOS, run `brew install pango` and, if WeasyPrint still can't find the libraries, link them into `~/lib`.

## Project structure

```
backend/
  api/          routes and auth (Supabase token verification)
  services/     parsing, scoring, JD matching, feedback, PDF export,
                and the Resume Coach (rag.py, agent.py, coach_tools.py)
  knowledge/    Markdown career guides the coach retrieves from
  evals/        retrieval evaluation for the knowledge base
  database/     Supabase history storage
  templates/    HTML templates for the PDF report
  core/         configuration and score weights
frontend/
  streamlit_app.py   entry point
  views/             landing, scorer, history, resources
  components/        results dashboard widgets
  services/          API client and Supabase auth
jupyter notebooks/   BERT fine-tuning experiment (dataset not included)
```

## Notes and limits

- Resumes are processed on the server, and their text is sent to the Groq API. Results are stored in your account's history and can be deleted from the History page.
- Accepted files: PDF and DOCX, up to 5 MB. Old `.doc` files need converting first.
- Sign-up doesn't verify email addresses. This is a demo.
- The free server is small, so a few people at once is fine and many at once may not be.

## Author

Built by [shishir9005](https://github.com/shishir9005).
