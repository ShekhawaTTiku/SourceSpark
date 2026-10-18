# Project Specification: SourceSpark

**Version:** 1 learning MVP — expanded scope  
**Revised:** 17 October 2026  
**Project location:** D:\projects\SourceSpark  
**Companion:** [DOCUMENT_SPEC.md](DOCUMENT_SPEC.md)

This is the authoritative product and build specification. Earlier seven-to-ten-topic campaign rules and the original combined reference are superseded. Requirements are not claims of completed functionality. Implementation, commands, configuration contents, and actual AI prompts belong in their owning files at the relevant build step.

**UI revision — 17 October 2026:** New plans now begin with Weekly or Campaign only, followed by five/seven days or a positive campaign topic count, a required start date for either mode, then a Yes checkbox that reveals optional name/audience/goal/guidance questions. Weekly plans use consecutive dates from any chosen start; campaigns retain the start as metadata. Sources, Topics and Finish are separate screens after setup. These user-requested rules supersede earlier Monday-only/undated setup and open-target creation descriptions below. Existing undated and open-target snapshots remain compatible.

## 1. Project Summary

**Topic review revision — 17 October 2026:** Source and factual validation is now advisory. Keep all readable structured candidates (up to the ten-record response bound), with green source-check labels or red review reasons. Tolerate harmless quote formatting, preserve research scope, and use a single generation response without a separate extraction or repair call. New topics require manual selection; selected topics and exports omit review labels. Uncertain evidence must remain saveable and reopenable. These user-requested rules supersede strict candidate rejection and automatic selection requirements below.

Help one person turn uploaded waste-related documents into distinct, evidence-backed communication topics, organized as a five/seven-topic weekly plan or a flexible campaign. Support a planning brief, user selection and ordering, readable exports, and saving/reopening work. This remains a personal learning project: the learner should understand each responsibility and data journey.

A workspace is the reusable source pool, topic library, exclusions, and working information. Its active plan is a named, ordered selection of topics. Campaign is one plan type, not the only organizing concept.

| Mode | Target | Completion |
| --- | --- | --- |
| Week | Five or seven selected topics, one per day/slot | Filled means ready for review; the user finalizes explicitly. |
| Targeted Campaign | User-selected positive whole number | No fixed ten-topic total ceiling; the user reviews and finalizes. |
| Open Campaign | No required total | Add bounded batches and decide when to finish. |

Targets count selected topics, not the entire library. Never invent or repeat ideas to fill slots. Zero is valid generation feedback but cannot become a finalized empty plan. A nonempty short plan can be finalized with explicit shortfall acknowledgement. Weekly empty slots remain visible.

### Definition of done

- Run through the approved existing global Python without creating an environment.
- Add, parse, and inspect PDF, DOCX, XLSX, and CSV, with individual invalid-file feedback.
- Support names, both modes, optional target/audience/goal, and conflict-safe mode changes.
- Generate structured topics with source membership, locations, excerpts, and local acceptance checks.
- Select/deselect, exclude/restore, reorder, assign days and optional dates, and finalize explicitly.
- Retain earlier work through reruns, additional rounds, and recoverable failures.
- Export matching finalized Markdown and CSV plans with evidence.
- Save/reopen a validated, versioned workspace without credentials or raw uploads.
- Pass meaningful automated/manual checks and explain source-to-topic-to-export-to-reopen behavior.

### Implementation and verification status

The one-shot build requested on 17 October implements the expanded V1 modules and interface across Steps 2R–13. Real extraction, reusable workspace/planning, explicit candidate batches, review/finalization, both exports, and versioned save/reopen are present. The old total ten-topic ceiling and campaign-only state were replaced. docs/PROGRESS.md records actual current checks. Gemini account/model access, quota/pricing eligibility, and live generated quality remain unverified at the initial build; current live checks are recorded in docs/PROGRESS.md; provider behavior is tested with controlled responses. Documentation and implementation do not establish the learner’s understanding or replace factual review.

## 2. Version 1 Features and Exclusions

| ID | Feature | Required outcome |
| --- | --- | --- |
| F1 | Multi-format source pool | Add mixed files, preserve metadata, detect identical content and name conflicts. |
| F2 | Format readers | Preserve text, tables, computed spreadsheet summaries, source locations, and warnings. |
| F3 | Source/context inspector | Inspect eligible evidence before it is sent to AI. |
| F4 | Grounded generation | Structured, distinct topics proportional to supplied evidence. |
| F5 | Incremental batches and retry | Preserve previous work; explicitly request more, even from unchanged sources. |
| F6 | Week and Campaign modes | Five/seven weekly slots or optional campaign target without a fixed total ceiling. |
| F7 | Workspace/plan names and brief | Recognizable names, optional audience and communication goal. |
| F8 | Review and topic inclusion | Select/deselect, exclude unwanted angles, restore deliberately. |
| F9 | Order and weekly assignment | Arrange topics, assign days, optionally show dates. |
| F10 | Explicit finalization and Markdown | Review before finishing and download readable evidence-bearing plans. |
| F11 | CSV export | Ordered planning table usable in Excel. |
| F12 | Save/reopen | Continue later from a local working snapshot, including sources and review state. |

Separate parsing/generation actions, busy guards, visible limits, duplicate feedback, clear errors, unsaved-change protection, and local/cloud disclosure apply throughout.

