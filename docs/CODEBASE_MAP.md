# Codebase Map

This map identifies responsibility in the actual V1 architecture. Consult the source before changing a contract and [PROGRESS.md](PROGRESS.md) for current verification. [PROJECT_SPEC.md](../PROJECT_SPEC.md) remains the authority for intended behavior.

## Root and runtime files

| Location | Owns | When to change it |
| --- | --- | --- |
| PROJECT_SPEC.md | Product requirements, architecture, acceptance, revised build sequence. | Agreed behavior or scope changes. |
| DOCUMENT_SPEC.md | Teaching, documentation, global Python policy. | Changes to learning or documentation requirements. |
| README.md | Concise setup, usage, and capability overview. | Entry point, environment, or user workflow changes. |
| .env.example | Names and nonsecret placeholders for supported local settings. | A supported environment setting changes. |
| .env | Ignored local credentials and model configuration. | User configuration; never commit or copy its values into reports. |
| .gitignore | Exclusions for secrets and local artifacts. | New private/generated artifact types. |
| config/settings.py | Shared limits and environment loading. | Resource policy, provider timeout, or supported configuration changes. |
| .streamlit/config.toml | Framework appearance and server/uploader settings. | Streamlit-specific presentation or runtime changes. |
| streamlit_setup/requirements.txt | The application's ten direct dependencies. | Actual compatibility or feature dependency changes. |
| streamlit_setup/dependency_notes.md | Observed package versions, purposes, and environment history. | Dependency inventory or installation changes. |

## Streamlit application

The existing web_app directory contains V1's Streamlit interface. It has not become a V2 frontend. There is no separate web API, React application, database, authentication system, or publishing service.

| File | Responsibility and dependencies |
| --- | --- |
| web_app/app.py | Entry point, page configuration, and session initialization; delegates rendering. It makes the root packages importable when Streamlit launches the nested script. |
| web_app/views.py | Workspace controls, names/brief/modes, intentional upload processing, evidence inspection, explicit generation, library review, active-plan controls, snapshots, and downloads. Delegates decisions to workflow/storage/export owners. |

Widget callbacks and page reruns must never independently decide to call Gemini. Stable topic and source IDs connect buttons to records; display titles and list positions are not identities.

## Validated data models

| File | Responsibility |
| --- | --- |
| models/topic.py | EvidenceReference, TopicCandidate, and accepted TopicIdea; text limits, source list shape, stable IDs, and origin metadata. |
| models/generation_result.py | A batch of zero to ten candidates and a required sufficiency explanation. |
| models/plan.py | Plan mode, target, brief, selections, weekday slots, dates, readiness, and explicit finalization consistency. |
| models/workspace.py | DocumentRecord and Workspace; canonical extracted content, unique identities, source totals, relationships, and evidence membership. |

Pydantic validates data at boundaries. Ordinary assignment is not automatically validated; workflow transactions rebuild the candidate record before committing. Export and storage revalidate rather than trusting a possibly mutated object.

## Document ingestion

| File | Responsibility |
| --- | --- |
| documents/extraction.py | Shared ExtractionResult and ExtractionError, canonical source blocks, extracted-character/location guards, and Office archive expansion checks. |
| documents/file_router.py | Safe filename/type/size checks, SHA-256 source identity, and routing to exactly one reader; returns DocumentRecord. |
| documents/docx_parser.py | Word body paragraphs and tables in reading order; unsupported-content warnings. |
| documents/tabular_parser.py | CSV decoding/shape checks and Excel stored-value reading; pandas-based summaries over full loaded tables and bounded individual previews. |
| documents/pdf_parser.py | Selectable page text with page locations and partial/unreadable-page warnings. |
| documents/context_builder.py | Complete evidence context with provenance and warnings; rejects overflow instead of silently truncating sources. |

Do not create a second parser in the interface or provider layer. The inspector and request builder must use the same source representation.

## Workflow and generation

