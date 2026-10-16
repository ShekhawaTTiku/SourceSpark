"""Excel-compatible CSV with proper quoting and spreadsheet formula protection."""

import csv
from io import StringIO

from exports import plan_rows, topic_warnings, validate_export_workspace
from models.workspace import Workspace


CSV_COLUMNS = [
    "workspace_name", "plan_name", "plan_mode", "plan_status", "finalized_at",
    "target", "selected_count", "unfilled_slots", "shortfall_acknowledged",
    "brief_audience", "brief_goal", "brief_guidance", "order", "weekday", "date",
    "slot_status", "topic_title", "topic_context", "core_insight", "target_audience",
    "suggested_format", "evidence_references", "extraction_warnings", "origin",
]


def _safe_cell(value: object) -> str:
    text = "" if value is None else str(value)
    # Spreadsheet programs may ignore whitespace before a formula marker.
    if text.lstrip().startswith(("=", "+", "-", "@")) or text.startswith(("\t", "\r", "\n")):
        return "'" + text
    return text


def export_csv(workspace: Workspace) -> bytes:
    workspace = validate_export_workspace(workspace)
    plan = workspace.plan
    output = StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=CSV_COLUMNS)
    writer.writeheader()
    for order, day, assigned_date, topic in plan_rows(workspace):
        evidence = "\n".join(
            f"{item.filename} | {item.location} | {item.excerpt} | source_id={item.document_id}"
            for item in topic.sources
        ) if topic else ""
        row = {
            "workspace_name": workspace.name, "plan_name": plan.name,
            "plan_mode": plan.mode, "plan_status": plan.status,
            "finalized_at": plan.finalized_at.isoformat(),
            "target": plan.effective_target, "selected_count": len(plan.selected_topic_ids),
            "unfilled_slots": plan.remaining_slots,
            "shortfall_acknowledged": plan.shortfall_acknowledged,
            "brief_audience": plan.audience, "brief_goal": plan.goal,
            "brief_guidance": plan.guidance, "order": order, "weekday": day,
            "date": assigned_date, "slot_status": "Assigned" if topic else "Unfilled",
            "topic_title": topic.title if topic else "", "topic_context": topic.context if topic else "",
            "core_insight": topic.core_insight if topic else "",
            "target_audience": topic.target_audience if topic else "",
            "suggested_format": topic.suggested_format if topic else "",
            "evidence_references": evidence,
            "extraction_warnings": "\n".join(topic_warnings(workspace, topic)),
            "origin": topic.origin if topic else "",
        }
        writer.writerow({key: _safe_cell(value) for key, value in row.items()})
    return output.getvalue().encode("utf-8-sig")
