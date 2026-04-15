# UI/UX Redesign — Full Documentation

**Version:** 2.0  
**Date:** 2026-04-15  
**Scope:** Complete replacement of `ui/app.py` layout, design system, navigation, and components  

---

## 1. What Changed & Why

### Before (v1)

- Three horizontal **tabs** across the top of the page
- Basic Streamlit widgets with minor CSS tweaks
- Plain `st.metric()` boxes
- Inline buttons outside forms
- No sidebar, no global navigation
- Single-page feel with no visual hierarchy

### After (v2)

- **Dark sidebar navigation** with logo and module links
- **Full custom CSS design system** (tokens, typography, component styles)
- **HTML-based card components** (metric cards, score cards, badges, decision cards, tables)
- **`st.form()`** wrapping every module — single submit action, no partial triggers
- **Polished result layouts** — grid of cards per module, score bars, flag pills, summary tables
- **Uniform visual language** across all three modules

---

## 2. Architecture: Before vs After

### v1 Layout

```
┌────────────────────────────────────────────────────┐
│  🏦 Banking Analytics System                        │
│  ─────────────────────────────────────────────────  │
│  [ Tab: Customer 360 ] [ Tab: Loan ] [ Tab: Fraud ] │
│  ┌──────────────────────────────────────────────┐  │
│  │ text_input(id)    [button]                   │  │
│  │ st.metric  st.metric  st.metric              │  │
│  │ st.write(badge)                              │  │
│  └──────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────┘
```

### v2 Layout

```
┌──────────┬──────────────────────────────────────────┐
│ SIDEBAR  │  PAGE CONTENT                            │
│  (dark)  │  ┌─────────────────────────────────────┐ │
│          │  │ [icon] Section Title                 │ │
│ 🏦       │  │ Subtitle                             │ │
│ BankCore │  └─────────────────────────────────────┘ │
│ ──────── │  ┌──────────────────────────────────────┐│
│ Modules  │  │ FORM (st.form)                       ││
│  ○ 💳    │  │  col1 | col2    [Submit →]           ││
│  ○ 📊    │  └──────────────────────────────────────┘│
│  ○ ⚠️    │                                          │
│          │  ┌─banner (success/danger)──────────────┐│
│ ──────── │  │ ✓ Decision text                      ││
│ System   │  └──────────────────────────────────────┘│
│ info     │                                          │
│          │  ┌─card──┐ ┌─card──┐ ┌─card──┐          │
│          │  │ Score │ │ Dec.  │ │ Rate  │          │
│          │  └───────┘ └───────┘ └───────┘          │
│          │                                          │
│          │  ┌─card (kv table / summary grid)───────┐│
│          │  └──────────────────────────────────────┘│
└──────────┴──────────────────────────────────────────┘
```

---

## 3. Design System

### 3.1 Color Tokens

All colors are defined as CSS custom properties in `:root {}`:

| Token | Hex | Usage |
|-------|-----|-------|
| `--navy` | `#0f172a` | Sidebar background, headings |
| `--navy-700` | `#1e293b` | Sidebar border, secondary dark |
| `--cyan` | `#06b6d4` | Primary accent, buttons, links |
| `--cyan-dim` | `rgba(6,182,212,.12)` | Active nav item background |
| `--emerald` | `#10b981` | Success states, low risk |
| `--amber` | `#f59e0b` | Warning states, medium risk |
| `--rose` | `#f43f5e` | Danger states, high risk, decline |
| `--slate-50` | `#f8fafc` | Page background |
| `--slate-100` | `#f1f5f9` | Card inner backgrounds, score bars |
| `--slate-200` | `#e2e8f0` | Borders, dividers |
| `--slate-400` | `#94a3b8` | Sub-labels, secondary text |
| `--slate-500` | `#64748b` | Muted text, captions |
| `--slate-600` | `#475569` | Widget labels |
| `--slate-900` | `#0f172a` | Primary text |
| `--card` | `#ffffff` | Card backgrounds |

