"""
Streamlit UI for Hybrid COBOL-Python Banking System.

Exposes three core analytics scripts via interactive web interface:
- Customer 360: View customer profile and transaction history
- Loan Assessment: Check loan eligibility and terms
- Fraud Detection: Assess transaction risk and get recommendation

Enhanced design: Modern fintech aesthetic with refined typography, sophisticated
color system, and professional visual hierarchy.
"""

import streamlit as st
from runner import run_script, RunnerError
from parse import parse_customer_360, parse_loan_scoring, parse_fraud_detect, ParseError
from datetime import datetime


# ============================================================================
# DESIGN SYSTEM & CUSTOM CSS
# ============================================================================

def inject_custom_css():
    """Inject custom CSS for modern fintech aesthetic."""
    custom_css = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');

        /* Color Palette */
        :root {
            --primary: #0f172a;      /* Deep slate-navy */
            --secondary: #1e293b;    /* Slate-700 */
            --accent: #06b6d4;       /* Cyan (fintech primary accent) */
            --success: #10b981;      /* Emerald (approval, low risk) */
            --warning: #f59e0b;      /* Amber (medium risk) */
            --danger: #ef4444;       /* Red (high risk, decline) */
            --bg-light: #f8fafc;     /* Slate-50 */
            --bg-card: #ffffff;      /* White */
            --text-primary: #0f172a; /* Slate-900 */
            --text-secondary: #64748b; /* Slate-500 */
            --border: #e2e8f0;       /* Slate-200 */
            --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
            --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.07);
            --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);
        }

        /* Global Typography */
        body, .stApp {
            font-family: 'Inter', sans-serif;
            color: var(--text-primary);
            background-color: var(--bg-light);
        }

        h1, h2, h3, h4, h5, h6 {
            font-family: 'Syne', sans-serif;
            font-weight: 700;
            letter-spacing: -0.5px;
        }

        h1 {
            font-size: 2.5rem;
            color: var(--primary);
            margin-bottom: 0.5rem;
        }

        h2 {
            font-size: 1.875rem;
            color: var(--primary);
            margin-bottom: 1.5rem;
            margin-top: 2rem;
        }

        h3 {
            font-size: 1.25rem;
            color: var(--secondary);
        }

        /* Streamlit Container Overrides */
        .stApp {
            background-color: var(--bg-light);
        }

        [data-testid="stAppViewContainer"] {
            background-color: var(--bg-light);
        }

        /* Tab Navigation */
        .stTabs [data-baseweb="tab-list"] {
            border-bottom: 2px solid var(--border);
            gap: 2rem;
        }

        .stTabs [data-baseweb="tab"] {
            font-family: 'Syne', sans-serif;
            font-weight: 600;
            font-size: 1.05rem;
            color: var(--text-secondary);
            padding: 1rem 0.5rem;
            border-bottom: 3px solid transparent;
            transition: all 0.3s ease;
        }

        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            color: var(--accent);
            border-bottom-color: var(--accent);
        }

        /* Cards / Sections */
        [data-testid="stVerticalBlock"] > [style*="flex-direction"] {
            background-color: var(--bg-card);
            border-radius: 12px;
            padding: 2rem;
            border: 1px solid var(--border);
            box-shadow: var(--shadow-md);
            margin-bottom: 1.5rem;
        }

        /* Input Fields */
        .stTextInput input, .stNumberInput input, .stSelectbox select {
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-card);
            border: 2px solid var(--border);
            border-radius: 8px;
            padding: 0.75rem 1rem;
            font-size: 1rem;
            color: var(--text-primary);
            transition: all 0.2s ease;
        }

        .stTextInput input:focus, .stNumberInput input:focus, .stSelectbox select:focus {
            border-color: var(--accent);
            box-shadow: 0 0 0 3px rgba(6, 182, 212, 0.1);
            outline: none;
        }

        /* Buttons */
        .stButton > button {
            font-family: 'Syne', sans-serif;
            font-weight: 600;
            background-color: var(--accent);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.75rem 2rem;
            font-size: 1rem;
            transition: all 0.3s ease;
            cursor: pointer;
            box-shadow: var(--shadow-sm);
        }

        .stButton > button:hover {
            background-color: #0891b2;
            box-shadow: var(--shadow-lg);
            transform: translateY(-2px);
        }

        .stButton > button:active {
            transform: translateY(0);
        }

        /* Metrics (Custom Styling) */
        .metric-card {
            background: linear-gradient(135deg, var(--bg-card) 0%, rgba(6, 182, 212, 0.02) 100%);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.5rem;
            text-align: center;
            box-shadow: var(--shadow-sm);
            transition: all 0.3s ease;
        }

        .metric-card:hover {
            box-shadow: var(--shadow-lg);
            border-color: var(--accent);
            transform: translateY(-4px);
        }

        .metric-label {
            font-family: 'Inter', sans-serif;
            font-size: 0.875rem;
            font-weight: 600;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.5rem;
        }

        .metric-value {
            font-family: 'Syne', sans-serif;
            font-size: 2rem;
            font-weight: 800;
            color: var(--primary);
            margin: 0.5rem 0;
        }

        /* Status Badges */
        .status-badge {
            display: inline-block;
            font-family: 'Syne', sans-serif;
            font-weight: 700;
            padding: 0.5rem 1.25rem;
            border-radius: 20px;
            font-size: 0.95rem;
            letter-spacing: 0.05em;
        }

        .badge-success {
            background-color: rgba(16, 185, 129, 0.1);
            color: var(--success);
        }

        .badge-warning {
            background-color: rgba(245, 158, 11, 0.1);
            color: var(--warning);
        }

        .badge-danger {
            background-color: rgba(239, 68, 68, 0.1);
            color: var(--danger);
        }

        /* Alert Messages */
        .stAlert {
            border-radius: 8px;
            border-left: 4px solid;
        }

        .stSuccess {
            border-left-color: var(--success);
        }

        .stWarning {
            border-left-color: var(--warning);
        }

        .stError {
            border-left-color: var(--danger);
        }

        /* Section Divider */
        hr {
            border: none;
            height: 2px;
            background: linear-gradient(to right, transparent, var(--border), transparent);
            margin: 2rem 0;
        }

        /* Footer Text */
        .footer-text {
            color: var(--text-secondary);
            font-size: 0.9rem;
            font-family: 'Inter', sans-serif;
            line-height: 1.6;
        }

        /* Info Boxes */
        .info-box {
            background-color: rgba(6, 182, 212, 0.05);
            border: 1px solid rgba(6, 182, 212, 0.2);
            border-left: 4px solid var(--accent);
            border-radius: 8px;
            padding: 1rem;
            margin: 1rem 0;
        }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)


