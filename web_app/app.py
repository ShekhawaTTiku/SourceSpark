"""Streamlit V1 entry point. A future V2 frontend is not implemented here."""

import logging
from pathlib import Path
import sys

import streamlit as st

# The agreed nested entry point needs root-owned packages on its import path.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import APP_TITLE
from web_app.views import (
    initialize, render_active_plan, render_generation, render_header,
    render_library, render_plan_setup, render_sources, render_workspace,
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
st.set_page_config(page_title=APP_TITLE, page_icon=':material/recycling:', layout='wide')
workspace = initialize()
render_header(workspace)
render_workspace(workspace)
render_plan_setup(workspace)
render_sources(workspace)
render_generation(workspace)
render_library(workspace)
render_active_plan(workspace)