### 3.2 Typography

| Use | Font | Weight | Size |
|-----|------|--------|------|
| Body | Inter | 400 | 0.875–0.9rem |
| Labels (uppercase) | Inter | 600 | 0.7–0.75rem |
| Values in cards | Inter | 700 | 1.875–2.75rem |
| Code / IDs | JetBrains Mono | 400 | 0.8rem |

Imported via Google Fonts CDN (requires internet on first load; cached after).

### 3.3 Spacing & Radius

- Base border radius: `12px` (cards) / `8px` (inputs, buttons) / `99px` (badges, pills)
- Card padding: `1.25rem 1.5rem`
- Section gap between rows: `1.25rem`
- Column gap: `medium` (Streamlit default ≈ 1rem)

### 3.4 Shadow Scale

| Level | Value |
|-------|-------|
| `--shadow-sm` | `0 1px 3px rgba(0,0,0,.06), 0 1px 2px rgba(0,0,0,.04)` |
| `--shadow-md` | `0 4px 6px rgba(0,0,0,.07), 0 2px 4px rgba(0,0,0,.05)` |
| `--shadow-lg` | `0 10px 25px rgba(0,0,0,.10), 0 4px 10px rgba(0,0,0,.05)` |

---

## 4. Component Library (`ui/app.py`)

All UI components are pure Python functions that return HTML strings.  
All are rendered via `st.markdown(..., unsafe_allow_html=True)`.

### 4.1 `_card(body, extra="")`

Base card wrapper. White background, 12px radius, subtle shadow.  
All other components call this internally.

```python
_card('<p>Hello</p>')
# → <div style="background:#fff;border:1px solid ...">...</div>
```

---

### 4.2 `metric_card(label, value, sub="", color="#0f172a")`

Displays a single KPI with uppercase label, large value, and optional sub-text.

| Parameter | Description |
|-----------|-------------|
| `label` | Uppercase caption (e.g. "Account Balance") |
| `value` | Main display value (e.g. "$12,345.67") |
| `sub` | Optional sub-caption (e.g. "30-day average") |
| `color` | Color of the value text |

Used in: Customer 360 (balance, txn count, monthly avg), Loan Assessment (rate, amounts)

---

### 4.3 `big_score_card(label, score, max_val, color)`

Score display with large number + filled progress bar below.

| Parameter | Description |
|-----------|-------------|
| `label` | Card caption |
| `score` | Integer score value |
| `max_val` | Scale maximum (999 for risk, 850 for credit, 100 for fraud) |
| `color` | Bar and value color (use `score_color()` helper) |

Used in: Customer 360 (risk score), Loan Assessment (credit score), Fraud Detection (fraud score)

---

### 4.4 `badge(text, kind="neutral")`

Inline pill badge. Pill-shaped, colored per semantic kind.

| `kind` | Background | Color | Use case |
|--------|------------|-------|----------|
| `success` | Light green | Dark green | Approved, Low Risk, APPROVE |
| `warning` | Light amber | Dark amber | Review, Medium Risk, REVIEW |
| `danger` | Light rose | Dark rose | Declined, High Risk, DECLINE |
| `info` | Light cyan | Dark cyan | Informational |
| `neutral` | Light slate | Dark slate | Default |

Used in: all three pages for risk levels, decisions, recommendations.

---

### 4.5 `decision_card(approved: bool)`

Shows approved (✓ green circle) or declined (✕ red circle) with large label.  
Used in: Loan Assessment.

---

### 4.6 `banner(text, kind)`

Full-width tinted rectangle for major decisions.  
Uses same `kind` values as `badge()`.  
Used as first element in results sections of all three pages.

```
┌──────────────────────────────────────────────────────────┐
│  ✓  Loan Approved — Customer meets all eligibility...    │  ← green banner
└──────────────────────────────────────────────────────────┘
```

