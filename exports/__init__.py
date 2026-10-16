"""Reports contain finalized selections; snapshots belong to storage instead."""

from datetime import timedelta
from typing import Iterator

from pydantic import ValidationError

from models.topic import TopicIdea
from models.workspace import Workspace


DAY_NAMES = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")


def validate_export_workspace(workspace: Workspace) -> Workspace:
    """Revalidate before exporting, including evidence and finalized plan coherence."""
    try:
        checked = Workspace.model_validate(workspace.model_dump(mode="python"))
    except (ValidationError, TypeError, ValueError):
        raise ValueError("The workspace is inconsistent; review the plan before exporting.") from None
    if checked.busy:
        raise ValueError("Wait until processing finishes before exporting.")
    if checked.plan.status != "FINALIZED" or not checked.plan.selected_topic_ids:
        raise ValueError("Finalize a nonempty plan before exporting.")
    return checked


def plan_rows(workspace: Workspace) -> Iterator[tuple[int, str, str, TopicIdea | None]]:
    """Yield authoritative rows, retaining unfilled weekly slots and selected order."""
    plan = workspace.plan
    topics = {topic.topic_id: topic for topic in workspace.topics}
    if plan.mode == "Week":
        for day in range(plan.weekly_days):
            topic_id = plan.day_assignments.get(day)
            assigned_date = (plan.start_date + timedelta(days=day)).isoformat() if plan.start_date else ""
            yield day + 1, DAY_NAMES[day], assigned_date, topics.get(topic_id)
    else:
        for index, topic_id in enumerate(plan.selected_topic_ids, start=1):
            yield index, "", "", topics[topic_id]


def topic_warnings(workspace: Workspace, topic: TopicIdea | None) -> list[str]:
    if topic is None:
        return []
    cited = {reference.document_id for reference in topic.sources}
    return [f"{document.filename}: {warning}"
            for document in workspace.documents if document.document_id in cited
            for warning in document.warnings]
