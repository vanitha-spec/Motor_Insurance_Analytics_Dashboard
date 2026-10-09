"""
Insurance Analysis Module
=========================
Standard business analysis functions and KPI calculations.

All functions are defensive against:
- missing tables / columns
- empty filtered DataFrames
- disjoint policy_ids between claims and policies after filtering
- divide-by-zero
"""

import numpy as np
import pandas as pd

from src.logger import setup_logger

logger = setup_logger(__name__)


# ======================================================================
# Internal helpers
# ======================================================================
def _empty_df():
    """Return a typed empty DataFrame used as a safe fallback."""
    return pd.DataFrame()


def _has_columns(df: pd.DataFrame, cols) -> bool:
    """True if df contains all the given columns."""
    return all(c in df.columns for c in cols)


def _safe_merge_claims_policies(data: dict,
                                claims_cols,
                                policies_cols) -> pd.DataFrame:
    """
    Inner-merge claims with policies on policy_id, keeping only the
    requested columns. Returns an empty DataFrame if any required
    column is missing.
    """
    claims = data.get("claims", _empty_df())
    policies = data.get("policies", _empty_df())

    if not _has_columns(claims, ["policy_id", *claims_cols]):
        return _empty_df()
    if not _has_columns(policies, ["policy_id", *policies_cols]):
        return _empty_df()

    left = claims[["policy_id", *claims_cols]].copy()
    right = policies[["policy_id", *policies_cols]].copy()

    # Avoid duplicate column names in the merged frame
    overlap = set(left.columns) & set(right.columns) - {"policy_id"}
    if overlap:
        right = right.drop(columns=list(overlap))

    return left.merge(right, on="policy_id", how="inner")


def _safe_merge_claims_policies_vehicles(data: dict) -> pd.DataFrame:
    """
    Inner-merge claims -> policies -> vehicles, returning a frame with
    claim_id, claim_amount, policy_id, vehicle_id, vehicle_type.
    Returns an empty DataFrame if any required column is missing.
    """
    claims = data.get("claims", _empty_df())
    policies = data.get("policies", _empty_df())
    vehicles = data.get("vehicles", _empty_df())

    if not _has_columns(claims, ["claim_id", "policy_id", "claim_amount"]):
        return _empty_df()
    if not _has_columns(policies, ["policy_id", "vehicle_id"]):
        return _empty_df()
    if not _has_columns(vehicles, ["vehicle_id", "vehicle_type"]):
        return _empty_df()

    df = (
        claims[["claim_id", "policy_id", "claim_amount"]]
        .merge(policies[["policy_id", "vehicle_id"]],
               on="policy_id", how="inner")
        .merge(vehicles[["vehicle_id", "vehicle_type"]],
               on="vehicle_id", how="inner")
    )
    return df


# ======================================================================
# Portfolio
# ======================================================================
def calculate_total_customers(data: dict) -> int:
    """Return the total number of unique customers."""
    df = data.get("customers", _empty_df())
    if "customer_id" not in df.columns:
        return 0
    return int(df["customer_id"].nunique())


def calculate_total_policies(data: dict) -> int:
    """Return the total number of policies."""
    df = data.get("policies", _empty_df())
    if "policy_id" not in df.columns:
        return 0
    return int(df["policy_id"].nunique())


def calculate_active_policies(data: dict) -> int:
    """Return the number of active policies."""
    df = data.get("policies", _empty_df())
    if "policy_status" not in df.columns:
        return 0
    return int((df["policy_status"] == "Active").sum())


def calculate_expired_policies(data: dict) -> int:
    """Return the number of expired policies."""
    df = data.get("policies", _empty_df())
    if "policy_status" not in df.columns:
        return 0
    return int((df["policy_status"] == "Expired").sum())


def calculate_cancelled_policies(data: dict) -> int:
    """Return the number of cancelled policies."""
    df = data.get("policies", _empty_df())
    if "policy_status" not in df.columns:
        return 0
    return int((df["policy_status"] == "Cancelled").sum())


def calculate_renewed_policies(data: dict) -> int:
    """Return the number of renewed policies."""
    df = data.get("policies", _empty_df())
    if "policy_status" not in df.columns:
        return 0
    return int((df["policy_status"] == "Renewed").sum())


# ======================================================================
# Premium
# ======================================================================
def calculate_total_premium(data: dict) -> float:
    """Return the total premium collected."""
    df = data.get("policies", _empty_df())
    if "premium_amount" not in df.columns or df.empty:
        return 0.0
    return float(df["premium_amount"].sum())


def calculate_average_premium(data: dict) -> float:
    """Return the average premium per policy."""
    df = data.get("policies", _empty_df())
    if "premium_amount" not in df.columns or df.empty:
        return 0.0
    return float(df["premium_amount"].mean())


