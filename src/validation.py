"""
Validation Module
=================
Validates schema, primary keys, relationships, and business rules
for all motor insurance tables.
"""

import pandas as pd

from src.logger import setup_logger, log_pipeline_step, log_error

logger = setup_logger(__name__)

# Required columns per table (from the project specification)
REQUIRED_COLUMNS = {
    "customers": [
        "customer_id", "customer_name", "gender", "date_of_birth",
        "age", "city", "state", "occupation",
    ],
    "vehicles": [
        "vehicle_id", "customer_id", "vehicle_type", "vehicle_make",
        "vehicle_model", "vehicle_year", "fuel_type", "vehicle_value",
    ],
    "policies": [
        "policy_id", "customer_id", "vehicle_id", "policy_start_date",
        "policy_end_date", "policy_type", "premium_amount", "coverage_amount",
        "policy_status", "payment_frequency",
    ],
    "claims": [
        "claim_id", "policy_id", "customer_id", "claim_date", "accident_date",
        "claim_type", "accident_location", "claim_amount", "claim_status",
        "approval_date", "settlement_date", "damage_severity",
    ],
    "payments": [
        "payment_id", "claim_id", "policy_id", "payment_date",
        "payment_amount", "payment_status", "payment_method",
    ],
}

# Primary keys per table
PRIMARY_KEYS = {
    "customers": "customer_id",
    "vehicles": "vehicle_id",
    "policies": "policy_id",
    "claims": "claim_id",
    "payments": "payment_id",
}

# Valid categorical values
VALID_CATEGORIES = {
    "customers": {
        "gender": ["Male", "Female"],
    },
    "policies": {
        "policy_status": ["Active", "Expired", "Cancelled", "Renewed"],
    },
    "claims": {
        "claim_status": ["Pending", "Approved", "Rejected", "Settled"],
        "damage_severity": ["Low", "Medium", "High"],
    },
    "payments": {
        "payment_status": ["Paid", "Pending", "Failed", "Completed"],
    },
}

# Numeric columns that must be non-negative
NUMERIC_NON_NEGATIVE = {
    "customers": ["age"],
    "vehicles": ["vehicle_value", "vehicle_year"],
    "policies": ["premium_amount", "coverage_amount"],
    "claims": ["claim_amount"],
    "payments": ["payment_amount"],
}

# Date columns
DATE_COLUMNS = {
    "customers": ["date_of_birth"],
    "policies": ["policy_start_date", "policy_end_date"],
    "claims": ["claim_date", "accident_date", "approval_date", "settlement_date"],
    "payments": ["payment_date"],
}


def _check_required_columns(df: pd.DataFrame, table: str) -> bool:
    """Check that all required columns exist in the DataFrame."""
    required = REQUIRED_COLUMNS.get(table, [])
    missing = [c for c in required if c not in df.columns]
    if missing:
        log_error(f"[{table}] Missing required columns: {missing}")
        return False
    return True


def _check_primary_key_unique(df: pd.DataFrame, table: str) -> bool:
    """Check that the primary key column has unique values."""
    pk = PRIMARY_KEYS.get(table)
    if pk and pk in df.columns:
        dupes = df[pk].duplicated().sum()
        if dupes > 0:
            log_error(f"[{table}] Primary key '{pk}' has {dupes} duplicate values.")
            return False
    return True


def _check_missing_identifiers(df: pd.DataFrame, table: str) -> bool:
    """Check for missing values in identifier columns."""
    id_cols = [c for c in df.columns if c.endswith("_id")]
    ok = True
    for col in id_cols:
        nulls = df[col].isna().sum()
        if nulls > 0:
            log_error(f"[{table}] Column '{col}' has {nulls} missing identifiers.")
            ok = False
    return ok


def _check_numeric_ranges(df: pd.DataFrame, table: str) -> bool:
    """Check that numeric columns are within valid ranges (non-negative)."""
    ok = True
    for col in NUMERIC_NON_NEGATIVE.get(table, []):
        if col in df.columns:
            if (df[col] < 0).any():
                log_error(f"[{table}] Column '{col}' contains negative values.")
                ok = False
    return ok


def _check_dates(df: pd.DataFrame, table: str) -> bool:
    """Check that date columns are parseable or missing."""
    ok = True
    for col in DATE_COLUMNS.get(table, []):
        if col in df.columns:
            try:
                parsed = pd.to_datetime(df[col], errors="coerce")
                # Only flag if a non-null original value became NaT
                invalid = df[col].notna() & parsed.isna()
                if invalid.sum() > 0:
                    log_error(f"[{table}] Column '{col}' has {invalid.sum()} invalid dates.")
                    ok = False
            except Exception as e:
                log_error(f"[{table}] Date parsing error on '{col}': {e}")
                ok = False
    return ok


