"""Native Streamlit screens; all planning and processing rules live in their owners."""

from datetime import date, timedelta
import hashlib
from typing import Callable, Any

import streamlit as st
from pydantic import ValidationError

from config import settings
from ai.response_validator import review_candidate
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
    workspace = st.session_state['workspace']
    st.session_state.setdefault('setup_complete', bool(
        workspace.documents or workspace.topics or workspace.plan.start_date
        or workspace.plan.name != 'Untitled plan'
    ))
    st.session_state.setdefault('setup_editing', False)
    st.session_state.setdefault('workspace_view', 'Sources')
    return st.session_state['workspace']


def workspace_digest(workspace: Workspace) -> str:
    """Compare meaningful working state with the latest explicit download/load action."""
    payload = workspace.model_dump_json(exclude={'busy'})
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()


def remember_snapshot(digest: str) -> None:
    """Mark the prepared snapshot without claiming its download was retained on disk."""
    st.session_state['last_saved_digest'] = digest


def render_header(workspace: Workspace) -> None:
    """Keep the entry screen focused on the next decision."""
    st.caption('SOURCESPARK · EVIDENCE TO IDEAS')
    st.title('Turn your sources into a plan')
    st.write('A few choices, your documents, and a clear plan to work from.')
    if st.session_state.get('notice'):
        st.info(st.session_state.pop('notice'))


def render_workspace(workspace: Workspace) -> None:
    """Offer explicit portable snapshots and guarded replacement/reset operations."""
    from storage.workspace_store import save_workspace

    with st.sidebar:
        st.header('Workspace')
        epoch = st.session_state['ui_epoch']
        if not st.session_state['setup_complete']:
            st.caption('Already have a saved plan? Pick up where you left off.')
            draft = st.session_state.get(f'setup_draft_{epoch}', {})
            has_work = bool(workspace.documents or workspace.topics or draft.get('mode'))
            render_workspace_import(workspace, epoch, dirty=has_work)
            return
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
        st.caption('Save a workspace file before closing. Session memory is temporary.')
        render_workspace_import(workspace, epoch, dirty)
        with st.expander('Start another plan or workspace'):
            st.caption('A new plan keeps sources, topic records and exclusions. A new workspace clears them.')
            confirm = st.checkbox('I have saved anything I want to keep', key=f'reset_ok_{epoch}')
            if st.button('New plan — keep sources and topics', key='new_plan',
                         disabled=workspace.busy or not confirm):
                state.new_plan(workspace)
                st.session_state['ui_epoch'] += 1
                st.session_state['setup_complete'] = False
                st.session_state['setup_editing'] = False
                notify('New plan created. Your sources, topic library and exclusions remain available.')
                st.rerun()
            if st.button('New empty workspace', key='reset_workspace',
                         disabled=workspace.busy or not confirm):
                state.reset_workspace(workspace)
                st.session_state['ui_epoch'] += 1
                st.session_state['upload_epoch'] += 1
                st.session_state['last_saved_digest'] = None
                st.session_state['setup_complete'] = False
                st.session_state['setup_editing'] = False
                notify('Started a new empty workspace.')
                st.rerun()


def render_workspace_import(workspace: Workspace, epoch: int, dirty: bool) -> None:
    """Allow saved work to reopen from both the welcome and working screens."""
    from storage.workspace_store import load_workspace

    with st.expander('Reopen a saved workspace'):
        uploaded = st.file_uploader(
            'Workspace file', type=['json'], max_upload_size=20, key=f'workspace_load_{epoch}',
            disabled=workspace.busy,
        )
        replace_ok = not dirty
        if dirty:
            replace_ok = st.checkbox('Replace my current unsaved work', key=f'load_ok_{epoch}')
        if st.button('Validate and reopen', key='load_workspace',
                     disabled=workspace.busy or uploaded is None or not replace_ok):
            try:
                candidate = load_workspace(uploaded.getvalue())
            except ValueError as error:
                st.error(error_message(error))
            else:
                st.session_state['workspace'] = candidate
                st.session_state['ui_epoch'] += 1
                st.session_state['upload_epoch'] += 1
                st.session_state['last_saved_digest'] = workspace_digest(candidate)
                st.session_state['setup_complete'] = True
                st.session_state['setup_editing'] = False
                st.session_state['workspace_view'] = 'Finish' if candidate.plan.status == 'FINALIZED' else 'Sources'
                notify('Workspace reopened. Your saved sources and plan are ready.')
                st.rerun()


