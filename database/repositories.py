import uuid
from datetime import datetime

from database.connection import (
    read_csv, append_row, update_rows,
    CUSTOMERS_FILE, ORDERS_FILE, PRODUCTS_FILE, DEPARTMENTS_FILE,
    WORKFLOW_TRANSITIONS_FILE,
    CASES_FILE, COMPLAINTS_FILE, ENQUIRIES_FILE, EVIDENCE_REVIEWS_FILE,
    HITL_REVIEWS_FILE, DEPARTMENT_TASKS_FILE, NOTIFICATIONS_FILE,
    REFUNDS_FILE, REPLACEMENTS_FILE, VOUCHERS_FILE, AUDIT_LOGS_FILE,
)
from database.schema import TABLE_COLUMNS


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _today():
    return datetime.now().strftime("%Y-%m-%d")


class BaseRepository:

    FILE = None

    @classmethod
    def _columns(cls):
        return TABLE_COLUMNS[cls.FILE]

    @classmethod
    def all(cls):
        return read_csv(cls.FILE)

    @classmethod
    def create(cls, row: dict):
        append_row(cls.FILE, cls._columns(), row)
        return row

    @classmethod
    def update(cls, match: dict, updates: dict):
        return update_rows(cls.FILE, cls._columns(), match, updates)

    @classmethod
    def find_by(cls, **match):
        df = cls.all()

        if df.empty:
            return df

        mask = None

        for col, val in match.items():
            col_mask = (df[col].astype(str) == str(val))
            mask = col_mask if mask is None else (mask & col_mask)

        return df[mask] if mask is not None else df

    @classmethod
    def get(cls, **match):
        rows = cls.find_by(**match)
        if rows.empty:
            return None
        return rows.iloc[0].to_dict()


# --- Read-only master/reference data ---

class CustomerRepository(BaseRepository):
    FILE = CUSTOMERS_FILE

    @classmethod
    def get_by_id(cls, customer_id):
        return cls.get(customer_id=customer_id)


class OrderRepository(BaseRepository):
    FILE = ORDERS_FILE

    @classmethod
    def get_by_id(cls, order_id):
        return cls.get(order_id=order_id)


class ProductRepository(BaseRepository):
    FILE = PRODUCTS_FILE

    @classmethod
    def get_by_id(cls, product_id):
        return cls.get(product_id=product_id)


class DepartmentRepository(BaseRepository):
    FILE = DEPARTMENTS_FILE


class WorkflowTransitionRepository(BaseRepository):
    FILE = WORKFLOW_TRANSITIONS_FILE

    @classmethod
    def next_step(cls, resolution: str, current_stage: str):
        """
        Looks up datasets/master_data/workflow_transitions.csv for the row
        matching (resolution, current_stage) and returns it as a dict, or
        None if there's no such transition defined.
        """

        rows = cls.find_by(resolution=resolution, current_stage=current_stage)

        if rows.empty:
            return None

        return rows.iloc[0].to_dict()


# --- Case lifecycle (mutable transaction data) ---

class CaseRepository(BaseRepository):
    FILE = CASES_FILE

    @classmethod
    def get_by_id(cls, case_id):
        return cls.get(case_id=case_id)

    @classmethod
    def create_case(cls, customer_id, order_id, case_type, current_stage="Open", status="Open"):

        case_id = f"CASE{uuid.uuid4().hex[:8].upper()}"

        row = {
            "case_id": case_id,
            "customer_id": customer_id,
            "order_id": order_id or "",
            "case_type": case_type,
            "current_stage": current_stage,
            "status": status,
            "opened_date": _today(),
            "closed_date": "",
        }

        cls.create(row)

        return row

    @classmethod
    def update_stage(cls, case_id, current_stage=None, status=None):

        updates = {}

        if current_stage is not None:
            updates["current_stage"] = current_stage

        if status is not None:
            updates["status"] = status

        if status == "Closed":
            updates["closed_date"] = _today()

        cls.update({"case_id": case_id}, updates)

    @classmethod
    def open_cases_for_order(cls, order_id, exclude_case_id=None):
        rows = cls.find_by(order_id=order_id)

        if rows.empty:
            return rows

        rows = rows[rows["status"] != "Closed"]

        if exclude_case_id:
            rows = rows[rows["case_id"] != exclude_case_id]

        return rows


class ComplaintRepository(BaseRepository):
    FILE = COMPLAINTS_FILE

    @classmethod
    def get_by_case(cls, case_id):
        return cls.get(case_id=case_id)

    @classmethod
    def set_recommended_resolution(cls, case_id, resolution_type):
        cls.update({"case_id": case_id}, {"recommended_resolution": resolution_type})


class EnquiryRepository(BaseRepository):
    FILE = ENQUIRIES_FILE

    @classmethod
    def create_enquiry(cls, case_id, customer_id, query, answer="", sources=None, escalated=False):

        enquiry_id = f"ENQ{uuid.uuid4().hex[:8].upper()}"

        row = {
            "enquiry_id": enquiry_id,
            "case_id": case_id,
            "customer_id": customer_id,
            "query": query,
            "answer": answer,
            "sources": "; ".join(sources or []),
            "escalated": str(bool(escalated)),
        }

        cls.create(row)

        return row


