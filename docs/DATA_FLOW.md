# Data Flow

This guide follows a source through the implemented boundaries. It uses Greenfield School, a fictional school whose report describes classroom bin labels. See [CODEBASE_MAP.md](CODEBASE_MAP.md) for file ownership and [PROGRESS.md](PROGRESS.md) for actual verification results.

## 1. A session owns one workspace

Streamlit session state (memory associated with the current browser connection) holds the reusable workspace. The workspace contains documents, accepted topics, exclusions, one active plan, request bookkeeping, and feedback. Separate sessions initialize separate records. A browser refresh, lost session, or server restart can lose unsaved changes.

The interface collects intent. Workflow functions decide what may change. A validated commit (replacement only after a complete candidate passes validation) prevents a partially changed document list from becoming the active state.

## 2. Intentional upload and extraction

The user chooses the fictional school report and explicitly processes the addition. Merely opening the uploader or rerendering the page is not ingestion and does not call Gemini.

planning_service processes each chosen file independently. file_router checks filename, supported extension, byte size, and readable bytes, then chooses the appropriate parser. SHA-256 produces a fingerprint (a content identifier calculated from the original bytes). Identical bytes are duplicates even after renaming; different bytes with the same case-insensitive filename are rejected to keep references unambiguous.

Each parser returns labelled locations and warnings. For example, a PDF uses pages; Word uses paragraphs/table rows; tabular sources use full-table summaries and included row locations. The reader never invents content for unreadable sections. XLSX formulas use stored values, and unavailable results remain missing rather than becoming zero.

For tables, all loaded data rows contribute to supported numeric summaries. The first hundred individual data rows are included as a preview. Later individual rows are not individually citable, even though their values contribute to full-table summaries. This distinction is shown in extraction warnings.

DocumentRecord retains metadata, extracted locations, canonical content (the exact common text representation assembled from those locations), warnings, and participation state. It does not retain the raw upload binary. Adding a new document increments the source-pool revision. A bad file reports an individual error without erasing already accepted files.

## 3. Inspection and complete request assembly

The source inspector uses the same canonical blocks that generation uses. context_builder includes source identity, filename, size, warnings, locations, and evidence text. Source instructions are labelled untrusted document data rather than app instructions.

prompts/builder adds the actual prompt assets, selected mode/target, audience/goal/guidance, all previous topic angles and supporting references, and exclusions. The brief helps decide relevance; it cannot supply documentary facts. Existing and excluded angles remain present so a request for more topics does not forget earlier work.

The complete assembled context must fit the character limit. It is not silently sliced, and later sources or exclusions are not dropped. An oversized request is blocked with guidance to save the current workspace and prepare a smaller one. Character count is a local guard, not a substitute for provider token limits.

## 4. One explicit generation round

Generate and Find more topics both enter generate_batch. It checks that the workspace is editable, that readable sources exist, and that capacity is available. Capacity is at most ten and may be smaller when a fixed plan has fewer vacancies. An open campaign can request another batch even though its nonempty selection is already ready for review.

A request fingerprint includes source revision, brief/mode/target, prior topics, exclusions, requested capacity, and a deliberate round number. Ordering, day changes, downloads, and page reruns are not generation requests. An unchanged source library can support a new explicit round.

The coordinator reserves busy state before provider work. A lazy chain tries Gemini 3.6 Flash, Groq GPT-OSS 120B on operational failure, then Gemini 3.8 Flash reserve. GeminiClient obtains metadata and exact request tokens; GroqClient conservatively bounds complete prompt/schema bytes against model capacity. Each reserves response capacity before sending. No route truncates evidence. All results then share local validation; zero valid output and evidence rejection do not cause another provider attempt. The API wrapper uses sanitized error categories rather than showing raw provider payloads.

At most one automatic retry is shared across metadata, token-count, and generation operations for eligible temporary errors. Long waits, permanent access/quota problems, malformed output, and timeouts are left for an informed manual retry. The transport's separate retry mechanism is disabled to avoid multiplying retries.

## 5. Candidate checks before merge

The provider returns GenerationResult: a required sufficiency explanation and zero to ten TopicCandidate records. Every topic includes descriptive context, a supported core insight, audience, suggested format, and evidence references.

response_validator checks source identity and filename, location membership, actual excerpt occurrence, numeric claims, some scope/unit/causal overreach, and practical distinctness against retained and excluded angles. These checks can reject obvious problems, but cannot establish complete semantic correctness. Human review remains necessary.

Accepted candidates become TopicIdea records with application-generated stable IDs. topic_pool also guards repetition during acceptance. No record is accepted just because a plan needs another slot.

## 6. Success, zero results, and failure

On success, one validated commit adds accepted topics, marks sources as participated, records feedback and the successful round, and fills vacant selections for review. Weekly selections follow assigned day order. Readiness is recomputed without finalizing.

A valid response with no new accepted topics still completes that explicit round and reports the shortfall. Another request requires another deliberate action. A provider failure or invalid response does not consume a successful round or erase prior libraries, exclusions, selections, or settings. Busy is released in all cases so retry remains possible.

## 7. User review and explicit finalization

Plan actions use stable topic IDs. Deselecting removes a selection but retains its topic. Excluding also removes it from the selection and remembers the angle. Restoring removes the excluded status without automatically selecting it. Reordering and weekday swaps do not involve the provider.

The active plan can be draft, ready for review, or finalized. A fixed target must fit the selected set; switching to a smaller mode refuses to silently discard extra choices. Shorter nonempty plans require explicit shortfall acknowledgement. Finalization records a time and freezes plan editing until an explicit reopen clears finalization metadata.

## 8. Reports from the authoritative selection

The exporters revalidate the workspace, require a nonempty finalized plan, and read only its selected topics. Markdown and CSV use shared ordered rows. Weekly rows retain holes and compute dates only when an optional Monday is present. Both carry supporting context, evidence, relevant extraction warnings, and metadata. The full source text is not copied unnecessarily into public planning reports.

Reopening/editing invalidates finalization, so a current draft cannot produce a new finalized report. A previously downloaded file remains a historical artifact on the user's computer; the application cannot revoke it.

## 9. Save and transactional reopen

Saving is explicit and separate from finalization. workspace_store revalidates the entire graph and creates a versioned JSON snapshot containing extracted evidence, topic records, exclusions, plan settings/order/dates/status, and save metadata. It excludes provider clients, credentials, raw original binaries, and arbitrary path settings. It is a private, unencrypted working artifact.

Reopen checks byte size, schema version, complete record fields, collection limits, IDs, source totals, source content consistency, evidence membership, selections/exclusions, days, targets, and finalization. Invalid imports return a sanitized error; the active workspace is untouched. Only a fully validated candidate may replace session memory after the UI's replacement confirmation. Transient busy state resets, and reopening makes no API call.

The snapshot does not contain the original PDF or workbook. Reopened fingerprints identify saved references; they cannot authenticate original bytes that are no longer present. To re-extract a source, retain and upload its original file in an appropriate new workspace.
