from langchain_core.tools import tool
from app.services.data_manager import data_manager

@tool
def search_accounting(query: str) -> str:
    """Search accounting/financial data across all CSV files. 
    
    Searches for any matching text in:
    - Asset.csv: Assets and equipment
    - COA_final.csv: Chart of accounts
    - debt_final.csv: Debt information
    - Human_Capital_final.csv: Employee data (names, salaries, departments, etc.)
    - profit&Loss_final.csv: Profit and loss
    - transaction.csv: Transactions
    
    Examples:
    - "amit kumar" or "amit" → finds employee records
    - "base salary" → finds salary information
    - "gurgaon" → finds location-based records
    - Use employee names, amounts, dates, departments, or any relevant keywords.
    """
    try:
        return data_manager.search_accounting(query, None)
    except Exception as e:
        return f"Error: {str(e)}"

@tool
def search_support(query: str) -> str:
    """
    Search the smart metering support knowledge base for relevant customer queries and evidence-based answers.

    This tool runs a combined keyword and simple semantic-style search over the support CSV and returns
    up to 3 relevance-ranked chunks. Each chunk contains up to 5 rows, and each row includes:
    - Customer_Query
    - Evidence_Based_Answer
    - Category

    Intended usage (by the LLM agent):
    - ALWAYS call this tool first for any smart metering support question
    - Pass the user's full question as the `query`
    - Read all returned chunks and pick the single most relevant row
    - Use the row's Evidence_Based_Answer as the core of your reply, paraphrasing in natural language
    - Use Category (e.g., Billing & Accuracy, Reliability & Outages) to frame the explanation

    If the result string contains "No matching support records found.", the agent should:
    - Tell the user that no exact match exists in the knowledge base, and
    - Either ask a brief clarifying question or give only high-level, non-fabricated guidance.
    """
    try:
        return data_manager.search_support(query)
    except Exception as e:
        return f"Error: {str(e)}"

ACCOUNTING_TOOLS = [search_accounting]
SUPPORT_TOOLS = [search_support]

