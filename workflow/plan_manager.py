"""Mode-specific plan rules shared by every interface and generation path."""

from datetime import date, datetime, timezone
from typing import Any

from config.settings import MAX_BATCH_TOPICS
from models.plan import Plan
from models.workspace import Workspace
from workflow.state_manager import commit, require_editable, require_idle


def draft_plan(workspace: Workspace, **changes: Any) -> Plan:
    """Construct a validated editable plan with readiness derived from selection."""
    payload = workspace.plan.model_dump()
    payload.update(changes)
    payload.update(finalized_at=None, shortfall_acknowledged=False)
    target = payload['weekly_days'] if payload['mode'] == 'Week' else payload['target']
    selected = payload['selected_topic_ids']
    ready = bool(selected) and (target is None or len(selected) == target)
    payload['status'] = 'READY_FOR_REVIEW' if ready else 'DRAFT'
    return Plan.model_validate(payload)


def configure_plan(
    workspace: Workspace, *, name: str, mode: str, weekly_days: int = 5,
    target: int | None = None, audience: str = '', goal: str = '',
    guidance: str = '', start_date: date | None = None,
) -> None:
    """Apply a brief/mode change, refusing to silently discard excess selections."""
    require_editable(workspace)
    selected = list(workspace.plan.selected_topic_ids)
    limit = weekly_days if mode == 'Week' else target
    if limit is not None and len(selected) > limit:
        raise ValueError(
            f'This change has {limit} slots but {len(selected)} topics are selected. '
            'Deselect the topics you do not want first; all remain in the library.'
        )
    assignments = {}
    if mode == 'Week':
        if workspace.plan.mode == 'Week' and workspace.plan.weekly_days == weekly_days:
            assignments = dict(workspace.plan.day_assignments)
        else:
            assignments = dict(enumerate(selected))
    plan = draft_plan(
        workspace, name=name, mode=mode, weekly_days=weekly_days,
        target=target if mode == 'Campaign' else None,
        audience=audience, goal=goal, guidance=guidance,
        day_assignments=assignments, start_date=start_date if mode == 'Week' else None,
    )
    if plan != workspace.plan:
        commit(workspace, plan=plan)


def get_topic(workspace: Workspace, topic_id: str) -> Any:
    """Find a stable topic identity, rejecting stale widget references."""
    for topic in workspace.topics:
        if topic.topic_id == topic_id:
            return topic
    raise ValueError('This topic is not in the workspace library.')


def select_topic(workspace: Workspace, topic_id: str) -> None:
    """Select an available topic into the next vacant slot or campaign position."""
    require_editable(workspace)
    get_topic(workspace, topic_id)
    if topic_id in workspace.excluded_topic_ids:
        raise ValueError('Restore this excluded topic before selecting it.')
    if topic_id in workspace.plan.selected_topic_ids:
        return
    if workspace.plan.remaining_slots == 0:
        raise ValueError('The selected target is full. Deselect a topic or change the target.')
    selected = [*workspace.plan.selected_topic_ids, topic_id]
    assignments = dict(workspace.plan.day_assignments)
    if workspace.plan.mode == 'Week':
        slot = next(day for day in range(workspace.plan.weekly_days) if day not in assignments)
        assignments[slot] = topic_id
        selected = [assignments[day] for day in sorted(assignments)]
    commit(workspace, plan=draft_plan(
        workspace, selected_topic_ids=selected, day_assignments=assignments,
    ))


def deselect_topic(workspace: Workspace, topic_id: str) -> None:
    """Remove a selection without deleting the topic or compacting weekly gaps."""
    require_editable(workspace)
    get_topic(workspace, topic_id)
    selected = [item for item in workspace.plan.selected_topic_ids if item != topic_id]
    assignments = {day: item for day, item in workspace.plan.day_assignments.items()
                   if item != topic_id}
    commit(workspace, plan=draft_plan(
        workspace, selected_topic_ids=selected, day_assignments=assignments,
    ))