Outside Version 1: accounts, multiple concurrent users, cloud sync/databases, automatic history/version archives, background autosave, OCR, vector retrieval, a separate frontend, complete post writing, generated images, automatic/scheduled publishing, billing, Docker, and deployment pipelines. Explicit local snapshots, CSV, and manual weekly day/date planning are now inside scope.

## 3. Runtime, Dependencies, and Budget

Use the approved global Python at C:\Users\GIGABYTE\AppData\Local\Programs\Python\Python311\python.exe, observed as Python 3.11.9. The terminal previously selected an unrelated ML311 environment; explicitly use the approved interpreter for installations, startup, and checks. Do not create/activate another environment or install another Python.

Retain all ten libraries: streamlit for UI/state; google-genai for Gemini; pydantic for validation; pymupdf for PDF; python-docx for Word; pandas for tables; openpyxl for XLSX; tabulate for Markdown tables; python-dotenv for local settings; pytest for verification. Standard-library fingerprints, dates, CSV, and JSON suffice for the new features; no database package is needed.

The 14 October inventory found pandas 3.0.5 and the other nine libraries absent. Steps 1 and 2 subsequently installed Streamlit, python-dotenv, pytest, and supporting dependencies. These are historical observations, not a fresh package audit. streamlit_setup/dependency_notes.md records observed versions and changes.

Keep compatible installed packages, install missing ones when needed, and change versions only for demonstrated issues. Inspect requirements before changes, check consistency afterwards, and record previous/resulting versions and reasons. streamlit_setup/requirements.txt declares the ten project libraries with only justified constraints, not historical pins or unrelated global packages.

