# Troubleshooting

Start with the failed user action and the displayed safe message. Record whether the failure occurred during setup, extraction, generation, planning, export, or reopening. Do not publish API keys, private source bodies, saved workspace content, or raw provider errors while asking for help.

This guide describes implemented checks; [PROGRESS.md](PROGRESS.md) records what has actually been verified. Use the exact approved interpreter identified in PROJECT_SPEC and dependency_notes when investigating local setup. No new environment is required.

## Setup and page startup

| Symptom | Likely cause and next action |
| --- | --- |
| A package appears installed, but the app cannot import it. | Installation and startup may use different Python installations. Compare the running interpreter with the approved global Python, then inspect its packages. Do not install into an unrelated default environment. |
| Root-owned packages are missing when opening the entry point. | V1 launches web_app/app.py from the repository. Confirm the documented entry point and its root-path initialization; do not copy files into another folder to bypass imports. |
| The local page is unavailable. | The local Streamlit process may be stopped, startup may have failed, or the configured port may already be in use. Inspect safe startup diagnostics and reopen the actual local server address. |
| Settings changed but the app still uses old values. | Local environment variables can take priority over .env because settings loading does not override existing environment values. Restart the application after reviewing configuration. Never print the key to check it. |

## Uploads and extraction

| Symptom | Diagnosis and recovery |
| --- | --- |
| Duplicate content was skipped under a new filename. | This is expected: identical bytes have the same fingerprint. The original source is retained. |
| A different file with the same name is refused. | References need unambiguous names. Rename the new file before processing it; earlier evidence is not overwritten. |
| A filename is rejected. | Use a plain filename with a supported extension, no directory path, invalid Windows characters, or trailing dot/space. |
| File, source-pool, archive, table, or extraction limit is reached. | Reduce or split the source. Large Office expansion and excessive tables are blocked before they can create unbounded work. Limits live in config/settings.py. |
| PDF has no selectable text. | It may be scanned or image-only. Obtain a selectable-text version. OCR is outside V1; uploading again cannot recover text that the reader cannot see. |
| Some PDF pages are missing. | Inspect page warnings. Unreadable or empty pages are excluded rather than silently treated as evidence. Check the original and create a readable replacement in a separate workspace if retained topics protect the existing source. |
| Word material is absent. | Only body paragraphs and table cells are supported. Images, text boxes, headers/footers, and embedded objects are not assumed read. Move needed material into readable body text in a new source. |
| CSV decoding warning or malformed row. | Prefer a rectangular UTF-8 export with a header. The app reports fallback decoding and rejects unreadable characters or inconsistent field counts. Check the named record and delimiter. |
| Excel formula results are missing or stale. | The reader does not calculate formulas. Recalculate and save the original in Excel, then use an appropriately named readable copy. Missing cached values are not zero. |
| A later spreadsheet row cannot be cited. | Individual preview evidence is bounded. Full-table summaries still include loaded later data rows, but an omitted individual row is unavailable as a quotation. Use an appropriate smaller evidence source if the row itself matters. |
| A source cannot be removed. | A retained topic cites it, even if the topic is excluded. The app protects future restoration and evidence integrity. A new plan retains those topics; replacing the whole workspace is a separate deliberate action. |

## Gemini configuration and generation

| Symptom | Diagnosis and recovery |
| --- | --- |
| Configuration message before generation. | Neither provider is configured. Fill the local GEMINI_API_KEY and GROQ_API_KEY fields; model IDs are predefined. Set supported local configuration privately. Extraction and planning remain local and do not need a live key. |
| Authentication or unavailable-model message. | Check account access, model name, API-key restrictions, and model permissions with the provider. No model is assumed free or account-accessible merely because it exists. |
| Quota/rate-limit message. | Review the account's actual quotas and any requested wait. Permanent/daily limits and long delays are not retried automatically. Do not enable billing as an automatic repair. |
| Timeout. | Earlier work remains. The provider may already have processed the request; choose a manual retry after checking conditions. The app does not automatically repeat timed-out work. |
| Temporary provider failure. | At most one eligible automatic retry is shared across operations. If it still fails, review connection/provider status and retry explicitly. Do not re-upload working sources merely because generation failed. |
| Incomplete/invalid structured response. | Try a smaller batch or check model/schema compatibility. Invalid output is not accepted as usable topics. Raw responses stay out of user diagnostics. |
| Complete context exceeds a limit. | Nothing was silently dropped. Save the workspace and use a smaller separate workspace. Provider token limits and local character guards are different checks. |
| Fewer topics than requested. | The provider may return fewer ideas. Read its sufficiency note; add useful sources or finalize a nonempty shorter plan deliberately. Evidence concerns flag topics for review instead of rejecting them. |
| Find more topics returns zero. | Another request cannot guarantee another angle. Earlier topics remain. Check exclusions and evidence, then deliberately choose whether new sources would help. |
| A topic is red / needs review. | Check the reason and cited passage, then select it or exclude the angle. Formatting-only quote differences are tolerated. Selection hides the review label, including in exports; it does not verify the research. |
| Topics were generated but the plan is empty. | New topics enter the Available library. Use Select for plan to choose the ones you want. Generation no longer selects them automatically. |

