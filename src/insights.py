"""
Insight and Pattern Engine
==========================
Generates data-driven patterns, evidence, business meaning,
and recommendations from the cleaned dataset.
"""

import pandas as pd
import numpy as np

from src.logger import setup_logger

logger = setup_logger(__name__)


def _fmt_money(x):
    try:
        return f"{x:,.0f}"
    except Exception:
        return str(x)


def generate_portfolio_insights(data: dict) -> list:
    """Generate portfolio-level insights."""
    insights = []
    policies = data["policies"]

    total = len(policies)
    active = (policies["policy_status"] == "Active").sum()
    expired = (policies["policy_status"] == "Expired").sum()
    cancelled = (policies["policy_status"] == "Cancelled").sum()
    renewed = (policies["policy_status"] == "Renewed").sum()

    if total == 0:
        return insights

    active_pct = active / total * 100
    insights.append({
        "pattern": f"Active policies represent {active_pct:.1f}% of the portfolio.",
        "evidence": f"Active: {active}, Expired: {expired}, Cancelled: {cancelled}, Renewed: {renewed} (Total: {total}).",
        "business_meaning": "Portfolio health depends on the share of active policies.",
        "recommendation": "Focus retention efforts on policies nearing expiry to maintain active share.",
    })

    # Concentration in policy type
    type_counts = policies["policy_type"].value_counts()
    if len(type_counts) > 1:
        top_type = type_counts.index[0]
        top_pct = type_counts.iloc[0] / total * 100
        insights.append({
            "pattern": f"'{top_type}' dominates the portfolio at {top_pct:.1f}% of policies.",
            "evidence": f"Policy type distribution: {type_counts.to_dict()}.",
            "business_meaning": "Over-reliance on a single policy type may expose the insurer to concentration risk.",
            "recommendation": "Consider diversifying product mix or promoting under-represented policy types.",
        })

    return insights


def generate_claim_insights(data: dict) -> list:
    """Generate claim-related insights."""
    insights = []
    claims = data["claims"]

    if len(claims) == 0:
        return insights

    status_counts = claims["claim_status"].value_counts()
    total = len(claims)
    approved = status_counts.get("Approved", 0)
    rejected = status_counts.get("Rejected", 0)
    pending = status_counts.get("Pending", 0)
    settled = status_counts.get("Settled", 0)

    approval_rate = approved / total * 100 if total else 0
    rejection_rate = rejected / total * 100 if total else 0

    insights.append({
        "pattern": f"Claim approval rate is {approval_rate:.1f}% and rejection rate is {rejection_rate:.1f}%.",
        "evidence": f"Approved: {approved}, Rejected: {rejected}, Pending: {pending}, Settled: {settled}.",
        "business_meaning": "High rejection rates may signal underwriting or validation issues.",
        "recommendation": "Audit rejected claims to identify root causes and improve claim intake quality.",
    })

    # Claim type concentration
    type_counts = claims.groupby("claim_type")["claim_amount"].sum().sort_values(ascending=False)
    if len(type_counts) > 0:
        top = type_counts.index[0]
        top_share = type_counts.iloc[0] / type_counts.sum() * 100
        insights.append({
            "pattern": f"'{top}' claims account for {top_share:.1f}% of total claim value.",
            "evidence": f"Top claim types by amount: {type_counts.head(3).to_dict()}.",
            "business_meaning": "Concentrated claim value in a few claim types can distort loss ratios.",
            "recommendation": "Review pricing and underwriting for the dominant claim types.",
        })

    return insights


def generate_premium_insights(data: dict) -> list:
    """Generate premium-related insights."""
    insights = []
    policies = data["policies"]

    if len(policies) == 0:
        return insights

    total_premium = policies["premium_amount"].sum()
    avg_premium = policies["premium_amount"].mean()
    by_type = policies.groupby("policy_type")["premium_amount"].sum().sort_values(ascending=False)

    if len(by_type) > 0:
        top_type = by_type.index[0]
        top_share = by_type.iloc[0] / total_premium * 100 if total_premium else 0
        insights.append({
            "pattern": f"'{top_type}' generates {top_share:.1f}% of total premium.",
            "evidence": f"Total premium: {_fmt_money(total_premium)}; top policy type: {top_type} ({_fmt_money(by_type.iloc[0])}).",
            "business_meaning": "Premium concentration matters for revenue stability.",
            "recommendation": f"Monitor performance of '{top_type}' policies and diversify revenue sources.",
        })

    insights.append({
        "pattern": f"Average premium per policy is {_fmt_money(avg_premium)}.",
        "evidence": f"Computed across {len(policies)} policies.",
        "business_meaning": "Average premium indicates pricing level and portfolio quality.",
        "recommendation": "Benchmark against market averages to ensure competitiveness.",
    })

    return insights


