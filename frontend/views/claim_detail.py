import pandas as pd
import streamlit as st

from common import CLAIM_STATUSES, DOCUMENT_TYPES, attempt, get_client, label, load

client = get_client()

st.title("Claim detail")

claims = sorted(load(client.list_claims), key=lambda claim: claim["id"], reverse=True)
if not claims:
    st.info("There are no claims yet. Create one on the New claim page.")
    st.stop()

numbers = {claim["id"]: claim["claim_number"] for claim in claims}
ids = list(numbers)
wanted = st.session_state.get("selected_claim_id", ids[0])
claim_id = st.selectbox(
    "Claim",
    ids,
    index=ids.index(wanted) if wanted in ids else 0,
    format_func=lambda claim_id: numbers[claim_id],
)
st.session_state["selected_claim_id"] = claim_id

claim = load(client.get_claim, claim_id)
policy = load(client.get_policy, claim["policy_id"])
customer = load(client.get_customer, policy["customer_id"])

st.subheader(f"{claim['claim_number']} - {customer['full_name']}")
st.caption(
    f"Policy {policy['policy_number']} | {policy['vehicle_make_model']} "
    f"({policy['vehicle_registration']}) | {label(policy['coverage_type'])}"
)

metrics = st.columns(4)
metrics[0].metric("Status", label(claim["status"]))
metrics[1].metric("Claimed amount (Rs)", f"{claim['claimed_amount']:,.0f}")
metrics[2].metric("Incident date", claim["incident_date"])
metrics[3].metric("Coverage limit (Rs)", f"{policy['coverage_limit']:,.0f}")

if claim["claimed_amount"] > policy["coverage_limit"]:
    st.warning("The claimed amount is above the policy's coverage limit. Review the documents.")

with st.expander("Update status"):
    new_status = st.selectbox(
        "Status",
        CLAIM_STATUSES,
        index=CLAIM_STATUSES.index(claim["status"]),
        format_func=label,
    )
    if st.button("Save status"):
        if attempt(client.update_claim_status, claim_id, new_status) is not None:
            st.rerun()

documents_tab, ask_tab, search_tab = st.tabs(["Documents", "Ask a question", "Search passages"])

with documents_tab:
    st.markdown("**Upload a document** (PDF only)")
    upload = st.file_uploader("PDF file", type=["pdf"], key=f"upload_{claim_id}")
    document_type = st.selectbox("Document type", DOCUMENT_TYPES, format_func=label)

    if st.button("Upload and index", disabled=upload is None):
        with st.spinner("Reading and indexing the document..."):
            result = attempt(
                client.upload_document, claim_id, upload.name, upload.getvalue(), document_type
            )
        if result is not None:
            st.success(f"{result['original_filename']}: {label(result['extraction_status'])}.")

    documents = load(client.list_documents, claim_id)
    if documents:
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "File": doc["original_filename"],
                        "Type": label(doc["document_type"]),
                        "Pages": doc["page_count"],
                        "Text": label(doc["extraction_status"]),
                        "Uploaded": doc["uploaded_at"],
                    }
                    for doc in documents
                ]
            ),
            hide_index=True,
        )
        if any(doc["extraction_status"] == "NO_TEXT" for doc in documents):
            st.warning(
                "Some documents are scanned images without text. They are stored but cannot "
                "be searched or used in answers yet."
            )
    else:
        st.info("No documents uploaded for this claim yet.")

with ask_tab:
    question = st.text_area(
        "Your question",
        placeholder="Was anyone injured, and what treatment was given?",
        key=f"question_{claim_id}",
    )
    passages = st.slider("Passages to consider", 1, 10, 5, key=f"passages_{claim_id}")

    if st.button("Ask", type="primary", disabled=len(question.strip()) < 5):
        with st.spinner("Searching the documents and asking the AI..."):
            result = attempt(client.ask, claim_id, question.strip(), passages)
        if result is not None:
            st.markdown("#### Answer")
            st.write(result["answer"])
            if result["citations"]:
                st.markdown("#### Sources")
                for citation in result["citations"]:
                    title = (
                        f"[{citation['number']}] {citation['original_filename']} "
                        f"({label(citation['document_type'])})"
                    )
                    with st.expander(title):
                        st.text(citation["text"])
            else:
                st.caption("No sources were cited, so treat this answer with extra care.")
            st.info(result["disclaimer"])

with search_tab:
    query = st.text_input("Search this claim's documents", key=f"query_{claim_id}")
    if st.button("Search", disabled=len(query.strip()) < 3):
        hits = attempt(client.search, claim_id, query.strip(), 5)
        if hits is not None:
            if not hits:
                st.info("No matching passages.")
            for hit in hits:
                with st.expander(f"{hit['original_filename']} (chunk {hit['chunk_index']})"):
                    st.text(hit["text"])
                    st.caption(f"Distance {hit['distance']:.3f} (lower means closer in meaning)")