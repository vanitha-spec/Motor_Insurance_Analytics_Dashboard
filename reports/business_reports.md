# Motor Insurance Analytics — Business Report

## Executive Summary

This report summarizes the analytical findings from the motor insurance
operational dataset. The analysis covers policy portfolio health, premium
collection, claim behavior, claim severity, settlement performance,
customer patterns, and operational risk indicators.

## Business Problem

The insurance company needs a reliable analytical solution to understand:

- Policy activity and portfolio composition
- Premium collection efficiency
- Claim volume, status, and severity
- Settlement performance
- Customer and vehicle risk patterns
- Areas requiring management investigation

## Data and Table Summary

| Table | Purpose | Key |
|-------|---------|-----|
| customers | Customer profile and demographics | customer_id |
| vehicles | Vehicle attributes | vehicle_id |
| policies | Policy, premium, and coverage info | policy_id |
| claims | Claim events and status | claim_id |
| payments | Payment / settlement info | payment_id |

## Data Quality Findings

- Missing values in numeric columns filled with median.
- Missing values in categorical columns filled with "Unknown".
- Duplicate rows removed.
- Dates parsed and invalid dates coerced to NaT.
- Business rules enforced: policy_start <= policy_end; accident_date <= claim_date.

## Cleaning Performed

1. `handle_missing_values`
2. `remove_duplicates`
3. `clean_text_columns`
4. `clean_date_columns`
5. `validate_numeric_columns`
6. `validate_business_rules`
7. `create_derived_columns`

## KPI Summary

| KPI | Description |
|-----|-------------|
| Total Policies | Unique policies |
| Active Policies | Policies with status Active |
| Total Premium | Sum of premium_amount |
| Total Claims | Unique claims |
| Total Claim Amount | Sum of claim_amount |
| Claim Approval Rate | Approved / total × 100 |
| Claim Rejection Rate | Rejected / total × 100 |
| Average Settlement Days | Mean of settlement_date - claim_date |
| Claim-to-Premium Ratio | Total claim / total premium |
| Paid Claim Ratio | Total payment / total claim |

## EDA Findings

- Premium and claim amount distributions are right-skewed.
- Certain vehicle types show higher average claim amounts.
- Some states have higher claim frequency and severity.
- Damage severity correlates with average claim amount.

## Important Patterns

- A small set of vehicle types contributes a large share of claim value.
- Certain policy types have a high claim-to-premium ratio.
- Some regions show above-average claim frequency.

## Business Insights

Each insight follows the PATTERN / EVIDENCE / BUSINESS MEANING / RECOMMENDATION format
(see `src/insights.py` for the generated outputs).

## Recommendations

- Re-price underperforming segments.
- Audit rejected claims for root causes.
- Streamline settlement for slow claim types.
- Diversify product mix if concentration is high.

## Dashboard Summary

The Streamlit dashboard includes:

- Executive Overview
- Policy Analysis
- Claims Analysis
- Customer Analysis
- Vehicle Analysis
- Premium & Risk
- Insights & Recommendations

Sidebar filters allow slicing by policy type, status, claim type, status,
vehicle type, make, state, and damage severity.

## Deployment Summary

- Docker image built from `Dockerfile`
- Image pushed to Amazon ECR
- Application deployed on AWS EC2
- Streamlit served on port 8501
- Live URL submitted via the admin Google Form

## Conclusion

The project converts raw motor insurance data into validated, cleaned,
business-ready data; produces KPIs, EDA, and insights; and exposes them
through an interactive Streamlit dashboard. The solution is containerized
and deployed to AWS, providing a reliable and reproducible analytics
platform for the insurance business.
