import streamlit as st

from graph.workflow import graph
from database.schema import ensure_tables_exist
from database.repositories import CustomerRepository
from utils.logger import logger

ensure_tables_exist()

st.set_page_config(page_title="E-Commerce Support Assistant")

st.title("E-Commerce Customer Support Assistant")


# --------------------------------------------------
# Simulated Customer Login
# --------------------------------------------------

customers_df = CustomerRepository.all()

customer_ids = customers_df["customer_id"].tolist() if not customers_df.empty else ["CUST1001"]

customer_id = st.sidebar.selectbox("Logged in as", customer_ids)

st.sidebar.caption(
    "This selector simulates customer login for the MVP. "
    "HITL review pages are under the Pages menu in the sidebar."
)


# --------------------------------------------------
# Session State
# --------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "complaint_data" not in st.session_state:
    st.session_state.complaint_data = {
        "order_id": "",
        "issue_type": "",
        "description": "",
        "pending_field": ""
    }


# --------------------------------------------------
# Display Chat History
# --------------------------------------------------

for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# --------------------------------------------------
# Chat Input
# --------------------------------------------------

user_input = st.chat_input(
    "Ask a question or raise a complaint..."
)

if user_input:

    # Display user message

    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_input
        }
    )

    with st.chat_message("user"):
        st.markdown(user_input)

    try:

        complaint_data = st.session_state.complaint_data

        pending_field = complaint_data["pending_field"]

        # -----------------------------------------
        # Store user response if bot is waiting
        # -----------------------------------------

        if pending_field == "order_id":

            complaint_data["order_id"] = user_input

        elif pending_field == "issue_type":

            complaint_data["issue_type"] = user_input

        elif pending_field == "description":

            complaint_data["description"] = user_input

        # -----------------------------------------
        # Build Graph State
        # -----------------------------------------

        state = {
            "user_query": user_input,
            "customer_id": customer_id,

            "intent": "",
            "response": "",
            "sources": [],

            "requires_hitl": False,
            "review_id": "",

            "case_id": "",

            "order_id": complaint_data["order_id"],
            "issue_type": complaint_data["issue_type"],
            "description": complaint_data["description"],

            "complaint_status": "",

            "pending_field": complaint_data["pending_field"]
        }

        logger.info("Invoking graph")

        result = graph.invoke(state)

        logger.info("Graph execution completed")

        # -----------------------------------------
        # Save Returned State
        # -----------------------------------------

        complaint_data["pending_field"] = result.get(
            "pending_field",
            ""
        )

        if result.get("order_id"):
            complaint_data["order_id"] = result["order_id"]

        if result.get("issue_type"):
            complaint_data["issue_type"] = result["issue_type"]

        if result.get("description"):
            complaint_data["description"] = result["description"]

        # -----------------------------------------
        # Reset after successful complaint creation
        # -----------------------------------------

        if result.get("case_id") and not complaint_data["pending_field"]:

            logger.info(
                f"Case Created/Updated: {result['case_id']}"
            )

            st.session_state.complaint_data = {
                "order_id": "",
                "issue_type": "",
                "description": "",
                "pending_field": ""
            }

        # -----------------------------------------
        # Show Bot Response
        # -----------------------------------------

        bot_response = result["response"]

        if result.get("sources"):
            bot_response += "\n\n**Sources:** " + ", ".join(result["sources"])

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": bot_response
            }
        )

        with st.chat_message("assistant"):
            st.markdown(bot_response)

    except Exception as e:

        logger.error(str(e))

        st.error(str(e))
