import pymupdf

API = "/api/v1"


def make_pdf(text: str | None = None) -> bytes:
    doc = pymupdf.open()
    page = doc.new_page()
    if text:
        page.insert_text((72, 72), text)
    data = doc.tobytes()
    doc.close()
    return data


def create_claim(client, suffix: str) -> int:
    customer = client.post(
        f"{API}/customers",
        json={"full_name": f"Customer {suffix}", "email": f"customer{suffix}@example.com"},
    ).json()
    policy = client.post(
        f"{API}/policies",
        json={
            "policy_number": f"POL-{suffix}",
            "customer_id": customer["id"],
            "vehicle_make_model": "Honda City",
            "vehicle_registration": "TN01AB1234",
            "coverage_type": "COMPREHENSIVE",
            "coverage_limit": 500000,
            "start_date": "2026-01-01",
            "end_date": "2026-12-31",
        },
    ).json()
    claim = client.post(
        f"{API}/claims",
        json={
            "claim_number": f"CLM-{suffix}",
            "policy_id": policy["id"],
            "incident_date": "2026-06-15",
            "incident_description": "Rear-ended at a traffic signal",
            "claimed_amount": 45000,
        },
    ).json()
    return claim["id"]


def upload(client, claim_id, text, filename, document_type):
    return client.post(
        f"{API}/claims/{claim_id}/documents",
        files={"file": (filename, make_pdf(text), "application/pdf")},
        data={"document_type": document_type},
    )