## Planning and session behavior

Changing names, brief fields, selections, day assignments, or order should never call Gemini. If network generation occurs during those actions, treat it as a regression in the UI-to-coordinator boundary and add a focused interaction test.

A smaller target or mode cannot silently discard selected topics. Deselect the unwanted choices first; they remain in the library. Campaigns store a plan start date but have no weekly day assignments. Weekly plans can start on any date, with the entire week inside the supported calendar. An extreme date that would push a later day beyond the calendar is rejected before it can break an export.

Reaching a target does not finalize. Explicitly review and finalize. For an incomplete nonempty fixed plan, acknowledge the shortfall. For an empty plan, select supported topics first. To edit an approved plan, reopen it or start a new plan.

If work disappeared after a session loss or restart, reopen a previously downloaded workspace. There is no background autosave, database, or automatic history. Preparing a download is not proof that the browser wrote it to disk.

## Reports and workspace files

| Symptom | Diagnosis and recovery |
| --- | --- |
| Report download is unavailable. | A current nonempty plan must be finalized and internally valid. Reopened drafts require review/finalization again. |
| Weekly report has empty rows. | These represent intentionally unfilled slots, not missing CSV data. The finalized plan records its shortfall. |
| CSV shows a leading apostrophe in some cells. | Formula-like values are neutralized for spreadsheet safety. This is deliberate. The CSV is text, not an XLSX workbook. |
| Saved workspace is rejected. | Check that it is a complete app-created version-1 snapshot, not a Markdown report, CSV, original upload, or edited partial record. Invalid files do not replace current work. |
| Unsupported schema version. | Current loading supports version 1 only. No migration or best-effort coercion is implemented. Retain the file for a future compatible loader. |
| Snapshot byte or topic-record limit. | Reduce/separate workspaces before saving. The record guard is a persistence resource limit and is different from per-request capacity. |
| Reopened source has no original-file download or re-extraction. | Snapshots intentionally contain extracted evidence and metadata only. Keep the original source separately if it may need re-extraction. |

## Automated-check failures

Use the approved global Python and project root. Test fixtures are small and fictional; API access is mocked where necessary. A missing credential must not make the deterministic test suite depend on a live account. Investigate the first relevant failing assertion and its owner rather than changing unrelated packages or weakening checks.

When reporting a failure, include the action, safe error category, expected/observed behavior, relevant file/test name, and whether the result was mocked, in-process, browser-observed, or live. Update PROGRESS with unresolved impact instead of claiming success.


## Provider chain checks

Read safe acceptance feedback for the actual successful route. The primary can
return a temporary503 high-demand response even when its key/model metadata work;
the configured Groq route can then be used. Groq has its own key and quota. Both
Gemini models share a key, so a known invalid Gemini key skips its reserve.
A final no-route error preserves the workspace; correct configuration or wait for
provider recovery before another explicit request.

Structured wire schemas differ by provider. Gemini receives its supported inlined
subset; Groq receives a strict structural JSON schema. Local length, field,
validation remains mandatory; evidence and duplicate checks provide advisory review notes. The Groq client uses an
application User-Agent because the default Python identifier was rejected in
live testing. A location mismatch flags the topic for manual review and does not
trigger a repair call or another model. Request assembly includes
a structured index of exact available source-location labels to reduce such errors.
