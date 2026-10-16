# Documentation and Learning Specification

**Version:** 1 learning MVP — expanded scope  
**Revised:** 17 October 2026  
**Companion:** [PROJECT_SPEC.md](PROJECT_SPEC.md)

PROJECT_SPEC.md owns product behavior, architecture, data contracts, features and acceptance. This document owns teaching, documentation, dependency practice and working rules. Both govern the build. The original combined reference and previous campaign-only teaching rules are superseded.

This revision includes weekly and campaign plans, brief/naming, review/ordering, Markdown/CSV, and explicit local save/reopen. The subsequent 17 October complete-build request explicitly authorized one continuous implementation. Expanded modules and UI are now present; progress records own current evidence and pending live checks. Steps 1 and 2 remain historical and the revised sequence remains the learning map.

## 1. Purpose and Requirement Priority

Act as a patient senior engineer helping the learner build and understand a real application. Explain what each piece does, why it belongs there, and how to change it later. Completion requires working features and honest verification, not explanations alone.

Resolve requirements in this order: current user instructions and explicit pace/scope changes; PROJECT_SPEC.md; this learning contract; historical reference material. Do not preserve conflicting old folder names, package pins, environment setup, prompts, topic caps or automatic-finalization rules.

The current product has a reusable workspace with one active named Week or Campaign plan. A five/seven target or optional campaign target is not a generation guarantee. A batch limit is not a campaign total limit. Ready for review is not finalized. These distinctions must remain consistent in teaching and records.

## 2. What Documentation Contains

Include purpose, scope, responsibility, user actions, validation/evidence/recovery behavior, learning goals, checkpoint questions, observed checks, known limitations, and reasons for significant decisions. Names of files, packages and fields may be used when they clarify ownership.

Do not include implementations, pseudocode, terminal transcripts, example JSON or actual AI prompts in specifications, progress or decision notes. Create implementation in its owner and actual prompts in prompts/ at Step 9. The 17 October SourceSpark publishing request authorizes practical setup, configuration, launch and test examples in README.md and the teaching conversation so a reader can run the project independently. Keep real credentials out of all examples.

Documentation must distinguish requirement, planned work, implemented behavior, simulated data, live service results, and verified behavior. Do not describe a future save/load feature as implemented session persistence. Do not claim a browser visual check from an in-process check or a live AI result from a fake provider.

## 3. Document Ownership

| Document | Responsibility/update |
| --- | --- |
| PROJECT_SPEC.md | Product/architecture/data/build/acceptance; revise on agreed scope changes. |
| DOCUMENT_SPEC.md | Teaching/documentation/dependency rules; revise on agreed learning changes. |
| README.md | Concise current introduction and plain-language setup/use/limitations; label pending scope. |
| docs/PROGRESS.md | Current stage, historical completions, actual checks, learner checkpoint, gaps and next step. |
| docs/DECISIONS.md | Dated meaningful choices, reasons, owners and verification where performed. |
| streamlit_setup/requirements.txt | Ten-library declaration and justified compatibility constraints. |
| streamlit_setup/dependency_notes.md | Selected interpreter, observed versions, impact and verification of changes. |

The required supporting guides live under docs/: PROJECT_GUIDE, CODEBASE_MAP, DATA_FLOW, LEARNING_GUIDE, LLM_HANDOFF, GLOSSARY, TROUBLESHOOTING, KNOWN_LIMITATIONS and DOCUMENTATION_INDEX. Each owns its stated purpose and links back to requirements/progress instead of duplicating the complete specification.

Do not create duplicate AGENT_RULES.md instructions or competing architecture/dependency maps. Historical decision entries may remain if dated and explicitly superseded by newer choices. Active requirements must be rewritten rather than contradicted by an appended note.

## 4. Existing Global Python Policy

Use C:\Users\GIGABYTE\AppData\Local\Programs\Python\Python311\python.exe, observed Python 3.11.9, consistently for installing, running and testing. The terminal's default previously pointed at ML311; an unrelated environment is not the approved interpreter. Do not create/activate virtual environments, Conda, containers or another Python.

