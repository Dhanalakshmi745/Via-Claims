import sys
import time
from pathlib import Path

import httpx

API = "http://127.0.0.1:8000/api/v1"
SAMPLE_DIR = Path(__file__).resolve().parent.parent / "sample_data"

DOCUMENTS = [
    ("police_report.pdf", "POLICE_REPORT"),
    ("repair_estimate.pdf", "REPAIR_ESTIMATE"),
    ("hospital_invoice.pdf", "INVOICE"),
    ("scanned_police_report.pdf", "POLICE_REPORT"),
]
INJECTION_TEST = ("witness_statement_injection_test.pdf", "OTHER")


def main() -> None:
    documents = list(DOCUMENTS)
    if "--include-injection-test" in sys.argv:
        documents.append(INJECTION_TEST)

    for filename, _ in documents:
        if not (SAMPLE_DIR / filename).exists():
            sys.exit(f"{filename} not found. Run scripts\\make_synthetic_pdfs.py first.")

    suffix = int(time.time())

    with httpx.Client(base_url=API, timeout=180) as client:
        customer = client.post(
            "/customers",
            json={"full_name": "Asha Raman", "email": f"asha.demo{suffix}@example.com"},
        )
        customer.raise_for_status()

        policy = client.post(
            "/policies",
            json={
                "policy_number": f"POL-DEMO-{suffix}",
                "customer_id": customer.json()["id"],
                "vehicle_make_model": "Honda City",
                "vehicle_registration": "TN01AB1234",
                "coverage_type": "COMPREHENSIVE",
                "coverage_limit": 500000,
                "start_date": "2026-01-01",
                "end_date": "2026-12-31",
            },
        )
        policy.raise_for_status()

        claim = client.post(
            "/claims",
            json={
                "claim_number": f"CLM-DEMO-{suffix}",
                "policy_id": policy.json()["id"],
                "incident_date": "2026-06-15",
                "incident_description": "Insured vehicle rear-ended by a lorry at a signal",
                "claimed_amount": 48500,
            },
        )
        claim.raise_for_status()
        claim_id = claim.json()["id"]
        print(f"Created claim {claim_id}")

        for filename, document_type in documents:
            response = client.post(
                f"/claims/{claim_id}/documents",
                files={"file": (filename, (SAMPLE_DIR / filename).read_bytes(), "application/pdf")},
                data={"document_type": document_type},
            )
            response.raise_for_status()
            status = response.json()["extraction_status"]
            print(f"  uploaded {filename}: {status}")

    print(f"\nDone. Use claim id {claim_id} in /docs.")


if __name__ == "__main__":
    main()