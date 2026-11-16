API = "/api/v1"


def create_customer(client, email="asha@example.com"):
    response = client.post(
        f"{API}/customers",
        json={"full_name": "Asha Raman", "email": email, "phone": "9876543210"},
    )
    assert response.status_code == 201
    return response.json()


def policy_payload(customer_id, number="POL-001"):
    return {
        "policy_number": number,
        "customer_id": customer_id,
        "vehicle_make_model": "Honda City",
        "vehicle_registration": "TN01AB1234",
        "coverage_type": "COMPREHENSIVE",
        "coverage_limit": 500000,
        "start_date": "2026-01-01",
        "end_date": "2026-12-31",
    }


def create_policy(client, customer_id, number="POL-001"):
    response = client.post(f"{API}/policies", json=policy_payload(customer_id, number))
    assert response.status_code == 201
    return response.json()


def claim_payload(policy_id, number="CLM-001", incident_date="2026-06-15"):
    return {
        "claim_number": number,
        "policy_id": policy_id,
        "incident_date": incident_date,
        "incident_description": "Rear-ended at a traffic signal",
        "claimed_amount": 45000,
    }


# ---------- customers ----------

def test_create_and_fetch_customer(client):
    created = create_customer(client)
    response = client.get(f"{API}/customers/{created['id']}")

    assert response.status_code == 200
    assert response.json()["email"] == "asha@example.com"


def test_duplicate_email_returns_409(client):
    create_customer(client)
    response = client.post(
        f"{API}/customers",
        json={"full_name": "Another Person", "email": "asha@example.com"},
    )
    assert response.status_code == 409


def test_invalid_email_returns_422(client):
    response = client.post(
        f"{API}/customers",
        json={"full_name": "Bad Email", "email": "not-an-email"},
    )
    assert response.status_code == 422


def test_partial_update_changes_only_sent_fields(client):
    created = create_customer(client)
    response = client.patch(f"{API}/customers/{created['id']}", json={"phone": "9000000000"})

    assert response.status_code == 200
    assert response.json()["phone"] == "9000000000"
    assert response.json()["full_name"] == "Asha Raman"


def test_missing_customer_returns_404(client):
    assert client.get(f"{API}/customers/999").status_code == 404


def test_cannot_delete_customer_with_policies(client):
    customer = create_customer(client)
    create_policy(client, customer["id"])

    assert client.delete(f"{API}/customers/{customer['id']}").status_code == 409


def test_delete_customer_without_policies(client):
    customer = create_customer(client)

    assert client.delete(f"{API}/customers/{customer['id']}").status_code == 204
    assert client.get(f"{API}/customers/{customer['id']}").status_code == 404


# ---------- policies ----------

def test_policy_requires_existing_customer(client):
    response = client.post(f"{API}/policies", json=policy_payload(customer_id=999))
    assert response.status_code == 404


def test_policy_end_date_before_start_returns_422(client):
    customer = create_customer(client)
    payload = policy_payload(customer["id"])
    payload["end_date"] = "2025-12-31"

    assert client.post(f"{API}/policies", json=payload).status_code == 422


# ---------- claims ----------

def test_claim_outside_policy_period_returns_400(client):
    customer = create_customer(client)
    policy = create_policy(client, customer["id"])

    response = client.post(
        f"{API}/claims",
        json=claim_payload(policy["id"], incident_date="2025-06-15"),
    )
    assert response.status_code == 400


def test_claim_lifecycle_and_status_filter(client):
    customer = create_customer(client)
    policy = create_policy(client, customer["id"])

    created = client.post(f"{API}/claims", json=claim_payload(policy["id"]))
    assert created.status_code == 201
    assert created.json()["status"] == "SUBMITTED"

    claim_id = created.json()["id"]
    updated = client.patch(f"{API}/claims/{claim_id}", json={"status": "UNDER_REVIEW"})
    assert updated.json()["status"] == "UNDER_REVIEW"

    under_review = client.get(f"{API}/claims", params={"status": "UNDER_REVIEW"})
    submitted = client.get(f"{API}/claims", params={"status": "SUBMITTED"})
    assert len(under_review.json()) == 1
    assert len(submitted.json()) == 0


def test_invalid_claim_status_returns_422(client):
    customer = create_customer(client)
    policy = create_policy(client, customer["id"])
    claim = client.post(f"{API}/claims", json=claim_payload(policy["id"])).json()

    response = client.patch(f"{API}/claims/{claim['id']}", json={"status": "FRAUDULENT"})
    assert response.status_code == 422