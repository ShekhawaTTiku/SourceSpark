"""Readable reports of explicit finalized plans, not the whole topic library."""

import re

from exports import plan_rows, topic_warnings, validate_export_workspace
from models.workspace import Workspace


def _text(value: str) -> str:
    """Keep source text readable without interpreting it as report structure."""
    return re.sub(r"([\\`*_{}\[\]<>#!|])", r"\\\1", value)


def export_markdown(workspace: Workspace) -> str:
    workspace = validate_export_workspace(workspace)
    plan = workspace.plan
    target = str(plan.effective_target) if plan.effective_target is not None else "Open-ended"
    lines = [f"# {_text(plan.name)}", "", f"**Workspace:** {_text(workspace.name)}",
             f"**Mode:** {plan.mode}", "**Status:** FINALIZED",
             f"**Selected topics:** {len(plan.selected_topic_ids)}",
             f"**Target:** {target}", f"**Finalized at:** {plan.finalized_at.isoformat()}"]
    if plan.start_date:
        lines.append(f"**Start date:** {plan.start_date.isoformat()}")
    if plan.shortfall_acknowledged:
        lines.append(f"**Shorter plan approved:** {plan.remaining_slots} slot(s) remain unfilled.")
    if any((plan.audience, plan.goal, plan.guidance)):
        lines.extend(["", "## Planning brief", ""])
        for label, value in (("Audience", plan.audience), ("Goal", plan.goal), ("Guidance", plan.guidance)):
            if value:
                lines.append(f"**{label}:** {_text(value)}")
    lines.extend(["", "## Selected plan", ""])
    cited_ids: set[str] = set()
    for order, day, assigned_date, topic in plan_rows(workspace):
        label = f"{day}" if day else f"Topic {order}"
        if assigned_date:
            label += f" — {assigned_date}"
        lines.extend([f"### {label}", ""])
        if topic is None:
            lines.extend(["*Unfilled slot.*", ""])
            continue
        lines.extend([f"**{_text(topic.title)}**", "", _text(topic.context), "",
                      f"**Supported insight:** {_text(topic.core_insight)}", "",
                      f"**Audience:** {_text(topic.target_audience)}",
                      f"**Suggested format:** {_text(topic.suggested_format)}", "",
                      "**Evidence:**", ""])
        if topic.origin == "sample":
            lines.extend(["*Fictional sample topic; this is not a live AI result.*", ""])
        for reference in topic.sources:
            cited_ids.add(reference.document_id)
            excerpt = " ".join(reference.excerpt.split())
            lines.append(f"- {_text(reference.filename)} — {_text(reference.location)}: “{_text(excerpt)}”")
        warnings = topic_warnings(workspace, topic)
        if warnings:
            lines.extend(["", "**Extraction warnings:**", ""])
            lines.extend(f"- {_text(warning)}" for warning in warnings)
        lines.append("")
    lines.extend(["## Cited sources", ""])
    for document in workspace.documents:
        if document.document_id in cited_ids:
            lines.append(f"- {_text(document.filename)} ({document.file_type.upper()}); source ID: {document.document_id}.")
    lines.extend(["", "Evidence references identify extracted text; they do not guarantee that every interpretation is correct. Review factual claims before publication.", ""])
    return "\n".join(lines)
