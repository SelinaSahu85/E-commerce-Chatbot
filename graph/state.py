#GraphState is the shared state object that is passed between all nodes (agents/functions).

from typing import TypedDict, List


class GraphState(TypedDict):

    user_query: str
    intent: str
    response: str
    sources: List[str]

    requires_hitl: bool
    review_id: str

    order_id: str
    issue_type: str
    description: str

    complaint_id: str
    complaint_type: str
    complaint_status: str
    pending_field: str