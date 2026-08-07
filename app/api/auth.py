from fastapi import APIRouter, HTTPException, status
from app.api.schemas import LoginRequest
from app.repositories.user_repository import get_user_by_email
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
