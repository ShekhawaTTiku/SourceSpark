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


def make_app(workspace: Workspace, view: str = 'Sources') -> AppTest:
    """Start the actual nested entry point with isolated source-backed session data."""
    app = AppTest.from_file(APP_PATH, default_timeout=30)
    app.session_state['workspace'] = workspace
    app.session_state['workspace_view'] = view
    app.run()
    assert not app.exception
    return app


def test_blank_entrypoint_no_simulation_buttons() -> None:
    """The final interface must not present fictional output as live results."""
    app = AppTest.from_file(APP_PATH, default_timeout=30).run()
    assert not app.exception
    assert not app.metric
    assert not any('fictional' in item.label.lower() for item in app.button)
    assert [item.label for item in app.main.button] == ['Weekly', 'Campaign']
    assert not app.main.get('file_uploader')
    assert not app.main.text_input and not app.main.date_input


def test_selection_rerun_exclude_restore_never_generate(workspace: Workspace, monkeypatch) -> None:
    """All review controls operate locally even when generation is configured."""
    import web_app.views as views

    call = Mock(side_effect=AssertionError('Unexpected generation request'))
    monkeypatch.setattr(views, 'generate_batch', call)
    monkeypatch.setattr(views.settings, 'GEMINI_API_KEY', 'test-only-not-a-real-key')
    monkeypatch.setattr(views.settings, 'GEMINI_MODEL', 'test-only-model')
    seed_topics(workspace, 2)
    app = make_app(workspace, 'Topics')
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
    app = make_app(workspace, 'Finish')
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
    assert app.session_state['workspace'].plan.mode == 'Campaign'
    checkbox(app, 'I have saved anything I want to keep').check().run()
    app.button(key='reset_workspace').click().run()
    assert not app.exception
    assert app.session_state['workspace'].plan.mode == 'Week'
    assert not app.session_state['setup_complete']
    assert [item.label for item in app.main.button] == ['Weekly', 'Campaign']
    assert app.session_state['upload_epoch'] == 1


def test_new_plan_retains_sources_library_and_exclusions(workspace: Workspace) -> None:
    """Starting another plan is visibly different from clearing the workspace."""
    seed_topics(workspace, 2)
    app = make_app(workspace, 'Topics')
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
    app = make_app(workspace, 'Topics')
    app.run()
    call.assert_not_called()
    app.button(key='generate_topics').click().run()
    assert not app.exception
    assert call.call_count == 1
    app.run()
    assert call.call_count == 1


def test_generated_topics_are_colored_for_review_until_manually_selected(workspace, monkeypatch):
    from ai.response_validator import review_candidate
    from models.generation_result import GenerationResult
    from storage.workspace_store import load_workspace, save_workspace
    from tests.conftest import make_candidate
    import web_app.views as views

    good = make_candidate(workspace, 1)
    flagged = make_candidate(workspace, 2)
    flagged.sources[0].excerpt = 'An unlocated quotation about waste collection.'
    provider = Mock()
    provider.feedback = []
    provider.generate.return_value = GenerationResult(
        candidates=[good, flagged], sufficiency_note='Two topics for manual review.',
    )
    monkeypatch.setattr('ai.topic_generator.configured_chain', lambda: provider)
    monkeypatch.setattr(views.settings, 'GEMINI_API_KEY', 'test-only-not-a-real-key')
    app = make_app(workspace, 'Topics')
    app.button(key='generate_topics').click().run()
    assert not app.exception
    current = app.session_state['workspace']
    assert len(current.topics) == 2 and not current.plan.selected_topic_ids
    assert any('Source checks passed' in item.value for item in app.success)
    assert any('Needs review' in item.value for item in app.error)
    identity = current.topics[-1].topic_id
    assert not app.button(key=f'select_{identity}').disabled
    app.button(key=f'select_{identity}').click().run()
    app.selectbox(key='topic_filter').select('Selected').run()
    assert not app.exception
    assert not app.error
    assert not any('Source checks passed' in item.value for item in app.success)
    reopened = load_workspace(save_workspace(app.session_state['workspace']))
    assert review_candidate(reopened.topics[-1], reopened.documents)
    selected_app = make_app(reopened, 'Topics')
    selected_app.selectbox(key='topic_filter').select('Selected').run()
    assert not selected_app.error
    selected_app.button(key=f'deselect_{identity}').click().run()
    selected_app.selectbox(key='topic_filter').select('Available').run()
    assert any('Needs review' in item.value for item in selected_app.error)
    assert not selected_app.exception
    provider.generate.assert_called_once()


def test_large_saved_target_renders_without_javascript_integer_overflow(workspace: Workspace) -> None:
    """No JavaScript number widget should impose a hidden campaign target ceiling."""
    from storage.workspace_store import load_workspace, save_workspace

    configure_plan(workspace, name='Large target', mode='Campaign', target=9007199254740993)
    app = make_app(load_workspace(save_workspace(workspace)))
    assert not app.exception
    button(app, 'Edit plan settings').click().run()
    button(app, 'Campaign').click().run()
    target = app.text_input(key='campaign_target_0')
    assert target.value == '9007199254740993'


