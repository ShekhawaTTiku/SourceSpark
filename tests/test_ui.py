"""Streamlit regressions: local interactions never generate, authoritative exports stay current."""

from unittest.mock import Mock
from pathlib import Path
from datetime import date

from streamlit.testing.v1 import AppTest

from models.workspace import Workspace
from tests.conftest import seed_topics
from workflow.plan_manager import configure_plan, select_topic

APP_PATH = Path(__file__).resolve().parents[1] / 'web_app' / 'app.py'


def button(app: AppTest, label: str):
    """Locate a visible action without depending on Streamlit's internal form keys."""
    return next(item for item in app.button if item.label == label)


def checkbox(app: AppTest, label: str):
    """Locate a labelled control in the complete main/sidebar element tree."""
    return next(item for item in app.checkbox if item.label == label)


def make_app(workspace: Workspace) -> AppTest:
    """Start the actual nested entry point with isolated source-backed session data."""
    app = AppTest.from_file(APP_PATH, default_timeout=30)
    app.session_state['workspace'] = workspace
    app.run()
    assert not app.exception
    return app


def test_blank_entrypoint_no_simulation_buttons() -> None:
    """The final interface must not present fictional output as live results."""
    app = AppTest.from_file(APP_PATH, default_timeout=30).run()
    assert not app.exception
    assert [metric.value for metric in app.metric] == ['0', '0', '0', '0']
    assert not any('fictional' in item.label.lower() for item in app.button)
    assert app.button(key='generate_topics').disabled


def test_selection_rerun_exclude_restore_never_generate(workspace: Workspace, monkeypatch) -> None:
    """All review controls operate locally even when generation is configured."""
    import web_app.views as views

    call = Mock(side_effect=AssertionError('Unexpected generation request'))
    monkeypatch.setattr(views, 'generate_batch', call)
    monkeypatch.setattr(views.settings, 'GEMINI_API_KEY', 'test-only-not-a-real-key')
    monkeypatch.setattr(views.settings, 'GEMINI_MODEL', 'test-only-model')
    seed_topics(workspace, 2)
    app = make_app(workspace)
    identity = workspace.topics[0].topic_id
    app.button(key=f'select_{identity}').click().run()
    app.run()
    assert app.session_state['workspace'].plan.selected_topic_ids == [identity]
    app.selectbox(key='topic_filter').select('Selected').run()
    app.button(key=f'exclude_{identity}').click().run()
    app.selectbox(key='topic_filter').select('Excluded').run()
    app.button(key=f'restore_{identity}').click().run()
    assert not app.exception
    assert not app.session_state['workspace'].excluded_topic_ids
    assert not app.session_state['workspace'].plan.selected_topic_ids
    call.assert_not_called()


def test_finalization_exports_and_reopen_invalidate_downloads(workspace: Workspace) -> None:
    """Only explicit approval produces exports; editing removes them immediately."""
    seed_topics(workspace, 1)
    select_topic(workspace, workspace.topics[0].topic_id)
    app = make_app(workspace)
    assert not any(item.label == 'Download CSV plan' for item in app.get('download_button'))
    checkbox(app, 'I want to finalize this shorter plan').check().run()
    app.button(key='finalize_plan').click().run()
    assert not app.exception
    assert app.session_state['workspace'].plan.status == 'FINALIZED'
    downloads = [item.label for item in app.get('download_button')]
    assert 'Download CSV plan' in downloads and 'Download Markdown report' in downloads
    app.button(key='reopen_plan').click().run()
    assert not app.exception
    assert app.session_state['workspace'].plan.status == 'DRAFT'
    assert 'Download CSV plan' not in [item.label for item in app.get('download_button')]


def test_reset_refreshes_mode_widgets_and_clears_upload_epoch(workspace: Workspace) -> None:
    """A stale Campaign widget cannot overwrite a newly reset Week plan."""
    configure_plan(workspace, name='Campaign', mode='Campaign')
    app = make_app(workspace)
    assert app.selectbox(key='planning_mode_0').value == 'Campaign'
    checkbox(app, 'I have saved anything I want to keep').check().run()
    app.button(key='reset_workspace').click().run()
    assert not app.exception
    assert app.session_state['workspace'].plan.mode == 'Week'
    assert app.selectbox(key='planning_mode_1').value == 'Week'
    assert app.session_state['upload_epoch'] == 1


def test_new_plan_retains_sources_library_and_exclusions(workspace: Workspace) -> None:
    """Starting another plan is visibly different from clearing the workspace."""
    seed_topics(workspace, 2)
    app = make_app(workspace)
    checkbox(app, 'I have saved anything I want to keep').check().run()
    app.button(key='new_plan').click().run()
    assert not app.exception
    current = app.session_state['workspace']
    assert len(current.documents) == 1 and len(current.topics) == 2
    assert current.plan.selected_topic_ids == []


def test_explicit_generation_action_and_ordinary_rerun(workspace: Workspace, monkeypatch) -> None:
    """The single generation button is the only UI entry to provider work."""
    import web_app.views as views

    call = Mock(return_value=['Controlled test response; no provider invoked.'])
    monkeypatch.setattr(views, 'generate_batch', call)
    monkeypatch.setattr(views.settings, 'GEMINI_API_KEY', 'test-only-not-a-real-key')
    monkeypatch.setattr(views.settings, 'GEMINI_MODEL', 'test-only-model')
    app = make_app(workspace)
    app.run()
    call.assert_not_called()
    app.button(key='generate_topics').click().run()
    assert not app.exception
    assert call.call_count == 1
    app.run()
    assert call.call_count == 1


def test_large_saved_target_renders_without_javascript_integer_overflow(workspace: Workspace) -> None:
    """No JavaScript number widget should impose a hidden campaign target ceiling."""
    from storage.workspace_store import load_workspace, save_workspace

    configure_plan(workspace, name='Large target', mode='Campaign', target=9007199254740993)
    app = make_app(load_workspace(save_workspace(workspace)))
    assert not app.exception
    target = next(item for item in app.text_input if item.label.startswith('Campaign target'))
    assert target.value == '9007199254740993'


def test_valid_calendar_boundary_week_renders(workspace: Workspace) -> None:
    """Explicit date-input bounds support a valid five-day final calendar week."""
    configure_plan(workspace, name='Last representable week', mode='Week',
                   weekly_days=5, start_date=date(9999, 12, 27))
    app = make_app(workspace)
    assert not app.exception