def format_currency(value):
    """Format value as USD currency."""
    return f"${value:,.2f}"


def format_percentage(value):
    """Format value as percentage."""
    return f"{value:.2f}%"


def get_risk_badge(score):
    """Return HTML badge for risk score."""
    if score < 300:
        return '<span class="status-badge badge-success">🟢 LOW RISK</span>'
    elif score < 600:
        return '<span class="status-badge badge-warning">🟡 MEDIUM RISK</span>'
    else:
        return '<span class="status-badge badge-danger">🔴 HIGH RISK</span>'


def get_approval_badge(eligible):
    """Return HTML badge for loan approval."""
    if eligible:
        return '<span class="status-badge badge-success">✅ APPROVED</span>'
    else:
        return '<span class="status-badge badge-danger">❌ DECLINED</span>'


def get_fraud_badge(risk_level):
    """Return HTML badge for fraud risk level."""
    if risk_level == "LOW":
        return '<span class="status-badge badge-success">🟢 LOW RISK</span>'
    elif risk_level == "MEDIUM":
        return '<span class="status-badge badge-warning">🟡 MEDIUM RISK</span>'
    else:
        return '<span class="status-badge badge-danger">🔴 HIGH RISK</span>'


def tab_customer_360():
    """Tab 1: Customer 360 View — Enhanced design"""
    st.subheader("Customer 360 View")
    st.write("Look up a customer's comprehensive profile, balance, and transaction history.")

    # Input section
    col1, col2, _ = st.columns([2, 1, 1])
    with col1:
        customer_id = st.text_input(
            "Customer ID",
            value="C-00001",
            placeholder="e.g. C-00001",
            key="cust_360_id"
        )
    with col2:
        lookup_btn = st.button("Lookup", key="btn_cust_360", use_container_width=True)

    if lookup_btn:
        if not customer_id.strip():
            st.error("Please enter a customer ID")
            return

        with st.spinner("Looking up customer..."):
            try:
                raw_output = run_script("python/customer_360.py", [customer_id])
                result = parse_customer_360(raw_output)

                # Success message
                st.success("✓ Customer found", icon="✓")

                # Customer Name Section
                st.markdown(f"### {result['name']}")

                # Key Metrics in three columns
                st.markdown("#### Account Overview")
                col1, col2, col3 = st.columns(3, gap="medium")

                with col1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Account Balance</div>
                        <div class="metric-value">{format_currency(result["balance"])}</div>
                    </div>
                    """, unsafe_allow_html=True)

                with col2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Total Transactions</div>
                        <div class="metric-value">{result["txn_count"]}</div>
                    </div>
                    """, unsafe_allow_html=True)

                with col3:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Avg Monthly Spend</div>
                        <div class="metric-value">{format_currency(result["avg_monthly"])}</div>
                    </div>
                    """, unsafe_allow_html=True)

                st.divider()

                # Risk Assessment
                st.markdown("#### Risk Assessment")
                risk_score = result["risk_score"]
                risk_badge = get_risk_badge(risk_score)

                col1, col2 = st.columns([1, 2])
                with col1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Risk Score</div>
                        <div class="metric-value">{risk_score}</div>
                        <div style="font-size: 0.9rem; color: #64748b; margin-top: 0.5rem;">out of 999</div>
                    </div>
                    """, unsafe_allow_html=True)

                with col2:
                    st.markdown(risk_badge, unsafe_allow_html=True)
                    st.markdown(f"**Last Transaction:** `{result['last_txn_date']}`")

                # Info box
                st.markdown(f"""
                <div class="info-box">
                    <strong>Summary:</strong> Customer {customer_id} has {result['txn_count']} transactions
                    with an average monthly spend of {format_currency(result['avg_monthly'])}.
                    Account balance is {format_currency(result['balance'])} with a risk score of {risk_score}/999.
                </div>
                """, unsafe_allow_html=True)

            except RunnerError as e:
                st.error(f"❌ Execution error: {e}")
            except ParseError as e:
                st.error(f"❌ Parse error: {e}")


