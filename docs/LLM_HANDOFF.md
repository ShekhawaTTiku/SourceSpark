# LLM Maintenance Handoff

This document gives another coding assistant enough context to investigate the project without relying on the conversation. Verify mutable details against current source and [PROGRESS.md](PROGRESS.md); do not infer implementation or passing checks from requirements text.

## Purpose, authority, and scope

SourceSpark is a local single-user Streamlit V1 application. It turns PDF, DOCX, CSV, and XLSX evidence into topic ideas, then supports reusable libraries, five/seven-day weekly plans, optionally targeted/open campaigns, explicit review/finalization, reports, and private workspace snapshots. It produces planning topics, not finished posts.

Current user instructions override earlier teaching pace. PROJECT_SPEC.md owns product behavior and the revised Step 2R through Step 13 build sequence. DOCUMENT_SPEC.md owns documentation/learning rules. The historical seven-to-ten-topic campaign-only implementation is superseded. The user's complete-build request authorized continuous implementation without learning-stage pauses.

V1 remains in web_app because that is the established Streamlit entry point. There is no V2 frontend, separate server, database, auth, OCR, cloud sync, vector retrieval, automatic publishing, or scheduled posting. Do not add those as incidental refactors.

Use the existing global Python 3.11.9 installation identified in PROJECT_SPEC and dependency_notes. Do not create an environment or use an unrelated terminal-default interpreter. The ten direct dependencies remain Streamlit, google-genai, Pydantic, PyMuPDF, python-docx, pandas, openpyxl, tabulate, python-dotenv, and pytest. Check installed versions and actual compatibility before changing them.

## Actual ownership and implementation

Read [CODEBASE_MAP.md](CODEBASE_MAP.md) for the full map. The main trace is web_app/app.py → views.py → workflow/planning_service.py → document readers or ai/topic_generator.py → validated merge → plan_manager → exports/storage. Interface code collects actions; core owners enforce rules.

workflow/state_manager.py defines commit, idle/editable guards, source creation/add/remove, workspace rename, new plan, and reset. commit builds a full candidate Workspace, updates modified time, validates, then replaces the existing object's working fields. Other workflow owners should use it for durable changes. Busy is transient and released in finally after generation.

workflow/plan_manager.py owns configure_plan, selection/deselection, exclude/restore, move_topic, assign_day, finalize_plan, reopen_plan, and batch_capacity. New plan retains libraries and exclusions but replaces the single active plan. A new workspace replaces everything only after UI confirmation.

## Data contracts to verify before edits

All models forbid extra fields. Pydantic validates construction and boundary rebuilds; assignment validation is intentionally not enabled. Do not assume a mutated model instance has been revalidated merely because its type is correct.

| Model | Important contract |
| --- | --- |
| EvidenceReference | document_id is 64 lowercase hexadecimal characters; exact filename, location, and excerpt identify support. |
| TopicCandidate | Title 5–120 characters; core_insight 20–500; descriptive context 20–1200; nonempty audience/format; one to ten distinct evidence references. |
| TopicIdea | Adds stable application-generated 32-hex topic_id and generated/sample origin. |
| GenerationResult | Zero to ten candidates and sufficiency_note of 1–1000 characters. |
| DocumentRecord | Safe basename, lower-case supported extension without dot, original byte size, content, locations, warnings, participation; no raw binary. content exactly matches the canonical location-block construction. |
| Plan | Stable ID/name, Week/Campaign, five/seven days, optional campaign target, brief, ordered selections, day assignments, optional Monday date, state, acknowledgement, finalization time. |
| Workspace | Stable ID/name, sources, topic library, exclusion IDs, active plan, busy, pool_revision, request_round, last_successful_request, note/feedback, timestamps. No provider/client/secret fields. |

DocumentRecord exposes character_count and content_characters for inspection. Source fingerprints derive from original bytes at ingestion; imported fingerprints do not authenticate absent raw originals.

