import os

import httpx

DEFAULT_API_URL = "http://127.0.0.1:8000/api/v1"


class ApiError(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def extract_error_message(response: httpx.Response) -> str:
    try:
        detail = response.json().get("detail")
    except (ValueError, AttributeError):
        detail = None

    if isinstance(detail, str):
        return detail
    if isinstance(detail, list):
        problems = []
        for item in detail:
            field = ".".join(str(part) for part in item.get("loc", [])[1:])
            message = item.get("msg", "invalid value")
            problems.append(f"{field}: {message}" if field else message)
        return "; ".join(problems)
    return f"The request failed (HTTP {response.status_code})."


class ClaimVisionClient:
    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = 120.0,
        transport: httpx.BaseTransport | None = None,
    ):
        self._http = httpx.Client(
            base_url=base_url or os.getenv("CLAIMVISION_API_URL", DEFAULT_API_URL),
            timeout=timeout,
            transport=transport,
        )

    def _request(self, method: str, path: str, **kwargs):
        try:
            response = self._http.request(method, path, **kwargs)
        except httpx.ConnectError as exc:
            raise ApiError(
                "Cannot reach the ClaimVision backend. Is it running on port 8000?"
            ) from exc
        except httpx.TimeoutException as exc:
            raise ApiError("The backend took too long to respond. Please try again.") from exc

        if response.status_code >= 400:
            raise ApiError(extract_error_message(response), response.status_code)
        if response.status_code == 204:
            return None
        return response.json()

    # customers
    def list_customers(self):
        return self._request("GET", "/customers", params={"limit": 200})

    def get_customer(self, customer_id: int):
        return self._request("GET", f"/customers/{customer_id}")

    def create_customer(self, full_name: str, email: str, phone: str | None = None):
        payload = {"full_name": full_name, "email": email}
        if phone:
            payload["phone"] = phone
        return self._request("POST", "/customers", json=payload)

    # policies
    def list_policies(self, customer_id: int | None = None):
        params: dict = {"limit": 200}
        if customer_id is not None:
            params["customer_id"] = customer_id
        return self._request("GET", "/policies", params=params)

    def get_policy(self, policy_id: int):
        return self._request("GET", f"/policies/{policy_id}")

    def create_policy(self, payload: dict):
        return self._request("POST", "/policies", json=payload)

    # claims
    def list_claims(self):
        return self._request("GET", "/claims", params={"limit": 200})

    def get_claim(self, claim_id: int):
        return self._request("GET", f"/claims/{claim_id}")

    def create_claim(self, payload: dict):
        return self._request("POST", "/claims", json=payload)

    def update_claim_status(self, claim_id: int, status: str):
        return self._request("PATCH", f"/claims/{claim_id}", json={"status": status})

    # documents, search and questions
    def list_documents(self, claim_id: int):
        return self._request("GET", f"/claims/{claim_id}/documents")

    def upload_document(self, claim_id: int, filename: str, content: bytes, document_type: str):
        return self._request(
            "POST",
            f"/claims/{claim_id}/documents",
            files={"file": (filename, content, "application/pdf")},
            data={"document_type": document_type},
        )

    def search(self, claim_id: int, query: str, top_k: int = 5):
        return self._request(
            "GET", f"/claims/{claim_id}/search", params={"q": query, "top_k": top_k}
        )

    def ask(self, claim_id: int, question: str, top_k: int = 5):
        return self._request(
            "POST", f"/claims/{claim_id}/ask", json={"question": question, "top_k": top_k}
        )