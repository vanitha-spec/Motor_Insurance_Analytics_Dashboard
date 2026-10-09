"""
Data Cleaner Module
===================
Provides reusable cleaning functions and derived column creation
for the motor insurance dataset.
"""

import os
import numpy as np
import pandas as pd

from src.logger import setup_logger, log_pipeline_step

logger = setup_logger(__name__)

# Columns that should be treated as dates per table
DATE_COLUMNS = {
    "customers": ["date_of_birth"],
    "policies": ["policy_start_date", "policy_end_date"],
    "claims": ["claim_date", "accident_date", "approval_date", "settlement_date"],
    "payments": ["payment_date"],
}

# Text columns to strip whitespace and title-case
TEXT_COLUMNS = {
    "customers": ["customer_name", "gender", "city", "state", "occupation"],
    "vehicles": ["vehicle_type", "vehicle_make", "vehicle_model", "fuel_type"],
    "policies": ["policy_type", "policy_status", "payment_frequency"],
    "claims": ["claim_type", "accident_location", "claim_status", "damage_severity"],
    "payments": ["payment_status", "payment_method"],
}

# Numeric columns to coerce and clean
NUMERIC_COLUMNS = {
    "customers": ["age"],
    "vehicles": ["vehicle_year", "vehicle_value"],
    "policies": ["premium_amount", "coverage_amount"],
    "claims": ["claim_amount"],
    "payments": ["payment_amount"],
}


def _ensure_datetime(df: pd.DataFrame, columns: list) -> pd.DataFrame:
    """
    Convert the given columns to datetime if they are not already.

    Safe to call on columns that are already datetime. Invalid values
    become NaT instead of raising an error.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame to modify (should already be a copy).
    columns : list
        Column names to convert, if present.

    Returns
    -------
    pd.DataFrame
        DataFrame with the requested columns as datetime64.
    """
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def handle_missing_values(data: dict) -> dict:
    """
    Handle missing values across all tables.

    Strategy:
    - Numeric columns: fill with median (or 0 if all null).
    - Categorical/text columns: fill with 'Unknown'.
    - Date columns: leave as NaT (missing dates are semantically meaningful).

    Parameters
    ----------
    data : dict
        Dictionary of DataFrames.

    Returns
    -------
    dict
        Cleaned dictionary of DataFrames.
    """
    log_pipeline_step("Handling missing values...", logger)

    for table, df in data.items():
        df = df.copy()

        # Numeric columns
        for col in NUMERIC_COLUMNS.get(table, []):
            if col in df.columns:
                if df[col].isna().all():
                    df[col] = df[col].fillna(0)
                else:
                    df[col] = df[col].fillna(df[col].median())

        # Text/categorical columns
        for col in TEXT_COLUMNS.get(table, []):
            if col in df.columns:
                df[col] = df[col].fillna("Unknown")

        data[table] = df

    return data


def remove_duplicates(data: dict) -> dict:
    """
    Remove duplicate rows from each table.

    Parameters
    ----------
    data : dict
        Dictionary of DataFrames.

    Returns
    -------
    dict
        Deduplicated DataFrames.
    """
    log_pipeline_step("Removing duplicates...", logger)

    for table, df in data.items():
        before = len(df)
        df = df.drop_duplicates().reset_index(drop=True)
        after = len(df)
        if before != after:
            log_pipeline_step(f"[{table}] Removed {before - after} duplicate rows.", logger)
        data[table] = df

    return data


def clean_text_columns(data: dict) -> dict:
    """
    Strip whitespace and standardize case for text columns.

    Parameters
    ----------
    data : dict
        Dictionary of DataFrames.

    Returns
    -------
    dict
        Cleaned DataFrames.
    """
    log_pipeline_step("Cleaning text columns...", logger)

    for table, df in data.items():
        df = df.copy()
        for col in TEXT_COLUMNS.get(table, []):
            if col in df.columns:
                df[col] = (
                    df[col]
                    .astype(str)
                    .str.strip()
                    .str.title()
                    .replace({"Nan": "Unknown", "None": "Unknown"})
                )
        data[table] = df

    return data


def clean_date_columns(data: dict) -> dict:
    """
    Parse date columns into pandas datetime objects.

    Parameters
    ----------
    data : dict
        Dictionary of DataFrames.

    Returns
    -------
    dict
        DataFrames with parsed dates.
    """
    log_pipeline_step("Cleaning date columns...", logger)

    for table, df in data.items():
        df = df.copy()
        df = _ensure_datetime(df, DATE_COLUMNS.get(table, []))
        data[table] = df

    return data


