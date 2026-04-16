"""
Banking Analytics System — Full Redesign
Fintech-grade UI: dark sidebar navigation, card grid layouts, polished components.
"""

import streamlit as st
import pandas as pd
from runner import run_script, RunnerError
from parse import (
    parse_customer_360, parse_loan_scoring, parse_fraud_detect,
    parse_customer_search, parse_customer_list, parse_customer_update,
    parse_customer_transactions, parse_fraud_batch_analysis, ParseError
)
from datetime import datetime


# ═══════════════════════════════════════════════════════════════════
#  DESIGN SYSTEM
# ═══════════════════════════════════════════════════════════════════

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&family=JetBrains+Mono:wght@400;600&display=swap');

/* ── Tokens ─────────────────────────────────────── */
:root {
  --navy:      #0f172a;
  --navy-700:  #1e293b;
  --navy-600:  #334155;
  --cyan:      #06b6d4;
  --cyan-dim:  rgba(6,182,212,.12);
  --emerald:   #10b981;
  --amber:     #f59e0b;
  --rose:      #f43f5e;
  --slate-50:  #f8fafc;
  --slate-100: #f1f5f9;
  --slate-200: #e2e8f0;
  --slate-400: #94a3b8;
  --slate-500: #64748b;
  --slate-600: #475569;
  --slate-900: #0f172a;
  --card:      #ffffff;
  --radius:    12px;
  --shadow-sm: 0 1px 3px rgba(0,0,0,.06), 0 1px 2px rgba(0,0,0,.04);
  --shadow-md: 0 4px 6px rgba(0,0,0,.07), 0 2px 4px rgba(0,0,0,.05);
  --shadow-lg: 0 10px 25px rgba(0,0,0,.10), 0 4px 10px rgba(0,0,0,.05);
}

/* ── Reset & base ────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; }
body, .stApp {
  font-family: 'Inter', sans-serif;
  background-color: var(--slate-50);
}

/* ── Hide Streamlit chrome ───────────────────────── */
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stDecoration"]  { display: none; }
[data-testid="stToolbar"]     { display: none; }

/* ── Sidebar — dark panel ────────────────────────── */
[data-testid="stSidebar"] {
  background-color: var(--navy) !important;
  border-right: 1px solid var(--navy-700);
  min-width: 220px;
}
[data-testid="stSidebar"] > div:first-child {
  padding: 2rem 1.5rem;
}

/* Radio group → nav links */
[data-testid="stSidebar"] .stRadio > label { display: none; }
/* Hide the "Menu" widget label specifically, keep option labels */
[data-testid="stSidebar"] label[data-testid="stWidgetLabel"] { display: none !important; }
[data-testid="stSidebar"] .stRadio [data-baseweb="radio"] {
  background: transparent;
  padding: 0;
}
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
[data-testid="stSidebar"] .stRadio label {
  display: flex !important;
  align-items: center;
  gap: 10px;
  padding: 9px 12px;
  border-radius: 8px;
  cursor: pointer;
  color: rgba(255,255,255,.6) !important;
  font-size: .9rem;
  font-weight: 500;
  transition: background .15s ease, color .15s ease;
  border: 1px solid transparent;
}
[data-testid="stSidebar"] .stRadio label:hover {
  background: rgba(255,255,255,.06) !important;
  color: rgba(255,255,255,.9) !important;
}
[data-testid="stSidebar"] .stRadio label[data-checked="true"],
[data-testid="stSidebar"] .stRadio input:checked ~ div {
  background: var(--cyan-dim) !important;
  color: var(--cyan) !important;
  border-color: rgba(6,182,212,.25) !important;
}
[data-testid="stSidebar"] .stRadio input[type="radio"] { display: none !important; }
[data-testid="stSidebar"] p {
  color: rgba(255,255,255,.9);
  margin: 0;
}

/* Sidebar divider */
[data-testid="stSidebar"] hr {
  border-color: rgba(255,255,255,.08);
  margin: 1.5rem 0;
}

/* ── Main content ────────────────────────────────── */
[data-testid="stAppViewContainer"] > .main > .block-container {
  padding: 2.5rem 2.5rem 3rem;
  max-width: 1100px;
}

/* ── Typography ──────────────────────────────────── */
h1, h2, h3 {
  letter-spacing: -.03em;
  color: var(--slate-900);
  line-height: 1.2;
}

/* ── Widget labels ───────────────────────────────── */
label[data-testid="stWidgetLabel"] p,
label[data-testid="stWidgetLabel"] span {
  color: #000000 !important;
  font-size: .8rem !important;
  font-weight: 600 !important;
}

/* ── Text & number inputs ─────────────────────────── */
.stTextInput > div > div,
.stNumberInput > div > div {
  background: #ffffff !important;
}
.stTextInput input,
.stNumberInput input {
  background: #ffffff !important;
  border: 1.5px solid var(--slate-200) !important;
  border-radius: 8px !important;
  color: #000000 !important;
  font-family: 'Inter', sans-serif;
  font-size: .875rem;
  padding: .55rem .875rem !important;
  transition: border-color .15s, box-shadow .15s;
}
.stTextInput input:focus,
.stNumberInput input:focus {
  border-color: var(--cyan) !important;
  box-shadow: 0 0 0 3px rgba(6,182,212,.12) !important;
  outline: none;
}

/* Number input +/- buttons */
.stNumberInput button {
  background: #ffffff !important;
  color: #000000 !important;
  border: 1px solid var(--slate-200) !important;
}

