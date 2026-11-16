import pymupdf
import pytest

from app.config import settings
from app.dependencies import get_vector_store
from app.main import app

API = "/api/v1"


def make_pdf(text: str | None = None) -> bytes:
    doc = pymupdf.open()
    page = doc.new_page()
    if text:
        page.insert_text((72, 72), text)
    data = doc.tobytes()
    doc.close()
    return data


@pytest.fixture(autouse=True)
def upload_dir(tmp_path, monkeypatch):
    folder = tmp_path / "uploads"
    monkeypatch.setattr(settings, "upload_dir", str(folder))
    return folder


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


def test_uploaded_pdf_becomes_searchable(client):
    claim_id = create_claim(client, "1")
    upload(
        client,
        claim_id,
        "The insured vehicle was rear-ended\nat the Adyar signal by a speeding lorry.",
        "police_report.pdf",
        "POLICE_REPORT",
    )
    upload(
        client,
        claim_id,
        "Estimate for rear bumper replacement\nand repainting totals 45000 rupees.",
        "estimate.pdf",
        "REPAIR_ESTIMATE",
    )

    response = client.get(
        f"{API}/claims/{claim_id}/search", params={"q": "rear bumper replacement estimate"}
    )

    assert response.status_code == 200
    top_hit = response.json()[0]
    assert top_hit["document_type"] == "REPAIR_ESTIMATE"
    assert top_hit["original_filename"] == "estimate.pdf"
    assert "bumper" in top_hit["text"]


def test_search_never_returns_another_claims_documents(client):
    first_claim = create_claim(client, "1")
    second_claim = create_claim(client, "2")
    upload(
        client,
        first_claim,
        "Ambulance charges invoice\nfrom Apollo hospital.",
        "ambulance.pdf",
        "INVOICE",
    )
    second_upload = upload(
        client,
        second_claim,
        "Windshield replacement quotation\nfrom the glass shop.",
        "glass.pdf",
        "REPAIR_ESTIMATE",
    )

    response = client.get(
        f"{API}/claims/{second_claim}/search", params={"q": "ambulance hospital invoice"}
    )

    assert response.status_code == 200
    assert {hit["document_id"] for hit in response.json()} == {second_upload.json()["id"]}


def test_pdf_without_text_adds_nothing_to_search(client):
    claim_id = create_claim(client, "1")

    assert upload(client, claim_id, None, "scan.pdf", "OTHER").status_code == 201

    response = client.get(f"{API}/claims/{claim_id}/search", params={"q": "anything here"})
    assert response.json() == []


def test_search_on_missing_claim_returns_404(client):
    response = client.get(f"{API}/claims/999/search", params={"q": "hello there"})
    assert response.status_code == 404


def test_too_short_query_returns_422(client):
    claim_id = create_claim(client, "1")

    response = client.get(f"{API}/claims/{claim_id}/search", params={"q": "ab"})
    assert response.status_code == 422


class BrokenVectorStore:
    def index_document(self, **kwargs):
        raise RuntimeError("index is down")

    def delete_document(self, document_id):
        pass


def test_failed_indexing_saves_nothing(client, upload_dir):
    claim_id = create_claim(client, "1")
    app.dependency_overrides[get_vector_store] = lambda: BrokenVectorStore()

    response = upload(
        client,
        claim_id,
        "Some readable report text for the claim.",
        "report.pdf",
        "POLICE_REPORT",
    )

    assert response.status_code == 503
    assert client.get(f"{API}/claims/{claim_id}/documents").json() == []
    assert list(upload_dir.glob("*.pdf")) == []