import pytest
from claimvision_ai.llm import LLMError
from claimvision_ai.rag import NO_EVIDENCE_ANSWER

from app.config import settings
from app.dependencies import build_llm_client, get_llm_client
from app.main import app
from tests.helpers import API, create_claim, upload


@pytest.fixture(autouse=True)
def upload_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path / "uploads"))


def ask(client, claim_id, question="Was anyone injured?"):
    return client.post(f"{API}/claims/{claim_id}/ask", json={"question": question})


def test_answer_comes_with_citations_to_the_uploaded_document(client, fake_llm):
    claim_id = create_claim(client, "1")
    upload(
        client,
        claim_id,
        "The passenger complained of neck pain\nand was taken to hospital.",
        "police_report.pdf",
        "POLICE_REPORT",
    )
    fake_llm.reply = "The passenger had neck pain [1]."

    response = ask(client, claim_id)

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "The passenger had neck pain [1]."
    assert len(body["citations"]) == 1
    assert body["citations"][0]["original_filename"] == "police_report.pdf"
    assert "neck pain" in body["citations"][0]["text"]
    assert "not a fraud finding" in body["disclaimer"]
    assert "neck pain" in fake_llm.calls[0][1]


def test_claim_without_documents_never_calls_the_llm(client, fake_llm):
    claim_id = create_claim(client, "1")

    response = ask(client, claim_id)

    assert response.status_code == 200
    assert response.json()["answer"] == NO_EVIDENCE_ANSWER
    assert response.json()["citations"] == []
    assert fake_llm.calls == []


def test_other_claims_documents_are_never_sent_to_the_llm(client, fake_llm):
    first_claim = create_claim(client, "1")
    second_claim = create_claim(client, "2")
    upload(
        client,
        first_claim,
        "Confidential settlement amount is 99999 rupees.",
        "settlement.pdf",
        "OTHER",
    )
    upload(
        client,
        second_claim,
        "Windshield quotation from the glass shop.",
        "glass.pdf",
        "REPAIR_ESTIMATE",
    )

    ask(client, second_claim, "What is the settlement amount?")

    assert "99999" not in fake_llm.calls[0][1]


def test_invented_citation_numbers_are_dropped(client, fake_llm):
    claim_id = create_claim(client, "1")
    upload(client, claim_id, "Rear bumper damaged at the signal.", "report.pdf", "POLICE_REPORT")
    fake_llm.reply = "The bumper was damaged [1] and also something else [9]."

    response = ask(client, claim_id, "What was damaged?")

    assert [citation["number"] for citation in response.json()["citations"]] == [1]


def test_ask_on_missing_claim_returns_404(client):
    assert ask(client, 999).status_code == 404


def test_too_short_question_returns_422(client):
    claim_id = create_claim(client, "1")

    assert ask(client, claim_id, "hi").status_code == 422


class FailingLLM:
    def generate(self, system_prompt, user_prompt):
        raise LLMError("provider is down")


def test_llm_failure_returns_502(client):
    claim_id = create_claim(client, "1")
    upload(client, claim_id, "Rear bumper damaged at the signal.", "report.pdf", "POLICE_REPORT")
    app.dependency_overrides[get_llm_client] = lambda: FailingLLM()

    response = ask(client, claim_id, "What was damaged?")

    assert response.status_code == 502


def test_unconfigured_llm_returns_503(client, monkeypatch):
    app.dependency_overrides.pop(get_llm_client, None)
    monkeypatch.setattr(settings, "llm_api_key", "")
    build_llm_client.cache_clear()
    claim_id = create_claim(client, "1")

    response = ask(client, claim_id)

    assert response.status_code == 503