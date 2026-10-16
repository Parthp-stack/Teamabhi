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