def validate_numeric_columns(data: dict) -> dict:
    """
    Coerce numeric columns and ensure non-negative values where required.

    Parameters
    ----------
    data : dict
        Dictionary of DataFrames.

    Returns
    -------
    dict
        Cleaned DataFrames.
    """
    log_pipeline_step("Validating numeric columns...", logger)

    for table, df in data.items():
        df = df.copy()
        for col in NUMERIC_COLUMNS.get(table, []):
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
                # Replace negatives with NaN then fill with median
                if col != "vehicle_year":  # vehicle_year can theoretically be old but positive
                    neg_mask = df[col] < 0
                    if neg_mask.any():
                        df.loc[neg_mask, col] = np.nan
                if df[col].isna().all():
                    df[col] = df[col].fillna(0)
                else:
                    df[col] = df[col].fillna(df[col].median())
        data[table] = df

    return data


def validate_business_rules(data: dict) -> dict:
    """
    Apply business rule filters to remove logically invalid rows.

    Rules:
    - Policies: start_date <= end_date
    - Claims: accident_date <= claim_date
    - Claims: approval_date >= claim_date (when present)
    - Claims: settlement_date >= claim_date (when present)

    Parameters
    ----------
    data : dict
        Dictionary of DataFrames.

    Returns
    -------
    dict
        Filtered DataFrames.
    """
    log_pipeline_step("Validating business rules...", logger)

    # Policies: start <= end
    if "policies" in data:
        df = data["policies"].copy()
        df = _ensure_datetime(df, ["policy_start_date", "policy_end_date"])
        mask = (
            df["policy_start_date"].isna()
            | df["policy_end_date"].isna()
            | (df["policy_start_date"] <= df["policy_end_date"])
        )
        removed = (~mask).sum()
        if removed > 0:
            log_pipeline_step(f"[policies] Removed {removed} rows with start > end.", logger)
        data["policies"] = df[mask].reset_index(drop=True)

    # Claims: accident <= claim date
    if "claims" in data:
        df = data["claims"].copy()
        df = _ensure_datetime(
            df, ["claim_date", "accident_date", "approval_date", "settlement_date"]
        )
        mask = (
            df["accident_date"].isna()
            | df["claim_date"].isna()
            | (df["accident_date"] <= df["claim_date"])
        )
        removed = (~mask).sum()
        if removed > 0:
            log_pipeline_step(f"[claims] Removed {removed} rows with accident > claim.", logger)
        data["claims"] = df[mask].reset_index(drop=True)

        # approval_date >= claim_date
        df = data["claims"].copy()
        mask = (
            df["approval_date"].isna()
            | df["claim_date"].isna()
            | (df["approval_date"] >= df["claim_date"])
        )
        removed = (~mask).sum()
        if removed > 0:
            log_pipeline_step(f"[claims] Removed {removed} rows with approval < claim.", logger)
        data["claims"] = df[mask].reset_index(drop=True)

        # settlement_date >= claim_date
        df = data["claims"].copy()
        mask = (
            df["settlement_date"].isna()
            | df["claim_date"].isna()
            | (df["settlement_date"] >= df["claim_date"])
        )
        removed = (~mask).sum()
        if removed > 0:
            log_pipeline_step(f"[claims] Removed {removed} rows with settlement < claim.", logger)
        data["claims"] = df[mask].reset_index(drop=True)

    return data


