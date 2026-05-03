from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = FastAPI()

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- EMAIL CONFIG ---
SENDER_EMAIL = "official.aurastylist@gmail.com"
APP_PASSWORD = "vdxu amhq hrfs ceid"

# --- MODELS ---
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

otp_storage = {}

# =========================
# 🔐 AUTH SYSTEM
# =========================

@app.post("/api/v1/send-otp")
async def send_otp(request: OTPRequest):
    email = request.email
    generated_otp = str(random.randint(1000, 9999))
    otp_storage[email] = generated_otp

    try:
        msg = MIMEMultipart()
        msg['From'] = f"Aura Stylist <{SENDER_EMAIL}>"
        msg['To'] = email
        msg['Subject'] = "Your Aura Stylist Security Code"

        body = f"Your OTP is: {generated_otp}"
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.send_message(msg)
        server.quit()

    except Exception as e:
        print("Email failed:", e)
        print("OTP:", generated_otp)

    return {"message": "OTP sent successfully"}


@app.post("/api/v1/verify-otp")
async def verify_otp(request: OTPVerify):
    stored = otp_storage.get(request.email)

    if stored and stored == request.otp:
        return {"status": "success"}
    else:
        raise HTTPException(status_code=400, detail="Invalid OTP")


# =========================
# 🧠 STYLE ENGINE
# =========================

def detect_body_shape(bust, waist, hips):
    if bust > hips and bust - waist > 10:
        return "Inverted Triangle"
    elif hips > bust and hips - waist > 8:
        return "Pear"
    elif abs(bust - hips) < 5 and abs(waist - bust) < 8:
        return "Rectangle"
    else:
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
            "tops": "Bright tops, puff sleeves, off-shoulder",
            "bottoms": "Dark straight pants, A-line skirts",
            "formula": "Statement Top + Simple Bottom",
            "goal": "Balance lower body"
        },
        "Inverted Triangle": {
            "tops": "Simple V-neck tops",
            "bottoms": "Wide-leg pants, flared skirts",
            "formula": "Simple Top + Wide Bottom",
            "goal": "Balance upper body"
        },
        "Rectangle": {
            "tops": "Layered tops, structured fits",
            "bottoms": "Flared pants, skirts",
            "formula": "Layer + Shape",
            "goal": "Create curves"
        },
        "Hourglass": {
            "tops": "Fitted tops, wrap styles",
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
    return palettes[season]


# =========================
# 📊 MAIN API
# =========================

@app.post("/api/v1/style-report")
async def get_style_report(metrics: UserMetrics):

    shape = detect_body_shape(metrics.bust, metrics.waist, metrics.hips)
    season = detect_season(metrics.undertone, metrics.contrast)

    style = generate_recommendation(shape)

    return {
        "status": "success",
        "data": {
            "shape": shape,
            "goal": style["goal"],
            "tops": style["tops"],
            "bottoms": style["bottoms"],
            "formula": style["formula"],
            "season": season,
            "vibe": "Stylish & Balanced",
            "palette": get_palette(season)
        }
    }


# =========================
# ▶ RUN SERVER
# =========================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)