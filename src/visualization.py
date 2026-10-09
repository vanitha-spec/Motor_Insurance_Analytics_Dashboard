"""
Visualization Module
====================
Standard chart generation functions for the motor insurance dashboard.

All functions are filter-safe:
- They never assume columns exist on the input DataFrames.
- They return a placeholder figure when there is not enough data
  (e.g. after aggressive sidebar filtering) instead of raising.
"""

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for server use
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd

from src.logger import setup_logger

logger = setup_logger(__name__)

sns.set_style("whitegrid")
plt.rcParams["figure.figsize"] = (10, 6)


# ======================================================================
# Internal helpers
# ======================================================================
def _placeholder(message: str):
    """Return a figure with a centered placeholder message."""
    fig, ax = plt.subplots()
    ax.text(0.5, 0.5, message, ha="center", va="center", fontsize=12, wrap=True)
    ax.axis("off")
    fig.tight_layout()
    return fig


def _safe_merge_claims_policies(data):
    """
    Inner-merge claims with policies on policy_id.

    Returns an empty DataFrame if required columns are missing.
    """
    claims = data.get("claims", pd.DataFrame())
    policies = data.get("policies", pd.DataFrame())

    needed_claims = {"policy_id", "claim_amount"}
    needed_policies = {"policy_id", "policy_type", "premium_amount"}

    if not needed_claims.issubset(claims.columns) or \
       not needed_policies.issubset(policies.columns):
        return pd.DataFrame()

    return (
        claims[["policy_id", "claim_amount"]]
        .merge(
            policies[["policy_id", "policy_type", "premium_amount"]],
            on="policy_id",
            how="inner",
        )
    )


def _safe_merge_claims_vehicles(data):
    """
    Inner-merge claims -> policies -> vehicles.

    Returns an empty DataFrame if required columns are missing.
    """
    claims = data.get("claims", pd.DataFrame())
    policies = data.get("policies", pd.DataFrame())
    vehicles = data.get("vehicles", pd.DataFrame())

    needed_claims = {"claim_id", "policy_id", "claim_amount"}
    needed_policies = {"policy_id", "vehicle_id"}
    needed_vehicles = {"vehicle_id", "vehicle_type"}

    if not needed_claims.issubset(claims.columns) or \
       not needed_policies.issubset(policies.columns) or \
       not needed_vehicles.issubset(vehicles.columns):
        return pd.DataFrame()

    return (
        claims[["claim_id", "policy_id", "claim_amount"]]
        .merge(policies[["policy_id", "vehicle_id"]], on="policy_id", how="inner")
        .merge(vehicles[["vehicle_id", "vehicle_type"]], on="vehicle_id", how="inner")
    )


def _safe_merge_claims_customers(data):
    """Inner-merge claims with customers on customer_id."""
    claims = data.get("claims", pd.DataFrame())
    customers = data.get("customers", pd.DataFrame())

    needed_claims = {"claim_id", "customer_id", "claim_amount"}
    needed_customers = {"customer_id", "customer_age"}

    if not needed_claims.issubset(claims.columns) or \
       not needed_customers.issubset(customers.columns):
        return pd.DataFrame()

    return (
        claims[["claim_id", "customer_id", "claim_amount"]]
        .merge(customers[["customer_id", "customer_age"]], on="customer_id", how="inner")
    )


def _safe_merge_claims_customers_state(data):
    """Inner-merge claims with customers to get the state column."""
    claims = data.get("claims", pd.DataFrame())
    customers = data.get("customers", pd.DataFrame())

    needed_claims = {"claim_id", "customer_id", "claim_amount"}
    needed_customers = {"customer_id", "state"}

    if not needed_claims.issubset(claims.columns) or \
       not needed_customers.issubset(customers.columns):
        return pd.DataFrame()

    return (
        claims[["claim_id", "customer_id", "claim_amount"]]
        .merge(customers[["customer_id", "state"]], on="customer_id", how="inner")
    )


def _safe_merge_claims_vehicle_age(data):
    """Inner-merge claims with vehicles (via policies) to get vehicle_age."""
    claims = data.get("claims", pd.DataFrame())
    policies = data.get("policies", pd.DataFrame())
    vehicles = data.get("vehicles", pd.DataFrame())

    needed_claims = {"claim_id", "policy_id", "claim_amount"}
    needed_policies = {"policy_id", "vehicle_id"}
    needed_vehicles = {"vehicle_id", "vehicle_age"}

    if not needed_claims.issubset(claims.columns) or \
       not needed_policies.issubset(policies.columns) or \
       not needed_vehicles.issubset(vehicles.columns):
        return pd.DataFrame()

    return (
        claims[["claim_id", "policy_id", "claim_amount"]]
        .merge(policies[["policy_id", "vehicle_id"]], on="policy_id", how="inner")
        .merge(vehicles[["vehicle_id", "vehicle_age"]], on="vehicle_id", how="inner")
    )