| File | Responsibility |
| --- | --- |
| workflow/state_manager.py | Validated commit, busy/editability guards, document pool changes, new plan, workspace reset, and naming. |
| workflow/topic_pool.py | Text normalization, practical repeated-angle detection, candidate-to-library acceptance; no global ten-topic library cap. |
| workflow/plan_manager.py | Configuration, selection/deselection, exclusion/restore, order/day assignment, readiness, finalization/reopen, and batch capacity. |
| workflow/planning_service.py | Intentional file ingestion and generation orchestration; request identity, atomic merge, automatic vacant selection, and failure preservation. |
| prompts/grounding_rules.txt | Actual source-grounding instructions; prompt wording belongs here, not in documentation. |
| prompts/topic_request.txt | Actual candidate-generation task instructions. |
| prompts/builder.py | Complete request assembly from assets, source context, brief, mode, existing angles, exclusions, and capacity. |
| ai/gemini_client.py | Google GenAI access, metadata/token checks, bounded retry, structured response validation, sanitized provider errors, and owned-client closure. |
| ai/topic_generator.py | Builds the request, selects the provider, and returns a source-validated batch without mutating the workspace. |
| ai/response_validator.py | Source/filename/location/excerpt checks, conservative factual guards, distinctness, exclusion suppression, and acceptance feedback. |

When a bug spans several areas, trace it through planning_service rather than placing a workaround inside a rendering function.

## Persistence and reports

| File | Responsibility |
| --- | --- |
| storage/workspace_store.py | Version-1 JSON snapshot bytes, byte/collection/shape limits, safe decoding, full cross-record validation, and transient busy reset. Returns a candidate; never replaces session state itself. |
| exports/__init__.py | Shared export validation, authoritative ordered rows, day/date calculation, and relevant warning selection. |
| exports/markdown_exporter.py | Standalone readable report of finalized selections and their evidence. |
| exports/csv_exporter.py | Standard CSV serialization, Unicode byte-order mark, spreadsheet formula neutralization, and the same finalized selected rows. |

Workspace and plan names are report metadata, not trusted filesystem paths. Snapshot storage returns bytes for browser download; it does not choose arbitrary local save paths.

## Tests, fixtures, and documentation

tests contains deterministic checks owned by the corresponding behavior. Test names are evidence of intent; only executed results establish verification.

| Test area | Current files |
| --- | --- |
| Workspace and topic rules | test_state_manager.py, test_topic_pool.py. |
| Planning and coordinator | test_plan_manager.py, test_planning_service.py. |
| Reading and evidence context | test_docx_parser.py, test_tabular_parser.py, test_pdf_parser.py, test_file_router.py, test_context_builder.py. |
| Prompt/provider behavior | test_prompt_builder.py, test_generation.py. |
| Models, snapshots, and reports | test_models_storage_exports.py. |
| Interface behavior | test_ui.py. |
| Shared fictional fixtures | conftest.py. |

Temporary fixtures represent fictional data and mocked providers avoid credentials or live quota. Tests can be expanded without requiring this map to prescribe a permanent total.

sample_docs contains fictional_school_guide.docx, fictional_school_audit.xlsx, fictional_school_report.pdf, and fictional_weekly_audit.csv, with generate_samples.py recreating those small fixtures. They are labelled fictional examples for trying the supported formats, not evidence of real-world waste conditions. This directory differs from user uploads and saved working snapshots.

docs separates product explanation, source mapping, data flow, learning, maintenance handoff, terminology, troubleshooting, and known limitations. Begin with [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md); update the owning documents rather than copying the complete specification into every guide.

## Provider routing additions

ai/provider_chain.py owns the explicit Gemini-primary, Groq-fallback and alternate-
Gemini-reserve sequence. It creates adapters lazily, skips repeated attempts with
known-invalid credentials, and returns only safe model/category feedback.
ai/groq_client.py implements one structured HTTPS request through the standard
library, with a fixed host, no redirects or hidden retries, bounded response and
conservative complete-context checks. ai/gemini_client.py now adapts the schema
into Gemini's supported wire subset while preserving local validation.
The shared topic generator validates the selected provider's result exactly once
before the workflow can merge it. tests/test_provider_chain.py covers routes,
rollback, no-hop conditions, request shape, privacy and Groq error boundaries.