def create_derived_columns(data: dict) -> dict:
    """
    Create derived columns across tables as defined in the project spec.

    Derived columns:
    - policy_duration_days
    - customer_age
    - vehicle_age
    - claim_processing_days
    - claim_settlement_days
    - claim_to_premium_ratio
    - claim_to_coverage_ratio
    - paid_claim_ratio
    - policy_active_flag

    Date columns are converted to datetime inside this function, so it can
    be called directly (for example in tests) without running
    clean_date_columns() first.

    Parameters
    ----------
    data : dict
        Dictionary of DataFrames.

    Returns
    -------
    dict
        DataFrames with derived columns added.
    """
    log_pipeline_step("Creating derived columns...", logger)

    # ---- policies: policy_duration_days, policy_active_flag
    if "policies" in data:
        df = data["policies"].copy()
        df = _ensure_datetime(df, ["policy_start_date", "policy_end_date"])

        df["policy_duration_days"] = (
            df["policy_end_date"] - df["policy_start_date"]
        ).dt.days

        # policy_active_flag: 1 if status is Active, else 0
        if "policy_status" in df.columns:
            df["policy_active_flag"] = (df["policy_status"] == "Active").astype(int)
        else:
            df["policy_active_flag"] = 0

        data["policies"] = df

    # ---- customers: customer_age (prefer computed from date_of_birth)
    if "customers" in data:
        df = data["customers"].copy()
        df = _ensure_datetime(df, ["date_of_birth"])
        today = pd.Timestamp.today()
        if "date_of_birth" in df.columns:
            computed_age = ((today - df["date_of_birth"]).dt.days / 365.25).round()
            # Use computed age if valid, else keep existing
            df["customer_age"] = computed_age.where(computed_age.notna(), df.get("age"))
            df["customer_age"] = (
                pd.to_numeric(df["customer_age"], errors="coerce").fillna(0).astype(int)
            )
        else:
            df["customer_age"] = (
                pd.to_numeric(df.get("age", 0), errors="coerce").fillna(0).astype(int)
            )
        data["customers"] = df

    # ---- vehicles: vehicle_age
    if "vehicles" in data:
        df = data["vehicles"].copy()
        current_year = pd.Timestamp.today().year
        if "vehicle_year" in df.columns:
            df["vehicle_age"] = current_year - pd.to_numeric(df["vehicle_year"], errors="coerce")
            df["vehicle_age"] = df["vehicle_age"].fillna(df["vehicle_age"].median())
        else:
            df["vehicle_age"] = 0
        data["vehicles"] = df

    # ---- claims: claim_processing_days, claim_settlement_days
    if "claims" in data:
        df = data["claims"].copy()
        df = _ensure_datetime(
            df, ["claim_date", "accident_date", "approval_date", "settlement_date"]
        )
        df["claim_processing_days"] = (
            df["approval_date"] - df["claim_date"]
        ).dt.days
        df["claim_settlement_days"] = (
            df["settlement_date"] - df["claim_date"]
        ).dt.days
        data["claims"] = df

    # ---- claim_to_premium_ratio, claim_to_coverage_ratio
    # Need to join claims -> policies
    if "claims" in data and "policies" in data:
        claims = data["claims"].copy()
        policies = data["policies"][
            ["policy_id", "premium_amount", "coverage_amount"]
        ].copy()

        claims = claims.merge(policies, on="policy_id", how="left")

        claims["claim_to_premium_ratio"] = np.where(
            claims["premium_amount"] > 0,
            claims["claim_amount"] / claims["premium_amount"],
            np.nan,
        )
        claims["claim_to_coverage_ratio"] = np.where(
            claims["coverage_amount"] > 0,
            claims["claim_amount"] / claims["coverage_amount"],
            np.nan,
        )
        data["claims"] = claims

    # ---- paid_claim_ratio (payments aggregated per claim)
    if "payments" in data and "claims" in data:
        payments = data["payments"].copy()
        # Aggregate payment amount per claim
        pay_agg = (
            payments.groupby("claim_id", as_index=False)["payment_amount"]
            .sum()
            .rename(columns={"payment_amount": "total_paid_amount"})
        )
        claims = data["claims"].copy()
        claims = claims.merge(pay_agg, on="claim_id", how="left")
        claims["total_paid_amount"] = claims["total_paid_amount"].fillna(0)
        claims["paid_claim_ratio"] = np.where(
            claims["claim_amount"] > 0,
            claims["total_paid_amount"] / claims["claim_amount"],
            np.nan,
        )
        data["claims"] = claims

    return data


def clean_data(data: dict) -> dict:
    """
    Run the full cleaning pipeline on the raw data.

    Parameters
    ----------
    data : dict
        Raw DataFrames.

    Returns
    -------
    dict
        Cleaned DataFrames with derived columns.
    """
    log_pipeline_step("=" * 60, logger)
    log_pipeline_step("STARTING DATA CLEANING PIPELINE", logger)
    log_pipeline_step("=" * 60, logger)

    data = handle_missing_values(data)
    data = remove_duplicates(data)
    data = clean_text_columns(data)
    data = clean_date_columns(data)
    data = validate_numeric_columns(data)
    data = validate_business_rules(data)
    data = create_derived_columns(data)

    log_pipeline_step("=" * 60, logger)
    log_pipeline_step("DATA CLEANING PIPELINE COMPLETE", logger)
    log_pipeline_step("=" * 60, logger)

    return data


def save_cleaned_data(data: dict, output_dir: str) -> None:
    """
    Save cleaned DataFrames to CSV files in the output directory.

    Parameters
    ----------
    data : dict
        Cleaned DataFrames.
    output_dir : str
        Directory where cleaned CSVs will be written.
    """
    os.makedirs(output_dir, exist_ok=True)

    for table, df in data.items():
        out_path = os.path.join(output_dir, f"{table}_cleaned.csv")
        df.to_csv(out_path, index=False)
        log_pipeline_step(f"Saved cleaned table: {out_path} (shape={df.shape})", logger)
        