# Learning Guide

This guide teaches the completed V1 design progressively. It explains responsibilities and decisions rather than reproducing implementation snippets. Use [CODEBASE_MAP.md](CODEBASE_MAP.md) beside the source, and [GLOSSARY.md](GLOSSARY.md) whenever a term is unfamiliar. Reading a guide or passing a test does not establish that the learner understands the concept; the questions below are invitations to explain it in their own words.

## A single example to carry through the system

Greenfield School is fictional. Its report identifies classrooms with labelled sorting bins, while a separate guide explains those labels. A school coordinator wants five student-facing topics for the coming week, and later a larger campaign using the same documents.

The documents establish facts. The coordinator's brief (audience, goal, and useful guidance) tells the app which supported material is relevant. The brief cannot turn a wish into a fact. For example, wanting a topic about improved recycling does not establish that the school measured an improvement.

## 1. Memory belongs to a workspace

Streamlit performs a rerun (executes the page script again) after widget interactions. Ordinary variables created during that run do not provide durable application memory. Session state keeps the workspace accessible across ordinary reruns associated with that connection.

The workspace groups related information: documents, accepted topics, exclusions, the active plan, request bookkeeping, and feedback. A dataclass was useful for the early learning preview; the expanded application uses Pydantic models (records that check expected fields and relationships).

This is still memory, not automatic permanent storage. If the coordinator closes a session without saving a workspace file, the application does not promise recovery. Explicit snapshots provide continuation after that temporary memory disappears.

Question: Which parts of the school example must survive a page rerun, and which require an explicit saved file to survive a lost session?

## 2. Stable identity differs from a label

The school's report has a filename, but filenames can change. The application calculates a fingerprint (an identifier derived from the file's bytes) to recognize identical content under another name. Different bytes with the same case-insensitive name are refused because future citations would otherwise be ambiguous.

Topics and plans receive stable IDs (identifiers that stay attached to records when their displayed position changes). A topic moved from Monday to Wednesday remains the same topic. Buttons, selections, evidence, and snapshots refer to its identity rather than relying on its current list position.

Question: Why should renaming an identical report not produce another source, while two different reports with the same name require clarification?

## 3. Keep presentation separate from decisions

The interface asks the coordinator what to do and displays the result. It does not determine whether an excluded topic can be selected, whether a short plan may be finalized, or whether a source is safe to remove. Those decisions belong in workflow modules.

For example, pressing Select submits a topic ID to plan_manager. That owner checks editability, exclusion status, and available slots. The interface displays the resulting selection or explains the refusal.

This separation makes the code easier to change and test. If the page layout changes, the evidence and planning rules do not need a second implementation. A deterministic test (a check whose expected outcome does not depend on live internet responses) can exercise those rules directly.

Question: Where should a developer change the rule for finalizing an incomplete week: a screen renderer or plan_manager?

## 4. Extraction creates evidence that can be inspected

Extraction (turning document contents into readable text and structured locations) is different from generation (asking the model to propose topics). The school report must be read first. Otherwise, the user cannot inspect what the model will receive.

Each parser returns location labels, text, and warnings. A PDF page can be cited as a page. A spreadsheet summary is a computed result that can be cited at its summary location. The canonical content is the common representation built from those labelled blocks so inspection, saving, and generation refer to the same evidence.

For a large school spreadsheet, summaries use all loaded rows. Only the first hundred individual rows appear in the row preview. A preview limit therefore limits individually visible row evidence, not which rows contribute to summaries. Neither the model nor the user should claim to quote an omitted individual row.

Question: If classroom 150 is outside the individual preview, can its data still affect the full-table sum? Can its row be cited individually?

## 5. Structured output is necessary but not enough

A topic needs a title, supported core insight, descriptive context, audience, suggested format, and evidence. Pydantic checks structure (whether required fields and types exist within limits). It does not determine whether a quotation logically supports the interpretation.

The source-aware validator checks whether the source exists, the filename matches, the location exists, and the excerpt is actually present. Additional conservative checks catch some invented numbers, unstated units, broader scope, causal claims, and unrelated insights. A candidate with a real quotation can still be misleading; review remains part of the workflow.

Topic context supplies the background needed to understand the idea. It is separate from the shorter core insight and is required in generation, reports, and snapshots. An attractive headline alone is not a complete topic.

