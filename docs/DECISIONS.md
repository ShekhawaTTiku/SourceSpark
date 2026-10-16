# Implementation decisions

## 15 October 2026 — Step 1 runtime and dependencies

Use the approved existing global Python 3.11.9 explicitly for installation,
verification, and startup. Its path differs from the terminal's previously
observed default interpreter. Install only Streamlit and python-dotenv now,
retaining existing compatible packages. Record all ten intended dependencies
without historical version pins. Dependency consistency checks passed before
and after installation; no existing distribution required a version change.
The inventory and supporting package additions are recorded in
streamlit_setup/dependency_notes.md.

## 15 October 2026 — Interface ownership and imports

Keep the entry point in web_app/app.py and display functions in web_app/views.py.
The entry point adds the resolved project root to Python's import search path
so the agreed nested startup location can import sibling application packages.
The project uses Python's namespace packages; empty package markers were not needed.
The initial page and sample interaction passed Streamlit's in-process app checks.

## 15 October 2026 — Configuration and learning scope

Keep product limits in config/settings.py, framework settings in
.streamlit/config.toml, and local configuration loading through python-dotenv.
The upload limit is 10 MiB in both relevant locations. The server listens on
loopback, and Streamlit usage statistics are disabled. No Gemini model has been
selected; account access will be verified in Step 10.

The Step 1 button displays fixed fictional cards for its current run. It does not
create campaign state or imply that sources were parsed. The page describes the
temporary behavior. Session memory begins in Step 2; live generation and removal
of simulation controls happen in Step 10.

## 15 October 2026 — Step 2 session memory

One campaign record lives in Streamlit session state, independent per browser
session. Plain workflow functions receive that record without importing Streamlit.
Standard-library dataclasses hold campaign and source data; typed dictionaries
hold early topic records until Step 8 introduces Pydantic models. UI callbacks
apply changes before rendering, keeping sidebar counts current.

SHA-256 content fingerprints detect duplicates regardless of filename. Conflicting
names are rejected. Source additions and removals increment the input revision;
only successful processing consumes it, including zero-topic success. Failure
releases the busy flag while preserving pending inputs. Cited sources cannot be
removed. Completed campaigns and active processing prevent source edits.

Topic rules reject normalized title and insight repetitions and enforce ten slots.
Accepted data is copied to preserve earlier results. Semantic distinctness and
factual support still need later evidence checks and human review.

The page uses controlled fictional records. Sample topic addition does not imply
that generation succeeded. Step 3 adds visible simulated processing and decisions;
Step 10 replaces simulation with Gemini. All 21 workflow tests and in-process UI
checks passed. Dependency consistency passed after installing pytest and its two
missing supporting packages; no existing package versions changed.

## 17 October 2026 — Expanded Version 1 scope; supersedes old count rules

The user approved two planning modes and every suggested addition: brief,
selection/exclusion, ordering/day assignment, names, CSV and workspace save/reopen.
The old seven-to-ten total, automatic completion at seven, campaign-only state,
and document-change-only generation eligibility are superseded requirements.
Historical implementation remains unchanged until Step 2R.

Use a reusable source/topic workspace and one active named plan. Week uses five
or seven slots; Campaign has an optional user target and no fixed total ceiling.
Ten is an initial per-request batch ceiling, not the maximum library/plan size.
Readiness never finalizes automatically. Mode conflicts preserve records and
require explicit selection; short plans require acknowledged gaps.

Deselect retains an available alternative; Exclude remembers an unwanted angle;
Restore is explicit. Evidence survives review, both exports and reopening.
An explicit Find more action can use unchanged sources without enabling rerun
requests. All prior/excluded summaries remain subject to complete request budgets.

Use a versioned downloadable JSON workspace file rather than a new database
package. It contains extracted content, topics, brief, plan, exclusions and
references, but no raw uploads, credentials, prompts, provider responses or local
paths. Validate wholly before replacing memory; protect unsaved work and disclose
unencrypted private content. No automatic history/autosave/cloud sync is included.

Add Step 2R before Step 3, preserve parser/model/prompt numbers, and extend through
Step 13 for CSV/dates, persistence and complete acceptance. All scope/design and
teaching records were updated without runtime implementation or installations.

## 17 October 2026 — Complete V1 implementation

The explicit one-shot build request overrides intermediate learning pauses for
this run. Implemented the expanded scope through Steps 2R–13, preserving existing
module ownership and extending the prior state/topic code rather than creating a
second application. web_app/app.py remains the Streamlit V1 entry point; moving
it was unnecessary. V2 has no scaffold, server, frontend or other implementation.

Pydantic records now cover sources, evidence, descriptive topic context, the active
plan and reusable workspace. Workflow changes validate a complete candidate before
committing. Stable IDs connect library/selection/exclusion/day/evidence records.
A source must remain while any retained topic, including excluded ones, cites it.