Windows is first supported. Parsing, review, exports, and saving are local; generation requires internet and sends extracted content to Gemini. No dedicated GPU is required. Free-tier use is a goal, not a guarantee. At Step 10 verify account access, schema support, quotas, and pricing using the official [models](https://ai.google.dev/gemini-api/docs/models), [pricing](https://ai.google.dev/gemini-api/docs/pricing), and [rate limits](https://ai.google.dev/gemini-api/docs/rate-limits). Do not enable billing automatically. Operational failover follows only the explicitly configured Gemini/Groq/Gemini chain.

## 4. Architecture and Data Journey

One Streamlit application has these boundaries:

| Area | Owns | Must delegate |
| --- | --- | --- |
| web_app/ | Screens, controls, previews, downloads | Parsing, requests, and planning rules. |
| streamlit_setup/ | Requirements and runtime records | Application behavior. |
| .streamlit/ | Framework appearance/uploader/server settings | Secrets and product targets. |
| config/ | Shared resource limits and setting loading | Rendering and processing. |
| documents/ | Readers, routing, provenance, context | Generation and planning. |
| workflow/ | Workspace state, topic acceptance, plan rules, request eligibility/orchestration | Provider, storage, parsing, formatting. |
| models/ | Topic/evidence, response, plan, saved workspace contracts | UI and network calls. |
| prompts/ | Instruction assets and request assembly at Step 9 | Acceptance and state mutation. |
| ai/ | Provider access and source-aware response validation | UI and persistent storage. |
| exports/ | Markdown and CSV formatting | Completion decisions. |
| storage/ | Bounded versioned serialization/load validation | API calls, arbitrary paths, automatic state replacement. |
| docs/, sample_docs/, tests/ | Learning records, fictional fixtures, focused verification | Runtime business logic. |

Flow: name workspace/plan and choose mode/brief; add files; inspect extracted sources; explicitly request a bounded batch; assemble complete source/prior-topic/exclusion context; validate returned candidates; retain valid topics and fill vacant selections for review; select/exclude/order/assign; explicitly finalize; export. Save a workspace at any non-busy stage; validate all loaded data before replacing memory. The coordinator is the place to trace the operation; app.py delegates.

| Plan state | Meaning and actions |
| --- | --- |
| DRAFT | Empty or below target; edit, add sources, select, generate when eligible, save. |
| READY_FOR_REVIEW | Fixed target filled, or open campaign has selected topics; review and explicitly finalize. Open campaigns can request more. |
| FINALIZED | Explicitly finished nonempty selection; read/export/save, or explicitly reopen for editing. |

Recompute readiness after relevant edits. Target attainment never finalizes. A short finalized plan records its shortfall acknowledgement. Busy state is transient and separate; failures are feedback, not completion. Ordinary reruns make no AI requests.

## 5. Folder Structure and Growth

Use the existing root; do not create a nested project. This is a target layout, not permission for empty scaffolding.

| Folder | Files |
| --- | --- |
| Root | PROJECT_SPEC.md, DOCUMENT_SPEC.md, README.md, .gitignore, .env.example, ignored .env. |
| web_app/ | app.py, views.py. |
| streamlit_setup/ | requirements.txt, dependency_notes.md. |
| .streamlit/ and config/ | config.toml and settings.py respectively. |
| workflow/ | state_manager.py, topic_pool.py, plan_manager.py, planning_service.py. |
| documents/ | docx_parser.py, tabular_parser.py, pdf_parser.py, file_router.py, context_builder.py. |
| models/ | topic.py, generation_result.py, plan.py, workspace.py. |
| prompts/ | grounding_rules.txt, topic_request.txt, builder.py; create at Step 9. |
| ai/ | gemini_client.py, groq_client.py, provider_chain.py, topic_generator.py, response_validator.py. |
| exports/ | markdown_exporter.py, csv_exporter.py. |
| storage/ | workspace_store.py. |
| docs/ | PROGRESS.md, DECISIONS.md. |
| sample_docs/ | Fictional fictional_school_guide.docx, fictional_weekly_audit.csv, fictional_school_audit.xlsx, fictional_school_report.pdf; generate_samples.py recreates these fixtures. |
| tests/ | test_state_manager.py, test_topic_pool.py, test_plan_manager.py, test_planning_service.py, reader/router/context tests, test_prompt_builder.py, test_generation.py, test_ui.py and shared conftest.py. Related models/export/storage checks are grouped in test_models_storage_exports.py to exercise shared snapshot/report fixtures. |

The uncreated campaign_service.py is replaced in the plan by planning_service.py. Excel/CSV share a parser; evidence shares the topic model file. Package markers may be added when needed; no generic miscellaneous utilities folder.

| Step | New areas | Existing updates |
| --- | --- | --- |
| 1, historical | Interface, settings, framework/setup files, README, records | No future modules. |
| 2, historical | State/topic rules and tests | Interface and records. |
| 2R | plan_manager.py and tests | State, topics, settings, UI/tests, README; replace legacy total ceiling. |
| 3 | planning_service.py, Markdown exporter, tests | Simulated review, exclusion, ordering, finalization. |
| 4 | Word reader, fixture, tests | Dependency/progress notes. |
| 5 | Tabular reader, fixtures, tests | Dependency/progress notes. |
| 6 | PDF reader, fixture, tests | Dependency/progress notes. |
| 7 | Router, context builder, tests | Real uploads/inspection. |
| 8 | Four model files and tests | Align ordinary early records and workflow contracts. |
| 9 | Prompt assets/builder/tests | Request assembly and records. |
| 10 | AI modules and generation tests | Live service; remove fictional UI controls. |
| 11 | CSV exporter/tests | Weekly day/date controls, both reports, plan checks. |
| 12 | Workspace storage/tests | Save/reopen controls, schema, ignore rules. |
| 13 | No required new area | Acceptance, repairs, records, learning review. |

## 6. Data and Storage Design

### Workspace lifecycle

Version 1 retains one active workspace and one active plan, plus a reusable topic library and exclusions. New plan clears selections after a clear user action while retaining sources/topics. New empty workspace clears all working data after confirmation. Separate snapshots retain previous work; there is no automatic history browser.

Session memory survives ordinary reruns but may be lost on refresh, connection loss, a new session, closed tab, or server restart. Explicit Save workspace creates a durable downloadable snapshot. Unsaved changes after that snapshot can be lost. Show an unsaved-changes indicator; do not imply autosave or guaranteed file retention merely because a download was prepared.

### Document record

Store content fingerprint, exact original filename, supported extension, byte size, readable extracted content and locations, character count, warnings, and generation participation. Release raw upload bytes after extraction. Matching bytes are duplicates regardless of filename; different content with a case-insensitive matching name requires renaming.

While editing, remove only sources not cited by any retained topic. Excluded topics retained for restoration also protect their evidence. New plan does not bypass this rule. Version 1 replaces cited sources by starting a deliberately new workspace or retaining the original under its identity, not by silently overwriting.

### Topic and evidence

A topic has a stable application-assigned identity, a 5–120-character title, a 20–500-character core insight, descriptive context of 20–1200 characters, nonempty audience/format, structured evidence, and origin metadata for fictional learning records where applicable. Evidence includes document identity, exact filename, available source location, and a short excerpt found in included source content. Facts, units, geography, dates, penalties, and causal interpretation must stay proportional to evidence. Audience/format can be editorial suggestions.

Library membership differs from selection. Deselect removes a topic from the plan but keeps it available. Exclude retains the topic and its angle as something to avoid repeating; Restore is explicit. Preserve identities and evidence through all actions. Arbitrary factual rewriting of generated insights is outside this version.

### Active plan

Retain identity/name, mode, optional audience/goal, target, ordered selected topic IDs, weekly slots, optional Monday start date, state, and shortfall acknowledgement. Workspace/plan names get editable nonempty defaults. Brief fields guide relevance without authorizing new facts.

Week mode uses five Monday–Friday or seven Monday–Sunday slots. Optional dates derive from a Monday week-start choice and the entire five/seven-day span must fit the supported calendar. Use accessible move/position/swap controls; drag-and-drop is not required. One topic per slot, no duplicate topic assignment. Short plans retain visible empty slots. Campaign uses order without mandatory days.

Mode/target changes retain sources/library. A smaller target must not silently discard or choose excess selections: preview the conflict and ask the user to choose which selections fit. Unselected records remain available. Removing a campaign target keeps selections. Order/date changes never spend AI quota. Finalized plans require explicit reopening before edits.

### Request identity and generation result

Responses contain zero to the requested batch capacity candidates and a sufficiency explanation. Retain accepted/rejected feedback and successful request records.

Track document revision separately from brief/planning changes. Request identity includes source revision, brief/mode/target, retained/excluded angles, and an explicit generation round. Document revision alone must not block a new deliberate round from unchanged sources. Ordinary reruns, day changes, and downloads are not requests.

Reserve one batch at a time. Failure preserves data and retry eligibility. Successful zero/new-zero responses consume that request, preventing automatic loops. A later explicit Find more topics can start another bounded round, with useful no-guarantee feedback after an unproductive round. Complete source and retained/excluded summaries must fit the provider budget; block oversized requests rather than silently forgetting earlier topics.

### Saved workspace

Use a versioned UTF-8 JSON file downloaded through the browser and reopened with a dedicated control. Include names/IDs, active plan/brief/state/slots, source metadata/extracted evidence, topics, exclusions, revisions, origin markers, and save metadata. Exclude raw uploads, secrets, environment contents, prompts, provider responses, client objects, and arbitrary local paths. Warn that extracted private content is included and the file is not encrypted.

Validate size/version, structure, unique identities, references, evidence membership/locations/excerpts, selected/excluded consistency, slot conflicts, target rules, source totals, and finalized state before applying anything. Imported fingerprints are references, not proof of authentic original bytes. Unsupported versions/corruption fail without partial replacement. Confirm replacement of unsaved work, then apply the fully validated workspace atomically. Reset busy/in-flight state; reopening makes no AI call. Support the current schema version without speculative migrations.

## 7. Functional Requirements and Acceptance

### F1–F3: Sources

Add documents parses locally without Gemini. Handle each file independently and display filename/type/size/character count/warnings. Extensions are case-insensitive. Keep routing separate from context assembly.

| Format | Required extraction | Visible limitations |
| --- | --- | --- |
| DOCX | Nonempty body paragraphs and tables in reading sequence with locations | Images, embedded objects, headers/footers, unsupported parts are not assumed read. |
| XLSX | All readable nonempty sheets, names/dimensions/labels, full-table numeric summaries, bounded row previews | Stored formula results are required; parser is not a calculation engine. |
| CSV | Labels/dimensions, summaries, bounded preview | Report fallback decoding; reject malformed/garbled content. |
| PDF | Selectable page text with page locations | No OCR; report scanned/empty pages and imperfect layout order. |

Statistics describe data, not causes. Distinguish previews from full summaries, avoid meaningless identifier averages, and retain units only where established. Location headings without underlying text are not evidence. Reject entirely unreadable files; disclose partial extraction.

The inspector shows complete eligible bounded source blocks with identity, filename, locations, and warnings. Its evidence must match generation input. Block oversized context with actionable feedback; never silently slice strings or omit later documents. Local characters and model tokens are different checks.

### F4–F5: Generation and recovery

Generate only on explicit eligible action. Supply sources, brief, prior titles/insights/evidence summaries, exclusions, and batch capacity. Source-embedded instructions are untrusted evidence, not app instructions.

Validate structure, required fields, source membership, locations, excerpts, obvious repeats within/across rounds, exclusion suppression, and capacity. Explain rejections. Matching excerpts and schemas do not prove correct reasoning; human review remains needed.

Valid candidates enter the library and can fill vacant plan slots for review, without displacing prior selections. Fixed-target capacity is vacant slots bounded by the batch ceiling. Open campaigns accumulate repeated bounded rounds without a ten-topic total cap. Full targets offer review/deselection/target changes rather than automatic generation.

No-new-topic success preserves earlier results and explains insufficiency. Failed or unusable responses leave retryable work. Brief changes and deliberate additional rounds can justify generation without new source uploads.

### F6–F9: Planning/review

Names, mode/target/brief, topic inclusion/exclusion/restore, ordering, and assignments must agree across UI/state/generation/saving. Display available versus selected counts and target/open-ended progress. Readiness is informational. Explicitly finalize only nonempty valid selections; acknowledge shortfalls. Finalization makes no AI call. Reopen explicitly before editing. Switching modes preserves records and resolves excess-selection conflicts visibly.

### F10–F11: Reports

Both formats use the same finalized selection/order/names/brief/mode/target and extraction limitations. Markdown includes finalization date, days/dates, all topic fields/evidence, and a source list distinguishing cited versus other pooled sources. Short weeks show empty slots.

CSV uses an Excel-compatible UTF-8 encoding choice, one row per campaign topic or weekly slot, with order/day/date/title/insight/audience/format/source filenames/locations/excerpts. Use a consistent representation for multiple evidence items, correct comma/newline quoting, and neutralization of spreadsheet formula interpretation in text cells. Empty slots have labels, not invented topics. Reports exclude secrets, excluded topics as planned content, raw responses, and full uploaded documents.

### F12: Persistence

Save drafts and finalized workspaces when not busy. Workspace snapshots include reusable source and review state, unlike public reports. Reopen through complete validation and atomic replacement. Verify round trips and restart/reopen behavior. Invalid inputs preserve current work; restored finalized plans remain finalized only if references and selection validate.

## 8. Interface Specification

Use a clear native Streamlit single-page layout with sidebar, readable contrast, text labels, and expandable source/evidence sections. No elaborate custom components are needed.

| Area | Controls and feedback |
| --- | --- |
| Workspace | Name, Save, Reopen file, unsaved changes, New plan retaining sources, confirmed New empty workspace. |
| Plan setup | Name, Week/Campaign, five/seven or optional target, optional audience/goal. |
| Sources | Multi-file selector, Add documents, metadata/warnings, protected removal, inspector. |
| Generation | Generate, Find more, Retry, slots/batch size, busy and no-new-topic feedback. |
| Review | Available/selected/excluded topics, select/deselect/exclude/restore, evidence, ordering and days. |
| Finish | Ready status, shortfall acknowledgement, explicit Finalize, both reports, explicit Reopen for editing. |

Day labels may precede dates until Step 11. Disclose local reading versus Gemini transmission before generation and extracted-content inclusion before saving. Enforce busy guards in workflow as well as controls. Confirm destructive reset/load with unsaved work, not every routine edit.

## 9. External Service and Model Choice

The user-authorized chain is Gemini 3.6 Flash as primary, Groq openai/gpt-oss-120b as direct fallback, then Gemini 3.8 Flash as reserve. Local configuration provides GEMINI_API_KEY, GEMINI_MODEL, GEMINI_FALLBACK_MODEL, GROQ_API_KEY and GROQ_MODEL. The two Gemini models share a key. Never export these credentials. Disclose potential transmission of the same extracted sources, brief and remembered angles to both services before generation.

Each route is attempted at most once, with the existing one temporary-error retry budget reserved for primary Gemini. Groq and the reserve do not add retries. Operational/access/quota/timeout/schema/context failures can advance; valid zero-topic results, refusals and local evidence rejection cannot. A known authentication/configuration failure skips remaining routes sharing that provider. Report a safe successful model label; total failure retains all prior work. Context is checked without truncation; Groq uses a conservative byte bound against its documented model budget. No new SDK is required.

Use google-genai with an account-accessible Gemini model and a tested compatible schema. The historical Gemini 2.5 Flash choice is not a current availability promise. At Step 10 verify model ID/capabilities/pricing/quota/date checked and full token budget through official documentation, including [structured output](https://ai.google.dev/gemini-api/docs/structured-output) and [token counting](https://ai.google.dev/gemini-api/docs/tokens).

Include instructions, sources, brief, retained/excluded summaries, and response allowance in budget checks. Use bounded timeout and at most one automatic retry for temporary errors, honoring provider guidance. Invalid credentials, inaccessible models, schema incompatibility, and nonrecoverable quota exhaustion need correction rather than blind retry. Keep a manual retry path. No automatic billing changes. The user-authorized bounded provider chain uses Gemini 3.6 Flash, then Groq GPT-OSS 120B, then Gemini 3.8 Flash. Structured outputs and conservative generation settings cannot guarantee factual truth.

## 10. Initial Limits and Processing Policy

| Setting | Initial policy |
| --- | --- |
| Week target | Five or seven selected topics. |
| Campaign target | Optional positive whole number; no fixed product-wide total ceiling. |
| Batch ceiling | Ten candidates per request; open campaigns can choose one to ten. |
| Fixed-target batch | Minimum of vacant selected slots and batch ceiling; no request with zero vacancies. |
| Single input file | 10 MiB, or 10,485,760 bytes. |
| Source pool | 20 files and 50 MiB total original input bytes. |
| Tabular preview | First 100 rows per table/sheet; full loaded table supports summaries. |
| Source-context guard | 400,000 characters, separately from provider token limits. |
| Workspace import | 20 MiB maximum, with independent restored-source/reference validation. |
| Snapshot collections | 10,000 topic records/selections/exclusions as a save/load resource guard, not a plan target or ten-topic total cap. |
| Extraction expansion | 100 MiB uncompressed Office archives and 1,000,000 table cells; reject excess rather than truncate. |
| API timeout/retry | Initially 60 seconds where SDK supports it; at most one automatic temporary-error retry. |

Shared limits belong in config/settings.py. Keep framework upload settings consistent and apply the larger workspace-file allowance only to its dedicated loader, retaining the 10 MiB source guard independently. Resource guards may block large requests/workspace files but are not a hidden total campaign-topic ceiling. Never truncate saving, loading, export, or request content silently. Existing valid work remains reviewable/exportable/saveable when generation exceeds context limits; explain when a smaller separately saved workspace is needed.

Processing order: validate plan/action/input; reserve request data; assemble/check context; request candidates; validate/merge; record successful request; recompute readiness; release transient busy state. Failure preserves pending data. New plan and New workspace are distinct operations.

## 11. Errors and Recovery

| Condition | Outcome |
| --- | --- |
| No readable sources | No request; explain suitable inputs. |
| Empty/corrupt/unsupported/oversized file | Per-file feedback, retain other additions. |
| Duplicate content/name conflict | Skip duplicate or require renamed content; never overwrite evidence. |
| Partial PDF, CSV fallback, missing formula cache | Visible warning, no invented recovery values. |
| Pool/context/provider budget exceeded | Block affected operation with totals/remedy, no truncation. |
| Invalid target/date/mode or excess selections | Explain and retain previous valid state until conflict resolved. |
| Zero or no-new-topic success | Keep earlier work, explain evidence limits and deliberate next actions. |
| API/configuration failure | Preserve data and retry eligibility; explain correction. |
| Busy double-click or rerun | No concurrent or accidental request. |
| Selection exclusion/removal | Recompute readiness and weekly vacancies. |
| Invalid/future/oversized workspace | Reject wholly; preserve current memory and unsaved status. |
| Destructive reset/load | Confirm unsaved replacement and offer saving first. |
| Session loss | Reopen latest saved file; unsaved changes may be lost. |

Log safe operation categories, timing, metadata, and sanitized errors. Do not log keys, entire prompts/sources/workspace contents, or raw sensitive provider responses by default.

## 12. Configuration and Secrets

The root .env is explicitly listed in .gitignore; .env.example stays safe and trackable. Both Gemini and Groq keys belong only in local configuration. This folder currently has no Git repository, so ignore rules can be inspected but index/tracking status is not asserted.

The ignored root .env is an application settings file, not a Python environment. Load key/model settings without displaying values. Keep .env.example safe and ignore real secrets, real uploads, and generated workspace snapshots in version control while retaining fictional fixtures. Credentials, provider execution settings, and filesystem paths cannot be imported from workspace files. Plan changes cannot enable billing or alter credentials.

## 13. Setup and Current-State Guide

Use the approved interpreter and existing root, add missing packages only as steps need them, and launch web_app/app.py from the root. Give exact commands in the teaching conversation; README explains purpose/startup/current limitations without runnable snippets.

The current Streamlit V1 entry remains web_app/app.py. The complete-build request explicitly authorized continuous execution through the revised sequence without intermediate readiness stops. The implementation record is in docs/PROGRESS.md; remaining live/manual checks must not be reported as completed. V2 remains future and unimplemented.

## 14. Step-by-Step Learning Plan

Preserve Steps 1 and 2 as history and the dependency-aware sequence below as the learning/build map. The 17 October complete-build request overrides intermediate pauses for this implementation. Future teaching follows the learner’s current pace. Explain goals, responsibilities and observed checks; do not claim that an unasked checkpoint was answered. Within stages keep responsibilities understandable.

### Step 1 — Global runtime and first page; historical

Goal/concept: selected interpreter, dependencies, Streamlit reruns. Built initial files. Verified base Python and fictional sample page. Checkpoint: why can packages differ by interpreter, and what reruns after an interaction? Optional: change a label. Suggested commit: Initialize global dependency records and basic Streamlit interface.

### Step 2 — Session and pools; historical

Goal/concept: session memory, fingerprints, early topic rules, revisions. State/topic modules and tests were verified on 15 October under previous scope. Checkpoint: what must survive reruns and why leave failures pending? Optional: add a duplicate. Suggested commit: Add campaign state and pool management. The old total topic ceiling and related tests are historical, not expanded acceptance.

### Step 2R — Revise workspace and mode rules

Goal: separate reusable workspace from active plan. Learn target versus batch versus library counts. Add plan_manager.py/tests; revise state/topic/settings/UI for names, brief, five/seven, optional campaign target, stable topic IDs, reset distinctions, and explicit round/request tracking. Keep fictional records clearly labelled.

Verify independent sessions, campaign capacity above ten and open target, target conflicts without lost records, failed retries, new explicit rounds on unchanged sources, and no requests on rerun. Replace superseded tests rather than preserving the old rule. Checkpoint: why is a ten-candidate batch compatible with a twenty-topic campaign? Optional: inspect a seven-to-five conflict. Suggested commit: Revise state for weekly and flexible campaign plans.

### Step 3 — Simulated review, finalization, and Markdown

Goal: verify the plan journey before network integration. Learn library versus selected/excluded records, readiness versus approval, and formatting versus workflow ownership. Add planning_service.py, markdown_exporter.py, focused tests, and controls for select/deselect/exclude/restore/order, shortfalls, explicit finish and reopen.

Verify zero, short, exact-target, and open-campaign flows; above-ten total across batches; exclusion suppression; fixed-target vacancies; retained earlier topics; no automatic finalization; selected-only ordered reports. Weekly slots can have day labels without dates. Checkpoint: why distinguish selection from exclusion? Optional: download a fictional short plan. Suggested commit: Add simulated planning review and Markdown export.

### Step 4 — Word extraction

Goal/concept: ordered body paragraphs/tables and traceable locations. Add reader, fictional DOCX, and tests. Verify empty/corrupt data, nonempty content, reading order, tables and limitations. Checkpoint: what is lost when reading only paragraphs? Optional: add a table row. Suggested commit: Add Word extraction and learning fixture.

### Step 5 — CSV and Excel extraction

Goal/concept: full summaries versus bounded previews, sheets, encodings, stored formulas. Add shared reader, fictional CSV/XLSX, tests and required missing libraries. Verify sheets/dimensions/row locations, summary correctness, missing values, empty/text/numeric tables, preview limits, decoding notes and formula warnings. Checkpoint: why are first rows not the complete dataset? Optional: add rows beyond preview. Suggested commit: Add spreadsheet and CSV extraction.

### Step 6 — PDF extraction

Goal/concept: selectable text, page provenance, layout/scanned limitations. Add reader, fictional PDF and tests. Verify multiple pages, corrupt/image-only/partly-readable data, no false readable content from headings, and resource closure. Checkpoint: why does a scan require another technique? Optional: compare page and extraction. Suggested commit: Add PDF extraction and page provenance.

### Step 7 — Routing, context, source inspection

Goal/concept: routing selects a reader; context assembly preserves evidence across readers. Add router/context builder/tests and real uploads through coordinator. Verify mixed files, duplicate/name conflicts, readable-content checks, source protection, complete context blocks, limits without truncation, and parsing without Gemini. Checkpoint: where would a new format plug in? Optional: uppercase extension. Suggested commit: Connect document routing and source inspection.

### Step 8 — Validated data contracts

Goal/concept: schema checks versus factual support. Add topic/evidence, result, plan, workspace Pydantic models/tests; align ordinary early records. Verify zero results, per-batch bounds, optional targets, more-than-ten library, required fields/lengths, stable IDs/references, invalid slots and source structures. Checkpoint: what needs source-aware checks beyond a schema? Optional: remove a required field. Suggested commit: Add validated topic plan and workspace models.

### Step 9 — Prompt assets and request assembly

Goal/concept: stable grounding rules versus changing workspace/brief data. Create actual prompt files/builder/tests only now. Cover source quality, zero results, facts versus editorial suggestions, existing insight/evidence summaries, exclusions, brief, mode and capacity, and untrusted embedded instructions. Verify initial/additional assembly and source/response budgeting inputs without live calls. Checkpoint: why send more than previous titles? Optional: compare two assembled requests. Suggested commit: Add grounded planning prompts and request builder.

### Step 10 — Gemini and evidence-aware recovery

Goal/concept: external failures, source checks, request identity. Add provider/generator/validator/tests, configure key, verify account-accessible model/schema/token/quota/pricing, and connect bounded retries/explicit rounds. Remove all fictional UI controls from the final interface.

Verify key-free fake-provider failures and invalid evidence, live grounded fields/distinctness/capacity, zero/no-new handling, additional rounds, no accidental rerun requests, and retry without data loss. This is live integration, not completion of added export/storage features. Checkpoint: trace source to accepted topic; what verifies structure versus support? Optional: inspect one suitable real document. Suggested commit: Connect Gemini generation with evidence-aware recovery.

### Step 11 — Weekly day/date controls and CSV

Goal/concept: calendar labels versus posting, shared export selection. Add CSV exporter/tests and finish day assignment/reorder/swap/optional Monday dates; align Markdown. Verify five/seven slots, unique assignments, short empty slots, dates crossing month/year boundaries, matching order/counts/evidence, Unicode/commas/newlines, and spreadsheet formula-like text. Checkpoint: why are dates separate from automatic posting? Optional: move a topic and inspect both reports. Suggested commit: Add weekly planning dates and CSV export.

### Step 12 — Save and reopen

Goal/concept: persistent snapshots versus session memory, versioned contracts, atomic validation. Add storage/workspace_store.py/tests and controls for explicit download/reopen/unsaved changes. Verify draft/finalized round trips after restart, IDs/evidence/exclusions/order/brief/dates, corrupt/oversized/future files, invalid references, busy reset, credential exclusion and replacement protection. Checkpoint: how does a workspace file differ from a public report? Optional: reopen a fictional draft. Suggested commit: Add validated workspace save and reopen.

### Step 13 — Full acceptance and learning review

Goal: validate the whole expanded product and align records. Run relevant full tests and Section 15 checklist, fix demonstrated failures, record live/manual/pending checks honestly. Checkpoint: trace one uploaded file through generation, user review, both exports and reopening. Suggested commit: Verify expanded Version 1 planning workflow.

### Feature coverage

F1–F3: Steps 2R and 4–7. F4–F5: Steps 2R, 3, 8–10. F6–F8: Steps 2R, 3, 8–10. F9: Steps 3/11. F10: Steps 3/8/10/11. F11: Step 11. F12: Steps 8/12. Step 13 checks every feature.

## 15. Testing and Acceptance

Keep pure rules deterministic and independent of Streamlit. Use fake provider results for exact transitions/failures; automated checks need no API key or live quota. Do not prescribe a permanent test count. Retain useful historical tests but replace assertions enforcing superseded rules.

| Area | Important checks |
| --- | --- |
| Workspace/state | Independent sessions, duplicate/name rules, limits, busy guards, explicit rounds, retries, reset distinctions. |
| Plan/review | Five/seven, optional target, library above ten, selection/exclusion/restore, no silent mode-switch losses, shortfalls, readiness versus finalization. |
| Readers/context | All formats, empty/corrupt/partial data, summaries/locations/previews, no silent truncation. |
| Generation | Schema, source/quote/location membership, duplicates/exclusions, bounded batch, retained earlier work. |
| Dates/reports | Order, optional dates, weekly gaps, evidence, CSV quoting/Unicode/formula neutralization, selected-only export. |
| Persistence | Version/size/ID/reference rules, complete round trip, invalid load preserves work, transient reset, finalized validation, no credentials. |

Manual final checklist:

- [ ] Launch through approved global Python; inspect modes, names and brief.
- [ ] Add all formats; inspect evidence/warnings; exercise duplicates and name conflicts.
- [ ] Generate five/seven weekly plans and verify each factual claim against evidence.
- [ ] Use controlled fixtures for zero, shortfall, target readiness, and explicit finalization.
- [ ] Build a targeted campaign above ten across rounds and an open campaign without forced filler.
- [ ] Select/deselect/exclude/restore/reorder; verify suppression and source protection.
- [ ] Switch a larger selection to a smaller week without lost topic records or silent choices.
- [ ] Explicitly request another round from unchanged sources; reruns/busy clicks do not request.
- [ ] Fail/retry generation without losing documents or earlier topics.
- [ ] Assign days/dates, inspect empty slots, and compare Markdown/CSV values.
- [ ] Save draft/finalized work, restart/reopen, and inspect brief/sources/topics/exclusions/order/evidence.
- [ ] Reject corrupt/oversized/unsupported workspace files without replacing work.
- [ ] Confirm unsaved-change protection, extracted-content saving disclosure, and no embedded secrets.
- [ ] Verify New plan retains sources/library; New workspace clears only after confirmation.

Live counts vary. Evaluate live results by traceability, supported claims, distinctness and batch bounds, not an exact fixture count.

## 16. Implementation Conventions

Use descriptive snake_case functions/modules, PascalCase records/models, explicit type hints, four spaces, focused docstrings and approximately 100-character lines. Prefer clear loops/helpers to unnecessary inheritance. Comments explain consequential reasons. One concern per module; no empty future stubs or broad utilities folder.

Return useful data or clear errors at parser/workflow boundaries; UI renders messages. Log safe timestamps/categories and sanitized details. Use portable paths where practical, release resources, and avoid raw upload persistence. Provider/storage code must not mutate UI session memory. Type hints are not validation of imported data; external boundaries require runtime checks.

## 17. Documentation and Teaching Contract

DOCUMENT_SPEC.md controls explanation, progress and verification records. The authorized continuous build followed the dependency relationships beginning with Step 2R; no learner-readiness pauses were required during that request. Define unfamiliar terms briefly beside first use when teaching, connect reasons to a coherent example where helpful, and adapt depth to the question. Specifications contain no code, commands, sample JSON or actual prompts. README describes current capabilities rather than treating future scope as working.

## 18. Decisions in This Revision

| Decision | Reason/consequence |
| --- | --- |
| Reusable workspace, one active plan | Reuse sources/topics without adding a history database. |
| Weekly five/seven, optional campaign target | Supports both short weekly planning and larger efforts. |
| Bounded batches without a fixed total ceiling | Controls requests while removing the old product restriction. |
| Explicit finalization | Reaching a target is not user approval; evidence shortfalls remain visible. |
| Selection distinct from exclusion | Keep alternatives reusable and remember unwanted angles. |
| Optional brief, ordering/dates, two reports | Make topics relevant and usable without writing or publishing posts. |
| Explicit local versioned snapshots | Continue later using current dependencies, with visible content/privacy limits. |
| Step 2R plus Steps 11–13 | Reconcile old implementation and teach added features in verified stages. |

## 19. Risks and Gotchas

No fixed total does not mean unlimited memory, quota, context, or distinct ideas. Matching quotes and schemas do not prove causal reasoning. Normalized text comparisons miss paraphrases. Extra sources or a brief cannot guarantee a target. Session memory is temporary; saved files contain extracted content and are not encrypted. Imported fingerprints do not authenticate original bytes. Preview limits, encodings and stored formula caches affect evidence. Use pymupdf rather than the unrelated fitz package and google-genai rather than incompatible older SDK examples. The earlier preview’s old total cap was replaced; preserve regression checks against reintroducing it.

## 20. Future Extensions

Keep OCR, full posts, images, automatic publishing, cloud sync, multi-user collaboration, automatic history/version browsing, and vector retrieval parked until a demonstrated need and explicit scope change. Describe owner, benefit, exposure, dependencies, learning concept and verification before building. Save/reopen, CSV, manual weekly planning, naming, brief, selection and ordering are Version 1 requirements, not future-only suggestions.

## 21. Glossary

| Term | Meaning |
| --- | --- |
| Workspace | Reusable sources, topic library, exclusions, active plan and records. |
| Plan | Named ordered topic selection in Week or Campaign mode. |
| Target | Desired selected count, never permission for filler. |
| Batch | Bounded candidate group requested by one explicit action. |
| Candidate | Proposed idea needing local acceptance and user review. |
| Selected | Retained topic included in the active plan. |
| Excluded | Retained angle deliberately avoided unless restored. |
| Grounding | Basing factual claims on supplied traceable evidence. |
| Revision/request identity | Records distinguishing changed data and explicit rounds from reruns. |
| Persistence | Keeping work beyond a session through explicit saving. |
| Snapshot/schema version | Complete saved working record and its identified validation format. |
| Ready/finalized | Review condition versus explicit user completion. |

## 22. Defaults and Checks During the Build

Default to Week with five slots; Campaign defaults to no target until enabled. Names have editable defaults; audience/goal/date are optional. Dates require a Monday start. Open-campaign batch defaults to ten, adjustable one to ten. These count rules are distinct from resource limits.

Recheck interpreter/packages before relevant changes; reader behavior against installed versions; model/schema/quota/token/pricing at Step 10; CSV in the user's Excel at Step 11; saved evidence/reference round trips at Step 12. Limits are initial operational defaults, not guarantees of arbitrary capacity. Record justified adjustments with tests.

The 17 October 2026 complete-build request authorizes implementing this scope continuously. The application now contains the expanded features; docs/PROGRESS.md distinguishes tested implementation from pending live/manual checks.