def render_plan_setup(workspace: Workspace) -> bool:
    """Guide setup in four steps, committing only the completed, validated draft."""
    if st.session_state['setup_complete'] and not st.session_state['setup_editing']:
        return True
    plan = workspace.plan
    epoch = st.session_state['ui_epoch']
    editing = st.session_state['setup_editing']
    draft = st.session_state.setdefault(f'setup_draft_{epoch}', {
        'step': 0, 'mode': plan.mode if editing else None,
        'weekly_days': plan.weekly_days if editing else None,
        'target': str(plan.target) if plan.target is not None else '',
        'start_date': plan.start_date,
        'extra': bool(plan.audience or plan.goal or plan.guidance),
        'name': plan.name if editing else '',
        'audience': plan.audience, 'goal': plan.goal, 'guidance': plan.guidance,
    })
    step = draft['step']
    locked = workspace.busy or plan.status == 'FINALIZED'
    st.caption(f'SET UP YOUR PLAN · STEP {step + 1} OF 4')
    st.progress((step + 1) / 4)
    with st.container(border=True):
        if step == 0:
            st.subheader('What would you like to create?')
            st.write('Choose the kind of plan that fits your work.')
            weekly, campaign = st.columns(2)
            with weekly:
                st.markdown('### :material/calendar_view_week: Weekly')
                st.caption('One topic a day, across 5 or 7 days.')
                if st.button('Weekly', key=f'choose_weekly_{epoch}', width='stretch', disabled=locked):
                    draft.update(mode='Week', step=1)
                    st.rerun()
            with campaign:
                st.markdown('### :material/campaign: Campaign')
                st.caption('Choose how many topics you want to extract.')
                if st.button('Campaign', key=f'choose_campaign_{epoch}', width='stretch', disabled=locked):
                    draft.update(mode='Campaign', step=1)
                    st.rerun()
        elif step == 1:
            if draft['mode'] == 'Week':
                st.subheader('How long is your weekly plan?')
                draft['weekly_days'] = st.segmented_control(
                    'Plan length', [5, 7], default=draft['weekly_days'],
                    format_func=lambda days: f'{days}-day plan',
                    key=f'weekly_days_{epoch}', required=True, width='stretch', disabled=locked,
                )
                st.caption('Each day has one topic. You can review and rearrange them later.')
            else:
                st.subheader('How many topics do you want to extract?')
                # Text preserves targets larger than JavaScript's exact integer range.
                draft['target'] = st.text_input(
                    'Number of campaign topics', value=draft['target'], placeholder='For example, 15',
                    key=f'campaign_target_{epoch}', max_chars=100, disabled=locked,
                )
                st.caption('We will use this as your target. The sources determine how many useful topics are available.')
        elif step == 2:
            st.subheader('When should your plan start?')
            draft['start_date'] = st.date_input(
                'Campaign start date' if draft['mode'] == 'Campaign' else 'Weekly plan start date',
                value=draft['start_date'], min_value=date.min, max_value=date.max,
                format='DD/MM/YYYY', key=f'setup_start_{epoch}', disabled=locked,
            )
            st.caption('Choose the first day of your plan.')
        else:
            st.subheader('Would you like to add more information?')
            st.write('You can tailor the topics to your audience and goals, or continue with your sources alone.')
            draft['extra'] = st.checkbox(
                'Yes, add additional information', value=draft['extra'],
                key=f'setup_extra_{epoch}', disabled=locked,
            )
            if draft['extra']:
                draft['name'] = st.text_input('Plan name (optional)', value=draft['name'],
                                              max_chars=200, key=f'setup_name_{epoch}', disabled=locked)
                draft['audience'] = st.text_input('Who is your target audience?', value=draft['audience'],
                                                  max_chars=500, key=f'setup_audience_{epoch}', disabled=locked)
                draft['goal'] = st.text_area('What do you want to achieve?', value=draft['goal'],
                                            max_chars=2000, key=f'setup_goal_{epoch}', disabled=locked)
                draft['guidance'] = st.text_area('Any other context or instructions?', value=draft['guidance'],
                                                max_chars=4000, key=f'setup_guidance_{epoch}', disabled=locked)
            size = f'{draft["weekly_days"]} days' if draft['mode'] == 'Week' else f'{draft["target"]} topics'
            st.divider()
            st.caption(f'{"Weekly" if draft["mode"] == "Week" else "Campaign"} · {size} · Starts {draft["start_date"]}')

        if step:
            with st.container(horizontal=True):
                if st.button('Back', key=f'setup_back_{epoch}', disabled=locked):
                    draft['step'] -= 1
                    st.rerun()
                if st.button('Continue to sources' if step == 3 else 'Continue',
                             key=f'setup_next_{epoch}', type='primary', disabled=locked):
                    target_text = draft['target'].strip()
                    if step == 1 and draft['mode'] == 'Campaign' and (
                        not target_text.isascii() or not target_text.isdigit() or int(target_text) < 1
                    ):
                        st.error('Enter a positive whole number of topics.')
                    elif step == 1 and draft['mode'] == 'Week' and draft['weekly_days'] not in (5, 7):
                        st.error('Choose a 5-day or 7-day plan.')
                    elif step == 2 and draft['start_date'] is None:
                        st.error('Choose a start date to continue.')
                    elif step == 2 and draft['mode'] == 'Week' and (
                        draft['start_date'] > date.max - timedelta(days=draft['weekly_days'] - 1)
                    ):
                        st.error('Choose an earlier start date so the entire plan fits within the calendar.')
                    elif step < 3:
                        draft['step'] += 1
                        st.rerun()
                    else:
                        extra = draft['extra']
                        default_name = f'{"Weekly plan" if draft["mode"] == "Week" else "Campaign"} · {draft["start_date"]}'
                        try:
                            plans.configure_plan(
                                workspace, name=(draft['name'].strip() if extra else '') or default_name,
                                mode=draft['mode'], weekly_days=draft['weekly_days'] or 5,
                                target=int(target_text) if draft['mode'] == 'Campaign' else None,
                                start_date=draft['start_date'],
                                audience=draft['audience'] if extra else '',
                                goal=draft['goal'] if extra else '', guidance=draft['guidance'] if extra else '',
                            )
                        except (ValueError, RuntimeError) as error:
                            st.error(error_message(error))
                        else:
                            st.session_state['setup_complete'] = True
                            st.session_state['setup_editing'] = False
                            st.session_state['workspace_view'] = 'Sources'
                            st.rerun()
        if editing and st.button('Cancel changes', key='cancel_setup', disabled=locked):
            st.session_state['setup_editing'] = False
            st.session_state.pop(f'setup_draft_{epoch}', None)
            st.rerun()
    return False