def test_valid_calendar_boundary_week_renders(workspace: Workspace) -> None:
    """Explicit date-input bounds support a valid five-day final calendar week."""
    configure_plan(workspace, name='Last representable week', mode='Week',
                   weekly_days=5, start_date=date(9999, 12, 27))
    app = make_app(workspace)
    assert not app.exception


def test_weekly_wizard_hides_later_controls_and_saves_without_extras() -> None:
    app = AppTest.from_file(APP_PATH).run()
    button(app, 'Weekly').click().run()
    assert not app.text_input and not app.date_input
    button(app, 'Continue').click().run()
    assert app.error  # A length must be chosen deliberately.
    app.button_group(key='weekly_days_0').set_value(7).run()
    button(app, 'Continue').click().run()
    assert len(app.date_input) == 1
    button(app, 'Continue').click().run()
    assert app.error  # An empty date cannot advance.
    app.date_input(key='setup_start_0').set_value(date(2026, 10, 17)).run()
    button(app, 'Continue').click().run()
    assert not app.main.text_input and not app.main.text_area
    button(app, 'Continue to sources').click().run()
    assert not app.exception
    plan = app.session_state['workspace'].plan
    assert plan.mode == 'Week' and plan.weekly_days == 7
    assert plan.start_date == date(2026, 10, 17)
    assert plan.audience == plan.goal == plan.guidance == ''
    assert not any(item.key == 'generate_topics' for item in app.button)
    assert app.button_group(key='workspace_view').value == 'Sources'


def test_campaign_wizard_validates_count_reveals_optional_brief_and_keeps_back_values() -> None:
    app = AppTest.from_file(APP_PATH).run()
    button(app, 'Campaign').click().run()
    for invalid in ('0', '-2', '1.5', 'abc'):
        app.text_input(key='campaign_target_0').set_value(invalid).run()
        button(app, 'Continue').click().run()
        assert app.error and not app.date_input
    app.text_input(key='campaign_target_0').set_value('12').run()
    button(app, 'Continue').click().run()
    app.date_input(key='setup_start_0').set_value(date(2026, 10, 20)).run()
    button(app, 'Back').click().run()
    assert app.text_input(key='campaign_target_0').value == '12'
    button(app, 'Continue').click().run()
    assert app.date_input(key='setup_start_0').value == date(2026, 10, 20)
    button(app, 'Continue').click().run()
    assert not app.main.text_area
    checkbox(app, 'Yes, add additional information').check().run()
    app.text_input(key='setup_audience_0').set_value('Residents').run()
    app.text_area(key='setup_goal_0').set_value('Improve sorting').run()
    app.text_area(key='setup_guidance_0').set_value('Keep it practical').run()
    button(app, 'Continue to sources').click().run()
    assert not app.exception
    plan = app.session_state['workspace'].plan
    assert plan.mode == 'Campaign' and plan.target == 12
    assert plan.start_date == date(2026, 10, 20)
    assert (plan.audience, plan.goal, plan.guidance) == ('Residents', 'Improve sorting', 'Keep it practical')


def test_unchecked_extras_are_not_applied_and_cancel_does_not_change_plan(workspace: Workspace) -> None:
    configure_plan(workspace, name='Existing', mode='Campaign', target=12,
                   start_date=date(2026, 10, 20), audience='Residents')
    before = workspace.plan.model_dump()
    app = make_app(workspace)
    button(app, 'Edit plan settings').click().run()
    button(app, 'Campaign').click().run()
    app.text_input(key='campaign_target_0').set_value('20').run()
    button(app, 'Cancel changes').click().run()
    assert app.session_state['workspace'].plan.model_dump() == before
    button(app, 'Edit plan settings').click().run()
    button(app, 'Campaign').click().run()
    button(app, 'Continue').click().run()
    button(app, 'Continue').click().run()
    checkbox(app, 'Yes, add additional information').uncheck().run()
    assert not app.main.text_area
    button(app, 'Continue to sources').click().run()
    assert not app.exception
    assert app.session_state['workspace'].plan.audience == ''


def test_workspace_stages_show_only_the_current_work(workspace: Workspace) -> None:
    seed_topics(workspace, 1)
    select_topic(workspace, workspace.topics[0].topic_id)
    app = make_app(workspace)
    assert not any(item.key == 'generate_topics' for item in app.button)
    button(app, 'Continue to topics').click().run()
    assert app.button(key='generate_topics')
    assert not any(item.key == 'finalize_plan' for item in app.button)
    button(app, 'Review and finish').click().run()
    assert app.button(key='finalize_plan')
    assert not any(item.key == 'generate_topics' for item in app.button)
    assert not app.exception
