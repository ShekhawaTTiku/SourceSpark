"""Native Streamlit screens; all planning and processing rules live in their owners."""

from datetime import date, timedelta
import hashlib
from typing import Callable, Any

import streamlit as st
from pydantic import ValidationError

from config import settings
from models.workspace import Workspace
from workflow import plan_manager as plans
from workflow import state_manager as state
from workflow.planning_service import generate_batch, ingest_files

DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']


def notify(message: str) -> None:
    """Retain brief feedback across the next ordinary rerun."""
    st.session_state['notice'] = message


def error_message(error: Exception) -> str:
    """Explain validation without copying private record values into error output."""
    if isinstance(error, ValidationError):
        return '; '.join(item['msg'] for item in error.errors(include_input=False))
    return str(error)


def act(action: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
    """Run an explicit local action, report failures, and redraw only after success."""
    try:
        result = action(*args, **kwargs)
        notify(result if isinstance(result, str) else 'Updated.')
    except (ValueError, RuntimeError) as error:
        st.error(error_message(error))
    else:
        st.rerun()


def initialize() -> Workspace:
    """Initialize one isolated workspace per browser session, not a shared cache."""
    if 'workspace' not in st.session_state:
        st.session_state['workspace'] = Workspace()
    st.session_state.setdefault('ui_epoch', 0)
    st.session_state.setdefault('upload_epoch', 0)
    st.session_state.setdefault('last_saved_digest', None)
    return st.session_state['workspace']


def workspace_digest(workspace: Workspace) -> str:
    """Compare meaningful working state with the latest explicit download/load action."""
    payload = workspace.model_dump_json(exclude={'busy'})
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()


def remember_snapshot(digest: str) -> None:
    """Mark the prepared snapshot without claiming its download was retained on disk."""
    st.session_state['last_saved_digest'] = digest


def render_header(workspace: Workspace) -> None:
    """Explain the current workspace, counts, temporary memory and cloud boundary."""
    st.caption('SOURCESPARK · EVIDENCE TO IDEAS')
    st.title(settings.APP_TITLE)
    st.write('Build a weekly plan or campaign from your documents, with evidence you can inspect.')
    if st.session_state.get('notice'):
        st.info(st.session_state.pop('notice'))
    with st.container(horizontal=True):
        st.metric('Sources', len(workspace.documents))
        st.metric('Topic library', len(workspace.topics))
        st.metric('Selected', len(workspace.plan.selected_topic_ids))
        st.metric('Excluded', len(workspace.excluded_topic_ids))
    st.caption(
        'Session memory is temporary. Save a workspace file to continue after closing or '
        'restarting. Parsing runs on this PC; generation uses Google Gemini, with Groq as a fallback.'
    )


def render_workspace(workspace: Workspace) -> None:
    """Offer explicit portable snapshots and guarded replacement/reset operations."""
    from storage.workspace_store import load_workspace, save_workspace

    with st.sidebar:
        st.header('Workspace')
        epoch = st.session_state['ui_epoch']
        with st.form(f'workspace_name_{epoch}'):
            name = st.text_input('Workspace name', value=workspace.name, max_chars=200)
            if st.form_submit_button('Save workspace name', disabled=workspace.busy):
                act(state.rename_workspace, workspace, name)
        digest = workspace_digest(workspace)
        dirty = digest != st.session_state.get('last_saved_digest')
        st.caption('Changes since the last snapshot action.' if dirty else 'Snapshot is up to date.')
        st.caption(
            'Save includes extracted document text and metadata, not original files or API keys. '
            'The file is not encrypted. Keep the downloaded file somewhere suitable.'
        )
        try:
            snapshot = save_workspace(workspace)
            st.download_button(
                'Save workspace file', snapshot, file_name='waste-awareness.workspace.json',
                mime='application/json', key='save_workspace', on_click=remember_snapshot,
                args=(digest,), disabled=workspace.busy,
            )
        except ValueError as error:
            st.warning(error_message(error))
        with st.expander('Reopen a saved workspace'):
            uploaded = st.file_uploader(
                'Workspace file', type=['json'], max_upload_size=20, key=f'workspace_load_{epoch}',
                disabled=workspace.busy,
            )
            replace_ok = st.checkbox('Replace my current unsaved work', key=f'load_ok_{epoch}')
            if st.button('Validate and reopen', key='load_workspace',
                         disabled=workspace.busy or uploaded is None or (dirty and not replace_ok)):
                try:
                    candidate = load_workspace(uploaded.getvalue())
                except ValueError as error:
                    st.error(error_message(error))
                else:
                    st.session_state['workspace'] = candidate
                    st.session_state['ui_epoch'] += 1
                    st.session_state['upload_epoch'] += 1
                    st.session_state['last_saved_digest'] = workspace_digest(candidate)
                    notify('Workspace reopened. Extracted sources are available; original uploads are not.')
                    st.rerun()
        with st.expander('Start another plan or workspace'):
            st.caption('A new plan keeps sources, topic records and exclusions. A new workspace clears them.')
            confirm = st.checkbox('I have saved anything I want to keep', key=f'reset_ok_{epoch}')
            if st.button('New plan — keep sources and topics', key='new_plan',
                         disabled=workspace.busy or not confirm):
                state.new_plan(workspace)
                st.session_state['ui_epoch'] += 1
                notify('New plan created. Your sources, topic library and exclusions remain available.')
                st.rerun()
            if st.button('New empty workspace', key='reset_workspace',
                         disabled=workspace.busy or not confirm):
                state.reset_workspace(workspace)
                st.session_state['ui_epoch'] += 1
                st.session_state['upload_epoch'] += 1
                st.session_state['last_saved_digest'] = None
                notify('Started a new empty workspace.')
                st.rerun()


def render_plan_setup(workspace: Workspace) -> None:
    """Collect a deliberate mode/brief update; ordinary field edits never generate."""
    st.header('1. Set up your plan')
    plan = workspace.plan
    locked = workspace.busy or plan.status == 'FINALIZED'
    if plan.status == 'FINALIZED':
        st.success('This plan is finalized. Reopen it below to make changes.')
    with st.form(f'plan_setup_{st.session_state["ui_epoch"]}'):
        name = st.text_input('Plan name', value=plan.name, max_chars=200, disabled=locked)
        mode = st.selectbox('Planning mode', ['Week', 'Campaign'],
                            index=0 if plan.mode == 'Week' else 1,
                            key=f'planning_mode_{st.session_state["ui_epoch"]}', disabled=locked)
        weekly_days = st.selectbox('Weekly slots (Week mode)', [5, 7],
                                   index=0 if plan.weekly_days == 5 else 1, disabled=locked)
        use_target = st.checkbox('Set a campaign target (optional)', value=plan.target is not None,
                                 disabled=locked)
        # Text avoids JavaScript's integer bound when reopening a large valid target.
        target = st.text_input('Campaign target (positive whole number, when enabled)',
                               value=str(plan.target or 15), disabled=locked)
        use_dates = st.checkbox('Assign weekly dates (optional)', value=plan.start_date is not None,
                                disabled=locked)
        start = st.date_input('Week beginning on Monday', value=plan.start_date,
                              min_value=date.min, max_value=date.max, disabled=locked)
        audience = st.text_input('Target audience (optional)', value=plan.audience,
                                 max_chars=500, disabled=locked)
        goal = st.text_area('Communication goal (optional)', value=plan.goal,
                            max_chars=2000, disabled=locked)
        guidance = st.text_area('Planning context or guidance (optional)', value=plan.guidance,
                                max_chars=4000, disabled=locked)
        st.caption('Your brief guides relevance. Factual claims still need documentary evidence.')
        if st.form_submit_button('Apply plan settings', disabled=locked):
            if mode == 'Week' and use_dates and start is None:
                st.error('Choose a Monday or turn off weekly dates.')
            elif mode == 'Campaign' and use_target and (
                not target.strip().isascii() or not target.strip().isdigit()
                or int(target.strip()) < 1
            ):
                st.error('Enter a positive whole-number campaign target, or turn the target off.')
            else:
                act(plans.configure_plan, workspace, name=name, mode=mode,
                    weekly_days=weekly_days,
                    target=int(target.strip()) if mode == 'Campaign' and use_target else None,
                    audience=audience, goal=goal, guidance=guidance,
                    start_date=start if use_dates else None)
    target_label = str(plan.effective_target) if plan.effective_target is not None else 'Open-ended'
    st.write(f'Active plan: **{plan.name}** · {plan.mode} · Target: **{target_label}**')
    if plan.remaining_slots is not None:
        st.caption(f'{len(plan.selected_topic_ids)} selected · {plan.remaining_slots} unfilled slot(s)')


def render_sources(workspace: Workspace) -> None:
    """Read only intentional additions, then expose the exact eligible source context."""
    from documents.context_builder import build_context

    st.header('2. Add and inspect sources')
    locked = workspace.busy or workspace.plan.status == 'FINALIZED'
    uploads = st.file_uploader(
        'Source documents', type=['pdf', 'docx', 'xlsx', 'csv'], accept_multiple_files=True,
        max_upload_size=10, key=f'sources_{st.session_state["upload_epoch"]}', disabled=locked,
        help='Up to 20 files, 10 MiB each and 50 MiB total. PDFs need selectable text.',
    )
    if st.button('Add documents', key='add_documents', disabled=locked or not uploads):
        with st.spinner('Reading selected documents locally…'):
            messages = ingest_files(workspace, [(item.name, item.getvalue()) for item in uploads])
        notify('\n\n'.join(messages))
        st.session_state['upload_epoch'] += 1
        st.rerun()
    if not workspace.documents:
        st.info('Add a report, guidance document or table to provide evidence for your topics.')
    for document in workspace.documents:
        with st.expander(f'{document.filename} · {document.file_type.upper()}'):
            st.caption(f'{document.size_bytes:,} bytes · {document.character_count:,} extracted characters')
            for warning in document.warnings:
                st.warning(warning)
            st.text(document.content)
            cited = any(ref.document_id == document.document_id
                        for topic in workspace.topics for ref in topic.sources)
            if cited:
                st.caption('Retained topics cite this source, so its evidence is protected.')
            if st.button('Remove source', key=f'remove_{document.document_id}',
                         disabled=locked or cited):
                act(state.remove_document, workspace, document.document_id)
    if workspace.documents:
        with st.expander('Inspect combined evidence sent for generation'):
            try:
                context = build_context(workspace.documents)
            except ValueError as error:
                st.error(error_message(error))
            else:
                st.caption(f'{len(context):,} characters. Prior topics and your brief also enter the request.')
                st.text(context)


def render_generation(workspace: Workspace) -> None:
    """Make a network request only inside this explicit button action."""
    st.header('3. Generate supported topics')
    configured = bool(
        (settings.GEMINI_API_KEY and (settings.GEMINI_MODEL or settings.GEMINI_FALLBACK_MODEL))
        or (settings.GROQ_API_KEY and settings.GROQ_MODEL)
    )
    if not configured:
        st.info(
            'Add GEMINI_API_KEY and GROQ_API_KEY to your local .env to enable both providers. '
            'Generation can use either configured provider. Restart after configuration changes.'
        )
    st.caption(
        'This action sends extracted source content, your brief and remembered angles to Google '
        'Gemini. On operational failure it may send the same material to Groq, then the alternate '
        'Gemini model. Check that the documents are suitable for both providers. '
        'No minimum number of ideas is guaranteed.'
    )
    st.caption(
        f'Order: Gemini {settings.GEMINI_MODEL} → Groq {settings.GROQ_MODEL} → '
        f'Gemini {settings.GEMINI_FALLBACK_MODEL or "reserve disabled"}.'
    )
    batch = st.number_input('Maximum candidates in this request', min_value=1, max_value=10,
                            value=10, step=1, key='batch_size')
    locked = workspace.busy or workspace.plan.status == 'FINALIZED'
    full = workspace.plan.remaining_slots == 0
    if full:
        st.info('The target is filled. Review the plan, or deselect topics/change its target before generating.')
    label = 'Find more topics' if workspace.topics else 'Generate topics'
    if st.button(label, key='generate_topics', type='primary',
                 disabled=locked or full or not configured or not workspace.documents):
        try:
            with st.spinner('Checking evidence and generating a candidate batch…'):
                messages = generate_batch(workspace, int(batch))
        except (ValueError, RuntimeError) as error:
            st.session_state['generation_failed'] = True
            st.error(error_message(error))
        else:
            st.session_state['generation_failed'] = False
            notify('\n\n'.join(messages))
            st.rerun()
    if st.session_state.get('generation_failed'):
        st.caption('Your workspace was retained. Correct the issue and use Generate/Find more to retry.')
    if workspace.sufficiency_note:
        st.write(workspace.sufficiency_note)
    with st.expander('Latest acceptance feedback'):
        for message in workspace.feedback:
            st.write(message)


def render_topic_details(topic: Any) -> None:
    """Show claims/context and explicit evidence without hiding limitations."""
    st.write(topic.core_insight)
    st.write(topic.context)
    st.caption(f'Audience: {topic.target_audience} · Format: {topic.suggested_format}')
    with st.expander('Supporting evidence'):
        for source in topic.sources:
            st.caption(f'{source.filename} · {source.location}')
            st.text(source.excerpt)
    if topic.origin == 'sample':
        st.warning('This topic is based on fictional learning material.')


def render_library(workspace: Workspace) -> None:
    """Review a paged reusable library; changing any control here never calls Gemini."""
    st.header('4. Review the topic library')
    st.caption('Select includes a topic in this plan. Deselect keeps it available. Exclude avoids its angle in later generation.')
    category = st.selectbox('Show topics', ['Available', 'Selected', 'Excluded', 'All'], key='topic_filter')
    selected, excluded = set(workspace.plan.selected_topic_ids), set(workspace.excluded_topic_ids)
    topics = [topic for topic in workspace.topics if (
        category == 'All' or (category == 'Selected' and topic.topic_id in selected)
        or (category == 'Excluded' and topic.topic_id in excluded)
        or (category == 'Available' and topic.topic_id not in selected | excluded)
    )]
    if not topics:
        st.caption('No topics in this view yet.')
        return
    pages = max(1, (len(topics) + 9) // 10)
    page = st.selectbox('Library page', range(1, pages + 1), key=f'library_page_{category}_{pages}')
    locked = workspace.busy or workspace.plan.status == 'FINALIZED'
    for topic in topics[(page - 1) * 10:page * 10]:
        identity = topic.topic_id
        with st.container(border=True):
            st.subheader(topic.title)
            render_topic_details(topic)
            with st.container(horizontal=True):
                if identity in excluded:
                    if st.button('Restore', key=f'restore_{identity}', disabled=locked):
                        act(plans.restore_topic, workspace, identity)
                else:
                    if identity in selected:
                        if st.button('Deselect', key=f'deselect_{identity}', disabled=locked):
                            act(plans.deselect_topic, workspace, identity)
                    elif st.button('Select for plan', key=f'select_{identity}',
                                   disabled=locked or workspace.plan.remaining_slots == 0):
                        act(plans.select_topic, workspace, identity)
                    if st.button('Exclude angle', key=f'exclude_{identity}', disabled=locked):
                        act(plans.exclude_topic, workspace, identity)


def render_active_plan(workspace: Workspace) -> None:
    """Organize selected topics, explicitly finalize, then export only current selections."""
    from exports.csv_exporter import export_csv
    from exports.markdown_exporter import export_markdown

    st.header('5. Arrange and finish your plan')
    plan = workspace.plan
    st.write(f'Status: **{plan.status.replace("_", " ").title()}**')
    by_id = {topic.topic_id: topic for topic in workspace.topics}
    locked = workspace.busy or plan.status == 'FINALIZED'
    if plan.mode == 'Week':
        for day in range(plan.weekly_days):
            date_label = f' · {(plan.start_date + timedelta(days=day)).isoformat()}' if plan.start_date else ''
            topic = by_id.get(plan.day_assignments.get(day))
            st.write(f'**{DAYS[day]}{date_label}:** {topic.title if topic else "Unfilled"}')
    selected = list(plan.selected_topic_ids)
    pages = max(1, (len(selected) + 9) // 10)
    page = st.selectbox('Plan page', range(1, pages + 1), key=f'plan_page_{plan.plan_id}_{pages}')
    for identity in selected[(page - 1) * 10:page * 10]:
        topic = by_id[identity]
        index = selected.index(identity)
        with st.container(border=True):
            st.write(f'**{index + 1}. {topic.title}**')
            with st.container(horizontal=True):
                if st.button('Move up', key=f'up_{identity}', disabled=locked or index == 0):
                    act(plans.move_topic, workspace, identity, -1)
                if st.button('Move down', key=f'down_{identity}',
                             disabled=locked or index == len(selected) - 1):
                    act(plans.move_topic, workspace, identity, 1)
                if st.button('Remove from plan', key=f'unselect_{identity}', disabled=locked):
                    act(plans.deselect_topic, workspace, identity)
            if plan.mode == 'Week':
                current = next(day for day, item in plan.day_assignments.items() if item == identity)
                day = st.selectbox('Assign to day (occupied days swap)', range(plan.weekly_days),
                                   index=current, format_func=lambda value: DAYS[value],
                                   key=f'assign_{identity}_{current}', disabled=locked)
                if st.button('Apply day', key=f'day_{identity}', disabled=locked):
                    act(plans.assign_day, workspace, identity, day)
    if plan.status == 'FINALIZED':
        st.caption('Verify factual reasoning before public use. Downloads include selected topics and evidence only.')
        try:
            markdown, csv_data = export_markdown(workspace), export_csv(workspace)
            st.download_button('Download Markdown report', markdown,
                               file_name='waste-awareness-plan.md', mime='text/markdown',
                               key='download_markdown', on_click='ignore')
            st.download_button('Download CSV plan', csv_data,
                               file_name='waste-awareness-plan.csv', mime='text/csv',
                               key='download_csv', on_click='ignore')
        except ValueError as error:
            st.error(error_message(error))
        if st.button('Reopen plan for editing', key='reopen_plan', disabled=workspace.busy):
            act(plans.reopen_plan, workspace)
    else:
        acknowledgement = False
        if plan.remaining_slots:
            st.warning(f'{plan.remaining_slots} slot(s) remain unfilled. Add sources, select available topics, or approve a shorter plan.')
            acknowledgement = st.checkbox(
                'I want to finalize this shorter plan',
                key=f'shortfall_ok_{plan.plan_id}_{plan.remaining_slots}',
            )
        if st.button('Finalize reviewed plan', key='finalize_plan', type='primary',
                     disabled=workspace.busy or not selected):
            act(plans.finalize_plan, workspace, acknowledgement)
