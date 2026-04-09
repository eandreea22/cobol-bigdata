"""
Streamlit UI for Hybrid COBOL-Python Banking System.

Exposes three core analytics scripts via interactive web interface:
- Customer 360: View customer profile and transaction history
- Loan Assessment: Check loan eligibility and terms
- Fraud Detection: Assess transaction risk and get recommendation
"""

import streamlit as st
from runner import run_script, RunnerError
from parse import parse_customer_360, parse_loan_scoring, parse_fraud_detect, ParseError
from datetime import datetime


def format_currency(value):
    """Format value as USD currency."""
    return f"${value:,.2f}"


def format_percentage(value):
    """Format value as percentage."""
    return f"{value:.2f}%"


def risk_color(risk_level):
    """Return color for risk level badge."""
    if risk_level == "LOW":
        return "#00ff00"  # Green
    elif risk_level == "MEDIUM":
        return "#ffaa00"  # Orange
    else:  # HIGH
        return "#ff0000"  # Red


def score_color(score, score_type="risk"):
    """Return color based on score type and value."""
    if score_type == "credit":
        if score < 580:
            return "#ff0000"  # Red
        elif score < 670:
            return "#ffaa00"  # Orange
        else:
            return "#00ff00"  # Green
    elif score_type == "fraud":
        if score < 30:
            return "#00ff00"  # Green
        elif score < 70:
            return "#ffaa00"  # Orange
        else:
            return "#ff0000"  # Red


def tab_customer_360():
    """Tab 1: Customer 360 View"""
    st.header("Customer 360 View")
    st.write("Look up a customer's profile, balance, and transaction history.")

    col1, col2 = st.columns([3, 1])
    with col1:
        customer_id = st.text_input(
            "Customer ID",
            value="C-00001",
            placeholder="e.g. C-00001",
            key="cust_360_id"
        )
    with col2:
        lookup_btn = st.button("Lookup", key="btn_cust_360")

    if lookup_btn:
        if not customer_id.strip():
            st.error("Please enter a customer ID")
            return

        with st.spinner("Looking up customer..."):
            try:
                raw_output = run_script("python/customer_360.py", [customer_id])
                result = parse_customer_360(raw_output)

                # Display results in a nice layout
                st.success("Customer found!")

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Account Balance", format_currency(result["balance"]))
                with col2:
                    st.metric("Transactions", result["txn_count"])
                with col3:
                    st.metric("Avg Monthly Spend", format_currency(result["avg_monthly"]))

                # Risk score with color coding
                risk_score = result["risk_score"]
                if risk_score < 300:
                    risk_badge = "🟢 LOW RISK"
                elif risk_score < 600:
                    risk_badge = "🟡 MEDIUM RISK"
                else:
                    risk_badge = "🔴 HIGH RISK"

                st.markdown(f"**Risk Score:** {risk_score}/999 — {risk_badge}")
                st.markdown(f"**Last Transaction:** {result['last_txn_date']}")
                st.markdown(f"**Name:** {result['name']}")

            except RunnerError as e:
                st.error(f"Execution error: {e}")
            except ParseError as e:
                st.error(f"Parse error: {e}")


def tab_loan_assessment():
    """Tab 2: Loan Assessment"""
    st.header("Loan Assessment")
    st.write("Check eligibility and terms for a loan request.")

    col1, col2 = st.columns(2)
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
            key="loan_amount"
        )

    with col2:
        term = st.selectbox(
            "Term (Months)",
            [12, 24, 36, 48, 60, 84, 120],
            index=2,  # Default 36
            key="loan_term"
        )
        purpose = st.selectbox(
            "Loan Purpose",
            ["HOME", "AUTO", "PERS", "EDUC"],
            key="loan_purpose"
        )

    assess_btn = st.button("Assess Loan", key="btn_assess_loan")

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

                # Credit score
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Credit Score", f"{result['credit_score']}/850")

                # Eligibility
                with col2:
                    if result["eligible"]:
                        st.markdown("#### ✅ **APPROVED**")
                    else:
                        st.markdown("#### ❌ **DECLINED**")

                # Additional details
                if result["eligible"]:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Interest Rate", format_percentage(result["int_rate"] * 100))
                    with col2:
                        st.metric("Max Amount", format_currency(result["max_amount"]))
                else:
                    st.warning(f"**Reason:** {result['reason']}")

            except RunnerError as e:
                st.error(f"Execution error: {e}")
            except ParseError as e:
                st.error(f"Parse error: {e}")


