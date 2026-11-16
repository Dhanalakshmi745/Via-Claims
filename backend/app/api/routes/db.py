from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database import engine
from app.main import app
from app.models import Customer, Policy

client = TestClient(app)


def test_database_health_endpoint():
    response = client.get("/api/v1/health/db")

    assert response.status_code == 200
    assert response.json()["database"] == "connected"


def test_customer_policy_relationship():
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    try:
        customer = Customer(full_name="Test Person", email="test.person@example.com")
        policy = Policy(
            policy_number="POL-TEST-001",
            customer=customer,
            vehicle_make_model="Honda City",
            vehicle_registration="TN01AB1234",
            coverage_type="COMPREHENSIVE",
            coverage_limit=500000,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
        )
        session.add(policy)
        session.flush()

        assert customer.id is not None
        assert customer.policies[0].policy_number == "POL-TEST-001"
    finally:
        session.close()
        transaction.rollback()
        connection.close()