"""Analysis tests."""

import os
import sys
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import insurance_analysis as ia


def _sample_data():
    policies = pd.DataFrame({
        "policy_id": ["P1", "P2", "P3"],
        "premium_amount": [1000, 2000, 3000],
        "coverage_amount": [10000, 20000, 30000],
        "policy_status": ["Active", "Expired", "Active"],
        "policy_type": ["A", "B", "A"],
    })
    claims = pd.DataFrame({
        "claim_id": ["C1", "C2", "C3", "C4"],
        "policy_id": ["P1", "P1", "P2", "P3"],
        "claim_amount": [500, 1500, 2500, 1000],
        "claim_status": ["Approved", "Rejected", "Pending", "Approved"],
    })
    payments = pd.DataFrame({
        "payment_id": ["PAY1", "PAY2"],
        "claim_id": ["C1", "C2"],
        "payment_amount": [500, 0],
        "payment_status": ["Paid", "Rejected"],
    })
    customers = pd.DataFrame({"customer_id": ["C1", "C2"]})
    vehicles = pd.DataFrame({"vehicle_id": ["V1", "V2"]})
    return {
        "customers": customers,
        "vehicles": vehicles,
        "policies": policies,
        "claims": claims,
        "payments": payments,
    }


def test_calculate_total_policies():
    data = _sample_data()
    assert ia.calculate_total_policies(data) == 3


def test_calculate_active_policies():
    data = _sample_data()
    assert ia.calculate_active_policies(data) == 2


def test_calculate_total_claims():
    data = _sample_data()
    assert ia.calculate_total_claims(data) == 4


def test_calculate_total_premium():
    data = _sample_data()
    assert ia.calculate_total_premium(data) == 6000


def test_calculate_claim_approval_rate():
    data = _sample_data()
    # 2 approved out of 4 -> 50%
    assert ia.calculate_claim_approval_rate(data) == 50.0


def test_calculate_average_claim_amount():
    data = _sample_data()
    # (500 + 1500 + 2500 + 1000) / 4 = 1375
    assert ia.calculate_average_claim_amount(data) == 1375.0
    