Plan effective_target is weekly_days for Week, otherwise optional target. remaining_slots is None for open campaigns or a nonnegative vacancy count. Week selected IDs must exactly match assignment values sorted by day index, with Monday at index zero. Gaps are valid. An optional Monday start must leave the entire week inside Python's representable calendar, including at the upper date boundary. Campaigns have no day assignments/date. Duplicate selections and selections beyond a fixed target are invalid.

Readiness derives from selection: filled fixed targets or a nonempty open campaign are READY_FOR_REVIEW. Other editable plans are DRAFT. FINALIZED requires a nonempty selection, timestamp, and acknowledgement when shorter than target. Nonfinalized plans cannot retain finalization metadata. Reaching a target never finalizes.

Workspace validates unique source/topic identities, case-insensitive source-name uniqueness, source counts/sizes, selection/exclusion membership and disjointness, evidence relationships, and canonical extraction. Imported evidence excerpts must match location text with whitespace-equivalent matching; live generation uses actual excerpt occurrence. Structural evidence checks do not establish complete factual entailment.

## Ingestion and context

file_router.parse_uploaded_file accepts a filename and bytes and returns DocumentRecord. Shared ExtractionResult/ExtractionError live in documents/extraction.py. DOCX body paragraphs/tables, selectable PDF pages, and CSV/XLSX tables follow their owning readers. Bad files receive independent feedback; accepted earlier files remain.

Tabular summaries use every loaded data row, while at most the configured hundred individual preview rows become row evidence. Formula cells use cached values; missing caches are missing, not zero. XLSX hidden sheets are included with warnings. Office archives and table sizes have resource guards.

context_builder.build_context emits the complete eligible evidence or raises; no silent truncation. prompts/builder.build_request adds real prompt assets, full brief/mode/capacity, all retained/excluded topic context, and all evidence. Prompt text belongs only under prompts, never copied into documentation.

## Generation, distinctness, and recovery

planning_service.generate_batch is an explicit operation. It checks editability/sources/capacity, fingerprints source revision plus brief/mode/target/prior topics/exclusions/round, reserves busy, calls generate_topics, then atomically merges accepted records and vacant selections. Success including zero accepted consumes a round; failure preserves previous work and retry eligibility. Routine reruns and non-generation actions must not call it.

ai/topic_generator accepts an optional provider implementing generate with prompt and capacity. Tests inject providers rather than depending on credentials. Its result is a ValidatedBatch with candidates, feedback, and sufficiency note. The coordinator, not the provider, assigns topic IDs and changes workspace state.

GeminiClient requires GEMINI_API_KEY and an account-accessible GEMINI_MODEL from local configuration. It obtains model metadata and counts full prompt/schema tokens with a response allowance before requesting structured JSON output. SDK transport retries are disabled. One automatic retry budget is shared across provider operations for eligible temporary failures; timeouts, permanent quota/access failures, long requested delays, and malformed output remain manual recovery paths. GenerationError exposes safe category/message and retryability rather than raw provider text.

response_validator checks evidence membership/excerpt, conservative numeric/unit/scope/causal guards and factual word overlap. topic_pool normalizes wording and uses practical similarity comparisons, retaining exclusions as prior angles. These checks cannot promise semantic deduplication or correct reasoning. Do not weaken evidence to fill a target.

## Snapshot schema and reports

storage.save_workspace returns UTF-8 JSON bytes with schema_version 1, saved_at, and a complete workspace record. load_workspace accepts bytes and returns a separate validated Workspace. It never installs state. The UI handles replacement confirmation and replaces memory only after successful validation.

The loader rejects unsupported versions, malformed UTF-8/JSON, duplicate object keys, nonstandard constants, unknown/missing fields, unsafe filenames, inconsistent evidence, invalid selections/exclusions/slots, and invalid finalization. It resets busy after loading. It never evaluates text, imports classes, opens named paths, or uses object deserialization. There is no speculative migration layer.

