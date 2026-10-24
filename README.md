<div align="center">

# ⚡ SourceSpark

### Evidence-Backed Content Planning & Grounded Campaign Generator

*Turn complex reports, PDFs, spreadsheets, and notes into strictly grounded, citation-backed weekly editorial schedules and strategic campaigns with multi-model fallback.*

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Web%20App-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Google Gemini](https://img.shields.io/badge/Google_Gemini-3.6%20%7C%203.8%20Flash-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev/)
[![Groq](https://img.shields.io/badge/Groq-GPT--OSS%20120B-F55036?style=for-the-badge)](https://groq.com/)
[![Pydantic](https://img.shields.io/badge/Pydantic-v2-E92063?style=for-the-badge&logo=pydantic&logoColor=white)](https://docs.pydantic.dev/)
[![Pytest](https://img.shields.io/badge/Tests-259%20Passed-brightgreen?style=for-the-badge&logo=pytest&logoColor=white)](tests/)

**[Overview](#-overview) · [Features](#-features) · [How It Works](#-how-it-works) · [Architecture](#-architecture) · [Planning Modes](#-planning-modes) · [Provider Configuration](#-provider-configuration) · [Installation](#-installation) · [Usage](#-usage) · [Maintainer](#-maintainer)**

</div>

---

## ✨ Overview

**SourceSpark** is a production-grade, local Streamlit application that transforms dense organizational documents—such as sustainability audits, internal reports, policy guides, and research spreadsheets—into structured, evidence-backed communication campaigns and weekly editorial schedules.

Instead of generic AI brainstorming that hallucinates facts or invents unverified figures, SourceSpark enforces **strict documentary grounding**. Every proposed topic idea is tied directly to an uploaded source document, complete with page or paragraph locations and verifiable text excerpts. Built-in deterministic verification checks numeric claims, scope, and quote fidelity locally—without burning extra model tokens or mutating original texts.

With an automated **three-tier LLM failover chain** (Gemini 3.6 Flash &rarr; Groq GPT-OSS 120B &rarr; Gemini 3.8 Flash), portable atomic workspace serialization, and one-click exports to Markdown and CSV, SourceSpark delivers an end-to-end editorial workspace for teams that value accuracy and accountability.

| 📁 Ingest | 🔍 Validate | 🧠 Generate | 📋 Output |
|:---:|:---:|:---:|:---:|
| PDF, DOCX, XLSX, and CSV documents with SHA-256 fingerprinting | Local quote, location, and numeric checks without extra AI calls | 3-tier resilient chain: Gemini 3.6 Flash, Groq, and Gemini 3.8 Flash | Grounded topic library, scheduled weekly/campaign calendars, Markdown, CSV, & workspaces |

---

## 🚀 Features

- 📂 **Multi-Format Ingestion**: Ingest PDF (via PyMuPDF), Word (`.docx`), Excel (`.xlsx`), and CSV files with SHA-256 content fingerprinting, duplicate detection, and file-level warning trackers.
- 🎯 **Strict Documentary Grounding**: Every candidate topic requires verifiable evidence citations matching exact canonical text passages across pages, paragraphs, or table rows.
- 🛡️ **Zero-AI Advisory Review**: Fast, deterministic local validation verifies excerpt occurrence, typographic quote variations, ligatures, soft hyphens, and numeric figures. Visual tags (green check / red review alert) give instant feedback without discarding readable ideas.
- 🔁 **3-Tier Resilient Provider Chain**:
  - **Tier 1 (Primary)**: Google Gemini 3.6 Flash (`gemini-3.6-flash`).
  - **Tier 2 (Operational Failover)**: Groq-hosted open model (`openai/gpt-oss-120b`) via a zero-dependency standard-library HTTP client.
  - **Tier 3 (Reserve)**: Google Gemini 3.8 Flash (`gemini-3.8-flash`).
- 📅 **Dual Strategic Planning Modes**:
  - **Weekly Plan**: 5-day (work week) or 7-day calendar schedules with start-date anchoring and sequential day assignments.
  - **Campaign Plan**: Target-based topic batches (up to 10 ideas per batch) aiming for a specific editorial quota.
- 🗃️ **Curated Topic Library**: Interactive management—select topics for your active plan, exclude unwanted angles (which future generation rounds remember and avoid), restore excluded ideas, and reorder slots.
- 🔒 **Explicit Finalization Lifecycle**: Clear boundary between draft exploration, review readiness, and formal finalization with shortfall acknowledgements and locked editing.
- 💾 **Portable Transactional Workspaces**: Export and resume entire working sessions through versioned `.workspace.json` snapshots. Strict Pydantic v2 graph validation protects against corrupt imports without storing API keys or heavy binary uploads.
- 📊 **Neutralized Multi-Format Export**: One-click export to standalone **Markdown** reports or spreadsheet-safe **CSV** files with UTF-8 BOM encoding and formula injection mitigation (`=`, `+`, `-`, `@`).
- 🧪 **Comprehensive Test Suite**: **259 automated unit and integration tests** verifying all ingestion parsers, planning rules, prompt builders, schema constraints, and export formats.

---

## 🔄 How It Works

```text
Upload Documents (PDF, DOCX, XLSX, CSV)
        │
        ▼
Extract Canonical Text, Tables & Locations (SHA-256 Fingerprinted)
        │
        ▼
Context & Request Assembly (Guarded 400k Character Limit)
        │
        ▼
Multi-Tier Resilient Provider Chain
        │
        ├── 1. Primary: Google Gemini 3.6 Flash
        │      │ (operational failover)
        ├── 2. Fallback: Groq (GPT-OSS 120B)
        │      │ (operational failover)
        └── 3. Reserve: Google Gemini 3.8 Flash
        │
        ▼
Deterministic Local Advisory & Evidence Verification
(Quote Matching, Location Checks, Numeric Consistency)
        │
        ▼
Interactive Topic Library (Select / Exclude / Reorder)
        │
        ▼
Weekly or Campaign Plan Scheduling & Formal Finalization
        │
        ├── 📄 Standalone Markdown Planning Report (.md)
        ├── 📊 Spreadsheet-Ready Sanitized CSV (.csv)
        └── 💾 Portable Working Workspace Snapshot (.workspace.json)
```

---

## 🏗️ Architecture

SourceSpark follows a clean, layered architecture separating user interfaces, domain models, document extraction, workflow services, and external provider clients.

```text
SourceSpark/
├── web_app/
│   ├── app.py                      # Streamlit application entry point & session initialization
│   └── views.py                    # Multi-screen reactive views (Setup, Sources, Topics, Finish)
├── config/
│   └── settings.py                 # Central environment configuration, bounds, and limits
├── documents/
│   ├── file_router.py              # File identification, SHA-256 fingerprinting, parser routing
│   ├── extraction.py               # Shared extraction results, canonical blocks, and safety guards
│   ├── pdf_parser.py               # Selectable page text & partial-rendering warnings (PyMuPDF)
│   ├── docx_parser.py              # Paragraph and table extraction in sequential reading order
│   ├── tabular_parser.py           # CSV/Excel parsing, shape bounds, and summary statistics
│   └── context_builder.py          # Assembled evidence context with strict size bounds
├── ai/
│   ├── provider_chain.py           # 3-tier lazy failover orchestration (Gemini -> Groq -> Gemini)
│   ├── gemini_client.py            # Google GenAI client with schema adaptation & retries
│   ├── groq_client.py              # Standard-library HTTPS client for Groq GPT-OSS 120B
│   ├── response_validator.py       # Local quote matching, location validation, and numeric checks
│   └── topic_generator.py          # Generation coordinator connecting prompts, providers, and validation
├── prompts/
│   ├── builder.py                  # Prompt assembly with briefs, exclusions, and capacity constraints
│   ├── grounding_rules.txt         # Documentary grounding and evidence extraction instructions
│   └── topic_request.txt           # Topic generation task instructions and output schema
├── models/
│   ├── topic.py                    # EvidenceReference, TopicCandidate, and TopicIdea Pydantic models
│   ├── plan.py                     # PlanMode, PlanStatus, target settings, and weekday slots
│   ├── workspace.py                # DocumentRecord, Workspace state, and relationship integrity
│   └── generation_result.py        # Candidate batch container and sufficiency explanation
├── workflow/
│   ├── state_manager.py            # Atomic workspace commits, busy locks, and reset safety
│   ├── plan_manager.py             # Selection, exclusions, slot allocation, and finalization rules
│   ├── topic_pool.py               # Topic deduplication, angle similarity, and library acceptance
│   └── planning_service.py         # End-to-end orchestration of ingestion, generation, and updates
├── exports/
│   ├── markdown_exporter.py        # Standalone Markdown report generation with evidence citations
│   └── csv_exporter.py             # Formula-neutralized CSV export with UTF-8 BOM
├── storage/
│   └── workspace_store.py          # Version-1 JSON workspace serialization and cryptographic verification
├── sample_docs/                    # Fictional documents for testing (PDF, DOCX, XLSX, CSV)
├── tests/                          # 259 unit and integration tests with deterministic mocks
├── docs/                           # In-depth architectural guides, data flows, and specifications
└── requirements.txt                # Production application dependencies
```

---

## 📋 Planning Modes & Lifecycle

SourceSpark supports two distinct editorial strategies, each tailored to specific operational requirements:

### 1. Weekly Planning Mode
- **Schedules**: Configurable for a **5-day work week** (Monday–Friday) or a **7-day full week** (Monday–Sunday).
- **Date Calculation**: Anchored to a specified **Start Date**, automatically calculating dates and assigning weekday names to topic slots.
- **Hole Handling**: Preserves deliberate empty days if the user chooses not to schedule an idea for a specific day.

### 2. Campaign Planning Mode
- **Quota-Driven**: Configured with a target topic count (e.g., 10, 15, or 25 ideas).
- **Batch Generation**: Generates ideas in iterative batches of up to **10 topics per round** until the campaign goal is achieved.
- **Continuous Expansion**: Additional batches can be generated at any time while preserving existing accepted topics.

### 🔄 The Plan Lifecycle
```text
[ DRAFT ] ────────► [ READY FOR REVIEW ] ────────► [ FINALIZED ]
    ▲                                                     │
    └──────────────── Reopen for Editing ─────────────────┘
```
1. **Draft**: Initial configuration where topics are generated, selected, excluded, and organized.
2. **Ready for Review**: The target capacity is satisfied, enabling review and finalization controls.
3. **Finalized**: Locks the plan against accidental modifications, generating a formal timestamp and enabling one-click exports.
4. **Reopened for Editing**: Explicitly clears finalization metadata to permit adjustments, ensuring exported reports always reflect authoritative, finalized selections.

---

## 🧠 Provider Configuration

SourceSpark orchestrates a resilient fallback chain designed to handle provider rate limits, network timeouts, and model availability issues seamlessly:

| Setting | Default | Purpose |
|---|---|---|
| `GEMINI_API_KEY` | — | API key for Google Gemini models. |
| `GEMINI_MODEL` | `gemini-3.6-flash` | **Primary model** for topic generation and structured extraction. |
| `GEMINI_FALLBACK_MODEL` | `gemini-3.8-flash` | **Reserve model** used if both primary Gemini and Groq failover fail. |
| `GROQ_API_KEY` | — | API key for Groq Cloud. |
| `GROQ_MODEL` | `openai/gpt-oss-120b` | **Operational fallback model** triggered on recognized Gemini errors. |
| `MAX_BATCH_TOPICS` | `10` | Maximum topic candidates generated in a single request. |
| `MAX_FILE_BYTES` | `10 MiB` | Maximum upload size per individual document. |
| `MAX_CAMPAIGN_BYTES` | `50 MiB` | Combined upload size ceiling across all active documents. |
| `MAX_DOCUMENTS` | `20` | Maximum number of active documents per workspace. |
| `MAX_CONTEXT_CHARACTERS` | `400,000` | Safety context ceiling to prevent silent evidence truncation. |
| `API_TIMEOUT_SECONDS` | `60` | Network request timeout per provider call. |
| `MAX_WORKSPACE_BYTES` | `20 MiB` | Maximum allowed file size for `.workspace.json` snapshots. |

---

## 📑 Document Ingestion Matrix

| Format | Extension | Underlying Parser | Location Granularity | Extraction Policy |
|:---:|:---:|:---:|:---:|---|
| **PDF** | `.pdf` | PyMuPDF (`fitz`) | Page numbers (`Page 1`, etc.) | Direct text extraction; unreadable or scanned pages yield explicit warnings. |
| **Word** | `.docx` | `python-docx` | Paragraphs & table rows | Extracts narrative flow and embedded tables in sequential document order. |
| **Excel** | `.xlsx` | `openpyxl` & `pandas` | Sheet name & row range | Uses stored cached values; calculates full-table numeric summaries over all rows; previews up to 100 rows. |
| **CSV** | `.csv` | `pandas` | Row intervals & columns | Evaluates shape bounds and encoding (UTF-8 with fallbacks); generates full-table statistical profiles. |

---

## ⚙️ Requirements

- Python **3.11 or newer** (tested with Python 3.11.9).
- An API key for **Google Gemini** (required for Primary and Reserve tiers).
- An API key for **Groq** (required for Tier 2 operational fallback).
- Modern web browser (Chrome, Edge, Firefox, Safari).

---

## 📦 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/ShekhawaTTiku/SourceSpark.git
cd SourceSpark
```

### 2. Create and Activate a Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy the example environment template to create your local `.env` file:

```bash
# Windows PowerShell:
Copy-Item .env.example .env

# macOS / Linux:
cp .env.example .env
```

Open `.env` in your editor and provide your API keys:

```dotenv
GEMINI_API_KEY=your-gemini-api-key
GROQ_API_KEY=your-groq-api-key

# Optional model overrides:
GEMINI_MODEL=gemini-3.6-flash
GEMINI_FALLBACK_MODEL=gemini-3.8-flash
GROQ_MODEL=openai/gpt-oss-120b
```

> **Note:** For deployment on **Streamlit Community Cloud**, store these variables directly in **App Settings &rarr; Secrets** instead of committing a `.env` file.

---

## ▶️ Usage

### Launch the Web Application

Launch the local Streamlit dashboard:

```bash
python -m streamlit run web_app/app.py
```

Once running, navigate to **[http://127.0.0.1:8501](http://127.0.0.1:8501)** in your browser.

```text
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.1.100:8501
```

### Quick Walkthrough

1. **Setup**: Select **Weekly Plan** (5 or 7 days) or **Campaign Plan**, assign a start date, and optionally enter your target audience, core campaign goals, and editorial guidance.
2. **Sources**: Upload your reference files (test with the fictional files in `sample_docs/`). Click **Add documents** to trigger parsing, inspect extracted text, and review parser warnings.
3. **Topics**: Click **Generate topics** to query the provider chain. SourceSpark extracts key insights, suggested audiences, formats, and verbatim evidence citations.
4. **Review & Library**:
   - Inspect evidence tags: **Green** means source checks passed; **Red** highlights items recommended for human review.
   - Click **Select** to add strong ideas to your plan.
   - Click **Exclude** to discard an angle; SourceSpark remembers excluded topics to prevent repeated ideas in subsequent generation batches.
5. **Finish & Export**:
   - Arrange selected topics into calendar slots or campaign order.
   - Click **Finalize Plan** to lock the schedule.
   - Download the finalized plan as a structured **Markdown report (`.md`)** or **CSV spreadsheet (`.csv`)**.
   - Use the sidebar to download a portable **`.workspace.json`** snapshot to resume your work at any time.

---

## 🧪 Testing & Verification

SourceSpark includes an extensive automated test suite covering document parsing, evidence grounding, provider failovers, Pydantic data models, and workspace serialization.

Tests execute completely **offline** using deterministic fictional fixtures and simulated provider responses, guaranteeing zero live API credit consumption during verification:

```bash
python -m pytest -q
```

**Verified Test Results:**
```text
........................................................................ [ 27%]
........................................................................ [ 55%]
........................................................................ [ 83%]
...........................................                              [100%]
259 passed in 13.16s
```

All 259 tests pass across the following test suites:
- `test_file_router.py`, `test_pdf_parser.py`, `test_docx_parser.py`, `test_tabular_parser.py`: Ingestion & extraction rules.
- `test_context_builder.py`: Provenance, evidence formatting, and context bounds.
- `test_generation.py`, `test_prompt_builder.py`, `test_provider_chain.py`: Provider failovers, prompt schemas, and quote validation.
- `test_plan_manager.py`, `test_planning_service.py`, `test_state_manager.py`, `test_topic_pool.py`: Planning rules and library state.
- `test_models_storage_exports.py`: Pydantic model integrity, workspace snapshot round-tripping, and Markdown/CSV export formatting.
- `test_ui.py`: Streamlit view routing and state handlers.

---

## 🔐 Data Privacy & Security

- **Local Execution**: All document parsing, text extraction, quote validation, and workspace serialization occur entirely on your local machine. Original document binaries are never sent to external servers.
- **Minimal Context Transmission**: Only canonical extracted text blocks and assembled prompts are transmitted to configured LLM providers during explicit generation calls.
- **Safe Workspaces**: Saved `.workspace.json` snapshots contain extracted text and plan metadata, but never store API keys, environment credentials, or raw binary files.
- **Spreadsheet Security**: CSV exports automatically neutralize dynamic formula triggers by prefixing cells starting with `=`, `+`, `-`, or `@` with a single apostrophe (`'`), preventing CSV injection attacks in Microsoft Excel and Google Sheets.
- **Sanitized Errors**: Provider error logs and feedback messages are sanitized to prevent internal stack traces or credential disclosures from reaching the user interface.

---

## ⚠️ Limitations

| Area | Current Limitation |
|---|---|
| **Scanned PDFs** | Text extraction relies on selectable text; image-only scanned PDFs require external OCR prior to upload. |
| **Excel Formulas** | Extraction reads stored calculated values; formulas are not dynamically re-evaluated during ingestion. |
| **Table Previews** | Tabular sources compute summary statistics across all loaded rows, while individual row previews are bounded to the first 100 rows. |
| **Context Boundaries** | Assembled prompts are capped at 400,000 characters to prevent silent truncation; oversized corpora must be partitioned into focused workspaces. |
| **Provider Quotas** | Multi-tier failover mitigates individual provider outages, but generation requires active internet access and valid API keys with available quota. |
| **Human Review** | Local validation verifies lexical quote occurrence and basic numeric claims, but cannot replace human editorial discretion. |

---

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| **Python 3.11** | Core application runtime and workflow engine |
| **Streamlit** | Interactive web application framework and reactive state management |
| **Streamlit Antd Components** | Polished navigation tabs and status indicators |
| **Streamlit Shadcn UI** | Refined modern UI design primitives |
| **Google GenAI SDK** | Client for Gemini 3.6 Flash and Gemini 3.8 Flash models |
| **Groq API** | High-speed inference for open model operational failover (`gpt-oss-120b`) |
| **Pydantic v2** | Strict domain modeling, boundary validation, and schema enforcement |
| **PyMuPDF (`fitz`)** | High-performance PDF text extraction and layout inspection |
| **python-docx** | Word document (`.docx`) paragraph and table parsing |
| **pandas & openpyxl** | Tabular parsing, summary statistics, and Excel spreadsheet processing |
| **pytest** | Comprehensive offline automated test suite |

---

## 📚 Documentation & Guides

For deeper technical deep dives and architectural rationale, explore the comprehensive documentation in `docs/`:

- [Codebase Map](docs/CODEBASE_MAP.md): Detailed inventory of file ownership and code structure.
- [Data Flow Guide](docs/DATA_FLOW.md): Step-by-step lifecycle of documents, prompts, and workspace states.
- [Architectural Decisions](docs/DECISIONS.md): Key design tradeoffs and structural decisions.
- [Project Specification](PROJECT_SPEC.md): Full product specification and acceptance criteria.
- [Learning Guide](docs/LEARNING_GUIDE.md): Guided conceptual walkthrough of the planning system.
- [Known Limitations](docs/KNOWN_LIMITATIONS.md): In-depth review of edge cases and boundaries.
- [Troubleshooting](docs/TROUBLESHOOTING.md): Solutions for common installation and execution issues.

---

## 👤 Maintainer

**Digvijay Singh Shekhawat**

[![GitHub](https://img.shields.io/badge/GitHub-@ShekhawaTTiku-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/ShekhawaTTiku)

---

<div align="center">

*Built with ⚡ Streamlit, 🧠 Gemini & Groq, 📄 PyMuPDF, and 🛡️ Pydantic.*

</div>
