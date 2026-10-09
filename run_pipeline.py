"""
Pipeline Entry Point
====================
Runs the full motor insurance analytics pipeline:
load -> validate -> clean -> save.
"""

import os
import sys

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data_loader import load_all_data
from src.validation import validate_all_tables
from src.data_cleaner import clean_data, save_cleaned_data
from src.logger import setup_logger, log_pipeline_step, log_error

logger = setup_logger("run_pipeline")


def run_pipeline():
    """
    Execute the complete data pipeline.

    Steps
    -----
    1. Load raw data
    2. Validate all tables and relationships
    3. Clean data and create derived columns
    4. Save cleaned data
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    raw_dir = os.path.join(base_dir, "data", "raw")
    cleaned_dir = os.path.join(base_dir, "data", "cleaned")

    log_pipeline_step("=" * 70, logger)
    log_pipeline_step("MOTOR INSURANCE ANALYTICS PIPELINE STARTED", logger)
    log_pipeline_step("=" * 70, logger)

    try:
        # 1. Load
        log_pipeline_step("STEP 1: Loading raw data...", logger)
        data = load_all_data(raw_dir)
        log_pipeline_step(f"Loaded tables: {list(data.keys())}", logger)

        # 2. Validate
        log_pipeline_step("STEP 2: Validating tables and relationships...", logger)
        is_valid = validate_all_tables(data)
        if not is_valid:
            log_pipeline_step(
                "Validation reported issues — continuing with cleaning, but review the log.",
                logger,
            )
        else:
            log_pipeline_step("All validations passed.", logger)

        # 3. Clean
        log_pipeline_step("STEP 3: Cleaning data...", logger)
        data = clean_data(data)

        # 4. Save
        log_pipeline_step("STEP 4: Saving cleaned data...", logger)
        save_cleaned_data(data, cleaned_dir)

        log_pipeline_step("=" * 70, logger)
        log_pipeline_step("PIPELINE COMPLETED SUCCESSFULLY", logger)
        log_pipeline_step("=" * 70, logger)

    except Exception as e:
        log_error(f"Pipeline failed: {e}", logger)
        raise


if __name__ == "__main__":
    run_pipeline()
    