def exclude_topic(workspace: Workspace, topic_id: str) -> None:
    """Retain an unwanted angle for suppression and remove its active assignment."""
    require_editable(workspace)
    get_topic(workspace, topic_id)
    selected = [item for item in workspace.plan.selected_topic_ids if item != topic_id]
    assignments = {day: item for day, item in workspace.plan.day_assignments.items()
                   if item != topic_id}
    excluded = list(dict.fromkeys([*workspace.excluded_topic_ids, topic_id]))
    commit(workspace, excluded_topic_ids=excluded, plan=draft_plan(
        workspace, selected_topic_ids=selected, day_assignments=assignments,
    ))


def restore_topic(workspace: Workspace, topic_id: str) -> None:
    """Make an excluded record available without selecting it automatically."""
    require_editable(workspace)
    get_topic(workspace, topic_id)
    commit(workspace, excluded_topic_ids=[item for item in workspace.excluded_topic_ids
                                          if item != topic_id])


def move_topic(workspace: Workspace, topic_id: str, direction: int) -> None:
    """Move a selected topic one position, preserving vacant weekly day slots."""
    require_editable(workspace)
    if direction not in {-1, 1}:
        raise ValueError('Choose a move of one position up or down.')
    selected = list(workspace.plan.selected_topic_ids)
    if topic_id not in selected:
        raise ValueError('Select a topic before moving it.')
    index = selected.index(topic_id)
    destination = index + direction
    if destination < 0 or destination >= len(selected):
        return
    selected[index], selected[destination] = selected[destination], selected[index]
    assignments = dict(workspace.plan.day_assignments)
    if workspace.plan.mode == 'Week':
        assignments = dict(zip(sorted(assignments), selected))
    commit(workspace, plan=draft_plan(
        workspace, selected_topic_ids=selected, day_assignments=assignments,
    ))


def assign_day(workspace: Workspace, topic_id: str, day: int) -> None:
    """Assign a day; swapping occupied selected days never duplicates a topic."""
    require_editable(workspace)
    get_topic(workspace, topic_id)
    if workspace.plan.mode != 'Week' or day not in range(workspace.plan.weekly_days):
        raise ValueError('Choose a valid day in the current weekly plan.')
    if topic_id in workspace.excluded_topic_ids:
        raise ValueError('Restore this excluded topic first.')
    assignments = dict(workspace.plan.day_assignments)
    old_day = next((slot for slot, item in assignments.items() if item == topic_id), None)
    occupant = assignments.get(day)
    if old_day is None and occupant is not None:
        raise ValueError('That day is occupied. Deselect its topic or choose an empty day.')
    if old_day is not None:
        del assignments[old_day]
        if occupant is not None and occupant != topic_id:
            assignments[old_day] = occupant
    assignments[day] = topic_id
    selected = [assignments[slot] for slot in sorted(assignments)]
    commit(workspace, plan=draft_plan(
        workspace, day_assignments=assignments, selected_topic_ids=selected,
    ))


def finalize_plan(workspace: Workspace, acknowledge_shortfall: bool = False) -> None:
    """Freeze an explicit nonempty selection without making a provider request."""
    require_editable(workspace)
    if not workspace.plan.selected_topic_ids:
        raise ValueError('An empty plan cannot be finalized.')
    if workspace.plan.remaining_slots and not acknowledge_shortfall:
        raise ValueError('Acknowledge the unfilled slots before finalizing a shorter plan.')
    payload = workspace.plan.model_dump()
    payload.update(status='FINALIZED', finalized_at=datetime.now(timezone.utc),
                   shortfall_acknowledged=bool(workspace.plan.remaining_slots))
    commit(workspace, plan=Plan.model_validate(payload))


def reopen_plan(workspace: Workspace) -> None:
    """Invalidate finalization metadata before allowing changes or fresh exports."""
    require_idle(workspace)
    commit(workspace, plan=draft_plan(workspace))


def batch_capacity(workspace: Workspace, requested: int = MAX_BATCH_TOPICS) -> int:
    """Bound one explicit batch by vacancies, not by total library size."""
    require_editable(workspace)
    if isinstance(requested, bool) or not 1 <= requested <= MAX_BATCH_TOPICS:
        raise ValueError('Choose a batch size from one to ten.')
    remaining = workspace.plan.remaining_slots
    return requested if remaining is None else min(requested, remaining)
