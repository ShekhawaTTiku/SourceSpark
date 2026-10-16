# Known Limitations

This document separates intentional V1 boundaries from environmental verification gaps. [PROGRESS.md](PROGRESS.md) is the current record of checks, failures, and any remaining implementation work. Passing deterministic tests does not remove these practical limits.

## Product boundaries

- The application is local and single-user. It maintains one active plan in one workspace, without accounts, collaboration, a database, or cloud synchronization.
- Session state survives ordinary reruns but is not permanent storage. Saving/reopening is explicit; there is no background autosave, recovery archive, or automatic plan-history browser.
- Starting a new plan retains reusable sources/topics/exclusions but replaces the active plan. Preserve a former plan in a downloaded snapshot before replacing it if it will be needed again.
- Topic plans are planning material. Full post writing, images, automatic publishing, scheduled posting, and social-account integration are outside V1.
- Week mode uses five Monday–Friday or seven Monday–Sunday slots, with an optional Monday start date. It is not a calendar integration or a configurable recurring schedule.
- A topic target is a desired selection size, not a promise that the evidence supports that many distinct ideas. Open campaigns can still exhaust useful source material.

## Extraction limits

- PDF reading requires selectable text. Scanned/image-only material needs OCR, which is not implemented. Multi-column layout and tables may extract in an imperfect reading order.
- Word extraction reads body paragraphs and table cells. Images, headers/footers, text boxes, embedded objects, and layout-dependent meaning are not interpreted. Merged table cells can repeat text.
- Excel reading uses cell values and stored formula results. The application does not calculate formulas or interpret charts, images, formatting-derived units, or embedded objects. Stored results may be missing or stale. Hidden sheets are included with warnings.
- Spreadsheet/CSV summaries use all loaded data rows, while only a bounded preview of individual rows is available as row evidence. Later individual rows cannot be quoted unless they are included through a suitable separate source. Summaries describe values; they do not establish causes.
- Header detection expects the supported rectangular-table structure. Messy reports, mixed numeric/text fields, irregular sheets, and meaningful formatting need user inspection; the parser does not infer a complete data model.
- Fallback CSV decoding is disclosed. Legacy encodings may still need re-export to UTF-8 for reliable interpretation.
- Oversized files, Office archive expansion, excessive tables/locations, empty material, and unreadable structures are rejected rather than silently trusted or truncated.

## Evidence and generation limits

Schema validation checks structure, source validation checks traceability, and conservative factual checks catch some obvious overreach. None proves that every interpretation is correct or relevant. A real quotation can still be misused. Users must review scope, units, dates, legal statements, causal reasoning, and audience fit before publication.

Repeated-angle detection uses normalized text and wording similarity, plus remembered titles/insights/context in the provider request. It does not provide perfect semantic comparison. It can miss paraphrases or reject closely worded ideas that a human would distinguish. Exclusions improve history awareness without guaranteeing suppression of every rephrased angle.

The brief guides the provider but has no authoritative factual status. Local acceptance cannot perfectly assess compliance with an audience or communication goal. It is deliberately conservative rather than a substitute for editorial review.

Generation requires internet and sends extracted sources, the brief, and remembered topic information to Gemini, and may send the same material to Groq during configured failover. Parsing and planning are local, but the overall product is not completely offline. Provider access, quotas, response behavior, and costs depend on the configured account/model.

## Resource boundaries

Central settings provide the operative values. Current guards include ten MiB per source, twenty sources, fifty MiB total recorded original-source sizes, four hundred thousand extracted/request characters, bounded Office expansion/table cells, and ten candidates per request. Provider model/token budgets add a separate check.

There is no global ten-topic campaign ceiling. Campaigns can exceed ten across requests, subject to evidence and resources. A saved snapshot is bounded to twenty MiB and ten thousand topic records as import/export resource safeguards. A large library can hit complete-context limits before those snapshot limits, because all remembered angles must remain available rather than being silently forgotten.

## Snapshot and report limits

Workspace files contain extracted source text and may contain private information. They are unencrypted. Keep them appropriately protected. The application intentionally excludes raw originals, credentials, environment configuration, provider clients, and arbitrary execution/path settings.

Only schema version 1 is supported. Unsupported versions are rejected; there is no migration mechanism. The loader validates internal consistency but cannot authenticate facts or prove that a fingerprint matches original bytes absent from the snapshot.

Reopening restores extracted content and metadata, not the raw PDF/DOCX/XLSX/CSV bytes. It cannot recalculate a workbook, rerun extraction, or reproduce unsupported content from those absent originals.

CSV is a planning table, not an XLSX workbook. It preserves Unicode, multiline fields, and order, and protects formula-like values with an apostrophe. Exact display can differ between spreadsheet programs. Markdown reports contain evidence excerpts, not an archive of entire documents.

Changing or reopening a finalized plan invalidates current export eligibility. Previously downloaded reports remain on the user's computer and cannot be revoked or automatically updated.

## Environmental verification gaps

The initial complete-build verification used mocks because credentials were absent. Keys have since been configured and live verification is recorded in PROGRESS.md. Controlled fallback failures are simulations even when the destination provider is live. A few successful calls do not establish future quota, free-tier eligibility or universal factual quality.

In-process Streamlit checks are not visual browser inspection. Automated CSV parsing is not a manual check in the user's Excel installation. Consult PROGRESS for which of those checks were actually performed; do not infer them from successful unit tests.

No product feature should be labelled unfinished solely because it needs account credentials to run, but unperformed live verification must remain explicit. Any actual unresolved implementation failures belong in PROGRESS with their impact.


## Latest provider verification limits

Live Gemini 3.6 Flash primary and Groq GPT-OSS 120B fallback checks now pass with
small fictional sources through finalization, reports and workspace reopening.
The reserve Gemini 3.8 Flash has returned HTTP 503 during generation, despite
working metadata and token endpoints. Its success remains unverified; its route
is covered by deterministic tests. Live availability can change at any time.

Fallback may send the same evidence to Groq as well as Google. It is bounded,
disclosed and restricted to operational/schema failures. It does not weaken local
evidence acceptance or chase another model after a refusal. Large requests can
fail Groq's conservative byte-based context guard even when they might fit an
exact tokenizer count; nothing is truncated. No free-tier/billing entitlement is
guaranteed by the app. Users manage keys, permissions, quotas and provider accounts.
