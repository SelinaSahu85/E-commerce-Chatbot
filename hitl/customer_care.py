import pandas as pd
import uuid
from pathlib import Path

HITL_FILE = Path(
    "datasets/transaction_data/hitl_reviews.csv"
)


def create_review_request(query: str):

    review_id = f"HR-{uuid.uuid4().hex[:8].upper()}"

    if not HITL_FILE.exists():

        pd.DataFrame(
            columns=[
                "review_id",
                "query",
                "status",
                "human_response"
            ]
        ).to_csv(HITL_FILE, index=False)

    df = pd.read_csv(HITL_FILE)

    df.loc[len(df)] = {
        "review_id": review_id,
        "query": query,
        "status": "PENDING",
        "human_response": ""
    }

    df.to_csv(HITL_FILE, index=False)

    return review_id