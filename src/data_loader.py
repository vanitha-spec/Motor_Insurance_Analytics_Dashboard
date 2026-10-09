"""
Data Loader Module
==================
Loads raw CSV tables into pandas DataFrames with relationship awareness.
"""

import os
import pandas as pd

from src.logger import setup_logger, log_pipeline_step, log_error

logger = setup_logger(__name__)

# Standard table names expected by the project
STANDARD_TABLES = ["customers", "vehicles", "policies", "claims", "payments"]


def check_file_exists(file_path: str) -> bool:
    """
    Check whether a file exists at the given path.

    Parameters
    ----------
    file_path : str
        Path to the file.

    Returns
    -------
    bool
        True if file exists, False otherwise.
    """
    exists = os.path.isfile(file_path)
    if not exists:
        log_error(f"File not found: {file_path}")
    return exists


def load_table(file_path: str) -> pd.DataFrame:
    """
    Load a single CSV file into a pandas DataFrame.

    Parameters
    ----------
    file_path : str
        Path to the CSV file.

    Returns
    -------
    pd.DataFrame
        Loaded DataFrame.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    """
    if not check_file_exists(file_path):
        raise FileNotFoundError(f"Required file not found: {file_path}")

    df = pd.read_csv(file_path)
    log_pipeline_step(f"Loaded table '{os.path.basename(file_path)}' with shape {df.shape}", logger)
    return df


def load_all_data(data_dir: str) -> dict:
    """
    Load all standard tables from the raw data directory.

    Parameters
    ----------
    data_dir : str
        Path to the directory containing raw CSV files.

    Returns
    -------
    dict
        Dictionary mapping table name -> DataFrame.

    Raises
    ------
    FileNotFoundError
        If any required file is missing.
    """
    data = {}
    missing = []

    for table in STANDARD_TABLES:
        file_path = os.path.join(data_dir, f"{table}.csv")
        if not check_file_exists(file_path):
            missing.append(table)
        else:
            data[table] = load_table(file_path)

    if missing:
        raise FileNotFoundError(
            f"Missing required tables: {missing}. "
            f"All of {STANDARD_TABLES} must be present in {data_dir}"
        )

    log_pipeline_step(f"All {len(data)} tables loaded successfully.", logger)
    return data