def generate_customer_insights(data: dict) -> list:
    """Generate customer-related insights."""
    insights = []
    customers = data["customers"]
    claims = data["claims"]

    if len(customers) == 0:
        return insights

    # Age group analysis
    if "customer_age" in customers.columns:
        bins = [0, 25, 35, 50, 65, 120]
        labels = ["<25", "25-34", "35-49", "50-64", "65+"]
        customers = customers.copy()
        customers["age_group"] = pd.cut(customers["customer_age"], bins=bins, labels=labels, right=False)
        age_counts = customers["age_group"].value_counts().sort_index()
        insights.append({
            "pattern": f"Customer age distribution peaks in group '{age_counts.idxmax()}'.",
            "evidence": f"Age group counts: {age_counts.to_dict()}.",
            "business_meaning": "Age groups differ in risk and premium potential.",
            "recommendation": "Design targeted products for the dominant age groups.",
        })

    return insights


def generate_vehicle_insights(data: dict) -> list:
    """Generate vehicle-related insights."""
    insights = []
    vehicles = data["vehicles"]
    claims = data["claims"]
    policies = data["policies"]

    if len(vehicles) == 0:
        return insights

    # Merge for claim analysis by vehicle type
    df = claims.merge(policies[["policy_id", "vehicle_id"]], on="policy_id", how="left") \
              .merge(vehicles[["vehicle_id", "vehicle_type"]], on="vehicle_id", how="left")

    if len(df) > 0:
        grouped = df.groupby("vehicle_type")["claim_amount"].sum().sort_values(ascending=False)
        total = grouped.sum()
        if total > 0:
            top = grouped.index[0]
            share = grouped.iloc[0] / total * 100
            insights.append({
                "pattern": f"'{top}' vehicles contribute {share:.1f}% of total claim value.",
                "evidence": f"Vehicle type claim totals: {grouped.head(3).to_dict()}.",
                "business_meaning": "Some vehicle types are disproportionately costly.",
                "recommendation": f"Review underwriting and claims handling for '{top}' vehicles.",
            })

    return insights


def generate_risk_patterns(data: dict) -> list:
    """Generate risk-related patterns."""
    insights = []
    claims = data["claims"]
    policies = data["policies"]

    if len(claims) == 0 or len(policies) == 0:
        return insights

    # Overall claim-to-premium ratio
    total_claims = claims["claim_amount"].sum()
    total_premium = policies["premium_amount"].sum()
    ratio = total_claims / total_premium if total_premium else 0

    insights.append({
        "pattern": f"Portfolio claim-to-premium ratio is {ratio:.2f}.",
        "evidence": f"Total claims: {_fmt_money(total_claims)}; Total premium: {_fmt_money(total_premium)}.",
        "business_meaning": "Ratios above 1.0 indicate claims exceed premium collected.",
        "recommendation": "Re-price underperforming segments if ratio exceeds target loss ratio.",
    })

    # High severity by damage severity
    if "damage_severity" in claims.columns:
        sev = claims.groupby("damage_severity")["claim_amount"].mean().sort_values(ascending=False)
        insights.append({
            "pattern": f"Average claim amount is highest for '{sev.index[0]}' damage severity.",
            "evidence": f"Severity averages: {sev.to_dict()}.",
            "business_meaning": "Severity tiers drive claim cost differences.",
            "recommendation": "Align deductibles and inspections with severity levels.",
        })

    return insights


def generate_business_recommendations(data: dict) -> list:
    """Generate high-level business recommendations."""
    recs = []
    claims = data["claims"]
    policies = data["policies"]

    if len(claims) == 0 or len(policies) == 0:
        return recs

    # Settlement performance
    if "claim_settlement_days" in claims.columns:
        avg_days = claims["claim_settlement_days"].mean()
        if pd.notna(avg_days):
            if avg_days > 30:
                recs.append(
                    f"Average settlement time is {avg_days:.0f} days — streamline claims processing to reduce turnaround."
                )
            else:
                recs.append(
                    f"Average settlement time is {avg_days:.0f} days — within acceptable range; maintain current processes."
                )

    # Pending claims
    pending = (claims["claim_status"] == "Pending").sum()
    if pending > 0:
        recs.append(f"There are {pending} pending claims — prioritize review to avoid backlog and customer dissatisfaction.")

    # Rejected claims
    rejected = (claims["claim_status"] == "Rejected").sum()
    if rejected > 0:
        recs.append(f"{rejected} claims were rejected — investigate root causes to improve claim quality and reduce disputes.")

    return recs
