# tools/complaint_validator.py

def validate_complaint(order_id, issue_type, description):
    """
    Validate complaint details.
    """

    missing_fields = []

    if not order_id:
        missing_fields.append("Order ID")

    if not issue_type:
        missing_fields.append("Issue Type")

    if not description:
        missing_fields.append("Description")

    if missing_fields:
        return False, f"Missing fields: {', '.join(missing_fields)}"

    return True, "Valid complaint"