# ======================================================================
# Policy visualizations
# ======================================================================
def plot_policy_status(data):
    """Plot policy status distribution."""
    df = data.get("policies", pd.DataFrame())
    if df.empty or "policy_status" not in df.columns:
        return _placeholder("No policy status data")

    counts = df["policy_status"].value_counts()
    fig, ax = plt.subplots()
    sns.barplot(x=counts.index, y=counts.values, ax=ax, palette="viridis")
    ax.set_title("Policy Status Distribution")
    ax.set_xlabel("Policy Status")
    ax.set_ylabel("Count")
    fig.tight_layout()
    return fig


def plot_policy_type_distribution(data):
    """Plot policy type distribution."""
    df = data.get("policies", pd.DataFrame())
    if df.empty or "policy_type" not in df.columns:
        return _placeholder("No policy type data")

    counts = df["policy_type"].value_counts()
    fig, ax = plt.subplots()
    sns.barplot(x=counts.index, y=counts.values, ax=ax, palette="magma")
    ax.set_title("Policy Type Distribution")
    ax.set_xlabel("Policy Type")
    ax.set_ylabel("Count")
    fig.tight_layout()
    return fig


def plot_premium_by_policy_type(data):
    """Plot total premium by policy type."""
    df = data.get("policies", pd.DataFrame())
    if df.empty or "policy_type" not in df.columns or "premium_amount" not in df.columns:
        return _placeholder("No premium / policy type data")

    grouped = (
        df.groupby("policy_type")["premium_amount"]
        .sum()
        .sort_values(ascending=False)
    )
    if grouped.empty:
        return _placeholder("No premium data after grouping")

    fig, ax = plt.subplots()
    sns.barplot(x=grouped.index, y=grouped.values, ax=ax, palette="Blues_d")
    ax.set_title("Total Premium by Policy Type")
    ax.set_xlabel("Policy Type")
    ax.set_ylabel("Total Premium")
    fig.tight_layout()
    return fig


def plot_monthly_premium_trend(data):
    """Plot monthly premium collection trend."""
    df = data.get("policies", pd.DataFrame())
    if df.empty or "policy_start_date" not in df.columns or "premium_amount" not in df.columns:
        return _placeholder("No monthly premium data")

    df = df.copy()
    df["policy_start_date"] = pd.to_datetime(df["policy_start_date"], errors="coerce")
    df = df.dropna(subset=["policy_start_date"])
    if df.empty:
        return _placeholder("No valid policy start dates")

    df["start_month"] = df["policy_start_date"].dt.to_period("M").astype(str)
    grouped = df.groupby("start_month")["premium_amount"].sum().sort_index()

    fig, ax = plt.subplots()
    ax.plot(grouped.index, grouped.values, marker="o", color="green")
    ax.set_title("Monthly Premium Trend")
    ax.set_xlabel("Month")
    ax.set_ylabel("Total Premium")
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    return fig


# ======================================================================
# Claim visualizations
# ======================================================================
def plot_claim_status(data):
    """Plot claim status distribution."""
    df = data.get("claims", pd.DataFrame())
    if df.empty or "claim_status" not in df.columns:
        return _placeholder("No claim status data")

    counts = df["claim_status"].value_counts()
    fig, ax = plt.subplots()
    sns.barplot(x=counts.index, y=counts.values, ax=ax, palette="coolwarm")
    ax.set_title("Claim Status Distribution")
    ax.set_xlabel("Claim Status")
    ax.set_ylabel("Count")
    fig.tight_layout()
    return fig


def plot_claim_type_distribution(data):
    """Plot claim type distribution."""
    df = data.get("claims", pd.DataFrame())
    if df.empty or "claim_type" not in df.columns:
        return _placeholder("No claim type data")

    counts = df["claim_type"].value_counts()
    fig, ax = plt.subplots()
    sns.barplot(x=counts.index, y=counts.values, ax=ax, palette="Set2")
    ax.set_title("Claim Type Distribution")
    ax.set_xlabel("Claim Type")
    ax.set_ylabel("Count")
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
    fig.tight_layout()
    return fig


