# /*import os
# import pandas as pd
# from typing import Dict, List
# from app.utils.custom_logging import custom_logger
# from app.services.mongodb_data_service import mongodb_data_service

# log = custom_logger()

# class DataManager:
#     def __init__(self):
#         self.accounting_data: Dict[str, pd.DataFrame] = {}
#         self.support_data: pd.DataFrame = None
#         self.data_dir = os.path.join(os.path.dirname(__file__), "../../data")
    
#     def load_accounting_data(self):
#         try:
#             accounting_dir = os.path.join(self.data_dir, "accounting")
#             files = ["Asset.csv", "COA_final.csv", "debt_final.csv", 
#                     "Human_Capital_final.csv", "profit&Loss_final.csv", "transaction.csv"]
#             for file in files:
#                 filepath = os.path.join(accounting_dir, file)
#                 if os.path.exists(filepath):
#                     self.accounting_data[file] = pd.read_csv(filepath)
#                     log.info(f"Loaded {file}: {len(self.accounting_data[file])} rows")
#         except Exception as e:
#             log.error(f"Error loading accounting data: {e}")
#     # def load_accounting_data(self):
#     #     files = [
#     #         "Asset.csv",
#     #         "COA_final.csv",
#     #         "debt_final.csv",
#     #         "Human_Capital_final.csv",
#     #         "profit&Loss_final.csv",
#     #         "transaction.csv",
#     #     ]

#     #     for file in files:
#     #         df = mongodb_data_service.load_csv_data(file)
#     #         if df is None:
#     #             raise RuntimeError(f"Accounting data missing in MongoDB: {file}")
#     #         self.accounting_data[file] = df
#     #         log.info(f"Loaded {file} from MongoDB: {len(df)} rows")

    
#     def load_support_data(self):
#         try:
#             support_file = os.path.join(self.data_dir, "support", "Smart_Metering_Support_Dataset.csv")
#             if os.path.exists(support_file):
#                 self.support_data = pd.read_csv(support_file)
#                 log.info(f"Loaded support data: {len(self.support_data)} rows")
#         except Exception as e:
#             log.error(f"Error loading support data: {e}")
#     # def load_support_data(self):
#     #     df = mongodb_data_service.load_csv_data("Smart_Metering_Support_Dataset.csv")
#     #     if df is None:
#     #         raise RuntimeError("Support data missing in MongoDB")
#     #     self.support_data = df
#     #     log.info(f"Loaded support data from MongoDB: {len(df)} rows")

    
#     def search_accounting(self, query: str, file_name: str = None) -> str:
#         try:
#             # Split query into keywords for better matching (keep words longer than 2 chars)
#             keywords = [q.strip() for q in query.lower().split() if len(q.strip()) > 2]
#             if not keywords:
#                 keywords = [query.lower().strip()]
            
#             # Helper function to check if row matches keywords
#             def row_matches_keywords(row, search_keywords):
#                 row_text = ' '.join([str(v).lower() for v in row.values if pd.notna(v)])
#                 return any(kw in row_text for kw in search_keywords)
            
#             if file_name and file_name in self.accounting_data:
#                 df = self.accounting_data[file_name]
#                 mask = df.apply(lambda row: row_matches_keywords(row, keywords), axis=1)
#                 results = df[mask]
#                 if not results.empty:
#                     return f"\n{file_name}:\n{results.to_string(index=False)}\n"
#                 return f"No matching records found in {file_name}."
            
#             # Search across all files
#             all_results = []
#             for name, df in self.accounting_data.items():
#                 mask = df.apply(lambda row: row_matches_keywords(row, keywords), axis=1)
#                 results = df[mask]
#                 if not results.empty:
#                     all_results.append(f"\n{name}:\n{results.to_string(index=False)}\n")
            
#             if all_results:
#                 return "\n".join(all_results)
            
#             # If no results with all keywords, try with first keyword only
#             if len(keywords) > 1:
#                 for name, df in self.accounting_data.items():
#                     mask = df.apply(lambda row: row_matches_keywords(row, [keywords[0]]), axis=1)
#                     results = df[mask]
#                     if not results.empty:
#                         all_results.append(f"\n{name}:\n{results.to_string(index=False)}\n")
#                 if all_results:
#                     return "\n".join(all_results)
            
