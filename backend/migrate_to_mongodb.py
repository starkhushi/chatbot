#!/usr/bin/env python3
"""
Migrate CSV data (accounting + support) into MongoDB
Run once before starting the backend
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv(".env")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "app"))

from app.services.data_manager import data_manager
from app.services.mongodb_data_service import mongodb_data_service
from app.utils.custom_logging import custom_logger


log = custom_logger()


def migrate_csv_data():
    if mongodb_data_service.csv_collection is None:
        log.error("❌ MongoDB not connected. Is the MongoDB container running?")
        return False

    log.info("✅ MongoDB connected")
    log.info("📊 Loading CSV data...")

    # Load CSVs into memory
    data_manager.load_accounting_data()
    data_manager.load_support_data()

    saved = 0

    # Save accounting CSVs
    for file_name, df in data_manager.accounting_data.items():
        if mongodb_data_service.save_csv_data(file_name, df):
            saved += 1

    # Save support CSV
    if data_manager.support_data is not None:
        if mongodb_data_service.save_csv_data(
            "Smart_Metering_Support_Dataset.csv",
            data_manager.support_data
        ):
            saved += 1

    log.info(f"✅ Migration completed. {saved} CSV files saved.")
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("MongoDB CSV Migration Script")
    print("=" * 60)

    success = migrate_csv_data()

    if success:
        print("🎉 CSV data successfully migrated to MongoDB")
    else:
        print("❌ Migration failed")