Snapshots are limited to twenty MiB and ten thousand topic records, with source/text/collection guards. The topic-record guard is a persistence resource boundary, not a ten-topic campaign ceiling. Saved extracted content is private and unencrypted. No raw originals, secrets, environment objects, prompts, raw provider responses, or client objects are saved.

Exports revalidate a full workspace and require a nonempty finalized plan. Shared row construction preserves selected order and every weekly slot; optional dates derive from a Monday only. Markdown is standalone. CSV uses csv.DictWriter, UTF-8 with a byte-order mark, and formula-like-cell neutralization. Reports include selected context/evidence/warnings rather than the whole library/source contents. Drafts after reopening cannot create current finalized exports.

## Tests and current verification limits

Inspect the tests directory and PROGRESS for exact executed results. Meaningful coverage includes plan lifecycle, above-ten campaigns, source retention, exclusions, API errors/retry, reader fixtures, context overflow, batch validation, exports, and transactional late-failure loading. Streamlit in-process interaction checks are different from browser visual review; mocks are different from live Gemini calls.

No usable live account credential/model was available during the complete-build verification. Do not claim live generation, account quota/pricing eligibility, or human factual quality were verified. Review KNOWN_LIMITATIONS for current environmental gaps. Automated tests do not demonstrate learner understanding.

## How to investigate and change safely

First reproduce the failure with the approved interpreter and smallest fictional fixture. Trace the owning boundary and identify observed behavior versus hypothesis. For data problems, inspect safe metadata and validation categories; never print credentials, full private documents, or snapshot contents into logs.

For a feature, compare current user intent with both governing specifications, determine ownership, and preserve stable identities and reusable material. Add focused regression coverage for the changed behavior. Exercise the integrated path when the change crosses boundaries. Run the relevant suite and existing required checks, then broaden only for failures or new risks.

Keep PROJECT_SPEC and README aligned when behavior changes. Record significant choices in DECISIONS, actual checks/gaps in PROGRESS, dependency changes in dependency_notes, and update the affected guide/map/handoff. Do not paste commands, implementation snippets, example JSON, configuration contents, or real prompts into these documents. The teaching conversation can supply launch/check commands when needed.

Never restore the obsolete global ten-topic limit, automatic finalization, campaign-only memory model, or source-revision-only eligibility. Do not replace a recoverable failure with a workspace reset. Do not treat a documented feature as evidence it has been tested.

## Configured provider chain

The user-approved order is Gemini 3.6 Flash, then Groq openai/gpt-oss-120b, then
Gemini 3.8 Flash as reserve. ai/provider_chain.py owns lazy ordered attempts,
operational failure categories, invalid-key family skipping and safe route feedback.
ai/groq_client.py uses the Python standard library HTTPS stack with a fixed Groq
endpoint, redirect blocking, response-size guard, timeout and no hidden retries.
No new package was installed. Gemini's primary retains at most one temporary retry;
the reserve receives a zero retry budget. Do not multiply retry loops by adding a
retrying SDK around this chain.

The Groq structural JSON Schema preserves property names such as title while
removing provider-unsupported annotation constraints; full Pydantic validation
still applies afterwards. Gemini inlines supported structural schema fields to
avoid legacy additionalProperties serialization errors. Neither provider adapter
weakens local evidence checks. Live tests and their current limitations belong in
PROGRESS.md, not inferred from schema conversion alone.

Groq's GPT-OSS 120B adapter has a 131,072-token documented context and 65,536-token
output limit. Before transmission it conservatively bounds input using UTF-8 bytes,
schema and framing plus response allowance. This can reject otherwise token-fit
requests; it is intentionally not presented as an exact tokenizer count. Nothing
is truncated. An operational context failure can proceed to the Gemini reserve.
Blocked/refused or locally unsupported responses do not cause model hopping.

Keys are read from local configuration and never saved in a workspace. Feedback
records safe provider/model labels only. No account/model/pricing permission is
inferred from a successful unrelated endpoint or a mocked test.
