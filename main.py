from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from jose import jwt, JWTError
from passlib.context import CryptContext
from datetime import datetime, timedelta
import os

from database import users_collection

app = FastAPI(title="Aura Stylist SaaS API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET_KEY = os.getenv("SECRET_KEY", "CHANGE_THIS_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(BaseModel):
    email: str
    password: str

class Login(BaseModel):
    email: str
    password: str

class UserMetrics(BaseModel):
    bust: float
    waist: float
    hips: float
    belly: float = 0.0
    lower_belly: float = 0.0
    undertone: str
    contrast: str
    gender: str = "women"

def create_token(data: dict):
    payload = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload.update({"exp": expire})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

@app.get("/")
def home():
    return {"status": "running", "message": "Aura Stylist SaaS API"}

@app.post("/signup")
async def signup(user: User):
    existing = await users_collection.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    hashed_password = pwd_context.hash(user.password)
    await users_collection.insert_one({
        "email": user.email,
        "password": hashed_password,
        "plan": "free",
        "created_at": datetime.utcnow()
    })
    return {"message": "User created successfully"}

@app.post("/login")
async def login(user: Login):
    db_user = await users_collection.find_one({"email": user.email})
    if not db_user or not pwd_context.verify(user.password, db_user["password"]):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    token = create_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}

def detect_shape(bust, waist, hips):
    if bust > hips: return "Inverted Triangle"
    elif hips > bust: return "Pear"
    return "Hourglass"

# =========================
# PROTECTED SAAS ROUTE (UPDATED)
# =========================
@app.post("/api/v1/style-report")
async def style_report(metrics: UserMetrics):
    # Temporarily removed JWT token verification so you can test the frontend-to-backend connection easily!
    shape = detect_shape(metrics.bust, metrics.waist, metrics.hips)

    # Returning the exact data structure your report.tsx expects
    return {
        "data": {
            "shape": shape,
            "goal": "Enhance your natural structure and balance proportions.",
            "tops": "Structured shoulders, v-necks, and tailored fits.",
            "bottoms": "High-waisted wide leg trousers and A-line skirts.",
            "formula": "Fitted Top + High-Waist Bottom + Layered Accessory",
            "season": "Autumn",
            "vibe": "Warm & Earthy",
            "palette": ["#000000", "#FFFFFF", "#E5A93C", "#8B4513"]
        }
    }