def tab_fraud_detection():
    """Tab 3: Fraud Detection"""
    st.header("Fraud Detection")
    st.write("Analyze a transaction for fraud risk.")

    col1, col2 = st.columns(2)
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
            key="fraud_amount"
        )
        mcc = st.text_input(
            "MCC (Merchant Category Code)",
            value="5411",
            placeholder="e.g. 5411",
            key="fraud_mcc"
        )

    with col2:
        location = st.text_input(
            "Location",
            value="Bucharest",
            placeholder="e.g. Bucharest",
            key="fraud_location"
        )
        channel = st.selectbox(
            "Channel",
            ["POS", "ATM", "ONL", "MOB"],
            key="fraud_channel"
        )

    # Timestamp (date + time)
    col1, col2 = st.columns(2)
    with col1:
        txn_date = st.date_input("Date", value=datetime.now(), key="fraud_date")
    with col2:
        txn_time = st.time_input("Time", value=datetime.now().time(), key="fraud_time")

    # Combine date and time into ISO 8601 format
    timestamp = datetime.combine(txn_date, txn_time).isoformat()

    analyze_btn = st.button("Analyze Transaction", key="btn_analyze_fraud")

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

                # Risk level with color
                risk_level = result["risk_level"]
                if risk_level == "LOW":
                    st.success(f"### Risk Level: {risk_level} 🟢")
                elif risk_level == "MEDIUM":
                    st.warning(f"### Risk Level: {risk_level} 🟡")
                else:
                    st.error(f"### Risk Level: {risk_level} 🔴")

                # Fraud score with progress bar
                fraud_score = result["fraud_score"]
                st.metric("Fraud Score", f"{fraud_score}/100")
                st.progress(min(fraud_score / 100.0, 1.0))

                # Recommendation
                rec = result["recommendation"]
                if rec == "APPROVE":
                    st.info(f"**Recommendation:** {rec} ✅")
                elif rec == "REVIEW":
                    st.warning(f"**Recommendation:** {rec} ⚠️")
                else:
                    st.error(f"**Recommendation:** {rec} ❌")

                # Detected flags
                if result["flags"]:
                    st.write("**Detected Flags:**")
                    cols = st.columns(len(result["flags"]))
                    for i, flag in enumerate(result["flags"]):
                        with cols[i]:
                            st.write(f"🚩 {flag}")
                else:
                    st.info("No fraud flags detected")

            except RunnerError as e:
                st.error(f"Execution error: {e}")
            except ParseError as e:
                st.error(f"Parse error: {e}")


def main():
    """Main Streamlit app."""
    st.set_page_config(
        page_title="Banking System UI",
        page_icon="🏦",
        layout="wide"
    )

    st.title("🏦 Hybrid COBOL-Python Banking System")
    st.markdown("---")

    # Three tabs
    tab1, tab2, tab3 = st.tabs(["Customer 360", "Loan Assessment", "Fraud Detection"])

    with tab1:
        tab_customer_360()

    with tab2:
        tab_loan_assessment()

    with tab3:
        tab_fraud_detection()

    # Footer
    st.markdown("---")
    st.markdown(
        """
        **About this UI:**
        This is a Streamlit interface for the hybrid COBOL-Python banking system.
        Each tab calls a Python analytics script via subprocess and parses the fixed-width response record.
        All data is queried from Parquet files in real time.
        """
    )


if __name__ == "__main__":
    main()
