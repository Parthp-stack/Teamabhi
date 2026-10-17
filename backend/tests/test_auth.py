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

def test_student_demo_otp_forgot_password_flow():
    from fastapi.testclient import TestClient
    from backend.main import app
    client = TestClient(app)

    # 1. Register student
    student_email = "student_otp_test@adaptive.edu"
    client.post("/api/auth/register", json={
        "name": "OTP Student",
        "email": student_email,
        "password": "oldStudentPass123",
        "role": "STUDENT"
    })

    # 2. Step 1: Request Demo OTP
    res_gen = client.post("/api/auth/forgot-password", json={
        "email": student_email,
        "role": "STUDENT"
    })
    assert res_gen.status_code == 200
    gen_data = res_gen.json()
    assert gen_data["success"] is True
    assert "demo_otp" in gen_data
    demo_otp = gen_data["demo_otp"]
    assert len(demo_otp) == 6
    assert demo_otp.isdigit()

    # 3. Step 2: Verify OTP
    res_verify = client.post("/api/auth/verify-reset-otp", json={
        "email": student_email,
        "otp": demo_otp,
        "role": "STUDENT"
    })
    assert res_verify.status_code == 200
    verify_data = res_verify.json()
    assert verify_data["verified"] is True
    assert "reset_token" in verify_data

    # 4. Step 3: Set New Password
    new_student_pass = "newSecureStudentPass456"
    res_reset = client.post("/api/auth/reset-password", json={
        "email": student_email,
        "new_password": new_student_pass,
        "confirm_password": new_student_pass,
        "role": "STUDENT"
    })
    assert res_reset.status_code == 200
    assert res_reset.json()["success"] is True

    # 5. Old password rejected
    res_old = client.post("/api/auth/login", json={
        "email": student_email,
        "password": "oldStudentPass123"
    })
    assert res_old.status_code == 401

    # 6. New password accepted
    res_new = client.post("/api/auth/login", json={
        "email": student_email,
        "password": new_student_pass
    })
    assert res_new.status_code == 200
    assert "access_token" in res_new.json()


def test_trainer_demo_otp_forgot_password_flow():
    from fastapi.testclient import TestClient
    from backend.main import app
    client = TestClient(app)

    # 1. Register trainer
    trainer_email = "trainer_otp_test@adaptive.edu"
    client.post("/api/auth/register", json={
        "name": "OTP Trainer",
        "email": trainer_email,
        "password": "oldTrainerPass123",
        "role": "TRAINER"
    })

    # 2. Step 1: Request Demo OTP
    res_gen = client.post("/api/auth/forgot-password", json={
        "email": trainer_email,
        "role": "TRAINER"
    })
    assert res_gen.status_code == 200
    gen_data = res_gen.json()
    assert gen_data["success"] is True
    assert "demo_otp" in gen_data
    demo_otp = gen_data["demo_otp"]
    assert len(demo_otp) == 6
    assert demo_otp.isdigit()

    # 3. Step 2: Verify OTP
    res_verify = client.post("/api/auth/verify-reset-otp", json={
        "email": trainer_email,
        "otp": demo_otp,
        "role": "TRAINER"
    })
    assert res_verify.status_code == 200
    verify_data = res_verify.json()
    assert verify_data["verified"] is True
    assert "reset_token" in verify_data

    # 4. Step 3: Set New Password
    new_trainer_pass = "newSecureTrainerPass456"
    res_reset = client.post("/api/auth/reset-password", json={
        "email": trainer_email,
        "new_password": new_trainer_pass,
        "confirm_password": new_trainer_pass,
        "role": "TRAINER"
    })
    assert res_reset.status_code == 200
    assert res_reset.json()["success"] is True

    # 5. Old password rejected
    res_old = client.post("/api/auth/login", json={
        "email": trainer_email,
        "password": "oldTrainerPass123"
    })
    assert res_old.status_code == 401

    # 6. New password accepted
    res_new = client.post("/api/auth/login", json={
        "email": trainer_email,
        "password": new_trainer_pass
    })
    assert res_new.status_code == 200
    assert "access_token" in res_new.json()