def tab_loan_assessment():
    """Tab 2: Loan Assessment — Enhanced design"""
    st.subheader("Loan Assessment")
    st.write("Check eligibility and terms for a loan request with detailed credit analysis.")

    # Input section in organized grid
    st.markdown("#### Loan Details")
    col1, col2 = st.columns(2, gap="medium")
    with col1:
        customer_id = st.text_input(
            "Customer ID",
            value="C-00001",
            placeholder="e.g. C-00001",
            key="loan_cust_id"
        )
        amount = st.number_input(
            "Loan Amount ($)",
            min_value=1000,
            max_value=500000,
            value=10000,
            step=1000,
            key="loan_amount",
            format="%d"
        )

    with col2:
        term = st.selectbox(
            "Loan Term (Months)",
            [12, 24, 36, 48, 60, 84, 120],
            index=2,  # Default 36
            key="loan_term"
        )
        purpose = st.selectbox(
            "Loan Purpose",
            ["HOME", "AUTO", "PERS", "EDUC"],
            index=0,
            key="loan_purpose"
        )

    assess_btn = st.button("Assess Loan Eligibility", key="btn_assess_loan", use_container_width=True)

    if assess_btn:
        if not customer_id.strip():
            st.error("Please enter a customer ID")
            return

        with st.spinner("Assessing loan eligibility..."):
            try:
                raw_output = run_script(
                    "python/loan_scoring.py",
                    [customer_id, str(amount), str(term), purpose]
                )
                result = parse_loan_scoring(raw_output)

                st.success("✓ Assessment complete", icon="✓")

                # Eligibility status - prominent display
                st.markdown("#### Loan Decision")
                approval_badge = get_approval_badge(result["eligible"])
                st.markdown(approval_badge, unsafe_allow_html=True)

                st.divider()

                # Credit details
                st.markdown("#### Credit Analysis")
                col1, col2 = st.columns(2, gap="medium")

                with col1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Credit Score</div>
                        <div class="metric-value">{result['credit_score']}</div>
                        <div style="font-size: 0.9rem; color: #64748b; margin-top: 0.5rem;">out of 850</div>
                    </div>
                    """, unsafe_allow_html=True)

                # Conditional details based on eligibility
                if result["eligible"]:
                    with col2:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">Interest Rate</div>
                            <div class="metric-value">{format_percentage(result["int_rate"] * 100)}</div>
                        </div>
                        """, unsafe_allow_html=True)

                    st.divider()
                    st.markdown("#### Loan Terms")
                    col1, col2, col3 = st.columns(3, gap="medium")

                    with col1:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">Requested Amount</div>
                            <div class="metric-value" style="font-size: 1.5rem;">{format_currency(amount)}</div>
                        </div>
                        """, unsafe_allow_html=True)

                    with col2:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">Maximum Approved</div>
                            <div class="metric-value" style="font-size: 1.5rem;">{format_currency(result["max_amount"])}</div>
                        </div>
                        """, unsafe_allow_html=True)

                    with col3:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">Term</div>
                            <div class="metric-value">{term}</div>
                            <div style="font-size: 0.9rem; color: #64748b; margin-top: 0.5rem;">months</div>
                        </div>
                        """, unsafe_allow_html=True)

                    st.markdown(f"""
                    <div class="info-box">
                        <strong>Decision:</strong> Loan of {format_currency(amount)} is approved for customer {customer_id}.
                        Maximum approved amount is {format_currency(result["max_amount"])} at {format_percentage(result["int_rate"] * 100)} APR.
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    # Declined scenario
                    with col2:
                        st.markdown(f"""
                        <div class="metric-card" style="background-color: rgba(239, 68, 68, 0.02);">
                            <div class="metric-label">Decline Reason</div>
                            <div style="color: #ef4444; font-weight: 600; margin-top: 1rem;">{result['reason']}</div>
                        </div>
                        """, unsafe_allow_html=True)

                    st.markdown(f"""
                    <div class="info-box" style="border-left-color: #ef4444;">
                        <strong>Reason for Decline:</strong> {result['reason']}
                    </div>
                    """, unsafe_allow_html=True)

            except RunnerError as e:
                st.error(f"❌ Execution error: {e}")
            except ParseError as e:
                st.error(f"❌ Parse error: {e}")


