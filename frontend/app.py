import streamlit as st

st.set_page_config(page_title="ClaimVision", page_icon=":material/search:", layout="wide")

navigation = st.navigation(
    [
        st.Page("views/claims.py", title="Claims", icon=":material/list_alt:", default=True),
        st.Page("views/new_claim.py", title="New claim", icon=":material/add_circle:"),
        st.Page("views/claim_detail.py", title="Claim detail", icon=":material/find_in_page:"),
    ]
)

st.sidebar.caption("ClaimVision: AI-assisted claim review. Decisions stay with the investigator.")

navigation.run()