def _check_categorical_values(df: pd.DataFrame, table: str) -> bool:
    """Check that categorical columns contain only valid values."""
    ok = True
    for col, valid in VALID_CATEGORIES.get(table, {}).items():
        if col in df.columns:
            invalid = df[~df[col].isin(valid) & df[col].notna()]
            if len(invalid) > 0:
                unique_invalid = invalid[col].unique().tolist()
                log_error(f"[{table}] Column '{col}' has invalid values: {unique_invalid}")
                ok = False
    return ok


def validate_customers(df: pd.DataFrame) -> bool:
    """Validate the customers table."""
    return all([
        _check_required_columns(df, "customers"),
        _check_primary_key_unique(df, "customers"),
        _check_missing_identifiers(df, "customers"),
        _check_numeric_ranges(df, "customers"),
        _check_dates(df, "customers"),
        _check_categorical_values(df, "customers"),
    ])


def validate_vehicles(df: pd.DataFrame) -> bool:
    """Validate the vehicles table."""
    return all([
        _check_required_columns(df, "vehicles"),
        _check_primary_key_unique(df, "vehicles"),
        _check_missing_identifiers(df, "vehicles"),
        _check_numeric_ranges(df, "vehicles"),
    ])


def validate_policies(df: pd.DataFrame) -> bool:
    """Validate the policies table."""
    return all([
        _check_required_columns(df, "policies"),
        _check_primary_key_unique(df, "policies"),
        _check_missing_identifiers(df, "policies"),
        _check_numeric_ranges(df, "policies"),
        _check_dates(df, "policies"),
        _check_categorical_values(df, "policies"),
    ])


def validate_claims(df: pd.DataFrame) -> bool:
    """Validate the claims table."""
    return all([
        _check_required_columns(df, "claims"),
        _check_primary_key_unique(df, "claims"),
        _check_missing_identifiers(df, "claims"),
        _check_numeric_ranges(df, "claims"),
        _check_dates(df, "claims"),
        _check_categorical_values(df, "claims"),
    ])


def validate_payments(df: pd.DataFrame) -> bool:
    """Validate the payments table."""
    return all([
        _check_required_columns(df, "payments"),
        _check_primary_key_unique(df, "payments"),
        _check_missing_identifiers(df, "payments"),
        _check_numeric_ranges(df, "payments"),
        _check_dates(df, "payments"),
        _check_categorical_values(df, "payments"),
    ])


def validate_relationships(data: dict) -> bool:
    """
    Validate foreign key relationships between tables.

    - policies.customer_id -> customers.customer_id
    - policies.vehicle_id -> vehicles.vehicle_id
    - claims.policy_id -> policies.policy_id
    - claims.customer_id -> customers.customer_id
    - payments.claim_id -> claims.claim_id
    - payments.policy_id -> policies.policy_id
    """
    ok = True

    checks = [
        ("policies", "customer_id", "customers", "customer_id"),
        ("policies", "vehicle_id", "vehicles", "vehicle_id"),
        ("claims", "policy_id", "policies", "policy_id"),
        ("claims", "customer_id", "customers", "customer_id"),
        ("payments", "claim_id", "claims", "claim_id"),
        ("payments", "policy_id", "policies", "policy_id"),
    ]

    for child_table, child_col, parent_table, parent_col in checks:
        if child_table not in data or parent_table not in data:
            log_error(f"Missing table for relationship check: {child_table} -> {parent_table}")
            ok = False
            continue

        child = data[child_table]
        parent = data[parent_table]

        if child_col not in child.columns or parent_col not in parent.columns:
            log_error(f"Missing column for relationship check: {child_table}.{child_col} -> {parent_table}.{parent_col}")
            ok = False
            continue

        valid_ids = set(parent[parent_col].dropna())
        orphans = child[~child[child_col].isin(valid_ids) & child[child_col].notna()]
        if len(orphans) > 0:
            log_error(
                f"Relationship violation: {child_table}.{child_col} has "
                f"{len(orphans)} values not found in {parent_table}.{parent_col}."
            )
            ok = False

    return ok


def validate_all_tables(data: dict) -> bool:
    """
    Validate all tables and their relationships.

    Parameters
    ----------
    data : dict
        Dictionary mapping table name -> DataFrame.

    Returns
    -------
    bool
        True if all validations pass.
    """
    log_pipeline_step("Starting validation of all tables...", logger)

    validators = {
        "customers": validate_customers,
        "vehicles": validate_vehicles,
        "policies": validate_policies,
        "claims": validate_claims,
        "payments": validate_payments,
    }

    all_ok = True
    for table, validator in validators.items():
        if table not in data:
            log_error(f"Table '{table}' missing from data.")
            all_ok = False
            continue
        result = validator(data[table])
        log_pipeline_step(f"Validation for '{table}': {'PASS' if result else 'FAIL'}", logger)
        all_ok = all_ok and result

    rel_ok = validate_relationships(data)
    log_pipeline_step(f"Relationship validation: {'PASS' if rel_ok else 'FAIL'}", logger)
    all_ok = all_ok and rel_ok

    log_pipeline_step(f"Overall validation result: {'PASS' if all_ok else 'FAIL'}", logger)
    return all_ok
