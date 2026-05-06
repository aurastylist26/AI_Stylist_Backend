from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import os
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import jwt

# 1. Pulling your working database connection from your other file!
from database import users_collection

app = FastAPI()

# 2. Environment Variables & Security Setup
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
SECRET_KEY = os.getenv("SECRET_KEY", "your-fallback-secret-key") # Uses Render's secret, or falls back safely
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_token(data: dict):
    """Generates the login token for the mobile app."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# 3. Pydantic Models (The Frontend Data Rules)
class User(BaseModel):
    email: str
    password: str

class Login(BaseModel):
    email: str
    password: str

class VerifyOTP(BaseModel):
    email: str
    otp_code: str

# 4. The OTP "Brain"
def generate_otp():
    """Generates a random 6-digit OTP."""
    return str(random.randint(100000, 999999))

def send_otp_email(receiver_email: str, otp_code: str):
    """Sends the OTP via the official Aura Stylist Gmail account."""
    try:
        msg = MIMEMultipart()
        msg['From'] = f"Aura Stylist <{EMAIL_ADDRESS}>"
        msg['To'] = receiver_email
        msg['Subject'] = "Your Aura Stylist Verification Code"

        body = f"""
        Welcome to Aura Stylist! 
        
        Your verification code is: {otp_code}
        
        Please enter this code in the app to complete your sign up.
        """
        msg.attach(MIMEText(body, 'plain'))

        # Connect to Gmail's server securely
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_ADDRESS, receiver_email, text)
        server.quit()
        
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

# 5. The API Routes
@app.post("/signup")
async def signup(user: User):
    # Step A: Check if they already have an account
    existing = await users_collection.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    
    # Step B: Secure the password and create the code
    hashed_password = pwd_context.hash(user.password)
    otp = generate_otp()
    
    # Step C: Try to send the email FIRST before saving to the database
    email_sent = send_otp_email(user.email, otp)
    if not email_sent:
        raise HTTPException(status_code=500, detail="Failed to send verification email. Please try again.")

    # Step D: Save to database as "unverified"
    await users_collection.insert_one({
        "email": user.email,
        "password": hashed_password,
        "plan": "free",
        "created_at": datetime.utcnow(),
        "is_verified": False,
        "otp_code": otp
    })
    
    return {"message": "User created. Please check your email for the verification code."}

@app.post("/verify-otp")
async def verify_otp(data: VerifyOTP):
    db_user = await users_collection.find_one({"email": data.email})
    
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if db_user.get("is_verified"):
        return {"message": "Account is already verified."}
        
    if db_user.get("otp_code") != data.otp_code:
        raise HTTPException(status_code=400, detail="Invalid verification code")
        
    # If the code matches, unlock the account and delete the OTP code for security!
    await users_collection.update_one(
        {"email": data.email},
        {
            "$set": {"is_verified": True},
            "$unset": {"otp_code": ""}
        }
    )
    
    return {"message": "Account successfully verified!"}

@app.post("/login")
async def login(user: Login):
    db_user = await users_collection.find_one({"email": user.email})
    
    # Check if user exists and password is correct
    if not db_user or not pwd_context.verify(user.password, db_user["password"]):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
        
    # NEW: Block them if they haven't typed in their OTP yet!
    if not db_user.get("is_verified"):
        raise HTTPException(status_code=403, detail="Please verify your email address before logging in.")
        
    # If they pass all checks, hand them the keys to the app
    token = create_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}