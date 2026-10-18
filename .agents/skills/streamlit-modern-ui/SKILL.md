---
name: streamlit-modern-ui
description: Best practices, component reference, and integration patterns for building non-AI, production-grade Streamlit UIs using streamlit-shadcn-ui and streamlit-antd-components (sac).
---

# Modern Streamlit UI Design Skill

This skill guides the design and development of polished, human-crafted, enterprise-grade Streamlit applications by combining **`streamlit-shadcn-ui`** and **`streamlit-antd-components` (sac)** to replace generic "AI-generated" defaults.

---

## 1. Coexistence: Using Both Together

**Yes, both packages can and should be used simultaneously.** They complement each other with zero conflict:

| Feature / Role | Recommended Package | Component Example |
| :--- | :--- | :--- |
| **Top-Level Navigation & Tabs** | `streamlit-antd-components` (`sac`) | `sac.tabs()`, `sac.segmented()` |
| **Workflow / Progress Steppers** | `streamlit-antd-components` (`sac`) | `sac.steps()` |
| **Hierarchical Trees / Filters** | `streamlit-antd-components` (`sac`) | `sac.tree()`, `sac.cascader()` |
| **Alerts & Status Ribbons** | `streamlit-antd-components` (`sac`) | `sac.alert()` |
| **KPI & Metric Cards** | `streamlit-shadcn-ui` (`ui`) | `ui.metric_card()` |
| **Cards & Content Grouping** | `streamlit-shadcn-ui` (`ui`) | `ui.card()` |
| **Status Badges & Chips** | `streamlit-shadcn-ui` (`ui`) | `ui.badges()` |
| **Action & Variant Buttons** | `streamlit-shadcn-ui` (`ui`) | `ui.button(variant="outline"\|"destructive")` |
| **Modal Dialogs & Confirmation** | `streamlit-shadcn-ui` (`ui`) | `ui.element("dialog")` |

---

## 2. Core Import Standards

```python
import streamlit as st
import streamlit_antd_components as sac
import streamlit_shadcn_ui as ui
```

---

## 3. High-Impact Patterns & Examples

### A. App Navigation with `sac.segmented` or `sac.tabs`
Replace raw `st.sidebar.radio` with modern segmented pills:
```python
selected_tab = sac.segmented(
    items=[
        sac.SegmentedItem(label="Overview", icon="grid"),
        sac.SegmentedItem(label="Documents", icon="file-text"),
        sac.SegmentedItem(label="Planning", icon="diagram-3"),
        sac.SegmentedItem(label="Exports", icon="download"),
    ],
    align="center",
    size="sm",
    use_container_width=True,
)
```

### B. Multi-Step Workflows with `sac.steps`
Instead of plain markdown headers, show real multi-step execution:
```python
current_step = sac.steps(
    items=[
        sac.StepsItem(title="Upload", description="Add raw source docs"),
        sac.StepsItem(title="Extraction", description="Parse evidence & concepts"),
        sac.StepsItem(title="Plan Generation", description="Generate curriculum"),
        sac.StepsItem(title="Export", description="Markdown & CSV"),
    ],
    index=1,
    direction="horizontal",
    format_func=None,
)
```

### C. Polished KPI Cards with `ui.metric_card`
Replace default `st.metric` with clean shadcn card metrics:
```python
c1, c2, c3 = st.columns(3)
with c1:
    ui.metric_card(title="Active Topics", content="24", description="+3 from review", key="card_topics")
with c2:
    ui.metric_card(title="Evidence Chunks", content="142", description="8 verified sources", key="card_evidence")
with c3:
    ui.metric_card(title="Coverage Score", content="96%", description="All criteria met", key="card_score")
```

### D. Clean Status Badges with `ui.badges`
Instead of messy emoji prefixes (`✅ Approved`, `❌ Rejected`), use subtle pill badges:
```python
ui.badges(
    badge_list=[
        ("Validated", "default"),
        ("Source Linked", "secondary"),
        ("Draft", "outline"),
    ],
    key="status_badges",
)
```

### E. Professional Alert Notice with `sac.alert`
```python
sac.alert(
    label="Workspace Synchronized",
    description="All 14 evidence chunks have been mapped to their respective topics.",
    size="sm",
    radius="md",
    variant="subtle",
    color="teal",
    icon=True,
    closable=True,
)
```

---

## 4. Strict Non-AI Design Guardrails

1. **No Emoji Overload**: Never prepend decorative emojis (`✨`, `🚀`, `🤖`, `💡`) to page titles, buttons, or navigation tabs.
2. **Never Dump Raw State**: Avoid raw `st.write(dict)`. Wrap structured data in clean cards or configured tables (`st.dataframe` with `column_config`).
3. **Consistent Spacing**: Use `st.container()` with border containers or `ui.card()` for clear grouped visual hierarchy.
4. **Subtle Feedback**: Use toasts (`st.toast`) and `sac.alert` rather than jarring full-width alerts.
