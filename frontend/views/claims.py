import pandas as pd
import streamlit as st

from common import CLAIM_STATUSES, get_client, label, load

client = get_client()

st.title("Claims")
st.caption("Select a row to open the claim.")

claims = sorted(load(client.list_claims), key=lambda claim: claim["id"], reverse=True)
policies = {policy["id"]: policy for policy in load(client.list_policies)}
customers = {customer["id"]: customer for customer in load(client.list_customers)}

columns = st.columns(len(CLAIM_STATUSES) + 1)
columns[0].metric("Total claims", len(claims))
for column, status in zip(columns[1:], CLAIM_STATUSES):
    column.metric(label(status), sum(1 for claim in claims if claim["status"] == status))

selected_statuses = st.multiselect(
    "Show statuses", CLAIM_STATUSES, default=CLAIM_STATUSES, format_func=label
)

rows = []
for claim in claims:
    if claim["status"] not in selected_statuses:
        continue
    policy = policies.get(claim["policy_id"], {})
    customer = customers.get(policy.get("customer_id"), {})
    rows.append(
        {
            "Id": claim["id"],
            "Claim": claim["claim_number"],
            "Customer": customer.get("full_name", "-"),
            "Vehicle": policy.get("vehicle_make_model", "-"),
            "Incident date": claim["incident_date"],
            "Amount (Rs)": claim["claimed_amount"],
            "Status": label(claim["status"]),
        }
    )

if not rows:
    st.info("No claims to show yet. Create one on the New claim page.")
    st.stop()

event = st.dataframe(
    pd.DataFrame(rows),
    hide_index=True,
    on_select="rerun",
    selection_mode="single-row",
)

chosen = event.selection.rows
if chosen:
    row = rows[chosen[0]]
    if st.button(f"Open {row['Claim']}", type="primary"):
        st.session_state["selected_claim_id"] = row["Id"]
        st.switch_page("views/claim_detail.py")