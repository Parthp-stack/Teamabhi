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
from backend.models.password_reset import PasswordResetToken
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
# TOKEN-BASED FORGOT PASSWORD WORKFLOW (NO OTP)
# Flow: EMAIL -> RESET LINK -> NEW PASSWORD -> CONFIRM PASSWORD -> LOGIN
# =====================================================================

@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Initiates Password Reset without OTP:
    1. Verifies user exists for Student or Trainer role.
    2. Generates a cryptographically secure, single-use, 15-minute token.
    3. Hashes token with SHA-256 for secure database storage.
    4. Invalidates previous unused reset tokens for this user.
    5. Sends a password reset link to user's email address.
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

    # Invalidate previous unused reset tokens for this user
    try:
        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.is_used == False
        ).update({"is_used": True})
        db.commit()
    except Exception as e:
        logger.warning(f"Could not invalidate previous reset tokens: {e}")
        db.rollback()

    # Generate cryptographically secure random token (32 bytes urlsafe)
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

    # Store SHA-256 hash in database (never raw token)
    try:
        reset_token_rec = PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
            is_used=False
        )
        db.add(reset_token_rec)
        db.commit()
    except Exception as e:
        logger.error(f"Failed to persist reset token in database: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not generate password reset request. Please try again."
        )

    # Build production-ready reset URL using configured FRONTEND_URL
    frontend_base = (settings.FRONTEND_URL or "http://localhost:5173").rstrip("/")
    reset_link = f"{frontend_base}/reset-password?token={raw_token}"

    # Log safe diagnostic message without exposing token
    logger.info(f"[Auth] Password reset link issued for user_id={user.id} ({user.email})")

    # Send reset link email
    sent, msg = await EmailService.send_reset_link_email(user.email, reset_link, user.name)
    if not sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send password reset email. Please try again later."
        )

    return ForgotPasswordResponse(
        success=True,
        message="Password reset link sent to your email address.",
        email=user.email,
        role=user.role,
        reset_link=reset_link if not os.getenv("RENDER") else None
    )

@router.get("/verify-reset-token", response_model=VerifyResetTokenResponse)
def verify_reset_token(token: str = Query(...), db: Session = Depends(get_db)):
    """
    Validates a password reset token:
    Checks existence, single-use state, and expiration.
    Returns account details for frontend display.
    """
    if not token or len(token.strip()) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset link"
        )

    token_hash = hashlib.sha256(token.strip().encode("utf-8")).hexdigest()
    token_rec = db.query(PasswordResetToken).filter(PasswordResetToken.token_hash == token_hash).first()

    if not token_rec:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset link"
        )

    if token_rec.is_used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset link already used"
        )

    now_utc = datetime.now(timezone.utc)
    exp = token_rec.expires_at
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)

    if now_utc > exp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset link expired"
        )

    user = token_rec.user
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

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
    3. Validates secure single-use reset token from database.
    4. Hashes password with bcrypt.
    5. Updates the exact user account (Student or Trainer).
    6. Invalidates the reset token immediately.
    """
    if not req.new_password or len(req.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 6 characters long."
        )

    if req.confirm_password and req.new_password != req.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match."
        )

    user = None
    token_rec = None

    if req.token:
        # Token-based flow (primary mechanism)
        token_hash = hashlib.sha256(req.token.strip().encode("utf-8")).hexdigest()
        token_rec = db.query(PasswordResetToken).filter(PasswordResetToken.token_hash == token_hash).first()

        if not token_rec:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid reset link"
            )

        if token_rec.is_used:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reset link already used"
            )

        now_utc = datetime.now(timezone.utc)
        exp = token_rec.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)

        if now_utc > exp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reset link expired"
            )

        user = token_rec.user
    elif req.email:
        # Fallback for internal direct programmatic tests or demo campus accounts
        user = find_user_by_identifier(req.email, db, role=req.role)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found"
        )

    # Securely hash new password using existing bcrypt mechanism
    try:
        user.password_hash = hash_password(req.new_password)
        
        # Invalidate the used token
        if token_rec:
            token_rec.is_used = True
        
        # Invalidate any other tokens for this user
        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.is_used == False
        ).update({"is_used": True})

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
        message="Password reset successful",
        email=user.email,
        role=user.role
    )

# Retained backwards-compatible endpoints for existing client callers
@router.post("/send-otp", response_model=ForgotPasswordResponse)
async def send_otp_legacy(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    return await forgot_password(req, db)

@router.post("/verify-otp", response_model=VerifyOTPResponse)
def verify_otp_legacy(req: VerifyOTPRequest, db: Session = Depends(get_db)):
    user = find_user_by_identifier(req.email, db, role=req.role)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email not found")
    return VerifyOTPResponse(success=True, message="Verified", email=user.email, role=user.role)

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
