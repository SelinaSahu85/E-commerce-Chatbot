# tools/duplicate_checker.py

import pandas as pd
from pathlib import Path

COMPLAINT_FILE = Path("data/complaints.csv")


def check_duplicate_complaint(order_id):
    """
    Check whether an active complaint already exists
    for the given order.
    """

    if not COMPLAINT_FILE.exists():
        return None

    df = pd.read_csv(COMPLAINT_FILE)

    existing = df[
        (df["order_id"] == order_id)
        & (df["status"] != "CLOSED")
    ]

    if existing.empty:
        return None

    row = existing.iloc[0]

    return {
        "complaint_id": row["complaint_id"],
        "status": row["status"]
    }