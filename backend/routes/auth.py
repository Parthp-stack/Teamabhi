import os
import secrets
import hashlib
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import get_db
from backend.models.user import User, UserRole, StudentProfile, TeacherProfile
from backend.models.password_reset import PasswordResetToken, PasswordResetOTP
from backend.schemas.user import (
    UserRegister,
    UserLogin,
    UserResponse,
    Token,
    VerifyEmailRequest,
    VerifyEmailResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    VerifyResetTokenResponse,
    VerifyOTPRequest,
    VerifyOTPResponse,
    ResetPasswordRequest,
    ResetPasswordResponse
)
from backend.utils.security import hash_password, verify_password, create_access_token, get_current_user
from backend.services.email_service import EmailService

logger = logging.getLogger("auth")
router = APIRouter(prefix="/auth", tags=["Authentication"])

def normalize_role(role: Optional[str]) -> Optional[str]:
    if not role:
        return None
    r = role.strip().upper()
    if r in ("TRAINER", "TEACHER", "INSTRUCTOR", "OWNER"):
        return UserRole.TRAINER.value
    if r in ("STUDENT", "LEARNER", "PUPIL"):
        return UserRole.STUDENT.value
    return r

def find_user_by_identifier(identifier: str, db: Session, role: Optional[str] = None) -> Optional[User]:
    if not identifier:
        return None
    clean = identifier.strip().lower()
    if not clean:
        return None

    target_role = normalize_role(role)

    # 1. Exact case-insensitive match on email (with trim)
    query = db.query(User).filter(func.trim(func.lower(User.email)) == clean)
    user = query.first()
    if user:
        return user

    # 2. If no '@' is present, try standard campus domain or prefix
    if "@" not in clean:
        user = db.query(User).filter(func.trim(func.lower(User.email)) == f"{clean}@adaptive.edu").first()
        if user:
            return user
        user = db.query(User).filter(func.lower(User.email).like(f"{clean}@%")).first()
        if user:
            return user

    # 3. Match by name (exact or prefix)
    user = db.query(User).filter(func.trim(func.lower(User.name)) == clean).first()
    if user:
        return user
    user = db.query(User).filter(func.lower(User.name).like(f"{clean}%")).first()
    if user:
        return user

    # 4. Search student enrollment number in students table
    profile = db.query(StudentProfile).filter(func.trim(func.lower(StudentProfile.enrollment_number)) == clean).first()
    if profile and profile.user:
        return profile.user

    # 5. Search teacher department in teachers table
    t_profile = db.query(TeacherProfile).filter(func.trim(func.lower(TeacherProfile.department)) == clean).first()
    if t_profile and t_profile.user:
        return t_profile.user

    return None

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(user_in: UserRegister, db: Session = Depends(get_db)):
    clean_email = user_in.email.strip().lower()
    existing = db.query(User).filter(func.lower(User.email) == clean_email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists"
        )
    
    role = UserRole.STUDENT.value
    if user_in.role and user_in.role.upper() == UserRole.TRAINER.value:
        role = UserRole.TRAINER.value

    user = User(
        name=user_in.name.strip(),
        email=clean_email,
        password_hash=hash_password(user_in.password),
        role=role
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(data={"sub": str(user.id), "role": user.role})
    return Token(access_token=token, token_type="bearer", user=UserResponse.model_validate(user))

@router.post("/login", response_model=Token)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    user = find_user_by_identifier(credentials.email, db)
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token = create_access_token(data={"sub": str(user.id), "role": user.role})
    return Token(access_token=token, token_type="bearer", user=UserResponse.model_validate(user))

# =====================================================================
# DEMO / HACKATHON OTP FORGOT PASSWORD WORKFLOW
# Flow: EMAIL -> GENERATE DEMO OTP -> SHOW OTP -> VERIFY OTP -> NEW PASSWORD -> CONFIRM PASSWORD -> LOGIN
# =====================================================================

def create_demo_otp(user: User, db: Session) -> str:
    """
    Generates a secure 6-digit Demo OTP and persists its SHA-256 hash.
    - Exactly 6 digits (supports leading zeros)
    - Expire after 5 minutes
    - Single-use
    - Invalidates any previous OTPs for this user
    - Maximum 5 attempts allowed
    - Never stores plaintext OTP in database
    """
    # 1. Invalidate previous unused OTPs for this user
    try:
        db.query(PasswordResetOTP).filter(
            func.lower(PasswordResetOTP.email) == user.email.lower(),
            PasswordResetOTP.is_used == False
        ).update({"is_used": True})
        db.commit()
    except Exception as e:
        logger.warning(f"Could not invalidate previous OTPs: {e}")
        db.rollback()

    # 2. Generate cryptographically secure random 6-digit OTP (e.g. 042781)
    raw_otp = f"{secrets.randbelow(1000000):06d}"
    otp_hash = hashlib.sha256(raw_otp.encode("utf-8")).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)

    otp_rec = PasswordResetOTP(
        email=user.email,
        role=user.role,
        otp_code=otp_hash,
        attempts=0,
        expires_at=expires_at,
        is_used=False,
        is_verified=False
    )
    db.add(otp_rec)
    db.commit()
    db.refresh(otp_rec)

    logger.info(f"[Auth DEMO] Generated 6-digit demo OTP for {user.email}")
    return raw_otp

