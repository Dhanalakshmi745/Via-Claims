import pymupdf
import pytest

from app.config import settings

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
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path))
    return tmp_path


@pytest.fixture()
def claim_id(client):
    customer = client.post(
        f"{API}/customers", json={"full_name": "Asha Raman", "email": "asha@example.com"}
    ).json()
    policy = client.post(
        f"{API}/policies",
        json={
            "policy_number": "POL-001",
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
            "claim_number": "CLM-001",
            "policy_id": policy["id"],
            "incident_date": "2026-06-15",
            "incident_description": "Rear-ended at a traffic signal",
            "claimed_amount": 45000,
        },
    ).json()
    return claim["id"]


def upload(client, claim_id, content, filename="report.pdf", mime="application/pdf",
           document_type="POLICE_REPORT"):
    return client.post(
        f"{API}/claims/{claim_id}/documents",
        files={"file": (filename, content, mime)},
        data={"document_type": document_type},
    )


def test_upload_pdf_extracts_text(client, claim_id, upload_dir):
    response = upload(client, claim_id, make_pdf("Rear-ended, vehicle TN01AB1234"))

    assert response.status_code == 201
    body = response.json()
    assert body["extraction_status"] == "EXTRACTED"
    assert body["page_count"] == 1
    assert len(list(upload_dir.glob("*.pdf"))) == 1

    text = client.get(f"{API}/documents/{body['id']}/text").json()
    assert "TN01AB1234" in text["extracted_text"]


def test_pdf_without_text_is_flagged(client, claim_id):
    response = upload(client, claim_id, make_pdf())

    assert response.status_code == 201
    assert response.json()["extraction_status"] == "NO_TEXT"


def test_non_pdf_rejected_with_415(client, claim_id):
    response = upload(client, claim_id, b"hello", "notes.txt", "text/plain")
    assert response.status_code == 415


def test_fake_pdf_extension_rejected_with_415(client, claim_id):
    response = upload(client, claim_id, b"not really a pdf", "fake.pdf")
    assert response.status_code == 415


def test_corrupt_pdf_rejected_with_422(client, claim_id):
    response = upload(client, claim_id, b"%PDF-1.4 corrupted content")
    assert response.status_code == 422


def test_oversized_file_rejected_with_413(client, claim_id, monkeypatch):
    monkeypatch.setattr(settings, "max_upload_mb", 1)
    response = upload(client, claim_id, b"%PDF-" + b"0" * (2 * 1024 * 1024))
    assert response.status_code == 413


def test_upload_for_missing_claim_returns_404(client):
    assert upload(client, 999, make_pdf("text")).status_code == 404


def test_invalid_document_type_returns_422(client, claim_id):
    response = upload(client, claim_id, make_pdf("text"), document_type="SELFIE")
    assert response.status_code == 422


def test_list_documents_for_claim(client, claim_id):
    upload(client, claim_id, make_pdf("first"))
    upload(client, claim_id, make_pdf("second"), document_type="INVOICE")

    response = client.get(f"{API}/claims/{claim_id}/documents")
    assert response.status_code == 200
    assert len(response.json()) == 2