class EvidenceRepository(BaseRepository):
    FILE = EVIDENCE_REVIEWS_FILE

    @classmethod
    def create_pending(cls, case_id, evidence_type, description=""):

        evidence_id = f"EV{uuid.uuid4().hex[:8].upper()}"

        row = {
            "evidence_id": evidence_id,
            "case_id": case_id,
            "evidence_type": evidence_type,
            "description": description,
            "result": "Pending",
            "comments": "",
            "reviewed_by": "",
        }

        cls.create(row)

        return row

    @classmethod
    def record_decision(cls, evidence_id, result, comments, reviewed_by):
        cls.update(
            {"evidence_id": evidence_id},
            {"result": result, "comments": comments, "reviewed_by": reviewed_by},
        )

    @classmethod
    def pending(cls):
        rows = cls.all()
        if rows.empty:
            return rows
        return rows[rows["result"] == "Pending"]

    @classmethod
    def latest_for_case(cls, case_id):
        rows = cls.find_by(case_id=case_id)
        if rows.empty:
            return None
        return rows.iloc[-1].to_dict()


class HitlReviewRepository(BaseRepository):
    FILE = HITL_REVIEWS_FILE

    @classmethod
    def create_review(cls, query):
        review_id = f"HR-{uuid.uuid4().hex[:8].upper()}"

        row = {
            "review_id": review_id,
            "query": query,
            "status": "PENDING",
            "human_response": "",
        }

        cls.create(row)

        return review_id

    @classmethod
    def resolve(cls, review_id, human_response):
        cls.update(
            {"review_id": review_id},
            {"status": "RESOLVED", "human_response": human_response},
        )

    @classmethod
    def pending(cls):
        rows = cls.all()
        if rows.empty:
            return rows
        return rows[rows["status"] == "PENDING"]


class DepartmentTaskRepository(BaseRepository):
    FILE = DEPARTMENT_TASKS_FILE

    @classmethod
    def create_task(cls, case_id, department, action, resolution, status="PENDING", notes=""):

        task_id = f"TASK{uuid.uuid4().hex[:8].upper()}"

        row = {
            "task_id": task_id,
            "case_id": case_id,
            "department": department,
            "action": action,
            "resolution": resolution,
            "status": status,
            "notes": notes,
            "created_date": _now(),
        }

        cls.create(row)

        return row

    @classmethod
    def update_status(cls, task_id, status, notes=""):
        cls.update({"task_id": task_id}, {"status": status, "notes": notes})

    @classmethod
    def pending_for_department(cls, department):
        rows = cls.find_by(department=department, status="PENDING")
        return rows


class NotificationRepository(BaseRepository):
    FILE = NOTIFICATIONS_FILE

    @classmethod
    def create_notification(cls, case_id, customer_id, message):

        notification_id = f"NOTIF{uuid.uuid4().hex[:8].upper()}"

        row = {
            "notification_id": notification_id,
            "case_id": case_id,
            "customer_id": customer_id,
            "message": message,
            "timestamp": _now(),
        }

        cls.create(row)

        return row

    @classmethod
    def for_case(cls, case_id):
        return cls.find_by(case_id=case_id)


class RefundRepository(BaseRepository):
    FILE = REFUNDS_FILE

    @classmethod
    def has_active_refund(cls, order_id):
        rows = cls.find_by(order_id=order_id)
        if rows.empty:
            return False
        return bool((rows["status"] != "Rejected").any())

    @classmethod
    def create_refund(cls, case_id, order_id, customer_id, amount, status="Initiated"):

        refund_id = f"REF{uuid.uuid4().hex[:8].upper()}"

        row = {
            "refund_id": refund_id,
            "case_id": case_id,
            "order_id": order_id,
            "customer_id": customer_id,
            "amount": amount,
            "status": status,
            "refund_date": _today(),
        }

        cls.create(row)

        return row


class ReplacementRepository(BaseRepository):
    FILE = REPLACEMENTS_FILE

    @classmethod
    def has_active_replacement(cls, order_id):
        rows = cls.find_by(order_id=order_id)
        if rows.empty:
            return False
        return bool((rows["status"] != "Rejected").any())

    @classmethod
    def create_replacement(cls, case_id, order_id, customer_id, status="Initiated"):

        replacement_id = f"REP{uuid.uuid4().hex[:8].upper()}"

        row = {
            "replacement_id": replacement_id,
            "case_id": case_id,
            "order_id": order_id,
            "customer_id": customer_id,
            "status": status,
            "replacement_date": _today(),
        }

        cls.create(row)

        return row


class VoucherRepository(BaseRepository):
    FILE = VOUCHERS_FILE

    @classmethod
    def has_previous_voucher(cls, customer_id):
        rows = cls.find_by(customer_id=customer_id)
        return not rows.empty

    @classmethod
    def create_voucher(cls, case_id, customer_id, amount, status="Issued"):

        voucher_id = f"VOC{uuid.uuid4().hex[:8].upper()}"

        row = {
            "voucher_id": voucher_id,
            "case_id": case_id,
            "customer_id": customer_id,
            "amount": amount,
            "status": status,
            "issued_date": _today(),
        }

        cls.create(row)

        return row


class AuditRepository(BaseRepository):
    FILE = AUDIT_LOGS_FILE

    @classmethod
    def log(cls, case_id, action, user="System"):

        log_id = f"LOG{uuid.uuid4().hex[:8].upper()}"

        row = {
            "log_id": log_id,
            "case_id": case_id,
            "timestamp": _now(),
            "action": action,
            "user": user,
        }

        cls.create(row)

        return row

    @classmethod
    def for_case(cls, case_id):
        return cls.find_by(case_id=case_id)