/* ── Selectbox ───────────────────────────────────── */
.stSelectbox > div > div,
[data-baseweb="select"],
[data-baseweb="select"] > div,
[data-baseweb="select"] > div > div,
[data-baseweb="select"] span {
  background: #ffffff !important;
  color: #000000 !important;
}
[data-baseweb="select"] > div {
  border: 1.5px solid var(--slate-200) !important;
  border-radius: 8px !important;
  font-size: .875rem;
}
[data-baseweb="select"] > div:focus-within {
  border-color: var(--cyan) !important;
  box-shadow: 0 0 0 3px rgba(6,182,212,.12) !important;
}
/* Dropdown list */
[data-baseweb="popover"],
[data-baseweb="menu"],
[data-baseweb="popover"] ul,
[data-baseweb="popover"] li {
  background: #ffffff !important;
  color: #000000 !important;
}
[data-baseweb="popover"] [role="option"] {
  background: #ffffff !important;
  color: #000000 !important;
}
[data-baseweb="popover"] [role="option"]:hover,
[data-baseweb="popover"] [aria-selected="true"] {
  background: var(--slate-100) !important;
  color: #000000 !important;
}

/* ── Date & time inputs ──────────────────────────── */
.stDateInput input,
.stTimeInput input {
  background: #ffffff !important;
  color: #000000 !important;
  border: 1.5px solid var(--slate-200) !important;
  border-radius: 8px !important;
}

/* ── Buttons ─────────────────────────────────────── */
.stButton > button, .stFormSubmitButton > button {
  font-family: 'Inter', sans-serif !important;
  font-weight: 600 !important;
  font-size: .875rem !important;
  background: var(--cyan) !important;
  color: white !important;
  border: none !important;
  border-radius: 8px !important;
  padding: .6rem 1.5rem !important;
  transition: background .2s, box-shadow .2s, transform .1s !important;
  box-shadow: var(--shadow-sm) !important;
  letter-spacing: .01em;
}
.stButton > button:hover, .stFormSubmitButton > button:hover {
  background: #0891b2 !important;
  box-shadow: var(--shadow-lg) !important;
  transform: translateY(-1px);
}
.stButton > button:active, .stFormSubmitButton > button:active {
  transform: translateY(0);
}

/* ── Divider ─────────────────────────────────────── */
hr {
  border: none;
  border-top: 1px solid var(--slate-200);
  margin: 1.75rem 0;
}

/* ── Alerts ──────────────────────────────────────── */
[data-testid="stAlert"] {
  border-radius: 8px !important;
  border: 1px solid;
  font-size: .875rem;
}

/* ── Spinner ─────────────────────────────────────── */
[data-testid="stSpinner"] { color: var(--cyan) !important; }

/* ── Form border ─────────────────────────────────── */
[data-testid="stForm"] {
  background: var(--card);
  border: 1px solid var(--slate-200) !important;
  border-radius: var(--radius);
  padding: 1.5rem !important;
  box-shadow: var(--shadow-sm);
}