Keep all ten libraries and their roles: streamlit UI/state, google-genai provider access, pydantic validation, pymupdf PDF, python-docx Word, pandas tabular processing, openpyxl Excel, tabulate Markdown tables, python-dotenv settings, pytest checks. Standard-library dates/CSV/JSON support weekly labels, CSV reports and local snapshots; there is no required new database/storage dependency.

Inventory the approved interpreter before relevant changes. The 14 October inventory and Step 1/2 additions are historical observations; dependency_notes.md is the implementation record. Retain working versions, install missing packages only as needed, and change versions for demonstrated compatibility/capability reasons. Inspect current requirements first and verify consistency and affected behavior afterwards. Record package, prior/resulting version, reason and observed checks. Do not freeze unrelated global packages, impose historical pins or upgrade everything.

Routine missing-package installs and limited compatibility corrections are within the approved policy. Explain consequential stack replacement or impact on other work and obtain a concrete choice if unresolved; do not silently use a new environment.

The root .env is a permitted configuration file, not an environment. Keep real secrets ignored and out of logs, documentation, exports, snapshots and teaching examples. Importing a workspace cannot override credentials/provider execution configuration or load arbitrary paths.

## 5. Architecture and Terminology

Maintain one Streamlit application with clear ownership:

| Owner | Responsibility |
| --- | --- |
| web_app/ | Collect actions/render results; delegates product rules. |
| streamlit_setup/, .streamlit/, config/ | Dependency records, framework settings, shared product/resource configuration respectively. |
| documents/ | Read formats, preserve locations/warnings, route files, assemble evidence context. |
| workflow/ | Workspace lifecycle, topic library/selection/exclusions, plan rules, explicit request eligibility and orchestration. |
| models/ | Validated topic/evidence, response, plan and saved workspace contracts. |
| prompts/ | Grounding assets and brief/mode-aware request assembly, created at Step 9. |
| ai/ | Provider communication, candidate generation and source-aware acceptance. |
| exports/ | Markdown/CSV formatting of finalized selected topics. |
| storage/ | Versioned bounded workspace file serialization and complete load validation. |
| docs/, sample_docs/, tests/ | Learning records, labelled fictional examples, meaningful verification. |

Use planning_service.py for the new coordinator; do not create the superseded campaign_service.py. Keep important concerns separate without splitting every tiny helper into a file. Avoid a miscellaneous utilities folder. Source/plan/persistence changes go through workflow coordination; providers/storage do not directly mutate UI state.

Teach these terms consistently: workspace is reusable sources/library plus one active plan; plan is selected ordered topics; campaign is a mode; exclusion differs from deselection; target differs from batch/resource guard; snapshot differs from public report. A finalized plan contains topic ideas, not finished posts. Weekly day/date labels do not implement automatic publishing.

## 6. Revised Build Sequence and Pacing

Follow PROJECT_SPEC.md Section 14 and its growth map. The earlier ten-step completion promise is replaced by completed Steps 1/2, revision Step 2R, and remaining Steps 3–13. Preserve the parser/model/prompt stage numbers so history and references stay understandable.

| Step | Focus | Teaching purpose |
| --- | --- | --- |
| 1, historical | Runtime and initial page | Interpreter and reruns. |
| 2, historical | Session/pool foundations | Memory, fingerprints, early revisions. |
| 2R | Workspace/plan modes, names/brief, IDs, target/batch rules, request rounds | Reconcile existing code before expanding behavior. |
| 3 | Simulated selection/exclusion/order, readiness/finalization, Markdown | Verify the complete planning decisions without a network service. |
| 4 | Word | Structured text/tables and evidence locations. |
| 5 | CSV/XLSX | Summaries versus previews and formula/encoding limits. |
| 6 | PDF | Pages, selectable text and missing extraction. |
| 7 | Routing/context/inspector | Connect extraction and verify what AI will receive. |
| 8 | Topic/result/plan/workspace models | Structure versus evidence and reference integrity. |
| 9 | Actual prompts and request assembly | Grounding, brief, mode/capacity, retained/excluded angles. |
| 10 | Gemini integration | Live service, validation, explicit requests and recovery. |
| 11 | Day/date assignment and CSV | Planning calendar and consistent reports. |
| 12 | Save/reopen | Versioning, durable files, private extracted content and atomic validation. |
| 13 | Complete acceptance | Verify the expanded product and learning outcomes. |

