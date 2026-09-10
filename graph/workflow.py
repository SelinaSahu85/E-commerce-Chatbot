from langgraph.graph import StateGraph, END

from agents.supervisor_agent import route_query
from agents.enquiry_agent import enquiry_agent
from agents.complaint_agent import complaint_agent

from graph.state import GraphState


workflow = StateGraph(GraphState)

workflow.add_node("supervisor", route_query)
workflow.add_node("enquiry", enquiry_agent)
workflow.add_node("complaint", complaint_agent)

workflow.set_entry_point("supervisor")


def route(state):
    return state["intent"]


workflow.add_conditional_edges(
    "supervisor",
    route,
    {
        "enquiry": "enquiry",
        "complaint": "complaint",
    }
)

workflow.add_edge("enquiry", END)
workflow.add_edge("complaint", END)

graph = workflow.compile()