# Documentation Index

The documentation separates requirements, current verification, product use, code ownership, and learning. It does not duplicate the full specification in every guide. Requirements text describes intended behavior; executed checks establish what was actually verified.

## Recommended reading order

| Reader's goal | Read in this order |
| --- | --- |
| Use the application | [README](../README.md), [Project Guide](PROJECT_GUIDE.md), then [Troubleshooting](TROUBLESHOOTING.md) when needed. |
| Understand how it works | [Project Guide](PROJECT_GUIDE.md), [Data Flow](DATA_FLOW.md), [Learning Guide](LEARNING_GUIDE.md), and [Codebase Map](CODEBASE_MAP.md) alongside the source. |
| Learn unfamiliar terminology | [Glossary](GLOSSARY.md), returning to the connected examples in the guides. |
| Check completion and evidence | [Progress](PROGRESS.md), [Known Limitations](KNOWN_LIMITATIONS.md), and the relevant tests/source. |
| Maintain the project with an LLM | Both governing specifications, [LLM Handoff](LLM_HANDOFF.md), [Codebase Map](CODEBASE_MAP.md), [Decisions](DECISIONS.md), and current [Progress](PROGRESS.md). |
| Change dependencies or setup | [Dependency Notes](../streamlit_setup/dependency_notes.md), the requirements declaration, and the runtime policy in the governing specifications. |

## Authority and ownership

| Document | Owns | Does not establish |
| --- | --- | --- |
| [PROJECT_SPEC.md](../PROJECT_SPEC.md) | Product scope, architecture, data requirements, revised build sequence, and acceptance. | That every requirement has been implemented or tested. |
| [DOCUMENT_SPEC.md](../DOCUMENT_SPEC.md) | Teaching, documentation style, dependency practice, and working rules. | A replacement product architecture. |
| [README.md](../README.md) | Concise current overview, prerequisites, setup, and main workflow. | Detailed implementation contracts. |
| [PROGRESS.md](PROGRESS.md) | Actual implementation status, observed checks, unresolved work, and learning record. | Unperformed live or visual verification. |
| [DECISIONS.md](DECISIONS.md) | Significant dated choices, rationale, and superseded history. | Authority to restore obsolete behavior over current requirements. |
| [PROJECT_GUIDE.md](PROJECT_GUIDE.md) | User purpose, modes, capabilities, workflow, and privacy boundaries. | Complete source-level details. |
| [CODEBASE_MAP.md](CODEBASE_MAP.md) | Actual module responsibilities, dependencies, and where changes belong. | A duplicate copy of implementation. |
| [DATA_FLOW.md](DATA_FLOW.md) | The source-to-topic-to-plan-to-report/snapshot lifecycle and failure boundaries. | Perfect factual correctness of model reasoning. |
| [LEARNING_GUIDE.md](LEARNING_GUIDE.md) | Beginner explanations and coherent fictional examples with checkpoint questions. | Demonstrated learner understanding. |
| [LLM_HANDOFF.md](LLM_HANDOFF.md) | Self-contained technical maintenance context and safe investigation/update workflow. | A reason to skip inspecting current code. |
| [GLOSSARY.md](GLOSSARY.md) | Consistent definitions for product and engineering terms. | New requirements. |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Likely causes and recovery grounded in actual behavior. | Proof that every listed failure occurred during verification. |
| [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md) | Intentional boundaries, practical limits, and environmental verification gaps. | Permission to leave undisclosed implementation failures. |
| [dependency_notes.md](../streamlit_setup/dependency_notes.md) | Observed package/runtime history, purposes, compatibility notes, and changes. | A lockfile for unrelated global packages. |

Current user instructions take precedence when they explicitly revise scope or pace. Resolve product behavior against PROJECT_SPEC, documentation/learning practice against DOCUMENT_SPEC, and implementation facts against source and current test results. Historical notes remain useful context but do not restore the removed ten-topic campaign cap or automatic finalization.

## Keeping documents accurate

Change the owning source first, verify it, and update the corresponding document. A planning-rule change may affect specifications, tests, guides, and the handoff. A package inventory belongs in dependency notes rather than repeated version tables everywhere. Current test counts and environmental gaps belong in Progress so other guides do not become stale copies.

Prompt assets stay under prompts. Implementation, runnable commands, configuration contents, and example JSON stay out of these guides under DOCUMENT_SPEC. The teaching conversation can provide exact launch/check instructions when needed.

Version 1 remains the local Streamlit application in web_app. A future V2 is separate and unimplemented; none of these guides implies a second frontend, server, or publishing integration already exists.