def tab_fraud_detection():
    """Tab 3: Fraud Detection — Enhanced design"""
    st.subheader("Fraud Detection")
    st.write("Analyze a transaction in real-time for fraud risk and get actionable recommendations.")

    # Transaction details section
    st.markdown("#### Transaction Details")
    col1, col2 = st.columns(2, gap="medium")
    with col1:
        customer_id = st.text_input(
            "Customer ID",
            value="C-00001",
            placeholder="e.g. C-00001",
            key="fraud_cust_id"
        )
        amount = st.number_input(
            "Transaction Amount ($)",
            min_value=0.01,
            value=500.00,
            step=0.01,
            key="fraud_amount",
            format="%.2f"
        )
        mcc = st.text_input(
            "MCC (Merchant Category Code)",
            value="5411",
            placeholder="e.g. 5411",
            key="fraud_mcc",
            max_chars=4
        )

    with col2:
        location = st.text_input(
            "Location",
            value="Bucharest",
            placeholder="e.g. Bucharest",
            key="fraud_location"
        )
        channel = st.selectbox(
            "Transaction Channel",
            ["POS", "ATM", "ONL", "MOB"],
            index=0,
            key="fraud_channel"
        )

    # Timestamp section
    st.markdown("#### Transaction Timestamp")
    col1, col2 = st.columns(2, gap="medium")
    with col1:
        txn_date = st.date_input("Date", value=datetime.now(), key="fraud_date")
    with col2:
        txn_time = st.time_input("Time", value=datetime.now().time(), key="fraud_time")

    # Combine date and time into ISO 8601 format
    timestamp = datetime.combine(txn_date, txn_time).isoformat()

    analyze_btn = st.button("Analyze Transaction", key="btn_analyze_fraud", use_container_width=True)

    if analyze_btn:
        if not customer_id.strip():
            st.error("Please enter a customer ID")
            return
        if len(mcc) != 4 or not mcc.isdigit():
            st.error("MCC must be a 4-digit number")
            return

        with st.spinner("Analyzing transaction..."):
            try:
                raw_output = run_script(
                    "python/fraud_detect.py",
                    [customer_id, str(amount), mcc, location, timestamp, channel]
                )
                result = parse_fraud_detect(raw_output)

                st.success("✓ Analysis complete", icon="✓")

                # Risk assessment
                st.markdown("#### Fraud Risk Assessment")
                risk_level = result["risk_level"]
                fraud_badge = get_fraud_badge(risk_level)

                col1, col2 = st.columns([1, 2], gap="medium")
                with col1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Fraud Score</div>
                        <div class="metric-value">{result["fraud_score"]}</div>
                        <div style="font-size: 0.9rem; color: #64748b; margin-top: 0.5rem;">out of 100</div>
                    </div>
                    """, unsafe_allow_html=True)

                with col2:
                    st.markdown(fraud_badge, unsafe_allow_html=True)

                # Fraud score progress bar with custom styling
                fraud_score = result["fraud_score"]
                progress_color = "#10b981" if fraud_score < 30 else "#f59e0b" if fraud_score < 70 else "#ef4444"
                st.markdown(f"""
                <div style="margin: 1rem 0;">
                    <div style="height: 8px; background-color: #e2e8f0; border-radius: 4px; overflow: hidden;">
                        <div style="height: 100%; background: linear-gradient(90deg, {progress_color}, {progress_color}); width: {min(fraud_score, 100)}%;"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                st.divider()

                # Recommendation
                st.markdown("#### Recommendation")
                rec = result["recommendation"]
                if rec == "APPROVE":
                    rec_badge = '<span class="status-badge badge-success">✅ APPROVE</span>'
                elif rec == "REVIEW":
                    rec_badge = '<span class="status-badge badge-warning">⚠️ REVIEW</span>'
                else:
                    rec_badge = '<span class="status-badge badge-danger">❌ DECLINE</span>'

                st.markdown(rec_badge, unsafe_allow_html=True)
                st.markdown(f"**Action:** Transaction should be {rec.lower()}")

                st.divider()

                # Detected flags
                st.markdown("#### Risk Indicators")
                if result["flags"]:
                    st.write(f"**{len(result['flags'])} risk flag(s) detected:**")
                    for flag in result["flags"]:
                        st.markdown(f"🚩 **{flag}**")
                else:
                    st.markdown("""
                    <div class="info-box" style="border-left-color: #10b981;">
                        ✓ No fraud flags detected — transaction appears legitimate
                    </div>
                    """, unsafe_allow_html=True)

                # Summary
                st.markdown("#### Transaction Summary")
                st.markdown(f"""
                <div class="info-box">
                    <strong>Analysis Summary:</strong><br>
                    Customer {customer_id} initiated a {format_currency(amount)} transaction at {location}
                    via {channel} on {txn_date} at {txn_time}. Fraud analysis returned a score of {fraud_score}/100
                    ({risk_level} risk) with recommendation to {rec.lower()}.
                </div>
                """, unsafe_allow_html=True)

            except RunnerError as e:
                st.error(f"❌ Execution error: {e}")
            except ParseError as e:
                st.error(f"❌ Parse error: {e}")


