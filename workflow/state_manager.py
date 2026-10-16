"""Workspace memory and source changes, independent of Streamlit."""

from datetime import datetime, timezone
import hashlib
from pathlib import PureWindowsPath

from config.settings import MAX_CAMPAIGN_BYTES, MAX_DOCUMENTS, MAX_FILE_BYTES
from models.plan import Plan
from models.workspace import DocumentRecord, Workspace


def commit(workspace: Workspace, **changes: object) -> None:
    """Validate a complete candidate before atomically replacing working fields."""
    payload = workspace.model_dump()
    payload.update(changes)
    payload['modified_at'] = datetime.now(timezone.utc)
    candidate = Workspace.model_validate(payload)
    workspace.__dict__.update(candidate.__dict__)


def require_idle(workspace: Workspace) -> None:
    """Reject concurrent actions while a request or replacement is in flight."""
    if workspace.busy:
        raise ValueError('Wait for the current operation to finish.')


def require_editable(workspace: Workspace) -> None:
    """Protect finalized authoritative selections until explicitly reopened."""
    require_idle(workspace)
    if workspace.plan.status == 'FINALIZED':
        raise ValueError('Reopen the plan for editing first, or start a new plan.')


def create_document(
    filename: str, file_bytes: bytes, content: str,
    warnings: tuple[str, ...] = (), locations: dict[str, str] | None = None,
) -> DocumentRecord:
    """Build source provenance from already extracted text; do not parse bytes here."""
    if not filename or PureWindowsPath(filename).name != filename or '/' in filename:
        raise ValueError('Use a plain source filename without directory paths.')
    extension = PureWindowsPath(filename).suffix.lower().lstrip('.')
    if extension not in {'pdf', 'docx', 'xlsx', 'csv'}:
        raise ValueError('Choose a PDF, Word, Excel, or CSV file.')
    if not file_bytes or len(file_bytes) > MAX_FILE_BYTES:
        raise ValueError('Source files must be nonempty and no larger than 10 MiB.')
    blocks = locations or {'Extracted text': content.strip()}
    canonical = '\n\n'.join(f'[{label}]\n{text}' for label, text in blocks.items())
    return DocumentRecord(
        document_id=hashlib.sha256(file_bytes).hexdigest(), filename=filename,
        file_type=extension, size_bytes=len(file_bytes), content=canonical,
        locations=blocks, warnings=list(warnings),
    )


def add_document(workspace: Workspace, document: DocumentRecord) -> str:
    """Add one source transactionally or explain why identical content was skipped."""
    require_editable(workspace)
    for existing in workspace.documents:
        if existing.document_id == document.document_id:
            return f'Duplicate content skipped; retained {existing.filename}.'
    if any(item.filename.casefold() == document.filename.casefold()
           for item in workspace.documents):
        raise ValueError('Different content has this filename. Rename the new file first.')
    if len(workspace.documents) >= MAX_DOCUMENTS:
        raise ValueError('The workspace already has 20 source documents.')
    total = sum(item.size_bytes for item in workspace.documents) + document.size_bytes
    if total > MAX_CAMPAIGN_BYTES:
        raise ValueError('The source pool would exceed 50 MiB.')
    commit(workspace, documents=[*workspace.documents, document],
           pool_revision=workspace.pool_revision + 1)
    return f'Added {document.filename}.'


def remove_document(workspace: Workspace, document_id: str) -> None:
    """Remove an uncited source; excluded retained topics still protect evidence."""
    require_editable(workspace)
    if any(source.document_id == document_id
           for topic in workspace.topics for source in topic.sources):
        raise ValueError('A retained topic cites this source. Start a new workspace to replace it.')
    remaining = [item for item in workspace.documents if item.document_id != document_id]
    if len(remaining) == len(workspace.documents):
        raise ValueError('This source is not in the workspace.')
    commit(workspace, documents=remaining, pool_revision=workspace.pool_revision + 1)


def rename_workspace(workspace: Workspace, name: str) -> None:
    """Update the user-facing name without interpreting it as a local path."""
    require_idle(workspace)
    commit(workspace, name=name)


def new_plan(workspace: Workspace, name: str = 'New plan') -> None:
    """Replace only the active plan while preserving sources, library and exclusions."""
    require_idle(workspace)
    commit(workspace, plan=Plan(name=name), sufficiency_note='', feedback=[])


def reset_workspace(workspace: Workspace) -> None:
    """Replace all working data after the interface has confirmed the user's intent."""
    require_idle(workspace)
    candidate = Workspace()
    workspace.__dict__.update(candidate.__dict__)