#             return "No matching records found. Try searching with different keywords like employee name, department, amount, or date."
#         except Exception as e:
#             log.error(f"Error searching accounting data: {e}")
#             return f"Error: {str(e)}"
    
#     def search_support(self, query: str) -> str:
#         try:
#             if self.support_data is None:
#                 return "Support data not loaded."
#             results = self.support_data[
#                 self.support_data['Customer_Query'].str.contains(query, case=False, na=False) |
#                 self.support_data['Evidence_Based_Answer'].str.contains(query, case=False, na=False)
#             ]
#             if results.empty:
#                 return "No matching support records found."
#             return results[['Customer_Query', 'Evidence_Based_Answer', 'Category']].to_string()
#         except Exception as e:
#             log.error(f"Error searching support data: {e}")
#             return f"Error: {str(e)}"

# data_manager = DataManager()
# data_manager.load_accounting_data()
# data_manager.load_support_data()

import os
import pandas as pd
from typing import Dict, List
from app.utils.custom_logging import custom_logger
from app.services.mongodb_data_service import mongodb_data_service

log = custom_logger()

class DataManager:
    def __init__(self):
        self.accounting_data: Dict[str, pd.DataFrame] = {}
        self.support_data: pd.DataFrame = None
        # self.data_dir = os.path.join(os.path.dirname(__file__), "../../data")
    
    # def load_accounting_data(self):
    #     try:
    #         accounting_dir = os.path.join(self.data_dir, "accounting")
    #         files = ["Asset.csv", "COA_final.csv", "debt_final.csv", 
    #                 "Human_Capital_final.csv", "profit&Loss_final.csv", "transaction.csv"]
    #         for file in files:
    #             filepath = os.path.join(accounting_dir, file)
    #             if os.path.exists(filepath):
    #                 self.accounting_data[file] = pd.read_csv(filepath)
    #                 log.info(f"Loaded {file}: {len(self.accounting_data[file])} rows")
    #     except Exception as e:
    #         log.error(f"Error loading accounting data: {e}")
    def load_accounting_data(self):
        files = [
            "Asset.csv",
            "COA_final.csv",
            "debt_final.csv",
            "Human_Capital_final.csv",
            "profit&Loss_final.csv",
            "transaction.csv",
        ]

        for file in files:
            df = mongodb_data_service.load_csv_data(file)
            if df is None:
                raise RuntimeError(f"Accounting data missing in MongoDB: {file}")
            self.accounting_data[file] = df
            log.info(f"Loaded {file} from MongoDB: {len(df)} rows")

    
    # def load_support_data(self):
    #     try:
    #         support_file = os.path.join(self.data_dir, "support", "Smart_Metering_Support_Dataset.csv")
    #         if os.path.exists(support_file):
    #             self.support_data = pd.read_csv(support_file)
    #             log.info(f"Loaded support data: {len(self.support_data)} rows")
    #     except Exception as e:
    #         log.error(f"Error loading support data: {e}")
    def load_support_data(self):
        df = mongodb_data_service.load_csv_data("Smart_Metering_Support_Dataset.csv")
        if df is None:
            raise RuntimeError("Support data missing in MongoDB")
        self.support_data = df
        log.info(f"Loaded support data from MongoDB: {len(df)} rows")

    
    def search_accounting(self, query: str, file_name: str = None) -> str:
        try:
            # Split query into keywords for better matching (keep words longer than 2 chars)
            keywords = [q.strip() for q in query.lower().split() if len(q.strip()) > 2]
            if not keywords:
                keywords = [query.lower().strip()]
            
            # Helper function to check if row matches keywords
            def row_matches_keywords(row, search_keywords):
                row_text = ' '.join([str(v).lower() for v in row.values if pd.notna(v)])
                return any(kw in row_text for kw in search_keywords)
            
            if file_name and file_name in self.accounting_data:
                df = self.accounting_data[file_name]
                mask = df.apply(lambda row: row_matches_keywords(row, keywords), axis=1)
                results = df[mask]
                print("Search accounting result:",results)
                if not results.empty:
                    return f"\n{file_name}:\n{results.to_string(index=False)}\n"
                return f"No matching records found in {file_name}."
            
            # Search across all files
            all_results = []
            for name, df in self.accounting_data.items():
                mask = df.apply(lambda row: row_matches_keywords(row, keywords), axis=1)
                results = df[mask]
                if not results.empty:
                    all_results.append(f"\n{name}:\n{results.to_string(index=False)}\n")
            
            if all_results:
                return "\n".join(all_results)
            print("All result before keyword search:",all_results)
            # If no results with all keywords, try with first keyword only
            if len(keywords) > 1:
                for name, df in self.accounting_data.items():
                    mask = df.apply(lambda row: row_matches_keywords(row, [keywords[0]]), axis=1)
                    results = df[mask]
                    if not results.empty:
                        all_results.append(f"\n{name}:\n{results.to_string(index=False)}\n")
                if all_results:
                    return "\n".join(all_results)
            print("All result after keyword search:",all_results)
            
            return "No matching records found. Try searching with different keywords like employee name, department, amount, or date."
        except Exception as e:
            log.error(f"Error searching accounting data: {e}")
            return f"Error: {str(e)}"
    
    def search_support(self, query: str) -> str:
        try:
            if self.support_data is None:
                return "Support data not loaded."

            df = self.support_data.copy()

            if df.empty:
                return "Support data is empty."

            # Normalize text for simple semantic + keyword style matching
            def normalize(text: str) -> str:
                if pd.isna(text):
                    return ""
                return str(text).lower()

            query_norm = normalize(query)
            if not query_norm.strip():
                return "No matching support records found."

            # Build keyword list (words longer than 2 chars)
            keywords = [w for w in query_norm.split() if len(w) > 2]
            if not keywords:
                keywords = [query_norm.strip()]

            def score_row(row) -> float:
                """Combined keyword + simple semantic-style overlap score for a single row."""
                text = normalize(row.get("Customer_Query", "")) + " " + normalize(
                    row.get("Evidence_Based_Answer", "")
                )
                if not text:
                    return 0.0

                # Keyword score: count of distinct keywords found
                keyword_score = sum(1 for kw in keywords if kw in text)

                # Simple semantic-style score: token overlap ratio
                row_tokens = set(t for t in text.split() if len(t) > 2)
                query_tokens = set(keywords)
                if not row_tokens or not query_tokens:
                    semantic_score = 0.0
                else:
                    intersection = len(row_tokens & query_tokens)
                    union = len(row_tokens | query_tokens)
                    semantic_score = intersection / union if union > 0 else 0.0

                # Weight keyword hits a bit more, but include semantic overlap
                return keyword_score + semantic_score

            df["__score"] = df.apply(score_row, axis=1)

            # Keep only rows with some match signal
            matched = df[df["__score"] > 0].sort_values("__score", ascending=False)
            if matched.empty:
                return "No matching support records found."

            # Take top 3 chunks; 1 chunk = up to 5 rows
            top_rows = matched.head(15)[["Customer_Query", "Evidence_Based_Answer", "Category", "__score"]]

            chunks: List[str] = []
            chunk_size = 5
            for i in range(0, len(top_rows), chunk_size):
                chunk_df = top_rows.iloc[i : i + chunk_size].copy()
                # Hide internal score from final table but keep it in text title
                max_score = chunk_df["__score"].max()
                display_df = chunk_df.drop(columns=["__score"])
                chunk_index = len(chunks) + 1
                chunk_text = f"\n=== Chunk {chunk_index} (approx. relevance score: {max_score:.2f}) ===\n"
                chunk_text += display_df.to_string(index=False)
                chunks.append(chunk_text)
                if len(chunks) >= 3:
                    break

            return "\n".join(chunks)
        except Exception as e:
            log.error(f"Error searching support data: {e}")
            return f"Error: {str(e)}"

data_manager = DataManager()
data_manager.load_accounting_data()
data_manager.load_support_data()