Complete the current step, explain actual results, and wait for the learner to say next or clearly indicate readiness before advancing. Checkpoint answers alone do not authorize progression. An explicit pace/combined-step request overrides this default; a broad instruction to build does not erase learning checkpoints. Routine actions within an authorized step do not need repeated permission.

Create each folder/file only when its stage needs it. Do not pre-create future placeholders or stubs; the complete-build request authorizes prompt and storage files when their stages are reached. Small necessary package markers are allowed when the package is introduced. Clearly identify simulations and remove fictional UI controls at Step 10; fictional test fixtures may remain explicitly labelled. Do not mark Version 1 complete at Step 10 when CSV and saving are still pending.

## 7. Teaching Each Step

Before implementation, state step number/title, goal, concept, exact affected files/responsibilities, dependencies on prior work, and observable success. Use three to six plain-language sentences for the core concept where helpful. State relevant limitations before the learner encounters them.

During implementation, explain inputs, outputs and ownership in small pieces. Use readable names/types/docstrings and comments explaining meaningful reasons. Connect decisions to user behavior: why excluded topics remain remembered, why a smaller mode cannot silently discard choices, and why evidence must survive a save/load cycle.

Adapt explanation depth to each question. Define new consequential terms briefly in brackets beside first use. If explaining several related mechanisms in depth, use one coherent fictional example and divide into parts when useful. Answer narrow follow-ups directly without repeating an entire earlier lesson. Do not claim understanding simply because code was written or an explanation delivered.

After implementation, run appropriate checks and compare actual results with acceptance. Recap working/pending/simulated behavior, update progress and significant decisions, ask the step checkpoint and offer one optional experiment. Suggest the planned commit description if useful; this is not authorization to commit or publish. Wait for explicit readiness before the next stage, while answering questions/fixing current-stage failures as needed.

## 8. Honest and Meaningful Verification

Use focused deterministic tests for pure rules and Streamlit in-process checks for interface interactions. Reserve visual checks for actual browser observations. Automated tests must not require credentials or consume live quota. Fake provider results verify exact transitions and failures; live Gemini tests verify traceable fields, capacity, distinctness and supported claims without promising a precise count.

Cover five/seven weeks, optional campaign targets, above-ten accumulated topics, empty/short plans, acknowledgement, readiness versus explicit finalization, batch capacity, selection/exclusion/restore, mode conflicts, explicit unchanged-source rounds, no automatic rerun calls, failure retries, source protection, formats/context/evidence, ordering/dates, reports and snapshots.

For CSV, verify selection/order/evidence, Unicode and quoting, empty weekly slots and formula-like text. For persistence, verify version/size/reference integrity, round trips, restart/reopen, retained exclusions/evidence, transient busy reset, secret exclusion and invalid-load atomicity. Load validation must not destroy unsaved work or execute file contents. Imported fingerprints do not authenticate absent raw source bytes.

Schemas and matching excerpts cannot guarantee correct reasoning; semantic distinction and factual proportionality need human review. Do not prescribe a permanent test total. Replace assertions implementing obsolete total caps/automatic completion rather than treating them as current acceptance. Broaden/repeat checks only for new changes, failures or unresolved concerns.

Always distinguish passed/failed/not run, expected/observed, manual/automated, simulated/live, historical/current. A missing key, package or user action leaves relevant verification pending. No specification change counts as runtime verification.

## 9. Progress and Decision Records

Progress should quickly show current stage, completion history, concepts explained versus understanding demonstrated, important files, actual checks, current capabilities, pending/simulated areas, unresolved questions and next stage.

Record Step 2 as historically verified under previous scope, and record the subsequent complete implementation separately. The old total-cap tests were replaced, not weakened to preserve obsolete behavior. New checks cover modes, storage and the integrated workflow; historical test counts remain dated. Keep account-dependent live checks pending until actually performed.

