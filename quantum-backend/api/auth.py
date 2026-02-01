"""
Authentication API Endpoints
Simple JWT-based authentication for demo
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class LoginRequest(BaseModel):
    """Login request"""
    email: str
    password: str


class SignupRequest(BaseModel):
    """Signup request"""
    name: str
    email: str
    password: str
    role: str


class TokenResponse(BaseModel):
    """Token response"""
    access_token: str
    token_type: str = "bearer"
    user: dict


# Mock user database (replace with real database in production)
# Password hashes are generated at runtime to avoid bcrypt import issues
MOCK_USERS = {}

def get_demo_user():
    """Get or create demo user"""
    if "demo@quantum.ai" not in MOCK_USERS:
        MOCK_USERS["demo@quantum.ai"] = {
            "name": "Demo User",
            "email": "demo@quantum.ai",
            "password_hash": pwd_context.hash("demo123"),
            "role": "manager"
        }
    return MOCK_USERS["demo@quantum.ai"]



def create_access_token(data: dict) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm
    )
    return encoded_jwt


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """
    Login endpoint
    Demo credentials: demo@quantum.ai / demo123
    """
    try:
        # Initialize demo user if needed
        get_demo_user()
        
        # Check if user exists
        user = MOCK_USERS.get(request.email)
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Verify password
        if not pwd_context.verify(request.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Create access token
        access_token = create_access_token(
            data={"sub": request.email, "role": user["role"]}
        )
        
        return TokenResponse(
            access_token=access_token,
            user={
                "name": user["name"],
                "email": user["email"],
                "role": user["role"]
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Login failed")


@router.post("/signup", response_model=TokenResponse)
async def signup(request: SignupRequest):
    """
    Signup endpoint
    Creates a new user account
    """
    try:
        # Check if user already exists
        if request.email in MOCK_USERS:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Hash password
        password_hash = pwd_context.hash(request.password)
        
        # Create user
        MOCK_USERS[request.email] = {
            "name": request.name,
            "email": request.email,
            "password_hash": password_hash,
            "role": request.role
        }
        
        # Create access token
        access_token = create_access_token(
            data={"sub": request.email, "role": request.role}
        )
        
        return TokenResponse(
            access_token=access_token,
            user={
                "name": request.name,
                "email": request.email,
                "role": request.role
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Signup failed")
