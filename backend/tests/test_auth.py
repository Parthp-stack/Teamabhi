import pytest
from backend.utils.security import hash_password, verify_password, create_access_token, decode_access_token

def test_password_hashing():
    raw_pass = "secure_password_123"
    hashed = hash_password(raw_pass)
    assert hashed != raw_pass
    assert verify_password(raw_pass, hashed) is True
    assert verify_password("wrong_password", hashed) is False

def test_jwt_generation_and_decoding():
    payload = {"sub": "42", "role": "STUDENT"}
    token = create_access_token(payload)
    decoded = decode_access_token(token)
    assert decoded["sub"] == "42"
    assert decoded["role"] == "STUDENT"
    assert "exp" in decoded

def test_verify_reset_email_endpoints():
    from fastapi.testclient import TestClient
    from backend.main import app
    client = TestClient(app)

    # Test student email check
    res_student = client.post("/api/auth/verify-reset-email", json={"email": "student.a@adaptive.edu"})
    assert res_student.status_code == 200
    data_student = res_student.json()
    assert data_student["exists"] is True
    assert data_student["role"] == "STUDENT"

    # Test flexible username / prefix lookup without domain
    res_prefix = client.post("/api/auth/verify-reset-email", json={"email": "student.a"})
    assert res_prefix.status_code == 200
    assert res_prefix.json()["email"] == "student.a@adaptive.edu"

    # Test whitespace and uppercase handling
    res_case = client.post("/api/auth/verify-reset-email", json={"email": "  STUDENT.A@ADAPTIVE.EDU  "})
    assert res_case.status_code == 200
    assert res_case.json()["exists"] is True

    # Test trainer email check
    res_trainer = client.post("/api/auth/verify-reset-email", json={"email": "trainer@adaptive.edu"})
    assert res_trainer.status_code == 200
    data_trainer = res_trainer.json()
    assert data_trainer["exists"] is True
    assert data_trainer["role"] == "TRAINER"

    # Test trainer short handle
    res_trainer_short = client.post("/api/auth/verify-reset-email", json={"email": "trainer"})
    assert res_trainer_short.status_code == 200

    # Test direct /auth/ route without /api prefix
    res_direct = client.post("/auth/verify-reset-email", json={"email": "student.a@adaptive.edu"})
    assert res_direct.status_code == 200

    # Test nonexistent email check
    res_fake = client.post("/api/auth/verify-reset-email", json={"email": "nonexistent_999@domain.com"})
    assert res_fake.status_code == 404

def test_reset_password_and_login_flow():
    from fastapi.testclient import TestClient
    from backend.main import app
    client = TestClient(app)

    # 1. Register a test user
    test_email = "reset_test_user@adaptive.edu"
    client.post("/api/auth/register", json={
        "name": "Reset Tester",
        "email": test_email,
        "password": "initialPassword123",
        "role": "STUDENT"
    })

    # 2. Reset the password
    new_pass = "newSecurePassword456"
    res_reset = client.post("/api/auth/reset-password", json={
        "email": test_email,
        "new_password": new_pass
    })
    assert res_reset.status_code == 200
    assert res_reset.json()["success"] is True

    # 3. Old password should fail login
    res_old_login = client.post("/api/auth/login", json={
        "email": test_email,
        "password": "initialPassword123"
    })
    assert res_old_login.status_code == 401

    # 4. New password should successfully log in
    res_new_login = client.post("/api/auth/login", json={
        "email": test_email,
        "password": new_pass
    })
    assert res_new_login.status_code == 200
    assert "access_token" in res_new_login.json()
    assert res_new_login.json()["user"]["email"] == test_email