/* ── Scrollbar ───────────────────────────────────── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--slate-100); }
::-webkit-scrollbar-thumb {
  background: var(--slate-200); border-radius: 99px;
}
::-webkit-scrollbar-thumb:hover { background: var(--slate-400); }
</style>
"""


# ═══════════════════════════════════════════════════════════════════
#  HTML COMPONENT LIBRARY
# ═══════════════════════════════════════════════════════════════════

def _card(body: str, extra: str = "") -> str:
    return (
        f'<div style="background:#fff;border:1px solid #e2e8f0;border-radius:12px;'
        f'padding:1.25rem 1.5rem;box-shadow:0 1px 3px rgba(0,0,0,.06);{extra}">'
        f'{body}</div>'
    )


def metric_card(label: str, value: str, sub: str = "", color: str = "#0f172a") -> str:
    sub_html = (
        f'<div style="font-size:.75rem;color:#94a3b8;margin-top:.3rem">{sub}</div>'
        if sub else ""
    )
    return _card(
        f'<div style="font-size:.7rem;font-weight:600;text-transform:uppercase;'
        f'letter-spacing:.08em;color:#64748b;margin-bottom:.45rem">{label}</div>'
        f'<div style="font-size:1.875rem;font-weight:700;color:{color};'
        f'letter-spacing:-.04em;line-height:1">{value}</div>'
        f'{sub_html}'
    )


def big_score_card(label: str, score: int, max_val: int, color: str) -> str:
    pct = min(score / max_val * 100, 100)
    return _card(
        f'<div style="font-size:.7rem;font-weight:600;text-transform:uppercase;'
        f'letter-spacing:.08em;color:#64748b;margin-bottom:.5rem">{label}</div>'
        f'<div style="font-size:2.75rem;font-weight:700;color:{color};'
        f'letter-spacing:-.04em;line-height:1">{score}</div>'
        f'<div style="font-size:.72rem;color:#94a3b8;margin:.2rem 0 .7rem">out of {max_val}</div>'
        f'<div style="height:5px;background:#f1f5f9;border-radius:99px;overflow:hidden">'
        f'<div style="height:100%;width:{pct:.1f}%;background:{color};border-radius:99px"></div>'
        f'</div>'
        f'<div style="text-align:right;font-size:.67rem;color:{color};'
        f'font-weight:600;margin-top:.25rem">{score}/{max_val}</div>'
    )


def badge(text: str, kind: str = "neutral") -> str:
    palettes = {
        "success": ("#d1fae5", "#065f46", "#6ee7b7"),
        "warning": ("#fef3c7", "#92400e", "#fcd34d"),
        "danger":  ("#ffe4e6", "#9f1239", "#fda4af"),
        "info":    ("#cffafe", "#164e63", "#67e8f9"),
        "neutral": ("#f1f5f9", "#334155", "#cbd5e1"),
    }
    bg, fg, border = palettes.get(kind, palettes["neutral"])
    return (
        f'<span style="display:inline-flex;align-items:center;padding:.3rem .85rem;'
        f'border-radius:99px;font-size:.78rem;font-weight:600;letter-spacing:.03em;'
        f'background:{bg};color:{fg};border:1px solid {border}">{text}</span>'
    )


def decision_card(approved: bool) -> str:
    if approved:
        icon, label, bg, fg, border = "✓", "APPROVED", "#d1fae5", "#065f46", "#6ee7b7"
    else:
        icon, label, bg, fg, border = "✕", "DECLINED", "#ffe4e6", "#9f1239", "#fda4af"
    return _card(
        f'<div style="font-size:.7rem;font-weight:600;text-transform:uppercase;'
        f'letter-spacing:.08em;color:#64748b;margin-bottom:.75rem">Decision</div>'
        f'<div style="display:flex;align-items:center;gap:.75rem">'
        f'<div style="width:40px;height:40px;border-radius:50%;background:{bg};'
        f'border:2px solid {border};display:flex;align-items:center;justify-content:center;'
        f'font-size:1.1rem;font-weight:700;color:{fg}">{icon}</div>'
        f'<div style="font-size:1.5rem;font-weight:700;color:{fg};'
        f'letter-spacing:-.03em">{label}</div>'
        f'</div>'
    )


def banner(text: str, kind: str = "info") -> str:
    palettes = {
        "success": ("#f0fdf4", "#15803d", "#bbf7d0"),
        "warning": ("#fffbeb", "#b45309", "#fde68a"),
        "danger":  ("#fff1f2", "#be123c", "#fecdd3"),
        "info":    ("#f0f9ff", "#0369a1", "#bae6fd"),
    }
    bg, fg, border = palettes.get(kind, palettes["info"])
    return (
        f'<div style="background:{bg};border:1px solid {border};border-radius:10px;'
        f'padding:.875rem 1.125rem;color:{fg};font-weight:600;font-size:.875rem;'
        f'margin:.75rem 0">{text}</div>'
    )


def section_title(icon: str, title: str, subtitle: str = "") -> str:
    sub = (
        f'<div style="color:#64748b;font-size:.875rem;margin:.2rem 0 0">{subtitle}</div>'
        if subtitle else ""
    )
    return (
        f'<div style="display:flex;align-items:flex-start;gap:.875rem;margin-bottom:1.75rem">'
        f'<div style="background:rgba(6,182,212,.1);border-radius:10px;padding:.65rem;'
        f'font-size:1.375rem;line-height:1;flex-shrink:0">{icon}</div>'
        f'<div><div style="font-size:1.375rem;font-weight:700;color:#0f172a;'
        f'letter-spacing:-.03em">{title}</div>{sub}</div>'
        f'</div>'
    )


def summary_grid(rows: list[tuple[str, str]]) -> str:
    cells = "".join(
        f'<div>'
        f'<div style="font-size:.72rem;color:#94a3b8;text-transform:uppercase;'
        f'letter-spacing:.05em;margin-bottom:.2rem">{k}</div>'
        f'<div style="font-size:.875rem;font-weight:600;color:#0f172a">{v}</div>'
        f'</div>'
        for k, v in rows
    )
    return _card(
        f'<div style="font-size:.7rem;font-weight:600;text-transform:uppercase;'
        f'letter-spacing:.08em;color:#64748b;margin-bottom:.875rem">Details</div>'
        f'<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:1rem">'
        f'{cells}</div>'
    )


def kv_table(rows: list[tuple[str, str]]) -> str:
    trs = "".join(
        f'<tr>'
        f'<td style="padding:.5rem 0;color:#64748b;font-size:.875rem;'
        f'border-bottom:1px solid #f1f5f9">{k}</td>'
        f'<td style="padding:.5rem 0;font-weight:600;color:#0f172a;font-size:.875rem;'
        f'text-align:right;border-bottom:1px solid #f1f5f9">{v}</td>'
        f'</tr>'
        for k, v in rows
    )
    return _card(
        f'<div style="font-size:.7rem;font-weight:600;text-transform:uppercase;'
        f'letter-spacing:.08em;color:#64748b;margin-bottom:.75rem">Account Details</div>'
        f'<table style="width:100%;border-collapse:collapse">{trs}</table>'
    )


def flag_pills(flags: list[str]) -> str:
    if not flags:
        return '<span style="color:#64748b;font-size:.875rem">No fraud indicators detected.</span>'
    pills = "".join(
        f'<span style="display:inline-flex;align-items:center;gap:5px;'
        f'padding:.3rem .75rem;background:rgba(244,63,94,.07);color:#be123c;'
        f'border:1px solid rgba(244,63,94,.2);border-radius:99px;'
        f'font-size:.78rem;font-weight:600;margin:.2rem">⚑ {f}</span>'
        for f in flags
    )
    return pills


def fmt_usd(v: float) -> str:
    return f"${v:,.2f}"


def fmt_pct(v: float) -> str:
    return f"{v:.2f}%"


def score_color(score: int, thresholds: tuple[int, int]) -> str:
    lo, hi = thresholds
    if score < lo:
        return "#10b981"   # emerald — good
    if score < hi:
        return "#f59e0b"   # amber — warning
    return "#f43f5e"       # rose — danger


# ═══════════════════════════════════════════════════════════════════
#  REUSABLE WIDGETS
# ═══════════════════════════════════════════════════════════════════

def search_widget(page_key: str) -> str:
    """
    Customer search by last name widget.
    Returns selected customer_id or empty string.
    Stores full customer info in session state for display.
    """
    session_key = f"selected_customer_{page_key}"
    customer_info_key = f"selected_customer_info_{page_key}"

    # Display search heading
    st.markdown(
        '<div style="margin-bottom:1rem">'
        '<div style="font-size:.8rem;font-weight:700;text-transform:uppercase;'
        'letter-spacing:.08em;color:#64748b">🔍 Search by Last Name</div>'
        '</div>',
        unsafe_allow_html=True
    )

    # Search input and button
    col1, col2 = st.columns([3, 1], gap="small")
    with col1:
        search_name = st.text_input(
            "Last Name",
            placeholder="e.g., Smith",
            key=f"search_name_{page_key}",
            label_visibility="collapsed"
        )
    with col2:
        st.write("")  # Spacing
        search_btn = st.button("Search", key=f"search_{page_key}", use_container_width=True)

    # Execute search when button clicked
    if search_btn and search_name.strip():
        try:
            with st.spinner("Searching…"):
                raw = run_script("python/customer_search.py", [search_name])
                results = parse_customer_search(raw)

            if not results:
                st.warning(f"No customers found with last name '{search_name}'")
            else:
                st.markdown(
                    f'<div style="font-size:.75rem;color:#64748b;margin:1rem 0 .5rem 0;">'
                    f'{len(results)} result{"s" if len(results) != 1 else ""} found</div>',
                    unsafe_allow_html=True
                )

                # Display each result as a selectable option
                for idx, customer in enumerate(results):
                    col_info, col_select = st.columns([5, 1], gap="small")

                    with col_info:
                        # Use markdown with proper color styling for visibility
                        st.markdown(
                            f'<div style="color:#0f172a;font-size:.95rem;padding:.5rem;">'
                            f'<strong>{customer["name"]}</strong> — '
                            f'{customer["customer_id"]} · {customer["city"]}</div>',
                            unsafe_allow_html=True
                        )

                    with col_select:
                        def select_customer(cust_id=customer['customer_id'], cust_name=customer['name']):
                            st.session_state[session_key] = cust_id
                            st.session_state[customer_info_key] = {"id": cust_id, "name": cust_name}

                        st.button(
                            "→",
                            key=f"select_{page_key}_{idx}_{customer['customer_id']}",
                            use_container_width=True,
                            on_click=select_customer,
                            help="Select this customer"
                        )

        except (RunnerError, ParseError) as e:
            st.error(f"Search failed: {str(e)}")

    # Divider to separate from form
    st.divider()

    # Return the selected customer ID from session state
    return st.session_state.get(session_key, "")


# ═══════════════════════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════════════════════

def build_sidebar() -> str:
    with st.sidebar:
        st.markdown(
            '<div style="margin-bottom:2.25rem">'
            '<div style="font-size:1.375rem;font-weight:700;color:#fff;'
            'letter-spacing:-.03em">🏦 BankCore</div>'
            '<div style="font-size:.7rem;color:rgba(255,255,255,.35);'
            'font-weight:500;margin-top:.2rem;text-transform:uppercase;'
            'letter-spacing:.1em">Analytics Platform</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div style="font-size:.65rem;font-weight:700;text-transform:uppercase;'
            'letter-spacing:.12em;color:rgba(255,255,255,.3);margin-bottom:.5rem">'
            'Modules</div>',
            unsafe_allow_html=True,
        )

        page = st.radio(
            "Menu",
            options=["💳  Customer 360", "📊  Loan Assessment", "⚠️  Fraud Detection", "👥  Customer List"],
            label_visibility="collapsed",
            key="nav",
        )

        st.markdown("<hr>", unsafe_allow_html=True)

        st.markdown(
            '<div style="color:rgba(255,255,255,.25);font-size:.7rem;line-height:1.7">'
            '<div style="color:rgba(255,255,255,.4);font-weight:600;'
            'margin-bottom:.4rem">System</div>'
            'COBOL + Python IPC<br>'
            'Parquet · DuckDB<br>'
            'Fixed-width records (145 / 51 / 78 B)'
            '</div>',
            unsafe_allow_html=True,
        )

    return page


# ═══════════════════════════════════════════════════════════════════
#  PAGE: CUSTOMER 360
# ═══════════════════════════════════════════════════════════════════

def page_customer_360():
    st.markdown(
        section_title("💳", "Customer 360", "Profile, balance & transaction history"),
        unsafe_allow_html=True,
    )

    # ── Search widget (only way to select customer) ──────
    cid = search_widget("c360")

    # If no customer selected, show instructions
    if not cid:
        st.info("👆 Search for a customer above to view their profile")
        return

    # Auto-load customer 360 data when customer is selected
    with st.spinner("Fetching customer data…"):
        try:
            raw = run_script("python/customer_360.py", [cid])
            r = parse_customer_360(raw)
        except (RunnerError, ParseError) as e:
            st.error(str(e))
            return

    # Risk classification
    rs = r["risk_score"]
    risk_kind  = "success" if rs < 300 else "warning" if rs < 600 else "danger"
    risk_label = "Low Risk"    if rs < 300 else "Medium Risk" if rs < 600 else "High Risk"
    risk_color = "#10b981"     if rs < 300 else "#f59e0b"      if rs < 600 else "#f43f5e"

    # ── Customer header ──────────────────────────────
    st.markdown(
        f'<div style="display:flex;align-items:center;justify-content:space-between;'
        f'flex-wrap:wrap;gap:.75rem;margin-bottom:1.5rem">'
        f'<div>'
        f'<div style="font-size:1.5rem;font-weight:700;color:#0f172a;'
        f'letter-spacing:-.03em">{r["name"]}</div>'
        f'<div style="color:#64748b;font-size:.825rem;margin-top:.2rem">'
        f'ID&nbsp;<code style="background:#f1f5f9;padding:.05rem .35rem;'
        f'border-radius:4px;font-size:.78rem">{cid}</code>'
        f'&nbsp;·&nbsp;Last active&nbsp;<strong>{r["last_txn_date"]}</strong>'
        f'</div>'
        f'</div>'
        f'<div>{badge(risk_label, risk_kind)}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Metric cards row ─────────────────────────────
    col1, col2, col3 = st.columns(3, gap="medium")
    with col1:
        st.markdown(metric_card("Account Balance", fmt_usd(r["balance"]), "Current balance"), unsafe_allow_html=True)
    with col2:
        st.markdown(metric_card("Total Transactions", f"{r['txn_count']:,}", "All time"), unsafe_allow_html=True)
    with col3:
        st.markdown(metric_card("Avg Monthly Spend", fmt_usd(r["avg_monthly"]), "30-day rolling avg"), unsafe_allow_html=True)

    st.markdown("<div style='margin-top:1.25rem'></div>", unsafe_allow_html=True)

    # ── Risk + details ───────────────────────────────
    col1, col2 = st.columns([1, 2], gap="medium")
    with col1:
        st.markdown(big_score_card("Risk Score", rs, 999, risk_color), unsafe_allow_html=True)
    with col2:
        st.markdown(
            kv_table([
                ("Customer ID",        cid),
                ("Full Name",          r["name"]),
                ("Account Balance",    fmt_usd(r["balance"])),
                ("Total Transactions", f"{r['txn_count']:,}"),
                ("Avg Monthly Spend",  fmt_usd(r["avg_monthly"])),
                ("Last Transaction",   r["last_txn_date"]),
                ("Risk Classification", risk_label),
            ]),
            unsafe_allow_html=True,
        )


# ═══════════════════════════════════════════════════════════════════
#  PAGE: LOAN ASSESSMENT
# ═══════════════════════════════════════════════════════════════════

def page_loan_assessment():
    st.markdown(
        section_title("📊", "Loan Assessment", "Credit analysis & eligibility decision"),
        unsafe_allow_html=True,
    )

    # ── Search widget ────────────────────────────────────
    cid = search_widget("loan")

    # If no customer selected, show instructions
    if not cid:
        st.info("👆 Search for a customer above to continue")
        return

    # ── Display selected customer (read-only) ──────────────
    customer_info = st.session_state.get("selected_customer_info_loan", {})
    customer_name = customer_info.get("name", "")
    display_text = f"{customer_name} — {cid}" if customer_name else cid

    st.markdown(
        f'<div style="background:#f1f5f9;padding:1rem;border-radius:8px;margin-bottom:1.5rem">'
        f'<div style="font-size:.75rem;text-transform:uppercase;color:#64748b;font-weight:600;margin-bottom:.3rem">Selected Customer</div>'
        f'<div style="font-size:1.1rem;font-weight:600;color:#0f172a">{display_text}</div>'
        f'</div>',
        unsafe_allow_html=True
    )

    # ── Loan assessment form ─────────────────────────────
    with st.form("f_loan"):
        col1, col2 = st.columns(2, gap="medium")
        with col1:
            amount = st.number_input("Loan Amount ($)", min_value=1000, max_value=500000,
                                     value=10000, step=1000, format="%d")
            term = st.selectbox("Loan Term", [12, 24, 36, 48, 60, 84, 120],
                               index=2, format_func=lambda x: f"{x} months")
        with col2:
            purpose = st.selectbox("Purpose", ["HOME", "AUTO", "PERS", "EDUC"])
            st.write("")  # Spacing

        go = st.form_submit_button("Run Credit Assessment →", use_container_width=True)

    if not go:
        return

    if not cid.strip():
        st.error("Customer ID is required.")
        return

    with st.spinner("Running credit assessment…"):
        try:
            raw = run_script("python/loan_scoring.py", [cid, str(amount), str(term), purpose])
            r = parse_loan_scoring(raw)
        except (RunnerError, ParseError) as e:
            st.error(str(e))
            return

    # ── Decision banner ──────────────────────────────
    if r["eligible"]:
        st.markdown(
            banner("✓  Loan Approved — Customer meets all eligibility criteria.", "success"),
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            banner(f"✕  Loan Declined — {r['reason']}", "danger"),
            unsafe_allow_html=True,
        )

    st.markdown("<div style='margin-top:.5rem'></div>", unsafe_allow_html=True)

    # ── Credit score + decision ───────────────────────
    cs = r["credit_score"]
    cs_color = score_color(cs, (580, 670))   # <580 bad, 580-670 fair, >670 good
    # For credit score: lower is worse, so invert thresholds
    cs_color = "#10b981" if cs >= 700 else "#f59e0b" if cs >= 580 else "#f43f5e"

    col1, col2 = st.columns(2, gap="medium")
    with col1:
        st.markdown(big_score_card("Credit Score", cs, 850, cs_color), unsafe_allow_html=True)
    with col2:
        st.markdown(decision_card(r["eligible"]), unsafe_allow_html=True)

    st.markdown("<div style='margin-top:1.25rem'></div>", unsafe_allow_html=True)

    if r["eligible"]:
        # ── Loan terms row ─────────────────────────────
        col1, col2, col3 = st.columns(3, gap="medium")
        with col1:
            st.markdown(metric_card("Requested Amount", fmt_usd(amount), f"{purpose} loan"), unsafe_allow_html=True)
        with col2:
            st.markdown(metric_card("Max Approved", fmt_usd(r["max_amount"]), "Upper limit"), unsafe_allow_html=True)
        with col3:
            st.markdown(metric_card("Interest Rate (APR)", fmt_pct(r["int_rate"] * 100), f"{term} month term"), unsafe_allow_html=True)
    else:
        # ── Decline detail ─────────────────────────────
        col1, col2 = st.columns(2, gap="medium")
        with col1:
            st.markdown(metric_card("Credit Score", f"{cs} / 850", "Current score", color=cs_color), unsafe_allow_html=True)
        with col2:
            st.markdown(
                _card(
                    f'<div style="font-size:.7rem;font-weight:600;text-transform:uppercase;'
                    f'letter-spacing:.08em;color:#64748b;margin-bottom:.5rem">Reason</div>'
                    f'<div style="color:#be123c;font-weight:600;font-size:.9rem">{r["reason"]}</div>'
                ),
                unsafe_allow_html=True,
            )


# ═══════════════════════════════════════════════════════════════════
#  HELPER: Fetch Customer Transactions
# ═══════════════════════════════════════════════════════════════════

def fetch_customer_transactions(customer_id: str) -> dict:
    """
    Fetch ALL transactions for a customer.

    Args:
        customer_id: Customer ID (e.g., "C-00001")

    Returns:
        {
            'count': int,
            'transactions': [...]
        }
    """
    try:
        raw = run_script("python/customer_transactions.py", [customer_id])
        return parse_customer_transactions(raw)
    except (RunnerError, ParseError) as e:
        st.error(f"Failed to fetch transactions: {str(e)}")
        return {'count': 0, 'transactions': []}


# ═══════════════════════════════════════════════════════════════════
#  PAGE: FRAUD DETECTION
# ═══════════════════════════════════════════════════════════════════

def page_fraud_detection():
    st.markdown(
        section_title("⚠️", "Fraud Detection", "Real-time transaction risk analysis"),
        unsafe_allow_html=True,
    )

    # ── Search widget ────────────────────────────────────
    cid = search_widget("fraud")

    # If no customer selected, show instructions
    if not cid:
        st.info("👆 Search for a customer above to continue")
        return

    # ── Display selected customer (read-only) ──────────────
    customer_info = st.session_state.get("selected_customer_info_fraud", {})
    customer_name = customer_info.get("name", "")
    display_text = f"{customer_name} — {cid}" if customer_name else cid

    st.markdown(
        f'<div style="background:#f1f5f9;padding:1rem;border-radius:8px;margin-bottom:1.5rem">'
        f'<div style="font-size:.75rem;text-transform:uppercase;color:#64748b;font-weight:600;margin-bottom:.3rem">Selected Customer</div>'
        f'<div style="font-size:1.1rem;font-weight:600;color:#0f172a">{display_text}</div>'
        f'</div>',
        unsafe_allow_html=True
    )

    # ══════════════════════════════════════════════════════════════
    # NEW: Fetch and display transaction list
    # ══════════════════════════════════════════════════════════════

    # Initialize session state for transaction list and batch analysis
    if "fraud_all_transactions" not in st.session_state:
        st.session_state.fraud_all_transactions = []
    if "fraud_txns_loaded_cid" not in st.session_state:
        st.session_state.fraud_txns_loaded_cid = ""
    if "fraud_batch_result" not in st.session_state:
        st.session_state.fraud_batch_result = None
    if "fraud_batch_cid" not in st.session_state:
        st.session_state.fraud_batch_cid = ""

    # Invalidate cached transactions if customer changed
    if st.session_state.fraud_txns_loaded_cid != cid:
        st.session_state.fraud_all_transactions = []
        st.session_state.fraud_txns_loaded_cid = cid
        st.session_state.fraud_batch_result = None

    # Invalidate cached batch result if customer changed
    if st.session_state.fraud_batch_cid != cid:
        st.session_state.fraud_batch_result = None
        st.session_state.fraud_batch_cid = cid

    # Load all transactions once (cached per customer)
    if not st.session_state.fraud_all_transactions:
        with st.spinner("Loading transactions..."):
            txn_result = fetch_customer_transactions(cid)
            st.session_state.fraud_all_transactions = txn_result['transactions']

    # Display transaction list with filters
    st.subheader("All Transactions")

    # Filter controls (4 columns)
    st.markdown("**Filters:**")
    col1, col2, col3, col4 = st.columns([3, 2, 2, 2], gap="medium")
    with col1:
        search_text = st.text_input("Search Merchant or City", placeholder="e.g., Jones Inc, New York", key="fraud_search")
    with col2:
        channel_filter = st.multiselect("Channel", ["ATM", "ONL", "POS", "MOB"], key="fraud_channel")
    with col3:
        min_amount = st.number_input("Min Amount ($)", min_value=0.0, value=0.0, step=10.0, key="fraud_min")
    with col4:
        max_amount = st.number_input("Max Amount ($)", min_value=0.0, value=10000.0, step=10.0, key="fraud_max")

    # Apply filters in-memory
    txns = st.session_state.fraud_all_transactions
    df = pd.DataFrame(txns) if txns else pd.DataFrame()

    if not df.empty:
        if search_text:
            mask = (
                df['merchant'].str.contains(search_text, case=False, na=False) |
                df['city'].str.contains(search_text, case=False, na=False)
            )
            df = df[mask]
        if channel_filter:
            df = df[df['channel'].isin(channel_filter)]
        if min_amount > 0:
            df = df[df['amount'] >= min_amount]
        if max_amount > 0:
            df = df[df['amount'] <= max_amount]

    # Display transaction table
    if not df.empty:
        total = len(st.session_state.fraud_all_transactions)
        st.caption(f"Showing {len(df)} of {total} transactions")

        display_df = df.rename(columns={
            'txn_id': 'ID',
            'date': 'Date',
            'time': 'Time',
            'amount': 'Amount ($)',
            'merchant': 'Merchant',
            'mcc': 'MCC',
            'city': 'City',
            'channel': 'Channel',
        })

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            height=400,
            column_config={
                "Amount ($)": st.column_config.NumberColumn(format="$%.2f"),
                "ID": st.column_config.TextColumn(width="small"),
            }
        )
    else:
        st.warning("No transactions found matching the filters.")

    # ══════════════════════════════════════════════════════════════
    # BATCH FRAUD ANALYSIS
    # ══════════════════════════════════════════════════════════════

    st.markdown("---")
    col_btn, col_hint = st.columns([2, 5], gap="small")
    with col_btn:
        run_batch = st.button(
            "Analyse All Transactions",
            key="fraud_run_batch",
            use_container_width=True,
            help="Score every transaction for this customer at once"
        )
    with col_hint:
        st.markdown(
            '<div style="color:#64748b;font-size:.825rem;padding:.6rem 0">'
            'Runs a full fraud report across all historical transactions.</div>',
            unsafe_allow_html=True
        )

    if run_batch:
        with st.spinner("Running batch fraud analysis..."):
            try:
                raw = run_script("python/fraud_batch_analysis.py", [cid])
                st.session_state.fraud_batch_result = parse_fraud_batch_analysis(raw)
            except (RunnerError, ParseError) as e:
                st.error(str(e))
                st.session_state.fraud_batch_result = None

    # Display batch results if available
    batch = st.session_state.fraud_batch_result
    if batch is not None:
        summary = batch['summary']
        txns = batch['transactions']

        # 1. Summary cards
        st.markdown(
            section_title("📊", "Fraud Analysis Report",
                          f"Customer {cid} — {summary['total']} transactions analysed"),
            unsafe_allow_html=True
        )

        col1, col2, col3, col4 = st.columns(4, gap="medium")
        with col1:
            st.markdown(metric_card("Total Transactions", str(summary['total']), "analysed"),
                       unsafe_allow_html=True)
        with col2:
            st.markdown(metric_card("High Risk", str(summary['high_count']), "DECLINE",
                                   color="#f43f5e"), unsafe_allow_html=True)
        with col3:
            st.markdown(metric_card("Medium Risk", str(summary['medium_count']), "REVIEW",
                                   color="#f59e0b"), unsafe_allow_html=True)
        with col4:
            st.markdown(metric_card("Low Risk", str(summary['low_count']), "APPROVE",
                                   color="#10b981"), unsafe_allow_html=True)

        # 2. Risk distribution
        if summary['total'] > 0:
            high_pct = summary['high_count'] / summary['total'] * 100
            medium_pct = summary['medium_count'] / summary['total'] * 100
            low_pct = summary['low_count'] / summary['total'] * 100
            st.markdown(
                _card(
                    f'<div style="font-size:.7rem;font-weight:600;text-transform:uppercase;'
                    f'letter-spacing:.08em;color:#64748b;margin-bottom:.875rem">Risk Distribution</div>'
                    f'<div style="display:flex;gap:2rem">'
                    f'<span style="color:#f43f5e;font-weight:600">HIGH {high_pct:.1f}%</span>'
                    f'<span style="color:#f59e0b;font-weight:600">MEDIUM {medium_pct:.1f}%</span>'
                    f'<span style="color:#10b981;font-weight:600">LOW {low_pct:.1f}%</span>'
                    f'</div>'
                ),
                unsafe_allow_html=True
            )

        # 3. Full transaction results table
        st.markdown("#### All Transactions")
        if txns:
            df = pd.DataFrame(txns)
            df = df.rename(columns={
                'txn_id': 'Transaction ID',
                'date': 'Date',
                'amount': 'Amount ($)',
                'mcc': 'MCC',
                'city': 'City',
                'channel': 'Channel',
                'score': 'Score',
                'risk': 'Risk',
                'recommendation': 'Action',
                'is_fraud': 'Ground Truth',
            })

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Amount ($)": st.column_config.NumberColumn(format="$%.2f"),
                    "Score": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%d"),
                    "Transaction ID": st.column_config.TextColumn(width="medium"),
                }
            )

        # 4. Flagged transactions section (HIGH only)
        high_risk_txns = [t for t in txns if t['risk'] == 'HIGH']
        if high_risk_txns:
            st.markdown(
                banner(
                    f"⚠ {len(high_risk_txns)} HIGH RISK transaction"
                    f"{'s' if len(high_risk_txns) != 1 else ''} — immediate review recommended",
                    "danger"
                ),
                unsafe_allow_html=True
            )
            st.markdown("#### Flagged Transactions")

            for t in high_risk_txns:
                gt_note = ""
                if t['is_fraud'] == "true":
                    gt_note = " — confirmed fraud"
                elif t['is_fraud'] == "false":
                    gt_note = " — labelled non-fraud"

                fs_color = "#f43f5e"
                st.markdown(
                    _card(
                        f'<div style="display:flex;justify-content:space-between;'
                        f'align-items:flex-start;flex-wrap:wrap;gap:.5rem">'
                        f'<div>'
                        f'  <code style="background:#f1f5f9;padding:.1rem .4rem;'
                        f'  border-radius:4px;font-size:.8rem">{t["txn_id"]}</code>'
                        f'  <span style="margin-left:.5rem;color:#64748b;font-size:.8rem">'
                        f'  {t["date"]}{gt_note}</span>'
                        f'</div>'
                        f'<div style="display:flex;gap:.75rem;align-items:center">'
                        f'  {badge("HIGH", "danger")}'
                        f'  {badge("DECLINE", "danger")}'
                        f'  <span style="font-size:.875rem;font-weight:600;color:{fs_color}">'
                        f'  Score {t["score"]}</span>'
                        f'</div>'
                        f'</div>'
                        f'<div style="display:flex;gap:1.5rem;margin-top:.75rem;'
                        f'font-size:.825rem;color:#64748b">'
                        f'  <span>Amount: <strong style="color:#0f172a">'
                        f'  ${t["amount"]:.2f}</strong></span>'
                        f'  <span>MCC: <strong style="color:#0f172a">{t["mcc"]}</strong></span>'
                        f'  <span>City: <strong style="color:#0f172a">{t["city"]}</strong></span>'
                        f'  <span>Channel: <strong style="color:#0f172a">'
                        f'  {t["channel"]}</strong></span>'
                        f'</div>',
                        "margin-bottom:.5rem"
                    ),
                    unsafe_allow_html=True
                )
        else:
            st.success("No HIGH risk transactions found in this batch.")

        st.markdown("---")



# ═══════════════════════════════════════════════════════════════════
#  PAGE: CUSTOMER LIST
# ═══════════════════════════════════════════════════════════════════

def page_customer_list():
    st.markdown(
        section_title("👥", "Customer List", "View and edit customer records"),
        unsafe_allow_html=True,
    )

    # Initialize state for pagination and filtering
    if "cust_page" not in st.session_state:
        st.session_state.cust_page = 1
    if "cust_page_size" not in st.session_state:
        st.session_state.cust_page_size = 100
    if "cust_data" not in st.session_state:
        st.session_state.cust_data = None
    if "cust_total" not in st.session_state:
        st.session_state.cust_total = 0
    if "cust_filter" not in st.session_state:
        st.session_state.cust_filter = ""

    # ── Filter & controls ────────────────────────────────
    col1, col2, col3 = st.columns([2, 1, 1], gap="medium")
    with col1:
        name_filter = st.text_input(
            "Filter by name",
            placeholder="e.g., Smith (optional)",
            key="list_filter_input",
            value=st.session_state.cust_filter
        )
    with col2:
        st.markdown("<div style='margin-top:1.65rem'></div>", unsafe_allow_html=True)
        apply_filter_clicked = st.button("Filter", use_container_width=True)
    with col3:
        st.markdown("<div style='margin-top:1.65rem'></div>", unsafe_allow_html=True)
        reset_filter_clicked = st.button("Clear", use_container_width=True)

    # Handle filter application/reset
    if apply_filter_clicked:
        st.session_state.cust_filter = name_filter
        st.session_state.cust_page = 1  # Reset to page 1 when filtering
        st.session_state.cust_data = None  # Reload with new filter

    if reset_filter_clicked:
        st.session_state.cust_filter = ""
        st.session_state.cust_page = 1  # Reset to page 1
        st.session_state.cust_data = None  # Reload without filter

    # Load data on initial load or when filter changes
    if st.session_state.cust_data is None:
        with st.spinner("Loading customer list…"):
            try:
                raw = run_script(
                    "python/customer_list.py",
                    [str(st.session_state.cust_page), str(st.session_state.cust_page_size), st.session_state.cust_filter]
                )
                rows, total = parse_customer_list(raw)
                st.session_state.cust_data = rows
                st.session_state.cust_total = total
            except (RunnerError, ParseError) as e:
                st.error(str(e))
                st.session_state.cust_data = []
                st.session_state.cust_total = 0
                return

    rows = st.session_state.cust_data
    total = st.session_state.cust_total
    page = st.session_state.cust_page
    page_size = st.session_state.cust_page_size
    num_pages = (total + page_size - 1) // page_size if total > 0 else 1

    if not rows:
        st.warning(f"No customers found. {' (Try clearing your filter)' if st.session_state.cust_filter else ''}")
        return

    # ── Pagination info ─────────────────────────────────
    filter_info = f"Filtering by '{st.session_state.cust_filter}'" if st.session_state.cust_filter else ""
    st.markdown(
        f'<div style="font-size:.8rem;color:#64748b;margin:1.5rem 0 1rem">'
        f'Showing {len(rows)} of {total:,} customers &nbsp;·&nbsp; '
        f'Page {page} of {num_pages}'
        f'{(" · " + filter_info) if filter_info else ""}'
        f'</div>',
        unsafe_allow_html=True
    )

    # ── Editable data table ──────────────────────────────
    # Prepare data for st.data_editor
    edit_data = []
    for row in rows:
        edit_data.append({
            'Customer ID': row['customer_id'],
            'Full Name': row['name'],
            'Email': row['email'],
            'City': row['city'],
            'Street': row['street'],
            'Balance': row['balance'],
            'Monthly Income': row['monthly_income'],
        })

    # Use st.data_editor for inline editing
    edited_df = st.data_editor(
        edit_data,
        use_container_width=True,
        hide_index=True,
        key="customer_table",
        disabled=['Customer ID', 'Balance'],  # Read-only columns
        num_rows="fixed",
    )

    st.markdown("<div style='margin-top:1.25rem'></div>", unsafe_allow_html=True)

    # ── Pagination controls ──────────────────────────────
    col_prev, col_info, col_next = st.columns([1, 2, 1], gap="medium")

    with col_prev:
        if st.button("← Prev", disabled=(page <= 1)):
            st.session_state.cust_page = max(1, page - 1)
            st.session_state.cust_data = None  # Reset to trigger reload
            st.rerun()

    with col_info:
        st.markdown(
            f'<div style="text-align:center;font-size:.85rem;color:#64748b;'
            f'padding:.5rem">Page {page} / {num_pages}</div>',
            unsafe_allow_html=True
        )

    with col_next:
        if st.button("Next →", disabled=(page >= num_pages)):
            st.session_state.cust_page = min(num_pages, page + 1)
            st.session_state.cust_data = None  # Reset to trigger reload
            st.rerun()

    st.markdown("<div style='margin-top:1rem'></div>", unsafe_allow_html=True)

    # ── Save changes button ──────────────────────────────
    save_clicked = st.button("💾 Save Changes", use_container_width=True)

    if save_clicked and edited_df is not None:
        # Compare original vs edited and save changes
        update_count = 0
        error_count = 0

        with st.spinner("Saving changes…"):
            for i, edited_row in enumerate(edited_df):
                original_row = rows[i]

                # Check if anything changed
                changed = (
                    edited_row['Full Name'] != original_row['name'] or
                    edited_row['Email'] != original_row['email'] or
                    edited_row['City'] != original_row['city'] or
                    edited_row['Street'] != original_row['street'] or
                    edited_row['Monthly Income'] != original_row['monthly_income']
                )

                if not changed:
                    continue

                # Call update script
                try:
                    raw = run_script(
                        "python/customer_update.py",
                        [
                            edited_row['Customer ID'],
                            edited_row['Full Name'],
                            edited_row['Email'],
                            edited_row['City'],
                            edited_row['Street'],
                            str(edited_row['Monthly Income']),
                        ]
                    )
                    result = parse_customer_update(raw)
                    if result['success']:
                        update_count += 1
                        st.toast(f"✓ {edited_row['Customer ID']} updated", icon="✓")
                    else:
                        error_count += 1
                        st.toast(f"✗ {edited_row['Customer ID']}: {result['message']}", icon="✗")
                except (RunnerError, ParseError) as e:
                    error_count += 1
                    st.toast(f"✗ {edited_row['Customer ID']}: {str(e)}", icon="✗")

        # Summary
        if update_count > 0:
            st.success(f"✓ {update_count} customer record{'s' if update_count != 1 else ''} updated successfully.")
        if error_count > 0:
            st.warning(f"✗ {error_count} update{'s' if error_count != 1 else ''} failed. Check messages above.")

        # Reload data after save
        if update_count > 0:
            st.session_state.cust_data = None
            st.rerun()


# ═══════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════

def main():
    st.set_page_config(
        page_title="BankCore Analytics",
        page_icon="🏦",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(CSS, unsafe_allow_html=True)

    page = build_sidebar()

    if "Customer 360" in page:
        page_customer_360()
    elif "Loan" in page:
        page_loan_assessment()
    elif "Fraud" in page:
        page_fraud_detection()
    else:
        page_customer_list()


if __name__ == "__main__":
    main()
