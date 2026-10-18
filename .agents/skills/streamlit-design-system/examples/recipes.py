"""Production-grade UI recipes combining streamlit-antd-components and streamlit-shadcn-ui.

These patterns replace generic AI Streamlit elements with polished SaaS designs.
"""

from typing import Any, Dict, List, Optional
import streamlit as st
import streamlit_antd_components as sac
import streamlit_shadcn_ui as ui


def render_metric_ribbon(metrics: List[Dict[str, Any]]) -> None:
    """Render a clean grid of metric cards using shadcn UI."""
    cols = st.columns(len(metrics), gap="small")
    for idx, (col, m) in enumerate(zip(cols, metrics)):
        with col:
            ui.metric_card(
                title=m.get("title", ""),
                content=str(m.get("content", "")),
                description=m.get("description", ""),
                key=f"metric_card_{idx}_{m.get('title', '')}",
            )


def render_action_bar(
    search_placeholder: str = "Search items...",
    status_options: Optional[List[str]] = None,
    action_label: str = "Add New",
) -> Dict[str, Any]:
    """Render a compact search, filter, and action toolbar."""
    status_options = status_options or ["All", "Active", "Pending"]
    col_search, col_filter, col_action = st.columns([2.5, 2.0, 1.2], vertical_alignment="center")

    with col_search:
        search_term = st.text_input(
            "Search",
            placeholder=search_placeholder,
            label_visibility="collapsed",
            key="action_bar_search",
        )

    with col_filter:
        selected_status = sac.segmented(
            items=[sac.SegmentedItem(label=opt) for opt in status_options],
            size="sm",
            align="center",
            use_container_width=True,
            key="action_bar_status",
        )

    with col_action:
        action_clicked = ui.button(
            text=action_label,
            variant="default",
            key="action_bar_primary_btn",
        )

    return {
        "search": search_term,
        "status": selected_status,
        "action_clicked": action_clicked,
    }


def render_master_detail_layout(
    items: List[Dict[str, Any]],
    selected_id_key: str = "selected_item_id",
) -> None:
    """Render a master-detail split layout for reviewing entities without page reloads."""
    col_master, col_detail = st.columns([1.5, 1.0], gap="medium")

    with col_master:
        st.subheader("Items List")
        for item in items:
            with st.container(border=True):
                c1, c2 = st.columns([3, 1], vertical_alignment="center")
                with c1:
                    st.markdown(f"**{item['title']}**")
                    st.caption(item.get("summary", ""))
                with c2:
                    if st.button("Inspect", key=f"inspect_{item['id']}"):
                        st.session_state[selected_id_key] = item["id"]

    with col_detail:
        current_id = st.session_state.get(selected_id_key)
        selected_item = next((i for i in items if i["id"] == current_id), None)
        if selected_item:
            with st.container(border=True):
                st.subheader(selected_item["title"])
                ui.badges(
                    badge_list=[
                        (selected_item.get("status", "Active"), "default"),
                        (selected_item.get("category", "General"), "secondary"),
                    ],
                    key=f"detail_badges_{current_id}",
                )
                st.write(selected_item.get("details", "No extra details."))
        else:
            with st.container(border=True):
                st.info("Select an item on the left to inspect details.")