def plot_claim_amount_distribution(data):
    """Plot histogram of claim amounts."""
    df = data.get("claims", pd.DataFrame())
    if df.empty or "claim_amount" not in df.columns:
        return _placeholder("No claim amount data")

    series = df["claim_amount"].dropna()
    if series.empty:
        return _placeholder("No valid claim amounts")

    fig, ax = plt.subplots()
    sns.histplot(series, bins=40, kde=True, ax=ax, color="teal")
    ax.set_title("Claim Amount Distribution")
    ax.set_xlabel("Claim Amount")
    ax.set_ylabel("Frequency")
    fig.tight_layout()
    return fig


def plot_damage_severity_distribution(data):
    """Plot damage severity distribution."""
    df = data.get("claims", pd.DataFrame())
    if df.empty or "damage_severity" not in df.columns:
        return _placeholder("No damage severity data")

    counts = df["damage_severity"].value_counts()
    fig, ax = plt.subplots()
    sns.barplot(x=counts.index, y=counts.values, ax=ax, palette="YlOrRd")
    ax.set_title("Damage Severity Distribution")
    ax.set_xlabel("Damage Severity")
    ax.set_ylabel("Count")
    fig.tight_layout()
    return fig


def plot_monthly_claims(data):
    """Plot monthly claim counts."""
    df = data.get("claims", pd.DataFrame())
    if df.empty or "claim_date" not in df.columns or "claim_id" not in df.columns:
        return _placeholder("No monthly claim data")

    df = df.copy()
    df["claim_date"] = pd.to_datetime(df["claim_date"], errors="coerce")
    df = df.dropna(subset=["claim_date"])
    if df.empty:
        return _placeholder("No valid claim dates")

    df["claim_month"] = df["claim_date"].dt.to_period("M").astype(str)
    counts = df.groupby("claim_month")["claim_id"].count().sort_index()

    fig, ax = plt.subplots()
    ax.plot(counts.index, counts.values, marker="o", color="steelblue")
    ax.set_title("Monthly Claim Volume")
    ax.set_xlabel("Month")
    ax.set_ylabel("Number of Claims")
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    return fig


def plot_average_settlement_time(data):
    """Plot average settlement days by claim type."""
    df = data.get("claims", pd.DataFrame())
    if df.empty or "claim_settlement_days" not in df.columns or "claim_type" not in df.columns:
        return _placeholder("No settlement time data")

    grouped = (
        df.groupby("claim_type")["claim_settlement_days"]
        .mean()
        .dropna()
        .sort_values(ascending=False)
    )
    if grouped.empty:
        return _placeholder("No valid settlement times")

    fig, ax = plt.subplots()
    sns.barplot(x=grouped.index, y=grouped.values, ax=ax, palette="Purples")
    ax.set_title("Average Settlement Days by Claim Type")
    ax.set_xlabel("Claim Type")
    ax.set_ylabel("Average Days")
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
    fig.tight_layout()
    return fig


# ======================================================================
# Vehicle visualizations
# ======================================================================
def plot_claim_amount_by_vehicle_type(data):
    """Plot average claim amount by vehicle type."""
    df = _safe_merge_claims_vehicles(data)
    if df.empty:
        return _placeholder("No vehicle-claim data for the current filters")

    grouped = (
        df.groupby("vehicle_type")["claim_amount"]
        .mean()
        .dropna()
        .sort_values(ascending=False)
    )
    if grouped.empty:
        return _placeholder("No valid claim amounts by vehicle type")

    fig, ax = plt.subplots()
    sns.barplot(x=grouped.index, y=grouped.values, ax=ax, palette="Oranges")
    ax.set_title("Average Claim Amount by Vehicle Type")
    ax.set_xlabel("Vehicle Type")
    ax.set_ylabel("Average Claim Amount")
    fig.tight_layout()
    return fig


def plot_vehicle_type_claim_performance(data):
    """Plot total claim amount by vehicle type."""
    df = _safe_merge_claims_vehicles(data)
    if df.empty:
        return _placeholder("No vehicle-claim data for the current filters")

    grouped = (
        df.groupby("vehicle_type")["claim_amount"]
        .sum()
        .sort_values(ascending=False)
    )
    if grouped.empty:
        return _placeholder("No valid claim totals by vehicle type")

    fig, ax = plt.subplots()
    sns.barplot(x=grouped.index, y=grouped.values, ax=ax, palette="crest")
    ax.set_title("Total Claim Amount by Vehicle Type")
    ax.set_xlabel("Vehicle Type")
    ax.set_ylabel("Total Claim Amount")
    fig.tight_layout()
    return fig


