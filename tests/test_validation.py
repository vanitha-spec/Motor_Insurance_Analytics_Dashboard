"""Validation tests."""

import os
import sys
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import validation as v


def _valid_data():
    customers = pd.DataFrame({
        "customer_id": ["C1", "C2"],
        "customer_name": ["A", "B"],
        "gender": ["Male", "Female"],
        "date_of_birth": ["1990-01-01", "1985-06-15"],
        "age": [34, 39],
        "city": ["X", "Y"],
        "state": ["S1", "S2"],
        "occupation": ["Engineer", "Teacher"],
    })
    vehicles = pd.DataFrame({
        "vehicle_id": ["V1", "V2"],
        "customer_id": ["C1", "C2"],
        "vehicle_type": ["Car", "Bike"],
        "vehicle_make": ["Honda", "Yamaha"],
        "vehicle_model": ["City", "FZ"],
        "vehicle_year": [2018, 2020],
        "fuel_type": ["Petrol", "Petrol"],
        "vehicle_value": [800000, 120000],
    })
    policies = pd.DataFrame({
        "policy_id": ["P1", "P2"],
        "customer_id": ["C1", "C2"],
        "vehicle_id": ["V1", "V2"],
        "policy_start_date": ["2023-01-01", "2023-02-01"],
        "policy_end_date": ["2024-01-01", "2024-02-01"],
        "policy_type": ["Comprehensive", "Third Party"],
        "premium_amount": [15000, 5000],
        "coverage_amount": [800000, 200000],
        "policy_status": ["Active", "Expired"],
        "payment_frequency": ["Yearly", "Yearly"],
    })
    claims = pd.DataFrame({
        "claim_id": ["CL1", "CL2"],
        "policy_id": ["P1", "P2"],
        "customer_id": ["C1", "C2"],
        "claim_date": ["2023-05-01", "2023-06-01"],
        "accident_date": ["2023-04-28", "2023-05-30"],
        "claim_type": ["Accident", "Theft"],
        "accident_location": ["City", "Highway"],
        "claim_amount": [50000, 30000],
        "claim_status": ["Approved", "Rejected"],
        "approval_date": ["2023-05-10", None],
        "settlement_date": [None, None],
        "damage_severity": ["Medium", "Low"],
    })
    payments = pd.DataFrame({
        "payment_id": ["PAY1", "PAY2"],
        "claim_id": ["CL1", "CL2"],
        "policy_id": ["P1", "P2"],
        "payment_date": ["2023-05-15", "2023-06-10"],
        "payment_amount": [50000, 0],
        "payment_status": ["Paid", "Rejected"],
        "payment_method": ["Bank", "Bank"],
    })
    return {
        "customers": customers,
        "vehicles": vehicles,
        "policies": policies,
        "claims": claims,
        "payments": payments,
    }


def test_validate_customers():
    data = _valid_data()
    assert v.validate_customers(data["customers"]) is True


def test_validate_policies():
    data = _valid_data()
    assert v.validate_policies(data["policies"]) is True


def test_validate_claims():
    data = _valid_data()
    assert v.validate_claims(data["claims"]) is True


def test_validate_relationships():
    data = _valid_data()
    assert v.validate_relationships(data) is True
    