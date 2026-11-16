import streamlit as st

from api_client import ApiError, ClaimVisionClient

CLAIM_STATUSES = ["SUBMITTED", "UNDER_REVIEW", "INFO_REQUESTED", "CLOSED"]
DOCUMENT_TYPES = ["POLICE_REPORT", "REPAIR_ESTIMATE", "INVOICE", "POLICY_DOCUMENT", "OTHER"]
COVERAGE_TYPES = ["COMPREHENSIVE", "THIRD_PARTY"]


@st.cache_resource
def get_client() -> ClaimVisionClient:
    return ClaimVisionClient()


def label(value: str) -> str:
    return value.replace("_", " ").title()


def load(function, *args, **kwargs):
    """Fetch data a page needs. On failure, show the error and stop rendering the page."""
    try:
        return function(*args, **kwargs)
    except ApiError as error:
        st.error(error.message)
        st.stop()


def attempt(function, *args, **kwargs):
    """Run a user action. On failure, show the error and return None."""
    try:
        return function(*args, **kwargs)
    except ApiError as error:
        st.error(error.message)
        return None