@router.post("/forgot-password", response_model=ForgotPasswordResponse)
@router.post("/send-otp", response_model=ForgotPasswordResponse)
@router.post("/generate-otp", response_model=ForgotPasswordResponse)
def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Demo / Hackathon OTP Generation:
    1. Verifies user exists for Student or Trainer role.
    2. Generates a secure random 6-digit OTP using secrets.
    3. Hashes OTP with SHA-256 for secure database storage.
    4. Invalidates previous unused OTPs for this user.
    5. Returns demo_otp directly in response for on-screen testing (NO email sent).
    """
    clean_input = req.email.strip()
    if not clean_input:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide an email address."
        )

    user = find_user_by_identifier(clean_input, db, role=req.role)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found"
        )

    # Verify role match if role requested
    target_role = normalize_role(req.role)
    if target_role and user.role != target_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"This account is registered as a {user.role}. Please switch to the {user.role.capitalize()} tab to continue."
        )

    demo_otp = create_demo_otp(user, db)

    return ForgotPasswordResponse(
        success=True,
        message="Demo OTP generated successfully",
        demo_otp=demo_otp,
        email=user.email,
        role=user.role
    )

@router.post("/verify-reset-otp", response_model=VerifyOTPResponse)
@router.post("/verify-otp", response_model=VerifyOTPResponse)
def verify_reset_otp(req: VerifyOTPRequest, db: Session = Depends(get_db)):
    """
    Verifies 6-digit Demo OTP:
    1. Checks user exists and role matches.
    2. Checks latest active OTP record.
    3. Enforces max 5 incorrect attempts.
    4. Enforces 5-minute expiry.
    5. Validates SHA-256 hash.
    6. On success: marks is_verified=True, issues reset_token.
    """
    if not req.otp or not req.otp.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP."
        )

    user = find_user_by_identifier(req.email, db, role=req.role)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found"
        )

    target_role = normalize_role(req.role)
    if target_role and user.role != target_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"This account is registered as a {user.role}. Please switch to the {user.role.capitalize()} tab to continue."
        )

    # Find latest OTP record for this user
    otp_rec = (
        db.query(PasswordResetOTP)
        .filter(func.lower(PasswordResetOTP.email) == user.email.lower())
        .order_by(PasswordResetOTP.created_at.desc())
        .first()
    )

    if not otp_rec:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP."
        )

    # Check maximum attempts reached
    if otp_rec.attempts >= 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Too many incorrect attempts. Please generate a new OTP."
        )

    if otp_rec.is_used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP."
        )

    # Check expiration (5 minutes)
    now_utc = datetime.now(timezone.utc)
    exp = otp_rec.expires_at
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)

    if now_utc > exp:
        otp_rec.is_used = True
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP expired. Please generate a new OTP."
        )

    # Validate OTP hash
    input_otp = req.otp.strip()
    input_hash = hashlib.sha256(input_otp.encode("utf-8")).hexdigest()

    if input_hash != otp_rec.otp_code:
        otp_rec.attempts += 1
        if otp_rec.attempts >= 5:
            otp_rec.is_used = True
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Too many incorrect attempts. Please generate a new OTP."
            )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP."
        )

    # Mark as verified and generate reset authorization token
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    otp_rec.is_verified = True
    otp_rec.reset_token = token_hash
    db.commit()

    return VerifyOTPResponse(
        verified=True,
        success=True,
        message="OTP verified successfully",
        email=user.email,
        role=user.role,
        reset_token=raw_token
    )

@router.get("/verify-reset-token", response_model=VerifyResetTokenResponse)
def verify_reset_token(token: str = Query(...), db: Session = Depends(get_db)):
    """
    Validates a password reset authorization token:
    Checks existence, single-use state, and expiration.
    Returns account details for frontend display.
    """
    if not token or len(token.strip()) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset link"
        )

    token_hash = hashlib.sha256(token.strip().encode("utf-8")).hexdigest()

    # Check PasswordResetOTP first
    otp_rec = db.query(PasswordResetOTP).filter(
        PasswordResetOTP.reset_token == token_hash,
        PasswordResetOTP.is_used == False,
        PasswordResetOTP.is_verified == True
    ).first()

    if otp_rec:
        now_utc = datetime.now(timezone.utc)
        exp = otp_rec.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if now_utc > exp:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP expired. Please generate a new OTP.")
        user = find_user_by_identifier(otp_rec.email, db, role=otp_rec.role)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return VerifyResetTokenResponse(
            valid=True,
            email=user.email,
            name=user.name,
            role=user.role
        )

    # Fallback for PasswordResetToken
    token_rec = db.query(PasswordResetToken).filter(PasswordResetToken.token_hash == token_hash).first()
    if not token_rec:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid reset link")
    if token_rec.is_used:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reset link already used")
    now_utc = datetime.now(timezone.utc)
    exp = token_rec.expires_at
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)
    if now_utc > exp:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reset link expired")

    user = token_rec.user
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return VerifyResetTokenResponse(
        valid=True,
        email=user.email,
        name=user.name,
        role=user.role
    )

@router.post("/reset-password", response_model=ResetPasswordResponse)
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    Completes password reset:
    1. Validates password length >= 6.
    2. Validates password confirmation match.
    3. Confirms OTP verification succeeded & reset authorization is still valid.
    4. Hashes new password with existing bcrypt hashing system.
    5. Updates the correct Student or Trainer account.
    6. Invalidate the OTP/reset authorization.
    7. Ensures old password no longer works.
    """
    if not req.new_password or len(req.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 6 characters long."
        )

    if req.confirm_password is not None and req.new_password != req.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match."
        )

    user = None
    target_otp_rec = None

    if req.token:
        token_hash = hashlib.sha256(req.token.strip().encode("utf-8")).hexdigest()
        target_otp_rec = db.query(PasswordResetOTP).filter(
            PasswordResetOTP.reset_token == token_hash,
            PasswordResetOTP.is_used == False,
            PasswordResetOTP.is_verified == True
        ).first()

        if target_otp_rec:
            now_utc = datetime.now(timezone.utc)
            exp = target_otp_rec.expires_at
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=timezone.utc)
            if now_utc > exp:
                target_otp_rec.is_used = True
                db.commit()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="OTP expired. Please generate a new OTP."
                )
            user = find_user_by_identifier(target_otp_rec.email, db, role=target_otp_rec.role)
        else:
            # Fallback for legacy PasswordResetToken
            legacy_token = db.query(PasswordResetToken).filter(
                PasswordResetToken.token_hash == token_hash,
                PasswordResetToken.is_used == False
            ).first()
            if not legacy_token:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid or expired reset authorization."
                )
            now_utc = datetime.now(timezone.utc)
            exp = legacy_token.expires_at
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=timezone.utc)
            if now_utc > exp:
                legacy_token.is_used = True
                db.commit()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Reset link expired"
                )
            user = legacy_token.user

    elif req.email:
        user = find_user_by_identifier(req.email, db, role=req.role)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email not found"
            )

        target_otp_rec = (
            db.query(PasswordResetOTP)
            .filter(
                func.lower(PasswordResetOTP.email) == user.email.lower(),
                PasswordResetOTP.is_used == False
            )
            .order_by(PasswordResetOTP.created_at.desc())
            .first()
        )

        if not target_otp_rec:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password reset authorization missing or expired. Please generate a new OTP."
            )

        now_utc = datetime.now(timezone.utc)
        exp = target_otp_rec.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if now_utc > exp:
            target_otp_rec.is_used = True
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OTP expired. Please generate a new OTP."
            )

        if req.otp:
            input_hash = hashlib.sha256(req.otp.strip().encode("utf-8")).hexdigest()
            if input_hash != target_otp_rec.otp_code:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid OTP."
                )
            target_otp_rec.is_verified = True
        elif not target_otp_rec.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please verify OTP before resetting password."
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or reset authorization is required."
        )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Validate role matching
    target_role = normalize_role(req.role)
    if target_role and user.role != target_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"This account is registered as a {user.role}. Please switch to the {user.role.capitalize()} tab to continue."
        )

    # Securely hash new password using existing bcrypt mechanism
    try:
        user.password_hash = hash_password(req.new_password)

        # Invalidate used OTPs and reset tokens for this user
        db.query(PasswordResetOTP).filter(
            func.lower(PasswordResetOTP.email) == user.email.lower(),
            PasswordResetOTP.is_used == False
        ).update({"is_used": True})

        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.is_used == False
        ).update({"is_used": True})

        db.commit()


        db.commit()
        db.refresh(user)
    except Exception as e:
        logger.error(f"Failed to update password in DB: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed"
        )

    logger.info(f"[Auth] Password reset successfully completed for user_id={user.id} ({user.email})")

    return ResetPasswordResponse(
        success=True,
        message="Password changed successfully",
        email=user.email,
        role=user.role
    )

@router.post("/verify-reset-email", response_model=VerifyEmailResponse)
def verify_reset_email(req: VerifyEmailRequest, db: Session = Depends(get_db)):
    user = find_user_by_identifier(req.email, db, role=req.role)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found"
        )

    return VerifyEmailResponse(
        exists=True,
        email=user.email,
        name=user.name,
        role=user.role,
        message=f"Account found for {user.name} ({user.role})"
    )

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)
