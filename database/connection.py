import os
import pandas as pd

from config.setting import TRANSACTION_DATA_DIR, MASTER_DATA_DIR


def read_csv(path):
    """
    Read a CSV as a DataFrame. Returns an empty DataFrame with no
    columns if the file does not exist yet (caller should check schema).
    """

    if not os.path.exists(path):
        return pd.DataFrame()

    return pd.read_csv(path, dtype=str).fillna("")


def write_csv(path, df):
    """
    Atomically write a DataFrame to CSV (write to temp file, then rename)
    to avoid corrupting the file if the process is interrupted mid-write.
    """

    os.makedirs(os.path.dirname(path), exist_ok=True)

    tmp_path = f"{path}.tmp"

    df.to_csv(tmp_path, index=False)

    os.replace(tmp_path, path)


def append_row(path, columns, row: dict):
    """
    Append a single row (dict) to a CSV, creating it with the given
    columns if it doesn't exist yet.
    """

    df = read_csv(path)

    if df.empty:
        df = pd.DataFrame(columns=columns)

    row_df = pd.DataFrame([{col: str(row.get(col, "")) for col in columns}])

    df = pd.concat([df, row_df], ignore_index=True)

    write_csv(path, df)


def update_rows(path, columns, match: dict, updates: dict):
    """
    Update all rows matching `match` (column -> value) with `updates`
    (column -> value). Returns the number of rows updated.
    """

    df = read_csv(path)

    if df.empty:
        return 0

    mask = pd.Series([True] * len(df))

    for col, val in match.items():
        mask &= (df[col].astype(str) == str(val))

    updated = int(mask.sum())

    for col, val in updates.items():
        df.loc[mask, col] = str(val)

    write_csv(path, df)

    return updated


# --- Transaction data (mutable, case-lifecycle CSVs) ---

CUSTOMERS_FILE = MASTER_DATA_DIR / "customers.csv"
ORDERS_FILE = TRANSACTION_DATA_DIR / "orders.csv"
PRODUCTS_FILE = MASTER_DATA_DIR / "products.csv"
DEPARTMENTS_FILE = MASTER_DATA_DIR / "departments.csv"
WORKFLOW_TRANSITIONS_FILE = MASTER_DATA_DIR / "workflow_transitions.csv"

CASES_FILE = TRANSACTION_DATA_DIR / "cases.csv"
COMPLAINTS_FILE = TRANSACTION_DATA_DIR / "complaints.csv"
ENQUIRIES_FILE = TRANSACTION_DATA_DIR / "enquiries.csv"
EVIDENCE_REVIEWS_FILE = TRANSACTION_DATA_DIR / "evidence_reviews.csv"
HITL_REVIEWS_FILE = TRANSACTION_DATA_DIR / "hitl_reviews.csv"
DEPARTMENT_TASKS_FILE = TRANSACTION_DATA_DIR / "department_tasks.csv"
NOTIFICATIONS_FILE = TRANSACTION_DATA_DIR / "notifications.csv"
REFUNDS_FILE = TRANSACTION_DATA_DIR / "refunds.csv"
REPLACEMENTS_FILE = TRANSACTION_DATA_DIR / "replacements.csv"
VOUCHERS_FILE = TRANSACTION_DATA_DIR / "vouchers.csv"
AUDIT_LOGS_FILE = TRANSACTION_DATA_DIR / "audit_logs.csv"
