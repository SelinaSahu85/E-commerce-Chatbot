import os
import shutil
import pandas as pd

from database.connection import (
    CASES_FILE,
    COMPLAINTS_FILE,
    ENQUIRIES_FILE,
    EVIDENCE_REVIEWS_FILE,
    HITL_REVIEWS_FILE,
    DEPARTMENT_TASKS_FILE,
    NOTIFICATIONS_FILE,
    REFUNDS_FILE,
    REPLACEMENTS_FILE,
    VOUCHERS_FILE,
    AUDIT_LOGS_FILE,
)

TABLE_COLUMNS = {
    CASES_FILE: [
        "case_id", "customer_id", "order_id", "case_type",
        "current_stage", "status", "opened_date", "closed_date",
    ],
    COMPLAINTS_FILE: [
        "case_id", "customer_id", "order_id", "product_id",
        "complaint_type", "complaint_text", "requested_resolution",
        "evidence_required", "recommended_resolution",
    ],
    ENQUIRIES_FILE: [
        "enquiry_id", "case_id", "customer_id", "query",
        "answer", "sources", "escalated",
    ],
    EVIDENCE_REVIEWS_FILE: [
        "evidence_id", "case_id", "evidence_type", "description",
        "result", "comments", "reviewed_by",
    ],
    HITL_REVIEWS_FILE: [
        "review_id", "query", "status", "human_response",
    ],
    DEPARTMENT_TASKS_FILE: [
        "task_id", "case_id", "department", "action",
        "resolution", "status", "notes", "created_date",
    ],
    NOTIFICATIONS_FILE: [
        "notification_id", "case_id", "customer_id", "message", "timestamp",
    ],
    # NOTE: the seeded refunds.csv shipped with the wrong (cases.csv) schema.
    # We repair it below in ensure_tables_exist().
    REFUNDS_FILE: [
        "refund_id", "case_id", "order_id", "customer_id",
        "amount", "status", "refund_date",
    ],
    REPLACEMENTS_FILE: [
        "replacement_id", "case_id", "order_id", "customer_id",
        "status", "replacement_date",
    ],
    VOUCHERS_FILE: [
        "voucher_id", "case_id", "customer_id", "amount", "status", "issued_date",
    ],
    AUDIT_LOGS_FILE: [
        "log_id", "case_id", "timestamp", "action", "user",
    ],
}


def ensure_tables_exist():
    """
    Creates any missing transaction CSVs with the correct headers, and
    repairs any file whose header doesn't match the expected schema
    (backing up the original next to it as *.bak).
    """

    for path, columns in TABLE_COLUMNS.items():

        os.makedirs(os.path.dirname(path), exist_ok=True)

        if not os.path.exists(path):
            pd.DataFrame(columns=columns).to_csv(path, index=False)
            continue

        existing_columns = list(pd.read_csv(path, nrows=0).columns)

        if existing_columns != columns:
            backup_path = f"{path}.bak"
            if not os.path.exists(backup_path):
                shutil.copy(path, backup_path)
            pd.DataFrame(columns=columns).to_csv(path, index=False)
