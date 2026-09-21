def test_checkout_guest_flow(client):
    payload = {
        "product": "Diwali Special Smart LED TV",
        "amount": 34999.0,
        "items_count": 1,
        "payment_method": "upi"
    }
    response = client.post("/api/v1/transactions/checkout", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["product"] == payload["product"]
    assert data["amount"] == payload["amount"]
    assert data["order_id"].startswith("ORD-FEST-")
    assert data["status"] == "completed"


def test_checkout_authenticated_flow(client, auth_headers, test_user):
    payload = {
        "product": "Smartphone Pro Max",
        "amount": 64999.0,
        "items_count": 1,
        "payment_method": "credit_card"
    }
    response = client.post("/api/v1/transactions/checkout", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == test_user.id
    assert data["product"] == payload["product"]


def test_transaction_stats_calculation(client, test_user):
    # Insert 2 transactions
    client.post("/api/v1/transactions/checkout", json={
        "user_id": test_user.id,
        "product": "Item 1",
        "amount": 1000.0,
        "items_count": 1
    })
    client.post("/api/v1/transactions/checkout", json={
        "user_id": test_user.id,
        "product": "Item 2",
        "amount": 2000.0,
        "items_count": 1
    })

    response = client.get("/api/v1/transactions/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_transactions"] >= 2
    assert data["total_revenue"] >= 3000.0
    assert data["average_order_value"] > 0


def test_list_transactions_with_user_filter(client, test_user):
    client.post("/api/v1/transactions/checkout", json={
        "user_id": test_user.id,
        "product": "Filtered Item",
        "amount": 500.0,
        "items_count": 1
    })

    response = client.get(f"/api/v1/transactions?user_id={test_user.id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert all(tx["user_id"] == test_user.id for tx in data)