def show_workspace_view(view: str) -> None:
    """Switch stages from a button callback before the navigation widget renders."""
    st.session_state['workspace_view'] = view


def render_workbench(workspace: Workspace) -> None:
    """Keep sources, topic work, and final arrangement on separate screens."""
    plan = workspace.plan
    size = f'{plan.weekly_days}-day weekly plan' if plan.mode == 'Week' else f'Campaign · {plan.target or "Open-ended"} topics'
    with st.container(border=True):
        st.subheader(plan.name)
        st.caption(f'{size} · Starts {plan.start_date or "not set"}')
        if st.button('Edit plan settings', icon=':material/edit:',
                     disabled=workspace.busy or plan.status == 'FINALIZED'):
            st.session_state['setup_editing'] = True
            st.session_state.pop(f'setup_draft_{st.session_state["ui_epoch"]}', None)
            st.rerun()
    view = st.segmented_control(
        'Your workspace', ['Sources', 'Topics', 'Finish'], key='workspace_view',
        required=True, width='stretch', disabled=workspace.busy,
    )
    if view == 'Sources':
        render_sources(workspace)
        st.button('Continue to topics', type='primary', disabled=workspace.busy or not workspace.documents,
                  on_click=show_workspace_view, args=('Topics',))
    elif view == 'Topics':
        if plan.status != 'FINALIZED':
            render_generation(workspace)
        if workspace.topics:
            render_library(workspace)
        st.button('Review and finish', type='primary', disabled=workspace.busy or not plan.selected_topic_ids,
                  on_click=show_workspace_view, args=('Finish',))
    elif view == 'Finish':
        render_active_plan(workspace)