def calculate_average_coverage(data: dict) -> float:
    """Return the average coverage amount."""
    df = data.get("policies", _empty_df())
    if "coverage_amount" not in df.columns or df.empty:
        return 0.0
    return float(df["coverage_amount"].mean())


def calculate_premium_by_policy_type(data: dict) -> pd.DataFrame:
    """Return total premium grouped by policy type."""
    df = data.get("policies", _empty_df())
    required = {"policy_type", "premium_amount"}
    if not required.issubset(df.columns) or df.empty:
        return _empty_df()
    return (
        df.groupby("policy_type", as_index=False)["premium_amount"]
        .sum()
        .sort_values("premium_amount", ascending=False)
    )


# ======================================================================
# Claims
# ======================================================================
def calculate_total_claims(data: dict) -> int:
    """Return the total number of claims."""
    df = data.get("claims", _empty_df())
    if "claim_id" not in df.columns:
        return 0
    return int(df["claim_id"].nunique())


def calculate_approved_claims(data: dict) -> int:
    """Return the number of approved claims."""
    df = data.get("claims", _empty_df())
    if "claim_status" not in df.columns:
        return 0
    return int((df["claim_status"] == "Approved").sum())


def calculate_rejected_claims(data: dict) -> int:
    """Return the number of rejected claims."""
    df = data.get("claims", _empty_df())
    if "claim_status" not in df.columns:
        return 0
    return int((df["claim_status"] == "Rejected").sum())


def calculate_pending_claims(data: dict) -> int:
    """Return the number of pending claims."""
    df = data.get("claims", _empty_df())
    if "claim_status" not in df.columns:
        return 0
    return int((df["claim_status"] == "Pending").sum())


def calculate_total_claim_amount(data: dict) -> float:
    """Return the total claim amount."""
    df = data.get("claims", _empty_df())
    if "claim_amount" not in df.columns or df.empty:
        return 0.0
    return float(df["claim_amount"].sum())


def calculate_average_claim_amount(data: dict) -> float:
    """Return the average claim amount."""
    df = data.get("claims", _empty_df())
    if "claim_amount" not in df.columns or df.empty:
        return 0.0
    return float(df["claim_amount"].mean())


def calculate_claim_approval_rate(data: dict) -> float:
    """Return approval rate as a percentage."""
    total = calculate_total_claims(data)
    if total == 0:
        return 0.0
    return float(calculate_approved_claims(data) / total * 100)


def calculate_claim_rejection_rate(data: dict) -> float:
    """Return rejection rate as a percentage."""
    total = calculate_total_claims(data)
    if total == 0:
        return 0.0
    return float(calculate_rejected_claims(data) / total * 100)


# ======================================================================
# Settlement
# ======================================================================
def calculate_average_claim_processing_days(data: dict) -> float:
    """Return average processing days (approval - claim date)."""
    df = data.get("claims", _empty_df())
    if "claim_processing_days" not in df.columns or df.empty:
        return float("nan")
    return float(df["claim_processing_days"].mean())


def calculate_average_claim_settlement_days(data: dict) -> float:
    """Return average settlement days (settlement - claim date)."""
    df = data.get("claims", _empty_df())
    if "claim_settlement_days" not in df.columns or df.empty:
        return float("nan")
    return float(df["claim_settlement_days"].mean())


def calculate_total_payment_amount(data: dict) -> float:
    """Return total payment amount."""
    df = data.get("payments", _empty_df())
    if "payment_amount" not in df.columns or df.empty:
        return 0.0
    return float(df["payment_amount"].sum())


def calculate_average_payment_amount(data: dict) -> float:
    """Return average payment amount."""
    df = data.get("payments", _empty_df())
    if "payment_amount" not in df.columns or df.empty:
        return 0.0
    return float(df["payment_amount"].mean())


# ======================================================================
# Risk / ratios
# ======================================================================
def calculate_claim_to_premium_ratio(data: dict) -> float:
    """Return overall claim-to-premium ratio."""
    total_claims = calculate_total_claim_amount(data)
    total_premium = calculate_total_premium(data)
    if total_premium == 0:
        return 0.0
    return float(total_claims / total_premium)


def calculate_claim_to_coverage_ratio(data: dict) -> float:
    """Return overall claim-to-coverage ratio."""
    df = data.get("claims", _empty_df())
    if "claim_to_coverage_ratio" not in df.columns or df.empty:
        return float("nan")
    return float(df["claim_to_coverage_ratio"].mean())


def calculate_paid_claim_ratio(data: dict) -> float:
    """Return overall paid-claim ratio."""
    df = data.get("claims", _empty_df())
    if "paid_claim_ratio" not in df.columns or df.empty:
        return float("nan")
    return float(df["paid_claim_ratio"].mean())


