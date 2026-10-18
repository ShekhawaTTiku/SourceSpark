"""Native Streamlit screens; all planning and processing rules live in their owners."""

from datetime import date, timedelta
import hashlib
from typing import Callable, Any

import streamlit as st
import streamlit_antd_components as sac
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
    st.session_state.setdefault('active_topic_id', None)
    st.session_state.setdefault('active_doc_id', None)
    st.session_state.setdefault('active_plan_topic_id', None)
    return st.session_state['workspace']


def workspace_digest(workspace: Workspace) -> str:
    """Compare meaningful working state with the latest explicit download/load action."""
    payload = workspace.model_dump_json(exclude={'busy'})
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()


def remember_snapshot(digest: str) -> None:
    """Mark the prepared snapshot without claiming its download was retained on disk."""
    st.session_state['last_saved_digest'] = digest


def render_header(workspace: Workspace) -> None:
    """Keep the entry screen focused on the next decision with a polished design system."""
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

/* Global Font & Canvas */
html, body, [class*="css"], .stApp {
  font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
  background-color: #F8FAFC !important;
  color: #0F172A !important;
}

/* Constrain content width comfortably */
.main .block-container {
  max-width: 1200px !important;
  padding-top: 1.25rem !important;
  padding-bottom: 3.5rem !important;
  padding-left: 2rem !important;
  padding-right: 2rem !important;
}

/* Headings */
h1, h2, h3, h4, [data-testid="stHeadingWithActionElements"] {
  font-family: 'Plus Jakarta Sans', sans-serif !important;
  letter-spacing: -0.025em !important;
  color: #0F172A !important;
}

h1 {
  font-size: 27px !important;
  font-weight: 800 !important;
  margin-top: 0px !important;
  margin-bottom: 4px !important;
}

/* Custom Eyebrow Badge */
.sp-eyebrow {
  display: inline-flex;
  align-items: center;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #166534;
  background: #DCFCE7;
  padding: 3px 10px;
  border-radius: 16px;
  margin-bottom: 6px;
  border: 1px solid #BBF7D0;
}

