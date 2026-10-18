---
name: streamlit-design-system
description: Comprehensive UI/UX design system and craft standards for building non-AI, production-grade Streamlit SaaS interfaces using streamlit-antd-components (sac), streamlit-shadcn-ui (ui), and clean CSS tokens.
---

# Streamlit Design System & UX Standards

This skill provides the architectural rules, styling tokens, and component recipes needed to build Streamlit applications that look like **bespoke, modern SaaS products** (Linear, Raycast, Vercel, Stripe) rather than generic, prompt-generated AI prototypes.

---

## 1. The Anti-AI UI Manifesto

To eliminate the stereotypical "AI-generated" aesthetic, strictly enforce these negative constraints:

| AI Prototype Trope (Banned) | Production SaaS Standard (Required) |
| :--- | :--- |
| **Emoji Prepending** (`🚀 Launch`, `✨ Generator`, `💡 Insights`) | Clean typography with standard Lucide/Ant icons via `sac` (`icon="file-text"`, `icon="gear"`). |
| **Centered Rainbow Gradients** & glowing banners | Refined neutral surfaces, subtle 1px border lines, and single accent colors. |
| **Raw Dictionary/JSON dumps** (`st.write(data)`) | Structured readouts using `ui.card`, key-value definition lists, or configured dataframes. |
| **Monotonous Vertical Stacks** of default widgets | Balanced multi-column grids, master-detail side-by-side panes, and contextual toolbars. |
| **Generic Alerts** (`st.info("No items")`, `st.warning("Please wait")`) | Custom empty states with actionable buttons and subtle dismissible toasts (`st.toast`). |
| **Unstyled Full-Width Metrics** (`st.metric`) | Cohesive metric cards (`ui.metric_card`) grouped inside structured card grids. |

---

## 2. Design Tokens & Visual Hierarchy

### Color Palette (Modern Dark / Slate)
* **Canvas Background**: `#090D16` (Deep Slate)
* **Surface / Container**: `#111827` (Card Surface)
* **Elevated Surface**: `#1E293B` (Dropdown / Dialog)
* **Borders / Separators**: `rgba(255, 255, 255, 0.08)` or `#334155`
* **Text Primary**: `#F8FAFC`
* **Text Secondary / Muted**: `#94A3B8`
* **Brand Accent**: `#4F46E5` (Indigo) or `#059669` (Emerald)
* **Destructive**: `#EF4444`

### Typography Scale
* **Page Header**: 24px - 28px (`font-weight: 600`, tracking tight, no emojis).
* **Section Header**: 16px - 18px (`font-weight: 500`, uppercase tracking for section labels).
* **Body / Content**: 14px (`line-height: 1.5`, `#E2E8F0`).
* **Captions / Meta**: 12px (`#94A3B8`).

---

## 3. Core Layout Architectures

### A. The Master-Detail Split (For Document / Record Inspection)
Never force the user to scroll through dozens of records. Use a 60/40 or 65/35 split:
```python
col_master, col_detail = st.columns([1.6, 1.0], gap="medium")

with col_master:
    # Table, list, or grid of records
    selected_record = render_record_list(records)

with col_detail:
    # Sticky or contextual inspector for the selected item
    render_inspector_card(selected_record)
```

### B. Action Toolbar Pattern
Place filters, search, and action triggers on a single compact horizontal strip:
```python
c_search, c_filter, c_action = st.columns([2.5, 2.0, 1.0], vertical_alignment="center")

with c_search:
    search_query = st.text_input("Search", placeholder="Filter by title or tag...", label_visibility="collapsed")
with c_filter:
    filter_status = sac.segmented(
        items=[sac.SegmentedItem(label="All"), sac.SegmentedItem(label="Active"), sac.SegmentedItem(label="Archived")],
        size="sm",
        align="center",
        use_container_width=True,
    )
with c_action:
    if ui.button(text="New Record", variant="default", key="btn_new"):
        st.session_state.open_new_modal = True
```

### C. Phased Execution Stepper
Use `sac.steps` at the top of multi-phase workflows to make progress crystal clear:
```python
current_step = sac.steps(
    items=[
        sac.StepsItem(title="Upload Documents", description="PDF, DOCX, TXT"),
        sac.StepsItem(title="Evidence Review", description="Extract & verify claims"),
        sac.StepsItem(title="Curriculum Planning", description="Generate units & topics"),
        sac.StepsItem(title="Export", description="Markdown & CSV reports"),
    ],
    index=st.session_state.get("workflow_step", 0),
    direction="horizontal",
    size="sm",
)
```

---

## 4. Component Pairing Standards (`sac` + `ui`)

| UI Requirement | Best Choice | Code Pattern |
| :--- | :--- | :--- |
| **Top Navigation** | `sac.tabs` or `sac.segmented` | `sac.tabs([sac.TabsItem(label="Overview", icon="house")], variant="line")` |
| **Tree Views / Nested Taxonomies** | `sac.tree` | `sac.tree(items=[sac.TreeItem(label="Unit 1", children=[...])])` |
| **Status Badges** | `ui.badges` | `ui.badges([("Verified", "default"), ("Draft", "outline")])` |
| **Metric Summary** | `ui.metric_card` | `ui.metric_card(title="Coverage", content="94%", description="+5% vs last run")` |
| **Secondary / Ghost Buttons** | `ui.button` | `ui.button(text="Discard", variant="outline")` |
| **Destructive Actions** | `ui.button` | `ui.button(text="Delete", variant="destructive")` |
| **Inline Notice Ribbons** | `sac.alert` | `sac.alert(label="Ready to Export", variant="subtle", color="teal")` |

---

## 5. Performance & State Guardrails

1. **Unique & Deterministic Keys**: Always pass explicit `key` parameters to all `ui.*` and `sac.*` widgets (e.g. `key=f"topic_badge_{topic.id}"`). This avoids duplicate ID warnings and keeps state intact across reruns.
2. **Partial Updates with `@st.fragment`**: When creating interactive widgets like item selection, review checkboxes, or inline edits, wrap the view in `@st.fragment` so only the specific component reruns, avoiding jarring full-page flashes.
3. **Empty States**: If a dataset or plan is empty, always render a clean empty card with a prompt action button rather than leaving blank space.
