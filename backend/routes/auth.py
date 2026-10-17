from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.user import User, UserRole
from backend.schemas.user import (
    UserRegister,
    UserLogin,
    UserResponse,
    Token,
    VerifyEmailRequest,
    VerifyEmailResponse,
    ResetPasswordRequest,
    ResetPasswordResponse
)
from backend.utils.security import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(user_in: UserRegister, db: Session = Depends(get_db)):
    clean_email = user_in.email.strip().lower()
    # Check if user already exists
    existing = db.query(User).filter(func.lower(User.email) == clean_email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists"
        )
    
    # Normalize role
    role = UserRole.STUDENT.value
    if user_in.role and user_in.role.upper() == UserRole.TRAINER.value:
        role = UserRole.TRAINER.value

    # Create new user
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

def find_user_by_identifier(identifier: str, db: Session):
    if not identifier:
        return None
    clean = identifier.strip().lower()
    if not clean:
        return None

    # 1. Exact case-insensitive match on email (with trim)
    user = db.query(User).filter(func.trim(func.lower(User.email)) == clean).first()
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

    # 4. Fallback: match by StudentProfile enrollment_number if present
    from backend.models.user import StudentProfile
    profile = db.query(StudentProfile).filter(func.trim(func.lower(StudentProfile.enrollment_number)) == clean).first()
    if profile and profile.user:
        return profile.user

    return None

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

@router.post("/verify-reset-email", response_model=VerifyEmailResponse)
def verify_reset_email(req: VerifyEmailRequest, db: Session = Depends(get_db)):
    user = find_user_by_identifier(req.email, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No account found matching '{req.email.strip()}' in our database. Please verify the email or create a new account."
        )

    return VerifyEmailResponse(
        exists=True,
        email=user.email,
        name=user.name,
        role=user.role,
        message=f"Account found for {user.name} ({user.role})"
    )

@router.post("/reset-password", response_model=ResetPasswordResponse)
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    if not req.new_password or len(req.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 6 characters long."
        )

    user = find_user_by_identifier(req.email, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No account found matching '{req.email.strip()}' in our database."
        )

    user.password_hash = hash_password(req.new_password)
    db.commit()
    db.refresh(user)

    return ResetPasswordResponse(
        success=True,
        message="Password has been successfully updated! You can now log in with your new password.",
        email=user.email,
        role=user.role
    )

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)