def test_security_validations():
    from fastapi.testclient import TestClient
    from datetime import datetime, timezone, timedelta
    from backend.main import app
    from backend.database import SessionLocal
    from backend.models.password_reset import PasswordResetOTP
    from backend.models.user import User

    client = TestClient(app)
    sec_email = "sec_test_user@adaptive.edu"
    client.post("/api/auth/register", json={
        "name": "Security User",
        "email": sec_email,
        "password": "initialPassword123",
        "role": "STUDENT"
    })

    # Test 1: Wrong OTP rejected
    res_gen = client.post("/api/auth/forgot-password", json={"email": sec_email})
    assert res_gen.status_code == 200
    valid_otp = res_gen.json()["demo_otp"]

    res_wrong = client.post("/api/auth/verify-reset-otp", json={"email": sec_email, "otp": "999999"})
    assert res_wrong.status_code == 400
    assert "Invalid OTP." in res_wrong.json()["detail"]

    # Test 2: Expired OTP rejected
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == sec_email).first()
        otp_rec = db.query(PasswordResetOTP).filter(
            PasswordResetOTP.email == sec_email,
            PasswordResetOTP.is_used == False
        ).order_by(PasswordResetOTP.created_at.desc()).first()
        otp_rec.expires_at = datetime.now(timezone.utc) - timedelta(minutes=10)
        db.commit()
    finally:
        db.close()

    res_expired = client.post("/api/auth/verify-reset-otp", json={"email": sec_email, "otp": valid_otp})
    assert res_expired.status_code == 400
    assert "OTP expired" in res_expired.json()["detail"]

    # Test 3: New OTP invalidates old OTP
    res_gen_old = client.post("/api/auth/forgot-password", json={"email": sec_email})
    old_otp = res_gen_old.json()["demo_otp"]

    res_gen_new = client.post("/api/auth/forgot-password", json={"email": sec_email})
    new_otp = res_gen_new.json()["demo_otp"]

    # Old OTP should be rejected
    res_old_otp = client.post("/api/auth/verify-reset-otp", json={"email": sec_email, "otp": old_otp})
    assert res_old_otp.status_code == 400
    assert "Invalid OTP." in res_old_otp.json()["detail"]

    # Test 4: 5 incorrect attempts and 6th attempt rejected
    res_attempt_otp = client.post("/api/auth/forgot-password", json={"email": sec_email})
    curr_otp = res_attempt_otp.json()["demo_otp"]

    # Attempts 1, 2, 3, 4 with wrong OTP
    for i in range(1, 5):
        r = client.post("/api/auth/verify-reset-otp", json={"email": sec_email, "otp": f"90000{i}"})
        assert r.status_code == 400
        assert "Invalid OTP." in r.json()["detail"]

    # Attempt 5: reaches maximum attempts
    r5 = client.post("/api/auth/verify-reset-otp", json={"email": sec_email, "otp": "900005"})
    assert r5.status_code == 400
    assert "Too many incorrect attempts" in r5.json()["detail"]

    # Attempt 6: rejected
    r6 = client.post("/api/auth/verify-reset-otp", json={"email": sec_email, "otp": curr_otp})
    assert r6.status_code == 400
    assert "Too many incorrect attempts" in r6.json()["detail"]

    # Test 5: Reuse OTP rejected after reset
    res_fresh = client.post("/api/auth/forgot-password", json={"email": sec_email})
    fresh_otp = res_fresh.json()["demo_otp"]

    # Verify fresh OTP
    res_v = client.post("/api/auth/verify-reset-otp", json={"email": sec_email, "otp": fresh_otp})
    assert res_v.status_code == 200

    # Test 6: Mismatched passwords rejected
    res_mismatch = client.post("/api/auth/reset-password", json={
        "email": sec_email,
        "new_password": "validNewPass123",
        "confirm_password": "differentPassword456"
    })
    assert res_mismatch.status_code == 400
    assert "Passwords do not match." in res_mismatch.json()["detail"]

    # Complete reset with matching passwords
    res_done = client.post("/api/auth/reset-password", json={
        "email": sec_email,
        "new_password": "validNewPass123",
        "confirm_password": "validNewPass123"
    })
    assert res_done.status_code == 200

    # Test 7: Re-use of same OTP rejected
    res_reuse = client.post("/api/auth/verify-reset-otp", json={"email": sec_email, "otp": fresh_otp})
    assert res_reuse.status_code == 400
    assert "Invalid OTP." in res_reuse.json()["detail"]

    # Test 8: Role isolation: student request for trainer role or vice versa rejected
    res_role_mismatch = client.post("/api/auth/forgot-password", json={
        "email": sec_email,
        "role": "TRAINER"
    })
    assert res_role_mismatch.status_code == 400
    assert "registered as a STUDENT" in res_role_mismatch.json()["detail"]

