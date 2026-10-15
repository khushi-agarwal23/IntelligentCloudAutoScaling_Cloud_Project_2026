def test_user_registration(client):
    payload = {
        "email": "newbuyer@festival.com",
        "password": "strongpassword123",
        "full_name": "New Festival Shopper"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == payload["email"]
    assert data["full_name"] == payload["full_name"]
    assert "id" in data
    assert "hashed_password" not in data


def test_duplicate_user_registration(client, test_user):
    payload = {
        "email": test_user.email,
        "password": "anotherpassword123",
        "full_name": "Duplicate Shopper"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_user_login_success(client, test_user):
    payload = {
        "email": test_user.email,
        "password": "securepassword123"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_user_login_invalid_password(client, test_user):
    payload = {
        "email": test_user.email,
        "password": "wrongpassword"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401


def test_get_current_user_me(client, auth_headers, test_user):
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
    assert data["id"] == test_user.id
