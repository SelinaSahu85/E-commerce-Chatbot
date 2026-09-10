# GraphState is the shared state object passed between graph nodes
# (agents/functions) for a single customer turn. Cross-turn / case
# lifecycle state lives in the database (see database/repositories.py),
# not here — HITL review pages act on the database directly, outside
# the graph.

from typing import TypedDict, List


class GraphState(TypedDict):

    user_query: str
    customer_id: str

    intent: str
    response: str
    sources: List[str]

    requires_hitl: bool
    review_id: str

    case_id: str

    order_id: str
    issue_type: str
    description: str

    complaint_status: str
    pending_field: str