def render_sources(workspace: Workspace) -> None:
    """Read only intentional additions, then expose the exact eligible source context."""
    from documents.context_builder import build_context

    st.header('Add your source documents')
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
    st.header('Find topics in your sources')
    configured = bool(
        (settings.GEMINI_API_KEY and (settings.GEMINI_MODEL or settings.GEMINI_FALLBACK_MODEL))
        or (settings.GROQ_API_KEY and settings.GROQ_MODEL)
    )
    if not configured:
        st.info(
            'Add GEMINI_API_KEY and GROQ_API_KEY to your local .env to enable both providers. '
            'Generation can use either configured provider. Restart after configuration changes.'
        )
    selected = len(workspace.plan.selected_topic_ids)
    target = workspace.plan.effective_target
    st.write(f'{selected} of {target} topics selected' if target else f'{selected} topics selected')
    st.caption('Generation sends extracted text and your brief to Gemini, with Groq as a fallback. Review each topic against its evidence.')
    with st.expander('Generation options'):
        batch = st.number_input('Maximum candidates in this request', min_value=1, max_value=10,
                                value=10, step=1, key='batch_size')
        st.caption('Each request returns up to 10 candidates. Continue in batches for a larger campaign; the sources determine how many distinct topics are possible.')
        st.caption(
            f'Provider order: Gemini {settings.GEMINI_MODEL} → Groq {settings.GROQ_MODEL} → '
            f'Gemini {settings.GEMINI_FALLBACK_MODEL or "reserve disabled"}.'
        )
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
            st.session_state['topic_filter'] = 'Available'
            notify('\n\n'.join(messages))
            st.rerun()
    if st.session_state.get('generation_failed'):
        st.caption('Your workspace was retained. Correct the issue and use Generate/Find more to retry.')
    if workspace.sufficiency_note:
        st.write(workspace.sufficiency_note)
    with st.expander('Latest generation feedback'):
        for message in workspace.feedback:
            st.write(message)


def render_topic_details(topic: Any) -> None:
    """Show claims/context and explicit evidence without hiding limitations."""
    st.caption('Document finding')
    st.write(topic.core_insight)
    st.caption('Suggested angle and context')
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
    st.header('Review your topics')
    st.caption('Select includes a topic in this plan. Deselect keeps it available. Exclude avoids its angle in later generation.')
    st.caption('Green: source checks passed. Red: needs review; you can still select it. These checks do not guarantee accuracy.')
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
            if identity not in selected:
                issues = review_candidate(topic, workspace.documents, workspace.topics,
                                          workspace.excluded_topic_ids)
                if issues:
                    st.error('Needs review: ' + '; '.join(issues) + '.')
                else:
                    st.success('Source checks passed')
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

    st.header('Arrange and finish your plan')
    plan = workspace.plan
    st.write(f'Status: **{plan.status.replace("_", " ").title()}**')
    by_id = {topic.topic_id: topic for topic in workspace.topics}
    locked = workspace.busy or plan.status == 'FINALIZED'
    if plan.mode == 'Week':
        for day in range(plan.weekly_days):
            date_label = f' · {(plan.start_date + timedelta(days=day)).isoformat()}' if plan.start_date else ''
            topic = by_id.get(plan.day_assignments.get(day))
            weekday = DAYS[(plan.start_date.weekday() + day) % 7] if plan.start_date else DAYS[day]
            st.write(f'**{weekday}{date_label}:** {topic.title if topic else "Unfilled"}')
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
                                   index=current, format_func=lambda value: (
                                       DAYS[(plan.start_date.weekday() + value) % 7] if plan.start_date else DAYS[value]),
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
