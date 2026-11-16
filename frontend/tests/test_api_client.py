import json

import httpx
import pytest

from api_client import ApiError, ClaimVisionClient


def make_client(handler) -> ClaimVisionClient:
    return ClaimVisionClient(
        base_url="http://test/api/v1", transport=httpx.MockTransport(handler)
    )


def test_successful_request_returns_json():
    def handler(request):
        assert request.url.path == "/api/v1/claims"
        return httpx.Response(200, json=[{"id": 1}])

    assert make_client(handler).list_claims() == [{"id": 1}]


def test_error_detail_is_extracted():
    def handler(request):
        return httpx.Response(404, json={"detail": "Claim not found"})

    with pytest.raises(ApiError) as error:
        make_client(handler).get_claim(99)

    assert error.value.message == "Claim not found"
    assert error.value.status_code == 404


def test_validation_errors_are_made_readable():
    def handler(request):
        return httpx.Response(
            422,
            json={"detail": [{"loc": ["body", "email"], "msg": "not a valid email address"}]},
        )

    with pytest.raises(ApiError) as error:
        make_client(handler).create_customer("Asha Raman", "bad")

    assert error.value.message == "email: not a valid email address"


def test_unreachable_backend_gives_a_friendly_error():
    def handler(request):
        raise httpx.ConnectError("connection refused")

    with pytest.raises(ApiError) as error:
        make_client(handler).list_claims()

    assert "Cannot reach" in error.value.message


def test_unknown_error_body_gets_a_generic_message():
    def handler(request):
        return httpx.Response(500, text="boom")

    with pytest.raises(ApiError) as error:
        make_client(handler).list_claims()

    assert error.value.message == "The request failed (HTTP 500)."


def test_upload_sends_the_file_and_document_type():
    seen = {}

    def handler(request):
        seen["method"] = request.method
        seen["path"] = request.url.path
        seen["body"] = request.read()
        return httpx.Response(201, json={"id": 1})

    make_client(handler).upload_document(5, "police_report.pdf", b"%PDF-fake", "POLICE_REPORT")

    assert seen["method"] == "POST"
    assert seen["path"] == "/api/v1/claims/5/documents"
    assert b'filename="police_report.pdf"' in seen["body"]
    assert b"POLICE_REPORT" in seen["body"]
    assert b"%PDF-fake" in seen["body"]


def test_ask_posts_the_question_as_json():
    seen = {}

    def handler(request):
        seen["payload"] = json.loads(request.content)
        return httpx.Response(200, json={"answer": "ok"})

    make_client(handler).ask(3, "Was anyone injured?", top_k=4)

    assert seen["payload"] == {"question": "Was anyone injured?", "top_k": 4}