/* Modern Card Containers */
div[data-testid="stVerticalBlockBorderWrapper"] {
  border: 1px solid #E2E8F0 !important;
  border-radius: 12px !important;
  background-color: #FFFFFF !important;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.02) !important;
  padding: 1.15rem !important;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:hover {
  border-color: #CBD5E1 !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05) !important;
}

/* Complete Visual Overhaul for All Buttons */
button[data-testid*="Button"],
button[data-testid*="button"],
button[data-testid*="baseButton"],
div.stButton > button,
div[data-testid="stButton"] button,
.stButton button,
div[data-testid="stFormSubmitButton"] button,
div[data-testid="stDownloadButton"] button {
  font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
  font-size: 13.5px !important;
  font-weight: 600 !important;
  border-radius: 8px !important;
  padding: 0.45rem 1rem !important;
  min-height: 38px !important;
  transition: all 0.15s cubic-bezier(0.16, 1, 0.3, 1) !important;
  cursor: pointer !important;
  letter-spacing: -0.01em !important;
}

/* Primary Buttons */
button[data-testid*="primary"],
button[data-testid*="Primary"],
button[kind="primary"],
div.stButton > button[kind="primary"],
div[data-testid="stButton"] button[kind="primary"],
div[data-testid="stFormSubmitButton"] button {
  background: linear-gradient(180deg, #166534 0%, #14532D 100%) !important;
  border: 1px solid #14532D !important;
  color: #FFFFFF !important;
  box-shadow: 0 1px 3px rgba(20, 83, 45, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.15) !important;
}
button[data-testid*="primary"]:hover,
button[kind="primary"]:hover,
div.stButton > button[kind="primary"]:hover,
div[data-testid="stFormSubmitButton"] button:hover {
  background: linear-gradient(180deg, #15803D 0%, #166534 100%) !important;
  border-color: #166534 !important;
  color: #FFFFFF !important;
  box-shadow: 0 4px 12px rgba(20, 83, 45, 0.35) !important;
  transform: translateY(-1px) !important;
}
button[data-testid*="primary"]:active,
button[kind="primary"]:active {
  transform: translateY(0px) !important;
  box-shadow: 0 1px 2px rgba(20, 83, 45, 0.2) !important;
}

/* Secondary / Default Buttons */
button[data-testid*="secondary"],
button[data-testid*="Secondary"],
button[kind="secondary"],
div.stButton > button[kind="secondary"],
div.stButton > button:not([kind="primary"]):not([data-testid*="primary"]):not([data-testid*="Primary"]),
div[data-testid="stDownloadButton"] button {
  background: #FFFFFF !important;
  border: 1px solid #D1D5DB !important;
  color: #1F2937 !important;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05) !important;
}
button[data-testid*="secondary"]:hover,
button[kind="secondary"]:hover,
div.stButton > button:not([kind="primary"]):not([data-testid*="primary"]):not([data-testid*="Primary"]):hover,
div[data-testid="stDownloadButton"] button:hover {
  background: #F9FAFB !important;
  border-color: #9CA3AF !important;
  color: #0F172A !important;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08) !important;
  transform: translateY(-1px) !important;
}

/* Segmented Control / Navigation Pills */
div[data-testid="stSegmentedControl"] {
  background: #F1F5F9 !important;
  padding: 4px !important;
  border-radius: 10px !important;
  border: 1px solid #E2E8F0 !important;
}
div[data-testid="stSegmentedControl"] button {
  font-family: 'Plus Jakarta Sans', sans-serif !important;
  font-weight: 600 !important;
  border-radius: 7px !important;
  font-size: 13.5px !important;
}

/* Form inputs & selectboxes */
div[data-baseweb="select"] > div,
div[data-baseweb="input"] > div,
div[data-testid="stTextInput"] input,
div[data-testid="stTextArea"] textarea {
  border-radius: 8px !important;
  border: 1px solid #D1D5DB !important;
  font-family: 'Plus Jakarta Sans', sans-serif !important;
  font-size: 13.5px !important;
}
div[data-baseweb="select"] > div:focus-within,
div[data-testid="stTextInput"] input:focus,
div[data-testid="stTextArea"] textarea:focus {
  border-color: #166534 !important;
  box-shadow: 0 0 0 2px rgba(22, 101, 52, 0.15) !important;
}

/* Evidence quote boxes */
.sp-evidence-box {
  border-left: 3px solid #166534;
  background-color: #F8FAFC;
  padding: 10px 14px;
  border-radius: 0 8px 8px 0;
  margin: 6px 0 10px 0;
  font-size: 12.5px;
  line-height: 1.6;
  color: #1E293B;
  border-top: 1px solid #E2E8F0;
  border-right: 1px solid #E2E8F0;
  border-bottom: 1px solid #E2E8F0;
}

/* Scrollable Monospace Box */
.sp-scroll-text {
  max-height: 380px;
  overflow-y: auto;
  background: #F8FAFC;
  padding: 12px 14px;
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  line-height: 1.6;
  color: #0F172A;
  white-space: pre-wrap;
  word-break: break-word;
}

/* Tag / pill badges */
.sp-tag {
  display: inline-flex;
  align-items: center;
  font-size: 11px;
  font-weight: 600;
  padding: 3px 9px;
  border-radius: 6px;
  background-color: #F1F5F9;
  color: #475569;
  border: 1px solid #E2E8F0;
  margin-right: 6px;
  margin-bottom: 4px;
}
.sp-tag-accent {
  background-color: #DCFCE7;
  color: #166534;
  border-color: #BBF7D0;
}
.sp-tag-warning {
  background-color: #FEF3C7;
  color: #92400E;
  border-color: #FDE68A;
}
.sp-tag-danger {
  background-color: #FEE2E2;
  color: #991B1B;
  border-color: #FECACA;
}
</style>
""", unsafe_allow_html=True)
    st.markdown('<div class="sp-eyebrow">SOURCESPARK · EVIDENCE TO IDEAS</div>', unsafe_allow_html=True)
    st.title('Turn your sources into a plan')
    st.write('A few choices, your documents, and a clear plan to work from.')
    if st.session_state.get('notice'):
        sac.alert(
            label="Notice",
            description=st.session_state.pop('notice'),
            color="teal", variant="subtle", size="sm", closable=True,
        )


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
        if dirty:
            sac.alert(label="Unsaved Changes", description="Changes since last snapshot.", color="orange", variant="subtle", size="sm")
        else:
            sac.alert(label="Snapshot Up to Date", description="Workspace is saved.", color="green", variant="subtle", size="sm")
        st.caption(
            'Save includes extracted document text and metadata, not original files or API keys. '
            'The file is not encrypted. Keep the downloaded file somewhere suitable.'
        )
        try:
            snapshot = save_workspace(workspace)
            st.download_button(
                'Save workspace file', snapshot, file_name='waste-awareness.workspace.json',
                mime='application/json', key='save_workspace', on_click=remember_snapshot,
                args=(digest,), disabled=workspace.busy, width='stretch',
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
    sac.steps(
        items=[
            sac.StepsItem(title='Plan Type', description='Weekly or Campaign', icon='grid'),
            sac.StepsItem(title='Scope', description='Length or Target', icon='sliders'),
            sac.StepsItem(title='Schedule', description='Start Date', icon='calendar-date'),
            sac.StepsItem(title='Brief Details', description='Audience & Goal', icon='file-earmark-text'),
        ],
        index=step,
        size='sm',
        color='#166534',
        return_index=False,
    )
    with st.container(border=True):
        if step == 0:
            st.subheader('What would you like to create?')
            st.caption('Choose the kind of plan that fits your work.')
            weekly, campaign = st.columns(2, gap='large')
            with weekly:
                with st.container(border=True):
                    st.markdown('### :material/calendar_view_week: Weekly Curriculum')
                    st.caption('One focused topic per day, structured across a 5 or 7 day calendar sequence.')
                    st.markdown('<div style="margin: 8px 0 12px 0;"><span class="sp-tag sp-tag-accent">Calendar Scheduled</span><span class="sp-tag">Daily Sequence</span></div>', unsafe_allow_html=True)
                    st.divider()
                    if st.button('Weekly', key=f'choose_weekly_{epoch}', width='stretch', disabled=locked):
                        draft.update(mode='Week', step=1)
                        st.rerun()
            with campaign:
                with st.container(border=True):
                    st.markdown('### :material/campaign: Topic Campaign')
                    st.caption('Extract and assemble a target volume of topics from your documents.')
                    st.markdown('<div style="margin: 8px 0 12px 0;"><span class="sp-tag sp-tag-accent">Target Volume</span><span class="sp-tag">Flexible Order</span></div>', unsafe_allow_html=True)
                    st.divider()
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
            st.caption('You can tailor the topics to your audience and goals, or continue with your sources alone.')
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
        col_info, col_action = st.columns([3, 1], vertical_alignment='center')
        with col_info:
            st.subheader(plan.name)
            st.caption(f'{size} · Starts {plan.start_date or "not set"}')
            st.markdown(
                f'<div style="margin-top: 4px;"><span class="sp-tag sp-tag-accent">{plan.mode} Mode</span>'
                f'<span class="sp-tag">{plan.status.replace("_", " ").title()}</span>'
                f'<span class="sp-tag">{len(plan.selected_topic_ids)} Selected</span></div>',
                unsafe_allow_html=True,
            )
        with col_action:
            if st.button('Edit plan settings', icon=':material/edit:',
                         disabled=workspace.busy or plan.status == 'FINALIZED', width='stretch'):
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
    """Read only intentional additions, then expose the exact eligible source context in Master-Detail."""
    from documents.context_builder import build_context

    st.header('Add your source documents')
    st.caption('Upload reference materials. SourceSpark parses text locally to build evidence-grounded topics.')
    locked = workspace.busy or workspace.plan.status == 'FINALIZED'
    
    if not workspace.documents:
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
        sac.alert(
            label='No Source Documents Yet',
            description='Add reports, guidance documents, spreadsheets or CSV files to extract evidence for topics.',
            color='blue', variant='subtle', size='sm',
        )
        return

    # Master-Detail two-column layout
    col_docs, col_doc_preview = st.columns([1.05, 1.35], gap='large')
    
    with col_docs:
        with st.container(border=True):
            st.markdown(f"**Document Library** · {len(workspace.documents)} file(s) available")
            with st.expander('Upload additional documents'):
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

        doc_ids = [d.document_id for d in workspace.documents]
        if st.session_state.get('active_doc_id') not in doc_ids:
            st.session_state['active_doc_id'] = doc_ids[0]
        active_doc_id = st.session_state['active_doc_id']

        for document in workspace.documents:
            identity = document.document_id
            is_active = (identity == active_doc_id)
            with st.container(border=True):
                st.markdown(f"**{document.filename}**")
                st.markdown(
                    f'<div style="margin-bottom: 6px;"><span class="sp-tag sp-tag-accent">{document.file_type.upper()}</span>'
                    f'<span class="sp-tag">{document.size_bytes:,} bytes</span>'
                    f'<span class="sp-tag">{document.character_count:,} characters</span></div>',
                    unsafe_allow_html=True,
                )
                for warning in document.warnings:
                    st.warning(warning)
                
                cited = any(ref.document_id == document.document_id
                            for topic in workspace.topics for ref in topic.sources)
                if cited:
                    st.caption('Retained topics cite this source, so its evidence is protected.')
                
                c_act1, c_act2 = st.columns([1, 1])
                with c_act1:
                    if st.button('Inspect 👁️' if not is_active else 'Viewing 👁️',
                                 key=f'inspect_doc_{identity}',
                                 type='primary' if is_active else 'secondary', width='stretch'):
                        st.session_state['active_doc_id'] = identity
                        st.rerun()
                with c_act2:
                    if st.button('Remove source', key=f'remove_{identity}',
                                 disabled=locked or cited, width='stretch'):
                        act(state.remove_document, workspace, identity)

    with col_doc_preview:
        active_doc = next((d for d in workspace.documents if d.document_id == active_doc_id), workspace.documents[0])
        with st.container(border=True):
            st.markdown('<div class="sp-eyebrow">DOCUMENT INSPECTOR</div>', unsafe_allow_html=True)
            st.subheader(active_doc.filename)
            st.markdown(
                f'<div style="margin-bottom: 8px;"><span class="sp-tag sp-tag-accent">{active_doc.file_type.upper()}</span>'
                f'<span class="sp-tag">{active_doc.character_count:,} characters</span>'
                f'<span class="sp-tag">{active_doc.size_bytes:,} bytes</span></div>',
                unsafe_allow_html=True,
            )
            for warning in active_doc.warnings:
                st.warning(warning)
            st.markdown(f'<div class="sp-scroll-text">{active_doc.content}</div>', unsafe_allow_html=True)

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
    locked = workspace.busy or workspace.plan.status == 'FINALIZED'
    full = workspace.plan.remaining_slots == 0

    if not workspace.topics:
        # Full hero view when generating initial topics
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
        if full:
            st.info('The target is filled. Review the plan, or deselect topics/change its target before generating.')
        label = 'Generate topics'
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
    else:
        # Compact 1-line top action bar so topics remain immediately visible without scrolling!
        with st.container(border=True):
            col_stat, col_opts, col_btn = st.columns([2.4, 1.2, 1.2], vertical_alignment='center')
            with col_stat:
                st.markdown(f"**Topics in Workspace** · {selected} of {target or '∞'} selected for plan")
                st.caption(f"{len(workspace.topics)} candidates extracted · Review against citations below")
            with col_opts:
                with st.expander('⚙️ Batch options'):
                    batch = st.number_input('Batch size', min_value=1, max_value=10,
                                            value=10, step=1, key='batch_size')
            with col_btn:
                label = 'Find more topics'
                if st.button(label, key='generate_topics', type='primary',
                             disabled=locked or full or not configured or not workspace.documents, width='stretch'):
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


def render_library(workspace: Workspace) -> None:
    """Review topics in a zero-scroll Master-Detail layout."""
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
    
    # Active topic tracking for the inspector
    page_topics = topics[(page - 1) * 10:page * 10]
    page_ids = [t.topic_id for t in page_topics]
    if st.session_state.get('active_topic_id') not in page_ids:
        st.session_state['active_topic_id'] = page_ids[0]
    active_id = st.session_state['active_topic_id']
    active_topic = next((t for t in page_topics if t.topic_id == active_id), page_topics[0])

    col_list, col_inspector = st.columns([1.1, 1.4], gap='large')
    
    with col_list:
        st.caption('Green: source checks passed. Red: needs review; you can still select it.')
        for topic in page_topics:
            identity = topic.topic_id
            is_active = (identity == active_id)
            with st.container(border=True):
                st.subheader(topic.title)
                if identity not in selected:
                    issues = review_candidate(topic, workspace.documents, workspace.topics,
                                              workspace.excluded_topic_ids)
                    if issues:
                        st.error('Needs review: ' + '; '.join(issues) + '.')
                    else:
                        st.success('Source checks passed')
                
                # Snippet of finding
                snippet = topic.core_insight if len(topic.core_insight) <= 110 else f"{topic.core_insight[:110]}..."
                st.caption(f"Finding: {snippet}")
                
                # Buttons row: Inspect + Actions
                c_insp, c_sel, c_excl = st.columns([1, 1.25, 1.25])
                with c_insp:
                    if st.button('Inspect 👁️' if not is_active else 'Viewing 👁️',
                                 key=f'inspect_{identity}',
                                 type='primary' if is_active else 'secondary', width='stretch'):
                        st.session_state['active_topic_id'] = identity
                        st.rerun()
                with c_sel:
                    if identity in excluded:
                        if st.button('Restore', key=f'restore_{identity}', disabled=locked, width='stretch'):
                            act(plans.restore_topic, workspace, identity)
                    else:
                        if identity in selected:
                            if st.button('Deselect', key=f'deselect_{identity}', disabled=locked, width='stretch'):
                                act(plans.deselect_topic, workspace, identity)
                        elif st.button('Select for plan', key=f'select_{identity}',
                                       disabled=locked or workspace.plan.remaining_slots == 0, width='stretch'):
                            act(plans.select_topic, workspace, identity)
                with c_excl:
                    if identity not in excluded:
                        if st.button('Exclude angle', key=f'exclude_{identity}', disabled=locked, width='stretch'):
                            act(plans.exclude_topic, workspace, identity)

    with col_inspector:
        with st.container(border=True):
            st.markdown('<div class="sp-eyebrow">TOPIC EVIDENCE INSPECTOR</div>', unsafe_allow_html=True)
            st.subheader(active_topic.title)
            
            # Status badges
            if active_topic.topic_id in selected:
                badge_html = '<span class="sp-tag sp-tag-accent">Selected for Plan</span>'
            elif active_topic.topic_id in excluded:
                badge_html = '<span class="sp-tag sp-tag-danger">Excluded Angle</span>'
            else:
                badge_html = '<span class="sp-tag">Available Candidate</span>'
            
            st.markdown(
                f'<div style="margin-bottom: 12px;">{badge_html}'
                f'<span class="sp-tag">Audience: {active_topic.target_audience}</span>'
                f'<span class="sp-tag">Format: {active_topic.suggested_format}</span>'
                f'<span class="sp-tag">{len(active_topic.sources)} source citations</span></div>',
                unsafe_allow_html=True,
            )
            
            st.markdown("**Document Finding**")
            st.markdown(f'<div class="sp-evidence-box">{active_topic.core_insight}</div>', unsafe_allow_html=True)
            
            st.markdown("**Suggested Angle & Context**")
            st.write(active_topic.context)
            
            st.markdown("**Supporting Evidence Excerpts**")
            for source in active_topic.sources:
                st.caption(f"**{source.filename}** · {source.location}")
                st.markdown(f'<div class="sp-evidence-box">{source.excerpt}</div>', unsafe_allow_html=True)
                
            if active_topic.origin == 'sample':
                st.warning('This topic is based on fictional learning material.')


def render_active_plan(workspace: Workspace) -> None:
    """Organize selected topics in Master-Detail, finalize, and export authoritative plans."""
    from exports.csv_exporter import export_csv
    from exports.markdown_exporter import export_markdown

    st.header('Arrange and finish your plan')
    plan = workspace.plan
    selected = list(plan.selected_topic_ids)
    st.markdown(
        f'<div style="margin-bottom: 12px;"><span class="sp-tag sp-tag-accent">Status: {plan.status.replace("_", " ").title()}</span>'
        f'<span class="sp-tag">{len(selected)} Topics Selected</span></div>',
        unsafe_allow_html=True,
    )
    by_id = {topic.topic_id: topic for topic in workspace.topics}
    locked = workspace.busy or plan.status == 'FINALIZED'
    
    if plan.mode == 'Week':
        with st.container(border=True):
            st.markdown('**Weekly Calendar Schedule**')
            for day in range(plan.weekly_days):
                date_label = f' · {(plan.start_date + timedelta(days=day)).isoformat()}' if plan.start_date else ''
                topic = by_id.get(plan.day_assignments.get(day))
                weekday = DAYS[(plan.start_date.weekday() + day) % 7] if plan.start_date else DAYS[day]
                st.write(f'**{weekday}{date_label}:** {topic.title if topic else "Unfilled"}')
                
    selected = list(plan.selected_topic_ids)
    if selected:
        pages = max(1, (len(selected) + 9) // 10)
        page = st.selectbox('Plan page', range(1, pages + 1), key=f'plan_page_{plan.plan_id}_{pages}')
        page_selected = selected[(page - 1) * 10:page * 10]
        
        if st.session_state.get('active_plan_topic_id') not in page_selected:
            st.session_state['active_plan_topic_id'] = page_selected[0]
        active_plan_id = st.session_state['active_plan_topic_id']
        active_plan_topic = by_id.get(active_plan_id, by_id[page_selected[0]])

        col_plan_list, col_plan_inspector = st.columns([1.1, 1.4], gap='large')
        with col_plan_list:
            for identity in page_selected:
                topic = by_id[identity]
                index = selected.index(identity)
                is_active = (identity == active_plan_id)
                with st.container(border=True):
                    st.write(f'**{index + 1}. {topic.title}**')
                    with st.container(horizontal=True):
                        if st.button('Inspect 👁️' if not is_active else 'Viewing 👁️',
                                     key=f'inspect_plan_{identity}',
                                     type='primary' if is_active else 'secondary'):
                            st.session_state['active_plan_topic_id'] = identity
                            st.rerun()
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
        with col_plan_inspector:
            with st.container(border=True):
                st.markdown('<div class="sp-eyebrow">PLAN TOPIC INSPECTOR</div>', unsafe_allow_html=True)
                st.subheader(active_plan_topic.title)
                st.markdown(
                    f'<div style="margin-bottom: 12px;"><span class="sp-tag sp-tag-accent">Position: #{selected.index(active_plan_id) + 1}</span>'
                    f'<span class="sp-tag">Audience: {active_plan_topic.target_audience}</span>'
                    f'<span class="sp-tag">Format: {active_plan_topic.suggested_format}</span></div>',
                    unsafe_allow_html=True,
                )
                st.markdown("**Document Finding**")
                st.markdown(f'<div class="sp-evidence-box">{active_plan_topic.core_insight}</div>', unsafe_allow_html=True)
                st.markdown("**Suggested Angle & Strategy**")
                st.write(active_plan_topic.context)
                st.markdown("**Supporting Evidence Excerpts**")
                for source in active_plan_topic.sources:
                    st.caption(f"**{source.filename}** · {source.location}")
                    st.markdown(f'<div class="sp-evidence-box">{source.excerpt}</div>', unsafe_allow_html=True)

    if plan.status == 'FINALIZED':
        with st.container(border=True):
            st.markdown('**Authoritative Plan Exports**')
            st.caption('Verify factual reasoning before public use. Downloads include selected topics and evidence only.')
            try:
                markdown, csv_data = export_markdown(workspace), export_csv(workspace)
                c_dl1, c_dl2 = st.columns(2)
                with c_dl1:
                    st.download_button('Download Markdown report', markdown,
                                       file_name='waste-awareness-plan.md', mime='text/markdown',
                                       key='download_markdown', on_click='ignore', width='stretch')
                with c_dl2:
                    st.download_button('Download CSV plan', csv_data,
                                       file_name='waste-awareness-plan.csv', mime='text/csv',
                                       key='download_csv', on_click='ignore', width='stretch')
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