---

### 4.7 `section_title(icon, title, subtitle="")`

Page header with icon block, title, and optional subtitle.

```
[💳]  Customer 360
      Profile, balance & transaction history
```

---

### 4.8 `kv_table(rows: list[tuple[str, str]])`

Two-column table (label | value) inside a card. Used for Account Details summary.  
Rows are separated by light `#f1f5f9` borders.

Used in: Customer 360 (right panel).

---

### 4.9 `summary_grid(rows: list[tuple[str, str]])`

3-column grid of label + value cells inside a card. Compact.  
Used in: Fraud Detection (transaction details row at bottom).

---

### 4.10 `flag_pills(flags: list[str])`

Returns inline rose-colored pills for each fraud flag.  
If no flags: returns grey "No fraud indicators detected." text.

```
⚑ GEO_ANOMALY    ⚑ AMOUNT_ANOMALY    ⚑ UNUSUAL_TIME
```

---

### 4.11 `score_color(score, thresholds)` and custom logic

Returns hex color based on score vs. two thresholds.  
Custom per-page logic for credit score (higher = better) vs. fraud score (lower = better).

---

### 4.12 `fmt_usd(v)` / `fmt_pct(v)`

```python
fmt_usd(1234.56)   # → "$1,234.56"
fmt_pct(4.5)       # → "4.50%"
```

---

## 5. Navigation: Tabs → Sidebar

### Why Sidebar?

| Criterion | Tabs (v1) | Sidebar (v2) |
|-----------|-----------|--------------|
| Scalability | Hard to add >4 tabs | Easy to add new sections |
| Prominence | Top bar, easily missed | Always visible |
| Branding | No space | Logo + system info |
| Professionalism | Standard/generic | Fintech dashboard feel |
| Active state | Hard to style | Clear selection highlight |

### Sidebar Implementation

```python
page = st.radio(
    "nav",
    options=["💳  Customer 360", "📊  Loan Assessment", "⚠️  Fraud Detection"],
    label_visibility="collapsed",
    key="nav",
)
```

The radio buttons are then styled via CSS to look like nav links (no visible radio circle, hover + selected states via background-color and color changes).

### Routing

```python
if "Customer 360" in page:
    page_customer_360()
elif "Loan" in page:
    page_loan_assessment()
else:
    page_fraud_detection()
```

Simple string matching on the selected option.

---

## 6. Form Design

All three pages now wrap inputs in `st.form()`. This means:

- Inputs are **not** evaluated on every keystroke
- The user fills in all fields, then clicks the submit button once
- Streamlit only reruns when the form is submitted (better performance)
- The submit button (`st.form_submit_button`) is styled the same as regular buttons

**Before:**
```python
customer_id = st.text_input(...)   # reruns on each keypress
if st.button("Lookup"):            # separate button, not linked to form
    ...
```

**After:**
```python
with st.form("f_cust"):
    customer_id = st.text_input(...)
    go = st.form_submit_button("Look up →")
if go:
    ...
```

---

## 7. Results Display per Module

### 7.1 Customer 360

```
Customer Name                               [Risk Badge]
ID: C-00001 · Last active: 2025-01-15

┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Balance      │ │ Transactions │ │ Monthly Avg  │
│ $45,231.92   │ │ 1,247        │ │ $3,456.78    │
└──────────────┘ └──────────────┘ └──────────────┘

┌─────────────┐ ┌─────────────────────────────────┐
│ Risk Score  │ │ Account Details (kv table)       │
│   324       │ │ Customer ID  |  C-00001          │
│  [=====>  ] │ │ Name         |  John Smith       │
│ out of 999  │ │ Balance      |  $45,231.92       │
│             │ │ ...                              │
└─────────────┘ └─────────────────────────────────┘
```

### 7.2 Loan Assessment

