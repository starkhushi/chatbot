import pandas as pd
from datetime import datetime
from app.utils.custom_logging import custom_logger
from app.services.mongodb_service import mongodb_service

log = custom_logger() 



class MongoDBDataService:
    """
    Handles CSV data storage in MongoDB
    Collection: csv_data
    """

    def __init__(self):
        self.csv_collection = None

        if mongodb_service.db is not None:
            self.csv_collection = mongodb_service.db.csv_data
            log.info("MongoDB CSV data service initialized")
        else:
            log.warning("MongoDB not available for CSV storage")

    def save_csv_data(self, file_name: str, df: pd.DataFrame) -> bool:
        try:
            if self.csv_collection is None:
                return False


            records = df.to_dict("records")

            self.csv_collection.update_one(
                {"file_name": file_name},
                {
                    "$set": {
                        "file_name": file_name,
                        "data": records,
                        "row_count": len(records),
                        "updated_at": datetime.utcnow(),
                    }
                },
                upsert=True,
            )

            log.info(f"Saved {file_name} to MongoDB ({len(records)} rows)")
            return True

        except Exception as e:
            log.error(f"Error saving {file_name}: {e}")
            return False

    def load_csv_data(self, file_name: str):
        try:
            if self.csv_collection is None:
                return None

            doc = self.csv_collection.find_one({"file_name": file_name})
            if doc is None:
                return None

            return pd.DataFrame(doc["data"])

        except Exception as e:
            log.error(f"Error loading {file_name}: {e}")
            return None


mongodb_data_service = MongoDBDataService()