def main():
    """Main Streamlit app with enhanced design."""
    st.set_page_config(
        page_title="Banking System",
        page_icon="🏦",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    # Inject custom CSS for refined fintech aesthetic
    inject_custom_css()

    # Header
    st.markdown("""
    <div style="margin-bottom: 3rem;">
        <h1 style="margin: 0; font-size: 2.5rem;">🏦 Banking Analytics System</h1>
        <p style="color: #64748b; font-size: 1.1rem; margin-top: 0.5rem;">
            Hybrid COBOL-Python Analytics Platform
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Three tabs with enhanced styling
    tab1, tab2, tab3 = st.tabs(["💳 Customer 360", "📊 Loan Assessment", "⚠️ Fraud Detection"])

    with tab1:
        tab_customer_360()

    with tab2:
        tab_loan_assessment()

    with tab3:
        tab_fraud_detection()

    # Footer with system information
    st.markdown("---")
    st.markdown(f"""
    <div class="footer-text">
        <strong>About This System</strong><br>
        This is a Streamlit interface for the hybrid COBOL-Python banking analytics system.
        Each analysis executes Python scripts that interface with Parquet data sources in real time.
        Response records use fixed-width COBOL-compatible formatting for maximum compatibility.
        <br><br>
        <em>Built with modern fintech design principles — streamlined, professional, and intuitive.</em>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