```
[✓ Loan Approved — Customer meets all eligibility criteria.]

┌──────────────┐ ┌──────────────┐
│ Credit Score │ │ Decision     │
│  680         │ │ ✓ APPROVED   │
│ [========>] │ │              │
└──────────────┘ └──────────────┘

┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Requested    │ │ Max Approved │ │ Interest Rate│
│ $10,000      │ │ $25,000      │ │ 4.50%        │
└──────────────┘ └──────────────┘ └──────────────┘
```

Declined case replaces the terms row with a reason card.

### 7.3 Fraud Detection

```
[✕ Transaction Declined — High fraud risk.]

┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Fraud Score  │ │ Risk Level   │ │ Recommendation│
│  74          │ │ [HIGH]       │ │ [DECLINE]    │
│ [=========>]│ │ 3 indicators │ │ decline txn  │
└──────────────┘ └──────────────┘ └──────────────┘

┌─── Risk Indicators (3 detected) ───────────────┐
│ ⚑ GEO_ANOMALY  ⚑ AMOUNT_ANOMALY  ⚑ VELOCITY   │
└─────────────────────────────────────────────────┘

┌─── Transaction Details ─────────────────────────┐
│ Customer  | Amount  | Channel                   │
│ Location  | MCC     | Timestamp                 │
└─────────────────────────────────────────────────┘
```

---

## 8. CSS Overrides — Key Selectors

| Selector | What it overrides |
|----------|------------------|
| `[data-testid="stSidebar"]` | Sidebar background, border |
| `[data-testid="stSidebar"] .stRadio label` | Nav link style |
| `[data-testid="stAppViewContainer"] > .main > .block-container` | Content padding, max-width |
| `[data-testid="stForm"]` | Form card style (background, border, radius) |
| `.stButton > button, .stFormSubmitButton > button` | Button style |
| `label[data-testid="stWidgetLabel"] > p` | Input label style (uppercase, spacing) |
| `.stTextInput > div > div > input` | Text input style |
| `[data-baseweb="select"] > div` | Selectbox style |
| `#MainMenu, footer, header` | Hides Streamlit chrome |

> **Note:** Streamlit's data-testid attributes and CSS class names can change between minor versions. These selectors target Streamlit 1.x. If upgrading Streamlit, check selector compatibility.

---

## 9. File Changes Summary

| File | Change |
|------|--------|
| `ui/app.py` | **Complete rewrite** — design system, components, sidebar nav, forms, results |
| `ui/runner.py` | No change |
| `ui/parse.py` | No change |
| `docs/UI-REDESIGN.md` | **New** — this document |
| `docs/INDEX.md` | Updated to reference this doc |

---

## 10. Running the Redesigned UI

Same command as before:

```bash
pip install streamlit
streamlit run ui/app.py
```

Browser opens at `http://localhost:8501`.

The sidebar is expanded by default. Click a module name to switch pages. Fill the form and click the submit button to run the analysis.

---

## 11. Future Design Improvements

| Idea | Effort | Impact |
|------|--------|--------|
| Animated number transitions in cards | Medium | High |
| Gauge chart (Plotly/Altair) for risk/credit score | Low | High |
| Dark mode toggle (sidebar switch) | High | Medium |
| Transaction history chart (line chart) | High | High |
| CSV export button on results | Low | Medium |
| Loading skeleton (ghost card) instead of spinner | High | High |
| Toast notification on success | Medium | Low |

---

## Summary

The v2 redesign replaces the flat tab-based layout with a **professional fintech dashboard**:

- **Dark sidebar** with logo, navigation links, and system info
- **Full design token system** (20+ CSS variables for colors, shadows, radii)
- **10+ reusable HTML components** (cards, badges, banners, tables, pills, score bars)
- **Form-based input** (single submit per module, no partial reruns)
- **Consistent result layouts** (grid of cards, score bars, flag pills, summary grids)
- **Zero new dependencies** — still just `streamlit` + existing `runner.py` / `parse.py`
