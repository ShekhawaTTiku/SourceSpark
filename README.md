# SourceSpark

**Turn source documents into evidence-backed weekly plans and campaigns.**

SourceSpark is a local Streamlit application for waste-awareness planning. Upload
reports, notes and spreadsheets, generate topic ideas linked to their sources,
and build a plan you can review, export and reopen.

## Features

- **Week and Campaign modes:** five/seven-topic weeks, or flexible campaigns with
  an optional target. Campaigns grow across batches of up to ten generated ideas.
- **PDF, DOCX, XLSX and CSV:** inspect extracted text, source locations and warnings.
- **Grounded ideas:** titles, insights, context, suggested audience/format and
  evidence excerpts, checked against the uploaded sources.
- **Provider fallback:** Gemini primary, Groq on operational failure, then a
  Gemini reserve. All routes use the same local validation.
- **Reusable library:** select, deselect, exclude, restore and reorder topics.
- **Weekly scheduling:** day assignments and optional dates from a Monday start.
- **Review and export:** explicitly finalize, then download Markdown or CSV.
- **Save and reopen:** portable workspace files preserve sources, ideas and plans.

## Run on your Windows PC

Open PowerShell and run:

```powershell
Set-Location 'D:\projects\SourceSpark'
& 'C:\Users\GIGABYTE\AppData\Local\Programs\Python\Python311\python.exe' -m streamlit run web_app/app.py
```

Open [http://127.0.0.1:8501](http://127.0.0.1:8501). Keep the terminal open;
**Ctrl+C** stops the app. Save your workspace inside the app before stopping or
restarting, because session memory is temporary. If that port is already in use,
use the running app or stop its terminal before starting another copy.

Your existing Python already has the dependencies. To install missing packages:

```powershell
& 'C:\Users\GIGABYTE\AppData\Local\Programs\Python\Python311\python.exe' -m pip install -r requirements.txt
```

Your `.env` already contains your keys. Keep it local and restart after changes.

## Set up another machine

Use Python 3.11. The local build was tested with Python 3.11.9 and Streamlit
1.66.0; see [dependency notes](streamlit_setup/dependency_notes.md) for observed
versions. Requirements declare dependencies but are not a complete lockfile.

```powershell
git clone https://github.com/ShekhawaTTiku/SourceSpark.git
Set-Location SourceSpark
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit the new `.env` and fill the two blank API key fields:

```dotenv
GEMINI_API_KEY=
GROQ_API_KEY=
GEMINI_MODEL=gemini-3.6-flash
GEMINI_FALLBACK_MODEL=gemini-3.8-flash
GROQ_MODEL=openai/gpt-oss-120b
```

Both Gemini models share one key. Model access depends on your provider account.
On your original PC, preserve your populated `.env` instead of copying over it.

```powershell
python -m streamlit run web_app/app.py
```

## Try the workflow

1. Name the workspace, choose Week or Campaign, and apply plan settings.
2. Upload the clearly fictional files in [sample_docs](sample_docs/), then press
   **Add documents**. Inspect extracted text and warnings.
3. Press **Generate** to send the extracted sources, brief and remembered angles
   to the configured providers.
4. Review ideas and evidence. Select useful topics and exclude unwanted angles.
5. Arrange topics, assign weekly days if relevant, and explicitly finalize.
   A nonempty shorter plan requires acknowledgement.
6. Download Markdown or CSV, and save a workspace file to resume later.

New plan retains the sources and library. New empty workspace clears them after
confirmation. Each workspace has one active plan. Reopen a finalized plan for
editing before changing it. SourceSpark produces topics, not finished posts or
automatic publishing.

## Run tests

Automated checks use fictional sources and simulated provider responses without
spending live API quota:

```powershell
python -m pytest -q
```

On your original PC, substitute the full Python path above if `python` resolves
a different installation.

The last complete verification passed **240 tests**. Separate live checks passed
for Gemini primary and Groq fallback, including evidence validation, finalization,
exports and snapshot reopening. The Gemini reserve returned a service-unavailable
response. A complete manual browser upload/download/reopen run and CSV appearance
in Excel remain pending.

## Privacy and limitations

Parsing happens locally. Explicit generation may send extracted sources to Google
and Groq. Workspace files contain private extracted text, topics and review state;
they are unencrypted and exclude keys and original uploaded binaries.

Source limits are 10 MiB per file, 20 files and 50 MiB combined. Additional context,
table, archive and provider guards reject excess without silently truncating
evidence. Workspace files have a 20 MiB guard.

Scanned PDFs need OCR, which is not implemented. Excel formulas use stored cached
results and are not recalculated. Individual row previews cover the first 100
rows; summaries can use all loaded rows. Human review remains necessary.

## Structure

| Folder | Responsibility |
| --- | --- |
| `web_app/` | Streamlit screens and actions |
| `config/`, `.streamlit/` | Settings, limits and theme |
| `documents/` | Source readers and evidence context |
| `models/` | Validated topics, plans and workspaces |
| `workflow/` | Planning rules and generation coordination |
| `ai/`, `prompts/` | Providers, fallback and evidence validation |
| `exports/`, `storage/` | Reports and workspace files |
| `tests/`, `sample_docs/` | Verification and fictional examples |
| `docs/`, `streamlit_setup/` | Guides and dependency records |

## Documentation

Start with the [documentation index](docs/DOCUMENTATION_INDEX.md),
[user guide](docs/PROJECT_GUIDE.md), or [learning guide](docs/LEARNING_GUIDE.md).
See the [project specification](PROJECT_SPEC.md),
[progress record](docs/PROGRESS.md), [known limitations](docs/KNOWN_LIMITATIONS.md)
and [troubleshooting](docs/TROUBLESHOOTING.md) for details.

## Repository hygiene

The repository includes application code, prompts, tests, specifications, guides
and fictional samples. Ignore rules exclude credentials, private uploads and
snapshots, caches, environments, build output, coverage reports, editor files and
the superseded chat reference. Only the blank `.env.example` is published.
Keep real uploads in `user_uploads/` and private snapshots in `workspace_snapshots/`
or use the `.workspace.json` suffix so they remain ignored.
