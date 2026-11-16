from datetime import date

import streamlit as st

from common import COVERAGE_TYPES, attempt, get_client, label, load

client = get_client()
NEW = "Create new"

st.title("New claim")
st.caption("Choose or create the customer and policy, then describe the claim.")

st.subheader("1. Customer")
customers = load(client.list_customers)
customer_options = {f"{c['full_name']} ({c['email']})": c for c in customers}
customer_choice = st.selectbox("Customer", [NEW] + list(customer_options))

existing_customer = None
if customer_choice == NEW:
    full_name = st.text_input("Full name")
    email = st.text_input("Email")
    phone = st.text_input("Phone (optional)")
else:
    existing_customer = customer_options[customer_choice]

st.subheader("2. Policy")
policy_options = {}
if existing_customer:
    for policy in load(client.list_policies, existing_customer["id"]):
        text = (
            f"{policy['policy_number']} - {policy['vehicle_make_model']} "
            f"({policy['start_date']} to {policy['end_date']})"
        )
        policy_options[text] = policy
policy_choice = st.selectbox("Policy", [NEW] + list(policy_options))

existing_policy = None
if policy_choice == NEW:
    policy_number = st.text_input("Policy number")
    vehicle = st.text_input("Vehicle make and model")
    registration = st.text_input("Registration number")
    coverage_type = st.selectbox("Coverage type", COVERAGE_TYPES, format_func=label)
    coverage_limit = st.number_input("Coverage limit (Rs)", min_value=0.0, value=500000.0, step=10000.0)
    start_date = st.date_input("Policy start", value=date(date.today().year, 1, 1))
    end_date = st.date_input("Policy end", value=date(date.today().year, 12, 31))
else:
    existing_policy = policy_options[policy_choice]

st.subheader("3. Claim")
claim_number = st.text_input("Claim number")
incident_date = st.date_input("Incident date", value=date.today(), max_value=date.today())
description = st.text_area("What happened?", height=120)
amount = st.number_input("Claimed amount (Rs)", min_value=0.0, step=1000.0)

if st.button("Create claim", type="primary"):
    customer = existing_customer
    if customer is None:
        customer = attempt(client.create_customer, full_name, email, phone)
        if customer is None:
            st.stop()

    policy = existing_policy
    if policy is None:
        policy = attempt(
            client.create_policy,
            {
                "policy_number": policy_number,
                "customer_id": customer["id"],
                "vehicle_make_model": vehicle,
                "vehicle_registration": registration,
                "coverage_type": coverage_type,
                "coverage_limit": coverage_limit,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
        )
        if policy is None:
            st.warning("The customer was saved, but the policy was not. Fix the problem above, then pick this customer from the list.")
            st.stop()

    claim = attempt(
        client.create_claim,
        {
            "claim_number": claim_number,
            "policy_id": policy["id"],
            "incident_date": incident_date.isoformat(),
            "incident_description": description,
            "claimed_amount": amount,
        },
    )
    if claim is not None:
        st.session_state["selected_claim_id"] = claim["id"]
        st.success(f"Claim {claim['claim_number']} created.")
        st.page_link("views/claim_detail.py", label="Open the claim to upload documents")