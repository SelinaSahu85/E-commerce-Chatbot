import streamlit as st

from rag.rag_chain import answer_query

st.set_page_config(
    page_title="Myntra Support Assistant",
    page_icon="🛍️",
    layout="wide"
)

st.title("🛍️ Myntra Customer Support Assistant")

st.markdown("""
Ask questions about:

- Returns & Exchanges
- Refunds
- Cancellations
- Order Tracking
- Delivery
- Payments
- Myntra Credit
- Coupons
- Gift Cards
""")

# Session State

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display Previous Messages

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.markdown(message["content"])

        if "sources" in message:

            st.caption(
                "📄 Sources: " +
                ", ".join(message["sources"])
            )

# User Input

query = st.chat_input(
    "Ask your question..."
)

if query:

    # User Message

    st.session_state.messages.append(
        {
            "role": "user",
            "content": query
        }
    )

    with st.chat_message("user"):
        st.markdown(query)

    # Assistant Response

    with st.chat_message("assistant"):

        with st.spinner("Searching knowledge base..."):

            result = answer_query(query)

            answer = result["answer"]

            sources = result["sources"]

            st.markdown(answer)

            st.caption(
                "📄 Sources: " +
                ", ".join(sources)
            )

    # Store Chat History

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer,
            "sources": sources
        }
    )