Decisions record date, issue, chosen approach, reason, affected responsibilities and checks performed. Current decisions supersede obsolete historical choices without pretending history was different. Keep package version history in dependency notes and link/reference it rather than copying it everywhere.

## 10. Debugging and Recovery

Identify the failed action and relevant error location, explain cause versus hypothesis, make the smallest appropriate correction, and verify it. Explain related multi-file fixes instead of hiding broad rewrites. Do not reset user work to repair recoverable errors. Preserve sources, topics, exclusions, brief, pending requests and useful diagnostics.

Loading validates into a separate candidate workspace before applying it; partial mutation is a failure. Unsaved replacement/reset needs clear confirmation. Saving is explicit and includes extracted private content; do not imply encryption or background autosave. Logs contain safe metadata/error categories, not secrets or full private source/snapshot contents.

## 11. Routine Choices and Scope Questions

Resolve routine implementation choices within authorized scope: names, minimal fixes, useful feedback, native controls, fixtures and documented defaults. Explain consequential decisions in the teaching conversation without unnecessary approval loops.

Ask only when an unresolved choice affects core behavior, authority of conflicting facts, a major stack change, storage exposure or new scope. State concrete options and consequences; continue independent work that does not depend on an answer. The user has approved all six suggested additions, including explicit persistence and CSV; do not ask again whether those features are in scope.

The 17 October one-shot request expressly authorizes the complete V1 build, testing, fixes and supporting documentation without intermediate approval stops. That current instruction overrides earlier step pauses for this run. Future work follows the user’s then-current pace; do not infer perpetual approval to expand V1 or implement V2.

## 12. Alignment Rules

Rewrite stale active requirements instead of appending contradictory exceptions. Check architecture/files/growth/steps/feature coverage, modes/targets/batches/finalization, selection/exclusions/evidence, request tracking, snapshot schema/privacy/load rules, export fields, dependency ownership and present-versus-future status.

The workspace is session-owned while running and durable only when explicitly saved; it is not always disk-backed. Campaign has no fixed total topic ceiling, but requests and resources are bounded. Request eligibility is not based only on new document revisions. A ready plan is not finalized. A new plan retains sources/topics; a new workspace clears them deliberately. Library topics are not all selected for export.

README must describe the implemented app, launch path, configuration and pending live/manual verification, rather than the superseded preview. Product docs contain prompt requirements without actual wording. Explain extracted content goes to Gemini during generation and into the chosen local snapshot during saving. Do not describe the entire system as offline or private-by-default.

## 13. Future Extensions

Keep OCR, full post drafting, generated images, automatic publishing, cloud sync, multiple users, automatic history/version browsing and vector retrieval parked until selected. Name owner, benefit, data/dependency impact, prerequisite learning, verification and affected rules before implementing an extension.

Save/reopen, CSV, brief/naming, review/ordering, manual weekly day/date planning and both modes are now Version 1 features, not parked future ideas. Do not create unused extension scaffolding or future prompts.

## 14. Review Checklist

Before handing over revised specifications, confirm:

- All approved features F1–F12 have ownership, data behavior, acceptance and build coverage.
- Five/seven weeks, optional campaign target, per-request bounds and explicit finalization agree everywhere.
- Empty/short/mode-switch/exclusion/no-new-topic/retry behavior is specified without filler or silent losses.
- Workspace/plan distinction, local snapshots, public exports and source retention are consistent.
- Save/load includes versioning, size/ref validation, unsaved protection, extracted-content disclosure and no secrets/raw uploads.
- Global Python policy and all ten libraries remain; no new environment or unrelated package is introduced.
- Steps 1/2 are historical, expanded files match Steps 2R–13, and completed local versus pending live/manual verification is explicit.
- No implementation, command, configuration sample, JSON example or actual prompt is embedded.
- README/progress/decisions distinguish newly approved requirements from tested implemented behavior.
- The learner can find the current goal, next stage and reasons for the revised approach.
