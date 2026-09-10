import streamlit as st

from database.schema import ensure_tables_exist
from database.repositories import ComplaintRepository
from hitl import evidence_review

ensure_tables_exist()

st.set_page_config(page_title="Evidence Reviewer")
st.title("Evidence Reviewer — Pending Evidence")

pending = evidence_review.pending_evidence()

if pending.empty:
    st.info("No evidence awaiting review.")
else:

    for _, row in pending.iterrows():

        complaint = ComplaintRepository.get_by_case(row["case_id"]) or {}

        with st.expander(f"{row['evidence_id']} — Case {row['case_id']}"):

            st.write(f"**Complaint:** {complaint.get('complaint_text', '')}")
            st.write(f"**Evidence type:** {row['evidence_type']}")
            st.write(f"**Description:** {row['description']}")

            result = st.radio(
                "Decision",
                ["Valid", "Invalid", "Unclear"],
                key=f"result_{row['evidence_id']}",
                horizontal=True,
            )

            comments = st.text_input("Comments", key=f"comments_{row['evidence_id']}")

            if st.button("Submit decision", key=f"submit_{row['evidence_id']}"):
                evidence_review.record_decision(
                    row["evidence_id"], result, comments, reviewed_by="EvidenceReviewer"
                )
                st.success(f"Recorded: {result}")
                st.rerun()