# ======================================================================
# Customer / Vehicle
# ======================================================================
def analyze_customer_claims(data: dict) -> pd.DataFrame:
    """Return claim aggregates per customer."""
    claims = data.get("claims", _empty_df())
    required = {"customer_id", "claim_id", "claim_amount"}
    if not required.issubset(claims.columns) or claims.empty:
        return _empty_df()
    return (
        claims.groupby("customer_id", as_index=False)
        .agg(total_claims=("claim_id", "count"),
             total_claim_amount=("claim_amount", "sum"),
             avg_claim_amount=("claim_amount", "mean"))
        .sort_values("total_claim_amount", ascending=False)
    )


def analyze_customer_premium(data: dict) -> pd.DataFrame:
    """Return premium aggregates per customer."""
    policies = data.get("policies", _empty_df())
    required = {"customer_id", "policy_id", "premium_amount"}
    if not required.issubset(policies.columns) or policies.empty:
        return _empty_df()
    return (
        policies.groupby("customer_id", as_index=False)
        .agg(total_premium=("premium_amount", "sum"),
             avg_premium=("premium_amount", "mean"),
             num_policies=("policy_id", "count"))
        .sort_values("total_premium", ascending=False)
    )


def analyze_vehicle_claims(data: dict) -> pd.DataFrame:
    """Return claim aggregates per vehicle type."""
    df = _safe_merge_claims_policies_vehicles(data)
    if df.empty:
        return _empty_df()
    return (
        df.groupby("vehicle_type", as_index=False)
        .agg(total_claims=("claim_id", "count"),
             total_claim_amount=("claim_amount", "sum"),
             avg_claim_amount=("claim_amount", "mean"))
        .sort_values("total_claim_amount", ascending=False)
    )


def analyze_vehicle_risk_patterns(data: dict) -> pd.DataFrame:
    """
    Return risk patterns per vehicle type (claim-to-premium ratio).

    Uses an inner merge so only claims whose policy survived the current
    filter are considered. Guards against empty frames and missing columns.
    """
    df = _safe_merge_claims_policies(data,
                                     claims_cols=["claim_id", "claim_amount"],
                                     policies_cols=["vehicle_id", "premium_amount"])
    vehicles = data.get("vehicles", _empty_df())

    if df.empty or "vehicle_id" not in df.columns or \
       not {"vehicle_id", "vehicle_type"}.issubset(vehicles.columns):
        return _empty_df()

    df = df.merge(vehicles[["vehicle_id", "vehicle_type"]],
                  on="vehicle_id", how="inner")

    if df.empty:
        return _empty_df()

    grouped = df.groupby("vehicle_type", as_index=False).agg(
        total_claim_amount=("claim_amount", "sum"),
        total_premium=("premium_amount", "sum"),
        claim_count=("claim_id", "count"),
    )

    grouped["claim_to_premium_ratio"] = np.where(
        grouped["total_premium"] > 0,
        grouped["total_claim_amount"] / grouped["total_premium"],
        np.nan,
    )

    return grouped.sort_values("claim_to_premium_ratio", ascending=False)


# ======================================================================
# Business analysis
# ======================================================================
def analyze_claim_type(data: dict) -> pd.DataFrame:
    """Return claim aggregates by claim type."""
    df = data.get("claims", _empty_df())
    required = {"claim_type", "claim_id", "claim_amount"}
    if not required.issubset(df.columns) or df.empty:
        return _empty_df()
    return (
        df.groupby("claim_type", as_index=False)
        .agg(total_claims=("claim_id", "count"),
             total_claim_amount=("claim_amount", "sum"),
             avg_claim_amount=("claim_amount", "mean"))
        .sort_values("total_claim_amount", ascending=False)
    )


def analyze_claim_status(data: dict) -> pd.DataFrame:
    """Return claim counts by status."""
    df = data.get("claims", _empty_df())
    required = {"claim_status", "claim_id", "claim_amount"}
    if not required.issubset(df.columns) or df.empty:
        return _empty_df()
    return (
        df.groupby("claim_status", as_index=False)
        .agg(count=("claim_id", "count"),
             total_amount=("claim_amount", "sum"))
        .sort_values("count", ascending=False)
    )


def analyze_policy_type(data: dict) -> pd.DataFrame:
    """Return policy counts and premium by policy type."""
    df = data.get("policies", _empty_df())
    required = {"policy_type", "policy_id", "premium_amount"}
    if not required.issubset(df.columns) or df.empty:
        return _empty_df()
    return (
        df.groupby("policy_type", as_index=False)
        .agg(num_policies=("policy_id", "count"),
             total_premium=("premium_amount", "sum"),
             avg_premium=("premium_amount", "mean"))
        .sort_values("total_premium", ascending=False)
    )