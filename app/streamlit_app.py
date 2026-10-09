"""
Streamlit Dashboard
===================
Interactive frontend for the Motor Insurance Analytics project.
"""

import os
import sys

import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_loader import load_all_data
from src.data_cleaner import clean_data
from src import insurance_analysis as ia
from src import visualization as viz
from src import insights as ins

# --------------------------------------------------------------
# Page configuration
# --------------------------------------------------------------
st.set_page_config(
    page_title="Motor Insurance Analytics",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded",
)


# --------------------------------------------------------------
# Data loading (cached)
# --------------------------------------------------------------
@st.cache_data(show_spinner=True)
def load_dashboard_data():
    """Load and clean all data for the dashboard."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raw_dir = os.path.join(base_dir, "data", "raw")
    cleaned_dir = os.path.join(base_dir, "data", "cleaned")

    # Prefer cleaned data if available
    cleaned_files = {
        "customers": os.path.join(cleaned_dir, "customers_cleaned.csv"),
        "policies": os.path.join(cleaned_dir, "policies_cleaned.csv"),
        "vehicles": os.path.join(cleaned_dir, "vehicles_cleaned.csv"),
        "claims": os.path.join(cleaned_dir, "claims_cleaned.csv"),
        "payments": os.path.join(cleaned_dir, "payments_cleaned.csv"),
    }

    if all(os.path.isfile(p) for p in cleaned_files.values()):
        data = {k: pd.read_csv(v) for k, v in cleaned_files.items()}
        # Reparse dates
        for tbl, cols in {
            "customers": ["date_of_birth"],
            "policies": ["policy_start_date", "policy_end_date"],
            "claims": ["claim_date", "accident_date", "approval_date", "settlement_date"],
            "payments": ["payment_date"],
        }.items():
            for c in cols:
                if c in data[tbl].columns:
                    data[tbl][c] = pd.to_datetime(data[tbl][c], errors="coerce")
    else:
        raw = load_all_data(raw_dir)
        data = clean_data(raw)

    return data


# --------------------------------------------------------------
# Sidebar filters
# --------------------------------------------------------------
def show_sidebar_filters(data):
    """Render sidebar filters and return the filtered data dict."""
    st.sidebar.header("🔎 Filters")

    policies = data["policies"]
    claims = data["claims"]
    vehicles = data["vehicles"]
    customers = data["customers"]

    # Policy type
    policy_types = ["All"] + sorted(policies["policy_type"].dropna().unique().tolist())
    sel_policy_type = st.sidebar.selectbox("Policy Type", policy_types)

    # Policy status
    policy_statuses = ["All"] + sorted(policies["policy_status"].dropna().unique().tolist())
    sel_policy_status = st.sidebar.selectbox("Policy Status", policy_statuses)

    # Claim status
    claim_statuses = ["All"] + sorted(claims["claim_status"].dropna().unique().tolist())
    sel_claim_status = st.sidebar.selectbox("Claim Status", claim_statuses)

    # Claim type
    claim_types = ["All"] + sorted(claims["claim_type"].dropna().unique().tolist())
    sel_claim_type = st.sidebar.selectbox("Claim Type", claim_types)

    # Vehicle type
    vehicle_types = ["All"] + sorted(vehicles["vehicle_type"].dropna().unique().tolist())
    sel_vehicle_type = st.sidebar.selectbox("Vehicle Type", vehicle_types)

    # Vehicle make
    vehicle_makes = ["All"] + sorted(vehicles["vehicle_make"].dropna().unique().tolist())
    sel_vehicle_make = st.sidebar.selectbox("Vehicle Make", vehicle_makes)

    # State
    states = ["All"] + sorted(customers["state"].dropna().unique().tolist())
    sel_state = st.sidebar.selectbox("State / City", states)

    # Damage severity
    severities = ["All"] + sorted(claims["damage_severity"].dropna().unique().tolist())
    sel_severity = st.sidebar.selectbox("Damage Severity", severities)

    # Apply filters
    filtered = {k: v.copy() for k, v in data.items()}

    if sel_policy_type != "All":
        filtered["policies"] = filtered["policies"][filtered["policies"]["policy_type"] == sel_policy_type]
    if sel_policy_status != "All":
        filtered["policies"] = filtered["policies"][filtered["policies"]["policy_status"] == sel_policy_status]
    if sel_claim_status != "All":
        filtered["claims"] = filtered["claims"][filtered["claims"]["claim_status"] == sel_claim_status]
    if sel_claim_type != "All":
        filtered["claims"] = filtered["claims"][filtered["claims"]["claim_type"] == sel_claim_type]
    if sel_vehicle_type != "All":
        filtered["vehicles"] = filtered["vehicles"][filtered["vehicles"]["vehicle_type"] == sel_vehicle_type]
    if sel_vehicle_make != "All":
        filtered["vehicles"] = filtered["vehicles"][filtered["vehicles"]["vehicle_make"] == sel_vehicle_make]
    if sel_state != "All":
        filtered["customers"] = filtered["customers"][filtered["customers"]["state"] == sel_state]
    if sel_severity != "All":
        filtered["claims"] = filtered["claims"][filtered["claims"]["damage_severity"] == sel_severity]

    return filtered


# --------------------------------------------------------------
# Pages
# --------------------------------------------------------------
def show_overview(data):
    """Executive overview page."""
    st.header("📊 Executive Overview")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Policies", ia.calculate_total_policies(data))
        st.metric("Active Policies", ia.calculate_active_policies(data))
    with col2:
        st.metric("Total Premium", f"₹ {ia.calculate_total_premium(data):,.0f}")
        st.metric("Total Claims", ia.calculate_total_claims(data))
    with col3:
        st.metric("Total Claim Amount", f"₹ {ia.calculate_total_claim_amount(data):,.0f}")
        st.metric("Approval Rate", f"{ia.calculate_claim_approval_rate(data):.1f}%")
    with col4:
        st.metric("Avg Settlement Days", f"{ia.calculate_average_claim_settlement_days(data):.1f}")
        st.metric("Claim-to-Premium", f"{ia.calculate_claim_to_premium_ratio(data):.2f}")

    st.markdown("---")
    st.subheader("Policy Status")
    fig = viz.plot_policy_status(data)
    st.pyplot(fig)
    plt.close(fig)


def show_policy_analysis(data):
    """Policy analysis page."""
    st.header("📄 Policy Analysis")
    c1, c2 = st.columns(2)
    with c1:
        fig = viz.plot_policy_type_distribution(data)
        st.pyplot(fig)
        plt.close(fig)
    with c2:
        fig = viz.plot_premium_by_policy_type(data)
        st.pyplot(fig)
        plt.close(fig)

    fig = viz.plot_monthly_premium_trend(data)
    st.pyplot(fig)
    plt.close(fig)

    st.subheader("Policy Type Summary")
    st.dataframe(ia.analyze_policy_type(data), use_container_width=True)


def show_claim_analysis(data):
    """Claim analysis page."""
    st.header("📋 Claims Analysis")
    c1, c2 = st.columns(2)
    with c1:
        fig = viz.plot_claim_status(data)
        st.pyplot(fig)
        plt.close(fig)
    with c2:
        fig = viz.plot_claim_type_distribution(data)
        st.pyplot(fig)
        plt.close(fig)

    c3, c4 = st.columns(2)
    with c3:
        fig = viz.plot_claim_amount_distribution(data)
        st.pyplot(fig)
        plt.close(fig)
    with c4:
        fig = viz.plot_damage_severity_distribution(data)
        st.pyplot(fig)
        plt.close(fig)

    st.subheader("Claim Type Summary")
    st.dataframe(ia.analyze_claim_type(data), use_container_width=True)

    st.subheader("Claim Status Summary")
    st.dataframe(ia.analyze_claim_status(data), use_container_width=True)


def show_customer_analysis(data):
    """Customer analysis page."""
    st.header("👥 Customer Analysis")
    st.subheader("Top Customers by Claim Amount")
    st.dataframe(ia.analyze_customer_claims(data).head(20), use_container_width=True)

    st.subheader("Top Customers by Premium")
    st.dataframe(ia.analyze_customer_premium(data).head(20), use_container_width=True)

    fig = viz.plot_customer_age_vs_claim_amount(data)
    st.pyplot(fig)
    plt.close(fig)


def show_vehicle_analysis(data):
    """Vehicle analysis page."""
    st.header("🚗 Vehicle Analysis")
    c1, c2 = st.columns(2)
    with c1:
        fig = viz.plot_claim_amount_by_vehicle_type(data)
        st.pyplot(fig)
        plt.close(fig)
    with c2:
        fig = viz.plot_vehicle_type_claim_performance(data)
        st.pyplot(fig)
        plt.close(fig)

    fig = viz.plot_vehicle_age_vs_claim_amount(data)
    st.pyplot(fig)
    plt.close(fig)

    st.subheader("Vehicle Risk Patterns")
    st.dataframe(ia.analyze_vehicle_risk_patterns(data), use_container_width=True)


def show_premium_analysis(data):
    """Premium & risk page."""
    st.header("💰 Premium & Risk")
    fig = viz.plot_claim_to_premium_by_policy_type(data)
    st.pyplot(fig)
    plt.close(fig)

    st.subheader("Vehicle Claim Aggregates")
    st.dataframe(ia.analyze_vehicle_claims(data), use_container_width=True)


def show_insights(data):
    """Insights & recommendations page."""
    st.header("💡 Insights & Recommendations")

    st.subheader("Portfolio Insights")
    for item in ins.generate_portfolio_insights(data):
        st.markdown(f"**PATTERN:** {item['pattern']}")
        st.markdown(f"- **EVIDENCE:** {item['evidence']}")
        st.markdown(f"- **BUSINESS MEANING:** {item['business_meaning']}")
        st.markdown(f"- **RECOMMENDATION:** {item['recommendation']}")
        st.markdown("---")

    st.subheader("Claim Insights")
    for item in ins.generate_claim_insights(data):
        st.markdown(f"**PATTERN:** {item['pattern']}")
        st.markdown(f"- **EVIDENCE:** {item['evidence']}")
        st.markdown(f"- **BUSINESS MEANING:** {item['business_meaning']}")
        st.markdown(f"- **RECOMMENDATION:** {item['recommendation']}")
        st.markdown("---")

    st.subheader("Premium Insights")
    for item in ins.generate_premium_insights(data):
        st.markdown(f"**PATTERN:** {item['pattern']}")
        st.markdown(f"- **EVIDENCE:** {item['evidence']}")
        st.markdown(f"- **BUSINESS MEANING:** {item['business_meaning']}")
        st.markdown(f"- **RECOMMENDATION:** {item['recommendation']}")
        st.markdown("---")

    st.subheader("Vehicle Insights")
    for item in ins.generate_vehicle_insights(data):
        st.markdown(f"**PATTERN:** {item['pattern']}")
        st.markdown(f"- **EVIDENCE:** {item['evidence']}")
        st.markdown(f"- **BUSINESS MEANING:** {item['business_meaning']}")
        st.markdown(f"- **RECOMMENDATION:** {item['recommendation']}")
        st.markdown("---")

    st.subheader("Risk Patterns")
    for item in ins.generate_risk_patterns(data):
        st.markdown(f"**PATTERN:** {item['pattern']}")
        st.markdown(f"- **EVIDENCE:** {item['evidence']}")
        st.markdown(f"- **BUSINESS MEANING:** {item['business_meaning']}")
        st.markdown(f"- **RECOMMENDATION:** {item['recommendation']}")
        st.markdown("---")

    st.subheader("Business Recommendations")
    for rec in ins.generate_business_recommendations(data):
        st.markdown(f"- {rec}")


# --------------------------------------------------------------
# Main
# --------------------------------------------------------------
def main():
    """Streamlit app entry point."""
    st.title("🚗 Motor Insurance Analytics Dashboard")

    data = load_dashboard_data()
    filtered = show_sidebar_filters(data)

    page = st.sidebar.radio(
        "Navigate",
        [
            "Executive Overview",
            "Policy Analysis",
            "Claims Analysis",
            "Customer Analysis",
            "Vehicle Analysis",
            "Premium & Risk",
            "Insights & Recommendations",
        ],
    )

    if page == "Executive Overview":
        show_overview(filtered)
    elif page == "Policy Analysis":
        show_policy_analysis(filtered)
    elif page == "Claims Analysis":
        show_claim_analysis(filtered)
    elif page == "Customer Analysis":
        show_customer_analysis(filtered)
    elif page == "Vehicle Analysis":
        show_vehicle_analysis(filtered)
    elif page == "Premium & Risk":
        show_premium_analysis(filtered)
    elif page == "Insights & Recommendations":
        show_insights(filtered)


if __name__ == "__main__":
    main()
    