Plan targets are separate from the ten-candidate batch ceiling. Campaigns above ten
and open targets share the same pipeline as five/seven-slot weeks. Readiness is
computed; finalization is explicit. Exclusion suppresses an angle; deselection
keeps it available. Mode conflicts require user choices rather than truncation.
Snapshots restore extracted text and metadata, not original binary uploads.

One reserved generation action includes the full brief, sources, prior/excluded
angles and response capacity. It checks model metadata and full tokens, uses a
60-second timeout, disables SDK hidden retries, and permits one shared temporary
retry. Invalid/all-rejected output remains retryable; a valid zero response is a
successful round. Existing work is merged only after validation. No credentials
were configured; account/model/quota/live factual verification remains pending.

Official SDK/schema/token documentation and local schema conversion were checked.
The six missing intended packages were installed. websockets changed 17.2 to 16.1.1
for SDK compatibility; dependency_notes.md records purposes and all versions.
Consistency passed. No new environment or unrelated project dependency was added.

Version 1 snapshots use strict complete JSON records, duplicate-field rejection,
size/collection limits, evidence/reference checks and atomic UI replacement. They
exclude credential settings/raw uploads and are not encrypted. CSV uses proper
serialization, UTF-8 BOM and formula neutralization. Reports revalidate finalized
selections so reopening immediately removes export eligibility.

Independent review found and repaired stale mode widget state after replacement,
large-target JavaScript overflow, calendar end-of-range overflow, and DOCX blank
edge-cell canonical whitespace. Regression checks cover these failures. The final
suite passed 196 checks; module compilation and dependency consistency passed;
local server/page/health succeeded. Browser initial layout was visually inspected.
The in-app automated chooser did not respond, so actual browser upload selection
is not claimed. Real-file ingestion is covered through integration tests.

Nine supporting guides explain usage, data flow, learning, maintenance/handoff,
terminology and troubleshooting without code snippets, actual prompts or commands.
Prompt text remains in prompts/. Future extensions remain out of scope.

## 17 October 2026 — Default Gemini configuration

At the user's request, the local .env and safe example now choose gemini-3.8-flash.
Google's current official model catalog lists it as stable, structured-output
guidance includes it, and the pricing page lists a free tier. This is a public
model suitability choice, not live verification of the user's account, quota,
pricing eligibility or response behavior. Existing key content was preserved;
no key value was printed. The user must add their key and restart the app.
Only the key and model ID are environment settings; operational guards remain
centralized in config/settings.py. Configuration parsing was checked without
making a provider request.

References: [model catalog](https://ai.google.dev/gemini-api/docs/models),
[structured outputs](https://ai.google.dev/gemini-api/docs/structured-output),
[pricing](https://ai.google.dev/gemini-api/docs/pricing).


## 17 October 2026 — User-authorized provider failover and live verification

Gemini 3.6 Flash is primary; Groq openai/gpt-oss-120b is the direct fallback;
Gemini 3.8 Flash is last reserve. This supersedes the previous single-model default
and original no-provider-fallback restriction. Models share the existing validation
pipeline. Zero valid results, refusals and unsupported evidence do not cause model
hopping. Operational failures may advance through a finite chain. Known bad Gemini
credentials skip its reserve. The original primary retry budget remains one;
Groq and the reserve add none. Python standard-library HTTPS avoids another SDK.

Generation disclosure now names both providers. Safe feedback identifies the route;
snapshots retain no credentials/client objects. Configuration contains both key
fields and the exact three user-selected model IDs. .env remains explicitly ignored;
.env.example contains no real key. The project is not initialized as a Git repository.

Live tests fixed schema transport differences without weakening local validation.
Gemini receives supported inlined structural fields; Groq uses strict JSON schema
with all property names preserved. An application User-Agent prevents the observed
Groq rejection of the default Python identifier. All tests passed after these fixes.

The live primary and controlled live Groq fallback completed evidence acceptance,
short-plan finalization, both exports and workspace reopening. The reserve's live
generation returned 503; it remains an external verification gap. Latest counts
and exact observations are in PROGRESS.md. No secrets or raw user documents were
included in diagnostics; small fictional sources were used.
# SourceSpark publishing update — 17 October 2026

The user chose SourceSpark as the product and folder name and authorized publishing
to ShekhawaTTiku/SourceSpark. README now includes practical setup and run commands,
as explicitly requested. A root requirements file delegates to the existing list.
Publication uses batches of at most four new files per commit, with a smaller final
batch when needed. Credentials, private data, caches and the superseded combined
chat reference remain local. The running app must release the folder before Windows
can rename it; saved work must be preserved before stopping the server.

After the user saved and authorized restart, Codex itself also held the parent
directory open. The project contents and intact repository were moved into
D:\projects\SourceSpark instead. The old directory has no project files, only an
empty .git directory. This preserves local keys and Git history without closing
the user's Codex session.

