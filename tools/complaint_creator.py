# tools/complaint_creator.py

import uuid
import pandas as pd
from pathlib import Path

COMPLAINT_FILE = Path("data/complaints.csv")


def create_complaint(
    order_id,
    issue_type,
    description
):
    """
    Create new complaint record.
    """

    complaint_id = f"CMP-{uuid.uuid4().hex[:8].upper()}"

    complaint_data = {
        "complaint_id": complaint_id,
        "order_id": order_id,
        "issue_type": issue_type,
        "description": description,
        "status": "OPEN"
    }

    df = pd.DataFrame([complaint_data])

    file_exists = COMPLAINT_FILE.exists()

    df.to_csv(
        COMPLAINT_FILE,
        mode="a",
        header=not file_exists,
        index=False
    )

    return complaint_data