Question: What is the difference between proving that a quotation exists and proving that the proposed conclusion follows from it?

## 6. A batch is not a campaign

A batch is a small group of candidates requested at once. It contains at most ten candidates. A campaign can accumulate more than ten accepted topics through several explicit rounds.

For the school week, generation capacity is reduced to the vacant weekly slots. For an open campaign, a nonempty plan can be ready for review and still accept another requested batch. An optional campaign target guides selection size; it does not become a universal application limit.

Previous topics and exclusions are supplied on later requests, then local repeated-angle checks compare returned titles and insights. Normalization (making text consistent for comparison) handles differences in case, punctuation, Unicode, and spacing. Similarity checks catch some close wording. They cannot guarantee perfect comparison of meaning.

Question: Why would a ten-candidate response limit be useful even if the school's campaign ultimately selects fifteen topics?

## 7. Selection, exclusion, and source protection have different purposes

The topic library retains accepted ideas. The active plan uses only some of them. Deselecting keeps an idea available for a later plan. Excluding remembers an unwanted idea and its angle so later generation can avoid repeating it. Restoring makes it available again without automatically choosing it.

Suppose an excluded topic still quotes the school's report. The report remains protected because that topic may be restored. Removing the source would break its evidence relationship. The application permits removal only when no retained topic cites the document.

Question: If the coordinator deselects a topic for a short weekly plan, should it disappear from the campaign library? What changes if it is excluded instead?

## 8. Readiness and finalization are separate state transitions

A state transition (an explicit change in the plan's working stage) matters because different actions are allowed at different stages. Draft means the plan is empty or below its fixed target. Ready for review means its target is filled, or an open campaign contains selected topics. Finalized means the user explicitly approved a nonempty selection.

If only three school topics are supported, the coordinator can acknowledge two empty weekday slots and finalize a shorter plan. Empty slots remain visible. The app never pads them with repeated or invented claims.

Reopening deliberately clears finalization before editing. This prevents the current draft from being exported as if it were still the approved selection. Previously downloaded reports remain historical files and cannot be recalled by the app.

Question: Why should reaching five topics enable review rather than automatically announce that the school has approved the plan?

## 9. Transactions preserve valid work through failures

A transaction here means preparing and validating a complete change before replacing active working fields. The generation coordinator does provider work before merging new topics. If a later request fails, prior successful work remains intact.

The input revision identifies changes to the document collection. A deliberate request round identifies another user-initiated attempt, even when sources are unchanged. A successful zero-topic result consumes a round but does not start a loop. A failed round remains retryable. Busy state is temporary and released after success or failure.

Workspace loading follows the same principle. It validates an entirely separate candidate before session replacement. A late failure in the last topic's evidence must leave the coordinator's current school plan untouched.

Question: Why must loading not replace the document list first and validate the topics afterward?

## 10. Public reports and private working snapshots serve different needs

Markdown and CSV contain the finalized selected plan, its context, evidence, and warnings. They do not export every unused library topic or copy all uploaded source content.

A workspace snapshot contains the extracted evidence needed to continue planning, including unused topics and exclusions. It is versioned JSON (a text data format with an explicitly identified schema), parsed as data rather than executed. It contains no raw original files or credentials, but it can contain sensitive extracted source text and is not encrypted.

CSV uses a standard serializer (a library that writes a format correctly) so commas, quotations, newlines, and Unicode remain usable. Formula-like cells receive a protective leading apostrophe to prevent spreadsheet execution. A CSV is not an XLSX workbook or a scheduling integration.

Question: Which file should the school share as its approved plan, and which should it keep privately to resume work later?

## 11. Learn from the checks without overclaiming

Read tests after reading the owner they exercise. Start with pure plan and workspace tests, then readers, response validation, snapshot/report tests, integration, and Streamlit interactions. Mocks (controlled replacements for external services) make failure and retry cases repeatable without spending quota.

Automated checks establish specific observed behavior; they do not prove perfect reasoning or a successful live Gemini account request. [PROGRESS.md](PROGRESS.md) records current results, and [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md) separates product boundaries from environmental verification gaps.

Optional exercise: explain the complete journey of one school topic from a source location to a finalized Wednesday slot, then identify what must remain if the next request times out.
