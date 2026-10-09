"""Pipeline tests."""

import os
import sys
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_cleaner import (
    remove_duplicates,
    create_derived_columns,
    clean_data,
    save_cleaned_data,
)
from src.data_loader import load_all_data


def _sample_data():
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


def test_load_all_data(tmp_path):
    """Test that load_all_data raises on missing files."""
    # Create only one file
    (tmp_path / "customers.csv").write_text("customer_id\nC1\n")
    with pytest.raises(FileNotFoundError):
        load_all_data(str(tmp_path))


def test_remove_duplicates():
    """Test that duplicate rows are removed."""
    df = pd.DataFrame({"a": [1, 1, 2], "b": ["x", "x", "y"]})
    data = {"t": df}
    out = remove_duplicates(data)
    assert len(out["t"]) == 2


def test_create_derived_columns():
    """Test that derived columns are created correctly."""
    data = _sample_data()
    out = create_derived_columns(data)

    # policies
    assert "policy_duration_days" in out["policies"].columns
    assert "policy_active_flag" in out["policies"].columns
    assert out["policies"]["policy_duration_days"].iloc[0] == 365

    # claims
    assert "claim_processing_days" in out["claims"].columns
    assert "claim_settlement_days" in out["claims"].columns

    # vehicles
    assert "vehicle_age" in out["vehicles"].columns

    # customers
    assert "customer_age" in out["customers"].columns


def test_clean_data():
    """Test that clean_data returns a dict with all tables."""
    data = _sample_data()
    out = clean_data(data)
    for tbl in ["customers", "vehicles", "policies", "claims", "payments"]:
        assert tbl in out
        assert isinstance(out[tbl], pd.DataFrame)


def test_save_cleaned_data(tmp_path):
    """Test that save_cleaned_data writes the expected files."""
    data = _sample_data()
    cleaned = clean_data(data)
    save_cleaned_data(cleaned, str(tmp_path))
    for tbl in ["customers", "vehicles", "policies", "claims", "payments"]:
        expected = tmp_path / f"{tbl}_cleaned.csv"
        assert expected.exists()
        