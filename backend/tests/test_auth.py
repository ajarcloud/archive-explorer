def test_register_success(client):
    res = client.post("/api/auth/register", json={"email": "a@b.com", "password": "pass1234"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_register_duplicate(client):
    client.post("/api/auth/register", json={"email": "dup@b.com", "password": "pass1234"})
    res = client.post("/api/auth/register", json={"email": "dup@b.com", "password": "pass1234"})
    assert res.status_code == 400
    assert "already registered" in res.json()["detail"].lower()


def test_login_success(client):
    client.post("/api/auth/register", json={"email": "login@b.com", "password": "pass1234"})
    res = client.post("/api/auth/login", json={"email": "login@b.com", "password": "pass1234"})
    assert res.status_code == 200
    assert "access_token" in res.json()


def test_login_wrong_password(client):
    client.post("/api/auth/register", json={"email": "wrong@b.com", "password": "pass1234"})
    res = client.post("/api/auth/login", json={"email": "wrong@b.com", "password": "badpass"})
    assert res.status_code == 401


def test_login_nonexistent(client):
    res = client.post("/api/auth/login", json={"email": "nobody@b.com", "password": "pass1234"})
    assert res.status_code == 401


def test_me_authenticated(client, auth_headers):
    res = client.get("/api/auth/me", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["email"] == "test@test.com"


def test_me_unauthenticated(client):
    res = client.get("/api/auth/me")
    assert res.status_code == 401


# ── API key tests ──────────────────────────────────────────────


def test_create_api_key(client, auth_headers):
    res = client.post(
        "/api/auth/api-keys",
        headers=auth_headers,
        json={"name": "my-key"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["raw_key"].startswith("ak_")
    assert len(data["raw_key"]) == 67  # "ak_" + 64 hex
    assert data["prefix"] == data["raw_key"][:12]
    assert data["name"] == "my-key"
    assert "id" in data
    assert "created_at" in data


def test_create_api_key_no_name(client, auth_headers):
    res = client.post("/api/auth/api-keys", headers=auth_headers, json={})
    assert res.status_code == 200
    assert res.json()["name"] is None


def test_create_api_key_unauthenticated(client):
    res = client.post("/api/auth/api-keys", json={"name": "k"})
    assert res.status_code == 401


def test_list_api_keys(client, auth_headers):
    client.post("/api/auth/api-keys", headers=auth_headers, json={"name": "a"})
    client.post("/api/auth/api-keys", headers=auth_headers, json={"name": "b"})
    res = client.get("/api/auth/api-keys", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 2
    assert "raw_key" not in data[0]
    assert data[0]["prefix"].startswith("ak_")
    assert data[0]["name"] in ("a", "b")


def test_list_api_keys_empty(client, auth_headers):
    res = client.get("/api/auth/api-keys", headers=auth_headers)
    assert res.status_code == 200
    assert res.json() == []


def test_delete_api_key(client, auth_headers):
    create = client.post("/api/auth/api-keys", headers=auth_headers, json={"name": "del-me"})
    key_id = create.json()["id"]

    res = client.delete(f"/api/auth/api-keys/{key_id}", headers=auth_headers)
    assert res.status_code == 204

    listed = client.get("/api/auth/api-keys", headers=auth_headers)
    assert listed.json() == []


def test_delete_nonexistent_key(client, auth_headers):
    res = client.delete("/api/auth/api-keys/9999", headers=auth_headers)
    assert res.status_code == 404


def test_delete_other_users_key(client):
    # User A creates a key
    client.post("/api/auth/register", json={"email": "a@b.com", "password": "pass1234"})
    login_a = client.post("/api/auth/login", json={"email": "a@b.com", "password": "pass1234"})
    token_a = login_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    create = client.post("/api/auth/api-keys", headers=headers_a, json={"name": "a-key"})
    key_id = create.json()["id"]

    # User B tries to delete User A's key
    client.post("/api/auth/register", json={"email": "b@b.com", "password": "pass1234"})
    login_b = client.post("/api/auth/login", json={"email": "b@b.com", "password": "pass1234"})
    token_b = login_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    res = client.delete(f"/api/auth/api-keys/{key_id}", headers=headers_b)
    assert res.status_code == 404


def test_authenticate_with_api_key(client, auth_headers):
    create = client.post("/api/auth/api-keys", headers=auth_headers, json={"name": "k"})
    raw_key = create.json()["raw_key"]

    res = client.get("/api/auth/me", headers={"X-API-Key": raw_key})
    assert res.status_code == 200
    assert res.json()["email"] == "test@test.com"


def test_invalid_api_key(client):
    res = client.get("/api/auth/me", headers={"X-API-Key": "ak_badkey"})
    assert res.status_code == 401


def test_jwt_still_works(client, auth_headers):
    res = client.get("/api/auth/me", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["email"] == "test@test.com"


def test_jwt_takes_precedence_over_api_key(client):
    # Register user A, get JWT
    client.post("/api/auth/register", json={"email": "jwta@b.com", "password": "pass1234"})
    login_a = client.post("/api/auth/login", json={"email": "jwta@b.com", "password": "pass1234"})
    token_a = login_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Create API key for user A
    client.post("/api/auth/api-keys", headers=headers_a, json={"name": "k"})

    # Register user B (whose API key we create below to test that JWT wins)
    client.post("/api/auth/register", json={"email": "jwtb@b.com", "password": "pass1234"})
    login_b = client.post("/api/auth/login", json={"email": "jwtb@b.com", "password": "pass1234"})
    token_b = login_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    create_b = client.post("/api/auth/api-keys", headers=headers_b, json={"name": "k"})
    raw_key_b = create_b.json()["raw_key"]

    # Send BOTH JWT (user A) and API key (user B) — JWT should win
    res = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token_a}", "X-API-Key": raw_key_b},
    )
    assert res.status_code == 200
    assert res.json()["email"] == "jwta@b.com"  # JWT user, not API-key user
