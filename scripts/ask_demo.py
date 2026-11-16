import sys

import httpx

API = "http://127.0.0.1:8000/api/v1"

QUESTIONS = [
    "Was anyone injured, and what treatment was given?",
    "What repairs are in the estimate and what is the total?",
    "Does the repair estimate include any damage that the police report does not mention?",
    "What colour is the lorry?",
]


def find_claim_with_documents(client: httpx.Client) -> int | None:
    claims = client.get("/claims", params={"limit": 200}).json()
    for claim in reversed(claims):
        documents = client.get(f"/claims/{claim['id']}/documents").json()
        if any(doc["extraction_status"] == "EXTRACTED" for doc in documents):
            return claim["id"]
    return None


def main() -> None:
    try:
        with httpx.Client(base_url=API, timeout=120) as client:
            claim_id = int(sys.argv[1]) if len(sys.argv) > 1 else find_claim_with_documents(client)
            if claim_id is None:
                sys.exit("No claim with documents found. Run scripts\\seed_demo_data.py first.")
            print(f"Using claim {claim_id}\n")

            for question in QUESTIONS:
                response = client.post(
                    f"/claims/{claim_id}/ask", json={"question": question, "top_k": 8}
                )
                print(f"Q: {question}")
                if response.status_code != 200:
                    print(f"   FAILED {response.status_code}: {response.json().get('detail')}\n")
                    continue

                body = response.json()
                print(f"A: {body['answer']}")
                for citation in body["citations"]:
                    print(
                        f"   [{citation['number']}] {citation['original_filename']} "
                        f"({citation['document_type']}, chunk {citation['chunk_index']})"
                    )
                print()
    except httpx.ConnectError:
        sys.exit("Cannot reach the backend. Is uvicorn running on port 8000?")


if __name__ == "__main__":
    main()