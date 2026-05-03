from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from jose import jwt, JWTError
from datetime import datetime, timedelta
import random
import smtplib
import os
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# =========================
# APP INIT
# =========================

app = FastAPI(
    title="Aura Stylist API",
    docs_url="/docs",
    redoc_url="/redoc"
)

# =========================
# CORS
# =========================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# ENV CONFIG (IMPORTANT)
# =========================

SENDER_EMAIL = os.getenv("SENDER_EMAIL")
APP_PASSWORD = os.getenv("APP_PASSWORD")

SECRET_KEY = os.getenv("SECRET_KEY", "change-this-immediately")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

OTP_EXPIRY_SECONDS = 300

# =========================
# STORAGE (TEMP)
# =========================

otp_storage = {}

# =========================
# MODELS
# =========================

class OTPRequest(BaseModel):
    email: str

class OTPVerify(BaseModel):
    email: str
    otp: str

class UserMetrics(BaseModel):
    gender: str
    bust: float
    waist: float
    hips: float
    belly: float
    lower_belly: float
    undertone: str
    contrast: str

# =========================
# ROOT CHECK
# =========================

@app.get("/")
def home():
    return {"status": "running", "message": "Aura Stylist API live"}

# =========================
# JWT FUNCTIONS
# =========================

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None


def get_current_user(token: str):
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload.get("sub")

# =========================
# OTP SYSTEM
# =========================

@app.post("/api/v1/send-otp")
async def send_otp(request: OTPRequest):

    email = request.email
    otp = str(random.randint(1000, 9999))

    otp_storage[email] = {
        "otp": otp,
        "time": time.time()
    }

    try:
        msg = MIMEMultipart()
        msg["From"] = f"Aura Stylist <{SENDER_EMAIL}>"
        msg["To"] = email
        msg["Subject"] = "Your Aura Stylist OTP"

        msg.attach(MIMEText(f"Your OTP is: {otp}", "plain"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.send_message(msg)
        server.quit()

    except Exception as e:
        print("Email failed:", e)
        print("DEV OTP:", otp)

    return {"message": "OTP sent successfully"}

# =========================
# VERIFY OTP → ISSUE JWT
# =========================

@app.post("/api/v1/verify-otp")
async def verify_otp(request: OTPVerify):

    record = otp_storage.get(request.email)

    if not record:
        raise HTTPException(status_code=400, detail="OTP not found")

    if time.time() - record["time"] > OTP_EXPIRY_SECONDS:
        del otp_storage[request.email]
        raise HTTPException(status_code=400, detail="OTP expired")

    if record["otp"] != request.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    del otp_storage[request.email]

    token = create_access_token({"sub": request.email})

    return {
        "status": "success",
        "access_token": token,
        "token_type": "bearer"
    }

# =========================
# STYLE ENGINE
# =========================

def detect_body_shape(bust, waist, hips):
    if bust > hips and (bust - waist) > 10:
        return "Inverted Triangle"
    elif hips > bust and (hips - waist) > 8:
        return "Pear"
    elif abs(bust - hips) < 5 and abs(waist - bust) < 8:
        return "Rectangle"
    return "Hourglass"


def detect_season(undertone, contrast):
    if undertone == "warm" and contrast == "high":
        return "Autumn"
    elif undertone == "warm":
        return "Spring"
    elif contrast == "low":
        return "Summer"
    return "Winter"


def generate_recommendation(shape):
    styles = {
        "Pear": {
            "tops": "Bright tops, puff sleeves",
            "bottoms": "Dark straight pants",
            "formula": "Statement Top + Simple Bottom",
            "goal": "Balance lower body"
        },
        "Inverted Triangle": {
            "tops": "Simple V-neck tops",
            "bottoms": "Wide-leg pants",
            "formula": "Simple Top + Wide Bottom",
            "goal": "Balance upper body"
        },
        "Rectangle": {
            "tops": "Layered tops",
            "bottoms": "Flared pants",
            "formula": "Layer + Shape",
            "goal": "Create curves"
        },
        "Hourglass": {
            "tops": "Fitted tops",
            "bottoms": "High-waist jeans",
            "formula": "Highlight Waist",
            "goal": "Enhance natural shape"
        }
    }

    return styles.get(shape, styles["Hourglass"])


def get_palette(season):
    palettes = {
        "Winter": ["#000000", "#FFFFFF", "#6B46C1"],
        "Summer": ["#A0AEC0", "#FBB6CE", "#EDF2F7"],
        "Autumn": ["#744210", "#C05621", "#D69E2E"],
        "Spring": ["#F6E05E", "#68D391", "#63B3ED"]
    }
    return palettes.get(season, [])

# =========================
# PROTECTED ROUTE
# =========================

@app.post("/api/v1/style-report")
async def style_report(metrics: UserMetrics, token: str):

    user = get_current_user(token)

    shape = detect_body_shape(metrics.bust, metrics.waist, metrics.hips)
    season = detect_season(metrics.undertone, metrics.contrast)
    style = generate_recommendation(shape)

    return {
        "user": user,
        "status": "success",
        "data": {
            "shape": shape,
            "goal": style["goal"],
            "tops": style["tops"],
            "bottoms": style["bottoms"],
            "formula": style["formula"],
            "season": season,
            "palette": get_palette(season)
        }
    }