def plot_vehicle_age_vs_claim_amount(data):
    """Scatter: vehicle age vs claim amount."""
    df = _safe_merge_claims_vehicle_age(data)
    if df.empty:
        return _placeholder("No vehicle age / claim data")

    df = df.dropna(subset=["vehicle_age", "claim_amount"])
    if df.empty:
        return _placeholder("No valid vehicle age / claim points")

    fig, ax = plt.subplots()
    sns.scatterplot(data=df, x="vehicle_age", y="claim_amount",
                    alpha=0.4, ax=ax, color="darkorange")
    ax.set_title("Vehicle Age vs Claim Amount")
    ax.set_xlabel("Vehicle Age (years)")
    ax.set_ylabel("Claim Amount")
    fig.tight_layout()
    return fig


# ======================================================================
# Customer visualizations
# ======================================================================
def plot_customer_age_vs_claim_amount(data):
    """Scatter: customer age vs claim amount."""
    df = _safe_merge_claims_customers(data)
    if df.empty:
        return _placeholder("No customer age / claim data")

    df = df.dropna(subset=["customer_age", "claim_amount"])
    if df.empty:
        return _placeholder("No valid customer age / claim points")

    fig, ax = plt.subplots()
    sns.scatterplot(data=df, x="customer_age", y="claim_amount",
                    alpha=0.4, ax=ax, color="steelblue")
    ax.set_title("Customer Age vs Claim Amount")
    ax.set_xlabel("Customer Age")
    ax.set_ylabel("Claim Amount")
    fig.tight_layout()
    return fig


# ======================================================================
# Region visualizations
# ======================================================================
def plot_claims_by_region(data):
    """Plot claim counts by state (region)."""
    df = _safe_merge_claims_customers_state(data)
    if df.empty or "claim_id" not in df.columns:
        return _placeholder("No region / claim data")

    grouped = (
        df.groupby("state")["claim_id"]
        .count()
        .sort_values(ascending=False)
        .head(15)
    )
    if grouped.empty:
        return _placeholder("No claims per region")

    fig, ax = plt.subplots()
    sns.barplot(x=grouped.values, y=grouped.index, ax=ax, palette="Spectral")
    ax.set_title("Top 15 States by Claim Count")
    ax.set_xlabel("Number of Claims")
    ax.set_ylabel("State")
    fig.tight_layout()
    return fig


def plot_claim_severity_by_region(data):
    """Plot average claim amount by state (region)."""
    df = _safe_merge_claims_customers_state(data)
    if df.empty:
        return _placeholder("No region / claim data")

    grouped = (
        df.groupby("state")["claim_amount"]
        .mean()
        .dropna()
        .sort_values(ascending=False)
        .head(15)
    )
    if grouped.empty:
        return _placeholder("No average claim amount per region")

    fig, ax = plt.subplots()
    sns.barplot(x=grouped.values, y=grouped.index, ax=ax, palette="Reds")
    ax.set_title("Top 15 States by Average Claim Amount")
    ax.set_xlabel("Average Claim Amount")
    ax.set_ylabel("State")
    fig.tight_layout()
    return fig


# ======================================================================
# Risk / ratio visualizations
# ======================================================================
def plot_claim_to_premium_by_policy_type(data):
    """
    Plot claim-to-premium ratio by policy type.

    Robust to:
    - missing columns in either table
    - empty filtered DataFrames
    - disjoint policy_ids between claims and policies after filtering
    """
    df = _safe_merge_claims_policies(data)
    if df.empty:
        return _placeholder("No claim-to-premium data for the current filters")

    grouped = df.groupby("policy_type", as_index=False).agg(
        total_claim=("claim_amount", "sum"),
        total_premium=("premium_amount", "sum"),
    )

    grouped["ratio"] = np.where(
        grouped["total_premium"] > 0,
        grouped["total_claim"] / grouped["total_premium"],
        np.nan,
    )
    grouped = grouped.dropna(subset=["ratio"]).sort_values("ratio", ascending=False)

    if grouped.empty:
        return _placeholder("No valid claim-to-premium ratios to plot")

    fig, ax = plt.subplots()
    sns.barplot(data=grouped, x="policy_type", y="ratio", ax=ax, palette="rocket")
    ax.set_title("Claim-to-Premium Ratio by Policy Type")
    ax.set_xlabel("Policy Type")
    ax.set_ylabel("Ratio")
    fig.tight_layout()
    return fig


# ======================================================================
# Payments
# ======================================================================
def plot_payment_status(data):
    """Plot payment status distribution."""
    df = data.get("payments", pd.DataFrame())
    if df.empty or "payment_status" not in df.columns:
        return _placeholder("No payment status data")

    counts = df["payment_status"].value_counts()
    fig, ax = plt.subplots()
    sns.barplot(x=counts.index, y=counts.values, ax=ax, palette="Set3")
    ax.set_title("Payment Status Distribution")
    ax.set_xlabel("Payment Status")
    ax.set_ylabel("Count")
    fig.tight_layout()
    return fig
