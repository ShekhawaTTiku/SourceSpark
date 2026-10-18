# Project Guide

This guide explains SourceSpark as a product. [PROJECT_SPEC.md](../PROJECT_SPEC.md) owns requirements; [PROGRESS.md](PROGRESS.md) records the checks actually completed. The existence of an interface or this guide is not evidence of live Gemini account access.

## Purpose and intended user

The application helps one person turn waste-related documents into communication topics with traceable supporting evidence. It runs locally in Streamlit (the Python framework that builds the page). The result is a planning report, not a finished social post, an image, or a publishing service.

The central object is a workspace (reusable sources, topics, exclusions, and one active plan). A plan is an ordered selection from that library. A campaign is one kind of plan; it does not define the whole application.

## One example throughout the project

Greenfield School is fictional. Suppose its waste report describes which classrooms have labelled bins, and its sorting guide explains those labels. A user adds both documents and checks their extracted text. The user supplies an optional brief such as an audience of students and a goal of explaining the documented labels.

The application requests source-supported topic suggestions. The user reviews their context and quotations, selects useful topics, assigns them to days or a campaign order, and explicitly finalizes the plan. If the documents support only three distinct ideas, the application retains those three rather than inventing extra claims.

These fictional examples teach behavior. They are not measured waste statistics or results of a live provider call.

## Planning choices

| Choice | Intended behavior |
| --- | --- |
| Five-day Week | Five consecutive days from the chosen start, one topic per day. |
| Seven-day Week | Seven consecutive days from the chosen start, one topic per day. |
| Targeted Campaign | A positive user-selected topic target. |
| Open Campaign | An ordered selection without a required target. |

New plans use a four-step setup: Weekly/Campaign, size, start date, then optional additional information. Audience, goal and guidance only appear after checking Yes. Sources, Topics and Finish are separate workspace screens. Campaigns retain their start date as plan metadata; weekly day names and dates follow the chosen start, and the entire five/seven-day range must fit the supported calendar. Older snapshots without dates or with open campaign targets still reopen. Empty weekly slots remain visible, including in a deliberately shorter finalized report.

Reaching a target means ready for review. Only the user's finalize action makes it finalized. A nonempty shorter plan can be finalized after acknowledging unfilled slots. An empty plan cannot become a substantive exported report. Reopen the finalized plan before changing its content.

## What the user can control

Users name the workspace and active plan, choose mode and optional target, and edit the audience, goal, and additional guidance. These brief fields influence relevance; they cannot supply missing factual evidence.

Selecting adds a library topic to the active plan. Deselecting keeps the topic for later use. Excluding also remembers its angle as something future generation should avoid. Restoring makes the topic available again without automatically selecting it. Moving a topic or assigning a weekday changes its position without asking Gemini for anything.

Newly generated topics enter the Available library and require manual selection. Green means local source checks passed; red means needs review, with a reason. Both remain selectable. Selecting hides that topic's review label, and exports do not add an unverified-source label. Deselecting shows its review status again. Quote matching tolerates harmless formatting differences; these checks and review actions use no extra AI validation or repair call.

Starting a new plan retains documents, the topic library, and exclusions. Starting a new empty workspace is a separate destructive replacement that the interface confirms. There is one active plan; older plans are retained only in snapshots the user deliberately saves.

## Sources and evidence

Supported inputs are PDF, DOCX, CSV, and XLSX. PDF pages need selectable text; image recognition is outside this version. Word body paragraphs and tables are read. Spreadsheet summaries use all loaded data rows even though individual row previews are bounded. Excel formulas use stored results; the application does not recalculate them.

An evidence reference names the source, location, and supporting excerpt. Inspect warnings as well as text. A cited source cannot be removed while any retained topic depends on it, including excluded topics that may be restored.

## Generation, size, and recovery

Generate or Find more topics is explicit. Uploading, reviewing, changing days, saving, reopening, or ordinary page reruns do not initiate generation. Each request asks for at most ten candidates. Multiple successful requests can build a campaign larger than ten; batch size and campaign size are different.

Resource guards still apply: ten MiB per source, twenty source files, fifty MiB total original source sizes, bounded extraction and complete request context, and a twenty MiB workspace snapshot. Snapshots also have a ten-thousand-topic record guard. These are operational safeguards, not a promise that any campaign can produce an arbitrary number of distinct supported ideas.

An unsuccessful request preserves earlier sources, topics, selections, exclusions, and settings. Zero accepted new topics is a valid outcome, accompanied by feedback. Additional rounds cannot guarantee more ideas.

## Reports, saving, and privacy

Finalized selections download as readable Markdown or Excel-compatible CSV. Both retain order, topic context, evidence, and relevant warnings. CSV includes explicit unfilled weekly rows and protects cells that resemble spreadsheet formulas.

Save workspace creates a portable, versioned working snapshot that can be reopened after validation. It contains extracted document content, so treat it as private material. It is not encrypted and is not an autosave service. Raw original files, API credentials, environment contents, and client objects are not included. Reopening restores extracted evidence, not an original PDF or workbook for re-extraction.

Reading, planning, export, and saving happen locally. Explicit generation sends extracted source information, the brief and remembered angles to Gemini, and potentially Groq on operational failure. The route is Gemini 3.6 Flash, Groq GPT-OSS 120B, then Gemini 3.8 Flash reserve; safe feedback identifies which model completed the round. Account credentials, model availability, pricing, and live generation quality require separate verification; see [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md).

Continue with [DATA_FLOW.md](DATA_FLOW.md) to understand how this behavior is implemented.
