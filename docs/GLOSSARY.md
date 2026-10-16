# Glossary

Terms describe the application's current boundaries. [PROJECT_GUIDE.md](PROJECT_GUIDE.md) gives a connected example; [LLM_HANDOFF.md](LLM_HANDOFF.md) gives maintenance contracts.

| Term | Meaning in this project |
| --- | --- |
| Active plan | The one current named, ordered selection of workspace topics, organized as Week or Campaign. |
| Audience | The people a topic is intended to help reach. An editorial choice, not a documentary fact. |
| Available topic | An accepted library topic that is not excluded and can be selected under current plan rules. |
| Batch | A group of at most ten candidates requested in one explicit generation operation. It is not the total campaign size. |
| Brief / planning brief | Optional audience, communication goal, and guidance that help frame useful topics without replacing evidence. |
| Busy | A temporary flag that an operation is underway; it blocks conflicting actions and resets after failure or reopening. |
| Campaign | A plan mode with an optional positive target, or no required total. It does not mean the whole workspace. |
| Candidate | A structured topic suggestion awaiting source-aware and repeated-angle checks. |
| Canonical content | The exact common text representation assembled from a document's labelled source locations. Inspection, validation, and saving use it consistently. |
| Context | Descriptive supporting background for a topic, separate from its shorter core insight. It remains evidence-grounded. |
| Core insight | The main supported observation or finding behind a topic. |
| CSV | A table stored as text with correctly serialized fields; the app exports Unicode CSV suitable for common spreadsheet programs. |
| Dataclass | A Python convenience for grouping named values; used in early learning work and shared extraction results. |
| Deselect | Remove a topic from the active plan while retaining it in the library for later use. |
| Distinctness | Whether a candidate adds a meaningfully different communication angle. Local wording checks are useful but imperfect. |
| Evidence reference | A link from a topic to a document ID, filename, source location, and supporting excerpt. |
| Excerpt | A short part of extracted source text used as support; it must be found at the referenced location. |
| Excluded topic | A retained topic deliberately marked unwanted, removed from selection, and remembered to suppress repeated angles. |
| Export | A report of finalized selected topics, as Markdown or CSV. It differs from a workspace snapshot. |
| Extraction | Reading supported document material into text, locations, and warnings. It does not ask Gemini to invent or summarize missing text. |
| Finalization | The user's explicit approval of a nonempty selection. A short plan also records acknowledgement of unfilled slots. |
| Fingerprint | A SHA-256 identifier calculated from original uploaded bytes to recognize identical content. An imported fingerprint cannot authenticate an absent original. |
| Gemini | The external provider used for candidate generation. Explicit requests send it extracted source information and planning context. |
| Generation round | One deliberate request attempt tracked separately from document changes; later explicit rounds can use unchanged sources. |
| Identifier / ID | A stable value used to refer to a source, topic, plan, or workspace independently of display position. |
| Input / pool revision | A number that changes when the document collection changes. It is not the only condition governing new requests. |
| Location | A human-readable source label, such as a PDF page, Word paragraph/table row, CSV row, or spreadsheet summary. |
| Markdown | A readable text report format with headings, emphasis, lists, topic details, and evidence. |
| Mock | A controlled stand-in for an external service, used to test outcomes and failures without credentials or live quota. |
| OCR | Recognition of text inside images. It is outside Version 1; PDFs need readable selectable text. |
| Origin | Metadata distinguishing generated topics from labelled fictional sample records. |
| Persistence | Keeping information after a temporary application session ends. V1 provides explicit downloadable snapshots. |
| Preview | A bounded set of individual tabular rows shown as evidence; full-table summaries still use all loaded data rows. |
| Provider | The component that supplies generated candidates. Gemini is the live implementation; tests can inject a mock. |
| Pydantic | The library that validates record shapes, values, and model-level consistency rules. It cannot by itself prove facts. |
| Ready for review | A nonempty open campaign or a filled fixed target; a stage before explicit finalization. |
| Reopen plan | Deliberately remove finalization protection so the active plan can be edited again. |
| Reopen workspace | Load a saved snapshot after complete validation; restores extracted evidence and working state rather than original files. |
| Rerun | Streamlit executing the page script again after an interaction. A rerun must not automatically generate topics. |
| Resource guard | A practical bound on file sizes, extraction, context, collections, or provider work. It differs from a user-facing topic target. |
| Restore | Deliberately remove a topic's excluded status, making it available without selecting it automatically. |
| Schema | The defined fields, types, and relationships a record or workspace file must follow. |
| Selection | The ordered topic IDs currently included in the active plan. Library size can be larger. |
| Semantic comparison | Comparing meaning rather than only wording. V1's local checks do not provide perfect semantic matching. |
| Session state | Temporary memory associated with a Streamlit browser session, surviving ordinary reruns but not guaranteed after session loss. |
| Snapshot / workspace file | A versioned, unencrypted working-state download containing extracted sources and reusable planning material. It is not a public report. |
| Source | An uploaded document retained as extracted evidence with identity, metadata, locations, and warnings. |
| Source library / pool | The workspace's retained document records. |
| Stable order | The user-selected sequence retained across reruns, reports, and save/reopen. Weekly selection order follows assigned days. |
| Streamlit | The Python framework providing the local application interface and session behavior. |
| Sufficiency note | An explanation of what the sources support and why a response may contain fewer or no new topics. |
| Target | The desired number of selected topics: five/seven for Week, optionally user-selected for Campaign. It is not a guarantee. |
| Token | A provider unit used to measure model input/output budget; it is different from a character count. |
| Topic library | All retained accepted topics, including currently unselected and excluded records. |
| Transactional loading | Validate a separate complete workspace first and replace current work only after success. |
| Validation | Checking required structure, values, references, and rules. Its practical factual checks do not prove every interpretation. |
| Week mode | A Monday-based plan with five or seven slots, one topic per day and optional dates. |
| Workspace | Reusable source and topic libraries, exclusions, working metadata, and one active plan. |

