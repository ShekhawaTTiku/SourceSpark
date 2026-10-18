# Streamlit UI Standards & Anti-AI Guidelines

When creating or modifying Streamlit applications in this repository:

1. **Aesthetic Standards (No "AI-Generated" Tropes)**:
   - Do NOT prefix page headers, tab names, or button text with decorative emojis (`🚀`, `✨`, `🤖`, `💡`).
   - Do NOT dump raw dictionaries, tracebacks, or raw JSON onto the screen with `st.write(data)`. Wrap structured data into clean cards or tables with `st.column_config`.
   - Prefer subtle dark slate surfaces with 1px borders (`rgba(255, 255, 255, 0.08)`) and controlled typography.

2. **Component Library Standards**:
   - Use `streamlit-antd-components` (`sac`) for:
     - Navigation bars and segmented tabs (`sac.tabs`, `sac.segmented`).
     - Multi-step workflow steppers (`sac.steps`).
     - Hierarchical trees and filters (`sac.tree`).
     - Subtle inline notices (`sac.alert`).
   - Use `streamlit-shadcn-ui` (`ui`) for:
     - KPI metric cards (`ui.metric_card`).
     - Entity status badges and tags (`ui.badges`).
     - Styled action buttons with variants (`ui.button(variant="default"|"outline"|"destructive")`).

3. **Layout & UX Standards**:
   - Master-Detail Layouts: When reviewing items (documents, topics, evidence), prefer a 60/40 or 65/35 dual-column layout rather than infinite vertical scrolling.
   - Action Bars: Group search input, segmented status filters, and primary action buttons on a single horizontal row.
   - Deterministic Keys: Always specify an explicit `key` parameter for any dynamic or repeated `sac` / `ui` component to avoid duplicate ID conflicts and state loss.
