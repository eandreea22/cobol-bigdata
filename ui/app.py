"""
Banking Analytics System — Full Redesign
Fintech-grade UI: dark sidebar navigation, card grid layouts, polished components.
"""

import streamlit as st
from runner import run_script, RunnerError
from parse import parse_customer_360, parse_loan_scoring, parse_fraud_detect, ParseError
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
            options=["💳  Customer 360", "📊  Loan Assessment", "⚠️  Fraud Detection"],
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

    with st.form("f_cust"):
        col1, col2 = st.columns([3, 1])
        with col1:
            cid = st.text_input("Customer ID", value="C-00001", placeholder="C-00001")
        with col2:
            st.markdown("<div style='margin-top:1.65rem'></div>", unsafe_allow_html=True)
            go = st.form_submit_button("Look up →", use_container_width=True)

    if not go:
        return

    if not cid.strip():
        st.error("Customer ID is required.")
        return

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

    with st.form("f_loan"):
        col1, col2 = st.columns(2, gap="medium")
        with col1:
            cid    = st.text_input("Customer ID", value="C-00001", placeholder="C-00001")
            amount = st.number_input("Loan Amount ($)", min_value=1000, max_value=500000,
                                     value=10000, step=1000, format="%d")
        with col2:
            term    = st.selectbox("Loan Term", [12, 24, 36, 48, 60, 84, 120],
                                   index=2, format_func=lambda x: f"{x} months")
            purpose = st.selectbox("Purpose", ["HOME", "AUTO", "PERS", "EDUC"])

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
#  PAGE: FRAUD DETECTION
# ═══════════════════════════════════════════════════════════════════

def page_fraud_detection():
    st.markdown(
        section_title("⚠️", "Fraud Detection", "Real-time transaction risk analysis"),
        unsafe_allow_html=True,
    )

    with st.form("f_fraud"):
        col1, col2 = st.columns(2, gap="medium")
        with col1:
            st.markdown("**Customer & Transaction**")
            cid     = st.text_input("Customer ID", value="C-00001", placeholder="C-00001")
            amount  = st.number_input("Amount ($)", min_value=0.01, value=500.00, step=0.01, format="%.2f")
            mcc     = st.text_input("MCC (4-digit code)", value="5411", placeholder="5411", max_chars=4)
        with col2:
            st.markdown("**Location & Channel**")
            location = st.text_input("Location", value="Bucharest", placeholder="City or region")
            channel  = st.selectbox("Channel", ["POS", "ATM", "ONL", "MOB"])

        st.markdown("**Timestamp**")
        col_d, col_t = st.columns(2, gap="medium")
        with col_d:
            txn_date = st.date_input("Date", value=datetime.now())
        with col_t:
            txn_time = st.time_input("Time", value=datetime.now().time())

        go = st.form_submit_button("Analyze Transaction →", use_container_width=True)

    if not go:
        return

    if not cid.strip():
        st.error("Customer ID is required.")
        return
    if len(mcc) != 4 or not mcc.isdigit():
        st.error("MCC must be exactly 4 digits (e.g. 5411).")
        return

    timestamp = datetime.combine(txn_date, txn_time).isoformat()

    with st.spinner("Analyzing transaction…"):
        try:
            raw = run_script(
                "python/fraud_detect.py",
                [cid, str(amount), mcc, location, timestamp, channel],
            )
            r = parse_fraud_detect(raw)
        except (RunnerError, ParseError) as e:
            st.error(str(e))
            return

    risk_level  = r["risk_level"]
    fraud_score = r["fraud_score"]
    rec         = r["recommendation"]
    flags       = r["flags"]

    kind_map = {"LOW": "success", "MEDIUM": "warning", "HIGH": "danger"}
    rec_map  = {"APPROVE": "success", "REVIEW": "warning", "DECLINE": "danger"}
    risk_kind = kind_map.get(risk_level, "neutral")
    rec_kind  = rec_map.get(rec, "neutral")

    # ── Decision banner ──────────────────────────────
    banner_text = {
        "APPROVE": "✓  Transaction Approved — Risk within acceptable range.",
        "REVIEW":  "⚠  Manual Review Required — Elevated risk indicators detected.",
        "DECLINE": "✕  Transaction Declined — High fraud risk.",
    }
    st.markdown(banner(banner_text.get(rec, rec), rec_kind), unsafe_allow_html=True)

    st.markdown("<div style='margin-top:.5rem'></div>", unsafe_allow_html=True)

    # ── Score / risk / recommendation ────────────────
    fs_color = "#10b981" if fraud_score < 30 else "#f59e0b" if fraud_score < 70 else "#f43f5e"

    col1, col2, col3 = st.columns(3, gap="medium")
    with col1:
        st.markdown(big_score_card("Fraud Score", fraud_score, 100, fs_color), unsafe_allow_html=True)
    with col2:
        st.markdown(
            _card(
                f'<div style="font-size:.7rem;font-weight:600;text-transform:uppercase;'
                f'letter-spacing:.08em;color:#64748b;margin-bottom:.75rem">Risk Level</div>'
                f'<div style="margin:.15rem 0">{badge(risk_level, risk_kind)}</div>'
                f'<div style="color:#94a3b8;font-size:.75rem;margin-top:.75rem">'
                f'{len(flags)} indicator{"s" if len(flags) != 1 else ""} flagged</div>'
            ),
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            _card(
                f'<div style="font-size:.7rem;font-weight:600;text-transform:uppercase;'
                f'letter-spacing:.08em;color:#64748b;margin-bottom:.75rem">Recommendation</div>'
                f'<div style="margin:.15rem 0">{badge(rec, rec_kind)}</div>'
                f'<div style="color:#94a3b8;font-size:.75rem;margin-top:.75rem">'
                f'Action: {rec.lower()} this transaction</div>'
            ),
            unsafe_allow_html=True,
        )

    st.markdown("<div style='margin-top:1.25rem'></div>", unsafe_allow_html=True)

    # ── Risk indicators ──────────────────────────────
    st.markdown(
        _card(
            f'<div style="font-size:.7rem;font-weight:600;text-transform:uppercase;'
            f'letter-spacing:.08em;color:#64748b;margin-bottom:.875rem">'
            f'Risk Indicators ({len(flags)} detected)</div>'
            f'<div style="display:flex;flex-wrap:wrap;gap:.25rem">'
            f'{flag_pills(flags)}'
            f'</div>'
        ),
        unsafe_allow_html=True,
    )

    st.markdown("<div style='margin-top:.75rem'></div>", unsafe_allow_html=True)

    # ── Transaction details ───────────────────────────
    st.markdown(
        summary_grid([
            ("Customer",  cid),
            ("Amount",    fmt_usd(amount)),
            ("Channel",   channel),
            ("Location",  location),
            ("MCC",       mcc),
            ("Timestamp", f"{txn_date} {str(txn_time)[:5]}"),
        ]),
        unsafe_allow_html=True,
    )


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
    else:
        page_fraud_detection()


if __name__ == "__main__":
    main()
