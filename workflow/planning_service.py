"""Coordinate explicit ingestion/generation actions without rendering a screen."""

import hashlib
import json
from typing import Any

from pydantic import ValidationError

from config.settings import MAX_BATCH_TOPICS
from models.plan import Plan
from models.workspace import Workspace
from workflow.plan_manager import batch_capacity
from workflow.state_manager import add_document, commit, require_editable
from workflow.topic_pool import accept_topics


def ingest_files(workspace: Workspace, files: list[tuple[str, bytes]]) -> list[str]:
    """Parse intentional additions independently so one bad file cannot erase valid ones."""
    from documents.file_router import parse_uploaded_file

    require_editable(workspace)
    feedback = []
    for filename, data in files:
        try:
            fingerprint = hashlib.sha256(data).hexdigest()
            existing = next((item for item in workspace.documents
                             if item.document_id == fingerprint), None)
            if existing is not None:
                feedback.append(f'Duplicate content skipped; retained {existing.filename}.')
                continue
            document = parse_uploaded_file(filename, data)
            feedback.append(add_document(workspace, document))
        except ValidationError:
            feedback.append(f'{filename}: extracted source validation failed; no source was added.')
        except (ValueError, RuntimeError) as error:
            # Parser errors are sanitized by their owners; do not show raw document bodies.
            feedback.append(f'{filename}: {error}')
    return feedback


def request_fingerprint(workspace: Workspace, capacity: int, round_number: int) -> str:
    """Identify explicit rounds and relevant data, excluding mere display changes."""
    payload = {
        'source_revision': workspace.pool_revision,
        'documents': [item.document_id for item in workspace.documents],
        'brief': [workspace.plan.audience, workspace.plan.goal, workspace.plan.guidance],
        'mode': workspace.plan.mode, 'target': workspace.plan.effective_target,
        'topics': [item.model_dump() for item in workspace.topics],
        'excluded': workspace.excluded_topic_ids,
        'capacity': capacity, 'round': round_number,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode('utf-8')).hexdigest()


def generate_batch(
    workspace: Workspace, requested: int = MAX_BATCH_TOPICS, provider: Any = None,
) -> list[str]:
    """Run one reserved batch and merge atomically; release busy on every failure."""
    from ai.topic_generator import generate_topics

    require_editable(workspace)
    if not workspace.documents:
        raise ValueError('Add a readable source document before generating topics.')
    capacity = batch_capacity(workspace, requested)
    if capacity == 0:
        raise ValueError('The plan target is full. Review it or change its selections/target.')
    round_number = workspace.request_round + 1
    fingerprint = request_fingerprint(workspace, capacity, round_number)
    # This object is session-owned: reserving before network work blocks a second UI action.
    workspace.busy = True
    try:
        result = generate_topics(workspace, capacity, provider=provider)
        accepted, feedback = accept_topics(workspace.topics, result.candidates, capacity)
        feedback = [*result.feedback, *feedback]
        plan_payload = workspace.plan.model_dump()
        selected = list(workspace.plan.selected_topic_ids)
        assignments = dict(workspace.plan.day_assignments)
        for topic in accepted:
            selected.append(topic.topic_id)
            if workspace.plan.mode == 'Week':
                day = next(slot for slot in range(workspace.plan.weekly_days)
                           if slot not in assignments)
                assignments[day] = topic.topic_id
        if workspace.plan.mode == 'Week':
            selected = [assignments[day] for day in sorted(assignments)]
        target = workspace.plan.effective_target
        ready = bool(selected) and (target is None or len(selected) == target)
        plan_payload.update(
            selected_topic_ids=selected, day_assignments=assignments,
            status='READY_FOR_REVIEW' if ready else 'DRAFT',
        )
        documents = [item.model_copy(update={'participated': True})
                     for item in workspace.documents]
        if not accepted:
            feedback.append(
                'No new distinct supported topics were accepted. Add more useful sources '
                'or deliberately try another round; additional ideas are not guaranteed.'
            )
        else:
            feedback.insert(0, f'Added {len(accepted)} supported candidate topics for review.')
        commit(
            workspace, topics=[*workspace.topics, *accepted], documents=documents,
            plan=Plan.model_validate(plan_payload), busy=False, request_round=round_number,
            last_successful_request=fingerprint, sufficiency_note=result.sufficiency_note,
            feedback=feedback,
        )
        return feedback
    finally:
        # A failure cannot consume the round or replace libraries; retry uses existing inputs.
        workspace.busy = False
