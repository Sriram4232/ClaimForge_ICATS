from fastapi import APIRouter, HTTPException, status
from app.api.schemas import LoginRequest, SignupRequest
from app.repositories.user_repository import get_user_by_email, create_user
from app.utils.jwt_helper import sign_jwt
from app.utils.security import verify_password

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/login")
def login(req: LoginRequest):
    user = get_user_by_email(req.email)
    if not user or not verify_password(user["password"], req.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password credentials."
        )
    
    token = sign_jwt({
        "email": user["email"],
        "role": user["role"],
        "name": user["name"]
    })
    
    return {
        "token": token,
        "name": user["name"],
        "email": user["email"],
        "role": user["role"]
    }

@router.post("/signup")
def signup(req: SignupRequest):
    # Validate non-empty fields
    if not req.name.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Name cannot be empty.")
    if not req.email.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email cannot be empty.")
    if not req.password or len(req.password) < 4:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must be at least 4 characters long.")
    
    # Normalize and validate role
    role = req.role.strip().lower()
    if role not in ["claimant", "bank_employee", "insurer"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Invalid role context. Must be claimant, bank_employee, or insurer."
        )
        
    # Check if user already exists
    existing_user = get_user_by_email(req.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists."
        )
        
    # Create the user
    user = create_user(
        name=req.name.strip(),
        email=req.email.strip().lower(),
        password_raw=req.password,
        role=role
    )
    
    # Automatically log the user in by returning a token
    token = sign_jwt({
        "email": user["email"],
        "role": user["role"],
        "name": user["name"]
    })
    
    return {
        "token": token,
        "name": user["name"],
        "email": user["email"],
        "role": user["role"]
    }
